"""Synthetic fault regressions over actual loopback HTTP/PostgreSQL apps."""
import json
import os
from pathlib import Path

import psycopg
from acceptance.http_client import Application, ApplicationError
from acceptance.runner import run
from acceptance.report import write_reports,load_report


def main():
    for mode in ('unknown_create','paired_read','known_plus_unknown','lost_ack'):
        class Adapter(Application):
            def environment(self):
                return {k:v for k,v in super().environment().items() if k in
                        {'PATH','PYTHONPATH','DATABASE_URL','ACCEPTANCE_SCHEMA','ACCEPTANCE_DISPOSABLE_DB'}}

            def create(self, conn, key, value):
                if self.version=='v2' and key==2:
                    if mode=='unknown_create': raise ApplicationError(None)
                    if mode=='known_plus_unknown': raise ApplicationError('23505')
                    if mode=='lost_ack':
                        super().create(conn,key,value)
                        raise ApplicationError(None)
                return super().create(conn,key,value)

            def read(self, conn, key):
                if mode=='paired_read' and self.version=='v2' and key==2:
                    raise ApplicationError(None)
                if mode=='known_plus_unknown' and self.version=='v1' and key==3:
                    raise ApplicationError(None)
                return super().read(conn,key)

        report=run('expand',os.environ['DATABASE_URL'],application_factory=Adapter)
        by_id={c['id']:c for c in report['checks']}
        assert report['verdict']=='INCONCLUSIVE',mode
        assert report['completed'] and report['cleanup_ok'] and len(by_id)==16,mode
        if mode=='paired_read':
            assert by_id['new_write']['write_acknowledged'] is True
            assert by_id['rollback_new_data']['status']=='PASS'
        else:
            assert by_id['new_write']['write_acknowledged'] is False
            assert by_id['rollback_new_data']['status']=='SKIP'
        with psycopg.connect(os.environ['DATABASE_URL']) as conn:
            assert not conn.execute('SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=%s)',
                                    (report['cleanup_evidence']['schema'],)).fetchone()[0]
        folder=Path('reports/dependency-regressions')/mode
        write_reports(report,folder)
        assert load_report(folder/'expand.json')==report
        print(json.dumps(dict(case=mode,verdict=report['verdict'],
                             acknowledged=by_id['new_write']['write_acknowledged'],
                             rollback=by_id['rollback_new_data']['status'],cleanup_verified=True)))


if __name__=='__main__':main()
