"""Read-only loopback preview of the existing saved synthetic catalog."""
from pathlib import Path
import uvicorn
from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    catalog = root / 'docs/review/generalization-v1/generalization-two-site-v1.json.gz'
    uvicorn.run(HostedLab(create_app(catalog_path=catalog)), host='127.0.0.1', port=8041, access_log=False)
