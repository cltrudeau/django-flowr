from flowr.models import Rule

done_enter = []
done_leave = []

class LocalRule(Rule):
    @classmethod
    def on_enter(cls, state):
        global done_enter
        done_enter.append(cls.__name__)

    @classmethod
    def on_leave(cls, state):
        global done_leave
        done_leave.append(cls.__name__)

    @classmethod
    def display_name(cls):
        return cls.__name__


# Rule Structure:
#
#           A
#          / \
#         B   C
#            / \
#           D   E
#                \
#                 A (loops)

class E(LocalRule):
    children = []

class D(LocalRule):
    children = []

class C(LocalRule):
    children = [D, E]
    multiple_paths = True
    has_edit_screen = True

    @classmethod
    def edit_screen(cls, request, flow_node_data):
        return 'Custom HTML for node: %s' % flow_node_data

class B(LocalRule):
    children = []

class A(LocalRule):
    children = [B, C]

E.children = [A]
