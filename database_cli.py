import argparse
import json
from contextlib import closing
from pathlib import Path

from fashion_database import ROOT, backup, connect, counts, lookup, migrate, settings


def main(arguments=None):
    parser = argparse.ArgumentParser(description='Import, query, export and back up the TikTok SQLite catalog.')
    parser.add_argument('--database', type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    imports = commands.add_parser('import')
    imports.add_argument('--videos', type=Path, required=True)
    imports.add_argument('--products', type=Path, required=True)
    query = commands.add_parser('lookup')
    query.add_argument('--pid', required=True)
    exports = commands.add_parser('export')
    exports.add_argument('--database', type=Path, default=argparse.SUPPRESS)
    exports.add_argument('--kind', choices=['all', 'videos', 'products'], default='all')
    exports.add_argument('--output-dir', type=Path, default=ROOT / 'data/exports')
    snapshots = commands.add_parser('backup')
    snapshots.add_argument('--output', type=Path, required=True)
    commands.add_parser('status')
    args = parser.parse_args(arguments)
    config_file = ROOT / 'config.local.json'
    config = json.loads(config_file.read_text(encoding='utf-8')) if config_file.exists() else {}
    database = args.database or settings(config)['path']
    if args.command == 'import':
        result = migrate(database, args.videos, args.products)
    elif args.command == 'lookup':
        result = lookup(database, args.pid)
    elif args.command == 'backup':
        backup(database, args.output)
        result = {'backup': str(args.output.resolve())}
    elif args.command == 'export':
        from fashion_excel import export_excel
        with closing(connect(database)) as db:
            workbooks = db.execute('SELECT kind,filename FROM workbooks ORDER BY kind').fetchall()
        result = [export_excel(database, row['kind'], args.output_dir / row['filename'])
                  for row in workbooks if args.kind == 'all' or args.kind == row['kind']]
    else:
        with closing(connect(database)) as db:
            result = counts(db)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
