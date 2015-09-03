import json
from django.test import TestCase

from flowr.models import Rule, RuleSet, Flow, State, DCCGraph
from flowr import sample_rules as rules

# ============================================================================

class FlowTests(TestCase):
    def setUp(self):
        self.rule_set = RuleSet.factory('My Rules', rules.A)

    def test_coverage(self):
        """Miscellaneous stuff to get our coverage to 100%"""
        Rule.on_enter(None)
        Rule.on_leave(None)
        with self.assertRaises(NotImplementedError):
            Rule.edit_screen(None, None)

        str(self.rule_set)
        rules.A.display_name()

    def test_rule_cytoscape(self):
        result = json.loads(self.rule_set.cytoscape_json())
        nodes = result['nodes']
        edges = result['edges']
        self.assertEqual(len(nodes), 5)
        self.assertEqual(len(edges), 5)

        for rule in [rules.A, rules.B, rules.C, rules.D, rules.E]:
            expected = {
                'data':{
                    'id':rule.name,
                    'label':rule.name,
                }
            }
            self.assertIn(expected, nodes)

        expected_edges = [(rules.A, rules.B), (rules.A, rules.C), 
            (rules.C, rules.D), (rules.C, rules.E), (rules.E, rules.A)]
        for edge in expected_edges:
            expected = {
                'data' : { 
                    'id':'%s_%s' % (edge[0].name, edge[1].name), 
                    'source':edge[0].name, 
                    'target':edge[1].name,
                }
            }
            self.assertIn(expected, edges)

    def test_flow1(self):
        """Tests a simple flow:
                    A
                    |
                    B
        """
        flow = Flow.factory('Flow', self.rule_set)
        self.assertFalse(flow.in_use())
        root = flow.root_data

        # should not be able to add D as it is against the rules
        with self.assertRaises(AttributeError):
            root.add_child_rule(rules.D)

        # should be able to add B
        root.add_child_rule(rules.B)

        # should not be able to add B again as A isn't multipath
        with self.assertRaises(AttributeError):
            root.add_child_rule(rules.B)

        # --- State testing
        rules.done_enter = []
        rules.done_leave = []

        # starting should call A's on_enter
        state = State.start(flow)
        self.assertEqual(rules.done_enter, ['A'])
        self.assertEqual(rules.done_leave, [])

        # next step
        state.next_state()
        self.assertEqual(rules.done_leave, ['A'])
        self.assertEqual(rules.done_enter, ['A', 'B'])

        # no next step in Flow
        with self.assertRaises(AttributeError):
            state.next_state()

        # force __str__ calls for coverage
        str(flow)
        str(root)
        str(state)

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
        flow = Flow.factory(name='Flow', rule_set=self.rule_set)
        root = flow.root_data
        node = root.add_child_rule(rules.C)
        node.add_child_rule(rules.D)

        # should not be able to add D a second time
        with self.assertRaises(AttributeError):
            node.add_child_rule(rules.D)

        node = node.add_child_rule(rules.E)
        node.connect_child(root)

        # -- start testing the flow
        rules.done_enter = []
        rules.done_leave = []
        state = State.start(flow=flow)
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

    def test_delete(self):
        flow = Flow.factory(name='Flow', rule_set=self.rule_set)
        flow.delete()

        self.assertEqual(Flow.objects.count(), 0)
        self.assertEqual(DCCGraph.objects.count(), 0)
