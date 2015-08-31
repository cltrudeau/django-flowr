# create_test_data.py

from django.core.management.base import BaseCommand

from flowr.models import RuleSet, Flow
from flowr import sample_rules as rules

# =============================================================================

class Command(BaseCommand):
    def handle(self, *args, **options):
        rule_set = RuleSet.factory('My Rules', rules.A)

        flow = Flow.factory('Simple Flow', rule_set)
        root = flow.root_data
        root.add_child_rule(rules.B)

        flow = Flow.factory('Branching, Looping Flow', rule_set)
        root = flow.root_data
        node = root.add_child_rule(rules.C)
        node.add_child_rule(rules.D)
        node = node.add_child_rule(rules.E)
        node.add_child_rule(rules.A)
