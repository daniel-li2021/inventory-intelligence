"""Bounded inspection of persisted evidence without loading whole reports in Python.

Pages do not waive whole-report semantic validation or authorize decisions.
"""
import json
from uuid import UUID
from psycopg.pq import TransactionStatus
from psycopg.rows import dict_row
from .planning_runs import exact_json
from .product import archive_digest

VERSION = 'persisted-evidence-page-v1'
MAX_PAGE_BYTES = 256*1024
SECTIONS = {'projection': ['projection'], 'training': ['training','days'],
            'candidate_training': ['candidates'], 'holdout_training': ['holdout','training','days']}


def read_page(conn, run_id, kind, section, *, page=1, page_size=50, expected_binding=None, candidate=None):
    run_id = str(UUID(str(run_id)))
    if (kind not in ('reliability','planning') or type(page) is not int or not 1<=page<=1000000 or
        type(page_size) is not int or not 1<=page_size<=100):
        raise ValueError('Bounded explicit evidence page required')
    if (kind=='reliability' and section!='findings') or (kind=='planning' and section not in SECTIONS):
        raise ValueError('Unsupported evidence section')
    if section=='candidate_training':
        if type(candidate) is not int or not 0<=candidate<=100000: raise ValueError('Explicit candidate ordinal required')
        path=['candidates',str(candidate),'training','days']
    else:
        if candidate is not None: raise ValueError('Candidate only applies to candidate_training')
        path=SECTIONS.get(section)
    if not conn.autocommit or conn.info.transaction_status != TransactionStatus.IDLE:
        raise ValueError('Idle autocommit connection required')
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        cur.execute("SET LOCAL statement_timeout='5s'")
        if cur.execute('SELECT current_user AS name').fetchone()['name']!='ii_runner':
            raise ValueError('Restricted ii_runner required')
        if kind=='planning':
            cur.execute('''SELECT CASE WHEN octet_length((to_jsonb(r)-'result')::text)<=65536
                THEN to_jsonb(r)-'result' END AS metadata,octet_length(result::text) AS report_bytes,
                encode(sha256(convert_to(result::text,'UTF8')),'hex') AS content_digest,
                jsonb_typeof(result #> %s) AS section_type,
                CASE WHEN jsonb_typeof(result #> %s)='array' THEN jsonb_array_length(result #> %s) END AS total_rows
                FROM planning.runs r WHERE run_id=%s''',(path,path,path,run_id))
            metadata=cur.fetchone()
            if metadata is None: raise ValueError('Unknown planning run')
            if metadata['metadata'] is None: raise ValueError('Oversized evidence metadata')
            metadata = metadata.pop('metadata') | metadata
            if metadata['section_type']!='array': raise ValueError('Section is absent or not an array; missing is not empty')
        else:
            cur.execute('SELECT CASE WHEN octet_length(to_jsonb(r)::text)<=65536 THEN to_jsonb(r) END AS metadata FROM reliability.runs r WHERE run_id=%s',(run_id,))
            metadata=cur.fetchone()
            if metadata is None: raise ValueError('Unknown reliability run')
            if metadata['metadata'] is None: raise ValueError('Oversized evidence metadata')
            metadata = metadata['metadata']
            metadata['checks']=cur.execute('SELECT rule_id,status FROM reliability.check_results WHERE run_id=%s ORDER BY rule_id COLLATE "C"',(run_id,)).fetchall()
            aggregate=cur.execute('''SELECT count(*) AS total_rows,coalesce(sum(octet_length(row_to_json(f)::text)),0) AS report_bytes,
                encode(sha256(convert_to(coalesce(string_agg(encode(sha256(convert_to(row_to_json(f)::text,'UTF8')),'hex'),'' ORDER BY finding_id COLLATE "C"),''),'UTF8')),'hex') AS content_digest
                FROM reliability.findings f WHERE run_id=%s''',(run_id,)).fetchone()
            metadata.update(aggregate)
        metadata=exact_json(metadata)
        binding=archive_digest(dict(kind=kind,section=section,candidate=candidate,metadata=metadata),False)
        if expected_binding is not None and expected_binding!=binding:
            raise ValueError('Persisted evidence binding changed')
        offset=(page-1)*page_size
        if offset>=metadata['total_rows'] and not (page==1 and metadata['total_rows']==0):
            raise ValueError('Page outside complete evidence')
        if kind=='planning':
            query='''WITH entries AS (SELECT value,ordinality FROM planning.runs,
                LATERAL jsonb_array_elements(result #> %s) WITH ORDINALITY WHERE run_id=%s),
                selected AS (SELECT * FROM entries ORDER BY ordinality LIMIT %s OFFSET %s)
                SELECT coalesce(jsonb_agg(jsonb_build_object('ordinal',ordinality-1,'record',value) ORDER BY ordinality),'[]')::text AS payload
                FROM selected'''
            args=(path,run_id,page_size,offset)
        else:
            query='''WITH selected AS (SELECT * FROM reliability.findings WHERE run_id=%s
                ORDER BY finding_id COLLATE "C" LIMIT %s OFFSET %s)
                SELECT coalesce(jsonb_agg(to_jsonb(selected) ORDER BY finding_id COLLATE "C"),'[]')::text AS payload FROM selected'''
            args=(run_id,page_size,offset)
        # Check encoded size in PostgreSQL before transferring a large row to Python.
        # A single enormous evidence record remains blocked; the complete report stays intact.
        cur.execute('WITH page_data AS ('+query+') SELECT CASE WHEN octet_length(payload)<=%s THEN payload END AS payload FROM page_data', (*args,MAX_PAGE_BYTES))
        payload=cur.fetchone()['payload']
        if payload is None: raise ValueError('Evidence page exceeds 256KiB; reduce page size or inspect another supported subsection')
        rows=json.loads(payload)
        result=dict(contract_version=VERSION,kind=kind,run_id=run_id,section=section,candidate=candidate,
                    binding=binding,metadata=metadata,page=page,page_size=page_size,total_rows=metadata['total_rows'],
                    rows=rows,next_page=page+1 if offset+len(rows)<metadata['total_rows'] else None,
                    semantic_validation='inspection_only; whole-report decision gates unchanged')
        if len(json.dumps(result).encode())>MAX_PAGE_BYTES: raise ValueError('Evidence page including metadata exceeds256KiB')
        return result


if __name__ == '__main__':
    import argparse
    import os
    import psycopg
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--kind',choices=('reliability','planning'),required=True)
    parser.add_argument('--section',required=True)
    parser.add_argument('--page',type=int,default=1)
    parser.add_argument('--page-size',type=int,default=50)
    parser.add_argument('--candidate',type=int)
    parser.add_argument('--binding')
    args=parser.parse_args()
    with psycopg.connect(os.environ['DATABASE_URL'],autocommit=True) as conn:
        print(json.dumps(read_page(conn,args.run_id,args.kind,args.section,page=args.page,
                                  page_size=args.page_size,candidate=args.candidate,expected_binding=args.binding),indent=2))
