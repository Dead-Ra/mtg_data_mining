import unittest
from genclose_analyzer import GenCloseAnalyzer as GCA

class TestGenCloseAnalyzer(unittest.TestCase):
    def setUp(self):
        """
        Validate the developments with the indications published here:
        https://pdfs.semanticscholar.org/56a4/ec156b26225b5922182bacc4c5b26fd5a555.pdf
        """

        self.db = []
        self.db.append(['a','b','c','e','g','h'])
        self.db.append(['a','c','d','f','h'])
        self.db.append(['a','d','e','f','g','h'])
        self.db.append(['b','c','e','f','g','h'])
        self.db.append(['b','c','e'])
        self.db.append(['b','c'])

        self.analyzer = GCA([], 1)
        root = None

        a = GCA.Node(3, ('a'), ['a'], (1,2,3),root)
        b = GCA.Node(4, ('b'), ['b'], (1,4,5,6),root)
        c = GCA.Node(5, ('c'), ['c'], (1,2,4,5,6),root)
        d = GCA.Node(2, ('d'), ['d'], (2,3),root)
        e = GCA.Node(4, ('e'), ['e'], (1,3,4,5),root)
        f = GCA.Node(3, ('f'), ['f'], (2,3,4),root)
        g = GCA.Node(3, ('g'), ['g'], (1,3,4),root)
        h = GCA.Node(4, ('h'), ['h'], (1,2,3,4),root)
        self.L1 = [d,a,f,g,b,e,h,c]

        dc = GCA.Node(1, ('a','d','f','h','c'), ['d','c'], set([2]), d)
        de = GCA.Node(1, ('a', 'd', 'f', 'h', 'e'), ['d', 'e'], set([3]), d)
        dg = GCA.Node(1, ('a', 'd', 'f', 'h', 'e', 'g'), ['d', 'g'], set([3]), d)
        af = GCA.Node(2, ('a','f','h'),['a','f'], (2,3), a)
        ag = GCA.Node(2, ('a','h','e','g'),['a','g'], (1,3), a)
        ab = GCA.Node(1, ('a','h','b','c'),['a','b'], set([1]), a)
        ac = GCA.Node(2, ('a','h','c'),['a','c'], (1,2), a)
        ae = GCA.Node(2, ('a','e'),['a','e'], (1,3), a)
        gb = GCA.Node(2, ('e','g','h','b','c'),['g','b'], (1,4), g)
        gc = GCA.Node(2, ('g','c'),['g','c'], (1,4), g)
        be = GCA.Node(3, ('b','c','e'),['b','e'], (1,4,5), b)
        bh = GCA.Node(2, ('b','c','h'),['b','h'], (1,4), b)
        eh = GCA.Node(3, ('e','h'),['e','h'], (1,3,4), e)
        ec = GCA.Node(3, ('e','c'),['e','c'], (1,4,5), e)
        fg = GCA.Node(2, ('f','h','e','g'),['f','g'], (3,4), f)
        fb = GCA.Node(1, ('f','h','b','c'),['f','b'], set([4]), f)
        fc = GCA.Node(2, ('f','h','c'),['f','c'], (2,4), f)
        fe = GCA.Node(2, ('f','h','e'),['f','e'], (3,4), f)
        hc = GCA.Node(3, ('h','c'),['h','c'], (1,2,4), h)

        #Order here is important, it depends of the order at L1
        self.L2 = [dg,de,dc,af,ag,ab,ae,ac,fg,fb,fe,fc,gb,gc,be,bh,eh,ec,hc]

    def test_attribute_folders_L1(self):
        self.analyzer.attribute_folders(self.L1, 1)
        self.assertEqual(len(self.analyzer.L_folders), len(self.L1))

    def test_attribute_folders_L2(self):
        self.analyzer.attribute_folders(self.L2, 2)
        folders = self.analyzer.L_folders
        self.assertEqual(len(folders[GCA.key_folder(['a'])]), 5)
        self.assertEqual(len(folders[GCA.key_folder(['b'])]), 2)
        self.assertEqual(len(folders[GCA.key_folder(['d'])]), 3)
        self.assertEqual(len(folders[GCA.key_folder(['e'])]), 2)
        self.assertEqual(len(folders[GCA.key_folder(['f'])]), 4)
        self.assertEqual(len(folders[GCA.key_folder(['g'])]), 2)
        self.assertEqual(len(folders[GCA.key_folder(['h'])]), 1)
        self.assertNotIn(GCA.key_folder(['c']), folders)

    def test_EOB_L1(self):
        self.analyzer.attribute_folders(self.L1,1)
        self.analyzer.extend_merge(self.L1,1)
        self.assertEqual(len(self.analyzer.L_folders), len(self.L1))

    def test_EOB_L2(self):
        self.analyzer.attribute_folders(self.L2,2)
        self.analyzer.extend_merge(self.L2,2)
        folders = self.analyzer.L_folders

        self.assertEqual(len(self.analyzer.L_folders), 5)

        self.assertEqual(len(folders[GCA.key_folder(['d'])]), 2)
        self.assertEqual(len(folders[GCA.key_folder(['a'])]), 4)
        self.assertEqual(len(folders[GCA.key_folder(['g'])]), 3)
        self.assertEqual(len(folders[GCA.key_folder(['f'])]), 3)
        self.assertEqual(len(folders[GCA.key_folder(['h'])]), 1)

        folder = folders[GCA.key_folder(['d'])]
        self.assertEqual(folder[0].closure,frozenset(('a','d','f','g','h','e','g')))
        self.assertEqual(folder[0].generators, [['d','g'], ['d','e']])
        self.assertEqual(folder[0].transactions,set([3]))
        self.assertEqual(folder[0].support, 1)
        self.assertEqual(folder[1].closure, frozenset(('a','d','f','h','c')))
        self.assertEqual(folder[1].generators, [['d','c']])
        self.assertEqual(folder[1].transactions, set([2]))
        self.assertEqual(folder[1].support, 1)

        folder = folders[GCA.key_folder(['a'])]
        self.assertEqual(folder[0].closure, frozenset(('a','h','f')))
        self.assertEqual(folder[0].generators, [['a', 'f']])
        self.assertEqual(folder[0].transactions, set([2,3]))
        self.assertEqual(folder[0].support, 2)
        self.assertEqual(folder[1].closure, frozenset(('a','h','e','g')))
        self.assertEqual(folder[1].generators, [['a','g'], ['a','e']])
        self.assertEqual(folder[1].transactions, set([1, 3]))
        self.assertEqual(folder[1].support, 2)
        self.assertEqual(folder[2].closure, frozenset(('a','h','b','c','e','g')))
        self.assertEqual(folder[2].generators, [['a', 'b']])
        self.assertEqual(folder[2].transactions, set([1]))
        self.assertEqual(folder[2].support, 1)
        self.assertEqual(folder[3].closure, frozenset(('a','h','c')))
        self.assertEqual(folder[3].generators, [['a','c']])
        self.assertEqual(folder[3].transactions, set([1,2]))
        self.assertEqual(folder[3].support, 2)

        folder = folders[GCA.key_folder(['g'])]
        self.assertEqual(folder[0].closure, frozenset(('e','g','h','b','c')))
        self.assertEqual(folder[0].generators, [['g','b'],['g','c'],['b','h']])
        self.assertEqual(folder[0].transactions, set([1, 4]))
        self.assertEqual(folder[0].support, 2)
        self.assertEqual(folder[1].closure, frozenset(('b', 'c', 'e')))
        self.assertEqual(folder[1].generators, [['b', 'e'], ['e', 'c']])
        self.assertEqual(folder[1].transactions, set([1,4,5]))
        self.assertEqual(folder[1].support, 3)
        self.assertEqual(folder[2].closure, frozenset(('e', 'h')))
        self.assertEqual(folder[2].generators, [['e', 'h']])
        self.assertEqual(folder[2].transactions, set([1, 3, 4]))
        self.assertEqual(folder[2].support, 3)

        folder = folders[GCA.key_folder(['f'])]
        self.assertEqual(folder[0].closure, frozenset(('f', 'h', 'e', 'g')))
        self.assertEqual(folder[0].generators, [['f', 'g'], ['f', 'e']])
        self.assertEqual(folder[0].transactions, set([3, 4]))
        self.assertEqual(folder[0].support, 2)
        self.assertEqual(folder[1].closure, frozenset(('f','h','b','c','e','g')))
        self.assertEqual(folder[1].generators, [['f', 'b']])
        self.assertEqual(folder[1].transactions, set([4]))
        self.assertEqual(folder[1].support, 1)
        self.assertEqual(folder[2].closure, frozenset(('f', 'h', 'c')))
        self.assertEqual(folder[2].generators, [['f', 'c']])
        self.assertEqual(folder[2].transactions, set([2,4]))
        self.assertEqual(folder[2].support, 2)

    def test_mine(self):
        analyzer = GCA(self.db, 0.16) #percentage to get a min_supp of 1 matching the publication
        analyzer.clean_database()
        analyzer.mine()
        #closed_items = analyzer.lcg_into_list() for double hash

        expected_LGC = []
        expected_LGC.append(GCA.Node(2,set(['a','d','f','h']),[['d'],['a','f']],None))
        expected_LGC.append(GCA.Node(3,set(['a','h']),[['a']],None))
        expected_LGC.append(GCA.Node(3,set(['f','h']),[['f']],None))
        expected_LGC.append(GCA.Node(3,set(['e','g','h']),[['g'],['e','h']],None))
        expected_LGC.append(GCA.Node(4,set(['b','c']),[['b']],None))
        expected_LGC.append(GCA.Node(4,set(['e']),[['e']],None))
        expected_LGC.append(GCA.Node(4,set(['h']),[['h']],None))
        expected_LGC.append(GCA.Node(5,set(['c']),[['c']],None))
        expected_LGC.append(GCA.Node(1,set(['a','d','f','h','e','g']),[['d','g'],['d','e'],['a','f','g'],['a','f','e']],None))
        expected_LGC.append(GCA.Node(1,set(['a','d','f','h','c']),[['d','c'], ['a','f','c']],None))

        #TODO: check with publication's authors since aheg appears in two transactions in the database.
        #TODO: the example illustration shows an error with support of 1 but two transactions 1 and 3
        #expected_LGC.append(GCA.Node(1,set(['a','h','e','g']),[['a','g'],['a','e']],None))

        expected_LGC.append(GCA.Node(2,set(['a','h','e','g']),[['a','g'],['a','e']],None))
        expected_LGC.append(GCA.Node(1,set(['a','h','b','c','e','g']),[['a','b'],['a','g','c'],['a','e','c']],None))
        expected_LGC.append(GCA.Node(2,set(['a','h','c']),[['a','c']],None))
        expected_LGC.append(GCA.Node(2,set(['f','h','e','g']),[['f','g'],['f','e']],None))
        expected_LGC.append(GCA.Node(1,set(['f','h','b','c','e','g']),[['f','b'],['f','g','c'],['f','e','c']],None))
        expected_LGC.append(GCA.Node(2,set(['f','h','c']),[['f','c']],None))
        expected_LGC.append(GCA.Node(2,set(['e','g','h','b','c']),[['g','b'],['g','c'],['b','h'],['c','e','h']],None))
        expected_LGC.append(GCA.Node(3,set(['b','c','e']),[['b','e'],['c','e']],None))
        expected_LGC.append(GCA.Node(3,set(['h','c']),[['h','c']],None))

        #TODO: check with publication's authors if it is a mistake that afc is seperated from dc
        #TODO: since they have the same closure and the same support
        #expected_LGC.append(GCA.Node(1,set(['a','h','f','c','d']),[['a','f','c']],None))

        for index,expected in enumerate(expected_LGC):
            #check closure
            match = analyzer.search_node_with_closure(expected.closure)
            self.assertSequenceEqual(expected.closure, match.closure)

            #check support
            self.assertEqual(expected.support, match.support)

            #check generators
            for generator in expected.generators:
                match = analyzer.search_node_with_generator(None, generator)
                self.assertIsNotNone(match)

        self.assertEqual(len(expected_LGC),len(analyzer.LCG))


