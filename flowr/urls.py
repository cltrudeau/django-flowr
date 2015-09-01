from django.conf.urls import patterns, url

urlpatterns = patterns('flowr.views',
    url(r'view_rule_set_tree/(\d+)/$', 'view_rule_set_tree',
        name='flowr-view-rule-set-tree'),
    url(r'create_flow/(\d+)/$', 'create_flow', name='flowr-create-flow'),
    url(r'edit_flow/(\d+)/$', 'edit_flow', name='flowr-edit-flow'),

    url(r'node_selected/n(\d+)/$', 'node_selected'),
    url(r'node_remove/n(\d+)/$', 'node_remove'),
    url(r'node_prune/n(\d+)/$', 'node_prune'),
)
