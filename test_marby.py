"""Dependency-free tests. Run: python -m unittest -v test_marby.py"""
import json
import tempfile
import time
import unittest
from pathlib import Path
from coin_changer_hardware import Storage, PulseCounter, HardwareFault


class TestHardware(unittest.TestCase):
    def storage(self, folder):
        return Storage({'journal_file': str(Path(folder) / 'transactions.json'),
                        'inventory_file': str(Path(folder) / 'inventory.json')})

    def test_pulses(self):
        p = PulseCounter(gap_s=.1, min_edge_s=.02)
        p.edge(); p.edge()    # bounce is ignored
        self.assertIsNone(p.drain())
        p.last = time.monotonic() - .15
        self.assertEqual(p.drain(), (1, False))

    def test_complete_transaction(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.storage(d)
            s.inventory = {'1': 10, '5': 10, '10': 5, '20': 5}
            from coin_changer_hardware import atomic_json
            atomic_json(s.inventory_path, s.inventory)
            s.receive('bill', 50)
            self.assertFalse(self.storage(d).can_pay({20: 6}))
            s.start({20: 2, 10: 1})
            for c in (20, 20, 10):
                s.confirmed(c)
            s.complete()
            self.assertEqual(s.state['status'], 'completed')
            self.assertEqual(self.storage(d).inventory['20'], 3)
            self.assertEqual(self.storage(d).inventory['10'], 4)

    def test_recovery_blocks_replay(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.storage(d)
            s.receive('coin', 5)
            self.assertTrue(self.storage(d).unresolved)
            s.start({1: 5}) if s.can_pay({1: 5}) else None
            self.assertTrue(self.storage(d).unresolved)

    def test_quarter_coin_fifth_servo_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.storage(d)
            s.inventory = {'0.25': 400, '1': 0, '5': 0, '10': 0, '20': 0}
            self.assertTrue(s.can_make_exact(100))
            self.assertTrue(s.can_pay({0.25: 4}))
            s.receive('coin', 1)
            s.start({0.25: 4})
            for _ in range(4):
                s.confirmed(0.25)
            s.complete()
            self.assertEqual(s.inventory['0.25'], 396)

    def test_operator_reconciliation_reopens_journal(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.storage(d)
            s.receive('coin', 5)
            s.fault('jam')
            s.state['status'] = 'reconciled'
            from coin_changer_hardware import atomic_json
            atomic_json(s.path, s.state)
            reopened = self.storage(d)
            self.assertFalse(reopened.unresolved)
            reopened.receive('coin', 1)
            self.assertEqual(reopened.state['credit'], 1)

    def test_not_enough_stock(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.storage(d)
            self.assertFalse(s.ready_for_source('coin', [1, 5, 10]))
            s.inventory = {'1': 100, '5': 0, '10': 0, '20': 0}
            self.assertTrue(s.ready_for_source('coin', [1, 5, 10]))
            self.assertTrue(s.can_make_exact(99))
            self.assertFalse(s.can_make_exact(101))

    def test_reject_bad_value(self):
        with tempfile.TemporaryDirectory() as d:
            s = self.storage(d)
            s.receive('bill', 100)
            with self.assertRaises(HardwareFault):
                s.start({20: 4})

if __name__ == '__main__':
    unittest.main()
