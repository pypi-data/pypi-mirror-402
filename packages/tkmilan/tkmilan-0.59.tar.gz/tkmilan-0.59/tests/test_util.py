# import typing
import unittest
import logging

from tkmilan import util


class Test_Containers(unittest.TestCase):
    def test_ReorderableDict(self):
        d2 = util.ReorderableDict({n: str(n) for n in range(5)})

        # __len__
        self.assertEqual(len(util.ReorderableDict()), 0)
        self.assertEqual(len(d2), 5)
        # __iter__
        self.assertSetEqual(set(k for k in d2), set(range(5)))
        # keys
        self.assertListEqual(list(d2.keys()), list(range(5)))
        # values
        self.assertListEqual(list(d2.values()), list(map(str, range(5))))
        # items
        self.assertListEqual(list(d2.items()), list((n, str(n)) for n in range(5)))

        # index
        self.assertEqual(d2.index(4), 4)
        self.assertEqual(d2.index(10), None)
        # at
        self.assertEqual(d2.at(0), 0)
        self.assertEqual(d2.at(-1), 4)
        for n in range(len(d2)):
            self.assertEqual(d2.index(d2.at(n)), n)
        self.assertListEqual(list(d2.at(slice(0, 2))), [0, 1])
        self.assertListEqual(list(d2.at(slice(-2, None))), [3, 4])

        dc = util.ReorderableDict(d2)
        # __getitem__
        self.assertEqual(dc[4], '4')
        # clear
        dc.clear()
        self.assertEqual(len(dc), 0)
        # get
        self.assertEqual(dc.get(100, None), None)
        # __setitem__
        dc[5] = 'five'
        self.assertEqual(len(dc), 1)
        self.assertEqual(dc[5], 'five')
        self.assertEqual(dc.index(5), 0)
        # __delitem__
        dc[1] = 'one'
        self.assertEqual(dc.index(1), 1)
        del dc[1]
        self.assertEqual(len(dc), 1)

    def test_ReorderableDict_insert(self):
        di = util.ReorderableDict({n: str(n) for n in range(5)})
        di.insert(1, key=10, value='10')
        self.assertEqual(len(di), 6)
        self.assertEqual(di[10], '10')
        self.assertListEqual(list(di.keys()), [0, 10, 1, 2, 3, 4])
        di.insert(4, key=20, value='20')
        self.assertEqual(len(di), 7)
        self.assertEqual(di[20], '20')
        self.assertListEqual(list(di.keys()), [0, 10, 1, 2, 20, 3, 4])

    def test_ReorderableDict_move(self):
        dm = util.ReorderableDict({n: str(n) for n in range(5)})
        dm.move(0, key=4)
        self.assertListEqual(list(dm.items()), list((n, str(n)) for n in [4, 0, 1, 2, 3]))
        dm.move(4, key=0)
        self.assertListEqual(list(dm.items()), list((n, str(n)) for n in [4, 1, 2, 3, 0]))


if __name__ == '__main__':
    import sys
    logs_lvl = logging.DEBUG if '-v' in sys.argv else logging.INFO
    logging.basicConfig(level=logs_lvl, format='%(levelname)5.5s:%(funcName)s: %(message)s', stream=sys.stderr)
    unittest.main()
