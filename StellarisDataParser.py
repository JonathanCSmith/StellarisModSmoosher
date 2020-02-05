import copy

import pyparsing as pp
import re

from model import SmoosherDataModel


class dict_list(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(dict_list, self).__setitem__(key, [])

        if isinstance(value, list):
            self[key].extend(value)
        else:
            self[key].append(value)

    def __eq__(self, other):
        if not isinstance(other, dict_list):
            return False

        if "value" in self and "value" in other:
            return self["value"] == other["value"]

        return super().__eq__(other)

    def __ne__(self, other):
        if not isinstance(other, dict_list):
            return True

        if "value" in self and "value" in other:
            return self["value"] != other["value"]

        return super().__ne__(other)

    def copy(self):
        return copy.deepcopy(self)


class StellarisDataParser(object):
    def parse_text(self, mod, file, src, debug=False):
        src = self._pre_process_source(src)

        # Check if src is now just whitespace (comment only files)
        if src.isspace():
            print("No content found in: " + file)
            return None, None

        # Parse our data
        print("Parsing: " + file)
        data = self._parse_grammar(src, debug=debug)
        document = self._derive_document(mod, data)
        model = self._derive_model(data, mod)
        return document, model

    def _derive_model(self, source, fallback_source):
        document = SmoosherDataModel.Document(fallback_source, fallback_source)

        # TODO: Assign some basic, relevant document properties

        mode = self.__derive_model_content(document, source, document, fallback_source)
        return mode

    def __derive_model_content(self, root_document, source, parent, fallback_source):
        # Loop through our root statement
        for statement in source:
            if len(statement) == 1:
                assignment = self._derive_weird_assignment(root_document, statement, fallback_source)
                parent.add_assignment(assignment)

            elif isinstance(statement[2], pp.ParseResults):
                node = self._derive_node(root_document, statement, fallback_source)
                parent.add_node(node)
            else:
                assignment = self._derive_assignment(root_document, statement, fallback_source)
                parent.add_assignment(assignment)

        return parent

    def _derive_node(self, root_document, statement, fallback_source):
        if len(statement) != 4:
            source = fallback_source
        else:
            source = statement[3]

        node = SmoosherDataModel.Node(root_document, statement[0], source)

        # Check for empty nodes
        if len(statement[2]) == 1 and statement[2][0] == "":
            return node

        # Check for statement lists
        if isinstance(statement[2], pp.ParseResults):
            return self.__derive_model_content(statement[2], node, fallback_source)

        print("There is an error with the format of your parsed document.")
        exit(1)
        return None

    def _derive_assignment(self, root_document, statement, fallback_source):
        if len(statement) != 4:
            source = fallback_source
        else:
            source = statement[3]
        return SmoosherDataModel.Assignment(root_document, statement[0], statement[1], statement[2], source)

    def _derive_weird_assignment(self, root_document, statement, fallback_source):
        if len(statement) != 4:
            source = fallback_source
        else:
            source = statement[3]
        return SmoosherDataModel.StatementAssignment(root_document, statement[0], source)

    def _pre_process_source(self, src):
        # Remove tags & dependencies which fuck everything up because they are formatted weirdly
        src = re.sub(r"^dependencies={[^}]*}$", "", src, flags=re.MULTILINE)
        src = re.sub(r"^tags={[^}]*}$", "", src, flags=re.MULTILINE)
        src = re.sub(r"#((?!ORIGIN).)*$", "", src,
                     flags=re.MULTILINE)  # Remove comments - I wish i could think of a good way to keep them
        src = re.sub(r"([A-Za-z0-9_.\-]+){", r"\1={", src)  # Solve phrases without equal sign
        src = re.sub(r"\"([A-Za-z0-9_.\-]+)\"\s*=", r"\1=", src, 0, re.MULTILINE)  # Unquote keys in phrases
        src = re.sub(r"=\s*{", r"={", src, 0, re.MULTILINE)  # Fix spaces
        src = re.sub(r"^\s*{\s*\}", r"", src, 0, re.MULTILINE)  # Hack for random empty objects start of the line
        return src

    def _parse_grammar(self, src, debug=True):
        # Generate a string type that handles quoted and unquoted
        unquoted = pp.Word(pp.alphanums + pp.alphas8bit + "_-.:?@[]")
        unquoted.setName("unquoted_string")
        pp.dblQuotedString.setName("quoted_string")
        string_type = (pp.dblQuotedString | unquoted)
        string_type.setName("string")

        # Generate a value type that handles all data types
        real = pp.Regex(r"[+-]?\d+\.\d*").setParseAction(lambda x: float(x[0]))
        integer = pp.Regex(r"[+-]?\d+").setParseAction(lambda x: int(x[0]))
        yes = pp.CaselessKeyword("yes").setParseAction(pp.replaceWith(True))
        no = pp.CaselessKeyword("no").setParseAction(pp.replaceWith(False))
        value_type = (real | integer | yes | no | pp.dblQuotedString | unquoted)
        value_type.setName("value")

        # Handle our special cased assignments
        assignment = (string_type + "=" + value_type)
        assignment.setName("assignment")

        # Handle our queries
        query = (string_type + pp.oneOf([">", "<", ">=", "<="]) + value_type)
        query.setName("query")

        # Handle our empties
        empty = pp.Empty().setParseAction(pp.replaceWith(""))
        empty.setName("empty")

        origin = (pp.Suppress("#ORIGIN = ") + string_type)
        origin.setName("Origin")

        # Block is an encapsulation of something else
        block = pp.Forward()
        block << (
                string_type + "=" + pp.Suppress("{") +
                pp.Group(
                    pp.OneOrMore(
                        pp.Group(
                            # pp.OneOrMore(
                            #     pp.Group(
                            (block | assignment | query | value_type) + pp.Optional(origin)
                            #     )
                            # )
                        )
                    )
                    | empty)
                + pp.Suppress("}") + pp.Optional(origin))
        block.setName("block")

        # We can either have a direct assignment or a block
        expressions = (assignment | block)
        expressions.setName("expression")

        # Set the whole doc
        document = pp.OneOrMore(pp.Group(expressions + pp.Optional(origin)))
        document.parseWithTabs()
        document.setName("document")

        if debug:
            pp.dblQuotedString.setDebug()
            unquoted.setDebug()
            value_type.setDebug()
            assignment.setDebug()
            query.setDebug()
            empty.setDebug()
            origin.setDebug()
            block.setDebug()
            expressions.setDebug()
            document.setDebug()

        try:
            return document.parseString(src, parseAll=True)
        except pp.ParseException as pe:
            # Prints the last lines to cause the error, sometimes not very useful
            print(pp.ParseException.explain(pe, depth=None))
            print("Recording attempt")

            if not debug:
                pp.dblQuotedString.setDebug()
                unquoted.setDebug()
                value_type.setDebug()
                assignment.setDebug()
                query.setDebug()
                empty.setDebug()
                origin.setDebug()
                block.setDebug()
                expressions.setDebug()
                document.setDebug()
                document.parseString(src, parseAll=True)

            raise pe  # Should throw exception, not exit

    def _derive_document(self, mod, source):
        document = dict_list()  # Allows duplicate keys in root - ideally we wouldn't want this but hey ho not my file format
        for statement in source:
            # Check if the first statement is a key
            if isinstance(statement[0], str):
                statement_content = self._derive_statement(mod, statement)
            else:
                continue

            # Can do a check here to see if any keys from statement content are already present in document
            # if any(item in document for item in statement_content):
            #     print("Duplicate key in source document. This is a big error. Figure it out.")
            #     return None

            # Compound dict
            for key, item in statement_content.items():
                document[key] = item

        return document

    def _derive_statement(self, mod, statement):
        properties = dict_list()

        if isinstance(statement[2], pp.ParseResults):
            properties["type"] = statement[1] + "{"
            if len(statement) != 4:
                properties["source"] = mod
            else:
                properties["source"] = statement[3]
            if len(statement[2]) == 1 and statement[2][0] == '':
                properties["value"] = ""
            elif len(statement[2]) == 1 and isinstance(statement[2][0], str):
                properties["value"] = statement[2][0]
            else:
                for item in statement[2]:
                    if isinstance(item, pp.ParseResults) and len(item) == 1:
                        properties["value"] = item[0]
                    else:
                        properties["value"] = self._derive_statement(mod, item)
        else:
            if len(statement) != 4:
                properties["source"] = mod
            else:
                properties["source"] = statement[3]
            properties["type"] = statement[1]
            properties["value"] = statement[2]

        return {statement[0]: properties}

    def dump(self, file_tree, file, graph):
        print("Creating file: " + file)
        with open(file, "w") as file_handle:
            #self._write(file_tree, 0, real_file)
            graph.write(file_handle, 0)

    def _write(self, tree, tab_count, file_handle):
        for key, value in tree.items():
            for item in value:  # Further nesting allows for duplicate keys
                self._write_block(key, item["type"], item["value"], item["source"], tab_count, file_handle)

    def _write_tree(self, tree, tab_count, file_handle):
        for key, value in tree.items():
            self._write_block(key, value["type"], value["value"], value["source"], tab_count, file_handle)

    def _write_block(self, key, assignment_type, value, source, tab_count, file_handle):
        tabs = "    " * tab_count
        if isinstance(value, list) and assignment_type[0][-1] == "{":
            file_handle.write(tabs + key + " " + assignment_type[0][0] + " {\n")
            tab_count += 1
            for item in value:
                if isinstance(item, dict):
                    self._write_tree(item, tab_count,
                                     file_handle)  # Realistically we should only have 1 item in here so we could redirect straight to _write_block with some wiggling
                else:
                    file_handle.write(tabs + "    " + self.__correct_value(item) + "\n")
            tab_count -= 1
            file_handle.write(tabs + "} #ORIGIN = " + source[0].replace(" ", "_") + "\n")

        else:
            file_handle.write(
                tabs + key + " " + assignment_type[0] + " " + self.__correct_value(value) + " #ORIGIN = " + source[
                    0].replace(" ", "_") + "\n")

    def __correct_value(self, value):
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

    def conflict_to_text(self, key, conflict):
        master_text = self._write_to_text(key, conflict["master"], 0, "")
        conflict_text = self._write_to_text(key, conflict["conflicting"], 0, "")
        return master_text, conflict_text

    def _write_to_text(self, key, items, tab_count, target_text):
        for block in items:
            target_text = self._write_block_to_text(key, block["type"], block["value"], block["source"], tab_count,
                                                    target_text)

        return target_text

        # for conflict in conflict_items:
        #     for key, item in conflict.items(): # Further nesting allows for duplicate keys
        #         self._write_block_to_text(key, item["type"], item["value"], item["source"], tab_count, target_text)

    def _write_tree_to_text(self, tree, tab_count, target_text):
        for key, value in tree.items():
            target_text = self._write_block_to_text(key, value["type"], value["value"], value["source"], tab_count,
                                                    target_text)

        return target_text

    def _write_block_to_text(self, key, assignment_type, value, source, tab_count, target_text):
        tabs = "    " * tab_count
        if isinstance(value, list) and assignment_type[0][-1] == "{":
            target_text += tabs + key + " " + assignment_type[0][0] + " {\n"
            tab_count += 1
            for item in value:
                if isinstance(item, dict):
                    target_text = self._write_tree_to_text(item, tab_count,
                                                           target_text)  # Realistically we should only have 1 item in here so we could redirect straight to _write_block with some wiggling
                else:
                    target_text += tabs + "    " + self.__correct_value(item) + "\n"
            tab_count -= 1
            target_text += tabs + "} #ORIGIN = " + source[0].replace(" ", "_") + "\n"

        else:
            target_text += tabs + key + " " + assignment_type[0] + " " + self.__correct_value(value) + " #ORIGIN = " + \
                           source[0].replace(" ", "_") + "\n"

        return target_text
