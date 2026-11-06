import argparse
import json
from pathlib import Path

from ops_client import ROOT, lookup, request, settings


def main(arguments=None):
    parser = argparse.ArgumentParser(description='Query and export the TikTok operations backend.')
    commands = parser.add_subparsers(dest='command', required=True)
    query = commands.add_parser('lookup')
    query.add_argument('--pid', required=True)
    exports = commands.add_parser('export')
    exports.add_argument('--kind', choices=['all', 'videos', 'products'], default='all')
    exports.add_argument('--output-dir', type=Path, default=ROOT / 'data/exports')
    commands.add_parser('status')
    args = parser.parse_args(arguments)
    config_file = ROOT / 'config.local.json'
    config = json.loads(config_file.read_text(encoding='utf-8')) if config_file.exists() else {}
    options = settings(config)
    if not options['enabled']:
        raise ValueError('Enable tiktok_ops; business database access belongs to tiktok-ops.')
    if args.command == 'lookup':
        result = lookup(options, args.pid)
    elif args.command == 'export':
        args.output_dir.mkdir(parents=True, exist_ok=True)
        result = []
        for kind in ('products', 'videos') if args.kind == 'all' else (args.kind,):
            output = args.output_dir / ('PID查询表格.xlsx' if kind == 'products' else 'BC渠道号视频.xlsx')
            output.write_bytes(request(options, '/service/export/' + kind, raw=True))
            result.append({'file': str(output.resolve())})
    else:
        result = request(options, '/service/status')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
