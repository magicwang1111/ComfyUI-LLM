import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import av
import numpy as np
import httpx

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/tiktok-fashion-video/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'run': run} if name == 'download_video' else {}):
        spec.loader.exec_module(module)
    return module


run = load('run')
media = load('video_media')
with patch.dict(sys.modules, {'video_media': media}):
    download = load('download_video')
    qc = load('gemini_qc')


def sample_video(path):
    with av.open(str(path), 'w') as output:
        video = output.add_stream('libx264', rate=10)
        video.width, video.height, video.pix_fmt = 64, 96, 'yuv420p'
        audio = output.add_stream('aac', rate=48000)
        audio.layout = 'mono'
        for index in range(10):
            frame = av.VideoFrame.from_ndarray(np.full((96, 64, 3), index * 20, dtype=np.uint8), format='rgb24')
            output.mux(video.encode(frame))
        output.mux(video.encode())
        samples = (0.2 * np.sin(2 * np.pi * 440 * np.arange(48000) / 48000)).astype(np.float32).reshape(1, -1)
        frame = av.AudioFrame.from_ndarray(samples, format='fltp', layout='mono')
        frame.sample_rate = 48000
        output.mux(audio.encode(frame))
        output.mux(audio.encode())


class MediaTests(unittest.TestCase):
    def test_existing_video_resumes_without_network_or_ffprobe(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            final = directory / 'final.mp4'
            sample_video(final)
            before = final.read_bytes()
            with patch.object(run, 'RUN', directory), patch.object(run, 'login') as login, patch.object(media.subprocess, 'run') as shell:
                summary = download.download(directory)
            login.assert_not_called()
            shell.assert_not_called()
            self.assertEqual(final.read_bytes(), before)
            self.assertEqual(summary['streams'][0]['width'], 64)
            self.assertTrue(any(s['codec_type'] == 'audio' for s in summary['streams']))
            self.assertTrue(summary['warnings'])  # A duration mismatch must not discard a valid video.
            self.assertEqual(json.loads((directory / 'status.json').read_text())['stage'], 'video_downloaded')

    def test_download_uses_rendered_duration_and_skips_smart_duration_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            final = directory / 'final.mp4'
            sample_video(final)
            for duration, mismatch in ((1, False), (20, True), (-1, False)):
                with self.subTest(duration=duration):
                    (directory / 'workflow-rendered.json').write_text(json.dumps({'61': {'inputs': {'duration': duration}}}), encoding='utf-8')
                    with patch.object(run, 'RUN', directory), patch.object(run, 'login') as login:
                        summary = download.download(directory)
                    login.assert_not_called()
                    self.assertEqual(any('Expected ' in warning for warning in summary['warnings']), mismatch)

    def test_corrupt_download_never_becomes_final(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'history.json').write_text(json.dumps({'outputs': {'77': {'images': [{'filename': 'bad.mp4', 'subfolder': '', 'type': 'output'}]}}}))
            response = SimpleNamespace(content=b'not a video', raise_for_status=lambda: None)
            with patch.object(run, 'login', return_value=SimpleNamespace(get=lambda *a, **kw: response)):
                with self.assertRaises(av.error.InvalidDataError):
                    download.download(directory)
            self.assertFalse((directory / 'final.mp4').exists())

    def test_compressed_copy_preserves_duration_and_decodable_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            source, proxy = Path(temp) / 'final.mp4', Path(temp) / 'qc.mp4'
            sample_video(source)
            before = source.read_bytes()
            media.compress_for_qc(source, proxy, small=True)
            self.assertEqual(source.read_bytes(), before)
            self.assertAlmostEqual(media.probe_video(proxy)['format']['duration'], 1.0, delta=0.1)
            with av.open(str(proxy)) as container:
                self.assertGreater(sum(f.samples for f in container.decode(audio=0)), 0)


class QCRetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.args = SimpleNamespace(video=root / 'final.mp4', face=root / 'face.jpg', garment=root / 'crop.jpg',
                                    output=root / 'gemini-response.json', base_url='https://example.invalid', model='test')

    def response(self, code, headers=None):
        return SimpleNamespace(status_code=code, headers=headers or {}, json=lambda: {'ok': True})

    def test_413_changes_payload_before_retry(self):
        with patch.object(qc, 'make_payload', side_effect=[b'x' * 100, b'x' * 30]), patch.object(qc, 'compress_for_qc', return_value=Path(self.temp.name) / 'small.mp4') as compress, patch.object(qc.VapeurClient, 'post', side_effect=[self.response(413), self.response(200)]) as post, patch.object(qc.time, 'sleep') as sleep:
            self.assertEqual(qc.request_qc(self.args, 'secret', 'instruction'), {'ok': True})
        self.assertEqual([len(c.kwargs['content']) for c in post.call_args_list], [100, 30])
        self.assertTrue(compress.call_args.kwargs['small'])
        sleep.assert_not_called()
        self.assertNotIn('secret', self.args.output.with_suffix('.attempts.json').read_text())

    def test_transient_failures_retry_with_backoff_then_succeed(self):
        with patch.object(qc, 'make_payload', return_value=b'payload'), patch.object(qc.VapeurClient, 'post', side_effect=[self.response(429, {'Retry-After': '3'}), httpx.ConnectError('connection failed'), self.response(200)]) as post, patch.object(qc.time, 'sleep') as sleep:
            qc.request_qc(self.args, 'secret', 'instruction')
        self.assertEqual(post.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [3, 4])

    def test_retries_stop_after_three_and_auth_errors_stop_immediately(self):
        for code, count in ((503, 3), (401, 1), (400, 1)):
            with self.subTest(code=code), patch.object(qc, 'make_payload', return_value=b'payload'), patch.object(qc.VapeurClient, 'post', return_value=self.response(code)) as post, patch.object(qc.time, 'sleep'):
                with self.assertRaisesRegex(ValueError, f'HTTP {code}'):
                    qc.request_qc(self.args, 'secret', 'instruction')
                self.assertEqual(post.call_count, count)

    def test_repeated_413_stops_after_one_smaller_copy(self):
        with patch.object(qc, 'make_payload', side_effect=[b'x' * 100, b'x' * 30]), patch.object(qc, 'compress_for_qc', return_value=Path(self.temp.name) / 'small.mp4'), patch.object(qc.VapeurClient, 'post', return_value=self.response(413)) as post:
            with self.assertRaisesRegex(ValueError, 'HTTP 413'):
                qc.request_qc(self.args, 'secret', 'instruction')
            self.assertEqual(post.call_count, 2)

    def test_large_inline_request_is_compressed_before_first_http_call(self):
        with patch.object(qc, 'MAX_INLINE_BYTES', 50), patch.object(qc, 'make_payload', side_effect=[b'x' * 100, b'x' * 30]), patch.object(qc, 'compress_for_qc', return_value=Path(self.temp.name) / 'qc.mp4') as compress, patch.object(qc.VapeurClient, 'post', return_value=self.response(200)) as post:
            qc.request_qc(self.args, 'secret', 'instruction')
            compress.assert_called_once()
            self.assertEqual(len(post.call_args.kwargs['content']), 30)


if __name__ == '__main__':
    unittest.main()
