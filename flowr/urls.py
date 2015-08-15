from django.conf.urls import patterns, url

urlpatterns = patterns('flowr.views',
    url(r'view_rule_store_set_tree/(\d+)/$', 'view_rule_store_set_tree',
        name='flowr-view-rule-store-set-tree'),
    url(r'create_flow/(\d+)/$', 'create_flow', name='flowr-create-flow'),
    url(r'edit_flow/(\d+)/$', 'edit_flow', name='flowr-edit-flow'),
)
