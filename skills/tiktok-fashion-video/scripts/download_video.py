import argparse
import json
from pathlib import Path

import run
from video_media import summarize_video


def download(directory):
    final = directory / 'final.mp4'
    if not final.exists():
        history = json.loads((directory / 'history.json').read_text(encoding='utf-8'))
        item = history['outputs']['77']['images'][0]
        session = run.login()
        response = session.get(run.BASE + '/view', params={k: item[k] for k in ['filename', 'subfolder', 'type']}, timeout=180)
        response.raise_for_status()
        temporary = directory / 'final.download.mp4'
        temporary.write_bytes(response.content)
        # Do not expose a partial download as a finished artifact.
        summarize_video(temporary)
        temporary.replace(final)
    expected_duration = 15
    workflow = directory / 'workflow-rendered.json'
    if workflow.exists():
        expected_duration = float(json.loads(workflow.read_text(encoding='utf-8'))['61']['inputs']['duration'])
    data, summary = summarize_video(final, expected_duration)
    # Preserve the workbook helper's metadata filename and schema.
    run.save('ffprobe.json', data)
    run.save('video-summary.json', summary)
    run.status('video_downloaded', video_summary=summary)
    print(json.dumps(summary))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, default=run.RUN)
    parser.add_argument('--base-url', default=run.BASE)
    args = parser.parse_args()
    run.RUN = args.run_dir.resolve()
    run.BASE = args.base_url.rstrip('/')
    download(run.RUN)


if __name__ == '__main__':
    main()
