import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from _loader import import_module

artifact_store = import_module("artifact_store")


class FakeOSSClient:
    def __init__(self):
        self.put_request = None

    def put_object(self, request):
        self.put_request = request
        return SimpleNamespace()

    def head_object(self, request):
        return SimpleNamespace(
            content_length=self.put_request.content_length,
            content_type=self.put_request.content_type,
            metadata=self.put_request.metadata,
        )

    def presign(self, request, **kwargs):
        return SimpleNamespace(url="https://example.invalid/file.png?secret=temporary")


class ArtifactStoreTests(unittest.TestCase):
    def test_error_messages_redact_signed_queries_and_credentials(self):
        error = ValueError(
            "GET https://bucket.example/key?x-oss-signature=secret "
            "access_key_secret=also-secret"
        )
        message = artifact_store.safe_error_message(error)
        self.assertNotIn("also-secret", message)
        self.assertNotIn("signature=secret", message)
        self.assertIn("?<redacted>", message)

    def test_oss_credentials_prefer_environment_then_config(self):
        class FakeCredentials:
            class EnvironmentVariableCredentialsProvider:
                pass

            class StaticCredentialsProvider:
                def __init__(self, access_key_id, access_key_secret, token):
                    self.values = (access_key_id, access_key_secret, token)

        class FakeConfig:
            @staticmethod
            def load_default():
                return SimpleNamespace()

        fake_oss = SimpleNamespace(
            credentials=FakeCredentials,
            config=FakeConfig,
            Client=lambda config: config,
        )
        with (
            patch.dict("sys.modules", {"alibabacloud_oss_v2": fake_oss}),
            patch.dict("os.environ", {}, clear=True),
        ):
            client = artifact_store.OSSArtifactStore._create_client(
                {
                    "oss_access_key_id": "config-ak",
                    "oss_access_key_secret": "config-sk",
                    "oss_region": "cn-hangzhou",
                }
            )
        self.assertEqual(client.credentials_provider.values, ("config-ak", "config-sk", None))

    def test_local_manifest_never_persists_signed_url(self):
        with tempfile.TemporaryDirectory() as temp:
            store = artifact_store.LocalArtifactStore(temp)
            path = store.output_path("result.png")
            Image.new("RGB", (4, 3), "red").save(path)
            record = store.add(path, width=4, height=3)
            record.oss_uri = "oss://bucket/key"
            record.signed_url = "https://example.invalid/key?signature=secret"
            manifest = store.write_manifest({"skill_name": "test"})
            payload = manifest.read_text(encoding="utf-8")
        self.assertIn("oss://bucket/key", payload)
        self.assertNotIn("signature=secret", payload)
        self.assertNotIn("signed_url", payload)

    def test_safe_filename_strips_traversal(self):
        self.assertEqual(artifact_store.safe_filename("../../bad name.png"), "bad_name.png")

    def test_oss_upload_sets_uri_and_runtime_signed_url(self):
        with tempfile.TemporaryDirectory() as temp:
            store = artifact_store.LocalArtifactStore(temp)
            path = store.output_path("result.png")
            Image.new("RGB", (4, 3), "blue").save(path)
            record = store.add(path, width=4, height=3)
            oss_store = artifact_store.OSSArtifactStore(
                {
                    "oss_bucket": "bucket",
                    "oss_prefix": "prefix",
                    "oss_signed_url_expires": 86400,
                },
                client=FakeOSSClient(),
            )
            result = oss_store._upload_sync(record, store.job_id)
        self.assertTrue(result.oss_uri.startswith("oss://bucket/prefix/"))
        self.assertIn("?secret=temporary", result.signed_url)

    def test_existing_job_cannot_escape_output_root(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "outside"):
                artifact_store.LocalArtifactStore(temp, job_dir=str(Path(temp).parent))


if __name__ == "__main__":
    unittest.main()
