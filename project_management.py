import os
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import auth_manager

DB_PATH = os.path.join(os.getcwd(), "projects.db")
# Folder to store exported task files
EXPORT_DIR = os.path.join(os.getcwd(), "project_management_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            notes TEXT,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS group_members (
            group_id INTEGER,
            username TEXT,
            PRIMARY KEY(group_id, username)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            assigned_user TEXT,
            assigned_group_id INTEGER,
            status TEXT,
            priority TEXT,
            due_date TEXT,
        parent_task_id INTEGER,
        created_by TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(assigned_group_id) REFERENCES groups(id),
        FOREIGN KEY(parent_task_id) REFERENCES tasks(id)
    )
    ''')

    conn.commit()

    # Ensure parent_task_id column exists for older DBs (migration)
    cur.execute("PRAGMA table_info('tasks')")
    cols = [r[1] for r in cur.fetchall()]
    if 'parent_task_id' not in cols:
        try:
            cur.execute('ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER')
            conn.commit()
        except Exception:
            pass

    conn.close()


# Simple date-time picker dialog (no external dependencies)
import calendar

class DateTimeDialog(simpledialog.Dialog):
    def __init__(self, parent, prefill=None):
        self.prefill = prefill
        self.selected_date = None
        self.selected_hour = 0
        self.selected_min = 0
        super().__init__(parent, title="Select Date & Time")

    def body(self, master):
        self.year = datetime.datetime.now().year
        self.month = datetime.datetime.now().month
        # parse prefill if provided
        if self.prefill:
            try:
                # accept 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM' or ISO
                parts = self.prefill.split()
                y, m, d = [int(x) for x in parts[0].split("-")]
                self.year, self.month = y, m
                self.selected_date = d
                if len(parts) > 1:
                    tparts = parts[1].split(":" )
                    self.selected_hour = int(tparts[0])
                    self.selected_min = int(tparts[1]) if len(tparts)>1 else 0
            except Exception:
                pass

        top = ttk.Frame(master)
        top.pack(padx=8, pady=6)

        nav = ttk.Frame(top)
        nav.pack(fill="x")
        self.lbl_month = ttk.Label(nav, text="")
        btn_prev = ttk.Button(nav, text="◀", width=3, command=self.prev_month)
        btn_next = ttk.Button(nav, text="▶", width=3, command=self.next_month)
        btn_prev.pack(side="left")
        self.lbl_month.pack(side="left", padx=10)
        btn_next.pack(side="left")

        self.cal_frame = ttk.Frame(top)
        self.cal_frame.pack()

        # time selectors
        time_frame = ttk.Frame(master)
        time_frame.pack(padx=8, pady=(4, 8), fill="x")
        ttk.Label(time_frame, text="Hour:").pack(side="left")
        self.spin_hour = tk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.spin_hour.pack(side="left", padx=(4, 10))
        ttk.Label(time_frame, text="Min:").pack(side="left")
        self.spin_min = tk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.spin_min.pack(side="left", padx=(4, 10))

        self.build_calendar()
        return None

    def build_calendar(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()
        self.lbl_month.config(text=f"{calendar.month_name[self.month]} {self.year}")
        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        for c, d in enumerate(days):
            ttk.Label(self.cal_frame, text=d, width=4).grid(row=0, column=c)
        month_cal = calendar.monthcalendar(self.year, self.month)
        for r, week in enumerate(month_cal, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.cal_frame, text="", width=4).grid(row=r, column=c)
                else:
                    b = ttk.Button(self.cal_frame, text=str(day), width=4, command=lambda dd=day: self.select_day(dd))
                    b.grid(row=r, column=c, padx=1, pady=1)

    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.build_calendar()

    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.build_calendar()

    def select_day(self, day):
        self.selected_date = day
        # set spinboxes to previously chosen or defaults
        try:
            self.spin_hour.delete(0, 'end')
            self.spin_hour.insert(0, f"{int(self.selected_hour):02d}")
            self.spin_min.delete(0, 'end')
            self.spin_min.insert(0, f"{int(self.selected_min):02d}")
        except Exception:
            pass

    def validate(self):
        if not self.selected_date:
            messagebox.showwarning("Selection Required", "Please select a date.", parent=self)
            return False
        try:
            h = int(self.spin_hour.get())
            m = int(self.spin_min.get())
            self.selected_hour = h
            self.selected_min = m
            return True
        except Exception:
            messagebox.showwarning("Invalid Time", "Please enter a valid hour/minute.", parent=self)
            return False

    def apply(self):
        dt = datetime.datetime(self.year, self.month, self.selected_date, int(self.selected_hour), int(self.selected_min))
        # store ISO-like format
        self.result = dt.strftime("%Y-%m-%d %H:%M")


def pick_datetime(parent, initial=None):
    dlg = DateTimeDialog(parent, prefill=initial)
    return getattr(dlg, 'result', None)


class ProjectManagementView(ttk.Frame):
    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        initialize_db()
        self.create_widgets()
        self.refresh_all()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_clients = ttk.Frame(self.notebook, padding=10)
        self.tab_projects = ttk.Frame(self.notebook, padding=10)
        self.tab_groups = ttk.Frame(self.notebook, padding=10)
        self.tab_tasks = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_clients, text="Clients")
        self.notebook.add(self.tab_projects, text="Projects")
        self.notebook.add(self.tab_groups, text="Groups")
        self.notebook.add(self.tab_tasks, text="Tasks")

        # Clients tab
        self.clients_tree = ttk.Treeview(self.tab_clients, columns=("contact", "email", "phone"), show="headings")
        for col, label in [("contact", "Contact"), ("email", "Email"), ("phone", "Phone")]:
            self.clients_tree.heading(col, text=label)
        self.clients_tree.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(self.tab_clients)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="Add Client", command=self.add_client).pack(side="left")
        ttk.Button(btn_frame, text="Edit Client", command=self.edit_selected_client).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Delete Client", command=self.delete_selected_client).pack(side="left")

        # Projects tab
        self.projects_tree = ttk.Treeview(self.tab_projects, columns=("client", "status"), show="headings")
        self.projects_tree.heading("client", text="Client")
        self.projects_tree.heading("status", text="Status")
        self.projects_tree.pack(fill="both", expand=True)

        pbtn_frame = ttk.Frame(self.tab_projects)
        pbtn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(pbtn_frame, text="Add Project", command=self.add_project).pack(side="left")
        ttk.Button(pbtn_frame, text="Edit Project", command=self.edit_selected_project).pack(side="left", padx=6)
        ttk.Button(pbtn_frame, text="Delete Project", command=self.delete_selected_project).pack(side="left")

        # Groups tab
        self.groups_tree = ttk.Treeview(self.tab_groups, columns=("members",), show="headings")
        self.groups_tree.heading("members", text="Members")
        self.groups_tree.pack(fill="both", expand=True)

        gbtn_frame = ttk.Frame(self.tab_groups)
        gbtn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(gbtn_frame, text="Create Group", command=self.create_group).pack(side="left")
        ttk.Button(gbtn_frame, text="Edit Group", command=self.edit_selected_group).pack(side="left", padx=6)
        ttk.Button(gbtn_frame, text="Delete Group", command=self.delete_selected_group).pack(side="left")

        # Tasks tab
        self.tasks_tree = ttk.Treeview(self.tab_tasks, columns=("project", "assignee", "status", "due"))
        # Use hierarchical treeview: first column is the item text (title)
        self.tasks_tree.heading("#0", text="Title")
        self.tasks_tree.column("#0", width=300)
        for col, label in [("project", "Project"), ("assignee", "Assignee"), ("status", "Status"), ("due", "Due Date")]:
            self.tasks_tree.heading(col, text=label)
        self.tasks_tree.pack(fill="both", expand=True)

        tbtn_frame = ttk.Frame(self.tab_tasks)
        tbtn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(tbtn_frame, text="Add Task", command=self.add_task).pack(side="left")
        ttk.Button(tbtn_frame, text="Add Subtask", command=self.add_subtask).pack(side="left", padx=6)
        ttk.Button(tbtn_frame, text="Edit Task", command=self.edit_selected_task).pack(side="left", padx=6)
        ttk.Button(tbtn_frame, text="Delete Task", command=self.delete_selected_task).pack(side="left")
        ttk.Button(tbtn_frame, text="Export CSV", command=self.export_tasks_csv).pack(side="right")
        ttk.Button(tbtn_frame, text="Export Excel", command=self.export_tasks_excel).pack(side="right", padx=6)

    # --- Clients CRUD ---
    def refresh_clients(self):
        for r in self.clients_tree.get_children():
            self.clients_tree.delete(r)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, contact_person, email, phone FROM clients ORDER BY name")
        for row in cur.fetchall():
            self.clients_tree.insert("", "end", iid=row["id"], values=(row["contact_person"], row["email"], row["phone"]))
        conn.close()

    def add_client(self):
        dlg = ClientDialog(self.master)
        if dlg.result:
            name, contact, email, phone, address, notes = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO clients (name, contact_person, email, phone, address, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, contact, email, phone, address, notes, datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
            self.refresh_clients()

    def edit_selected_client(self):
        sel = self.clients_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a client to edit.", parent=self.master)
            return
        client_id = int(sel[0])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cur.fetchone()
        conn.close()
        dlg = ClientDialog(self.master, prefill=row)
        if dlg.result:
            name, contact, email, phone, address, notes = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE clients SET name=?, contact_person=?, email=?, phone=?, address=?, notes=? WHERE id=?", (name, contact, email, phone, address, notes, client_id))
            conn.commit()
            conn.close()
            self.refresh_clients()

    def delete_selected_client(self):
        sel = self.clients_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a client to delete.", parent=self.master)
            return
        client_id = int(sel[0])
        if not messagebox.askyesno("Confirm Delete", "Delete selected client?", parent=self.master):
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM clients WHERE id=?", (client_id,))
        conn.commit()
        conn.close()
        self.refresh_clients()

    # --- Projects CRUD ---
    def refresh_projects(self):
        for r in self.projects_tree.get_children():
            self.projects_tree.delete(r)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT p.id, p.name, p.status, c.name as client FROM projects p LEFT JOIN clients c ON p.client_id = c.id ORDER BY p.name")
        for row in cur.fetchall():
            self.projects_tree.insert("", "end", iid=row["id"], values=(row["client"] or "", row["status"] or ""))
        conn.close()

    def add_project(self):
        dlg = ProjectDialog(self.master)
        if dlg.result:
            client_id, name, description, start_date, end_date, status = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO projects (client_id, name, description, start_date, end_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (client_id, name, description, start_date, end_date, status, datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
            self.refresh_projects()

    def edit_selected_project(self):
        sel = self.projects_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a project to edit.", parent=self.master)
            return
        project_id = int(sel[0])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        conn.close()
        dlg = ProjectDialog(self.master, prefill=row)
        if dlg.result:
            client_id, name, description, start_date, end_date, status = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE projects SET client_id=?, name=?, description=?, start_date=?, end_date=?, status=? WHERE id=?", (client_id, name, description, start_date, end_date, status, project_id))
            conn.commit()
            conn.close()
            self.refresh_projects()

    def delete_selected_project(self):
        sel = self.projects_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a project to delete.", parent=self.master)
            return
        project_id = int(sel[0])
        if not messagebox.askyesno("Confirm Delete", "Delete selected project?", parent=self.master):
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()
        conn.close()
        self.refresh_projects()

    # --- Groups CRUD ---
    def refresh_groups(self):
        for r in self.groups_tree.get_children():
            self.groups_tree.delete(r)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM groups ORDER BY name")
        for row in cur.fetchall():
            # get members
            cur2 = conn.cursor()
            cur2.execute("SELECT username FROM group_members WHERE group_id=?", (row["id"],))
            members = ", ".join([m[0] for m in cur2.fetchall()])
            self.groups_tree.insert("", "end", iid=row["id"], values=(members,))
        conn.close()

    def create_group(self):
        dlg = GroupDialog(self.master)
        if dlg.result:
            name, description, members = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO groups (name, description, created_at) VALUES (?, ?, ?)", (name, description, datetime.datetime.now().isoformat()))
            group_id = cur.lastrowid
            for m in members:
                cur.execute("INSERT OR IGNORE INTO group_members (group_id, username) VALUES (?, ?)", (group_id, m))
            conn.commit()
            conn.close()
            self.refresh_groups()

    def edit_selected_group(self):
        sel = self.groups_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a group to edit.", parent=self.master)
            return
        group_id = int(sel[0])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
        group = cur.fetchone()
        cur.execute("SELECT username FROM group_members WHERE group_id=?", (group_id,))
        members = [r[0] for r in cur.fetchall()]
        conn.close()
        dlg = GroupDialog(self.master, prefill=(group, members))
        if dlg.result:
            name, description, members = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE groups SET name=?, description=? WHERE id=?", (name, description, group_id))
            cur.execute("DELETE FROM group_members WHERE group_id=?", (group_id,))
            for m in members:
                cur.execute("INSERT OR IGNORE INTO group_members (group_id, username) VALUES (?, ?)", (group_id, m))
            conn.commit()
            conn.close()
            self.refresh_groups()

    def delete_selected_group(self):
        sel = self.groups_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a group to delete.", parent=self.master)
            return
        group_id = int(sel[0])
        if not messagebox.askyesno("Confirm Delete", "Delete selected group?", parent=self.master):
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM groups WHERE id=?", (group_id,))
        cur.execute("DELETE FROM group_members WHERE group_id=?", (group_id,))
        conn.commit()
        conn.close()
        self.refresh_groups()

    # --- Tasks CRUD ---
    def refresh_tasks(self):
        # Build hierarchical tree from tasks using parent_task_id
        for r in self.tasks_tree.get_children():
            self.tasks_tree.delete(r)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT t.id, t.title, t.status, t.due_date, t.parent_task_id, p.name as project, t.assigned_user, g.name as group_name FROM tasks t LEFT JOIN projects p ON t.project_id=p.id LEFT JOIN groups g ON t.assigned_group_id=g.id ORDER BY t.id")
        rows = cur.fetchall()
        conn.close()
        # Build map id->row and children
        tasks = {r["id"]: dict(r) for r in rows}
        children = {}
        roots = []
        for tid, r in tasks.items():
            pid = r.get("parent_task_id")
            if pid:
                children.setdefault(pid, []).append(tid)
            else:
                roots.append(tid)
        # recursive insert
        def insert_task(tid, parent_tree_id=""):
            r = tasks[tid]
            assignee = r.get("assigned_user") or (r.get("group_name") or "")
            tree_id = str(tid)
            self.tasks_tree.insert(parent_tree_id, "end", iid=tree_id, text=r.get("title", ""), values=(r.get("project") or "", assignee, r.get("status") or "", r.get("due_date") or ""))
            for child_id in sorted(children.get(tid, [])):
                insert_task(child_id, tree_id)
        for root_id in sorted(roots):
            insert_task(root_id)


    def add_task(self):
        dlg = TaskDialog(self.master)
        if dlg.result:
            project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO tasks (project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date, self.user_data.get("username", "system"), datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
            self.refresh_tasks()

    def add_subtask(self):
        sel = self.tasks_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a parent task to add a subtask.", parent=self.master)
            return
        parent_id = int(sel[0])
        # prefill project from parent
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT project_id FROM tasks WHERE id=?", (parent_id,))
        row = cur.fetchone()
        conn.close()
        parent_project = row["project_id"] if row else None
        # Pass initial_project so the dialog pre-selects the same project as the parent
        dlg = TaskDialog(self.master, initial_project=parent_project)
        if dlg.result:
            project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO tasks (project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date, parent_task_id, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (project_id or parent_project, title, description, assigned_user, assigned_group_id, status, priority, due_date, parent_id, self.user_data.get("username", "system"), datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
            self.refresh_tasks()

    def edit_selected_task(self):
        sel = self.tasks_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a task to edit.", parent=self.master)
            return
        task_id = int(sel[0])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cur.fetchone()
        conn.close()
        dlg = TaskDialog(self.master, prefill=task)
        if dlg.result:
            project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE tasks SET project_id=?, title=?, description=?, assigned_user=?, assigned_group_id=?, status=?, priority=?, due_date=?, updated_at=? WHERE id=?", (project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date, datetime.datetime.now().isoformat(), task_id))
            conn.commit()
            conn.close()
            self.refresh_tasks()

    def delete_selected_task(self):
        sel = self.tasks_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Error", "Please select a task to delete.", parent=self.master)
            return
        task_id = int(sel[0])
        if not messagebox.askyesno("Confirm Delete", "Delete selected task and all its subtasks?", parent=self.master):
            return
        # delete recursively
        conn = get_conn()
        cur = conn.cursor()
        def delete_recursive(tid):
            cur.execute("SELECT id FROM tasks WHERE parent_task_id=?", (tid,))
            children = [r[0] for r in cur.fetchall()]
            for c in children:
                delete_recursive(c)
            cur.execute("DELETE FROM tasks WHERE id=?", (tid,))
        delete_recursive(task_id)
        conn.commit()
        conn.close()
        self.refresh_tasks()

    def refresh_all(self):
        self.refresh_clients()
        self.refresh_projects()
        self.refresh_groups()
        self.refresh_tasks()

    # --- Export/Import ---
    def _generate_uids(self, tasks_rows):
        # tasks_rows: list of dicts with id and parent_task_id
        tasks = {r['id']: dict(r) for r in tasks_rows}
        children = {}
        roots = []
        for tid, r in tasks.items():
            pid = r.get('parent_task_id')
            if pid:
                children.setdefault(pid, []).append(tid)
            else:
                roots.append(tid)
        # sort children lists for deterministic ids
        for k in children:
            children[k].sort()
        roots.sort()
        uid_map = {}
        def assign_uids(tid, parent_uid=None):
            if parent_uid is None:
                uid = str(tid)
            else:
                # sibling index among parent's children
                siblings = children.get(int(tasks[tid].get('parent_task_id') or 0), [])
                idx = siblings.index(tid) + 1
                uid = f"{parent_uid}-{idx}"
            uid_map[tid] = uid
            for c in children.get(tid, []):
                assign_uids(c, uid)
        for r in roots:
            assign_uids(r, None)
        return uid_map

    def export_tasks_csv(self):
        import csv
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT t.* , p.name as project_name, g.name as group_name FROM tasks t LEFT JOIN projects p ON t.project_id=p.id LEFT JOIN groups g ON t.assigned_group_id=g.id ORDER BY t.id")
        rows = [dict(r) for r in cur.fetchall()]
        uid_map = self._generate_uids(rows)
        out_path = os.path.join(EXPORT_DIR, f"tasks_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["TaskUID","TaskID","ParentTaskUID","Project","Title","Description","Assignee","AssignedGroup","Status","Priority","DueDate","CreatedBy","CreatedAt","UpdatedAt"])
            for r in rows:
                tid = r['id']
                uid = uid_map.get(tid, str(tid))
                pid = r.get('parent_task_id')
                parent_uid = uid_map.get(pid) if pid else ''
                writer.writerow([uid, tid, parent_uid, r.get('project_name') or '', r.get('title') or '', r.get('description') or '', r.get('assigned_user') or '', r.get('group_name') or '', r.get('status') or '', r.get('priority') or '', r.get('due_date') or '', r.get('created_by') or '', r.get('created_at') or '', r.get('updated_at') or ''])
        conn.close()
        messagebox.showinfo("Export Complete", f"Tasks exported to {out_path}", parent=self.master)

    def export_tasks_excel(self):
        # Create an HTML table and save with .xls extension so Excel can open it
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT t.* , p.name as project_name, g.name as group_name FROM tasks t LEFT JOIN projects p ON t.project_id=p.id LEFT JOIN groups g ON t.assigned_group_id=g.id ORDER BY t.id")
        rows = [dict(r) for r in cur.fetchall()]
        uid_map = self._generate_uids(rows)
        out_path = os.path.join(EXPORT_DIR, f"tasks_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xls")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('<html><head><meta charset="utf-8" /></head><body><table border="1">')
            f.write('<tr><th>TaskUID</th><th>TaskID</th><th>ParentTaskUID</th><th>Project</th><th>Title</th><th>Description</th><th>Assignee</th><th>AssignedGroup</th><th>Status</th><th>Priority</th><th>DueDate</th><th>CreatedBy</th><th>CreatedAt</th><th>UpdatedAt</th></tr>')
            for r in rows:
                tid = r['id']
                uid = uid_map.get(tid, str(tid))
                pid = r.get('parent_task_id')
                parent_uid = uid_map.get(pid) if pid else ''
                def esc(x):
                    return (x or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                f.write(f"<tr><td>{esc(uid)}</td><td>{tid}</td><td>{esc(parent_uid)}</td><td>{esc(r.get('project_name') or '')}</td><td>{esc(r.get('title') or '')}</td><td>{esc(r.get('description') or '')}</td><td>{esc(r.get('assigned_user') or '')}</td><td>{esc(r.get('group_name') or '')}</td><td>{esc(r.get('status') or '')}</td><td>{esc(r.get('priority') or '')}</td><td>{esc(r.get('due_date') or '')}</td><td>{esc(r.get('created_by') or '')}</td><td>{esc(r.get('created_at') or '')}</td><td>{esc(r.get('updated_at') or '')}</td></tr>")
            f.write('</table></body></html>')
        conn.close()
        messagebox.showinfo("Export Complete", f"Tasks exported to {out_path}", parent=self.master)


# --- Dialogs ---
class ClientDialog(simpledialog.Dialog):
    def __init__(self, parent, prefill=None):
        self.prefill = prefill
        super().__init__(parent, title="Client")

    def body(self, master):
        tk.Label(master, text="Name:").grid(row=0, column=0, sticky="w")
        self.e_name = tk.Entry(master, width=50)
        self.e_name.grid(row=0, column=1)

        tk.Label(master, text="Contact Person:").grid(row=1, column=0, sticky="w")
        self.e_contact = tk.Entry(master, width=50)
        self.e_contact.grid(row=1, column=1)

        tk.Label(master, text="Email:").grid(row=2, column=0, sticky="w")
        self.e_email = tk.Entry(master, width=50)
        self.e_email.grid(row=2, column=1)

        tk.Label(master, text="Phone:").grid(row=3, column=0, sticky="w")
        self.e_phone = tk.Entry(master, width=50)
        self.e_phone.grid(row=3, column=1)

        tk.Label(master, text="Address:").grid(row=4, column=0, sticky="w")
        self.e_address = tk.Entry(master, width=50)
        self.e_address.grid(row=4, column=1)

        tk.Label(master, text="Notes:").grid(row=5, column=0, sticky="w")
        self.e_notes = tk.Entry(master, width=50)
        self.e_notes.grid(row=5, column=1)

        if self.prefill:
            row = self.prefill
            self.e_name.insert(0, row["name"])
            self.e_contact.insert(0, row["contact_person"] or "")
            self.e_email.insert(0, row["email"] or "")
            self.e_phone.insert(0, row["phone"] or "")
            self.e_address.insert(0, row["address"] or "")
            self.e_notes.insert(0, row["notes"] or "")

        return self.e_name

    def apply(self):
        self.result = (
            self.e_name.get().strip(),
            self.e_contact.get().strip(),
            self.e_email.get().strip(),
            self.e_phone.get().strip(),
            self.e_address.get().strip(),
            self.e_notes.get().strip(),
        )


class ProjectDialog(simpledialog.Dialog):
    def __init__(self, parent, prefill=None):
        self.prefill = prefill
        super().__init__(parent, title="Project")

    def body(self, master):
        tk.Label(master, text="Client:").grid(row=0, column=0, sticky="w")
        self.clients = [(r["id"], r["name"]) for r in get_conn().cursor().execute("SELECT id, name FROM clients ORDER BY name").fetchall()]
        self.client_var = tk.StringVar()
        self.c_combo = ttk.Combobox(master, values=[c[1] for c in self.clients], state="readonly")
        self.c_combo.grid(row=0, column=1)

        tk.Label(master, text="Name:").grid(row=1, column=0, sticky="w")
        self.e_name = tk.Entry(master, width=50)
        self.e_name.grid(row=1, column=1)

        tk.Label(master, text="Description:").grid(row=2, column=0, sticky="w")
        self.e_desc = tk.Entry(master, width=50)
        self.e_desc.grid(row=2, column=1)

        tk.Label(master, text="Start Date:").grid(row=3, column=0, sticky="w")
        start_frame = ttk.Frame(master)
        start_frame.grid(row=3, column=1, sticky="w")
        self.e_start = tk.Entry(start_frame, width=38)
        self.e_start.pack(side="left")
        ttk.Button(start_frame, text="📅", width=3, command=lambda: self._pick_dt(self.e_start)).pack(side="left", padx=6)

        tk.Label(master, text="End Date:").grid(row=4, column=0, sticky="w")
        end_frame = ttk.Frame(master)
        end_frame.grid(row=4, column=1, sticky="w")
        self.e_end = tk.Entry(end_frame, width=38)
        self.e_end.pack(side="left")
        ttk.Button(end_frame, text="📅", width=3, command=lambda: self._pick_dt(self.e_end)).pack(side="left", padx=6)

        tk.Label(master, text="Status:").grid(row=5, column=0, sticky="w")
        self.e_status = ttk.Combobox(master, values=["Planned", "Active", "Completed", "On Hold"], state="readonly")
        self.e_status.grid(row=5, column=1)

        if self.prefill:
            row = self.prefill
            # prefill client selection
            cid = row["client_id"]
            for idx, c in enumerate(self.clients):
                if c[0] == cid:
                    self.c_combo.current(idx)
                    break
            self.e_name.insert(0, row["name"] or "")
            self.e_desc.insert(0, row["description"] or "")
            self.e_start.insert(0, row["start_date"] or "")
            self.e_end.insert(0, row["end_date"] or "")
            if row["status"]:
                try:
                    self.e_status.set(row["status"])
                except Exception:
                    pass

        return self.c_combo

    def apply(self):
        cid = None
        sel = self.c_combo.get()
        for c in self.clients:
            if c[1] == sel:
                cid = c[0]
                break
        self.result = (
            cid,
            self.e_name.get().strip(),
            self.e_desc.get().strip(),
            self.e_start.get().strip(),
            self.e_end.get().strip(),
            self.e_status.get().strip(),
        )

    def _pick_dt(self, entry_widget):
        # Open the date-time picker and set the entry if a value is chosen
        val = pick_datetime(self)
        if val:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, val)


class GroupDialog(simpledialog.Dialog):
    def __init__(self, parent, prefill=None):
        self.prefill = prefill
        super().__init__(parent, title="Group")

    def body(self, master):
        tk.Label(master, text="Name:").grid(row=0, column=0, sticky="w")
        self.e_name = tk.Entry(master, width=50)
        self.e_name.grid(row=0, column=1)

        tk.Label(master, text="Description:").grid(row=1, column=0, sticky="w")
        self.e_desc = tk.Entry(master, width=50)
        self.e_desc.grid(row=1, column=1)

        tk.Label(master, text="Members:").grid(row=2, column=0, sticky="nw")
        # load users from auth_manager
        self.users = [u["username"] for u in auth_manager.load_users()]
        self.user_vars = {}
        members_frame = tk.Frame(master)
        members_frame.grid(row=2, column=1, sticky="w")
        for i, u in enumerate(self.users):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(members_frame, text=u, variable=var)
            cb.grid(row=i // 3, column=i % 3, sticky="w", padx=3, pady=2)
            self.user_vars[u] = var

        if self.prefill:
            group_row, members = self.prefill
            self.e_name.insert(0, group_row["name"])
            self.e_desc.insert(0, group_row["description"] or "")
            for m in members:
                if m in self.user_vars:
                    self.user_vars[m].set(True)

        return self.e_name

    def apply(self):
        members = [u for u, v in self.user_vars.items() if v.get()]
        self.result = (self.e_name.get().strip(), self.e_desc.get().strip(), members)


class TaskDialog(simpledialog.Dialog):
    def __init__(self, parent, prefill=None, initial_project=None):
        """initial_project: optional project_id to pre-select in the project combobox for subtasks."""
        self.prefill = prefill
        self.initial_project = initial_project
        super().__init__(parent, title="Task")

    def body(self, master):
        tk.Label(master, text="Project:").grid(row=0, column=0, sticky="w")
        self.projects = [(r["id"], r["name"]) for r in get_conn().cursor().execute("SELECT id, name FROM projects ORDER BY name").fetchall()]
        self.p_combo = ttk.Combobox(master, values=[p[1] for p in self.projects], state="readonly")
        self.p_combo.grid(row=0, column=1)
        # If an initial project id was provided (e.g., when creating a subtask), pre-select it
        if getattr(self, 'initial_project', None):
            try:
                for idx, p in enumerate(self.projects):
                    if p[0] == self.initial_project:
                        self.p_combo.current(idx)
                        break
            except Exception:
                pass

        tk.Label(master, text="Title:").grid(row=1, column=0, sticky="w")
        self.e_title = tk.Entry(master, width=50)
        self.e_title.grid(row=1, column=1)

        tk.Label(master, text="Description:").grid(row=2, column=0, sticky="w")
        self.e_desc = tk.Entry(master, width=50)
        self.e_desc.grid(row=2, column=1)

        tk.Label(master, text="Assign to User (optional):").grid(row=3, column=0, sticky="w")
        self.users = [u["username"] for u in auth_manager.load_users()]
        self.u_combo = ttk.Combobox(master, values=["" ] + self.users, state="readonly")
        self.u_combo.grid(row=3, column=1)

        tk.Label(master, text="Assign to Group (optional):").grid(row=4, column=0, sticky="w")
        self.groups = [(r["id"], r["name"]) for r in get_conn().cursor().execute("SELECT id, name FROM groups ORDER BY name").fetchall()]
        self.g_combo = ttk.Combobox(master, values=["" ] + [g[1] for g in self.groups], state="readonly")
        self.g_combo.grid(row=4, column=1)

        tk.Label(master, text="Status:").grid(row=5, column=0, sticky="w")
        self.e_status = ttk.Combobox(master, values=["Open", "In Progress", "Done", "Blocked"], state="readonly")
        self.e_status.grid(row=5, column=1)

        tk.Label(master, text="Priority:").grid(row=6, column=0, sticky="w")
        self.e_prio = ttk.Combobox(master, values=["Low", "Medium", "High"], state="readonly")
        self.e_prio.grid(row=6, column=1)

        tk.Label(master, text="Due Date:").grid(row=7, column=0, sticky="w")
        due_frame = ttk.Frame(master)
        due_frame.grid(row=7, column=1, sticky="w")
        self.e_due = tk.Entry(due_frame, width=38)
        self.e_due.pack(side="left")
        ttk.Button(due_frame, text="📅", width=3, command=lambda: self._pick_dt(self.e_due)).pack(side="left", padx=6)

        if self.prefill:
            row = self.prefill
            # project selection
            pid = row["project_id"]
            for idx, p in enumerate(self.projects):
                if p[0] == pid:
                    self.p_combo.current(idx)
                    break
            self.e_title.insert(0, row["title"] or "")
            self.e_desc.insert(0, row["description"] or "")
            if row["assigned_user"]:
                try:
                    self.u_combo.set(row["assigned_user"])
                except Exception:
                    pass
            if row["assigned_group_id"]:
                for idx, g in enumerate(self.groups):
                    if g[0] == row["assigned_group_id"]:
                        self.g_combo.current(idx+1)
                        break
            if row["status"]:
                try:
                    self.e_status.set(row["status"])
                except Exception:
                    pass
            if row["priority"]:
                try:
                    self.e_prio.set(row["priority"])
                except Exception:
                    pass
            if row["due_date"]:
                self.e_due.insert(0, row["due_date"])

        return self.p_combo

    def apply(self):
        pid = None
        sel = self.p_combo.get()
        for p in self.projects:
            if p[1] == sel:
                pid = p[0]
                break
        assigned_user = self.u_combo.get() or None
        assigned_group_id = None
        gsel = self.g_combo.get()
        for g in self.groups:
            if g[1] == gsel:
                assigned_group_id = g[0]
                break
        self.result = (
            pid,
            self.e_title.get().strip(),
            self.e_desc.get().strip(),
            assigned_user,
            assigned_group_id,
            self.e_status.get().strip(),
            self.e_prio.get().strip(),
            self.e_due.get().strip(),
        )

    def _pick_dt(self, entry_widget):
        val = pick_datetime(self)
        if val:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, val)
