# flowr.admin.py

import logging

from django.contrib import admin
from django.core.urlresolvers import reverse

from flowr.models import DCCGraph, Node, RuleSet, Flow, FlowNodeData, State

logger = logging.getLogger(__name__)

# =============================================================================
# Graph Admin Classes
# =============================================================================

@admin.register(DCCGraph)
class DCCGraphAdmin(admin.ModelAdmin):
    list_display = ('id', 'self_model', 'self_root', 'self_num_nodes', 
        'self_nodes')

    def self_model(self, obj):
        return '%s' % obj.data_content_type.model_class().__name__
    self_model.short_description = 'Data Model'

    def self_root(self, obj):
        return '%s' % obj.root
    self_root.short_description = 'Root'

    def self_num_nodes(self, obj):
        return Node.objects.filter(graph=obj).count()
    self_num_nodes.short_description = '# Nodes'

    def self_nodes(self, obj):
        return ('<a href="/admin/flowr/node/?graph__id__exact=%s"'
            '>Associated Nodes</a>') % obj.id
    self_nodes.allow_tags = True
    self_nodes.short_description = 'Associated Nodes'


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'self_graph', 'self_parents', 'self_children', 
        'self_is_root', 'data')

    def self_graph(self, obj):
        return '%s' % obj.graph
    self_graph.short_description = 'DCC Graph'

    def self_parents(self, obj):
        parents = [str(p) for p in obj.parents.all()]
        return ', '.join(parents)
    self_parents.short_description = 'Parents'

    def self_children(self, obj):
        children = [str(c) for c in obj.children.all()]
        return ','.join(children)
    self_children.short_description = 'Children'

    def self_is_root(self, obj):
        return obj.is_root()
    self_is_root.short_description = 'Is Root'

# =============================================================================
# Flow Admin Classes
# =============================================================================

@admin.register(RuleSet)
class RuleSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'root_rule_label', 'self_flows',
        'self_actions')

    def self_flows(self, obj):
        return ('<a href="/admin/flowr/flow/?rule_set__id__exact=%s"'
            '>Associated Flows</a>') % obj.id
    self_flows.allow_tags = True
    self_flows.short_description = 'Associated Flows'

    def self_actions(self, obj):
        view = reverse('flowr-view-rule-set-tree', args=(obj.id,))
        flow = reverse('flowr-create-flow', args=(obj.id,))
        return ('<a href="%s">View Tree</a>&nbsp;|&nbsp;'
            '<a href="%s">New Flow</a>') % (view, flow)
    self_actions.allow_tags = True
    self_actions.short_description = 'Actions'


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rule_set', 'state_graph', 'root_data', 
        'self_actions')
    list_filter = ('rule_set', )

    def self_actions(self, obj):
        flow = reverse('flowr-edit-flow', args=(obj.id,))
        if obj.in_use():
            return '<i>Flow in use</i>'

        return '<a href="%s">Edit Flow</a>' % flow
    self_actions.allow_tags = True
    self_actions.short_description = 'Actions'


@admin.register(FlowNodeData)
class FlowNodeDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'rule_label', 'self_flow', 'self_children')

    def self_children(self, obj):
        kids = [str(node.data.rule_name) for node in obj.node.children.all()]
        return ', '.join(kids)

    def self_flow(self, obj):
        # django admin only detects declared items, this value is set in
        # __init__ so it needs a helper function
        return str(obj.flow)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'flow', 'current_node', 'self_rule', 'self_rule_set')
    list_filter = ('flow', 'flow__rule_set', )

    def self_rule_set(self, obj):
        return str(obj.flow.rule_set)

    def self_rule(self, obj):
        return str(obj.current_node.data.rule.label)
