import asyncio
import base64
import io
import json
from pathlib import Path

import httpx
import numpy as np
from PIL import Image, ImageOps


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_IMAGE_MODEL = "gpt-image-2"


def validate_image_size(model, size):
    normalized = str(size or "").strip().lower()
    if normalized == "auto":
        return normalized
    try:
        width, height = [int(part) for part in normalized.split("x", 1)]
    except (TypeError, ValueError) as exc:
        raise ValueError("size must be 'auto' or WIDTHxHEIGHT.") from exc
    if width <= 0 or height <= 0:
        raise ValueError("size dimensions must be positive.")
    if model == "gpt-image-2":
        long_edge = max(width, height)
        short_edge = min(width, height)
        pixels = width * height
        if (
            long_edge > 3840
            or width % 16
            or height % 16
            or long_edge / short_edge > 3
            or not 655360 <= pixels <= 8294400
        ):
            raise ValueError(
                "gpt-image-2 size requires edges divisible by 16, max edge 3840, "
                "aspect ratio at most 3:1, and 655360-8294400 total pixels."
            )
    return f"{width}x{height}"


def scan_images(path, limit=200):
    path = Path(path)
    candidates = [path] if path.is_file() else sorted(path.rglob("*"))
    result = []
    for candidate in candidates:
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            try:
                with Image.open(candidate) as image:
                    image.verify()
                result.append(candidate.resolve())
            except (OSError, ValueError):
                continue
        if len(result) >= limit:
            break
    return result


def tensor_to_pil_batch(images):
    if images is None:
        return []
    if hasattr(images, "detach"):
        array = images.detach().cpu().numpy()
    else:
        array = np.asarray(images)
    if array.ndim != 4 or array.shape[-1] not in (3, 4):
        raise ValueError("IMAGE input must be a BHWC tensor with RGB or RGBA channels.")
    result = []
    for item in array:
        pixels = np.rint(np.clip(item, 0.0, 1.0) * 255.0).astype(np.uint8)
        result.append(Image.fromarray(pixels, "RGBA" if pixels.shape[-1] == 4 else "RGB"))
    return result


def mask_to_pil(mask, size):
    if mask is None:
        return None
    if hasattr(mask, "detach"):
        array = mask.detach().cpu().numpy()
    else:
        array = np.asarray(mask)
    if array.ndim == 3:
        array = array[0]
    if array.ndim != 2:
        raise ValueError("MASK input must be a BHW or HW tensor.")
    alpha = np.rint((1.0 - np.clip(array, 0.0, 1.0)) * 255.0).astype(np.uint8)
    return Image.fromarray(alpha, "L").resize(size, Image.Resampling.LANCZOS)


def save_input_images(images, target_dir):
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, image in enumerate(tensor_to_pil_batch(images), 1):
        path = target_dir / f"comfyui_input_{index:03d}.png"
        image.convert("RGB").save(path, format="PNG")
        paths.append(path.resolve())
    return paths


def image_data_url(path, max_edge=1024):
    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def _decode_image_response(data):
    items = data.get("data")
    if not isinstance(items, list) or not items:
        raise ValueError("Image response did not contain data items.")
    return items


class VapeurImageClient:
    def __init__(self, api_key, timeout=600, max_retries=1, retry_delay=2.0, transport=None):
        self.api_key = api_key
        self.max_retries = max(0, int(max_retries))
        self.retry_delay = max(0.0, float(retry_delay))
        self.client = httpx.AsyncClient(
            base_url="https://api.vapeur.ai",
            timeout=httpx.Timeout(float(timeout)),
            transport=transport,
        )
        self.download_client = httpx.AsyncClient(
            timeout=httpx.Timeout(float(timeout)),
            follow_redirects=True,
            transport=transport,
        )

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _request(self, method, path, **kwargs):
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                response = await self.client.request(method, path, headers=self.headers, **kwargs)
                if response.status_code >= 400:
                    message = response.text[:1000]
                    try:
                        payload = response.json()
                        error = payload.get("error", payload)
                        message = error.get("message", error) if isinstance(error, dict) else error
                    except ValueError:
                        pass
                    raise ValueError(f"Vapeur image API error {response.status_code}: {message}")
                return response
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt + 1 >= attempts:
                    raise ValueError(
                        f"Vapeur image request failed after {attempts} attempt(s): {type(exc).__name__}: {exc}"
                    ) from exc
                if self.retry_delay:
                    await asyncio.sleep(self.retry_delay)
        raise RuntimeError("unreachable")

    async def _materialize(self, payload):
        images = []
        for item in _decode_image_response(payload):
            encoded = item.get("b64_json")
            if encoded:
                raw = base64.b64decode(encoded, validate=True)
            elif item.get("url"):
                response = await self.download_client.get(item["url"])
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if content_type and not content_type.startswith("image/"):
                    raise ValueError(f"Image URL returned unexpected content type: {content_type}")
                raw = response.content
            else:
                raise ValueError("Image result contained neither b64_json nor url.")
            if len(raw) > 25 * 1024 * 1024:
                raise ValueError("Downloaded image exceeded the 25 MB safety limit.")
            try:
                with Image.open(io.BytesIO(raw)) as image:
                    images.append(image.convert("RGB").copy())
            except OSError as exc:
                raise ValueError("Image API returned invalid image bytes.") from exc
        return images

    async def generate(self, prompt, model=DEFAULT_IMAGE_MODEL, n=1, size="1024x1024"):
        size = validate_image_size(model, size)
        payload = {
            "model": model,
            "prompt": prompt,
            "n": max(1, min(int(n), 10)),
            "size": size,
            "quality": "high",
            "output_format": "png",
        }
        response = await self._request("POST", "/v1/images/generations", json=payload)
        return await self._materialize(response.json())

    async def edit(self, prompt, image_paths, model=DEFAULT_IMAGE_MODEL, n=1, size="1024x1024", mask=None):
        paths = [Path(path).resolve() for path in image_paths]
        if not paths:
            raise ValueError("Image editing requires at least one input image.")
        if len(paths) > 16:
            raise ValueError("Image editing supports at most 16 input images per request.")
        if sum(path.stat().st_size for path in paths) > 25 * 1024 * 1024:
            raise ValueError("Image editing input files must total no more than 25 MB.")
        size = validate_image_size(model, size)
        files = []
        handles = []
        try:
            for path in paths:
                handle = path.open("rb")
                handles.append(handle)
                files.append(("image", (path.name, handle, _content_type(path))))
            if mask:
                mask_path = Path(mask).resolve()
                handle = mask_path.open("rb")
                handles.append(handle)
                files.append(("mask", (mask_path.name, handle, "image/png")))
            data = {
                "model": model,
                "prompt": prompt,
                "n": str(max(1, min(int(n), 10))),
                "size": size,
                "quality": "high",
                "output_format": "png",
            }
            response = await self._request("POST", "/v1/images/edits", params=data, files=files)
        finally:
            for handle in handles:
                handle.close()
        return await self._materialize(response.json())

    async def close(self):
        await self.client.aclose()
        await self.download_client.aclose()


def _content_type(path):
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(Path(path).suffix.lower(), "application/octet-stream")


def save_generated_images(images, artifact_store, output_name):
    records = []
    base = Path(output_name).stem or "generated"
    for index, image in enumerate(images, 1):
        suffix = f"_{index:02d}" if len(images) > 1 else ""
        path = artifact_store.output_path(f"{base}{suffix}.png")
        image.convert("RGB").save(path, format="PNG")
        records.append(artifact_store.add(path, width=image.width, height=image.height))
    return records


def compose_contact_sheet(image_paths, artifact_store, output_name="contact_sheet.png", columns=3):
    images = []
    for path in image_paths:
        with Image.open(path) as image:
            images.append(image.convert("RGB").copy())
    if not images:
        raise ValueError("Contact sheet requires at least one image.")
    thumb = 512
    rows = (len(images) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * thumb, rows * thumb), "white")
    for index, image in enumerate(images):
        fitted = ImageOps.contain(image, (thumb - 24, thumb - 24), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb + (thumb - fitted.width) // 2
        y = (index // columns) * thumb + (thumb - fitted.height) // 2
        canvas.paste(fitted, (x, y))
    return save_generated_images([canvas], artifact_store, output_name)[0]


def records_to_preview(records, max_edge=2048):
    images = []
    for record in records:
        if record.status != "success" or not record.content_type.startswith("image/"):
            continue
        with Image.open(record.path) as image:
            image = image.convert("RGB")
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            images.append(image.copy())
    if not images:
        array = np.zeros((1, 64, 64, 3), dtype=np.float32)
    else:
        width = max(image.width for image in images)
        height = max(image.height for image in images)
        batch = []
        for image in images:
            canvas = Image.new("RGB", (width, height), "white")
            canvas.paste(image, ((width - image.width) // 2, (height - image.height) // 2))
            batch.append(np.asarray(canvas, dtype=np.float32) / 255.0)
        array = np.stack(batch, axis=0)
    try:
        import torch

        return torch.from_numpy(array)
    except ImportError:
        return array


def artifact_json(records):
    return json.dumps([record.__dict__ for record in records], ensure_ascii=False, indent=2)
