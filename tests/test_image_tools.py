import asyncio
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path

import httpx
import numpy as np
from PIL import Image

from _loader import import_module

image_tools = import_module("image_tools")
artifact_store = import_module("artifact_store")


def encoded_png(color="red", size=(5, 4)):
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode("ascii")


class ImageToolTests(unittest.TestCase):
    def test_generate_decodes_base64(self):
        async def handler(request):
            self.assertEqual(request.url.path, "/v1/images/generations")
            body = json.loads(request.content)
            self.assertEqual(body["model"], "gpt-image-2")
            return httpx.Response(200, json={"data": [{"b64_json": encoded_png()}]})

        transport = httpx.MockTransport(handler)

        async def run():
            client = image_tools.VapeurImageClient("key", transport=transport)
            try:
                return await client.generate("test")
            finally:
                await client.close()

        images = asyncio.run(run())
        self.assertEqual(images[0].size, (5, 4))

    def test_external_image_download_does_not_send_vapeur_key(self):
        seen = []

        async def handler(request):
            seen.append((request.url.host, request.headers.get("authorization")))
            if request.url.path == "/v1/images/generations":
                return httpx.Response(200, json={"data": [{"url": "https://files.example/result.png"}]})
            return httpx.Response(200, content=base64.b64decode(encoded_png()), headers={"content-type": "image/png"})

        async def run():
            client = image_tools.VapeurImageClient("secret-key", transport=httpx.MockTransport(handler))
            try:
                return await client.generate("test")
            finally:
                await client.close()

        result = asyncio.run(run())
        self.assertEqual(result[0].size, (5, 4))
        self.assertEqual(seen[0], ("api.vapeur.ai", "Bearer secret-key"))
        self.assertEqual(seen[1], ("files.example", None))

    def test_edit_uses_multipart_and_multiple_images(self):
        async def handler(request):
            self.assertEqual(request.url.path, "/v1/images/edits")
            self.assertIn("multipart/form-data", request.headers["content-type"])
            self.assertEqual(request.url.params["model"], "gpt-image-2")
            self.assertEqual(request.url.params["size"], "2048x2048")
            return httpx.Response(200, json={"data": [{"b64_json": encoded_png("blue")}]})

        with tempfile.TemporaryDirectory() as temp:
            paths = []
            for index in range(2):
                path = Path(temp) / f"{index}.png"
                Image.new("RGB", (3, 3), "white").save(path)
                paths.append(path)

            async def run():
                client = image_tools.VapeurImageClient("key", transport=httpx.MockTransport(handler))
                try:
                    return await client.edit("edit", paths)
                finally:
                    await client.close()

            result = asyncio.run(run())
        self.assertEqual(len(result), 1)

    def test_preview_pads_different_sizes(self):
        with tempfile.TemporaryDirectory() as temp:
            store = artifact_store.LocalArtifactStore(temp)
            records = []
            for name, size in (("one.png", (8, 4)), ("two.png", (3, 7))):
                path = store.output_path(name)
                Image.new("RGB", size, "green").save(path)
                records.append(store.add(path, width=size[0], height=size[1]))
            preview = image_tools.records_to_preview(records)
        array = preview.detach().cpu().numpy() if hasattr(preview, "detach") else np.asarray(preview)
        self.assertEqual(array.shape, (2, 7, 8, 3))

    def test_gpt_image_2_size_validation(self):
        self.assertEqual(image_tools.validate_image_size("gpt-image-2", "2048x1536"), "2048x1536")
        with self.assertRaisesRegex(ValueError, "divisible by 16"):
            image_tools.validate_image_size("gpt-image-2", "1000x1000")

    def test_auto_edit_size_preserves_ratio_at_2048_square_pixel_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            landscape = Path(temp) / "landscape.png"
            portrait = Path(temp) / "portrait.png"
            Image.new("RGB", (4000, 3000), "white").save(landscape)
            Image.new("RGB", (900, 1600), "white").save(portrait)

            self.assertEqual(
                image_tools.automatic_edit_size(landscape, "gpt-image-2"),
                "2368x1776",
            )
            self.assertEqual(
                image_tools.automatic_edit_size(portrait, "gpt-image-2"),
                "1536x2736",
            )

    def test_explicit_edit_size_is_not_overridden(self):
        async def handler(request):
            self.assertEqual(request.url.params["size"], "2048x1536")
            return httpx.Response(200, json={"data": [{"b64_json": encoded_png()}]})

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.png"
            Image.new("RGB", (1600, 900), "white").save(path)

            async def run():
                client = image_tools.VapeurImageClient("key", transport=httpx.MockTransport(handler))
                try:
                    return await client.edit("edit", [path], size="2048x1536")
                finally:
                    await client.close()

            result = asyncio.run(run())
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
