import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse, quote
import oss2
import requests

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--video',type=Path,required=True)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--key',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    assert args.key.startswith('Goumee-ComfyUI-Server-Data/public/servers/'), 'Use the authorized public asset prefix'
    config=json.loads(args.config.read_text(encoding='utf-8-sig'))
    endpoint=config['oss_endpoint']
    if '://' not in endpoint:
        endpoint='https://'+endpoint
    endpoint_host=urlparse(endpoint).netloc.replace('-internal','')
    bucket_name=config['oss_bucket']
    bucket=oss2.Bucket(oss2.Auth(config['oss_access_key_id'],config['oss_access_key_secret']),endpoint,bucket_name)
    content=args.video.read_bytes()
    digest=hashlib.sha256(content).hexdigest()
    if bucket.object_exists(args.key):
        head=bucket.head_object(args.key)
        assert head.headers.get('x-oss-meta-sha256')==digest, 'Existing object differs; refusing overwrite'
    else:
        bucket.put_object_from_file(args.key,str(args.video),headers={'Content-Type':'video/mp4','x-oss-object-acl':'public-read','x-oss-meta-sha256':digest})
    url=f'https://{bucket_name}.{endpoint_host}/{quote(args.key, safe="/")}'
    response=requests.get(url,timeout=180)
    response.raise_for_status()
    assert response.headers.get('Content-Type','').split(';')[0]=='video/mp4'
    assert hashlib.sha256(response.content).hexdigest()==digest
    result={'url':url,'status':response.status_code,'content_type':response.headers['Content-Type'],'bytes':len(response.content),'sha256':digest,'public_unauthenticated_get_verified':True,'object_key':args.key}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':
    main()
