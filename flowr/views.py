# flowr.views.py
import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from flowr.models import RuleStoreSet, Flow

logger = logging.getLogger(__name__)

# ============================================================================

@staff_member_required
def view_rule_store_set_tree(request, rule_store_set_id):
    rule_store_set = get_object_or_404(RuleStoreSet, id=rule_store_set_id)
    data = {
        'rule_store_set':rule_store_set,
    }

    return render_to_response('flowr/view_rule_tree.html', data,
        context=RequestContext(request))


@staff_member_required
def create_flow(request, rule_store_set_id):
    rule_store_set = get_object_or_404(RuleStoreSet, id=rule_store_set_id)
    data = {
        'rule_store_set':rule_store_set,
    }

    return render_to_response('flowr/create_flow.html', data,
        context=RequestContext(request))


@staff_member_required
def edit_flow(request, flow_id):
    flow = get_object_or_404(Flow, id=flow_id)
    data = {
        'flow':flow,
    }

    return render_to_response('flowr/edit_flow.html', data,
        context=RequestContext(request))
