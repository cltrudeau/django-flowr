# create_test_data.py

from django.core.management.base import BaseCommand

from flowr.models import RuleStoreSet, Flow
from flowr import sample_rules as rules

# =============================================================================

class Command(BaseCommand):
    def handle(self, *args, **options):
        rule_store_set = RuleStoreSet.factory('My Rules', [rules.A, ])

        flow = Flow.objects.create(name='Simple Flow', 
            rule_store_set=rule_store_set)
        node = flow.set_start_rule(rules.A)
        node.add_child_rule(rules.B)

        flow = Flow.objects.create(name='Branching, Looping Flow', 
            rule_store_set=rule_store_set)
        node = flow.set_start_rule(rules.A)
        node = node.add_child_rule(rules.C)
        node.add_child_rule(rules.D)
        node = node.add_child_rule(rules.E)
        node.add_child_rule(rules.A)
