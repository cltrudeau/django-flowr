# flowr.models.py
import logging, json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

logger = logging.getLogger(__name__)

# ============================================================================

"""
Flowr Rule System
=================

Most state machine libraries are "static" and require the flow in the state
machine to be definied programmatically.  Flowr is designed so that you can
build state machine flows and store them in a database.  The system is not
fully dynamic as states in the machine are still tied to classes that you
define, but within your allowed rule sets multiple state machines can be
created.

Definitions:

* **Rule** -- a class that you define which specifies what other Rule objects
    can be connected to and what happens when a state is entered and exited
* **RuleStore** -- a model representation in the database of your Rule object,
    these are generated automatically by Flowr
* **RuleStoreSet** -- a container for a group of Rules that operate together
    in order to specify one or more state machines
* **Flow** -- the state machine node graph which you created based on a
    defined RuleStoreSet
* **State** -- a state in the state machine

Example
-------

A user defines the following Rule classes::

    class A(Rule):
        children = [B, C]

    class B(Rule):
        children = []

    class C(Rule):
        children = [D, E]
        multiple_paths = True

    class D(Rule):
        children = []

    class E(Rule):
        children = []


A RuleStoreSet is created using the factory and passing in the single starting
point of our allowed Flows::

    set = RuleStoreSet.factory('My Rules', [A, ])

This will traverse the defined Rule classes and automatically create::

    RuleStore(rulestoreset=set, node_class='A', starting=True)
    RuleStore(rulestoreset=set, node_class='B', starting=False)
    RuleStore(rulestoreset=set, node_class='C', starting=False)
    RuleStore(rulestoreset=set, node_class='D', starting=False)
    RuleStore(rulestoreset=set, node_class='E', starting=False)


Using these rules, you could create some flows:

* A -> B
* A -> C -> D
* A -> C -> D or E

You would not be able to create:

* A -> D
* A -> B -> C

The first of these is not allowed because "D" is not a direct child of "A" in
the Rule definitions.  The second is not allowed because "B" has no allowed
children.
"""

# ============================================================================

class TimeTrackedModel(models.Model):
    """Abstract model for create & update fields.  """

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# ============================================================================
# Rule Models
# ============================================================================

class Rule(object):
    children = []
    multiple_paths = False

    @classmethod
    def on_enter(self, state):
        pass

    @classmethod
    def on_leave(self, state):
        pass


class RuleStoreSet(TimeTrackedModel):
    """RuleStoreSet objects are references to a set of RuleStore objects
    defined by the user in the flow system.  Any instantiated Flow will be
    associated with a RuleStoreSet that determines what nodes can be connected
    to each other and in what order.
    """
    name = models.CharField(max_length=25)

    def __str__(self):
        return 'RuleStoreSet(id=%s %s)' % (self.id, self.name)

    # --------------------------------------------
    @classmethod
    @transaction.atomic
    def factory(cls, name, starting_rules):
        """Creates a RuleStoreSet and corresponding RuleStore objects by
        introspecting all the given Rules which are viable starting nodes in a
        Flow.

        :param name: human readable name for this collection
        :param starting_rules: an iterable of one or more Rule classes
            which the RuleStoreSet can start with.

        :returns: created RuleStoreSet object, as a side effect will create
            one or more RuleStore objects as well
        """
        rule_store_set = RuleStoreSet.objects.create(name=name)
        visited = set([])
        for rule in starting_rules:
            store = RuleStore.factory(rule_store_set, rule, True)
            visited.add(store)
            rule_store_set._depth_traverse_create(store, visited)

        return rule_store_set

    # --------------------------------------------
    def _depth_traverse_create(self, rule_store, visited):
        for child in rule_store.rule.children:
            store = RuleStore.factory(self, child)
            if store not in visited:
                visited.add(store)
                self._depth_traverse_create(store, visited)

    def cytoscape_json(self):
        data = {
            'nodes':[],
            'edges':[],
        }
        for rule_store in RuleStore.objects.filter(rule_store_set=self):
            data['nodes'].append( { 'data':{ 'id':rule_store.name } } )
            for child in rule_store.rule.children:
                data['edges'].append( { 
                    'data':{ 
                        'id':'%s_%s' % (rule_store.name, child.__name__),
                        'source':rule_store.name,
                        'target':child.__name__,
                    }
                })


        return json.dumps(data)


class RuleStore(TimeTrackedModel):
    rule_store_set = models.ForeignKey(RuleStoreSet)
    rule_class_name = models.CharField(max_length=80)
    starting = models.BooleanField(default=False)

    def __str__(self):
        return 'RuleStore(id=%s set=%s %s)' % (self.id, 
            self.rule_store_set.name, self.rule_class_name)

    @classmethod
    def factory(cls, rule_store_set, rule, starting=False):
        try:
            store = RuleStore.objects.get(rule_store_set=rule_store_set, 
                rule_class_name='%s.%s' % (rule.__module__, rule.__name__))
        except RuleStore.DoesNotExist:
            # can't use get_or_create: A -> B -> A is legal, and so would have
            # starting=True for the first and starting=False for the second
            # call but should result in only one Rule object
            store = RuleStore.objects.create(rule_store_set=rule_store_set, 
                rule_class_name='%s.%s' % (rule.__module__, rule.__name__),
                starting=starting)
        return store

    @classmethod
    def find(cls, rule_store_set, rule):
        return RuleStore.objects.get(rule_store_set=rule_store_set, 
            rule_class_name='%s.%s' % (rule.__module__, rule.__name__))

    def rule_match(self, rule):
        """Returns True if this RuleStore contains the given Rule
        """
        return self.rule_class_name == '%s.%s' % (rule.__module__, 
            rule.__name__)

    @property
    def rule(self):
        if hasattr(self, '_rule_class'):
            return self._rule_class

        (modname, classname) = self.rule_class_name.rsplit('.', 1)
        mod = __import__(modname, globals(), locals(), [classname])
        self._rule_class = getattr(mod, classname)
        return self._rule_class

    @property
    def name(self):
        return self.rule.__name__

# ============================================================================
# Flow Models
# ============================================================================

class Flow(TimeTrackedModel):
    name = models.CharField(max_length=25)
    rule_store_set = models.ForeignKey(RuleStoreSet)
    start_node = models.ForeignKey('flowr.FlowNode', null=True, blank=True,
        related_name='+')

    def __str__(self):
        return 'Flow(id=%s %s)' % (self.id, self.name)

    def set_start_rule(self, rule):
        """Gets or creates a FlowNode for the given Rule as the first Rule in
        this Flow.  The Rule must be a starting Rule in the RuleStoreSet.

        :param rule: Rule object to be the first in this Flow.
        :returns: FlowNode for the Rule that was set
        """
        try:
            rule_store = RuleStore.objects.get(starting=True,
                rule_store_set=self.rule_store_set, 
                rule_class_name='%s.%s' % (rule.__module__, rule.__name__))
        except RuleStore.DoesNotExist:
            raise AttributeError('Rule %s was not a starting rule in the set' %(
                rule.__name__))

        node, _ = FlowNode.objects.get_or_create(flow=self,
            rule_store=rule_store)
        self.start_node = node
        self.save()
        return node

    def in_use(self):
        state = State.objects.filter(flow=self).first()
        return bool(state)

    def _depth_serialize(self, node, data):
        n = { 'data':{ 'id':node.rule_store.name } }
        if n not in data['nodes']:
            data['nodes'].append(n)
            for child in node.children.all():
                data['edges'].append({ 
                    'data':{ 
                        'id':'%s_%s' % (node.rule_store.name,
                            child.rule_store.name),
                        'source':node.rule_store.name,
                        'target':child.rule_store.name,
                    }
                })
                self._depth_serialize(child, data)

    def cytoscape_json(self):
        data = {
            'nodes':[],
            'edges':[],
        }
        self._depth_serialize(self.start_node, data)
        return json.dumps(data)


class FlowNode(TimeTrackedModel):
    flow = models.ForeignKey(Flow)
    rule_store = models.ForeignKey(RuleStore)
    children = models.ManyToManyField('flowr.FlowNode')

    def add_child_rule(self, rule):
        """Add a child path in the Flow graph using the given Rule.  A
        corresponding FlowNode will be retrieved or created as necessary.  The
        Rule must be allowed at this stage of the Flow according to the
        corresponding RuleStoreSet.

        :param rule: Rule object to add to the Flow as a child of this node
        :returns: FlowNode that was added
        """
        if rule not in self.allowed_children():
            raise AttributeError('Rule %s is not a valid child of Rule %s' % (
                rule.__name__, self.rule_store.name))

        if self.children.count() > 0 and \
                not self.rule_store.rule.multiple_paths:
            raise AttributeError('Rule %s only allows one child' % (
                self.rule_store.name))

        store = RuleStore.find(self.flow.rule_store_set, rule)
        node, _ = FlowNode.objects.get_or_create(flow=self.flow,
            rule_store=store)
        self.children.add(node)
        return node

    def allowed_children(self):
        """Returns an iterable of the allowed Rule objects that can be
        children of the Rule associated with this FlowNode.
        """
        return self.rule_store.rule.children


class State(TimeTrackedModel):
    flow = models.ForeignKey(Flow)
    current_node = models.ForeignKey(FlowNode, null=True, blank=True)

    def start(self):
        """Kicks of the progression through this Flow.  Calls Rule.on_enter() 
        for the starting Rule for this Flow.
        """
        if not self.flow.start_node:
            raise AttributeError('Flow id=%s has no starting node set' % (
                self.flow.id))

        self.flow.start_node.rule_store.rule.on_enter(self)
        self.current_node = self.flow.start_node
        self.save()

    def next_state(self, rule=None):
        """Proceeds to the next step in the Flow.  Calls the Rule.on_leave()
        for the current rule and the Rule.on_enter() for the Rule being
        entered.  If the current step in the Flow is multipath then a Rule
        must be passed into this call.  

        :param rule: if the current Rule in the Flow is multipath then the 
            next Rule in the Flow must be provided.
        """
        if self.current_node.children.count() == 0:
            raise AttributeError('No next state in this Flow id=%s' % (
                self.flow.id))

        next_node = None
        if self.current_node.rule_store.rule.multiple_paths and \
                len(self.current_node.rule_store.rule.children) > 1:
            if not rule:
                raise AttributeError(('Current Rule %s is multipath but no '
                    'choice was passed in') % self.current_node.rule_store.name)

            for node in self.current_node.children.all():
                if node.rule_store.rule_match(rule):
                    next_node = node
                    break

            if not next_node:
                raise AttributeError(('Current Rule %s is multipath and the '
                    'Rule choice passed in was not in the Flow') % (
                    self.current_node.rule_store.name))
        else:
            # not a multipath Rule, use first (and only) child for next node
            next_node = self.current_node.children.first()

        self.current_node.rule_store.rule.on_leave(self)
        next_node.rule_store.rule.on_enter(self)
        self.current_node = next_node
        self.save()

# ============================================================================
# Directed, Connected(ish), Cyclic Graph

class DCCGraph(models.Model):
    """DCCGraph is a modified Directed, Connected, Cyclic Graph.  It consists
    of a series of nodes connected in a directed fashion with a defined root.
    All nodes in the graph are reachable by traversing the edges from the
    root.  This is similar to a DAG with a single root, except that cycles are
    allowed.

    Each Node in the DCCGraph may have a related data class in order to
    associated arbitrary with the node.  A data class can be any django model,
    that inherits from NodeData, the type of which is specified upon the
    creation of the DCCGraph.
    """
    data_content_type = models.ForeignKey(ContentType)
    root = models.ForeignKey('flowr.Node', blank=True, null=True)

    def __str__(self):
        return 'DCCGraph(id=%s)' % self.id

    @classmethod
    @transaction.atomic
    def factory(cls, data_class, **kwargs):
        """Creates a DCCGraph, a root Node and the Node's associated data
        class instance.  This factory is used to get around the
        chicken-and-egg problem of the DCCGraph and Nodes within it having
        pointers to each other.

        :param data_class: django model class that extends DataNode and is
            used to associate information with the Nodes in this graph
        :param **kwargs: arguments to pass to constructor of the data class
            instance that is to be created for the root node
        :returns: instance of the newly created DCCGraph
        """
        if not issubclass(data_class, DataNode):
            raise AttributeError('data_class must be a DataNode extender')

        content_type = ContentType.objects.get_for_model(data_class)
        graph = DCCGraph.objects.create(data_content_type=content_type)
        node = Node.objects.create(graph=graph)
        data_class.objects.create(node=node, **kwargs)
        graph.root = node
        graph.save()
        return graph

    @classmethod
    def _depth_create(cls, node, child_args, grandchildren):
        child = node.add_child(**child_args)
        for grandkid in grandchildren:
            cls._depth_create(child, grandkid[0], grandkid[1])

    @classmethod
    @transaction.atomic
    def factory_from_graph(cls, data_class, root_args, children):
        """Creates a DCCGraph and corresponding nodes.  The root_args parm is
        a dictionary specifying the parameters for creating a Node and its
        corresponding DataNode from the data_class specified.  The children
        parm is an iterable containing pairs of dictionaries and iterables,
        where the dictionaries specify the parameters for a DataNode and the
        iterable the list of children.

        Example::
            DCCGraph.factory_from_graph(Label, 
                {'name':'A'}, [
                    ({'name':'B', []),
                    ({'name':'C', [])
                ])

        creates the graph::
                 A
                / \
               B   C

        :param data_class: django model class that extends DataNode and is
            used to associate information with the Nodes in this graph
        :param root_args: dictionary of arguments to pass to constructor of
            the data class instance that is to be created for the root node
        :param children: iterable with a list of dictionary and iterable pairs
        :returns: instance of the newly created DCCGraph
        """
        graph = cls.factory(data_class, **root_args)
        for child in children:
            cls._depth_create(graph.root, child[0], child[1])

        return graph

    def find_nodes(self, **kwargs):
        """Searches the data nodes that are associated with this graph using
        the key word arguments as a filter and returns a QuerySet of the
        attached Nodes.

        :param **kwargs: filter arguments for searching the DataNode extender
        :returns: QuerySet of Node objects that are associated with the
            results of querying the DataNode extender
        """
        filter_args = {}
        classname = self.data_content_type.model_class().__name__.lower()
        for key, value in kwargs.items():
            filter_args['%s__%s' % (classname, key)] = value

        return Node.objects.filter(**filter_args)

    def cytoscape_json(self, extra_fields=lambda x:{}):
        data = {
            'nodes':[],
            'edges':[],
        }
        for node in Node.objects.filter(graph=self):
            node_data = {
                'data':{ 
                    'id':node.id,
                }
            }
            for key, value in extra_fields(node).items():
                node_data['data'][key] = value

            data['nodes'].append(node_data)

            for child in node.children.all():
                data['edges'].append({ 
                    'data':{ 
                        'id':'%s_%s' % (node.id, child.id),
                        'source':node.id,
                        'target':child.id,
                    }
                })

        return json.dumps(data)


class DataNode(models.Model):
    node = models.ForeignKey('flowr.Node')

    class Meta:
        abstract = True


class Node(models.Model):
    graph = models.ForeignKey(DCCGraph)
    parents = models.ManyToManyField('self', symmetrical=False,
        related_name='parent_nodes')
    children = models.ManyToManyField('self', symmetrical=False,
        related_name='child_nodes')

    def __str__(self):
        return 'Node(id=%s)' % self.id

    @property
    def data_node(self):
        data_model = self.graph.data_content_type.model_class()
        return data_model.objects.get(node=self)

    def is_root(self):
        return self == self.graph.root

    def add_child(self, **kwargs):
        """Creates a new Node based on the extending class and adds it as a
        child to this Node.

        :param **kwargs: arguments for constructing the data object associated
            with this Node
        :returns: extender of the Node class
        """
        data_class = self.graph.data_content_type.model_class()
        node = Node.objects.create(graph=self.graph)
        data_class.objects.create(node=node, **kwargs)
        node.parents.add(self)
        self.children.add(node)
        return node

    def connect_child(self, node):
        """Adds the given node as a child to this one.  No new nodes are
        created, only connections are made.
        
        :param node: a Node object to connect
        """
        if node.graph != self.graph:
            raise AttributeError('cannot connect nodes from different graphs')

        node.parents.add(self)
        self.children.add(node)

    def _depth_ascend(self, node, visited, limit=False):
        for parent in node.parents.all():
            if limit and parent.is_root():
                visited.add(parent)

            if parent not in visited:
                visited.add(parent)
                self._depth_ascend(parent, visited, limit)

    def ancestors(self):
        """Returns a list of the ancestors of this node."""
        ancestors = set([])
        self._depth_ascend(self, ancestors)
        try:
            ancestors.remove(self)
        except KeyError:
            # we weren't ancestor of ourself, that's ok
            pass

        return list(ancestors)

    def ancestors_root(self):
        """Returns a list of the ancestors of this node but does not pass the
        root node, even if the root has parents due to cycles."""
        if self.is_root():
            return []

        ancestors = set([])
        self._depth_ascend(self, ancestors, True)
        try:
            ancestors.remove(self)
        except KeyError:
            # we weren't ancestor of ourself, that's ok
            pass

        return list(ancestors)

    def _depth_descend(self, node, visited, limit=False):
        for child in node.children.all():
            if limit and child.is_root():
                visited.add(child)

            if child not in visited:
                visited.add(child)
                self._depth_descend(child, visited, limit)

    def descendents(self):
        """Returns a list of descendents of this node."""
        visited = set([])
        self._depth_descend(self, visited)
        try:
            visited.remove(self)
        except KeyError:
            # we weren't descendent of ourself, that's ok
            pass

        return list(visited)

    def descendents_root(self):
        """Returns a list of descendents of this node, if the root node is in
        the list (due to a cycle) it will be included bbut will not pass
        through it.  
        """
        visited = set([])
        self._depth_descend(self, visited, True)
        try:
            visited.remove(self)
        except KeyError:
            # we weren't descendent of ourself, that's ok
            pass

        return list(visited)

    def can_remove(self):
        """Returns True if it is legal to remove this node and still leave the
        graph as a single connected entity, not splitting it into a forest.
        Only nodes with no children or those who cause a cycle can be deleted.
        """
        if self.children.count() == 0:
            return True

        ancestors = set(self.ancestors_root())
        children = set(self.children.all())
        return children.issubset(ancestors)

    def remove(self):
        """Removes the node from the graph.  Note this does not remove the
        associated DataNode.  See :func:`Node.can_remove` for limitations on
        what can be deleted.

        :returns: DataNode associated with the deleted Node
        :raises: AttributeError if called on a Node that cannot be deleted
        """
        if not self.can_remove():
            raise AttributeError('this node cannot be deleted')

        data = self.data_node
        self.parents.remove(self)
        self.delete()
        return data
