import os
import re
import sys
import tkinter as tk

from gui import StellarisConflictResolverGUI
import StellarisDataParser
import StellarisModFilesystem
from model import SmoosherComparator

# TODO: Check for overriding events?


class StellarisModSmoosher:
    file_blacklist = [
        r'.*\.mod',
        r'.*README.*\.',
        r'.*mod description\.txt',
        r'.*\.gitignore',
        r'.*\.git\\.*',
        r'.*thumbnail\..*'
    ]

    files_to_migrate = [
        '.*\.dds',
        '.*\.xcf',
        '.*\.yml',
        '.*\.gfx',
        '.*\.jpg',
        '.*\.png',
        '.*\.gui'
    ]

    def __init__(self, source, target, flags):
        self._source = source
        self._target = target
        self._flags = flags
        self._tk_geometry = None
        self._tk_fullscreen = None

        # Create a file system interface for our application
        target_mod_directory = os.path.join(source_mod_directory, target)
        self._filesystem = StellarisModFilesystem.StellarisModFilesystem(source, target_mod_directory, "clean" in flags,
                                                                         target)
        self._parser = StellarisDataParser.StellarisDataParser()

    def run(self):
        # Loop through mods to identify file sets
        was_staged = False
        for mod_file in self._filesystem.source_files:
            mod_text = self._filesystem.load_file(mod_file)
            data, graph = self._parser.parse_text(mod_file, mod_file, mod_text)
            if data is None:
                continue

            # Check for poorly formatted files
            name = ""
            path = ""
            if "name" in data:
                name = data["name"][0]["value"][0]

            if "path" in data:
                path = data["path"][0]["value"][0]

            if "archive" in data:
                path = data["path"][0]["archive"][0]

            # Strip quotes for this if present and check for validity
            name = name.replace('"', "")
            path = path.replace('"', "")
            if name == "" or path == "":
                print("Malformed mod: " + mod_file)
                continue

            # Handle archives
            if path.endswith(".zip"):
                was_staged = True
                path = self._filesystem.stage_mod(path)

            # Loop through every file
            for root, nested, files in os.walk(path):
                for file in files:
                    full_file = os.path.join(root, file)

                    # Check if file should be ignored
                    if re.match("|".join(self.file_blacklist), full_file):
                        continue

                    # Check if files should me migrated
                    if re.match("|".join(self.files_to_migrate), full_file):
                        continue

                    # Load our mod file into memory
                    text = self._filesystem.load_file(full_file)
                    tree, graph = self._parser.parse_text(name, full_file, text, debug=False)
                    if tree is None:
                        continue

                    # Allow our filesystem to calculate what should be saved and what shouldn't
                    self._smoosh_file(path, full_file, tree, graph)

            # Clean up our staging directory for re-use
            if was_staged:
                self._filesystem.clean_directory(path)
                was_staged = False

    def _smoosh_file(self, mod_root, full_file, file_tree, graph):
        # Calculate our folder hierarchy and create where necessary
        intermediates = self._filesystem.calculate_intermediates(mod_root, full_file)
        created_file, file = self._filesystem.create_intermediates(intermediates)

        # Check if an existing master is present - if not just dump the tree
        if not created_file:
            self._parser.dump(file_tree, file, graph)
            return

        # Conflict the existing
        print("Confilict handling!!!!")
        master_text = self._filesystem.load_file(file)
        master_tree, master_graph = self._parser.parse_text(os.path.basename(file), file, master_text, debug=False)

        # identify and generate an indexed difference
        differ = SmoosherComparator.DataDifferentiator(master_graph, graph)
        differ.compare()

        # Maybe unnecessary as we have now moved to our own data model
        #conflicts, safe = self._identify_conflicts(file, file_tree, master_tree)
        #
        # Resolve our conflicts
        # if len(conflicts) == 0:
        #     resolved_conflicts = dict()
        # else:
        #     resolved_conflicts = self._resolve_conflicts(conflicts)
        # self._modify_master(file, safe, resolved_conflicts)

        # Go through a conflict resolution process
        if differ.get_conflict_count() > 0:
            pass

            # What we want to do here is display a gui with all diffs that has the following properties:
            #   [OLD] [NEW] [BUILDER OUTPUT] [CUSTOM] <- they should also be hideable???
            #       [BUILDER] =
            #           [INFO]  [A] [B]
            #           [CURRENT SECTION]
            #           [EDITABLE RESULT]

    def _resolve_conflicts(self, conflicts):
        resolved = StellarisDataParser.dict_list()
        for conflict_key, conflict_value in conflicts.items():
            if len(conflict_value) > 1:
                print("We need to look into this")
                exit(1)

            # Extract our other variables
            master_type = conflict_value[0]["master"][0]["type"]
            master_source = conflict_value[0]["master"][0]["source"]
            conflict_type = conflict_value[0]["conflicting"][0]["type"]
            conflict_source = conflict_value[0]["conflicting"][0]["source"]

            # Convert out conflict to text and display to allow the user to diff it
            master_text, conflict_text = self._parser.conflict_to_text(conflict_key, conflict_value[0])
            value, source, type = self._visualize_conflict_and_wait(conflict_key, master_text, master_type, master_source, conflict_text, conflict_type, conflict_source)

            # Convert value & source back to a useable object and inject
            branch = StellarisDataParser.dict_list()
            value = self._parser.parse_text("Conflict Resolution", "Conflict Resolution", value)
            branch["value"] = value
            branch["source"] = source
            branch["type"] = type
            resolved[conflict_key] = branch

        return resolved

    def _visualize_conflict_and_wait(self, conflict_key, master_text, master_type, master_source, conflict_text, conflict_type, conflict_source):
        root = tk.Tk()
        gui = StellarisConflictResolverGUI.StellarisConflictResolver(root, self._tk_geometry, self._tk_fullscreen)
        gui.pack(fill="both", expand=True)
        gui.populate(master_text, master_type, master_source, conflict_text, conflict_type, conflict_source)
        root.mainloop()

        self._tk_geometry = gui.geometry_values
        self._tk_fullscreen = gui.fullscreen
        return gui.done_text, gui.result_source, gui.result_type

    def _modify_master(self, file, safe_items, resolved_items):
        for key, item in resolved_items.items():
            safe_items[key] = item

        self._filesystem.remove_file(file)
        self._parser.dump(safe_items, file)



    # def _identify_conflicts(self, file, upstart_tree, master_tree):
    #
    #     # TODO: There are multiple ways of determining conflicts.
    #     # First - already implemented is by root key
    #     # TODO: Second - by id
    #     # TODO: Determine type by file
    #
    #     # TODO: For now we gonna catch here which ones have multi roots, then we can back determine how to behave
    #     for key in upstart_tree:
    #         if len(upstart_tree[key]) > 1:
    #             print("We need to look into this")
    #             exit(1)
    #
    #     for key in master_tree:
    #         if len(master_tree[key]) > 1:
    #             print("We need to look into this")
    #             exit(1)
    #
    #     safe = master_tree.copy()
    #     conflicts = StellarisDataParser.dict_list()
    #     for key in upstart_tree:
    #         if key in safe:
    #             if upstart_tree[key] == master_tree[key]:
    #                 continue
    #
    #             # Obtain the list of blocks that use this key
    #             master_blocks = master_tree[key]
    #             upstart_blocks = upstart_tree[key]
    #
    #             # Check to see if they are different lengths - if so we can safely say they are in conflict
    #             if len(master_blocks) != len(upstart_blocks):
    #                 continue
    #
    #             # Loop through each block to compare identity
    #             count = len(master_blocks)
    #             for upstart_block in upstart_blocks:
    #                 if upstart_block in master_blocks:
    #                     count -= 1
    #
    #             # This occurs when there are multiple key entries and they were out of order
    #             if count == 0:
    #                 continue
    #
    #             # TODO: we could probably recurse on this
    #             # Further, it may be that the contents of each block have been re-arranged
    #             count = len(master_blocks)
    #             for upstart_block in upstart_blocks:
    #                 upstart_block_content = upstart_block["value"]
    #                 upstart_block_length = len(upstart_block_content)
    #
    #                 for master_block in master_blocks:
    #                     master_block_content = master_block["value"]
    #                     master_block_length = len(master_block_content)
    #
    #                     # If the length doesn't match here we don't need to compare them
    #                     if upstart_block_length != master_block_length:
    #                         continue
    #
    #                     # Check the contents of the block to see if they are disordered
    #                     for upstart_item in upstart_block_content:
    #                         found = False
    #                         for master_item in master_block_content:
    #                             if upstart_item == master_item:
    #                                 master_block_length -= 1
    #                                 found = True
    #                                 break
    #
    #                         # Essentially here our selected block definitely does not match this block, so we need to move on
    #                         if not found:
    #                             break
    #
    #                     # It really should be by now
    #                     if master_block_length == 0:
    #                         count -= 1
    #
    #             if count == 0:
    #                 continue
    #
    #             # Assign
    #             conflicts, master_tree = self._identify_conflict(key, conflicts, master_tree, upstart_tree)
    #
    #         else:
    #             safe[key] = upstart_tree[key]
    #
    #     return conflicts, safe
    #
    # def _identify_conflict(self, key, current_conflicts, master_tree, upstart_tree):
    #     if key in current_conflicts:
    #         conflict_properties = current_conflicts[key]
    #     else:
    #         conflict_properties = StellarisDataParser.dict_list()
    #         conflict_properties["master"] = master_tree[key]
    #
    #     conflict_properties["conflicting"] = upstart_tree[key]
    #     current_conflicts[key] = conflict_properties
    #     master_tree.pop(key)
    #     return current_conflicts, master_tree


# Inputs TODO: Improve with argparse
source_mod_directory = sys.argv[1]
target_mod = sys.argv[2]
flags = ""
if len(sys.argv) == 4:
    flags = sys.argv[3]

# Create our application & run
application = StellarisModSmoosher(source_mod_directory, target_mod, flags)
application.run()
