# flowr.models.py
import logging, json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# ============================================================================
# Directed, Connected(ish), Cyclic Graph

class DCCGraph(models.Model):
    """``DCCGraph`` is a modified Directed, Connected, Cyclic Graph.  It
    consists of a series of nodes connected in a directed fashion with a
    defined root.  All nodes in the graph are reachable by traversing the
    edges from the root.  This is similar to a DAG with a single root, except
    that cycles are allowed.

    Each :class:`Node` in the ``DCCGraph`` may have a related data class in
    order to associated arbitrary with the node.  A data class can be any
    django model, that inherits from :class:`BaseNodeData`, the type of which
    is specified upon the creation of the ``DCCGraph``.
    """
    data_content_type = models.ForeignKey(ContentType)
    root = models.ForeignKey('flowr.Node', blank=True, null=True)

    class Meta:
        verbose_name = 'DCC Graph'

    def __str__(self):
        return 'DCCGraph(id=%s)' % self.id

    @classmethod
    @transaction.atomic
    def factory(cls, data_class, **kwargs):
        """Creates a ``DCCGraph``, a root :class:`Node: and the node's
        associated data class instance.  This factory is used to get around
        the chicken-and-egg problem of the ``DCCGraph`` and ``Nodes`` within
        it having pointers to each other.

        :param data_class: django model class that extends
            :class:`BaseNodeData` and is used to associate information with
            the nodes in this graph
        :param **kwargs: arguments to pass to constructor of the data class
            instance that is to be created for the root node
        :returns: instance of the newly created ``DCCGraph``
        """
        if not issubclass(data_class, BaseNodeData):
            raise AttributeError('data_class must be a BaseNodeData extender')

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
        """Creates a ``DCCGraph`` and corresponding nodes.  The root_args parm
        is a dictionary specifying the parameters for creating a :class:`Node`
        and its corresponding :class:`BaseNodeData` subclass from the
        data_class specified.  The children parm is an iterable containing
        pairs of dictionaries and iterables, where the dictionaries specify
        the parameters for a :class:`BaseNodeData` subclass and the iterable
        the list of children.

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

        :param data_class: django model class that extends
            :class:`BaseNodeData` and is used to associate information with
            the Nodes in this graph
        :param root_args: dictionary of arguments to pass to constructor of
            the data class instance that is to be created for the root node
        :param children: iterable with a list of dictionary and iterable pairs
        :returns: instance of the newly created ``DCCGraph``
        """
        graph = cls.factory(data_class, **root_args)
        for child in children:
            cls._depth_create(graph.root, child[0], child[1])

        return graph

    def find_nodes(self, **kwargs):
        """Searches the data nodes that are associated with this graph using
        the key word arguments as a filter and returns a ``QuerySet`` of the
        attached :class:`Node` objects.

        :param **kwargs: filter arguments applied to searching the
            :class:`BaseNodeData` subclass associated with this graph.
        :returns: ``QuerySet`` of :class:`Node` objects 
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
                    'id':'n%s' % node.id,
                }
            }
            for key, value in extra_fields(node).items():
                node_data['data'][key] = value

            data['nodes'].append(node_data)

            for child in node.children.all():
                data['edges'].append({ 
                    'data':{ 
                        'id':'e%s_%s' % (node.id, child.id),
                        'source':'n%s' % node.id,
                        'target':'n%s' % child.id,
                    }
                })

        return json.dumps(data)


class BaseNodeData(models.Model):
    """Subclasses of this object are used to store information associated with
    a :class:`Node` in the :class:`DCCGraph`."""
    node = models.OneToOneField('flowr.Node')

    class Meta:
        abstract = True


class Node(models.Model):
    """Represents a single ``Node`` in the :class:`DCCGraph`.  Can be
    associated with custom data using a subclass of :class:`BaseNodeData`."""
    graph = models.ForeignKey(DCCGraph)
    parents = models.ManyToManyField('self', symmetrical=False,
        related_name='parent_nodes')
    children = models.ManyToManyField('self', symmetrical=False,
        related_name='child_nodes')

    def __str__(self):
        return 'Node(id=%s)' % self.id

    @property
    def data(self):
        data_model = self.graph.data_content_type.model_class()
        return data_model.objects.get(node=self)

    def is_root(self):
        return self == self.graph.root

    def add_child(self, **kwargs):
        """Creates a new ``Node`` based on the extending class and adds it as
        a child to this ``Node``.

        :param **kwargs: arguments for constructing the data object associated
            with this ``Node``
        :returns: extender of the ``Node`` class
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
        
        :param node: a ``Node`` object to connect
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
        the list (due to a cycle) it will be included but will not pass
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
        associated data object.  See :func:`Node.can_remove` for limitations
        on what can be deleted.

        :returns: :class:`BaseNodeData` subclass associated with the deleted
            Node
        :raises: AttributeError if called on a Node that cannot be deleted
        """
        if not self.can_remove():
            raise AttributeError('this node cannot be deleted')

        data = self.data
        self.parents.remove(self)
        self.delete()
        return data

    def prune(self):
        """Removes the node and all descendents without looping back past the
        root.  Note this does not remove the associated data objects.

        :returns: list of :class:`BaseDataNode` subclassers associated with
        the removed Nodes.
        """
        targets = self.descendents_root()
        try:
            targets.remove(self.graph.root)
        except ValueError:
            # root wasn't in the target list, no problem
            pass

        results = [n.data for n in targets]
        results.append(self.data)
        for node in targets:
            node.delete()

        for parent in self.parents.all():
            parent.children.remove(self)

        self.delete()
        return results

    def prune_list(self):
        """Returns a list of nodes that would be removed if prune were called
        on this element.
        """
        targets = self.descendents_root()
        try:
            targets.remove(self.graph.root)
        except ValueError:
            # root wasn't in the target list, no problem
            pass

        targets.append(self)
        return targets

# ============================================================================

"""
Flowr Rule System
=================

Most state machine libraries are "static" and require the flow in the state
machine to be definied programmatically.  Flowr is designed so that you can
build state machine flows and store them in a database.  There are two key
concepts: rule graphs and state machines.  The programmer defines one or more
sets of rules that describe the allowed flow between states, the user can then
use the GUI tools to construct state machines that follow these rules and
store the machines in the database.  The state machines can then be
instantiated for processing the flow which triggers call-back mechanisms in
the rule objects on entering and leaving a state.

Rules are defined by subclassing the :class:`Rule` class and filling in the
"children" attribute.  Cycles are allowed, so :class:`Rule` instances can
point to each other or themselves.  Once a hierarchy of :class:`Rule` classes
have been defined, a :class:`RuleSet` can be created and stored in the
database.  :class:`Flow` objects are created with the GUI and describe the
flow through a state machine with the state flow graph being a subset of those
defined by the collection of :class:`Rule` objects that were registered in the
:class:`RuleSet` instance.

The :class:`State` object is an instantiation of a traversal of the state
machine represented by a :class:`Flow`.  Once there are :class:`State` objects
for a :class:`Flow`, the :class:`Flow` can no longer be edited.

Definitions:

* :class:`Rule` -- a base class for rules that the programmer defines which 
    specifies what other Rule objects can be connected to and what happens
    when a state is entered and exited
* :class:`RuleSet` -- a registery for the collections of Rule subclasses 
* :class:`Flow` -- user defined state machine based on a :class:`RuleSet` 
    instance
* :class:`State` -- an instance of a state machine and its current state

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


A :class:`RuleSet` object is created using the factory and passing in the
single starting point of our allowed flows::

    RuleSet.factory('My Rules', A)

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

class _MetaRule(type):
    def __new__(cls, name, bases, classdict):
        klass = type.__new__(cls, name, bases, dict(classdict))
        klass.class_label = '%s.%s' % (klass.__module__, klass.__name__)
        klass.name = klass.__name__
        return klass

class Rule(metaclass=_MetaRule):
    """Subclasses of ``Rule`` are associated with states in the flow graph.
    As states are entered and exited, the :func:`Rule.on_enter` and 
    :func:`Rule.on_leave` methods are called respectively.

    :param children: list of other subclasses of ``Rule`` that
        are allowed as children of this node in the flow.  Cycles are allowed
        even with the ``Rule`` being its own child.
    :param multiple_paths: ``True`` if the exit of this state can have
        multiple choices.  Multiple children mean you can construct different
        exits in the flow, multiple paths mean there is a branching choice in
        the flow that can go down the path of more than one of the children.
        Defaults to ``False``.
    :param has_edit_screen: ``True`` if the GUI should show an edit screen
        when a node for this ``Rule`` is selected.   If ``True``, the
        :func:`Rule.edit_screen` method will be called when the user clicks on
        an associated node.  Defaults to ``False``.
    """
    children = []
    multiple_paths = False
    has_edit_screen = False

    @classmethod
    def on_enter(cls, state):
        """Called when a state corresponding to this ``Rule`` is entered."""
        pass

    @classmethod
    def on_leave(cls, state):
        """Called when a state corresponding to this ``Rule`` is left."""
        pass

    @classmethod
    def edit_screen(cls, request, flow_node_data):
        """Called if ``Rule.has_edit_screen`` is ``True`` and the user clicks
        on a flow node associated with this ``Rule`.  

        :returns: implementation should return the HTML to display when the
            user selects this node on the edit screen.
        """
        raise NotImplementedError()


class RuleSet(TimeTrackedModel):
    """Contains the name of a :class:`Rule` subclass that acts as the root in
    a rule graph.  All :class:`Flow` objects are associated with a ``RuleSet``
    and the state flow graphs of the flow are a subset of those defined in the
    :class:`Rule` objects.
    """
    name = models.CharField(max_length=80)
    root_rule_label = models.CharField(max_length=80)

    class Meta:
        verbose_name = 'Rule Set'

    def __init__(self, *args, **kwargs):
        super(RuleSet, self).__init__(*args, **kwargs)

        # ---
        # define:
        #   root_rule
        #
        # as parameters on class
        if self.root_rule_label:
            (modname, classname) = self.root_rule_label.rsplit('.', 1)
            mod = __import__(modname, globals(), locals(), [classname])
            self.root_rule = getattr(mod, classname)
            self.root_rule_name = self.root_rule.__name__

    def __str__(self):
        return 'RuleSet(id=%s, %s:%s)' % (self.id, self.name,
            self.root_rule_label)

    @classmethod
    def factory(self, name, root_rule):
        return RuleSet.objects.create(name=name,
            root_rule_label=root_rule.class_label)


    def _depth_cyto_traverse(self, rule, nodes, edges, visited):
        if rule not in visited:
            visited.add(rule)

            nodes.append({
                'data':{ 
                    'id':rule.name,
                    'label':rule.name,
                }
            })

            for child in rule.children:
                edges.append({ 
                    'data':{ 
                        'id':'%s_%s' % (rule.name, child.name),
                        'source':rule.name,
                        'target':child.name,
                    }
                })
                self._depth_cyto_traverse(child, nodes, edges, visited)

    def cytoscape_json(self, extra_fields=lambda x:{}):
        nodes = []
        edges = []
        visited = set([])

        self._depth_cyto_traverse(self.root_rule, nodes, edges, visited)

        data = {
            'nodes':nodes,
            'edges':edges,
        }

        return json.dumps(data)

# ============================================================================
# Flow Models
# ============================================================================

class FlowNodeData(TimeTrackedModel, BaseNodeData):
    rule_label = models.CharField(max_length=80)

    class Meta:
        verbose_name = 'Flow Node Data'
        verbose_name_plural = 'Flow Node Data'

    def __init__(self, *args, **kwargs):
        super(FlowNodeData, self).__init__(*args, **kwargs)

        # ---
        # define:
        #   rule
        #   flow
        #
        # as parameters on object
        if self.rule_label:
            (modname, classname) = self.rule_label.rsplit('.', 1)
            mod = __import__(modname, globals(), locals(), [classname])
            self.rule = getattr(mod, classname)
            self.rule_name = self.rule.__name__

        if self.node:
            try:
                self.flow = Flow.objects.get(state_graph=self.node.graph)
            except Flow.DoesNotExist:
                # first time a Flow is created there is a chicken-and-egg
                # problem with the Flow and its first Node, ignore it
                self.flow = None

    def __str__(self):
        return 'FlowNodeData(id=%s, %s)' % (self.id, self.rule_label)

    def _child_allowed(self, child_rule):
        """Called to verify that the given rule can become a child of the
        current node.  

        :raises AttributeError: if the child is not allowed
        """
        num_kids = self.node.children.count()
        num_kids_allowed = len(self.rule.children)
        if not self.rule.multiple_paths:
            num_kids_allowed = 1

        if num_kids >= num_kids_allowed:
            raise AttributeError('Rule %s only allows %s children' % (
                self.rule_name, self.num_kids_allowed))

        # verify not a duplicate
        for node in self.node.children.all():
            if node.data.rule_label == child_rule.class_label:
                raise AttributeError('Child rule already exists')

        # check if the given rule is allowed as a child
        if child_rule not in self.rule.children:
            raise AttributeError('Rule %s is not a valid child of Rule %s' % (
                child_rule.__name__, self.rule_name))

    def add_child_rule(self, child_rule):
        """Add a child path in the :class:`Flow` graph using the given 
        :class:`Rule` subclass.  This will create a new child :class:`Node` in
        the associated :class:`Flow` object's state graph with a new
        :class:`FlowNodeData` instance attached.
        
        The :class:`Rule` must be allowed at this stage of the flow according
        to the hierarchy of rules.

        :param child_rule: :class:`Rule` class to add to the flow as a child of 
            :class:`Node` that this object owns
        :returns: ``FlowNodeData`` that was added
        """
        self._child_allowed(child_rule)
        child_node = self.node.add_child(rule_label=child_rule.class_label)
        return child_node.data

    def connect_child(self, child_node):
        """Adds a connection to an existing rule in the :class`Flow` graph.
        The given :class`Rule` subclass must be allowed to be connected at
        this stage of the flow according to the hierarchy of rules.

        :param child_node: ``FlowNodeData`` to attach as a child
        """
        self._child_allowed(child_node.rule)
        self.node.connect_child(child_node.node)


class Flow(TimeTrackedModel):
    name = models.CharField(max_length=25)
    rule_set = models.ForeignKey(RuleSet)
    state_graph = models.ForeignKey(DCCGraph)

    def __str__(self):
        return 'Flow(id=%s %s)' % (self.id, self.name)

    @classmethod
    def factory(cls, name, rule_set):
        graph = DCCGraph.factory(FlowNodeData, 
            rule_label=rule_set.root_rule_label)
        flow = Flow.objects.create(name=name, rule_set=rule_set,
            state_graph=graph)
        return flow

    def in_use(self):
        """Returns True if there is a :class:`State` object that uses this
        ``Flow``"""
        state = State.objects.filter(flow=self).first()
        return bool(state)

    @property
    def root_data(self):
        """Returns the :class:`FlowDataNode` object for the root node in the
        graph."""
        return self.state_graph.root.data


@receiver(post_delete, sender=Flow)
def _flow_post_delete(sender, **kwargs):
    # Flow creates a DCCGraph instance, this should be removed when Flow is
    # deleted
    kwargs['instance'].state_graph.delete()


class State(TimeTrackedModel):
    flow = models.ForeignKey(Flow)
    current_node = models.ForeignKey(Node)

    @classmethod
    def start(self, flow):
        """Factory method for a running state based on a flow.  Creates and
        returns a ``State`` object and calls the associated
        :func:`Rule.on_enter` method.

        :param flow: :class:`Flow` which defines this state machine
        :returns: newly created instance
        """
        state = State.objects.create(flow=flow, 
            current_node=flow.state_graph.root)
        flow.state_graph.root.data.rule.on_enter(state)
        return state

    def __str__(self):
        return 'State(id=%s current=%s)' % (self.id,
            self.current_node.data.rule_name)

    def next_state(self, rule=None):
        """Proceeds to the next step in the flow.  Calls the associated
        :func:`Rule.on_leave` method for the for the current rule and the
        :func:`Rule.on_enter` for the rule being entered.  If the current step
        in the flow is multipath then a valid :class:`Rule` subclass must be
        passed into this call.  

        If there is only one possible path in the flow and a :class:`Rule` is
        given it will be ignored.

        :param rule: if the current :class:`Rule` in the :class:`Flow` is
            multipath then the next :class:`Rule` in the flow must be provided.
        """
        num_kids = self.current_node.children.count()
        next_node = None
        if num_kids == 0:
            raise AttributeError('No next state in this Flow id=%s' % (
                self.flow.id))
        elif num_kids == 1:
            next_node = self.current_node.children.first()
        else:
            if not rule:
                raise AttributeError(('Current Rule %s is multipath but no '
                    'choice was passed in') % self.current_node.data.rule_name)

            for node in self.current_node.children.all():
                if node.data.rule_label == rule.class_label:
                    next_node = node
                    break

            if not next_node:
                raise AttributeError(('Current Rule %s is multipath and the '
                    'Rule choice passed in was not in the Flow') % (
                    self.current_node.data.rule_name))

        self.current_node.data.rule.on_leave(self)
        next_node.data.rule.on_enter(self)
        self.current_node = next_node
        self.save()
