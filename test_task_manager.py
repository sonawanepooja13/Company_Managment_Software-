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

    def test_task_creation_validates_required_fields_and_ignores_blank_assignees(self):
        with self.assertRaises(ValueError):
            self.manager.create_task("   ", "Missing title", self.hr_dept.id, self.admin.id, assignee_id=self.employee_1.id)
        with self.assertRaises(ValueError):
            self.manager.create_task("Policy review", "No valid assignee", self.hr_dept.id, self.admin.id, assignee_ids=["", "   "])

        task = self.manager.create_task(
            title="Team sync",
            description="Check the project status.",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_ids=["", self.employee_1.id, self.employee_1.id, self.employee_2.id],
        )
        self.assertEqual(task.assignee_ids, [self.employee_1.id, self.employee_2.id])
        self.assertEqual(task.assignee_id, self.employee_1.id)

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

    def test_chat_message_creates_notification_and_validation(self):
        sender = self.manager.add_user("Manager One", "manager@company.com", UserRole.MANAGER)

        sent = self.manager.send_chat_message(sender.id, self.employee_1.id, "Please review the onboarding checklist.")
        self.assertEqual(sent["sender_id"], sender.id)
        self.assertEqual(sent["recipient_id"], self.employee_1.id)
        self.assertTrue(any(n["type"] == "chat_message" for n in self.manager.notifications_for_user(self.employee_1.id)))
        self.assertEqual(self.manager.unread_chat_count(self.employee_1.id), 1)

        with self.assertRaises(ValueError):
            self.manager.send_chat_message(sender.id, self.employee_1.id, "   ")
        with self.assertRaises(ValueError):
            self.manager.send_chat_message(sender.id, self.employee_1.id, "x" * 1001)
        with self.assertRaises(ValueError):
            self.manager.send_chat_message(sender.id, sender.id, "self message")

    def test_admin_and_assignee_access_chat_permissions(self):
        admin = self.manager.add_user("Site Admin", "siteadmin@company.com", UserRole.ADMIN)
        task = self.manager.create_task(
            title="Urgent review",
            description="Check the final draft",
            department_id=self.hr_dept.id,
            created_by=admin.id,
            assignee_id=self.employee_1.id,
        )

        self.assertIn(self.employee_1.id, [u.id for u in self.manager.available_chat_users(admin.id, task.id)])
        self.assertIn(admin.id, [u.id for u in self.manager.available_chat_users(self.employee_1.id, task.id)])
        self.assertNotIn(self.employee_2.id, [u.id for u in self.manager.available_chat_users(self.employee_1.id, task.id)])
        self.assertTrue(self.manager.can_access_chat_with(admin.id, self.employee_1.id, task.id))
        self.assertTrue(self.manager.can_access_chat_with(self.employee_1.id, self.employee_1.id, task.id))
        self.assertFalse(self.manager.can_access_chat_with(self.employee_1.id, self.employee_2.id, task.id))
        self.assertTrue(task.id)

    def test_admin_can_send_messages_in_any_task_chat(self):
        task = self.manager.create_task(
            title="Admin support chat",
            description="Allow administration to coordinate service updates",
            department_id=self.hr_dept.id,
            created_by=self.employee_1.id,
            assignee_id=self.employee_2.id,
        )
        task_group = self.manager.get_or_create_task_group(task.id)

        sent = self.manager.send_group_message(
            self.admin.id,
            task_group["id"],
            "I have updated the service request.",
        )

        self.assertEqual(sent["sender_id"], self.admin.id)
        self.assertEqual(self.manager.get_group_chat_messages(task_group["id"]), [sent])

    def test_chat_attachment_keeps_display_name_and_path(self):
        task = self.manager.create_task(
            title="Attachment chat",
            description="Review the attached service document",
            department_id=self.hr_dept.id,
            created_by=self.admin.id,
            assignee_id=self.employee_1.id,
        )
        task_group = self.manager.get_or_create_task_group(task.id)

        sent = self.manager.send_group_message(
            self.admin.id,
            task_group["id"],
            "",
            attachment="service-document.pdf",
            attachment_path=os.path.join(self.temp_dir.name, "service-document.pdf"),
        )

        self.assertEqual(sent["attachment"], "service-document.pdf")
        self.assertTrue(sent["attachment_path"].endswith("service-document.pdf"))

    def test_stale_task_participant_ids_are_ignored_in_chat_lists(self):
        admin = self.manager.add_user("Site Admin 2", "siteadmin2@company.com", UserRole.ADMIN)
        task = self.manager.create_task(
            title="Cleanup stale participants",
            description="Make sure only valid users appear in task chat",
            department_id=self.hr_dept.id,
            created_by=admin.id,
            assignee_id=self.employee_1.id,
        )
        task.assignee_ids = [self.employee_1.id, "MISSING-ID"]
        task.assignee_id = self.employee_1.id

        participants = [u.id for u in self.manager.available_chat_users(admin.id, task.id)]
        self.assertIn(self.employee_1.id, participants)
        self.assertNotIn("MISSING-ID", participants)
        task_group = self.manager.get_or_create_task_group(task.id)
        self.assertIn(self.employee_1.id, task_group["participants"])
        self.assertNotIn("MISSING-ID", task_group["participants"])

    def test_hr_employee_record_department_matches_task_department_filters(self):
        view = TaskManagerView.__new__(TaskManagerView)
        view.manager = TaskManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            original_csv_dir = __import__("config").CSV_DIR
            __import__("config").CSV_DIR = temp_dir
            try:
                with open(os.path.join(temp_dir, "employee record.csv"), "w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=("employee_id", "full_name", "department"))
                    writer.writeheader()
                    writer.writerow({"employee_id": "SE-0101", "full_name": "Research Engineer", "department": "Research & Development (R&D)"})
                options = view._employee_options_for_department("Research & Development (R&D)")
                self.assertTrue(options)
                self.assertEqual(options[0][1].id, "SE-0101")
            finally:
                __import__("config").CSV_DIR = original_csv_dir

    def test_hr_employee_record_path_prefers_hr_directory_when_root_is_empty(self):
        view = TaskManagerView.__new__(TaskManagerView)
        view.manager = TaskManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            original_csv_dir = __import__("config").CSV_DIR
            original_hr_dir = getattr(__import__("config"), "HR_DIR", None)
            __import__("config").CSV_DIR = temp_dir
            __import__("config").HR_DIR = os.path.join(temp_dir, "HR")
            os.makedirs(__import__("config").HR_DIR, exist_ok=True)
            try:
                with open(os.path.join(temp_dir, "employee record.csv"), "w", newline="", encoding="utf-8") as file:
                    file.write("employee_id,full_name,department\n")
                with open(os.path.join(__import__("config").HR_DIR, "employee record.csv"), "w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=("employee_id", "full_name", "department"))
                    writer.writeheader()
                    writer.writerow({"employee_id": "SE-0122", "full_name": "POOJA SONAWANE", "department": "Research & Development (R&D)"})
                self.assertEqual(os.path.basename(view._resolve_employee_record_path()), "employee record.csv")
                self.assertTrue(os.path.dirname(view._resolve_employee_record_path()).endswith("HR"))
                options = view._employee_options_for_department("Research & Development (R&D)")
                self.assertEqual(options[0][1].id, "SE-0122")
            finally:
                __import__("config").CSV_DIR = original_csv_dir
                __import__("config").HR_DIR = original_hr_dir


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
            original_hr_dir = getattr(__import__("config"), "HR_DIR", None)
            __import__("config").CSV_DIR = temp_dir
            __import__("config").HR_DIR = os.path.join(temp_dir, "HR")
            os.makedirs(__import__("config").HR_DIR, exist_ok=True)
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
                __import__("config").HR_DIR = original_hr_dir

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
