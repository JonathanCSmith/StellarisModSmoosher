def correct_value(value):
    if isinstance(value, list):
        value = value[0]

    if isinstance(value, bool):
        if value:
            string_value = "yes"
        else:
            string_value = "no"
    else:
        string_value = str(value)

    return string_value


class InformationSource:
    def __init__(self, root, key, source):
        self.unique_id = root.get_unique_id()
        self.key = key
        self.source = source.replace(" ", "_")


class Node(InformationSource):
    def __init__(self, root, assignee, source):
        self.assignee = assignee
        self.child_nodes = list()
        self.assignments = list()
        index = assignee  # TODO: We can modify this later with assignment digging to identify when an id / key is provided (its key)
        super().__init__(root, index, source)

    def __iter__(self):
        return NodeIterator(self)

    def add_node(self, node):
        if not isinstance(node, Node):
            print("Cannot add: " + str(node) + " to the node as it is not a Node object")
            exit(1)  # TODO: Remove
            return

        self.child_nodes.append(node)

    def add_assignment(self, assignment):
        if not isinstance(assignment, Assignment):
            print("Cannot add: " + str(assignment) + " to the node as it is not an assignment object")
            exit(1)  # TODO: Remove
            return

        self.assignments.append(assignment)

    def __repr__(self):
        return "Node: " + self.assignee + " with " + str(len(self.child_nodes)) + " children and " + str(
            len(self.assignments)) + " assignments"

    def write(self, file_handle, tab_count):
        tabs = "    " * tab_count
        file_handle.write(tabs + self.assignee + " = {\n")
        tab_count += 1

        # Write out our node content
        for assignment in self.assignments:
            assignment.write(file_handle, tab_count)

        for node in self.child_nodes:
            node.write(file_handle, tab_count)

        tab_count -= 1
        file_handle.write(tabs + "} #ORIGIN = " + self.source + "\n")


class Document(Node):
    def __init__(self, assignee, source):
        super().__init__(self, assignee, source)
        self.__id_count = -1

    def __repr__(self):
        return "Document for: " + self.assignee

    def get_unique_id(self):
        self.__id_count += 1
        return self.__id_count

    def write(self, file_handle, tab_count):
        for assignment in self.assignments:
            assignment.write(file_handle, tab_count)

        for node in self.child_nodes:
            node.write(file_handle, tab_count)

    def compare(self, diff_record, cannonical_document):
        # Loop though our assignments - identical keys are identical
        for assignment in self.assignments:
            master_assignment = cannonical_document.contains_assignment(assignment)
            if master_assignment is not None:
                diff_record.diff_assignment(assignment, master_assignment)
            else:
                diff_record.diff_assignment(assignment, None)

    def contains_assignment(self, assignment_to_compare):
        for assignment in self.assignments:
            if assignment.assignee == assignment_to_compare.assignee:
                return assignment

        return None


class NodeIterator:
    def __init__(self, document):
        self.__document = document
        self.__index = 0

    def __next__(self):
        if self.__index < len(self.__document.nodes):
            result = self.__document.nodes[self.__index]
            self.__index += 1
            return result

        raise StopIteration


class Assignment(InformationSource):
    def __init__(self, root, assignee, type, value, source):
        super().__init__(root, assignee, source)
        self.assignee = assignee
        self.type = type
        self.value = value

    def __repr__(self):
        return "Assignment: " + self.assignee + " " + self.type + " " + str(self.value)

    def write(self, file_handle, tab_count):
        tabs = "    " * tab_count
        file_handle.write(tabs + self.assignee + " " + self.type + " " + correct_value(
            self.value) + " #ORIGIN = " + self.source + "\n")


class StatementAssignment(Assignment):
    def __init__(self, root, assignment, source):
        super().__init__(root, assignment, "", "", source)

    def __repr__(self):
        return "Statement: " + self.assignee

    def write(self, file_handle, tab_count):
        tabs = "    " * tab_count
        file_handle.write(tabs + self.assignee + " #ORIGIN = " + self.source + "\n")
