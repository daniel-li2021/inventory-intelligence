"""Acquire/attest official UCI inputs locally; keep real rows and series ignored."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from inventory_intelligence import public_sales as sales

MAX_BYTES = 64 * 1024 * 1024


def write_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    temporary.replace(path)


def verify_source(manifest, archive, workbook):
    """Fail closed on changed files/rights instead of accepting a replacement."""
    if (manifest.get("protocol_version") != sales.VERSION or manifest.get("archive_url") != sales.ARCHIVE_URL
            or manifest.get("license_url") != sales.LICENSE_URL or manifest.get("member") != sales.MEMBER):
        raise ValueError("accepted source metadata changed")
    for kind, path in (("archive", archive), ("workbook", workbook)):
        if (not path.is_file() or path.stat().st_size != manifest[kind + "_bytes"]
                or sales.sha256_file(path) != manifest[kind + "_sha256"]):
            raise ValueError(f"accepted {kind} hash/size changed")


def acquire(raw_dir):
    """One official, bounded atomic acquisition, preserving accepted source files."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive = raw_dir / "online-retail.zip"
    workbook = raw_dir / sales.MEMBER
    manifest_path = raw_dir / "source-manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        verify_source(manifest, archive, workbook)
        return manifest
    if archive.exists() or workbook.exists():
        raise ValueError("unattested existing source files; refusing replacement")
    temporary = raw_dir / "online-retail.zip.download"
    with urlopen(sales.ARCHIVE_URL, timeout=60) as response, temporary.open("wb") as output:
        final_url = response.url
        if final_url != sales.ARCHIVE_URL:
            raise ValueError("official source redirected; review the source before acceptance")
        size = 0
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("official archive exceeds bounded size")
            output.write(chunk)
    acquired_at = datetime.now(timezone.utc).isoformat()
    with ZipFile(temporary) as source:
        if source.namelist() != [sales.MEMBER] or source.getinfo(sales.MEMBER).file_size > MAX_BYTES:
            raise ValueError("official archive member schema/size changed")
        member_temp = raw_dir / "Online Retail.xlsx.download"
        with source.open(sales.MEMBER) as member, member_temp.open("wb") as output:
            while chunk := member.read(1024 * 1024):
                output.write(chunk)
    # A failed download/extraction leaves only unaccepted .download files.
    # Never replace accepted data; rename only after archive/member validation.
    temporary.rename(archive)
    member_temp.rename(workbook)
    manifest = dict(protocol_version=sales.VERSION, dataset=sales.DATASET,
        attribution=sales.ATTRIBUTION, source_url=sales.SOURCE_URL, archive_url=sales.ARCHIVE_URL,
        response_url=final_url, license="CC BY 4.0", license_url=sales.LICENSE_URL,
        acquired_at_utc=acquired_at, member=sales.MEMBER,
        archive_sha256=sales.sha256_file(archive), archive_bytes=archive.stat().st_size,
        workbook_sha256=sales.sha256_file(workbook), workbook_bytes=workbook.stat().st_size)
    write_json(manifest_path, manifest)
    return manifest


def prepare(raw_dir, *, allow_acquisition=False):
    """Reuse an attested extraction; a new adapter hash gets a distinct artifact."""
    manifest_path = raw_dir / "source-manifest.json"
    if not manifest_path.exists() and not allow_acquisition:
        raise ValueError("no accepted source; use --acquire for the assigned official acquisition")
    manifest = acquire(raw_dir)
    root = Path(__file__).resolve().parents[1]
    dependencies = ("src/inventory_intelligence/public_sales.py", "scripts/public_sales_adapter.py",
                    "docs/CONTRACTS.md")
    hashes = {name: sales.sha256_file(root / name) for name in dependencies}
    transform_hash = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    derived = raw_dir / f"adapted-{transform_hash[:12]}.json"
    receipt_path = raw_dir / f"adapted-{transform_hash[:12]}.manifest.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if (receipt["archive_sha256"] != manifest["archive_sha256"]
                or receipt["transform_sha256"] != transform_hash or not derived.is_file()
                or receipt["artifact_sha256"] != sales.sha256_file(derived)):
            raise ValueError("accepted derived artifact changed")
        return receipt, derived
    if derived.exists():
        raise ValueError("unattested derived file; refusing replacement")
    adapted = sales.read_workbook(raw_dir / sales.MEMBER, archive_sha256=manifest["archive_sha256"])
    write_json(derived, adapted)
    receipt = dict(protocol_version=sales.VERSION, archive_sha256=manifest["archive_sha256"],
        transform_sha256=transform_hash, source_sha256=hashes, artifact_sha256=sales.sha256_file(derived),
        audit=adapted["audit"], observed_sales_only=True, availability="unknown",
        attribution=sales.ATTRIBUTION, source_url=sales.SOURCE_URL, license_url=sales.LICENSE_URL)
    write_json(receipt_path, receipt)
    return receipt, derived


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/uci-online-retail"))
    parser.add_argument("--acquire", action="store_true")
    args = parser.parse_args()
    receipt, path = prepare(args.raw_dir, allow_acquisition=args.acquire)
    print(json.dumps(dict(status=receipt["audit"]["status"], reasons=receipt["audit"]["reasons"],
                         counts=receipt["audit"]["counts"], local_artifact=str(path)), sort_keys=True))


if __name__ == "__main__":
    main()
