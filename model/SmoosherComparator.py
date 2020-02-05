def compare(master_graph, graph):
    diff = DiffRecord(master_graph, graph)
    diff.compare()
    graph.compare(diff, master_graph)
    return diff


class NewDiff:
    # TODO: Add unique indexing per doc which we can use to reference diff spots
    # TODO: Centralize information source to provide us with everything we need to index and represent a diff
    def __init__(self, information_source):
        self.diff_type = "NEW"
        self.diff_id = information_source.unique_id


class DeleteDiff:
    def __init__(self, information_source):
        self.diff_type = "DELETE"
        self.diff_id = information_source.unique_id


class ChangeDiff:
    def __init__(self, information_source_1, information_source_2):
        self.diff_type = "CHANGE"
        self.source_diff_id = information_source_1.unique_id
        self.target_diff_id = information_source_2.unique_id


class DiffRecord:
    def __init__(self, original_graph, difference_graph):
        self.original_graph = original_graph
        self.difference_graph = difference_graph
        self.diffs = list()

    def compare(self):
        self._compare_nodes(self.original_graph, self.difference_graph)

    def _compare_nodes(self, original_node, different_node):
        # Compare assignments
        for different_assignment in different_node.assignments:
            original_assignment = original_node.has_comparable_assignment(different_assignment)
            self._generate_diff_for_assignment(original_assignment, different_assignment)

        # We do this in the other direction so we can highlight them as 'deletions'
        # despite that not necessarily being the case
        for original_assignment in original_node.assigments:
            different_assignment = different_node.has_comparable_assignment(original_assignment)
            if different_assignment is None:
                self._generate_diff_for_assignment(original_assignment, different_assignment)

        # Compare nodes
        for diff_node in different_node.child_nodes:
            source_node = original_node.has_comparable_node(diff_node)
            self._generate_diff_for_node(source_node, diff_node)

        # As above
        for source_node in original_node.child_nodes:
            diff_node = different_node.has_comparable_assignment(source_node)
            if diff_node is None:
                self._generate_diff_for_node(source_node, diff_node)

    def _generate_diff_for_assignment(self, original_assignment, different_assignment):
        if original_assignment is None:
            self.diffs.append(NewDiff(different_assignment))

        if different_assignment is None:
            self.diffs.append(DeleteDiff(original_assignment))

        if original_assignment != different_assignment:
            self.diffs.append(ChangeDiff(original_assignment, different_assignment))
