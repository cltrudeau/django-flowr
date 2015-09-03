import json
from django.test import TestCase

from flowr.models import DCCGraph, Node
from flowr.tests.models import Label

# ============================================================================

#def pprint(data):
#    print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

# ============================================================================
# Test Class
# ============================================================================

class GraphTests(TestCase):
    def setUp(self):
        # create a bunch of test graphs

        # ---
        #    A.A
        #     |
        #    A.B
        self.graph_a = DCCGraph.factory(Label, name='A.A')
        self.graph_a.root.add_child(name='A.B')

        # verify
        self.assertEqual(Node.objects.filter(graph=self.graph_a).count(), 2)
        a, b = self._graph_query(self.graph_a, ['A.A', 'A.B'])
        self.assertEqual(a.parents.count(), 0)
        self.assertEqual(list(a.children.all()), [b])
        self.assertEqual(list(b.parents.all()), [a])
        self.assertEqual(b.children.count(), 0)

        # ---
        #      B.A
        #     /   \
        #   B.B   B.C
        #           \
        #           B.A (cycle)
        self.graph_b = DCCGraph.factory(Label, name='B.A')
        self.graph_b.root.add_child(name='B.B')
        node = self.graph_b.root.add_child(name='B.C')
        node.connect_child(self.graph_b.root)

        # verify
        self.assertEqual(Node.objects.filter(graph=self.graph_b).count(), 3)
        a,b,c = self._graph_query(self.graph_b, ['B.A', 'B.B', 'B.C'])

        self.assertEqual(a, self.graph_b.root)
        self.assertEqual(list(a.parents.all()), [c])
        self.assertEqual(set(a.children.all()), set([b, c]))
        self.assertEqual(list(b.parents.all()), [a])
        self.assertEqual(b.children.count(), 0)
        self.assertEqual(list(c.parents.all()), [a])
        self.assertEqual(list(c.children.all()), [a])

        # ---
        #           C.A
        #          /   \
        #        C.B   C.C
        #             /   \
        #            /     \
        #           /       \
        #          /         \
        #         /           \
        #       C.D           C.E
        #      /   \            \
        #    C.G   C.H          C.F
        #    /       \             \
        #  C.I        C.A (cycle)  C.A (cycle)
        #    \
        #    C.H (loop back)

        self.graph_c = DCCGraph.factory_from_graph(Label, 
            {'name':'C.A'}, [
                ({'name':'C.B'}, []),
                ({'name':'C.C'}, [
                    ({'name':'C.D'}, [
                        ({'name':'C.G'}, [
                            ({'name':'C.I'}, []),
                        ]),
                        ({'name':'C.H'}, []),
                    ]),
                    ({'name':'C.E'}, [
                        ({'name':'C.F'}, []),
                    ]),
                ]),
            ])
        i = self.graph_c.find_nodes(name='C.I').first()
        h = self.graph_c.find_nodes(name='C.H').first()
        i.connect_child(h)
        h.connect_child(self.graph_c.root)
        f = self.graph_c.find_nodes(name='C.F').first()
        f.connect_child(self.graph_c.root)

        # verify
        self.assertEqual(Node.objects.filter(graph=self.graph_c).count(), 9)
        a,b,c,d,e,f,g,h,i = self._graph_query(self.graph_c, ['C.A', 'C.B',
            'C.C', 'C.D', 'C.E', 'C.F', 'C.G', 'C.H', 'C.I'])

        self.assertEqual(a, self.graph_c.root)
        self.assertEqual(set(a.parents.all()), set([f, h]))
        self.assertEqual(set(a.children.all()), set([b, c]))
        self.assertEqual(list(b.parents.all()), [a])
        self.assertEqual(b.children.count(), 0)

        self.assertEqual(list(c.parents.all()), [a])
        self.assertEqual(set(c.children.all()), set([d, e]))

        self.assertEqual(list(d.parents.all()), [c])
        self.assertEqual(set(d.children.all()), set([g, h]))

        self.assertEqual(list(e.parents.all()), [c])
        self.assertEqual(set(e.children.all()), set([f]))

        self.assertEqual(list(f.parents.all()), [e])
        self.assertEqual(set(f.children.all()), set([a]))

        self.assertEqual(list(g.parents.all()), [d])
        self.assertEqual(set(g.children.all()), set([i]))

        self.assertEqual(list(h.parents.all()), [d, i])
        self.assertEqual(set(h.children.all()), set([a]))

        self.assertEqual(list(i.parents.all()), [g])
        self.assertEqual(set(i.children.all()), set([h]))

    def _graph_query(self, graph, values):
        nodes = []
        for value in values:
            nodes.append(graph.find_nodes(name=value).get())

        return nodes

    def _c_graph_nodes(self):
        return self._graph_query(self.graph_c, ['C.A', 'C.B', 'C.C', 'C.D', 
            'C.E', 'C.F', 'C.G', 'C.H', 'C.I'])

    def test_ancestors(self):
        a,b,c,d,e,f,g,h,i = self._c_graph_nodes()

        self.assertEqual(set(a.ancestors()), set([f, e, c, h, d, i, g]))
        self.assertEqual(set(b.ancestors()), set([a, f, e, c, h, d, i, g]))
        self.assertEqual(set(c.ancestors()), set([a, f, e, h, d, i, g]))
        self.assertEqual(set(d.ancestors()), set([c, a, f, e, h, i, g]))
        self.assertEqual(set(e.ancestors()), set([c, a, f, h, d, i, g]))
        self.assertEqual(set(f.ancestors()), set([e, c, a, h, d, i, g]))
        self.assertEqual(set(g.ancestors()), set([d, c, a, f, e, h, i]))
        self.assertEqual(set(h.ancestors()), set([d, c, a, f, e, i, g]))
        self.assertEqual(set(i.ancestors()), set([g, d, c, a, f, e, h,]))

        self.assertEqual(set(a.ancestors_root()), set([]))
        self.assertEqual(set(b.ancestors_root()), set([a]))
        self.assertEqual(set(c.ancestors_root()), set([a]))
        self.assertEqual(set(d.ancestors_root()), set([c, a]))
        self.assertEqual(set(e.ancestors_root()), set([c, a]))
        self.assertEqual(set(f.ancestors_root()), set([e, c, a]))
        self.assertEqual(set(g.ancestors_root()), set([d, c, a]))
        self.assertEqual(set(h.ancestors_root()), set([d, c, a, i, g]))
        self.assertEqual(set(i.ancestors_root()), set([g, d, c, a]))

    def test_descendents(self):
        a,b,c,d,e,f,g,h,i = self._c_graph_nodes()

        self.assertEqual(set(a.descendents()), set([b, c, d, e, f, g, h, i]))
        self.assertEqual(set(b.descendents()), set([]))
        self.assertEqual(set(c.descendents()), set([a, b, d, e, f, g, h, i]))
        self.assertEqual(set(d.descendents()), set([a, b, c, e, f, g, h, i]))
        self.assertEqual(set(e.descendents()), set([a, b, c, d, f, g, h, i]))
        self.assertEqual(set(f.descendents()), set([a, b, c, d, e, g, h, i]))
        self.assertEqual(set(g.descendents()), set([a, b, c, d, e, f, h, i]))
        self.assertEqual(set(h.descendents()), set([a, b, c, d, e, f, g, i]))
        self.assertEqual(set(i.descendents()), set([a, b, c, d, e, f, g, h]))

        self.assertEqual(set(a.descendents_root()), 
            set([b, c, d, e, f, g, h, i]))
        self.assertEqual(set(b.descendents_root()), set([]))
        self.assertEqual(set(c.descendents_root()), set([d, e, f, g, h, i, a]))
        self.assertEqual(set(d.descendents_root()), set([g, h, i, a]))
        self.assertEqual(set(e.descendents_root()), set([f, a]))
        self.assertEqual(set(f.descendents_root()), set([a]))
        self.assertEqual(set(g.descendents_root()), set([i, h, a]))
        self.assertEqual(set(h.descendents_root()), set([a]))
        self.assertEqual(set(i.descendents_root()), set([h, a]))

    def test_cytoscape(self):
        a,b,c,d,e,f,g,h,i = self._c_graph_nodes()

        extra_fields = lambda n: {'name':n.data.name}
        result = json.loads(self.graph_c.cytoscape_json(extra_fields))
        nodes = result['nodes']
        edges = result['edges']
        self.assertEqual(len(nodes), 9)
        self.assertEqual(len(edges), 11)

        for node in [a,b,c,d,e,f,g,h,i]:
            expected = {
                'data':{
                    'id':'n%s' % node.id,
                    'name':node.data.name,
                }
            }
            self.assertIn(expected, nodes)

        expected_edges = [(a,b), (a,c), (c,d), (c,e), (d, g), (d, h), (e, f),
            (f, a), (g, i), (h, a), (i, h)]
        for edge in expected_edges:
            expected = {
                'data' : { 
                    'id':'e%s_%s' % (edge[0].id, edge[1].id), 
                    'source':'n%s' % edge[0].id, 
                    'target':'n%s' % edge[1].id,
                }
            }
            self.assertIn(expected, edges)

    def test_can_delete(self):
        a,b,c,d,e,f,g,h,i = self._c_graph_nodes()

        self.assertFalse( a.can_remove() )
        self.assertFalse( c.can_remove() )
        self.assertFalse( d.can_remove() )
        self.assertFalse( e.can_remove() )
        self.assertFalse( g.can_remove() )
        self.assertFalse( i.can_remove() )

        self.assertTrue( b.can_remove() )
        self.assertTrue( f.can_remove() )
        self.assertTrue( h.can_remove() )

    def test_delete(self):
        a,b,c,d,e,f,g,h,i = self._c_graph_nodes()

        with self.assertRaises(AttributeError):
            a.remove()

        expected = b.data
        result = b.remove()
        self.assertEqual(expected, result)
        self.assertEqual(Node.objects.filter(graph=self.graph_c).count(), 8)
        self.assertEqual(set(a.descendents()), set([c, d, e, f, g, h, i]))

        expected = h.data
        result = h.remove()
        self.assertEqual(expected, result)
        self.assertEqual(Node.objects.filter(graph=self.graph_c).count(), 7)
        self.assertEqual(set(a.descendents()), set([c, d, e, f, g, i]))
        self.assertEqual(i.children.count(), 0)
        self.assertEqual(set(d.descendents_root()), set([g, i]))

    def test_prune(self):
        a,b,c,d,e,f,g,h,i = self._c_graph_nodes()

        # -- simple prune of childless node
        expected = [b, ]
        result = b.prune_list()
        self.assertEqual(expected, result)

        expected = [b.data, ]
        result = b.prune()
        self.assertEqual(expected, result)
        self.assertEqual(set(a.descendents()), set([c, d, e, f, g, h, i]))
        self.assertEqual(a.children.count(), 1)
        self.assertEqual(Node.objects.filter(graph=self.graph_c).count(), 8)

        # -- more complex prune of node with children and cycles
        expected = [d, g, h, i]
        result = d.prune_list()
        self.assertEqual(set(expected), set(result))

        expected = [d.data, g.data, h.data, i.data]
        result = d.prune()
        self.assertEqual(set(expected), set(result))
        self.assertEqual(set(a.descendents()), set([c, e, f]))
        self.assertEqual(c.children.count(), 1)
        self.assertEqual(Node.objects.filter(graph=self.graph_c).count(), 4)

    def test_errors(self):
        # Check we can't connect nodes from different graphs
        a = self._graph_query(self.graph_a, ['A.A', ])[0]
        b = self._graph_query(self.graph_a, ['B.A', ])[0]
        
        with self.assertRaises(AttributeError):
            a.connect_child(b)

        # check we can't create a graph without a DataNode extender
        with self.assertRaises(AttributeError):
            DCCGraph.factory(object)

    def test_coverage(self):
        # misc items to get full coverage
        str(self.graph_a)
        str(self.graph_a.root)
        str(self.graph_a.root.data)
