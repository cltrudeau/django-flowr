# flowr.views.py
import logging, json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from flowr.models import RuleStoreSet, RuleStore, Flow

logger = logging.getLogger(__name__)

# ============================================================================

@staff_member_required
def view_rule_store_set_tree(request, rule_store_set_id):
    rule_store_set = get_object_or_404(RuleStoreSet, id=rule_store_set_id)
    data = {
        'title':'View: %s' % rule_store_set.name,
        'graph':rule_store_set.cytoscape_json(),
        'roots':json.dumps([rs.name for rs in \
            RuleStore.objects.filter(rule_store_set=rule_store_set,
                starting=True)
            ]),
    }

    return render_to_response('flowr/view_rules.html', data,
        context_instance=RequestContext(request))


@staff_member_required
def create_flow(request, rule_store_set_id):
    rule_store_set = get_object_or_404(RuleStoreSet, id=rule_store_set_id)
    flow = Flow.objects.create(name='New Flow', rule_store_set=rule_store_set)
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
