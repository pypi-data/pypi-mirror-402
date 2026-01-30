# import typing
import unittest
import logging

from tkmilan.validation import StaticList, StaticMap, StaticMapLabels, StaticMapValues
from tkmilan.validation import LimitBounded, LimitUnbounded
from tkmilan import fn

logger = logging.getLogger(__name__)


class Test_StaticList(unittest.TestCase):
    def test_valid(self):
        spec_basic = StaticList(['1', '2', '3'], default='2')
        with self.subTest(spec=spec_basic):
            self.assertTrue('2' in spec_basic)
            self.assertFalse('10' in spec_basic)
            self.assertEqual(len(spec_basic), 3)

    def test_errors(self):
        with self.assertRaises(ValueError):
            StaticList(['1', '2', '3'], default='5')
        with self.assertRaises(ValueError):
            StaticList(['1', '2', '3'], defaultIndex=5)


class Test_StaticMap(unittest.TestCase):
    map_basic = {'1': 1, '2': 2, '3': 3}

    def test_valid(self):
        spec_basic = StaticMap(self.map_basic, defaultLabel='2')
        with self.subTest(spec=spec_basic):
            self.assertTrue('2' in spec_basic)
            self.assertTrue(2 in spec_basic.rlabels)
            self.assertFalse('5' in spec_basic)
            self.assertFalse(5 in spec_basic.rlabels)
            self.assertEqual(len(spec_basic), 3)

    def test_valid_wrappers(self):
        spec_basic_labels = StaticMapLabels(int, tuple(self.map_basic.keys()), defaultIndex=0)
        with self.subTest(spec=spec_basic_labels):
            self.assertTrue('2' in spec_basic_labels)
            self.assertTrue(2 in spec_basic_labels.rlabels)
            self.assertFalse('5' in spec_basic_labels)
            self.assertFalse(5 in spec_basic_labels.rlabels)
            self.assertTrue('1', spec_basic_labels.ldefault)
        spec_basic_values = StaticMapValues(str, tuple(self.map_basic.values()), defaultIndex=-1)
        with self.subTest(spec=spec_basic_values):
            self.assertTrue('2' in spec_basic_values)
            self.assertTrue(2 in spec_basic_values.rlabels)
            self.assertFalse('5' in spec_basic_values)
            self.assertFalse(5 in spec_basic_values.rlabels)
            self.assertTrue('3', spec_basic_values.ldefault)

    def test_errors(self):
        with self.assertRaises(ValueError):
            StaticMap(self.map_basic, defaultLabel='5')
        with self.assertRaises(ValueError):
            StaticMap(self.map_basic, defaultValue=5)
        with self.assertRaises(AssertionError):
            StaticMapLabels(str, tuple(self.map_basic.values()), defaultIndex=0)


class Test_Limit(unittest.TestCase):
    def test_int_bounded(self):
        lim_imin = LimitBounded(1, 10, fn=fn.valNumber, imin=True, imax=False)
        with self.subTest(limit=str(lim_imin)):
            self.assertTrue('1' in lim_imin)
            self.assertTrue('5' in lim_imin)
            self.assertFalse('10' in lim_imin)
        lim_imax = LimitBounded('1', '10', fn=fn.valNumber, imin=False, imax=True)
        with self.subTest(limit=str(lim_imax)):
            self.assertFalse('1' in lim_imax)
            self.assertTrue('5' in lim_imax)
            self.assertTrue('10' in lim_imax)
        lim_inone = LimitBounded('1', '10', fn=fn.valNumber, imin=False, imax=False, default='5')
        with self.subTest(limit=str(lim_inone)):
            self.assertFalse('1' in lim_inone)
            self.assertTrue('5' in lim_inone)
            self.assertFalse('10' in lim_inone)

    def test_int_bounded_step(self):
        lim_imin = LimitBounded(0, 100, step=10, fn=fn.valNumber,
                                imin=True, imax=False)
        with self.subTest(limit=lim_imin):
            self.assertTrue('0' in lim_imin)
            self.assertFalse('1' in lim_imin)
            self.assertFalse('49' in lim_imin)
            self.assertTrue('50' in lim_imin)
            self.assertFalse('51' in lim_imin)
            self.assertFalse('100' in lim_imin)
        lim_imax = LimitBounded('33', '39', step=3, fn=fn.valNumber,
                                imin=False, imax=True)
        with self.subTest(limit=lim_imax):
            self.assertFalse('33' in lim_imax)
            self.assertTrue('36' in lim_imax)
            self.assertTrue('39' in lim_imax)
        lim_inone = LimitBounded(19, 31, step=2, fn=fn.valNumber,
                                 imin=False, imax=False, default='25')
        with self.subTest(limit=lim_inone):
            self.assertFalse('19' in lim_inone)
            self.assertFalse('20' in lim_inone)
            self.assertTrue('21' in lim_inone)
            self.assertTrue('25' in lim_inone)
            self.assertTrue('29' in lim_inone)
            self.assertFalse('30' in lim_inone)
            self.assertFalse('31' in lim_inone)
            self.assertListEqual(list(lim_inone), ['21', '23', '25', '27', '29'])
        lim_iboth = LimitBounded(12, 28, step=2, fn=fn.valNumber,
                                 imin=True, imax=True)
        with self.subTest(limit=lim_iboth):
            self.assertTrue('12' in lim_iboth)
            self.assertTrue('28' in lim_iboth)
            self.assertEqual(len(lim_iboth), 1 + (28 - 12) // 2)

    def test_int_infinite(self):
        lim_nomin = LimitUnbounded(None, 10, fn=fn.valNumber)
        with self.subTest(limit=str(lim_nomin)):
            self.assertTrue('-100' in lim_nomin)
            self.assertTrue('5' in lim_nomin)
            self.assertFalse('+100' in lim_nomin)
        lim_nomax = LimitUnbounded('1', None, fn=fn.valNumber)
        with self.subTest(limit=str(lim_nomax)):
            self.assertFalse('-100' in lim_nomax)
            self.assertTrue('5' in lim_nomax)
            self.assertTrue('+100' in lim_nomax)

    def test_errors(self):
        for cls in (LimitBounded, LimitUnbounded):
            with self.assertRaises(ValueError):
                cls('1', '10', fn=fn.valNumber, imin=False, imax=False)  # Default Default 0 not in range
            with self.assertRaises(ValueError):
                # Weirdness: Strange `fn`
                cls('x', 'xxx', fn=len, default=2)  # No default roundtrip: str(2) == '2'; len('2') == 1; 1 != 2
        # Steps
        with self.assertRaises(ValueError):
            LimitBounded(1, 10, step=2, fn=fn.valNumber)  # max=6
        with self.assertRaises(ValueError):
            LimitBounded(10, 59, step=5, imax=False,      # max=60
                         fn=fn.valNumber)
        with self.assertRaises(ValueError):
            LimitUnbounded('-5', '5', step=1, fn=fn.valNumber)  # step:unsupported

    def test_padsize(self):
        lim_basic = LimitBounded(1, 0xFF, fn=fn.valNumber)
        with self.subTest(limit=str(lim_basic)):
            self.assertEqual(lim_basic.count_padsize(2), 8)
            self.assertEqual(lim_basic.count_padsize(16), 2)
        for n in range(30):
            for num in (2**n - n, 2**n, 2**n + n):
                lim = LimitBounded(1, num, fn=fn.valNumber)
                with self.subTest(limit=str(lim)):
                    self.assertEqual(lim.count_padsize(2), len(bin(num)) - 2)  # 0b
                    self.assertEqual(lim.count_padsize(8), len(oct(num)) - 2)  # 0o
                    self.assertEqual(lim.count_padsize(10), len(str(num)))
                    self.assertEqual(lim.count_padsize(16), len(hex(num)) - 2)  # 0x

    def test_fn_w(self):
        lim_b_basic = LimitBounded('-5', '5', fn=fn.valNumber)
        lim_b_basic_w = lim_b_basic.w(imin=False, default='0')
        self.assertIsNot(lim_b_basic.imin, lim_b_basic_w.imin)
        self.assertEqual(lim_b_basic.step, lim_b_basic_w.step)
        lim_b_step = LimitBounded(0, 12, step=2, fn=fn.valNumber)
        lim_b_step_w = lim_b_step.w(step=4)
        self.assertNotEqual(lim_b_step.step, lim_b_step_w.step)
        lim_u_basic = LimitUnbounded('-1/2', '1/2', fn=fn.valFraction)
        lim_u_basic_w = lim_u_basic.w(imin=False, imax=False, default='0')
        self.assertIsNot(lim_u_basic.imin, lim_u_basic_w.imin)
        self.assertIsNot(lim_u_basic.imax, lim_u_basic_w.imax)
        self.assertEqual(lim_u_basic.step, lim_u_basic_w.step)


if __name__ == '__main__':
    import sys
    logs_lvl = logging.DEBUG if '-v' in sys.argv else logging.INFO
    logging.basicConfig(level=logs_lvl, format='%(levelname)5.5s:%(funcName)s: %(message)s', stream=sys.stderr)
    unittest.main()
