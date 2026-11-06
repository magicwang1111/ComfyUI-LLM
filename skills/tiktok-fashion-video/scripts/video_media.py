import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import av


def probe_video(path):
    """Read media metadata using the node's PyAV dependency, without ffprobe."""
    with av.open(str(path)) as container:
        if not container.streams.video or next(container.decode(video=0), None) is None:
            raise ValueError('Downloaded file has no decodable video frames.')
        streams = []
        for stream in container.streams:
            codec = stream.codec_context
            item = {'codec_type': stream.type, 'codec_name': codec.name}
            if stream.type == 'video':
                item.update(width=codec.width, height=codec.height,
                            r_frame_rate=str(stream.average_rate or 0))
            elif stream.type == 'audio':
                item.update(sample_rate=codec.sample_rate, channels=codec.channels)
            streams.append(item)
        duration = container.duration / av.time_base if container.duration is not None else max(
            (float(s.duration * s.time_base) for s in container.streams if s.duration is not None), default=0
        )
    if duration <= 0:
        raise ValueError('Cannot determine downloaded video duration.')
    return {'probe_backend': 'pyav', 'format': {'duration': duration}, 'streams': streams}


def summarize_video(path, expected_duration=15):
    data = probe_video(path)
    summary = {'duration': float(data['format']['duration']), 'bytes': path.stat().st_size,
               'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'streams': data['streams'], 'warnings': []}
    if abs(summary['duration'] - expected_duration) >= 0.2:
        summary['warnings'].append(f'Expected {expected_duration}s; measured {summary["duration"]}s.')
    if not any(s['codec_type'] == 'audio' for s in summary['streams']):
        summary['warnings'].append('Video has no audio stream; speech QC is unavailable.')
    return data, summary


def compress_for_qc(source, output, small=False):
    if source.resolve() == output.resolve():
        raise ValueError('QC compression must not overwrite the original video.')
    executable = shutil.which('ffmpeg')
    if not executable:
        sibling = Path(sys.executable).with_name('ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg')
        if sibling.is_file():
            executable = str(sibling)
        else:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
    edge, crf, bitrate, audio_rate = (640, 30, '600k', '64k') if small else (960, 26, '1500k', '96k')
    scale = f"scale=w='min(iw,{edge})':h='min(ih,{edge})':force_original_aspect_ratio=decrease:force_divisible_by=2"
    result = subprocess.run([
        executable, '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-i', str(source),
        '-map', '0:v:0', '-map', '0:a:0?', '-vf', scale, '-c:v', 'libx264', '-preset', 'fast',
        '-crf', str(crf), '-maxrate', bitrate, '-bufsize', '3000k', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', audio_rate, '-movflags', '+faststart', str(output),
    ], capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise ValueError('QC video compression failed: ' + result.stderr[-500:])
    original, proxy = probe_video(source), probe_video(output)
    if abs(float(original['format']['duration']) - float(proxy['format']['duration'])) > 0.2:
        raise ValueError('QC copy did not preserve the full video duration.')
    if any(s['codec_type'] == 'audio' for s in original['streams']) and not any(
        s['codec_type'] == 'audio' for s in proxy['streams']
    ):
        raise ValueError('QC copy lost the source audio stream.')
    return output
