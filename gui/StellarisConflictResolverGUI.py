import tkinter as tk

from model import SmoosherDataModel, SmoosherComparator


class StellarislatestResolver(tk.Frame):
    default_text = "This is the file builder wizard. The wizard will iterate through each difference detected between" \
                   " the two files as highlighted using the blue colour. Manual changes can be made by editing the " \
                   "document below."

    def __init__(self, root, geometry, state):
        super().__init__(root)
        self.root = root
        self.done_text = ""
        self.geometry_values = geometry
        self.fullscreen = state
        self.left_type = ""
        self.left_source = ""
        self.right_type = ""
        self.right_source = ""
        self.result_type = ""
        self.result_source = ""

        # Remember geometry
        if geometry is not None:
            self.root.geometry(geometry)

        if state is not None:
            self.root.state(state)

        # Main frame components
        self.header = tk.Frame(self)
        self.header.grid(row=1, column=1, sticky="nsew")
        self.main = tk.Frame(self)
        self.main.grid(row=2, column=1, sticky="nsew")
        self.footer = tk.Frame(self)
        self.footer.grid(row=3, column=1, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # Header components

        # Main components
        self.original_text = tk.Text(self.main, bg="white")
        self.original_text.grid(row=1, column=1, sticky="nsew")
        self.original_scroll = tk.Scrollbar(self.main, command=self.original_text.yview)
        self.original_scroll.grid(row=1, column=2, sticky="nsew")
        self.latest_text = tk.Text(self.main, bg="white")
        self.latest_text.grid(row=1, column=3, sticky="nsew")
        self.latest_scroll = tk.Scrollbar(self.main, command=self.latest_text.yview)
        self.latest_scroll.grid(row=1, column=4, sticky="nsew")
        self.custom_frame = tk.Frame(self.main, bg="white")
        self.custom_frame.grid(row=1, column=5, sticky="nsew")
        self.main.columnconfigure(1, weight=1)
        self.main.columnconfigure(3, weight=1)
        self.main.columnconfigure(5, weight=1)
        self.main.rowconfigure(1, weight=1)

        # Custom frame components
        self.info_frame = tk.Frame(self.custom_frame)
        self.info_frame.grid(row=1, column=1, sticky="nsew")
        self.custom_text_frame = tk.Frame(self.custom_frame, bg="white")
        self.custom_text_frame.grid(row=2, column=1, sticky="nsew")
        self.custom_frame.columnconfigure(1, weight=1)
        self.custom_frame.rowconfigure(2, weight=1)

        # Info frame
        self.info_label = tk.Message(self.info_frame, text="", bg="white")
        self.info_label.grid(row=1, column=1, sticky="nsew")
        self.choose_left = tk.Button(self.info_frame, text="Use Original", command=self.select_original)
        self.choose_left.grid(row=1, column=2)
        self.choose_right = tk.Button(self.info_frame, text="Use Latest", command=self.select_latest)
        self.choose_right.grid(row=1, column=3)
        self.info_frame.columnconfigure(1, weight=1)

        # Custom Text Display
        self.custom_text = tk.Text(self.custom_text_frame, bg="white")
        self.custom_text.grid(row=1, column=1, sticky="nsew")
        self.custom_scroll = tk.Scrollbar(self.custom_text_frame, command=self.custom_text.yview)
        self.custom_scroll.grid(row=1, column=2, sticky="nsew")
        self.custom_text_frame.columnconfigure(1, weight=1)
        self.custom_text_frame.rowconfigure(1, weight=1)

        # Footer components
        self.footer_label = tk.Message(self.footer, text="", bg="white")
        self.footer_label.grid(row=1, column=1, sticky="nsew")
        self.original_button = tk.Button(self.footer, text="Choose Original", command=self.left)
        self.original_button.grid(row=1, column=2)
        self.latest_button = tk.Button(self.footer, text="Choose Latest", command=self.right)
        self.latest_button.grid(row=1, column=3)
        self.custom_button = tk.Button(self.footer, text="Choose Custom", command=self.custom)
        self.custom_button.grid(row=1, column=4)
        self.footer.columnconfigure(1, weight=1)

        # Linking
        self.original_text["yscrollcommand"] = self.original_scroll.set
        self.latest_text["yscrollcommand"] = self.latest_scroll.set
        self.custom_text["yscrollcommand"] = self.custom_scroll.set

        # Do you like TAAAGS
        self.original_text.tag_configure("add", background="green")
        self.original_text.tag_configure("del", background="red")
        self.original_text.tag_configure("edit", background="yellow")
        self.original_text.tag_configure("highlight", background="blue")
        self.latest_text.tag_configure("add", background="green")
        self.latest_text.tag_configure("del", background="red")
        self.latest_text.tag_configure("edit", background="yellow")
        self.latest_text.tag_configure("highlight", background="blue")

    def left(self):
        self.done_text = self.original_text.get(1.0, 'end-1c')
        self.result_source = self.left_source
        self.result_type = self.left_type
        self.on_exit()

    def right(self):
        self.done_text = self.latest_text.get(1.0, 'end-1c')
        self.result_source = self.right_source
        self.result_type = self.right_type
        self.on_exit()

    def custom(self):
        self.done_text = self.custom_text.get(1.0, 'end-1c')
        self.result_source = "latest resolution between: " + self.left_source + " and " + self.right_source
        if self.left_type != self.right_type:
            print("We shouldn't be comparing different node types I believe")
            exit(1)
        self.result_type = self.left_type
        self.on_exit()

    def select_original(self):
        pass

    def select_latest(self):
        pass

    def populate(self, original, original_type, original_source, latest, latest_type, latest_source):
        self.original_text.insert(1.0, original)
        self.left_type = original_type
        self.left_source = original_source

        self.latest_text.insert(1.0, latest)
        self.right_type = latest_type
        self.right_source = latest_source

    def populate(self, difference):
        # TODO: Somehow it would be good to store the diffs by line so we can move to them

        self._populate_from_node(difference.original, self.original_text, difference.original_changes, 0)
        self._populate_from_node(difference.latest, self.latest_text, difference.latest_changes, 0)

    def _populate_from_node(self, node, destination, difference, tabs):
        # Do the original first
        for metadata_holder in node:
            # This will store the start point of any text we add from now on
            marking_diff = False
            start_pos = -1  # Just to fix linter
            if metadata_holder.unique_id in difference:
                start_pos = destination.index("end")
                marking_diff = True

            # In this situation we can just write our content
            if isinstance(metadata_holder, SmoosherDataModel.Leaf):
                destination.instert("end", metadata_holder.write_to_text(tabs))

            else:
                destination.insert("end", metadata_holder.write_header_to_text(tabs) + "\n")
                nested_tabs = tabs + 1
                self._populate_from_node(metadata_holder, destination, difference, nested_tabs)
                destination.insert("end", metadata_holder.write_footer_to_text(tabs))

            # Now we need to back highlight
            if marking_diff:
                end_pos = difference.index("end")

                # If so use cursors to assign a highlight
                diff = difference[metadata_holder.unique_id]
                if isinstance(diff, SmoosherComparator.Addition):
                    destination.tag_add("add", start_pos, end_pos)

                elif isinstance(diff, SmoosherComparator.Deletion):
                    destination.tag_add("del", start_pos, end_pos)

                elif isinstance(diff, SmoosherComparator.Change):
                    destination.tag_add("edit", start_pos, end_pos)

    def on_exit(self):
        self.geometry_values = self.root.geometry()
        self.fullscreen = self.root.state()
        self.root.destroy()


if __name__ == "__main__":
    # Display our latest resolution gui
    root = tk.Tk()
    gui = StellarislatestResolver(root, None, None)
    gui.pack(fill="both", expand=True)
    root.mainloop()
