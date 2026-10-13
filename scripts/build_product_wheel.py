"""Build a wheel in a clean source tree; reject stale or omitted UI assets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def verify_assets(wheel, root=ROOT):
    expected = {path.name: path.read_bytes() for path in
                (root/'src/inventory_intelligence/product_static').iterdir() if path.is_file()}
    with ZipFile(wheel) as archive:
        prefix = 'inventory_intelligence/product_static/'
        actual = {name[len(prefix):]: archive.read(name) for name in archive.namelist()
                  if name.startswith(prefix) and not name.endswith('/')}
        if actual != expected:
            raise ValueError('Wheel UI assets differ from the current built frontend')
        evidence = archive.read('inventory_intelligence/product_evidence.json.gz')
        if evidence != (root/'src/inventory_intelligence/product_evidence.json.gz').read_bytes():
            raise ValueError('Wheel evidence differs from the validated product archive')
    return sorted(actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    with tempfile.TemporaryDirectory(prefix='ii-product-build-') as directory:
        clean = Path(directory)
        for name in ('pyproject.toml', 'README.md'):
            shutil.copyfile(ROOT/name, clean/name)
        shutil.copytree(ROOT/'src', clean/'src', ignore=shutil.ignore_patterns('__pycache__', '*.egg-info'))
        (clean/'sql').mkdir()
        for name in ('checks.sql', 'views.sql'):
            shutil.copyfile(ROOT/'sql'/name, clean/'sql'/name)
        subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
                        '--wheel-dir', str(clean/'wheels'), '.'], cwd=clean, check=True)
        wheels = list((clean/'wheels').glob('*.whl'))
        if len(wheels) != 1:
            raise ValueError('Expected one product wheel')
        wheel = wheels[0]
        assets = verify_assets(wheel)
        output.mkdir(parents=True, exist_ok=True)
        destination = output/wheel.name
        with destination.open('xb') as stream:
            stream.write(wheel.read_bytes())
        print(json.dumps(dict(wheel=str(destination), sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                              assets=assets, evidence_matches=True)))


if __name__ == '__main__':
    main()
