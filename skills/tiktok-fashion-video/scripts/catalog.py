"""Read the configured product catalog; generation writes happen in the node."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from fashion_database import lookup, settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', required=True)
    args = parser.parse_args()
    config_file = ROOT / 'config.local.json'
    config = json.loads(config_file.read_text(encoding='utf-8')) if config_file.exists() else {}
    options = settings(config)
    if not options['enabled']:
        print(json.dumps({'catalog_enabled': False, 'next': 'Continue verified browser product lookup.'}))
        return
    print(json.dumps(lookup(options['path'], args.pid), ensure_ascii=False))


if __name__ == '__main__':
    main()
