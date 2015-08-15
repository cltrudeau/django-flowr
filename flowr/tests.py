from django.test import TestCase

from flowr.models import Rule, RuleStoreSet, RuleStore, Flow, State
from flowr import sample_rules as rules

# ============================================================================
# Test Class
# ============================================================================

class AllTests(TestCase):
    def setUp(self):
        self.rule_store_set = RuleStoreSet.factory('My Rules', [rules.A, ])

    def _rule_get(self, rule_store_set, rule_class_name, starting=False):
        return RuleStore.objects.get(rule_store_set=rule_store_set, 
            rule_class_name=rule_class_name, starting=starting)

    def test_coverage(self):
        """Miscellaneous stuff to get our coverage to 100%"""
        Rule.on_enter(None)
        Rule.on_leave(None)
        str(self.rule_store_set)
        store = self._rule_get(self.rule_store_set, rules.A.name(), True)
        str(store)

    def test_rule_store_set_factory(self):
        # check all the RuleStore objects got created
        self._rule_get(self.rule_store_set, rules.A.name(), True)
        self._rule_get(self.rule_store_set, rules.B.name(), False)
        self._rule_get(self.rule_store_set, rules.C.name(), False)
        self._rule_get(self.rule_store_set, rules.D.name(), False)
        self._rule_get(self.rule_store_set, rules.E.name(), False)

        self.assertEqual(RuleStore.objects.count(), 5)

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

        # start testing the flow
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
