# flowr.views.py
import logging, json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from flowr.models import RuleSet, Flow

logger = logging.getLogger(__name__)

# ============================================================================

@staff_member_required
def view_rule_set_tree(request, rule_set_id):
    rule_set = get_object_or_404(RuleSet, id=rule_set_id)
    data = {
        'title':'View: %s' % rule_set.name,
        'graph':rule_set.cytoscape_json(),
        'root':rule_set.name,
    }

    return render_to_response('flowr/view_rules.html', data,
        context_instance=RequestContext(request))


@staff_member_required
def create_flow(request, rule_set_id):
    rule_set = get_object_or_404(RuleSet, id=rule_set_id)
    flow = Flow.factory('New Flow', rule_set)
    return edit_flow(request, flow.id)


@staff_member_required
def edit_flow(request, flow_id):
    flow = get_object_or_404(Flow, id=flow_id)
    roots = []
    if flow.start_node:
        roots = [flow.start_node.rule_store.name]

    data = {
        'flow':flow,
        'title':'Edit: %s' % flow.name,
        'graph':flow.cytoscape_json(),
        'roots':roots,
    }

    return render_to_response('flowr/edit_flow.html', data,
        context_instance=RequestContext(request))
