import asyncio
import json
from pathlib import Path

from .artifact_store import OSSArtifactStore, safe_error_message
from .fashion_database import record_generation, settings


async def record_outputs(records, job_dir, job_id, config, publish_enabled):
    options = settings(config)
    if not options['enabled']:
        return None
    result = {'records': [], 'warnings': []}
    for record in records:
        if record.kind != 'output' or record.status != 'success' or not record.content_type.startswith('video/'):
            continue
        try:
            final = Path(record.path).resolve()
            if final.name != 'final.mp4' or not final.is_relative_to(Path(job_dir).resolve()):
                continue
            if not options['path'].is_file():
                raise ValueError('视频数据库尚未初始化，请先导入两份原表。')
            run = final.parent
            publication, publication_error = None, ''
            receipt = run / 'publication.json'
            if receipt.exists():
                saved = json.loads(receipt.read_text(encoding='utf-8'))
                if saved.get('sha256') == record.sha256 and saved.get('public_unauthenticated_get_verified'):
                    publication = saved
            if publication is None and publish_enabled and config.get('oss_enabled'):
                try:
                    public_config = {**config, 'oss_prefix': options.get('public_oss_prefix', 'Goumee-ComfyUI-Server-Data/public/servers/comfyui-llm')}
                    store = OSSArtifactStore(public_config)
                    publication = await store.publish_public_video(record, job_id, config.get('oss_endpoint', 'https://oss-cn-hangzhou.aliyuncs.com'))
                    receipt.write_text(json.dumps(publication, ensure_ascii=False, indent=2), encoding='utf-8')
                except Exception as exc:
                    publication_error = safe_error_message(exc)
                    result['warnings'].append('永久视频链接发布失败，仍保留数据库记录：' + publication_error)
            saved = await asyncio.to_thread(record_generation, options['path'], run, record.disk_dict(),
                                             options['sheet'], publication, publication_error)
            result['records'].append(saved)
        except Exception as exc:
            result['warnings'].append('视频已输出，但数据库写入失败：' + safe_error_message(exc))
    return result
