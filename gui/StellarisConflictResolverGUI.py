import tkinter as tk


class StellarisConflictResolver(tk.Frame):
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

        self.master_text = tk.Text(self, bg="white")
        self.master_scroll = tk.Scrollbar(self, command=self.master_text.yview)
        self.conflict_text = tk.Text(self, bg="white")
        self.conflict_scroll = tk.Scrollbar(self, command=self.conflict_text.yview)
        self.custom_text = tk.Text(self, bg="white")
        self.custom_scroll = tk.Scrollbar(self, command=self.custom_text.yview)

        # Packing
        self.master_text.grid(column=1, row=1, sticky="nsew")
        self.master_scroll.grid(column=2, row=1, sticky="nsew")
        self.conflict_text.grid(column=3, row=1, sticky="nsew")
        self.conflict_scroll.grid(column=4, row=1, sticky="nsew")
        self.custom_text.grid(column=5, row=1, sticky="nsew")
        self.custom_scroll.grid(column=6, row=1, sticky="nsew")

        # Linking
        self.master_text["yscrollcommand"] = self.master_scroll.set
        self.conflict_text["yscrollcommand"] = self.conflict_scroll.set
        self.custom_text["yscrollcommand"] = self.custom_scroll.set

        # Buttons
        self.master_button = tk.Button(self, text="LEFT", command=self.left)
        self.master_button.grid(column=1, row=2)
        self.conflict_button = tk.Button(self, text="RIGHT", command=self.right)
        self.conflict_button.grid(column=3, row=2)
        self.custom_button = tk.Button(self, text="CUSTOM", command=self.custom)
        self.custom_button.grid(column=5, row=2)

        # Sizing
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(5, weight=1)

    def left(self):
        self.done_text = self.master_text.get(1.0, 'end-1c')
        self.result_source = self.left_source
        self.result_type = self.left_type
        self.on_exit()

    def right(self):
        self.done_text = self.conflict_text.get(1.0, 'end-1c')
        self.result_source = self.right_source
        self.result_type = self.right_type
        self.on_exit()

    def custom(self):
        self.done_text = self.custom_text.get(1.0, 'end-1c')
        self.result_source = "Conflict resolution between: " + self.left_source + " and " + self.right_source
        if self.left_type != self.right_type:
            print("We shouldn't be comparing different node types I believe")
            exit(1)
        self.result_type = self.left_type
        self.on_exit()

    def populate(self, master, master_type, master_source, conflict, conflict_type, conflict_source):
        self.master_text.insert(1.0, master)
        self.left_type = master_type
        self.left_source = master_source

        self.conflict_text.insert(1.0, conflict)
        self.right_type = conflict_type
        self.right_source = conflict_source

    def on_exit(self):
        self.geometry_values = self.root.geometry()
        self.fullscreen = self.root.state()
        self.root.destroy()


if __name__ == "__main__":
    # Display our conflict resolution gui
    root = tk.Tk()
    gui = StellarisConflictResolver(root, None, None)
    gui.pack(fill="both", expand=True)
    root.mainloop()