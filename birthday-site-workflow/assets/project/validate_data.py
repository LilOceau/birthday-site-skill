"""Read-only validation of the three configuration files and referenced assets."""
import sys
sys.dont_write_bytecode = True
from project_lib import load_configuration


def main():
    try:
        load_configuration()
    except (ValueError, OSError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print('PASS: data format v1, album references and local assets are valid.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
