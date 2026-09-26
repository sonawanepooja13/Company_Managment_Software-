import unittest
import csv
import os
import tempfile
import tkinter as tk
from datetime import datetime, timedelta

from task_manager import TaskManager, TaskManagerView, UserRole, TaskStatus, TaskPriority


class TaskManagerTests(unittest.TestCase):
    def setUp(self):
        self.original_csv_dir = __import__("config").CSV_DIR
        self.temp_dir = tempfile.TemporaryDirectory()
        __import__("config").CSV_DIR = self.temp_dir.name
        self.manager = TaskManager()
        self.admin = self.manager.add_user("System Admin", "admin@company.com", UserRole.ADMIN)
        self.hr_dept = self.manager.add_department("HR", manager_id=self.admin.id)
        self.employee_1 = self.manager.add_user("Alice", "alice@company.com", UserRole.EMPLOYEE)
        self.employee_2 = self.manager.add_user("Bob", "bob@company.com", UserRole.EMPLOYEE)
        self.manager.assign_user_to_department(self.employee_1.id, self.hr_dept.id, "Member")
        self.manager.assign_user_to_department(self.employee_2.id, self.hr_dept.id, "Member")

    def tearDown(self):
        __import__("config").CSV_DIR = self.original_csv_dir
        self.temp_dir.cleanup()

    def test_task_assignment_creates_notification(self):
        task = self.manager.create_task(
            title="Review onboarding",
            description="Check onboarding documents",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_id=self.employee_1.id,
            priority=TaskPriority.HIGH,
            due_date=datetime.utcnow() + timedelta(days=2),
        )
        self.assertEqual(task.status, TaskStatus.ASSIGNED)
        notifications = self.manager.notifications_for_user(self.employee_1.id)
        self.assertTrue(any(n["type"] == "assigned" for n in notifications))

    def test_task_supports_multiple_assignees(self):
        task = self.manager.create_task(
            title="Prepare handover",
            description="Coordinate the handover",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_ids=[self.employee_1.id, self.employee_2.id],
        )
        self.assertEqual(task.assignee_ids, [self.employee_1.id, self.employee_2.id])
        self.assertEqual(task.assignee_id, self.employee_1.id)
        self.assertTrue(any(n["type"] == "assigned" for n in self.manager.notifications_for_user(self.employee_1.id)))
        self.assertTrue(any(n["type"] == "assigned" for n in self.manager.notifications_for_user(self.employee_2.id)))
        self.manager.accept_task(task.id, self.employee_2.id)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

    def test_employee_can_accept_and_update_status(self):
        task = self.manager.create_task(
            title="Policy review",
            description="Review vendor policy",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_id=self.employee_1.id,
        )
        self.manager.accept_task(task.id, self.employee_1.id)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

    def test_manager_can_submit_for_review_and_complete(self):
        task = self.manager.create_task(
            title="Benefits update",
            description="Update employee benefit list",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_id=self.employee_1.id,
            reviewer_id=self.admin.id,
        )
        self.manager.accept_task(task.id, self.employee_1.id)
        self.manager.submit_for_review(task.id, self.employee_1.id)
        self.manager.complete_task(task.id, self.admin.id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)

    def test_department_dashboard_summary(self):
        self.manager.create_task(
            title="Task A",
            description="A",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_id=self.employee_1.id,
        )
        self.manager.create_task(
            title="Task B",
            description="B",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_id=self.employee_2.id,
        )
        summary = self.manager.department_dashboard(self.hr_dept.id)
        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["department_name"], "HR")


class TaskManagerViewTests(unittest.TestCase):
    def test_new_task_window_opens(self):
        root = tk.Tk()
        root.withdraw()
        try:
            view = TaskManagerView(root, user_data={"username": "Alice", "role": "Admin"})
            view.open_new_task_window()
            self.assertIsNotNone(view.new_task_window)
            self.assertTrue(view.new_task_window.winfo_exists())
            view.new_task_window.destroy()
        finally:
            root.destroy()

    def test_employee_records_with_duplicate_names_remain_separate(self):
        view = TaskManagerView.__new__(TaskManagerView)
        view.manager = TaskManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            original_csv_dir = __import__("config").CSV_DIR
            __import__("config").CSV_DIR = temp_dir
            try:
                with open(os.path.join(temp_dir, "employee record.csv"), "w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=("employee_id", "full_name", "department"))
                    writer.writeheader()
                    writer.writerow({"employee_id": "EMP-1", "full_name": "Same Name", "department": "HR"})
                    writer.writerow({"employee_id": "EMP-2", "full_name": "Same Name", "department": "Finance"})
                users = view._load_employee_users()
                self.assertEqual([user.id for user in users], ["EMP-1", "EMP-2"])
            finally:
                __import__("config").CSV_DIR = original_csv_dir

    def test_empty_reload_does_not_overwrite_existing_task_file(self):
        manager = TaskManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            original_csv_dir = __import__("config").CSV_DIR
            __import__("config").CSV_DIR = temp_dir
            try:
                task_path = manager.task_csv_path()
                with open(task_path, "w", encoding="utf-8") as file:
                    file.write("task_id,title\nexisting,Keep this task\n")
                manager.load_tasks()
                manager._persist_tasks()
                with open(task_path, encoding="utf-8") as file:
                    self.assertIn("Keep this task", file.read())
            finally:
                __import__("config").CSV_DIR = original_csv_dir


if __name__ == "__main__":
    unittest.main()
