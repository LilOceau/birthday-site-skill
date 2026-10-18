"""Example project marker; this repository does not ship a media importer."""
import sys

if __name__ == '__main__':
    print('Example only: use the real importer from your existing birthday-site project. No files were changed.', file=sys.stderr)
    raise SystemExit(2)
