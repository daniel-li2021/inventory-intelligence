"""Serve the packaged workbench and durable synthetic sandbox on loopback only."""
import argparse
from pathlib import Path
import uvicorn
from inventory_intelligence.lab_api import create_app
from inventory_intelligence.lab_hosted import HostedLab


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8015)
    parser.add_argument('--journal',type=Path,default=Path('output/synthetic-journal.sqlite'))
    args=parser.parse_args()
    uvicorn.run(HostedLab(create_app(journal_path=args.journal)),host='127.0.0.1',port=args.port,
                workers=1,access_log=False)


if __name__=='__main__':main()
