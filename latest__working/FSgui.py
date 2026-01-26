import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path

# Import your backend module here
# import your_backend_module as backend

class FSProjectGUI:
    def __init__(self, root,fs):
        self.fs = fs
        self.isCliActive = False
        self.item_cache = dict() # map tree id with dict

        self.root = root
        self.root.title("File System Project")
        self.root.geometry("1200x700")
        self.root.configure(bg='white')
        
        # Create menu bar
        self.create_menu_bar()
        
        # Main container
        main_container = tk.Frame(root, bg='white')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        self.create_toolbar(main_container)
        
        # Address bar
        self.create_address_bar(main_container)
        
        # Content area with sidebar and main view
        content_area = tk.Frame(main_container, bg='white')
        content_area.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Left sidebar (navigation pane)
        self.create_sidebar(content_area)
        
        # Splitter
        splitter = tk.Frame(content_area, bg='#d0d0d0', width=2)
        splitter.pack(side=tk.LEFT, fill=tk.Y)
        
        # Right pane (file list and preview)
        right_pane = tk.Frame(content_area, bg='white')
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # File/Folder list view
        self.create_list_view(right_pane)
        
        # Status bar
        self.create_status_bar(main_container)
        
        # Initialize with sample data
        self.load_sample_data()


    
    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_item)
        file_menu.add_command(label="Open", command=self.open_item)
        file_menu.add_command(label="Create", command=self.create_item)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", command=lambda: self.update_status("Cut"))
        edit_menu.add_command(label="Copy", command=lambda: self.update_status("Copy"))
        edit_menu.add_command(label="Paste", command=lambda: self.update_status("Paste"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Delete", command=self.delete_selected)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh", command=self.refresh_view)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Details", command=self.toggle_view)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Options", command=lambda: self.update_status("Options"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self, parent):
        toolbar = tk.Frame(parent, bg='#f0f0f0', height=40, relief=tk.RAISED, bd=1)
        toolbar.pack(fill=tk.X, padx=0, pady=0)
        toolbar.pack_propagate(False)
        
        # Navigation buttons
        btn_back = tk.Button(toolbar, text="←", font=('Segoe UI', 12), 
                            bg='#f0f0f0', relief=tk.FLAT, width=3,
                            command=self.go_back)
        btn_back.pack(side=tk.LEFT, padx=2, pady=4)
        
        btn_forward = tk.Button(toolbar, text="→", font=('Segoe UI', 12),
                               bg='#f0f0f0', relief=tk.FLAT, width=3,
                               command=self.go_forward)
        btn_forward.pack(side=tk.LEFT, padx=2, pady=4)
        
        btn_up = tk.Button(toolbar, text="↑", font=('Segoe UI', 12),
                          bg='#f0f0f0', relief=tk.FLAT, width=3,
                          command=self.go_up)
        btn_up.pack(side=tk.LEFT, padx=2, pady=4)
        
        # Separator
        tk.Frame(toolbar, bg='#d0d0d0', width=2).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=6)
        
        # Action buttons
        btn_new = tk.Button(toolbar, text="New Folder", font=('Segoe UI', 9),
                           bg='#f0f0f0', relief=tk.FLAT,
                           command=self.new_item)
        btn_new.pack(side=tk.LEFT, padx=2, pady=4)

        btn_create = tk.Button(toolbar, text="New file", font=('Segoe UI', 9),
                           bg='#f0f0f0', relief=tk.FLAT,
                           command=self.create_item)
        btn_create.pack(side=tk.LEFT, padx=2, pady=4)
        
        btn_delete = tk.Button(toolbar, text="Delete", font=('Segoe UI', 9),
                              bg='#f0f0f0', relief=tk.FLAT,
                              command=self.delete_selected)
        btn_delete.pack(side=tk.LEFT, padx=2, pady=4)
        
        btn_refresh = tk.Button(toolbar, text="Refresh", font=('Segoe UI', 9),
                               bg='#f0f0f0', relief=tk.FLAT,
                               command=self.refresh_view)
        btn_refresh.pack(side=tk.LEFT, padx=2, pady=4)
        
        # Search box (right side)
        search_frame = tk.Frame(toolbar, bg='#f0f0f0')
        search_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(search_frame, text="🔍", bg='#f0f0f0', font=('Segoe UI', 10)).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=('Segoe UI', 9), width=25, relief=tk.FLAT,
                               bg='white', bd=1)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<Return>', lambda e: self.search_items())
        # CLI button
        btn_cli = tk.Button(toolbar, text="CLI", font=('Segoe UI', 9),
                            bg='#f0f0f0', relief=tk.FLAT,
                            command=self.open_cli_window)
        btn_cli.pack(side=tk.RIGHT, padx=5, pady=4)

    def create_address_bar(self, parent):
        address_frame = tk.Frame(parent, bg='white', height=35)
        address_frame.pack(fill=tk.X, padx=10, pady=5)
        address_frame.pack_propagate(False)
        
        tk.Label(address_frame, text="Address:", bg='white',
                font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.address_var = tk.StringVar(value=self.fs.cwd.path)
        address_entry = tk.Entry(address_frame, textvariable=self.address_var,
                                font=('Segoe UI', 9), relief=tk.SUNKEN, bd=1)
        address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        address_entry.bind('<Return>', lambda e: self.navigate_to_address())
    
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg='#f7f7f7', width=200, relief=tk.FLAT)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Quick access header
        quick_header = tk.Label(sidebar, text="Quick Access", 
                               font=('Segoe UI', 9, 'bold'),
                               bg='#f7f7f7', fg='#333', anchor='w')
        quick_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Quick access items
        self.add_nav_item(sidebar, "🏠 Home", "home")
        self.add_nav_item(sidebar, "📂 Recent", "recent")
        self.add_nav_item(sidebar, "⭐ Favorites", "favorites")
        
        # Separator
        tk.Frame(sidebar, bg='#d0d0d0', height=1).pack(fill=tk.X, pady=10)
        
        # This PC header
        pc_header = tk.Label(sidebar, text="This PC",
                            font=('Segoe UI', 9, 'bold'),
                            bg='#f7f7f7', fg='#333', anchor='w')
        pc_header.pack(fill=tk.X, padx=10, pady=(5, 5))
        
        # PC items
        self.add_nav_item(sidebar, "💾 Database", "database")
        self.add_nav_item(sidebar, "📊 Reports", "reports")
        self.add_nav_item(sidebar, "⚙️ Settings", "settings")
        
        # Separator
        tk.Frame(sidebar, bg='#d0d0d0', height=1).pack(fill=tk.X, pady=10)
        
        # Network header
        net_header = tk.Label(sidebar, text="Network",
                             font=('Segoe UI', 9, 'bold'),
                             bg='#f7f7f7', fg='#333', anchor='w')
        net_header.pack(fill=tk.X, padx=10, pady=(5, 5))
        
        self.add_nav_item(sidebar, "🌐 Server", "server")
    
    def add_nav_item(self, parent, text, item_id):
        btn = tk.Button(parent, text=text, font=('Segoe UI', 9),
                       bg='#f7f7f7', fg='#333', relief=tk.FLAT,
                       anchor='w', padx=10, pady=5,
                       cursor='hand2',
                       command=lambda: self.navigate_sidebar(item_id))
        btn.pack(fill=tk.X, padx=5, pady=1)
        
        # Hover effect
        btn.bind('<Enter>', lambda e: btn.configure(bg='#e5e5e5'))
        btn.bind('<Leave>', lambda e: btn.configure(bg='#f7f7f7'))
    
    def create_list_view(self, parent):
        # Column headers frame
        headers_frame = tk.Frame(parent, bg='#f0f0f0', height=25)
        headers_frame.pack(fill=tk.X, padx=0, pady=0)
        headers_frame.pack_propagate(False)
        
        tk.Label(headers_frame, text="Name", bg='#f0f0f0', 
                font=('Segoe UI', 9, 'bold'), anchor='w').pack(side=tk.LEFT, padx=10)
        tk.Label(headers_frame, text="Date Modified", bg='#f0f0f0',
                font=('Segoe UI', 9, 'bold'), anchor='w').pack(side=tk.LEFT, padx=80)
        tk.Label(headers_frame, text="Type", bg='#f0f0f0',
                font=('Segoe UI', 9, 'bold'), anchor='w').pack(side=tk.LEFT, padx=80)
        tk.Label(headers_frame, text="Size", bg='#f0f0f0',
                font=('Segoe UI', 9, 'bold'), anchor='w').pack(side=tk.LEFT, padx=80)
        
        # Treeview for file list
        tree_frame = tk.Frame(parent, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Scrollbars
        vsb = tk.Scrollbar(tree_frame, orient="vertical")
        hsb = tk.Scrollbar(tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(tree_frame, 
                                columns=('Date', 'Type', 'Size'),
                                show='tree headings',
                                yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading('#0', text='Name', anchor='w')
        self.tree.heading('Date', text='Date Modified', anchor='w')
        self.tree.heading('Type', text='Type', anchor='w')
        self.tree.heading('Size', text='Size', anchor='w')
        
        self.tree.column('#0', width=300, minwidth=200)
        self.tree.column('Date', width=180, minwidth=100)
        self.tree.column('Type', width=150, minwidth=100)
        self.tree.column('Size', width=100, minwidth=80)
        
        # Pack scrollbars and tree
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind double-click
        self.tree.bind('<Double-1>', self.on_item_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)
    
    def create_status_bar(self, parent):
        status_frame = tk.Frame(parent, bg='#f0f0f0', height=25, relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Ready", 
                                     bg='#f0f0f0', font=('Segoe UI', 8),
                                     anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.item_count_label = tk.Label(status_frame, text="0 items",
                                        bg='#f0f0f0', font=('Segoe UI', 8))
        self.item_count_label.pack(side=tk.RIGHT, padx=10)
    
    def load_sample_data(self):
        # Clear existing items
        self.address_var.set(self.fs.cwd.path)
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        items = self.fs.show_list()
        for item in items:
        #item =  {
        #   0  'name': self.name,
        #   1  'path': self.path,
        #   2  'type': self.type,
        #   3  'size': self.size,
        #   4  'modified_time': self.modified_time,
        #   5  'created_time': self.created_time,
        #   6  'mode': self.mode
        # }
            tree_id = self.tree.insert('', tk.END, text=item['name'], 
                           values=(item['modified_time'],item['type'],item['size']))
                        #    values=(item['path'],item['modified_time'], item['type'], item['size']))
            self.item_cache[tree_id] = item
            
        
        self.item_count_label.config(text=f"{len(items)} items")
        self.update_status("Ready")
    
    def on_item_double_click(self, event):
        self.open_item()
         
    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Open", command=self.open_item)
        menu.add_separator()
        menu.add_command(label="Cut", command=lambda: self.update_status("Cut"))
        menu.add_command(label="Copy", command=lambda: self.update_status("Copy"))
        menu.add_command(label="Paste", command=lambda: self.update_status("Paste"))
        menu.add_separator()
        menu.add_command(label="Delete", command=self.delete_selected)
        menu.add_command(label="Rename", command=self.rename_item)
        menu.add_separator()
        menu.add_command(label="Info", command=self.show_info_panel)
        menu.add_command(label="Properties", command=self.show_properties)
        
        menu.post(event.x_root, event.y_root)
    
    def update_status(self, message):
        self.status_label.config(text=message)
    
    def navigate_sidebar(self, item_id):
        self.update_status(f"Navigating to: {item_id}")
        self.address_var.set(f"Home > {item_id.title()}")
        # backend.navigate_to(item_id)
        self.refresh_view()
    
    def go_back(self):
        self.fs.go_back()
        self.refresh_view()
        self.update_status("Go back")
        # backend.navigate_back()
    
    def go_forward(self):
        self.fs.go_forward()
        self.refresh_view()
        self.update_status("Go forward")
        # backend.navigate_forward()
    
    def go_up(self):
        self.fs.go_to_root()
        self.refresh_view()
        self.update_status("Go up one level")
        # backend.navigate_up()
    
    def new_item(self):
        name = tk.simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            item = self.fs.create_dir(name)
            # backend.create_folder(name)
            self.tree.insert('', 0, text=item['name'], 
                           values=list(item.values()))
            self.update_status(f"Created: {name}")
    
    def open_item(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            name = item['text']
            self.fs.go_to(name)
            self.refresh_view()
            self.update_status(f"Opening folder: {item['values'][2]}")
    
    def create_item(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Create File")
        dialog.geometry("350x220")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # -------- Frame --------
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # -------- Variables --------
        name_var = tk.StringVar()
        ext_var = tk.StringVar()
        content_var = tk.StringVar()

        # -------- Widgets --------
        ttk.Label(frame, text="Filename:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=name_var).grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Extension(optional):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=ext_var).grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Content:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=content_var).grid(row=2, column=1, sticky="ew", pady=5)
        def submit():
            name = name_var.get()
            ext = ext_var.get()
            content = content_var.get()
            if ext == '':
                ext = 'txt'

            if name:
                item = self.fs.create_file(f'{name}.{ext}',content)
                # backend.create_folder(name)
                self.tree.insert('', 0, text=item['name'], 
                               values=list(item.values()))
                self.update_status(f"Created: {name}")
            

            print(name, ext=='', content)
            dialog.destroy()

        ttk.Button(frame, text="Create", command=submit).grid(row=3, column=0, pady=15)
        ttk.Button(frame, text="Cancel", command=dialog.destroy).grid(row=3, column=1, pady=15)

        dialog.wait_window()

        frame.columnconfigure(1, weight=1)
    
    def delete_selected(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            confirm = messagebox.askyesno("Delete", 
                                             f"Delete {item['text']}?")
            if confirm:
                for select in selected:
                    item_ = self.tree.item(select)
                    self.tree.delete(select)
                    isDel = self.fs.delete(item_['text'])
                    if isDel:
                        self.update_status(f"Deleted: {item_['text']}")
                    else:
                        messagebox.showwarning("delete", "Please select an item to delete")

                # backend.delete_item(item['text'])
    
    def refresh_view(self):
        self.update_status("Refreshing...")
        self.load_sample_data()
    
    def toggle_view(self):
        self.update_status("View toggled")
    
    def search_items(self):
        query = self.search_var.get()
        self.update_status(f"Searching for: {query}")
        # results = backend.search(query)
    
    def navigate_to_address(self):
        path = self.address_var.get()
        print(path)
        i,m = self.fs.go_to_address(path)
        if i:
            pass
        else:
            messagebox.showwarning("not found",m)
        self.refresh_view()
        self.update_status(f"Navigating to: {path}")

        # backend.navigate_to_path(path)
    
    def show_properties(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            messagebox.showinfo("Properties", 
                              f"Name: {item['text']}\n"
                              f"Type: {item['values'][1]}\n"
                              f"Size: {item['values'][2]}\n"
                              f"Modified: {item['values'][0]}")
    
    def show_about(self):
        messagebox.showinfo("About", "FS Project Explorer\nVersion 1.0")
    
    def rename_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Rename", "Please select an item to rename")
            return
        
        item = self.tree.item(selected[0])
        old_name = item['text']
        
        # Create rename dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Rename")
        dialog.geometry("400x150")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (75)
        dialog.geometry(f'400x150+{x}+{y}')
        
        # Content frame
        content = tk.Frame(dialog, bg='white')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Label
        tk.Label(content, text=f"Enter a new name for '{old_name}':", 
                bg='white', font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 10))
        
        # Entry field
        name_var = tk.StringVar(value=old_name)
        entry = tk.Entry(content, textvariable=name_var, 
                        font=('Segoe UI', 10), relief=tk.SOLID, bd=1)
        entry.pack(fill=tk.X, ipady=5)
        entry.focus_set()
        entry.select_range(0, tk.END)
        
        # Button frame
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(pady=(20, 0))
        
        def do_rename():
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Name", "Name cannot be empty")
                return
            
            if new_name == old_name:
                dialog.destroy()
                return
            
            isRenamed = self.fs.rename(old_name,new_name)
            if isRenamed:
                self.tree.item(selected[0], text=new_name)
                self.update_status(f"Renamed '{old_name}' to '{new_name}'")
            else:
                messagebox.showwarning("rename","name already exist")
            dialog.destroy()
        
        def cancel_rename():
            dialog.destroy()
        
        # Buttons
        btn_ok = tk.Button(btn_frame, text="OK", command=do_rename,
                          bg='#0078d4', fg='white', font=('Segoe UI', 9),
                          relief=tk.FLAT, padx=20, pady=5, cursor='hand2')
        btn_ok.pack(side=tk.LEFT, padx=5)
        
        btn_cancel = tk.Button(btn_frame, text="Cancel", command=cancel_rename,
                              bg='#e1e1e1', fg='black', font=('Segoe UI', 9),
                              relief=tk.FLAT, padx=20, pady=5, cursor='hand2')
        btn_cancel.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter and Escape keys
        entry.bind('<Return>', lambda e: do_rename())
        dialog.bind('<Escape>', lambda e: cancel_rename())
    
    def show_info_panel(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Info", "Please select an item to view info")
            return
        
        # item =  {
        #   0  'name': self.name,
        #   1  'path': self.path,
        #   2  'type': self.type,
        #   3  'size': self.size,
        #   4  'modified_time': self.modified_time,
        #   5  'created_time': self.created_time,
        #   6  'mode': self.mode
        # }
        item = self.item_cache[selected[0]]
        item_name = item['name']
        item_path = item['path']
        item_type = item['type']
        item_size = item['size']
        item_modified_time = item['modified_time']
        item_created_time = item['created_time']
        item_mode = item['mode']

        
        # Create info side panel window
        info_window = tk.Toplevel(self.root)
        info_window.title("Info")
        info_window.geometry("350x600")
        info_window.configure(bg='#f5f5f5')
        info_window.resizable(True, True)
        
        # Position on right side of main window
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        info_window.geometry(f"350x600+{main_x + main_width + 10}+{main_y}")
        
        # Header with icon and name
        header_frame = tk.Frame(info_window, bg='white', height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Large icon
        icon_label = tk.Label(header_frame, text="📄", font=('Segoe UI', 48),
                             bg='white')
        icon_label.pack(pady=(20, 5))
        
        # Item name
        name_label = tk.Label(header_frame, text=item_name, 
                             font=('Segoe UI', 11, 'bold'),
                             bg='white', fg='#333')
        name_label.pack()
        
        # Separator
        tk.Frame(info_window, bg='#e0e0e0', height=1).pack(fill=tk.X)
        
        # Info content with scrollbar
        info_frame = tk.Frame(info_window, bg='#f5f5f5')
        info_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        canvas = tk.Canvas(info_frame, bg='#f5f5f5', highlightthickness=0)
        scrollbar = tk.Scrollbar(info_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f5')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Info sections
        self.add_info_section(scrollable_frame, "General Information")
        self.add_info_row(scrollable_frame, "Type:", item_type)
        self.add_info_row(scrollable_frame, "Size:", item_size if item_size else "N/A")
        self.add_info_row(scrollable_frame, "Location:", item_path)
        
        tk.Frame(scrollable_frame, bg='#e0e0e0', height=1).pack(fill=tk.X, pady=15, padx=20)
        
        self.add_info_section(scrollable_frame, "Dates")
        self.add_info_row(scrollable_frame, "Modified:", item_modified_time)
        self.add_info_row(scrollable_frame, "Created:", item_created_time)
        self.add_info_row(scrollable_frame, "mode:", item_mode)
        
        tk.Frame(scrollable_frame, bg='#e0e0e0', height=1).pack(fill=tk.X, pady=15, padx=20)
        
        self.add_info_section(scrollable_frame, "Details")
        self.add_info_row(scrollable_frame, "Owner:", "Administrator")
        self.add_info_row(scrollable_frame, "Permissions:", "Read, Write")
        
        # Get additional info from backend
        # backend_info = backend.get_item_info(item_name)
        # self.add_info_row(scrollable_frame, "Status:", backend_info.get('status'))
        
        tk.Frame(scrollable_frame, bg='#e0e0e0', height=1).pack(fill=tk.X, pady=15, padx=20)
        
        self.add_info_section(scrollable_frame, "Statistics")
        self.add_info_row(scrollable_frame, "Version:", "1.0")
        self.add_info_row(scrollable_frame, "Checksum:", "a3f5c8e9...")
        
        # Action buttons at bottom
        action_frame = tk.Frame(info_window, bg='white', height=60)
        action_frame.pack(fill=tk.X, side=tk.BOTTOM)
        action_frame.pack_propagate(False)
        
        tk.Frame(info_window, bg='#e0e0e0', height=1).pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_open = tk.Button(action_frame, text="Open", 
                            font=('Segoe UI', 9),
                            bg='#0078d4', fg='white', relief=tk.FLAT,
                            padx=15, pady=8, cursor='hand2',
                            command=lambda: self.update_status(f"Opening {item_name}"))
        btn_open.pack(side=tk.LEFT, padx=20, pady=15)
        
        btn_edit = tk.Button(action_frame, text="Edit",
                            font=('Segoe UI', 9),
                            bg='#e1e1e1', fg='black', relief=tk.FLAT,
                            padx=15, pady=8, cursor='hand2',
                            command=self.rename_item)
        btn_edit.pack(side=tk.LEFT, padx=5, pady=15)
        
        btn_close = tk.Button(action_frame, text="Close",
                             font=('Segoe UI', 9),
                             bg='#e1e1e1', fg='black', relief=tk.FLAT,
                             padx=15, pady=8, cursor='hand2',
                             command=info_window.destroy)
        btn_close.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def add_info_section(self, parent, title):
        section = tk.Label(parent, text=title, 
                          font=('Segoe UI', 10, 'bold'),
                          bg='#f5f5f5', fg='#333', anchor='w')
        section.pack(fill=tk.X, padx=20, pady=(10, 5))
    
    def add_info_row(self, parent, label, value):
        row_frame = tk.Frame(parent, bg='#f5f5f5')
        row_frame.pack(fill=tk.X, padx=20, pady=3)
        
        lbl = tk.Label(row_frame, text=label, 
                      font=('Segoe UI', 9),
                      bg='#f5f5f5', fg='#666', anchor='w', width=15)
        lbl.pack(side=tk.LEFT)
        
        val = tk.Label(row_frame, text=value,
                      font=('Segoe UI', 9),
                      bg='#f5f5f5', fg='#333', anchor='w')
        val.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def open_cli_window(self):
        def on_cli_close(event=None):
            print("CLI window closed")
            self.cli_window.destroy()
            self.cli_window = None
            self.isCliActive = False

        if not self.isCliActive:
            self.isCliActive = True
            self.cli_window = tk.Toplevel(self.root)
            self.cli_window.title("FS CLI")
            self.cli_window.geometry("600x400")
            self.cli_window.configure(bg='black')
            self.cli_window.resizable(True, True)
            self.cli_window.protocol("WM_DELETE_WINDOW", on_cli_close)
            


            # Text widget for output
            output_text = tk.Text(self.cli_window, bg='black', fg='white', insertbackground='white',
                                  font=('Consolas', 10))
            output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5,0))

            # Entry widget for command input
            cmd_var = tk.StringVar()
            cmd_entry = tk.Entry(self.cli_window, textvariable=cmd_var, bg='black', fg='white',
                                 insertbackground='white', font=('Consolas', 10))
            cmd_entry.pack(fill=tk.X, padx=5, pady=5)
            cmd_entry.focus_set()

            # Simple command handler
            def run_command(event=None):
                cmd = cmd_var.get().strip()
                if not cmd:
                    return
                output_text.insert(tk.END, f"> {cmd}\n")

                # Handle some example commands
                if cmd.lower() == "help":
                    output_text.insert(tk.END, "Available commands: help, list, clear\n")
                elif cmd.lower() == "list":
                    # Here you can list items from your tree
                    items = [self.tree.item(i)['text'] for i in self.tree.get_children()]
                    for i in items:
                        output_text.insert(tk.END, f"{i}\n")
                elif cmd.lower() == "clear":
                    output_text.delete(1.0, tk.END)
                else:
                    output_text.insert(tk.END, f"Unknown command: {cmd}\n")

                output_text.see(tk.END)
                cmd_var.set("")

            cmd_entry.bind('<Return>', run_command)
        else:
            messagebox.showwarning("CLI", "CLI already active")


# For dialogs
import tkinter.simpledialog

if __name__ == "__main__":
    root = tk.Tk()
    app = FSProjectGUI(root,[])
    root.mainloop()