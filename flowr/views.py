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
        'roots':json.dumps([rule_set.root_rule_name, ] ),
        'return_url': request.META['HTTP_REFERER'],
    }

    t = json.loads(data['graph'])
    print(json.dumps(t, sort_keys=True, indent=4, separators=(',', ': ')))

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

    extra_fields = lambda n: {'label':n.data.rule_name}
    data = {
        'flow':flow,
        'title':'Edit: %s' % flow.name,
        'graph':flow.state_graph.cytoscape_json(extra_fields),
        'roots':json.dumps(['n%s' % flow.state_graph.root.id, ] ),
        'return_url': request.META['HTTP_REFERER'],
    }

    return render_to_response('flowr/edit_flow.html', data,
        context_instance=RequestContext(request))
