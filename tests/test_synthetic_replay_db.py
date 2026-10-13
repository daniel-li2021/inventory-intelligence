"""Real PostgreSQL controls in a fresh, isolated synthetic database."""
from copy import deepcopy
from pathlib import Path
import json
import os
import unittest
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from inventory_intelligence.synthetic_replay import admit, replay, source_tables
from inventory_intelligence.product import archive_digest

ROOT=Path(__file__).resolve().parents[1]


class ReplayDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options=conninfo_to_dict(os.environ['TEST_DATABASE_URL'])
        cls.admin=psycopg.connect(os.environ['TEST_DATABASE_URL'],autocommit=True)
        cls.db='ii_replay_test_'+uuid4().hex[:12]
        cls.admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(cls.db)))
        cls.owner=psycopg.connect(make_conninfo(**(options|dict(dbname=cls.db))),autocommit=True)
        cls.runner=psycopg.connect(make_conninfo(**(conninfo_to_dict(os.environ['DATABASE_URL'])|dict(dbname=cls.db))),autocommit=True)
        for filename in ('schema.sql','planning_schema.sql'):cls.owner.execute((ROOT/'sql'/filename).read_text())
        cls.sources=json.loads((ROOT/'docs/examples/dynamic-controls-v1.json').read_text())
        cls.archive=replay(cls.owner,cls.runner,cls.sources)

    @classmethod
    def tearDownClass(cls):
        cls.owner.close();cls.runner.close()
        cls.admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(cls.db)))
        cls.admin.close()

    def test_idempotent_admission_and_new_report_replay(self):
        before=self.owner.execute('SELECT count(*) FROM operational_fixture.batches').fetchone()[0]
        admit(self.owner,self.sources)
        self.assertEqual(self.owner.execute('SELECT count(*) FROM operational_fixture.batches').fetchone()[0],before)
        second=replay(self.owner,self.runner,self.sources)
        self.assertEqual([b['source_digest'] for b in second['cutoffs']],[b['source_digest'] for b in self.archive['cutoffs']])
        self.assertTrue(set(second['reports']).isdisjoint(self.archive['reports']))
        self.assertEqual(self.owner.execute('SELECT count(*) FROM operational_fixture.batches').fetchone()[0],before)

    def test_conflicting_identity_rolls_back_entire_admission(self):
        changed=deepcopy(self.sources[:2]);changed[0]['version_id']='new-version'
        changed[1]['keys'][0]['stock']+=1
        stem,_=source_tables(changed[0])
        with self.assertRaises(ValueError):admit(self.owner,changed)
        self.assertIsNone(self.owner.execute('SELECT digest FROM synthetic_replay.sources WHERE version_id=%s',('new-version',)).fetchone())
        self.assertEqual(self.owner.execute('SELECT count(*) FROM operational_fixture.batches WHERE batch_id=%s',(stem+':ledger',)).fetchone()[0],0)

    def test_sources_immutable_and_runner_has_no_write_permission(self):
        stem,_=source_tables(self.sources[0])
        with self.assertRaises(psycopg.Error):self.owner.execute('UPDATE operational_fixture.snapshots SET on_hand_qty=0 WHERE batch_id=%s',(stem+':snapshot',))
        with self.assertRaises(psycopg.Error):self.owner.execute('DELETE FROM synthetic_replay.sources')
        with self.assertRaises(psycopg.Error):self.runner.execute('DELETE FROM operational_fixture.snapshots')
        with self.assertRaises(psycopg.Error):self.runner.execute('CREATE TABLE synthetic_replay.unauthorized (value integer)')
        self.assertEqual(self.owner.execute('SELECT count(*) FROM synthetic_replay.sources').fetchone()[0],3)

    def test_original_source_rows_survive_reopen(self):
        with psycopg.connect(self.owner.info.dsn,autocommit=True) as conn:
            for source in self.sources:
                digest,payload=conn.execute('SELECT digest,payload FROM synthetic_replay.sources WHERE dataset_id=%s AND version_id=%s',(source['dataset_id'],source['version_id'])).fetchone()
                self.assertEqual((digest,payload),(archive_digest(source,False),source))

    def test_first_admission_refuses_an_occupied_database(self):
        options=conninfo_to_dict(self.owner.info.dsn);name='ii_replay_occupied_'+uuid4().hex[:12]
        self.admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
        try:
            with psycopg.connect(make_conninfo(**(options|dict(dbname=name))),autocommit=True) as conn:
                for filename in ('schema.sql','planning_schema.sql'):conn.execute((ROOT/'sql'/filename).read_text())
                conn.execute("INSERT INTO operational_fixture.styles VALUES ('sentinel','S','Retain existing data')")
                with self.assertRaises(ValueError):admit(conn,self.sources)
                self.assertIsNone(conn.execute("SELECT to_regnamespace('synthetic_replay')").fetchone()[0])
                self.assertEqual(conn.execute('SELECT style_id FROM operational_fixture.styles').fetchall(),[('sentinel',)])
        finally:self.admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))

if __name__=='__main__':unittest.main()
