import asyncio
import hashlib
import json
import mimetypes
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


ROOT_DIR = Path(__file__).resolve().parent


def safe_error_message(exc):
    message = f"{type(exc).__name__}: {str(exc)[:1000]}"
    message = re.sub(r"(https?://[^\s?]+)\?[^\s]+", r"\1?<redacted>", message)
    message = re.sub(
        r"(?i)(access[_-]?key(?:[_-]?(?:id|secret))?|session[_-]?token|signature)\s*[=:]\s*[^\s,;]+",
        r"\1=<redacted>",
        message,
    )
    return message[:500]


def _comfy_directory(kind):
    try:
        import folder_paths

        getter = getattr(folder_paths, f"get_{kind}_directory")
        return Path(getter()).resolve()
    except (ImportError, AttributeError, TypeError):
        return (ROOT_DIR / kind).resolve()


def _path_list(value):
    if not value:
        return []
    if isinstance(value, str):
        value = [value]
    return [Path(item).expanduser().resolve() for item in value if str(item).strip()]


def _is_within(path, roots):
    resolved = Path(path).resolve()
    return any(resolved == root or root in resolved.parents for root in roots)


def resolve_output_dir(value, config):
    default_root = _comfy_directory("output")
    roots = [default_root, *_path_list(config.get("allowed_output_roots"))]
    raw = str(value or "ComfyUI-LLM-Agent").strip()
    target = Path(raw).expanduser()
    if not target.is_absolute():
        try:
            import folder_paths

            target = Path(
                folder_paths.get_save_image_path(
                    f"{raw}/__agent_output__", str(default_root)
                )[0]
            )
        except (ImportError, AttributeError, TypeError):
            target = default_root / target
    target = target.resolve()
    if not _is_within(target, roots):
        raise ValueError("output_dir must be inside ComfyUI output or allowed_output_roots.")
    target.mkdir(parents=True, exist_ok=True)
    return target


def resolve_input_path(value, config):
    if not str(value or "").strip():
        return None
    roots = [
        _comfy_directory("input"),
        _comfy_directory("output"),
        *_path_list(config.get("allowed_input_roots")),
    ]
    path = Path(value).expanduser().resolve()
    if not _is_within(path, roots):
        raise ValueError("input_path must be inside ComfyUI input/output or allowed_input_roots.")
    if not path.exists():
        raise ValueError(f"input_path does not exist: {path}")
    return path


def safe_filename(value, default="artifact.png"):
    name = Path(str(value or default)).name
    name = re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", name, flags=re.UNICODE).strip("._")
    return name[:120] or default


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class ArtifactRecord:
    path: str
    kind: str = "output"
    status: str = "success"
    width: int | None = None
    height: int | None = None
    sha256: str = ""
    content_type: str = ""
    oss_uri: str = ""
    signed_url: str = ""
    error: str = ""

    def disk_dict(self):
        data = self.__dict__.copy()
        data.pop("signed_url", None)
        return data


class LocalArtifactStore:
    def __init__(self, output_root, job_id=None, job_dir=None, flat_outputs=False):
        self.output_root = Path(output_root).resolve()
        self.job_id = str(job_id or uuid4().hex)
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        if job_dir:
            candidate = Path(job_dir).resolve()
            if not _is_within(candidate, [self.output_root]):
                raise ValueError("job_dir is outside output_dir.")
            self.job_dir = candidate
        else:
            self.job_dir = (
                self.output_root / self.job_id
                if flat_outputs
                else self.output_root / date_path / self.job_id
            )
        self.inputs_dir = self.job_dir / "inputs"
        self.outputs_dir = self.job_dir if flat_outputs else self.job_dir / "outputs"
        self.inputs_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.records = []

    def output_path(self, filename):
        path = (self.outputs_dir / safe_filename(filename)).resolve()
        if self.outputs_dir.resolve() not in path.parents:
            raise ValueError("Artifact path escaped the job output directory.")
        stem, suffix = path.stem, path.suffix
        counter = 2
        while path.exists():
            path = path.with_name(f"{stem}_{counter}{suffix}")
            counter += 1
        return path

    def add(self, path, kind="output", width=None, height=None):
        path = Path(path).resolve()
        record = ArtifactRecord(
            path=str(path),
            kind=kind,
            width=width,
            height=height,
            sha256=file_sha256(path),
            content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        )
        self.records.append(record)
        return record

    def write_manifest(self, route, status="completed"):
        payload = {
            "job_id": self.job_id,
            "status": status,
            "route": route,
            "artifacts": [record.disk_dict() for record in self.records],
        }
        path = self.job_dir / "manifest.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


class OSSArtifactStore:
    def __init__(self, config, client=None):
        self.bucket = str(config.get("oss_bucket") or "").strip()
        self.prefix = str(config.get("oss_prefix") or "ComfyUI-LLM-Agent").strip("/ ")
        self.expires = int(config.get("oss_signed_url_expires", 86400))
        if self.expires <= 0 or self.expires > 604800:
            raise ValueError("oss_signed_url_expires must be between 1 and 604800 seconds.")
        if not self.bucket:
            raise ValueError("oss_bucket is required when oss_enabled is true.")
        if client is None:
            client = self._create_client(config)
        self.client = client

    @staticmethod
    def _create_client(config):
        try:
            import alibabacloud_oss_v2 as oss
        except ImportError as exc:
            raise ValueError("Install alibabacloud-oss-v2 to enable OSS publishing.") from exc
        access_key_id = os.getenv("OSS_ACCESS_KEY_ID", "").strip()
        access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET", "").strip()
        session_token = os.getenv("OSS_SESSION_TOKEN", "").strip()
        if access_key_id and access_key_secret:
            credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
        else:
            access_key_id = str(config.get("oss_access_key_id") or "").strip()
            access_key_secret = str(config.get("oss_access_key_secret") or "").strip()
            session_token = str(config.get("oss_session_token") or "").strip()
            if not access_key_id or not access_key_secret:
                raise ValueError(
                    "OSS credentials are required in environment variables or config.local.json."
                )
            credentials_provider = oss.credentials.StaticCredentialsProvider(
                access_key_id,
                access_key_secret,
                session_token or None,
            )
        cfg = oss.config.load_default()
        cfg.region = str(config.get("oss_region") or "cn-hangzhou")
        endpoint = str(config.get("oss_endpoint") or "").strip()
        if endpoint and not endpoint.startswith(("http://", "https://")):
            endpoint = f"https://{endpoint}"
        cfg.endpoint = endpoint or None
        cfg.credentials_provider = credentials_provider
        return oss.Client(cfg)

    def object_key(self, record, job_id):
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        filename = safe_filename(Path(record.path).name)
        return f"{self.prefix}/{date_path}/{job_id}/{record.kind}s/{record.sha256[:12]}_{filename}"

    def _upload_sync(self, record, job_id):
        import alibabacloud_oss_v2 as oss

        path = Path(record.path)
        key = self.object_key(record, job_id)
        with path.open("rb") as body:
            self.client.put_object(
                oss.PutObjectRequest(
                    bucket=self.bucket,
                    key=key,
                    body=body,
                    content_type=record.content_type,
                    content_length=path.stat().st_size,
                    metadata={"sha256": record.sha256},
                )
            )
        head = self.client.head_object(oss.HeadObjectRequest(bucket=self.bucket, key=key))
        remote_size = getattr(head, "content_length", path.stat().st_size)
        if int(remote_size) != path.stat().st_size:
            raise ValueError("OSS object size did not match the local artifact.")
        remote_type = str(getattr(head, "content_type", "") or "")
        if remote_type != record.content_type:
            raise ValueError("OSS object Content-Type did not match the local artifact.")
        remote_metadata = getattr(head, "metadata", None) or {}
        remote_sha256 = str(
            remote_metadata.get("sha256")
            or remote_metadata.get("x-oss-meta-sha256")
            or ""
        )
        if remote_sha256 != record.sha256:
            raise ValueError("OSS object SHA-256 metadata did not match the local artifact.")
        signed = self.client.presign(
            oss.GetObjectRequest(bucket=self.bucket, key=key),
            expires=timedelta(seconds=self.expires),
        )
        record.oss_uri = f"oss://{self.bucket}/{key}"
        record.signed_url = str(signed.url)
        return record

    async def upload(self, record, job_id):
        return await asyncio.to_thread(self._upload_sync, record, job_id)


async def publish_records(records, job_id, config):
    if not config.get("oss_enabled"):
        return records
    try:
        store = OSSArtifactStore(config)
    except ValueError as exc:
        for record in records:
            record.error = f"OSS publish skipped: {safe_error_message(exc)}"
        return records
    for record in records:
        if record.status != "success":
            continue
        try:
            await store.upload(record, job_id)
        except Exception as exc:
            record.error = f"OSS publish failed: {safe_error_message(exc)}"
    return records
