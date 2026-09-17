import os
import datetime
import sqlite3
import project_management

print('Initializing DB...')
project_management.initialize_db()
conn = project_management.get_conn()
cur = conn.cursor()
# Insert client
cur.execute("INSERT OR IGNORE INTO clients (name, contact_person, email, phone, address, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (
    'Test Client', 'Alice', 'alice@example.com', '1234567890', '123 Test St', 'Notes', datetime.datetime.now().isoformat()
))
conn.commit()
cur.execute("SELECT id FROM clients WHERE name=?", ('Test Client',))
client_id = cur.fetchone()[0]
print('Client id:', client_id)
# Insert project
cur.execute("INSERT INTO projects (client_id, name, description, start_date, end_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (
    client_id, 'BMS Project', 'Building Management System', '2026-08-27 09:00', '2026-12-31 17:00', 'Active', datetime.datetime.now().isoformat()
))
conn.commit()
cur.execute("SELECT id FROM projects WHERE name=?", ('BMS Project',))
project_id = cur.fetchone()[0]
print('Project id:', project_id)
# Insert tasks and subtasks
cur.execute("INSERT INTO tasks (project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
    project_id, 'Install sensors', 'Install sensors across building', 'bob', None, 'Open', 'High', '2026-09-10 12:00', 'tester', datetime.datetime.now().isoformat()
))
conn.commit()
cur.execute("SELECT id FROM tasks WHERE title=? AND project_id=?", ('Install sensors', project_id))
parent_id = cur.fetchone()[0]
print('Parent task id:', parent_id)
# subtask 1
cur.execute("INSERT INTO tasks (project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date, parent_task_id, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
    project_id, 'Mount sensor brackets', 'Mount brackets at locations', 'carol', None, 'Open', 'Medium', '2026-09-05 10:00', parent_id, 'tester', datetime.datetime.now().isoformat()
))
conn.commit()
cur.execute("SELECT id FROM tasks WHERE title=? AND parent_task_id=?", ('Mount sensor brackets', parent_id))
sub1 = cur.fetchone()[0]
print('Subtask1 id:', sub1)
# subtask 1.1
cur.execute("INSERT INTO tasks (project_id, title, description, assigned_user, assigned_group_id, status, priority, due_date, parent_task_id, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
    project_id, 'Fasten brackets', 'Use screws to fasten', 'dave', None, 'Open', 'Low', '2026-09-05 15:00', sub1, 'tester', datetime.datetime.now().isoformat()
))
conn.commit()
cur.execute("SELECT id FROM tasks WHERE title=? AND parent_task_id=?", ('Fasten brackets', sub1))
sub11 = cur.fetchone()[0]
print('Subtask1.1 id:', sub11)

# Verify tree
cur.execute("SELECT id, title, parent_task_id FROM tasks ORDER BY id")
rows = cur.fetchall()
print('Tasks in DB:')
for r in rows:
    print(r)
# Basic assertions
assert any(r[1]=='Install sensors' for r in rows), 'Parent task missing'
assert any(r[1]=='Mount sensor brackets' for r in rows), 'Subtask1 missing'
assert any(r[1]=='Fasten brackets' for r in rows), 'Subtask1.1 missing'

# Export CSV (using same logic as module but without GUI messagebox)
import csv

cur.execute("SELECT t.* , p.name as project_name, g.name as group_name FROM tasks t LEFT JOIN projects p ON t.project_id=p.id LEFT JOIN groups g ON t.assigned_group_id=g.id ORDER BY t.id")
rows = [dict(r) for r in cur.fetchall()]
# build uid map
tasks = {r['id']: r for r in rows}
children = {}
roots = []
for tid, r in tasks.items():
    pid = r.get('parent_task_id')
    if pid:
        children.setdefault(pid, []).append(tid)
    else:
        roots.append(tid)
for k in children:
    children[k].sort()
roots.sort()
uid_map = {}
def assign_uids(tid, parent_uid=None):
    if parent_uid is None:
        uid = str(tid)
    else:
        siblings = children.get(int(tasks[tid].get('parent_task_id') or 0), [])
        idx = siblings.index(tid) + 1
        uid = f"{parent_uid}-{idx}"
    uid_map[tid] = uid
    for c in children.get(tid, []):
        assign_uids(c, uid)
for r in roots:
    assign_uids(r, None)

EXPORT_DIR = os.path.join(os.getcwd(), "project_management_exports")
import os
os.makedirs(EXPORT_DIR, exist_ok=True)
out_csv = os.path.join(EXPORT_DIR, f"test_tasks_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(["TaskUID","TaskID","ParentTaskUID","Project","Title","Description","Assignee","AssignedGroup","Status","Priority","DueDate","CreatedBy","CreatedAt","UpdatedAt"])
    for r in rows:
        tid = r['id']
        uid = uid_map.get(tid, str(tid))
        pid = r.get('parent_task_id')
        parent_uid = uid_map.get(pid) if pid else ''
        w.writerow([uid, tid, parent_uid, r.get('project_name') or '', r.get('title') or '', r.get('description') or '', r.get('assigned_user') or '', r.get('group_name') or '', r.get('status') or '', r.get('priority') or '', r.get('due_date') or '', r.get('created_by') or '', r.get('created_at') or '', r.get('updated_at') or ''])

print('CSV exported to', out_csv)

# Export Excel-like .xls
out_xls = os.path.join(EXPORT_DIR, f"test_tasks_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xls")
with open(out_xls, 'w', encoding='utf-8') as f:
    f.write('<html><head><meta charset="utf-8" /></head><body><table border="1">')
    f.write('<tr><th>TaskUID</th><th>TaskID</th><th>ParentTaskUID</th><th>Project</th><th>Title</th><th>Description</th><th>Assignee</th><th>AssignedGroup</th><th>Status</th><th>Priority</th><th>DueDate</th><th>CreatedBy</th><th>CreatedAt</th><th>UpdatedAt</th></tr>')
    def esc(x):
        return (x or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    for r in rows:
        tid = r['id']
        uid = uid_map.get(tid, str(tid))
        pid = r.get('parent_task_id')
        parent_uid = uid_map.get(pid) if pid else ''
        f.write(f"<tr><td>{esc(uid)}</td><td>{tid}</td><td>{esc(parent_uid)}</td><td>{esc(r.get('project_name') or '')}</td><td>{esc(r.get('title') or '')}</td><td>{esc(r.get('description') or '')}</td><td>{esc(r.get('assigned_user') or '')}</td><td>{esc(r.get('group_name') or '')}</td><td>{esc(r.get('status') or '')}</td><td>{esc(r.get('priority') or '')}</td><td>{esc(r.get('due_date') or '')}</td><td>{esc(r.get('created_by') or '')}</td><td>{esc(r.get('created_at') or '')}</td><td>{esc(r.get('updated_at') or '')}</td></tr>")
    f.write('</table></body></html>')

print('XLS exported to', out_xls)

# Attempt to export a real .xlsx using openpyxl if available
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ["TaskUID","TaskID","ParentTaskUID","Project","Title","Description","Assignee","AssignedGroup","Status","Priority","DueDate","CreatedBy","CreatedAt","UpdatedAt"]
    ws.append(headers)
    for r in rows:
        tid = r['id']
        uid = uid_map.get(tid, str(tid))
        pid = r.get('parent_task_id')
        parent_uid = uid_map.get(pid) if pid else ''
        ws.append([uid, tid, parent_uid, r.get('project_name') or '', r.get('title') or '', r.get('description') or '', r.get('assigned_user') or '', r.get('group_name') or '', r.get('status') or '', r.get('priority') or '', r.get('due_date') or '', r.get('created_by') or '', r.get('created_at') or '', r.get('updated_at') or ''])
    out_xlsx = os.path.join(EXPORT_DIR, f"test_tasks_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    wb.save(out_xlsx)
    print('XLSX exported to', out_xlsx)
except Exception as e:
    print('openpyxl not available or export failed:', e)
    print('To enable .xlsx export install openpyxl: pip install openpyxl')

conn.close()
print('Test completed.')
