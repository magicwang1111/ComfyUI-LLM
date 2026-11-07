import json
from pathlib import Path

from ..artifact_store import ArtifactRecord, LocalArtifactStore, publish_records
from ..fashion_delivery import record_outputs
from ..llm import format_cost_estimate


async def deliver(job, result, config):
    """Delivery can be retried using a saved worker result without running the Agent again."""
    artifacts = LocalArtifactStore(job['output_root'], job_id=job['job_id'],
                                   job_dir=job['job_dir'], flat_outputs=True)
    artifacts.records = [ArtifactRecord(**item) for item in result.get('artifacts', [])]
    is_fashion = (result['route'].get('skill_name') == 'tiktok-fashion-video'
                  or job['skill_override'] == 'tiktok-fashion-video')
    database_enabled = is_fashion and config.get('tiktok_ops', {}).get('enabled', False)
    publish = bool(job['publish_to_oss'])
    await publish_records(
        [r for r in artifacts.records if not (database_enabled and r.content_type.startswith('video/'))],
        artifacts.job_id, {**config, 'oss_enabled': bool(publish and config.get('oss_enabled'))},
    )
    database = None
    if is_fashion:
        database = await record_outputs(artifacts.records, artifacts.job_dir, artifacts.job_id,
                                        config, publish, job['identity'])
    text = result['text']
    if database:
        messages = [f"视频已保留，等待后台投递：{item['sheet']}" if item.get('pending')
                    else f"视频已入库：{item['sheet']} / {item['sequence']}" for item in database['records']]
        messages.extend(database['warnings'])
        text += '\n\n' + '\n'.join(messages)
    final = {'text': text, 'usage': result.get('usage'),
             'cost': format_cost_estimate(result.get('usage'), agent=True),
             'artifacts': [r.disk_dict() for r in artifacts.records], 'database': database}
    state = final | {'status': 'completed', 'job_id': job['job_id'], 'job_dir': job['job_dir'],
                     'route': result['route'], 'events': result.get('events', [])}
    for filename, value in [('artifacts.json', final['artifacts']), ('state.json', state)]:
        path = Path(job['job_dir']) / filename
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(path)
    return final
