"""Maintain site.schema.json optional configuration fields from configuration.py."""
import argparse
import json
from pathlib import Path
from configuration import schema_properties


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = Path(__file__).resolve().parent/'schemas/site.schema.json'
    schema = json.loads(path.read_text(encoding='utf-8'))
    properties = schema_properties()
    if args.check:
        if any(schema['properties'].get(key) != value for key, value in properties.items()):
            raise SystemExit('Stale configuration schema: run python sync_config_schema.py')
        print('PASS: configuration schema matches runtime defaults and constraints.')
        return
    schema['properties'].update(properties)
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
