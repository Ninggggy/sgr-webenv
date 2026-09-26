"""Synthetic counts only; exercise public query semantics without research data."""
import importlib.util
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wonder_query', ROOT / 'environments/wonder/app/query.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class Protection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data = patch.object(w, 'DATA', Path(self.tmp.name))
        self.data.start()
        self.addCleanup(self.data.stop)
        self.catalog = patch.object(w, 'catalog', return_value={
            'linked': {'years': ['2020', '2021'], 'records': []}})
        self.catalog.start()
        self.addCleanup(self.catalog.stop)
        for year in ('2020', '2021'):
            with closing(sqlite3.connect(Path(self.tmp.name) / f'linked-{year}.sqlite')) as c, c:
                c.execute('CREATE TABLE births(year TEXT, sex TEXT, n INTEGER, weight_micro INTEGER)')
                c.execute('CREATE TABLE deaths(year TEXT, sex TEXT, cause_leaf TEXT, n INTEGER, weight_micro INTEGER)')
                c.executemany('INSERT INTO births VALUES (?,?,?,?)', [(year, sex, 1000, 1000000000) for sex in ('M', 'F')])

    def seed(self, leaf, count, year='2021', sex='M', micro=None):
        with closing(sqlite3.connect(Path(self.tmp.name) / f'linked-{year}.sqlite')) as c, c:
            c.execute('INSERT INTO deaths VALUES (?,?,?,?,?)', (year, sex, leaf, count, count * 1000000 if micro is None else micro))

    def run_query(self, causes=None, groups=None, years=None, **options):
        filters = {'year': years or ['2021']}
        if causes is not None:
            filters['cause'] = causes
        return w.query({'dataset': 'linked', 'groups': groups or ['cause'],
                        'filters': filters, 'show_zeros': True, **options})

    def rows(self, result):
        return {tuple(r['codes'][g] for g in result['query']['groups']): r for r in result['rows']}

    def test_small_count_and_reliability_boundaries(self):
        # Separate leaves avoid overlapping totals; values are wholly synthetic.
        leaves = ['GR130-013', 'GR130-014', 'GR130-015', 'GR130-016', 'GR130-017', 'GR130-018']
        for leaf, count in zip(leaves, [0, 1, 9, 10, 19, 20]):
            self.seed(leaf, count)
        rows = self.rows(self.run_query(leaves))
        for leaf, count in zip(leaves, [0, 1, 9, 10, 19, 20]):
            r = rows[(leaf,)]
            if count in (1, 9):
                self.assertTrue(all(v is None for v in r['values'].values()))
                self.assertEqual(set(r['status'].values()), {'Suppressed'})
            else:
                self.assertEqual(r['values']['deaths'], str(count))
                self.assertEqual(r['values']['births'], '2000')
                self.assertEqual(r['status']['rate'], 'Unreliable' if count < 20 else 'Available')

    def test_round_after_aggregation(self):
        self.seed('GR130-016', 4, micro=4400000)
        self.seed('GR130-016', 5, micro=5100000)
        r = self.rows(self.run_query(['GR130-016']))[('GR130-016',)]
        self.assertEqual(r['values'], {'deaths': '10', 'births': '2000', 'rate': '5.00'})
        self.assertEqual(r['status']['rate'], 'Unreliable')

    def test_parent_selection_overlap_and_unrelated_branch(self):
        self.seed('GR130-016', 2)
        self.seed('GR130-018', 30)
        self.seed('GR130-034', 40)
        alone = self.rows(self.run_query(['GR130-012']))
        self.assertEqual(alone[('GR130-012',)]['values']['deaths'], '32')
        r = self.run_query(['GR130-001', 'GR130-012', 'GR130-016', 'GR130-018', 'GR130-033'])
        rows = self.rows(r)
        for code in ['GR130-001', 'GR130-012', 'GR130-016']:
            self.assertEqual(set(rows[(code,)]['status'].values()), {'Suppressed'})
        self.assertEqual(rows[('GR130-018',)]['values']['deaths'], '30')
        self.assertEqual(rows[('GR130-033',)]['values']['deaths'], '40')
        self.assertFalse(r['totals_enabled'])
        self.assertEqual(r['subtotals'], [])
        self.assertTrue(all(v is None for v in r['total']['values'].values()))

    def test_year_and_population_do_not_share_protection(self):
        for year, sex, small in [('2020', 'M', 2), ('2020', 'F', 20), ('2021', 'M', 20), ('2021', 'F', 20)]:
            self.seed('GR130-016', small, year, sex)
            self.seed('GR130-018', 30, year, sex)
        for groups in [['year', 'sex', 'cause'], ['cause', 'year', 'sex']]:
            r = self.run_query(['GR130-012', 'GR130-016', 'GR130-018'], groups, ['2020', '2021'])
            for row in r['rows']:
                c = row['codes']
                protected = c['year'] == '2020' and c['sex'] == 'M' and c['cause'] in ['GR130-012', 'GR130-016']
                self.assertEqual(row['status']['deaths'] == 'Suppressed', protected)
                if not protected:
                    self.assertEqual(row['values']['births'], '1000')

    def test_hidden_rows_do_not_unprotect_parent(self):
        self.seed('GR130-016', 2)
        self.seed('GR130-018', 30)
        selected = ['GR130-012', 'GR130-016', 'GR130-018']
        full = self.run_query(selected)
        hidden = self.run_query(selected, show_suppressed=False)
        self.assertEqual(hidden['rows'], [r for r in full['rows'] if not all(s == 'Suppressed' for s in r['status'].values())])
        reverse = self.run_query(list(reversed(selected)))
        self.assertEqual(full['rows'], reverse['rows'])

    def test_multiple_suppressed_descendants_keep_ancestor_protection(self):
        for leaf, count in [('GR130-016', 2), ('GR130-017', 3), ('GR130-018', 30)]:
            self.seed(leaf, count)
        r = self.rows(self.run_query(['GR130-012', 'GR130-016', 'GR130-017', 'GR130-018']))
        self.assertEqual(r[('GR130-012',)]['status']['deaths'], 'Suppressed')

    def test_single_suppressed_component_protects_total(self):
        self.seed('GR130-018', 2, sex='M')
        self.seed('GR130-018', 30, sex='F')
        r = self.run_query(groups=['sex'])
        self.assertEqual(r['total']['status']['deaths'], 'Suppressed')
        self.assertIsNone(r['total']['values']['rate'])

    def test_multiple_suppressed_components_do_not_force_total(self):
        self.seed('GR130-018', 6, sex='M')
        self.seed('GR130-018', 7, sex='F')
        r = self.run_query(groups=['sex'])
        self.assertEqual(r['total']['values']['deaths'], '13')
        self.assertEqual(r['total']['status']['rate'], 'Unreliable')


if __name__ == '__main__':
    unittest.main()
