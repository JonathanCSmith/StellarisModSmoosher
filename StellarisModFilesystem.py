import glob
import os
import shutil
import zipfile


class StellarisModFilesystem:

    def __init__(self, source, target, should_clean_if_required, mod):
        self.source = source
        self.target = target

        # Quick check for path validity
        self.source_files = self.list_files(source, "*.mod")
        if len(self.source_files) == 0:
            print("No mods were found in the provided mod directory - either download some mods first or you have provided the wrong path.")
            exit(1)

        # Create our mod directory
        if not os.path.exists(target):
            os.mkdir(target)
        elif os.listdir(target):
            if should_clean_if_required:
                self.clean_directory(target)
            else:
                print("Target mod exists and is not empty. If you wish to clean this folder rerun the program with third argument 'clean'")
                exit(1)

        # Create a staging zone for a place to unpack zipped mods for integration
        self.stage_directory = os.path.join(target, "temporary_staging")
        if not os.path.exists(self.stage_directory):
            os.mkdir(self.stage_directory)

        # Create our mappings
        self._file_mappings = dict()
        for key, value in self.__raw_file_mappings.items():
            self._file_mappings[key] = mod + value

    def list_files(self, directory, regex):
        return glob.glob(directory + "/" + regex)

    def remove_file(self, file):
        os.unlink(os.path.join(file))

    def clean_directory(self, directory):
        # Clean up our staging directory
        for root, dirs, files in os.walk(directory):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    def stage_mod(self, path):
        with zipfile.ZipFile(path, "r") as zip_file:
            zip_file.extractall(self.stage_directory)

        return self.stage_directory

    def load_file(self, file):
        # Load in our data
        with open(file, "r") as mod_file:
            src = mod_file.read()

        return src

    def calculate_intermediates(self, mod_root, full_file):
        root_parts = self._split_path(mod_root)
        file_parts = self._split_path(full_file)
        return [x for x in file_parts if x not in root_parts]

    def _split_path(self, path):
        allparts = []
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path:  # sentinel for relative paths
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts

    def create_intermediates(self, intermediates):
        file = intermediates.pop()
        current_path = self.target
        for folder in intermediates:
            current_path = os.path.join(current_path, folder)
            if not os.path.exists(current_path):
                os.mkdir(current_path)

        file = self._translate_file(intermediates, file)
        file = os.path.join(current_path, file)
        return os.path.exists(file), file

    __absolute_file_mappings = [
        "00_common_categories.txt",
        "00_diplomacy_economy.txt",
        "00_urban_districts.txt",
        "02_rural_districts.txt"
    ]

    __raw_file_mappings = {
        "common/ambient_objects": "_ambient_objects.txt",
        "common/armies": "_armies.txt",
        "common/ascension_perks": "_ascension_perks.txt",
        "common/buildings": "_buildings.txt",
        "common/button_effects": "_button_effects.txt",
        "common/decisions": "_decisions.txt",
        "common/deposits": "_deposits.txt",
        "common/defines": "_defines.txt",
        "common/diplomatic_actions": "_diplomatic_actions.txt",
        "common/edicts": "_edicts.txt",
        "common/ethics": "_ethics.txt",
        "common/governments": "_governments.txt",
        "common/on_actions": "_on_actions.txt",
        "common/opinion_modifiers": "_opinion_modifiers.txt",
        "common/policies": "_policies.txt",
        "common/pop_jobs": "_jobs.txt",
        "common/scripted_triggers": "_scripted_triggers.txt",
        "common/ship_sizes": "_ship_sizes.txt",
        "common/special_projects": "_special_projects.txt",
        "common/species_rights": "_living_standards.txt",
        "common/starbase_buildings": "_starbase_buildings.txt",
        "common/starbase_modules": "_starbase_modules.txt",
        "common/static_modifiers": "_static_modifiers.txt",
        "common/technology": "_tech.txt",
        "common/trade_conversions": "_trade_conversions.txt",
        "common/traits": "_combined_traits.txt"
    }

    __copy_direct = [
        "events"
    ]

    def _translate_file(self, intermediates, file):
        if file[0].isdigit() and file[1].isdigit():
            print("is: " + file + " a core file?")
            return file

        if file in self.__absolute_file_mappings:
            return file

        key = "/".join(intermediates)
        if key in self.__copy_direct:
            return file

        if key in self._file_mappings:
            return self._file_mappings[key]

        return "unknown"

