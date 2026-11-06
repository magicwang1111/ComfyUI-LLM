import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageOps
import requests

ROOT = Path(__file__).resolve().parents[3]


def browser_config(root=ROOT):
    path = root / 'config.local.json'
    settings = json.loads(path.read_text(encoding='utf-8')).get('tiktok_browser', {}) if path.exists() else {}
    def resolve(value):
        path = Path(value).expanduser()
        return str((root / path).resolve()) if not path.is_absolute() else str(path.resolve())
    executable = settings.get('node_executable', 'node')
    if '/' in executable or '\\' in executable:
        executable = resolve(executable)
    return {
        'profile_dir': resolve(settings.get('profile_dir', '.tiktok_browser/profile')),
        'playwright_module': resolve(settings.get('playwright_module', '.tiktok_browser/node_modules/playwright')),
        'node_executable': executable,
        'channel': settings.get('channel', ''),
        'run_as_user': settings.get('run_as_user', ''),
    }


@contextmanager
def browser_lock(profile):
    import fcntl
    lock_path = Path(profile).parent / '.agent-browser.lock'
    with lock_path.open('a') as lock:
        deadline = time.monotonic() + 30
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise ValueError('商品浏览器正被其他任务使用，请稍后重试。')
                time.sleep(0.5)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def read_product(pid, config, login=False):
    if os.name != 'posix':
        raise ValueError('商品采集需在已配置浏览器的 Linux 服务器执行。')
    if not Path(config['profile_dir']).is_dir():
        raise ValueError('浏览器登录目录不存在，请先按 browser-setup.md 安装并登录店铺。')
    if not Path(config['playwright_module'], 'package.json').is_file():
        raise ValueError('Playwright 尚未安装，请运行节点的 install_tiktok_browser.sh。')
    node = shutil.which(config['node_executable'])
    if not node:
        raise ValueError('未找到 Node.js，请安装 Node.js 20+ 或配置 tiktok_browser.node_executable。')
    command = [node, str(Path(__file__).with_name('browser_collect.cjs'))]
    if config['run_as_user']:
        command = ['runuser', '-u', config['run_as_user'], '--', *command]
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(ROOT / '.tiktok_browser/browsers')
    with browser_lock(config['profile_dir']):
        result = subprocess.run(command, input=json.dumps({**config, 'pid': pid, 'login': login}),
                                text=True, encoding='utf-8', capture_output=True, timeout=1800 if login else 150, env=env)
    if result.returncode:
        raise ValueError('商品浏览器读取失败：' + result.stderr.strip()[-700:])
    product = json.loads(result.stdout)
    if login:
        return product
    if product.get('pid') != pid or not product.get('title') or not product.get('images'):
        raise ValueError('商品资料不完整或 PID 不匹配。')
    return product


def download_image(item):
    index, image, directory = item
    url = image['url']
    host = (urlsplit(url).hostname or '').lower()
    if urlsplit(url).scheme != 'https' or not any(host == domain or host.endswith('.' + domain) for domain in ('ttcdn-us.com', 'tiktokcdn-us.com', 'tiktokcdn.com', 'byteimg.com', 'ibyteimg.com')):
        raise ValueError('商品图片地址不是受支持的 TikTok HTTPS 图片域名。')
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    path = directory / f'{index:02}.jpg'
    path.write_bytes(response.content)
    with Image.open(path) as photo:
        size = list(photo.size)
        photo.verify()
    return {'index': index, 'file': path.name, 'url': url,
            'size': size, 'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}


def contact_sheet(manifest, directory, output):
    images = manifest['images']
    sheet = Image.new('RGB', (1200, 440 * ((len(images) + 2) // 3)), 'white')
    draw = ImageDraw.Draw(sheet)
    for offset, item in enumerate(images):
        with Image.open(directory / item['file']) as photo:
            thumb = ImageOps.exif_transpose(photo).convert('RGB')
            thumb.thumbnail((390, 400))
        x, y = (offset % 3) * 400, (offset // 3) * 440
        sheet.paste(thumb, (x + (400 - thumb.width) // 2, y + 30))
        draw.text((x + 10, y + 8), f"Image {item['index']:02}  {item['size'][0]} x {item['size'][1]}", fill='black')
    sheet.save(output)


def collect(pid, run_dir, output):
    if len(pid) != 19 or not pid.isascii() or not pid.isdecimal():
        raise ValueError('PID 必须是完整的 19 位数字字符串。')
    run_dir = Path(run_dir).resolve()
    output = Path(output).resolve()
    if run_dir not in output.parents:
        raise ValueError('商品预览图必须保存在本次 run-dir 内。')
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / 'status.json'
    if not status_path.exists():
        status_path.write_text(json.dumps({'stage': 'collecting_product', 'pid': pid, 'prompt_id': None, 'errors': [], 'artifacts': {}}), encoding='utf-8')
    directory = run_dir / 'product'
    directory.mkdir(exist_ok=True)
    manifest_path = directory / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest.get('pid') != pid:
            raise ValueError('本次运行目录已属于另一个 PID，请使用新任务目录。')
        for item in manifest['images']:
            if hashlib.sha256((directory / item['file']).read_bytes()).hexdigest() != item['sha256']:
                raise ValueError('已下载商品图校验失败，不能复用。')
    else:
        product = read_product(pid, browser_config())
        with ThreadPoolExecutor(max_workers=3) as pool:
            images = list(pool.map(download_image, ((i, item, directory) for i, item in enumerate(product['images'], 1))))
        manifest = {'pid': pid, 'title': product['title'], 'source_url': product['url'],
                    'verified_at': datetime.now(timezone.utc).isoformat(), 'images': images}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    contact_sheet(manifest, directory, output)
    return {'pid': pid, 'title': manifest['title'], 'manifest': str(manifest_path),
            'contact_sheet': str(output), 'images': [{'index': item['index'], 'path': str(directory / item['file']), 'size': item['size']} for item in manifest['images']]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read the exact PID from the logged-in shop and download original product images.')
    parser.add_argument('--login', action='store_true', help='Open the configured login profile on a trusted server display; close it after login.')
    parser.add_argument('--pid')
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.login:
        print(json.dumps(read_product(None, browser_config(), login=True), ensure_ascii=False))
    else:
        if not args.pid or not args.run_dir or not args.output:
            parser.error('Collection requires --pid, --run-dir and --output.')
        print(json.dumps(collect(args.pid, args.run_dir, args.output), ensure_ascii=False))
