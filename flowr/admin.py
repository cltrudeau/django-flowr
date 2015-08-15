# flowr.admin.py

import logging

from django.contrib import admin
from django.core.urlresolvers import reverse

from flowr.models import RuleStoreSet, RuleStore, Flow, FlowNode, State

logger = logging.getLogger(__name__)

# =============================================================================
# Admin Classes
# =============================================================================

@admin.register(RuleStoreSet)
class RuleStoreSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'self_rule_stores', 'self_flows',
        'self_actions')

    def self_rule_stores(self, obj):
        return ('<a href="/admin/flowr/rulestore/?rule_store_set__id__exact=%s"'
            '>Associated RuleStores</a>') % obj.id
    self_rule_stores.allow_tags = True
    self_rule_stores.short_description = 'Associated RuleStores'

    def self_flows(self, obj):
        return ('<a href="/admin/flowr/flow/?rule_store_set__id__exact=%s"'
            '>Associated Flows</a>') % obj.id
    self_flows.allow_tags = True
    self_flows.short_description = 'Associated Flows'

    def self_actions(self, obj):
        view = reverse('flowr-view-rule-store-set-tree', args=(obj.id,))
        flow = reverse('flowr-create-flow', args=(obj.id,))
        return ('<a href="%s">View Tree</a>&nbsp;|&nbsp;'
            '<a href="%s">New Flow</a>') % (view, flow)
    self_actions.allow_tags = True
    self_actions.short_description = 'Actions'


@admin.register(RuleStore)
class RuleStoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rule_store_set', 'rule_class_name',
        'starting')
    list_filter = ('rule_store_set', 'starting')


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rule_store_set', 'self_start_rule',
        'self_actions')
    list_filter = ('rule_store_set', )

    def self_start_rule(self, obj):
        if obj.start_node:
            return obj.start_node.rule_store.name
        else:
            return '<i>None</i>'
    self_start_rule.allow_tags = True

    def self_actions(self, obj):
        flow = reverse('flowr-edit-flow', args=(obj.id,))
        if obj.in_use():
            return '<i>Flow in use</i>'

        return '<a href="%s">Edit Flow</a>' % flow
    self_actions.allow_tags = True
    self_actions.short_description = 'Actions'


@admin.register(FlowNode)
class FlowNodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'flow', 'rule_store', 'self_rule', 'self_children')
    list_filter = ('flow', 'flow__rule_store_set', )

    def self_rule(self, obj):
        return obj.rule_store.rule.name

    def self_children(self, obj):
        kids = [str(node.id) for node in obj.children.all()]
        return ', '.join(kids)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'flow', 'self_rule_store_set', 'current_node')
    list_filter = ('flow', 'flow__rule_store_set', )

    def self_rule_store_set(self, obj):
        return str(obj.flow.rule_store_set)
