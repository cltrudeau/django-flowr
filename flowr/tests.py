import json
from django.test import TestCase

from flowr.models import Rule, RuleStoreSet, RuleStore, Flow, State
from flowr import sample_rules as rules

# ============================================================================
# Test Class
# ============================================================================

class AllTests(TestCase):
    def setUp(self):
        self.rule_store_set = RuleStoreSet.factory('My Rules', [rules.A, ])

    def _pprint(self, data):
        print(json.dumps(data, sort_keys=True, indent=4, 
            separators=(',', ': ')))

    def _rule_get(self, rule_store_set, rule_class_name, starting=False):
        return RuleStore.objects.get(rule_store_set=rule_store_set, 
            rule_class_name=rule_class_name, starting=starting)

    def _verify_cytoscape_tree(self, expected_nodes, expected_edges,
            json_data):
        data = json.loads(json_data)
        self.assertEqual(len(expected_nodes), len(data['nodes']))
        self.assertEqual(len(expected_edges), len(data['edges']))

        for node in expected_nodes:
            d = { 'data': { 'id':node } }
            self.assertIn(d, data['nodes'])

        for edge in expected_edges:
            d = {'data' : { 'id':edge[0], 'source':edge[1], 'target':edge[2]}}
            self.assertIn(d, data['edges'])

    def _make_edge(self, rule1, rule2):
        edge = (
            '%s_%s' % (rule1.display_name(), rule2.display_name()),
            rule1.display_name(), 
            rule2.display_name(),
        )
        return edge

    def test_coverage(self):
        """Miscellaneous stuff to get our coverage to 100%"""
        Rule.on_enter(None)
        Rule.on_leave(None)
        str(self.rule_store_set)
        store = self._rule_get(self.rule_store_set, rules.A.class_name(), True)
        str(store)

    def test_rule_store_set_factory(self):
        # check all the RuleStore objects got created
        self._rule_get(self.rule_store_set, rules.A.class_name(), True)
        self._rule_get(self.rule_store_set, rules.B.class_name(), False)
        self._rule_get(self.rule_store_set, rules.C.class_name(), False)
        self._rule_get(self.rule_store_set, rules.D.class_name(), False)
        self._rule_get(self.rule_store_set, rules.E.class_name(), False)

        self.assertEqual(RuleStore.objects.count(), 5)

        # verify cytoscape graph
        self._verify_cytoscape_tree(
            [rules.A.display_name(), rules.B.display_name(), 
                rules.C.display_name(), rules.D.display_name(), 
                rules.E.display_name(),], 
            [self._make_edge(rules.A, rules.B),
                self._make_edge(rules.A, rules.C),
                self._make_edge(rules.C, rules.D),
                self._make_edge(rules.C, rules.E),
                self._make_edge(rules.E, rules.A),
            ], 
            self.rule_store_set.cytoscape_json())


    def test_flow1(self):
        """Tests a simple flow:
                    A
                    |
                    B
        """
        flow = Flow.objects.create(name='Flow', 
            rule_store_set=self.rule_store_set)
        str(flow)  # force the __str__ call to happen
        self.assertFalse(flow.in_use())
        state = State.objects.create(flow=flow)
        self.assertTrue(flow.in_use())

        # shouldn't be able to start the state yet
        with self.assertRaises(AttributeError):
            state.start()

        # B isn't allowed to be the start of a flow
        with self.assertRaises(AttributeError):
            flow.set_start_rule(rules.B)

        # set the starting node for our Flow
        root = flow.set_start_rule(rules.A)

        # should not be able to add D as it is against the rules
        with self.assertRaises(AttributeError):
            root.add_child_rule(rules.D)

        # should be able to add B
        root.add_child_rule(rules.B)

        # should not be able to add B again as A isn't multipath
        with self.assertRaises(AttributeError):
            root.add_child_rule(rules.B)

        # -- serialization test
        self._verify_cytoscape_tree(
            [rules.A.display_name(), rules.B.display_name(), ],
            [self._make_edge(rules.A, rules.B),], 
            flow.cytoscape_json())

        # --- State testing
        rules.done_enter = []
        rules.done_leave = []

        # starting should call A's on_enter
        state.start()
        self.assertEqual(rules.done_enter, ['A'])
        self.assertEqual(rules.done_leave, [])

        # next step
        state.next_state()
        self.assertEqual(rules.done_leave, ['A'])
        self.assertEqual(rules.done_enter, ['A', 'B'])

        # no next step in Flow
        with self.assertRaises(AttributeError):
            state.next_state()

    def test_flow2(self):
        """Tests multipath, looping flow:
                   A
                   |
                   C
                  / \
                 D   E
                      \
                       A (loops)
        """
        flow = Flow.objects.create(name='Flow', 
            rule_store_set=self.rule_store_set)
        node = flow.set_start_rule(rules.A)
        node = node.add_child_rule(rules.C)
        node.add_child_rule(rules.D)
        node = node.add_child_rule(rules.E)
        node.add_child_rule(rules.A)

        # -- serialization test
        self._verify_cytoscape_tree(
            [rules.A.display_name(), rules.C.display_name(), 
                rules.D.display_name(), 
                rules.E.display_name(),], 
            [self._make_edge(rules.A, rules.C),
                self._make_edge(rules.C, rules.D),
                self._make_edge(rules.C, rules.E),
                self._make_edge(rules.E, rules.A),
            ], 
            flow.cytoscape_json())

        # -- start testing the flow
        rules.done_enter = []
        rules.done_leave = []
        state = State.objects.create(flow=flow)
        state.start()
        self.assertEqual(rules.done_enter, ['A'])
        self.assertEqual(rules.done_leave, [])

        state.next_state()
        self.assertEqual(rules.done_enter, ['A', 'C'])
        self.assertEqual(rules.done_leave, ['A'])

        # next step requires a choice, can't use parameterless call
        with self.assertRaises(AttributeError):
            state.next_state()

        # next step must be D or E
        with self.assertRaises(AttributeError):
            state.next_state(rules.A)

        state.next_state(rules.E)
        state.next_state(rules.A)
        self.assertEqual(rules.done_enter, ['A', 'C', 'E', 'A'])
        self.assertEqual(rules.done_leave, ['A', 'C', 'E'])
