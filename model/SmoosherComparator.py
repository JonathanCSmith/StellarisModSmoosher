class Difference:
    def __init__(self, type, original, latest):
        self.type = type
        self.original = original
        self.latest = latest


class Addition(Difference):
    def __init__(self, latest):
        super().__init__("addition", None, latest)


class Deletion(Difference):
    def __init__(self, original):
        super().__init__("deletion", original, None)


class Change(Difference):
    def __init__(self, original, latest):
        super().__init__("change", original, latest)


class DataDifferentiator:
    def __init__(self, original, latest):
        self.original = original
        self.latest = latest
        self.original_changes = dict()
        self.latest_changes = dict()

    def get_conflict_count(self):
        return len(self.original_changes) + len(self.latest_changes)

    def compare(self):
        # Quick and eminently defeatable check to validate if our docs have been pruned ahead of time
        if not self.original.is_pruned:
            self.original.prune_children()

        if not self.latest.is_pruned:
            self.latest.prune_children()

        # Compare our attribute - this is easy as we can use the key for identity
        original_attributes = self.original.attributes.copy()
        latest_attributes = self.latest.attributes.copy()
        while len(original_attributes) > 0:
            original_attribute = original_attributes.pop()
            found = False
            for latest_attribute in latest_attributes:

                # Check if the key is the same if so we can either register a change or its the same
                if original_attribute.key == latest_attribute.key:
                    if not original_attributes.equals(latest_attribute):
                        self._register_difference(Change(original_attribute, latest_attribute))

                    latest_attributes.remove(latest_attribute)  # Safe as we break out of loop
                    found = True
                    break

            # If it wasn't found then we need to assign it as a deletion
            if not found:
                self._register_difference(Deletion(original_attribute))

        # Any remaining in latest_attributes are new
        for latest_attribute in latest_attributes:
            self._register_difference(Addition(latest_attribute))

        # Cheeky assumption: Root node (not doc) == identity of branch. We also assume that key is sufficiently unique -
        # normally this would not be true, but we special case for situations where it's not Note its only going to
        # be true for a root node
        for node in self.original:

            # Lets obtain the leaves
            # Now evaluate leafs on both (or do this automatically when constructing the tree)
            original_leaves = node.get_leaves().copy()
            latest_leaves = node.get_leaves().copy()

            # Work through each of the original leaves until we have none left
            while len(original_leaves) > 0:
                original_leaf = original_leaves.pop()
                found = False
                potential_matches = list()
                latest_leaf = None

                # Side by side comparison to latest leaves
                for latest_leaf in latest_leaves:

                    # Assess whether the leaves are the same - note leaves may not be unique
                    if original_leaf.key == latest_leaf.key:

                        # In this scenario we can assume identity - it may be a false assumption but its not a bad one
                        if original_leaf.get_branch_path() == latest_leaf.get_branch_path():
                            found = True

                        # Otherwise we should store the candidates
                        potential_matches.append(latest_leaf)

                # This leaf has a one to one match
                if found:

                    # Evaluate if there is a change to register
                    if not original_leaf.equals(latest_leaf):
                        self._register_difference(Change(original_leaf, latest_leaf))

                    latest_leaves.remove()  # Safe as we break out of loop

                # If we have no matches then we can assume its a deletion
                if len(potential_matches) == 0:
                    self._register_difference(Deletion(original_leaf))

                # One fuzzy match means we could assume its been moved
                elif len(potential_matches) == 1:
                    self._register_difference(Change(original_leaf, latest_leaf))
                    latest_leaves.remove(latest_leaf)  # Safe as we break out of loop

                # Otherwise we should assume this is a deletion rather than attempting to calculate reassignments
                self._register_difference(Deletion(original_leaf))

            # All remaining leaves in the latest list can be assigned as additions
            for leaf in latest_leaves:
                self._register_difference(Addition(leaf))

    def _register_difference(self, difference):
        # Store the relevant ids of where the diff is - specifically where the divergence originates in the tree by
        # calculating the true origin of this diff by recursing up plain trunks until a branch is reached
        if isinstance(difference, Addition):
            real_id = difference.latest.compute_branch_point_successor()
            self.latest_changes[real_id] = difference

        elif isinstance(difference, Deletion):
            real_id = difference.original.compute_branch_point_successor()
            self.original_changes[real_id] = difference

        # Note this is not entirely correct as a new branching point could have been added in latest which would mean
        # not enough is highlighted in latest - but its a minor gripe
        else:
            original_real_id = difference.original.compute_branch_point_successor()
            self.original_changes[original_real_id] = difference
            latest_real_id = difference.latest.compute_branch_point_successor()
            self.latest_changes[latest_real_id] = difference
