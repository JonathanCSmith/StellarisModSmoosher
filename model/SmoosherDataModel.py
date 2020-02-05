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


class MetadataHolder:
    def __init__(self, root, key, assignee, source):
        self.root_graph = root
        self.unique_id = self.root_graph.unique_id(self)
        self.key = key
        self.assignee = assignee
        self.source = source.replace(" ", "_")
        self.parent = None

    def set_parent(self, parent):
        self.parent = parent


class Leaf(MetadataHolder):
    def __init__(self, root, key, source):
        super().__init__(root, key, key, source)

    def equals(self, query_attribute):
        exit(1)
        pass

    def get_branch_path(self):
        exit(1)
        pass

    def compute_branch_point_successor(self):
        # Travese rootwards to identify the branching point and return the id
        found = False
        holder = self.parent
        first_trunk = None
        while not found:
            found = holder.is_branch_point()
            if not found:
                first_trunk = holder
                holder = first_trunk.traverse_rootwards()

                if holder is None:
                    print("Could not find a branch point up to root")
                    exit(1)

        return first_trunk.unique_id

    def write_to_text(self, tab_count):
        pass


class Attribute(Leaf):
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

    def write_to_text(self, tab_count):
        tabs = "    " * tab_count
        return tabs + self.assignee + " " + self.type + " " + correct_value(self.value) + " #ORIGIN = " + self.source


class ListAttribute(Leaf):
    def __init__(self, root, assignee, source):
        super().__init__(root, assignee, source)

    def __repr__(self):
        return "Statement: " + self.assignee

    def write(self, file_handle, tab_count):
        tabs = "    " * tab_count
        file_handle.write(tabs + self.assignee + " #ORIGIN = " + self.source + "\n")

    def write_to_text(self, tab_count):
        tabs = "    " * tab_count
        return tabs + self.assignee + " #ORIGIN = " + self.source


class Node(MetadataHolder):

    use_default = True  # TODO: Remove this

    def __init__(self, root, key, source):
        self.attributes = list()  # technically this could be a dict
        self.children = list()
        self.is_pruned = False

        # TODO: We can modify this later with assignment digging to identify when an id / key is provided (its key)
        if self.use_default:
            real_index = key
        else:
            real_index = ""  # Not a thing yet - but we should grab the 'key' property

        super().__init__(root, key, real_index, source)

    def add_attribute(self, attribute):
        if not isinstance(attribute, Leaf):
            print("Cannot add: " + str(attribute) + " to the node as it is not an Lead object")

        attribute.set_parent(self)
        self.attributes.append(attribute)

    def add_node(self, node):
        if not isinstance(node, Node):
            print("Cannot add: " + str(node) + " to the node as it is not a Node object")
            exit(1)  # TODO: Remove
            return

        node.set_parent(self)
        self.children.append(node)

    def write(self, file_handle, tab_count):
        tabs = "    " * tab_count
        file_handle.write(tabs + self.assignee + " = {\n")
        tab_count += 1

        # Write out our node content
        for attribute in self.attributes:
            attribute.write(file_handle, tab_count)

        for node in self.children:
            node.write(file_handle, tab_count)

        tab_count -= 1
        file_handle.write(tabs + "} #ORIGIN = " + self.source + "\n")

    def write_header_to_text(self, tab_count):
        tabs = "    " * tab_count
        return tabs + self.assignee + " = {\n"

    def write_footer_to_text(self, tab_count):
        tabs = "    " * tab_count
        return tabs + "} #ORIGIN = " + self.source + "\n"

    def traverse_rootwards(self):
        return self.parent

    def is_branch_point(self):
        return len(self.attributes) + len(self.children) > 1

    def __iter__(self):
        return NodeIterator(self)

    def __repr__(self):
        return "Node: " + self.assignee + " with " + str(len(self.children)) + " children and " + str(len(self.attributes)) + " assignments"


class Document(Node):
    def __init__(self, assignee, source):
        self.__id_count = 0
        self.node_keys = list()
        self.objects = dict()
        super().__init__(self, assignee, source)

    def __repr__(self):
        return "Document for: " + self.assignee

    def add_node(self, node):
        # We expect that at this level, each node has a unique identifier *somewhere*. See Node for more info
        if node.key in self.node_keys:
            print("Non unique level 1 node.")
            exit(1)

        super().add_node(node)

    def get_unique_id(self, obj):
        if obj in self.objects:
            return self.objects[obj]

        unique_id = self.__id_count
        self.__id_count += 1
        self.objects[obj] = unique_id
        return unique_id

    def write(self, file_handle, tab_count):
        for attribute in self.attributes:
            attribute.write(file_handle, tab_count)

        for node in self.children:
            node.write(file_handle, tab_count)

    def compare(self, diff_record, cannonical_document):
        # Loop though our assignments - identical keys are identical
        for attribute in self.attributes:
            master_attribute = cannonical_document.contains_assignment(attribute)
            if master_attribute is not None:
                diff_record.diff_attribute(attribute, master_attribute)
            else:
                diff_record.attribute(attribute, None)

    def contains_assignment(self, assignment_to_compare):
        for assignment in self.children:
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
