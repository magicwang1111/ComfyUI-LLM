import hashlib
import argparse
import json
import subprocess
import run
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--run-dir',type=Path,default=run.RUN)
parser.add_argument('--base-url',default=run.BASE)
args=parser.parse_args()
run.RUN=args.run_dir.resolve()
run.BASE=args.base_url.rstrip('/')
RUN=run.RUN
BASE=run.BASE
login,save,status=run.login,run.save,run.status

history=json.loads((RUN/'history.json').read_text(encoding='utf-8'))
item=history['outputs']['77']['images'][0]
session=login()
response=session.get(BASE+'/view',params={k:item[k] for k in ['filename','subfolder','type']},timeout=180)
response.raise_for_status()
(RUN/'final.mp4').write_bytes(response.content)
probe=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(RUN/'final.mp4')],capture_output=True,text=True,check=True)
data=json.loads(probe.stdout)
save('ffprobe.json',data)
summary={'duration':float(data['format']['duration']),'bytes':len(response.content),'sha256':hashlib.sha256(response.content).hexdigest(),'streams':[{k:s.get(k) for k in ['codec_type','codec_name','width','height','r_frame_rate','sample_rate','channels']} for s in data['streams']]}
assert abs(summary['duration']-15)<0.2
assert any(s['codec_type']=='audio' for s in summary['streams'])
save('video-summary.json',summary)
status('video_downloaded',video_summary=summary)
print(json.dumps(summary))
