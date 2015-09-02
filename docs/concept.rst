Introduction
************

Flowr is based on two key concepts: rules and flow graphs.  A flow graph is
the dynamic state machine that the user can create and is stored in the
database.  Multiple instances of states can then be active for any given flow
graph.  One or more sets of rules is defined by the programmer which limits
the progression of possible states in a flow graph.

Rules are defined by subclassing the :class:`.Rule` class and filling in the
"children" attribute.  Cycles are allowed, so :class:`.Rule` instances can
point to each other or themselves.  Once a hierarchy of :class:`.Rule` classes
have been defined, a :class:`.RuleSet` can be created and stored in the
database.  :class:`.Flow` objects are created with the GUI and describe the
flow through a state machine with the state flow graph being a subset of those
defined by the collection of :class:`.Rule` objects that were registered in
the :class:`.RuleSet` instance.

The :class:`.State` object is an instantiation of a traversal of the state
machine represented by a :class:`.Flow`.  Once there are :class:`.State`
objects for a :class:`.Flow`, the :class:`.Flow` can no longer be edited.

Definitions:

* :class:`.Rule` -- a base class for rules that the programmer defines which 
    specifies what other Rule objects can be connected to and what happens
    when a state is entered and exited
* :class:`.RuleSet` -- a registery for the collections of Rule subclasses 
* :class:`.Flow` -- user defined state machine based on a :class:`.RuleSet` 
    instance
* :class:`.State` -- an instance of a state machine and its current state

Example
+++++++

A user defines the following :class:`.Rule` subclasses::

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


A :class:`.RuleSet` object is created using the factory and passing in the
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
the :class:`.Rule` definitions.  The second is not allowed because "B" has no
allowed children.
