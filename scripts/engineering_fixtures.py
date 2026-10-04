"""Frozen synthetic engineering pilot inputs; never derive truth from the engine."""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json

from psycopg import sql

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
CUTOFF = BASE + timedelta(days=1)
START = date(2025, 7, 6)
ORIGIN_DAY = START + timedelta(days=180)
# This interval ends in winter: hand-specified Pacific midnight, not adapter output.
ORIGIN = datetime(2026, 1, 2, 8, tzinfo=timezone.utc)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def digest(value):
    return sha256(encoded(value)).hexdigest()


def copy_rows(conn, schema, table, rows):
    with conn.cursor().copy(sql.SQL("COPY {}.{} FROM STDIN").format(
            sql.Identifier(schema), sql.Identifier(table))) as stream:
        for row in rows:
            stream.write_row(row)


def allocation(keys, movements, shape):
    if keys < 1 or movements < 0 or movements % keys:
        raise ValueError("uniform controls require integral movements/key")
    if shape == "skew":
        if keys % 100 or movements % 5:
            raise ValueError("skew requires exact 1% keys and 80% rows")
        hot = keys // 100
        def split(total, n):
            q, r = divmod(total, n)
            return [q + (i < r) for i in range(n)]
        return split(movements * 4 // 5, hot) + split(movements // 5, keys-hot)
    return [movements // keys] * keys


def grain(prefix, k, warehouses):
    return f"{prefix}:sku:{k//warehouses}", f"{prefix}:wh:{k%warehouses}"


def inventory_manifest(prefix, keys, movements, *, shape="uniform", warehouses=1,
                       defect_rows=0, opening=1000, cutoff=CUTOFF, quantity_probe=False):
    counts = allocation(keys, movements, shape)
    if keys % warehouses or shape == "transfer" and (warehouses < 2 or warehouses % 2
            or any(n % 10 for n in counts)):
        raise ValueError("transfer grains require paired warehouses and exact 20% legs")
    if shape == "exclusions" and any(n % 20 for n in counts):
        raise ValueError("each exclusion class requires exactly 5% rows/key")
    if defect_rows < 0 or defect_rows > movements or defect_rows % 2:
        raise ValueError("duplicate defects are complete pairs within raw row count")
    quantities = []
    for k, n in enumerate(counts):
        contribution = n
        if shape == "exclusions":
            contribution = n * 17 // 20
        elif shape == "transfer":
            contribution = n * 4 // 5 + (-3 if k % 2 == 0 else 3) * (n // 5)
        quantities.append([*grain(prefix, k, warehouses), opening+contribution])
    # Duplicates are first d rows, paired consecutively; all pilot counts/key even.
    if defect_rows and any(n % 2 for n in counts):
        raise ValueError("duplicate pairs may not cross key boundaries")
    groups = [[f"{prefix}:m:{i}", f"{prefix}:m:{i+1}"] for i in range(0, defect_rows, 2)]
    blocked, consumed = [], 0
    for k, n in enumerate(counts):
        if consumed < defect_rows and n:
            blocked.append(list(grain(prefix, k, warehouses)))
        consumed += n
    return dict(version="engineering-pilot-v1", prefix=prefix, keys=keys, movements=movements,
        quantity_probe=quantity_probe,
        warehouses=warehouses, skus=keys//warehouses, shape=shape, counts=counts,
        opening=opening, cutoff=cutoff.isoformat(), raw_snapshots=keys,
        eligible_movements=movements*17//20 if shape=="exclusions" else movements,
        exclusions={c:movements//20 for c in ("pending","future_effective","above_watermark")}
            if shape=="exclusions" else {},
        expected_quantities=quantities, duplicate_groups=groups, blocked_keys=blocked,
        expected_checks={f"R00{i}": "fail" if i==1 and quantity_probe else "not_assessable" if i==1 and groups else
            "fail" if i==2 and groups else "pass" for i in range(1,6)},
        expected_status="fail" if groups or quantity_probe else "pass")


def load_inventory(conn, manifest, *, reuse_references=False, natural_prefix=None):
    p, counts, wh = manifest["prefix"], manifest["counts"], manifest["warehouses"]
    cutoff = datetime.fromisoformat(manifest["cutoff"])
    baseline = cutoff-timedelta(days=1)
    natural = natural_prefix or p
    with conn.transaction():
        if not reuse_references:
            copy_rows(conn,"operational_fixture","styles",[(p+":style",p+":style","Synthetic pilot")])
            copy_rows(conn,"operational_fixture","skus",(
                (f"{p}:sku:{i}",p+":style",f"{p}:sku:{i}","navy","M","each")
                for i in range(manifest["skus"])))
            copy_rows(conn,"operational_fixture","warehouses",(
                (f"{p}:wh:{i}",f"{p}:wh:{i}","Synthetic pilot") for i in range(wh)))
        copy_rows(conn,"operational_fixture","batches",[
            (p+":ledger","ledger","complete",baseline,cutoff,100,cutoff,manifest["movements"]),
            (p+":snapshot","snapshot","complete",None,cutoff,100,cutoff,manifest["keys"])])
        copy_rows(conn,"operational_fixture","coverage",(
            (f"{p}:c:{kind}:{k}",p+":"+kind,*q[:2])
            for kind in ("ledger","snapshot") for k,q in enumerate(manifest["expected_quantities"])))
        copy_rows(conn,"operational_fixture","opening_balances",(
            (f"{p}:o:{k}",p+":ledger",*q[:2],manifest["opening"],baseline,"pilot-v1")
            for k,q in enumerate(manifest["expected_quantities"])))
        copy_rows(conn,"operational_fixture","snapshots",(
            (f"{p}:s:{k}",p+":snapshot",*q[:2],q[2]+int(manifest["quantity_probe"]),cutoff,100,cutoff)
            for k,q in enumerate(manifest["expected_quantities"])))
        def movements():
            offset = 0
            for k,n in enumerate(counts):
                for j in range(n):
                    i = offset+j
                    event = i//2 if i < 2*len(manifest["duplicate_groups"]) else i
                    event = f"{natural}:event:{'duplicate' if i < 2*len(manifest['duplicate_groups']) else 'normal'}:{event}"
                    qty, kind, status, effective, seq, transfer = 1,"receipt","posted",cutoff,1,None
                    if manifest["shape"]=="exclusions":
                        if j < n//20: status="pending"
                        elif j < n//10: effective=cutoff+timedelta(microseconds=1)
                        elif j < n*3//20: seq=101
                    elif manifest["shape"]=="transfer" and j < n//5:
                        qty,kind=(-3 if k%2==0 else 3),"transfer"
                        transfer=f"{natural}:transfer:{k//2}:{j}"
                        event=transfer
                    sku,warehouse=manifest["expected_quantities"][k][:2]
                    yield (f"{p}:m:{i}",p+":ledger","pilot",event,"synthetic", "1",
                        f"{natural}:wh:{k%wh}",sku,warehouse,qty,kind,status,effective,
                        min(effective,cutoff),seq,cutoff,transfer,None,"synthetic engineering pilot")
                offset += n
        copy_rows(conn,"operational_fixture","movements",movements())


def verify_inventory(report, manifest):
    if report["overall_status"] != manifest["expected_status"]:
        raise AssertionError("overall status differs from frozen oracle")
    if {c["rule_id"]:c["status"] for c in report["checks"]} != manifest["expected_checks"]:
        raise AssertionError("rule status differs from frozen oracle")
    if manifest["quantity_probe"]:
        expected={tuple(q[:2]):q[2] for q in manifest["expected_quantities"]}
        actual={(f["sku_id"],f["warehouse_id"]):f["expected_qty"] for f in report["findings"]}
        if actual!=expected or len(report["findings"])!=manifest["keys"]:
            raise AssertionError("every key must match independently frozen integer balance")
        if any((f["rule_id"],f["reason"],f["observed_qty"],f["delta_qty"]) !=
                ("R001","quantity_mismatch",f["expected_qty"]+1,1) for f in report["findings"]):
            raise AssertionError("exact quantity/delta probe differs")
        return
    expected = sorted(manifest["duplicate_groups"])
    actual = sorted(f["source_row_ids"] for f in report["findings"])
    if actual != expected or any((f["rule_id"],f["reason"]) !=
            ("R002","duplicate_movement_key") for f in report["findings"]):
        raise AssertionError("exact defect identities differ from frozen oracle")
    if any(any(f[k] is not None for k in ("expected_qty","observed_qty","delta_qty"))
            for f in report["findings"]):
        raise AssertionError("blocked defect cannot invent quantities")


def source_digest(conn):
    """Stream all source rows, including references/history, in canonical table order."""
    h = sha256()
    for schema,tables in (("operational_fixture",("styles","skus","warehouses","batches",
            "coverage","opening_balances","movements","snapshots")),
            ("planning_input",("demand_batches","order_versions","day_observations",
             "supply_batches","reservations","inbound","policies"))):
        for table in tables:
            h.update(f"{schema}.{table}\n".encode())
            key = "style_id" if table=="styles" else "sku_id" if table=="skus" else \
                "warehouse_id" if table=="warehouses" else "batch_id" if table.endswith("batches") else "row_id"
            with conn.cursor().copy(sql.SQL("COPY (SELECT row_to_json(t)::text FROM {}.{} t ORDER BY {}) TO STDOUT")
                    .format(sql.Identifier(schema),sql.Identifier(table),sql.Identifier(key))) as stream:
                for block in stream: h.update(block)
    return h.hexdigest()


def load_demand(conn, prefix, keys, *, blocked=False):
    """180 days/key, 54 zeros, 126 positive lines; exact global revision allocation."""
    from zoneinfo import ZoneInfo
    pacific=ZoneInfo("America/Los_Angeles")
    positive=keys*126
    with conn.transaction():
        copy_rows(conn,"planning_input","demand_batches",[(prefix+":demand","pilot-v1",
            "America/Los_Angeles",START,ORIGIN_DAY,ORIGIN,"complete",
            positive+positive//20+positive//100,keys*180)])
        def days():
            for k in range(keys):
                for i in range(180):
                    day=START+timedelta(days=i)
                    closed=datetime.combine(day+timedelta(days=1),datetime.min.time(),pacific)
                    yield (f"{prefix}:day:{k}:{i}",prefix+":demand",*grain(prefix,k,1),day,1,
                        closed,closed,"complete","stockout" if blocked and i==0 else "available",int(i%10>=3))
        copy_rows(conn,"planning_input","day_observations",days())
        def orders():
            index=0
            for k in range(keys):
                for i in range(180):
                    if i%10<3: continue
                    day=START+timedelta(days=i)
                    accepted=datetime.combine(day,datetime.min.time(),pacific)+timedelta(hours=12)
                    common=(prefix+":demand","pilot",f"{prefix}:order:{k}:{i}","1")
                    for revision in (1,2,3):
                        if revision==2 and (index+1)%20: continue
                        if revision==3 and (index+1)%100: continue
                        recorded=ORIGIN+timedelta(days=1) if revision==3 else accepted+timedelta(hours=revision-1)
                        yield (f"{prefix}:order:{k}:{i}:r{revision}",*common,revision,
                            *grain(prefix,k,1),accepted,recorded,recorded,1000 if revision==3 else 10,"accepted")
                    index+=1
        copy_rows(conn,"planning_input","order_versions",orders())


def load_supply(conn, prefix, keys, horizon, *, incomplete=False):
    with conn.transaction():
        for k in range(keys):
            supply=f"{prefix}:supply:{horizon}:{k}"
            copy_rows(conn,"planning_input","supply_batches",[(supply,"pilot-v1",*grain(prefix,k,1),
                ORIGIN,ORIGIN,"complete",not incomplete,True,1,1)])
            copy_rows(conn,"planning_input","policies",[(supply+":policy",supply,2,horizon-2,2,6,10,ORIGIN,ORIGIN)])
            copy_rows(conn,"planning_input","reservations",[(supply+":reservation",supply,"pilot","1",3,
                ORIGIN_DAY,"open",ORIGIN,ORIGIN)])
            copy_rows(conn,"planning_input","inbound",[(supply+":inbound",supply,"pilot","1",5,
                ORIGIN_DAY+timedelta(days=1),"confirmed",ORIGIN,ORIGIN)])
