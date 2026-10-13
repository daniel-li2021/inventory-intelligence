"""Validate and replay a bounded, explicitly local synthetic JSON version set."""
import argparse
import json
import os
from pathlib import Path
import time
import resource
import psycopg
from inventory_intelligence.synthetic_replay import replay, publish, INPUT_BYTES, parse_input


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--local-synthetic',action='store_true',required=True)
    args = parser.parse_args()
    if args.input.stat().st_size > 12*INPUT_BYTES: raise ValueError('input exceeds bounded version envelope')
    text = args.input.read_bytes().decode('utf-8')
    sources = parse_input(text)
    start = time.perf_counter()
    with psycopg.connect(os.environ['FIXTURE_DATABASE_URL'],autocommit=True) as owner, psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as runner:
        archive = replay(owner,runner,sources,text)
    path = publish(archive,args.output_dir)
    print(json.dumps(dict(path=str(path.resolve()),digest=archive['digest'],source_versions=len(sources),keys_per_version=len(sources[0]['keys']),saved_reports=len(archive['reports']),seconds=time.perf_counter()-start,compressed_bytes=path.stat().st_size,raw_bytes=len(json.dumps(archive,separators=(',',':')).encode()),max_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))


if __name__ == '__main__': main()
