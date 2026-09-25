
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import tkinter as tk
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Dict, List, Optional
from uuid import uuid4

import config


DEPARTMENT_NAMES = [
    "Executive / Leadership",
    "Human Resources (HR)",
    "Finance & Accounting",
    "Sales & Business Development",
    "Marketing & Communications",
    "Operations & Logistics",
    "Information Technology (IT) / Engineering",
    "Customer Support / Success",
    "Legal & Compliance",
    "Research & Development (R&D)",
]
ALL_DEPARTMENTS = "All Departments"
ALL_USERS = "All Users"
TASK_CSV_HEADERS = (
    "task_id", "title", "description", "department", "created_by", "created_by_name",
    "assignee_id", "assignee_ids", "assignee_name", "reviewer_id", "reviewer_name", "priority", "status",
    "due_date", "created_at", "updated_at", "completed_at", "accepted_at",
)


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class TaskStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CLOSED = "closed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


PRIORITY_LABELS = {
    TaskPriority.VERY_LOW: "Very Low",
    TaskPriority.LOW: "Low",
    TaskPriority.MEDIUM: "Medium",
    TaskPriority.HIGH: "High",
    TaskPriority.VERY_HIGH: "Very High",
}
PRIORITY_BY_LABEL = {label: priority for priority, label in PRIORITY_LABELS.items()}
PRIORITY_CHOICES = [PRIORITY_LABELS[priority] for priority in TaskPriority]
LEGACY_PRIORITY_MAP = {"urgent": TaskPriority.VERY_HIGH}


def parse_priority(value, default=TaskPriority.MEDIUM) -> TaskPriority:
    if value is None:
        return default
    text = str(value).strip().lower()
    if not text:
        return default
    if text in LEGACY_PRIORITY_MAP:
        return LEGACY_PRIORITY_MAP[text]
    try:
        return TaskPriority(text)
    except ValueError:
        return default


@dataclass
class User:
    id: str
    name: str
    email: str
    role: UserRole
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Department:
    id: str
    name: str
    manager_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    members: Dict[str, str] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    title: str
    description: str
    department_id: str
    created_by: str
    assignee_id: Optional[str] = None
    assignee_ids: List[str] = field(default_factory=list)
    reviewer_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.CREATED
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None


class TaskManager:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.departments: Dict[str, Department] = {}
        self.tasks: Dict[str, Task] = {}
        self.notifications: Dict[str, List[Dict[str, Any]]] = {}
        self.email_notifications: Dict[str, List[Dict[str, Any]]] = {}
        self.chat_messages: Dict[str, List[Dict[str, Any]]] = {}
        self.chat_groups: Dict[str, Dict[str, Any]] = {}
        self.group_chat_messages: Dict[str, List[Dict[str, Any]]] = {}
        self._task_file_had_rows = False

    @staticmethod
    def task_csv_path():
        return os.path.join(config.CSV_DIR, "task.csv")

    @staticmethod
    def _format_datetime(value):
        return value.isoformat() if value else ""

    @staticmethod
    def _parse_datetime(value):
        return datetime.fromisoformat(value) if value else None

    def _persist_tasks(self) -> None:
        if self._task_file_had_rows and not self.tasks and os.path.exists(self.task_csv_path()):
            return
        os.makedirs(config.CSV_DIR, exist_ok=True)
        with open(self.task_csv_path(), "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=TASK_CSV_HEADERS)
            writer.writeheader()
            for task in self.tasks.values():
                department = self.departments.get(task.department_id)
                creator = self.users.get(task.created_by)
                assignee_ids = task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])
                assignee_names = [self.users[user_id].name for user_id in assignee_ids if user_id in self.users]
                reviewer = self.users.get(task.reviewer_id) if task.reviewer_id else None
                writer.writerow({
                    "task_id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "department": department.name if department else "",
                    "created_by": task.created_by,
                    "created_by_name": creator.name if creator else "",
                    "assignee_id": task.assignee_id or "",
                    "assignee_ids": json.dumps(assignee_ids),
                    "assignee_name": ", ".join(assignee_names),
                    "reviewer_id": task.reviewer_id or "",
                    "reviewer_name": reviewer.name if reviewer else "",
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "due_date": self._format_datetime(task.due_date),
                    "created_at": self._format_datetime(task.created_at),
                    "updated_at": self._format_datetime(task.updated_at),
                    "completed_at": self._format_datetime(task.completed_at),
                    "accepted_at": self._format_datetime(task.accepted_at),
                })

    def load_tasks(self) -> None:
        path = self.task_csv_path()
        if not os.path.exists(path):
            return
        with open(path, newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
            self._task_file_had_rows = bool(rows)
            for row in rows:
                department_name = (row.get("department") or "").strip()
                department = next((item for item in self.departments.values() if item.name.casefold() == department_name.casefold()), None)
                if department is None:
                    continue

                def resolve_user(user_id_key, name_key):
                    name = (row.get(name_key) or "").strip()
                    existing = next((user for user in self.users.values() if user.name.casefold() == name.casefold()), None)
                    if existing:
                        return existing.id
                    return (row.get(user_id_key) or "").strip() or None

                assignee_ids = []
                try:
                    stored_assignee_ids = json.loads(row.get("assignee_ids") or "[]")
                    if isinstance(stored_assignee_ids, list):
                        assignee_ids = [user_id for user_id in stored_assignee_ids if user_id in self.users]
                except (TypeError, json.JSONDecodeError):
                    assignee_ids = []
                legacy_assignee_id = resolve_user("assignee_id", "assignee_name")
                if not assignee_ids and legacy_assignee_id:
                    assignee_ids = [legacy_assignee_id]

                task = Task(
                    id=(row.get("task_id") or str(uuid4())).strip(),
                    title=(row.get("title") or "").strip(),
                    description=(row.get("description") or "").strip(),
                    department_id=department.id,
                    created_by=resolve_user("created_by", "created_by_name") or next(iter(self.users), ""),
                    assignee_id=assignee_ids[0] if assignee_ids else None,
                    assignee_ids=assignee_ids,
                    reviewer_id=resolve_user("reviewer_id", "reviewer_name"),
                    priority=parse_priority(row.get("priority")),
                    status=TaskStatus((row.get("status") or TaskStatus.CREATED.value).strip()),
                    due_date=self._parse_datetime(row.get("due_date") or ""),
                    created_at=self._parse_datetime(row.get("created_at") or "") or datetime.utcnow(),
                    updated_at=self._parse_datetime(row.get("updated_at") or "") or datetime.utcnow(),
                    completed_at=self._parse_datetime(row.get("completed_at") or ""),
                    accepted_at=self._parse_datetime(row.get("accepted_at") or ""),
                )
                if task.title:
                    self.tasks[task.id] = task

    def add_user(self, name: str, email: str, role: UserRole = UserRole.EMPLOYEE) -> User:
        user_id = str(uuid4())
        user = User(id=user_id, name=name, email=email, role=role)
        self.users[user_id] = user
        self.notifications.setdefault(user_id, [])
        return user

    def add_department(self, name: str, manager_id: Optional[str] = None) -> Department:
        department = Department(id=str(uuid4()), name=name, manager_id=manager_id)
        self.departments[department.id] = department
        return department

    def assign_user_to_department(self, user_id: str, department_id: str, role_name: str = "Member") -> None:
        if user_id not in self.users:
            raise ValueError("User not found")
        if department_id not in self.departments:
            raise ValueError("Department not found")
        self.departments[department_id].members[user_id] = role_name

    def _ensure_user_exists(self, user_id: str) -> None:
        if user_id not in self.users:
            raise ValueError("User not found")

    def _ensure_department_exists(self, department_id: str) -> None:
        if department_id not in self.departments:
            raise ValueError("Department not found")

    def _record_notification(self, user_id: str, notification_type: str, message: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_user_exists(user_id)
        notification = {
            "id": str(uuid4()),
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "task_id": task_id,
            "read": False,
            "created_at": datetime.utcnow(),
        }
        self.notifications.setdefault(user_id, []).append(notification)
        self.send_email_notification(
            user_id,
            f"{notification_type.replace('_', ' ').title()} Notification",
            message,
            task_id=task_id,
        )
        return notification

    def send_email_notification(self, user_id: str, subject: str, body: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_user_exists(user_id)
        user = self.users[user_id]
        email_message = {
            "id": str(uuid4()),
            "user_id": user_id,
            "email": user.email,
            "subject": subject,
            "body": body,
            "task_id": task_id,
            "sent_at": datetime.utcnow(),
            "read": False,
        }
        self.email_notifications.setdefault(user_id, []).append(email_message)
        return email_message

    def email_notifications_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        self._ensure_user_exists(user_id)
        return self.email_notifications.get(user_id, [])

    def create_task(
        self,
        title: str,
        description: str,
        department_id: str,
        created_by: str,
        assignee_id: Optional[str] = None,
        assignee_ids: Optional[List[str]] = None,
        reviewer_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
    ) -> Task:
        self._ensure_user_exists(created_by)
        self._ensure_department_exists(department_id)

        cleaned_title = (title or "").strip()
        if not cleaned_title:
            raise ValueError("Task title is required.")

        normalized_assignee_ids = []
        seen = set()
        for user_id in (assignee_ids or []) + ([assignee_id] if assignee_id else []):
            if user_id is None:
                continue
            candidate = str(user_id).strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            self._ensure_user_exists(candidate)
            normalized_assignee_ids.append(candidate)

        if not normalized_assignee_ids:
            raise ValueError("At least one valid assignee is required to create a task.")

        if reviewer_id is not None:
            reviewer_id = str(reviewer_id).strip()
            if reviewer_id:
                self._ensure_user_exists(reviewer_id)

        task = Task(
            id=str(uuid4()),
            title=cleaned_title,
            description=(description or "").strip() or "No description provided.",
            department_id=department_id,
            created_by=created_by,
            assignee_id=normalized_assignee_ids[0] if normalized_assignee_ids else None,
            assignee_ids=normalized_assignee_ids,
            reviewer_id=reviewer_id,
            priority=priority,
            status=TaskStatus.ASSIGNED if normalized_assignee_ids else TaskStatus.CREATED,
            due_date=due_date,
        )
        self.tasks[task.id] = task
        self._persist_tasks()

        for assigned_user_id in normalized_assignee_ids:
            self._record_notification(
                assigned_user_id,
                "assigned",
                f"You have been assigned task: {cleaned_title}",
                task_id=task.id,
            )

        return task

    def accept_task(self, task_id: str, user_id: str) -> Task:
        task = self.tasks[task_id]
        if user_id not in (task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])):
            raise PermissionError("Only an assignee can accept the task")
        task.status = TaskStatus.IN_PROGRESS
        task.accepted_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        self._record_notification(
            task.created_by,
            "status_update",
            f"Task '{task.title}' has been accepted and is now in progress.",
            task_id=task.id,
        )
        self._persist_tasks()
        return task

    def submit_for_review(self, task_id: str, user_id: str) -> Task:
        task = self.tasks[task_id]
        if user_id not in (task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])):
            raise PermissionError("Only an assignee can submit a task for review")
        task.status = TaskStatus.UNDER_REVIEW
        task.updated_at = datetime.utcnow()
        if task.reviewer_id is not None:
            self._record_notification(
                task.reviewer_id,
                "review_requested",
                f"Task '{task.title}' is ready for review.",
                task_id=task.id,
            )
        self._persist_tasks()
        return task

    def complete_task(self, task_id: str, user_id: str) -> Task:
        task = self.tasks[task_id]
        user = self.users[user_id]
        if task.reviewer_id != user_id and user.role != UserRole.ADMIN:
            raise PermissionError("Only the reviewer or admin can complete the task")
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        self._record_notification(
            task.created_by,
            "completed",
            f"Task '{task.title}' has been completed.",
            task_id=task.id,
        )
        for assigned_user_id in task.assignee_ids or ([task.assignee_id] if task.assignee_id else []):
            self._record_notification(
            assigned_user_id,
                "completed",
                f"Your task '{task.title}' has been marked completed.",
                task_id=task.id,
            )
        self._persist_tasks()
        return task

    @staticmethod
    def _conversation_key(user_one: str, user_two: str) -> str:
        return "|".join(sorted((user_one, user_two)))

    @staticmethod
    def _validate_chat_message(message: str) -> str:
        cleaned = (message or "").strip()
        if not cleaned:
            raise ValueError("Chat message is required.")
        if len(cleaned) > 1000:
            raise ValueError("Chat message cannot exceed 1000 characters.")
        return cleaned

    def send_chat_message(self, sender_id: str, recipient_id: str, message: str) -> Dict[str, Any]:
        self._ensure_user_exists(sender_id)
        self._ensure_user_exists(recipient_id)
        if sender_id == recipient_id:
            raise ValueError("A user cannot send a chat message to themselves.")

        cleaned_message = self._validate_chat_message(message)
        sender = self.users[sender_id]
        conversation_key = self._conversation_key(sender_id, recipient_id)
        chat_message = {
            "id": str(uuid4()),
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message": cleaned_message,
            "created_at": datetime.utcnow(),
            "read": False,
        }
        self.chat_messages.setdefault(conversation_key, []).append(chat_message)
        self._record_notification(
            recipient_id,
            "chat_message",
            f"New message from {sender.name}: {cleaned_message[:80]}{'...' if len(cleaned_message) > 80 else ''}",
        )
        return chat_message

    def get_chat_messages(self, user_one_id: str, user_two_id: str) -> List[Dict[str, Any]]:
        self._ensure_user_exists(user_one_id)
        self._ensure_user_exists(user_two_id)
        return list(self.chat_messages.get(self._conversation_key(user_one_id, user_two_id), []))

    def unread_chat_count(self, user_id: str) -> int:
        self._ensure_user_exists(user_id)
        total = 0
        for conversation in self.chat_messages.values():
            total += sum(1 for message in conversation if message.get("recipient_id") == user_id and not message.get("read", False))
        return total

    def mark_chat_messages_read(self, user_id: str, other_user_id: Optional[str] = None) -> int:
        self._ensure_user_exists(user_id)
        marked = 0
        if other_user_id is not None:
            self._ensure_user_exists(other_user_id)
            conversation = self.chat_messages.get(self._conversation_key(user_id, other_user_id), [])
            for message in conversation:
                if message.get("recipient_id") == user_id and not message.get("read", False):
                    message["read"] = True
                    marked += 1
            return marked

        for conversation in self.chat_messages.values():
            for message in conversation:
                if message.get("recipient_id") == user_id and not message.get("read", False):
                    message["read"] = True
                    marked += 1
        return marked

    def _valid_task_participants(self, task: Any) -> List[str]:
        assignee_ids = task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])
        participant_ids = set(assignee_ids)
        if task.created_by:
            participant_ids.add(task.created_by)
        if task.reviewer_id:
            participant_ids.add(task.reviewer_id)
        valid_ids = [user_id for user_id in participant_ids if user_id in self.users]
        return sorted(valid_ids, key=lambda item: self.users[item].name.lower())

    def get_or_create_task_group(self, task_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError("Task not found.")

        participant_ids = self._valid_task_participants(task)
        if not participant_ids:
            raise ValueError("This task has no valid participants for a chat group.")

        group_key = f"task:{task_id}"
        group = self.chat_groups.get(group_key)
        if group is None:
            group = {
                "id": group_key,
                "name": f"Task: {task.title}",
                "task_id": task_id,
                "participants": participant_ids,
                "created_by": task.created_by,
                "created_at": datetime.utcnow(),
            }
            self.chat_groups[group_key] = group
            self.group_chat_messages.setdefault(group_key, [])
        return group

    def available_chat_users(self, user_id: str, task_id: Optional[str] = None) -> List[User]:
        self._ensure_user_exists(user_id)
        if task_id is None:
            if self.users[user_id].role == UserRole.ADMIN:
                return [user for user_id_key, user in self.users.items() if user_id_key != user_id]
            return []

        task = self.tasks.get(task_id)
        if task is None:
            return []

        participant_ids = set(self._valid_task_participants(task))
        if self.users[user_id].role == UserRole.ADMIN:
            participant_ids.add(user_id)
        participant_ids.discard(user_id)
        return [self.users[user_key] for user_key in sorted(participant_ids, key=lambda item: self.users[item].name.lower()) if user_key in self.users]

    def can_access_chat_with(self, user_id: str, other_user_id: str, task_id: Optional[str] = None) -> bool:
        self._ensure_user_exists(user_id)
        self._ensure_user_exists(other_user_id)
        if task_id is None:
            if user_id == other_user_id:
                return True
            return self.users[user_id].role == UserRole.ADMIN
        task = self.tasks.get(task_id)
        if task is None:
            return False
        if user_id == other_user_id:
            return True
        if self.users[user_id].role == UserRole.ADMIN:
            return True
        assignee_ids = task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])
        participant_ids = set(assignee_ids)
        if task.created_by:
            participant_ids.add(task.created_by)
        if task.reviewer_id:
            participant_ids.add(task.reviewer_id)
        return user_id in participant_ids and other_user_id in participant_ids

    def create_group_chat(self, creator_id: str, participant_ids: List[str], title: str = "Team Group") -> Dict[str, Any]:
        self._ensure_user_exists(creator_id)
        unique_people = []
        seen = set()
        for participant_id in participant_ids:
            if participant_id not in self.users or participant_id == creator_id:
                continue
            if self.users[creator_id].role != UserRole.ADMIN and not self.can_access_chat_with(creator_id, participant_id):
                continue
            if participant_id not in seen:
                seen.add(participant_id)
                unique_people.append(participant_id)
        if not unique_people:
            raise ValueError("At least one valid participant is required for a group chat.")
        group = {
            "id": str(uuid4()),
            "name": (title or "Team Group").strip() or "Team Group",
            "participants": [creator_id] + unique_people,
            "created_by": creator_id,
            "created_at": datetime.utcnow(),
        }
        self.chat_groups[group["id"]] = group
        self.group_chat_messages.setdefault(group["id"], [])
        return group

    def send_group_message(self, sender_id: str, group_id: str, message: str, attachment: Optional[str] = None, attachment_path: Optional[str] = None, reaction: Optional[str] = None, call_type: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_user_exists(sender_id)
        group = self.chat_groups.get(group_id)
        if group is None:
            raise ValueError("Group chat not found.")
        sender = self.users[sender_id]
        admin_can_access_task_chat = sender.role == UserRole.ADMIN and group.get("task_id") in self.tasks
        if sender_id not in group["participants"] and not admin_can_access_task_chat:
            raise PermissionError("Only group members can send messages in this chat.")
        cleaned_message = message.strip() if message else ""
        if not cleaned_message and not attachment and not call_type:
            raise ValueError("A group chat message, file, or call action is required.")
        if len(cleaned_message) > 1000:
            raise ValueError("Group chat message cannot exceed 1000 characters.")
        payload = {
            "id": str(uuid4()),
            "sender_id": sender_id,
            "group_id": group_id,
            "message": cleaned_message,
            "attachment": attachment,
            "attachment_path": attachment_path,
            "reaction": reaction,
            "call_type": call_type,
            "created_at": datetime.utcnow(),
            "read_by": {sender_id},
        }
        self.group_chat_messages.setdefault(group_id, []).append(payload)
        for participant_id in group["participants"]:
            if participant_id == sender_id:
                continue
            self._record_notification(
                participant_id,
                "group_chat",
                f"New group message in '{group['name']}': {cleaned_message[:80]}{'...' if len(cleaned_message) > 80 else ''}",
            )
        return payload

    def get_group_chat_messages(self, group_id: str) -> List[Dict[str, Any]]:
        if group_id not in self.chat_groups:
            return []
        return list(self.group_chat_messages.get(group_id, []))

    def notifications_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        self._ensure_user_exists(user_id)
        return self.notifications.get(user_id, [])

    def department_dashboard(self, department_id: str) -> Dict[str, Any]:
        self._ensure_department_exists(department_id)
        department = self.departments[department_id]
        tasks = [t for t in self.tasks.values() if t.department_id == department_id]
        overdue_count = 0
        for task in tasks:
            if task.due_date and task.status not in (TaskStatus.COMPLETED, TaskStatus.CLOSED) and task.due_date < datetime.utcnow():
                overdue_count += 1

        summary = {
            "department_name": department.name,
            "total_tasks": len(tasks),
            "completed_tasks": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            "under_review": sum(1 for t in tasks if t.status == TaskStatus.UNDER_REVIEW),
            "overdue": overdue_count,
            "tasks_by_status": {status.value: sum(1 for t in tasks if t.status == status) for status in TaskStatus},
        }
        return summary


class TaskManagerView(ttk.Frame):
    """Simple embedded task manager view for the main desktop app."""

    def __init__(self, parent, user_data=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.manager = TaskManager()
        self.new_task_window = None
        self.show_my_tasks = False
        self._bootstrap_demo_data()
        self.create_widgets()
        self.refresh_view()

    def _bootstrap_demo_data(self):
        username = self.user_data.get("username") or self.user_data.get("name") or "Employee"
        role_string = str(self.user_data.get("role") or "").strip().lower()
        employee_users = self._load_employee_users()
        current_user = next((u for u in employee_users if u.name.casefold() == username.casefold()), None)
        if current_user is None:
            current_user = next((u for u in self.manager.users.values() if u.name.casefold() == username.casefold()), None)
        if current_user is None:
            current_user = self.manager.add_user(username, self.user_data.get("email") or f"{username.lower()}@company.com", UserRole.ADMIN if role_string in {"admin", "administrator"} else UserRole.EMPLOYEE)
        elif role_string in {"admin", "administrator"}:
            current_user.role = UserRole.ADMIN

        has_saved_tasks = os.path.exists(self.manager.task_csv_path())

        if not self.manager.departments:
            departments = {
                name: self.manager.add_department(name, current_user.id if index == 0 else None)
                for index, name in enumerate(DEPARTMENT_NAMES)
            }
            hr = departments["Human Resources (HR)"]
            it = departments["Information Technology (IT) / Engineering"]
            self.manager.assign_user_to_department(current_user.id, hr.id, "Member")
            self.manager.assign_user_to_department(current_user.id, it.id, "Member")

            other_user = next((user for user in employee_users if user.id != current_user.id), None)
            if other_user is None:
                other_user = self.manager.add_user("Alice", "alice@company.com", UserRole.EMPLOYEE)
            self.manager.assign_user_to_department(other_user.id, hr.id, "Member")
            self.manager.assign_user_to_department(other_user.id, it.id, "Member")

            if not has_saved_tasks:
                self.manager.create_task(
                    title="Prepare onboarding checklist",
                    description="Finalize onboarding documents for new hires.",
                    department_id=hr.id,
                    created_by=current_user.id,
                    assignee_id=current_user.id,
                    reviewer_id=current_user.id,
                    priority=TaskPriority.HIGH,
                    due_date=datetime.utcnow() + timedelta(days=2),
                )
                self.manager.create_task(
                    title="Review IT service request",
                    description="Check pending equipment request and confirm delivery window.",
                    department_id=it.id,
                    created_by=current_user.id,
                    assignee_id=other_user.id,
                    reviewer_id=current_user.id,
                    priority=TaskPriority.MEDIUM,
                    due_date=datetime.utcnow() + timedelta(days=4),
                )
        self.manager.load_tasks()

    def _resolve_employee_record_path(self):
        candidate_paths = []
        for base_dir in (getattr(config, "HR_DIR", None), getattr(config, "CSV_DIR", None)):
            if base_dir:
                candidate_paths.append(os.path.join(base_dir, "employee record.csv"))
        for candidate in candidate_paths:
            if os.path.exists(candidate):
                return candidate
        # Fall back to the legacy desktop root path if no HR file exists; this keeps
        # the current workflow intact without losing the newer HR-backed employee data.
        return candidate_paths[0] if candidate_paths else os.path.join(getattr(config, "CSV_DIR", "."), "employee record.csv")

    def _load_employee_users(self):
        path = self._resolve_employee_record_path()
        if not os.path.exists(path):
            return []

        self._employee_users_by_record_id = {}
        loaded_users = []
        with open(path, newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                employee_id = (row.get("employee_id") or "").strip()
                name = (row.get("full_name") or "").strip()
                if not name:
                    name = " ".join(
                        part.strip()
                        for part in (row.get("first_name") or "", row.get("middle_name") or "")
                        if part.strip()
                    )
                if not name:
                    continue
                existing = self.manager.users.get(employee_id) if employee_id else None
                if existing is None and not employee_id:
                    existing = next((user for user in self.manager.users.values() if user.name.casefold() == name.casefold()), None)
                if existing is None:
                    email = (row.get("work_email") or row.get("personal_email") or f"{name.lower().replace(' ', '.')}@company.com").strip()
                    existing = User(id=employee_id or str(uuid4()), name=name, email=email, role=UserRole.EMPLOYEE)
                    self.manager.users[existing.id] = existing
                    self.manager.notifications.setdefault(existing.id, [])
                self._employee_users_by_record_id[employee_id] = existing
                loaded_users.append(existing)
        return loaded_users

    def _load_department_employee_users(self, department_name: Optional[str] = None):
        """Load HR-backed employee records for the selected department and keep the
        runtime assignee list in sync with the actual employee CSV, especially for
        Research & Development and similarly named departments."""
        employees = self._load_employee_users()
        if not department_name:
            return employees
        target_name = self._normalize_department_name(department_name)
        return [user for user in employees if self._normalize_department_name(self._employee_record_department_for_user(user)) == target_name]

    def _employee_record_department_for_user(self, user: User) -> str:
        path = self._resolve_employee_record_path()
        if not os.path.exists(path):
            return ""
        with open(path, newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                employee_id = (row.get("employee_id") or "").strip()
                if employee_id and user.id == employee_id:
                    return row.get("department") or ""
        return ""

    def _employee_names_for_department(self, department_name):
        path = self._resolve_employee_record_path()
        if not os.path.exists(path):
            return []

        target_name = self._normalize_department_name(department_name)
        names = []
        with open(path, newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                employee_department = self._normalize_department_name(row.get("department") or "")
                if employee_department != target_name:
                    continue
                name = (row.get("full_name") or "").strip()
                if not name:
                    name = " ".join(
                        part.strip()
                        for part in (row.get("first_name") or "", row.get("middle_name") or "")
                        if part.strip()
                    )
                if name and name not in names:
                    names.append(name)
        return names

    def _employee_options_for_department(self, department_name):
        path = self._resolve_employee_record_path()
        if not os.path.exists(path):
            return []

        target_name = self._normalize_department_name(department_name)
        options = []
        with open(path, newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                employee_department = self._normalize_department_name(row.get("department") or "")
                if employee_department != target_name:
                    continue
                employee_id = (row.get("employee_id") or "").strip()
                first_name = (row.get("first_name") or "").strip()
                middle_name = (row.get("middle_name") or "").strip()
                full_name = (row.get("full_name") or "").strip()
                display_name = " | ".join(
                    value for value in (
                        employee_id,
                        " ".join(value for value in (first_name, middle_name) if value),
                        full_name,
                    ) if value
                )
                if not display_name:
                    continue
                user = getattr(self, "_employee_users_by_record_id", {}).get(employee_id)
                if user is not None:
                    options.append((display_name, user))
                elif employee_id:
                    options.append((display_name, User(id=employee_id, name=full_name or first_name or employee_id, email=f"{employee_id}@company.com", role=UserRole.EMPLOYEE)))
        return options

    def _get_current_user(self) -> Optional[User]:
        username = self.user_data.get("username") or self.user_data.get("name") or "Employee"
        for user in self.manager.users.values():
            if user.name.lower() == username.lower():
                return user
        return None

    def create_widgets(self):
        self.columnconfigure(0, weight=1)

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Task Manager", font=("Helvetica", 14, "bold")).pack(anchor="w")

        self.summary_frame = ttk.Frame(top)
        self.summary_frame.pack(fill="x", pady=(8, 0))

        self.summary_labels = {}
        stats = [
            ("Total", "total"),
            ("In Progress", "in_progress"),
            ("Under Review", "under_review"),
            ("Completed", "completed"),
            ("Overdue", "overdue"),
        ]
        for idx, (label, key) in enumerate(stats):
            box = ttk.Frame(self.summary_frame, padding=8)
            box.grid(row=0, column=idx, padx=6, sticky="ew")
            self.summary_labels[key] = ttk.Label(box, text=f"{label}: 0", font=("Helvetica", 10, "bold"))
            self.summary_labels[key].pack(anchor="center")

        actions = ttk.Frame(self, padding=(10, 5, 10, 10))
        actions.pack(fill="x")
        ttk.Button(actions, text="New Task", command=self.add_task).pack(side="left", padx=4)
        self.my_tasks_button = ttk.Button(actions, text="My Tasks", command=self.toggle_my_tasks)
        self.my_tasks_button.pack(side="left", padx=4)
        ttk.Button(actions, text="Open Chat", command=self.open_chat_window).pack(side="left", padx=4)
        ttk.Button(actions, text="Notifications", command=self.open_notifications_window).pack(side="left", padx=4)
        ttk.Button(actions, text="Mark In Progress", command=self.mark_in_progress).pack(side="left", padx=4)
        ttk.Button(actions, text="Send to Review", command=self.send_to_review).pack(side="left", padx=4)
        ttk.Button(actions, text="Complete", command=self.complete_task).pack(side="left", padx=4)

        self.tree = ttk.Treeview(self, columns=("Title", "Department", "Assignee", "Status", "Priority", "Due"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Department", text="Department")
        self.tree.heading("Assignee", text="Assignee")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Due", text="Due Date")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _visible_tasks(self):
        current_user = self._get_current_user()
        visible = []
        for task in self.manager.tasks.values():
            assignee_ids = task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])
            if self.show_my_tasks and (current_user is None or current_user.id not in assignee_ids):
                continue
            if current_user is None:
                visible.append(task)
                continue
            if self.user_data.get("role") == "Admin":
                visible.append(task)
            else:
                department = self.manager.departments.get(task.department_id)
                if department and current_user.id in department.members:
                    visible.append(task)
                elif current_user.id in (task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])) or task.created_by == current_user.id:
                    visible.append(task)
        return visible

    def toggle_my_tasks(self):
        self.show_my_tasks = not self.show_my_tasks
        self.my_tasks_button.configure(text="All Tasks" if self.show_my_tasks else "My Tasks")
        self.refresh_view()

    def _task_summary_counts(self):
        tasks = self._visible_tasks()
        summary = {
            "total": len(tasks),
            "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            "under_review": sum(1 for t in tasks if t.status == TaskStatus.UNDER_REVIEW),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "overdue": sum(
                1
                for t in tasks
                if t.due_date and t.status not in (TaskStatus.COMPLETED, TaskStatus.CLOSED) and t.due_date < datetime.utcnow()
            ),
        }
        return summary

    def refresh_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        summary = self._task_summary_counts()
        for key, label in {
            "total": "Total",
            "in_progress": "In Progress",
            "under_review": "Under Review",
            "completed": "Completed",
            "overdue": "Overdue",
        }.items():
            self.summary_labels[key].configure(text=f"{label}: {summary.get(key, 0)}")

        for task in sorted(self._visible_tasks(), key=lambda x: (x.due_date or datetime.max, x.title.lower())):
            department = self.manager.departments.get(task.department_id)
            assignee_ids = task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])
            assignee_names = [self.manager.users[user_id].name for user_id in assignee_ids if user_id in self.manager.users]
            assignee = ", ".join(assignee_names) if assignee_names else "Unassigned"
            self.tree.insert("", "end", values=(task.title, department.name if department else "Unknown", assignee, task.status.value, PRIORITY_LABELS.get(task.priority, task.priority.value), task.due_date.strftime("%Y-%m-%d") if task.due_date else "-"))

    def _current_user_id(self) -> Optional[str]:
        current = self._get_current_user()
        return current.id if current else None

    def _default_department_name(self, user: Optional[User]) -> str:
        if user is not None:
            for department in self.manager.departments.values():
                if user.id in department.members:
                    return department.name
        if DEPARTMENT_NAMES:
            return DEPARTMENT_NAMES[0]
        first_department = next(iter(self.manager.departments.values()), None)
        return first_department.name if first_department else ALL_DEPARTMENTS

    @staticmethod
    def _normalize_department_name(value: Optional[str]) -> str:
        text = (value or "").strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", " ", text).strip()
        aliases = {
            "research and development": "research and development",
            "research development": "research and development",
            "research development r d": "research and development",
            "research and development r d": "research and development",
            "r and d": "research and development",
            "r d": "research and development",
            "rnd": "research and development",
            "information technology": "information technology",
            "information technology it": "information technology",
            "it": "information technology",
            "human resources": "human resources",
            "human resources hr": "human resources",
            "sales and business development": "sales and business development",
        }
        if normalized in aliases:
            return aliases[normalized]
        if normalized.endswith(" r d") or normalized.endswith(" rnd"):
            return "research and development"
        if normalized.endswith(" it"):
            return "information technology"
        if normalized.endswith(" hr"):
            return "human resources"
        return normalized

    def _resolve_target_departments(self, department_name: str, manager_id: Optional[str] = None) -> List[Department]:
        """Resolve the department(s) a new task should be created in.

        Selecting "All Departments" returns every department so the task is
        created for each one, instead of silently defaulting to the first
        department (e.g. "Executive / Leadership").
        """
        normalized_input = self._normalize_department_name(department_name)
        if normalized_input == self._normalize_department_name(ALL_DEPARTMENTS):
            return list(self.manager.departments.values())

        department = next(
            (
                d for d in self.manager.departments.values()
                if self._normalize_department_name(d.name) == normalized_input
            ),
            None,
        )
        if department is None:
            department = self.manager.add_department(department_name.strip() or "Operations", manager_id)
        return [department]

    def open_new_task_window(self):
        if self.new_task_window is not None and self.new_task_window.winfo_exists():
            self.new_task_window.focus_set()
            return

        current_user = self._get_current_user()
        if not current_user:
            messagebox.showwarning("Access Denied", "No active user found for this session.")
            return

        self.new_task_window = tk.Toplevel(self)
        self.new_task_window.title("New Task")
        self.new_task_window.state("zoomed")
        self.new_task_window.transient(self.winfo_toplevel())
        self.new_task_window.grab_set()

        ttk.Label(self.new_task_window, text="Create New Task", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=16, pady=(14, 8))

        form = ttk.Frame(self.new_task_window, padding=(16, 0, 16, 16))
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        title_var = tk.StringVar()
        description_var = tk.StringVar()
        department_var = tk.StringVar()
        assignee_var = tk.StringVar()
        due_date_var = tk.StringVar()
        due_time_var = tk.StringVar()
        priority_var = tk.StringVar(value=PRIORITY_LABELS[TaskPriority.MEDIUM])

        department_var.set(self._default_department_name(current_user))

        rows = [
            ("Title", title_var),
            ("Description", description_var),
            ("Department", department_var),
        ]

        for index, (label_text, variable) in enumerate(rows):
            ttk.Label(form, text=f"{label_text}:").grid(row=index, column=0, sticky="w", padx=(0, 10), pady=6)
            entry = ttk.Entry(form, textvariable=variable, width=40)
            entry.grid(row=index, column=1, sticky="ew", pady=6)

        current_department_names = [ALL_DEPARTMENTS] + DEPARTMENT_NAMES
        if current_department_names:
            department_combo = ttk.Combobox(form, textvariable=department_var, values=current_department_names, state="readonly")
            department_combo.grid(row=2, column=1, sticky="ew", pady=6)

        employee_users = self._load_employee_users()
        current_usernames = [u.name for u in employee_users]
        if not current_usernames:
            current_usernames = [u.name for u in self.manager.users.values()]
        ttk.Label(form, text="Assignee:").grid(row=3, column=0, sticky="nw", padx=(0, 10), pady=6)
        assignee_controls = ttk.Frame(form)
        assignee_controls.grid(row=3, column=1, sticky="ew", pady=6)
        assignee_controls.columnconfigure(0, weight=1)
        assignee_combo = ttk.Combobox(assignee_controls, textvariable=assignee_var, state="readonly")
        assignee_combo.grid(row=0, column=0, sticky="ew")

        ttk.Label(form, text="Available Employees:").grid(row=4, column=0, sticky="nw", padx=(0, 10), pady=(0, 6))
        assignee_pool = tk.Listbox(form, height=6, selectmode="extended", exportselection=False)
        assignee_pool.grid(row=4, column=1, sticky="ew", pady=(0, 6))

        added_assignees_listbox = tk.Listbox(form, height=4, exportselection=False)
        added_assignees_listbox.grid(row=5, column=1, sticky="ew", pady=(0, 6))
        ttk.Label(form, text="Added Users:").grid(row=5, column=0, sticky="nw", padx=(0, 10), pady=(0, 6))

        assignee_users = {}
        added_assignees = {}

        def refresh_assignees(_event=None):
            added_assignees.clear()
            added_assignees_listbox.delete(0, tk.END)

            if department_var.get().strip().casefold() == ALL_DEPARTMENTS.casefold():
                assignee_users.clear()
                assignee_users.update({f"{user.id} | {user.name}": user for user in employee_users})
                department_users = employee_users
            else:
                options = self._employee_options_for_department(department_var.get().strip())
                if options:
                    assignee_users.clear()
                    assignee_users.update({display_name: user for display_name, user in options})
                    department_users = [user for _display_name, user in options]
                else:
                    department_users = [
                        user
                        for user in self.manager.users.values()
                        if any(
                            user.id in department.members
                            for department in self.manager.departments.values()
                            if self._normalize_department_name(department.name) == self._normalize_department_name(department_var.get().strip())
                        )
                    ]
                    assignee_users.clear()
                    assignee_users.update({user.name: user for user in department_users})

            assignee_pool.delete(0, tk.END)
            for user in sorted(department_users, key=lambda item: item.name.lower()):
                assignee_pool.insert(tk.END, f"{user.id} | {user.name}")

            assignee_combo["values"] = list(assignee_users)
            if assignee_combo["values"]:
                first_user = next(iter(assignee_users.values()), None)
                assignee_var.set(next((key for key, value in assignee_users.items() if value.id == first_user.id), assignee_combo["values"][0]))
                if len(department_users) == 1:
                    default_user = department_users[0]
                    added_assignees[default_user.id] = default_user
                    added_assignees_listbox.insert(tk.END, default_user.name)
                    assignee_var.set(next((key for key, value in assignee_users.items() if value.id == default_user.id), assignee_combo["values"][0]))
            else:
                assignee_var.set("")

        def add_assignee():
            selected_indexes = list(assignee_pool.curselection())
            if selected_indexes:
                for index in selected_indexes:
                    label = assignee_pool.get(index)
                    assignee = assignee_users.get(label) or next((user for user in assignee_users.values() if user.name == label.split(" | ")[-1]), None)
                    if assignee is None or assignee.id in added_assignees:
                        continue
                    added_assignees[assignee.id] = assignee
                    added_assignees_listbox.insert(tk.END, assignee.name)
                return

            assignee = assignee_users.get(assignee_var.get().strip())
            if assignee is None:
                messagebox.showwarning("Assignee Required", "Select a user before clicking Add.")
                return
            if assignee.id in added_assignees:
                return
            added_assignees[assignee.id] = assignee
            added_assignees_listbox.insert(tk.END, assignee.name)

        def add_all_department_users():
            if not assignee_users:
                messagebox.showwarning(
                    "No Department Users",
                    "No users are available for the selected department.",
                    parent=self.new_task_window,
                )
                return
            for assignee in assignee_users.values():
                if assignee.id in added_assignees:
                    continue
                added_assignees[assignee.id] = assignee
                added_assignees_listbox.insert(tk.END, assignee.name)

        def remove_selected_user():
            selected_indices = list(added_assignees_listbox.curselection())
            if not selected_indices:
                messagebox.showwarning(
                    "Select User",
                    "Select a user from the Added Users list first.",
                    parent=self.new_task_window,
                )
                return
            selected_names = {
                added_assignees_listbox.get(index)
                for index in selected_indices
            }
            for user_id, user in list(added_assignees.items()):
                if user.name in selected_names:
                    added_assignees.pop(user_id)
            for index in reversed(selected_indices):
                added_assignees_listbox.delete(index)

        def remove_all_department_users():
            department_user_ids = {user.id for user in assignee_users.values()}
            removed_indices = []
            for index, (user_id, user) in enumerate(added_assignees.items()):
                if user_id in department_user_ids:
                    removed_indices.append(index)
            for user_id in department_user_ids:
                added_assignees.pop(user_id, None)
            for index in reversed(removed_indices):
                added_assignees_listbox.delete(index)

        ttk.Button(assignee_controls, text="Add", command=add_assignee).grid(row=0, column=1, padx=(6, 0))
        user_management_buttons = ttk.Frame(form)
        user_management_buttons.grid(row=5, column=1, sticky="w", pady=(0, 6))
        ttk.Button(
            user_management_buttons,
            text="+ All Department Users",
            command=add_all_department_users,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            user_management_buttons,
            text="Remove Selected User",
            command=remove_selected_user,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            user_management_buttons,
            text="- All Selected Department Users",
            command=remove_all_department_users,
        ).pack(side="left")

        department_combo.bind("<<ComboboxSelected>>", refresh_assignees)

        selectable_dates = [(datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(366)]
        ttk.Label(form, text="Due Date:").grid(row=6, column=0, sticky="w", padx=(0, 10), pady=6)
        due_date_combo = ttk.Combobox(form, textvariable=due_date_var, values=selectable_dates, state="readonly")
        due_date_combo.grid(row=6, column=1, sticky="ew", pady=6)

        selectable_times = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 30)]
        ttk.Label(form, text="Due Time:").grid(row=7, column=0, sticky="w", padx=(0, 10), pady=6)
        due_time_combo = ttk.Combobox(form, textvariable=due_time_var, values=selectable_times, state="readonly")
        due_time_combo.grid(row=7, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Priority:").grid(row=8, column=0, sticky="w", padx=(0, 10), pady=6)
        priority_combo = ttk.Combobox(form, textvariable=priority_var, values=PRIORITY_CHOICES, state="readonly")
        priority_combo.grid(row=8, column=1, sticky="ew", pady=6)

        def save_task():
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("Validation", "Task title is required.")
                return

            description = description_var.get().strip() or "No description provided."
            department_name = department_var.get().strip() or "Operations"
            target_departments = self._resolve_target_departments(department_name, current_user.id)

            if not target_departments:
                messagebox.showwarning("Validation", "No departments are available to create the task.")
                return

            due_raw = due_date_var.get().strip()
            due_time_raw = due_time_var.get().strip()
            if not due_raw or not due_time_raw:
                messagebox.showwarning("Validation", "Due date and due time are required.")
                return
            due_date = datetime.strptime(f"{due_raw} {due_time_raw}", "%Y-%m-%d %H:%M")

            assignees = list(added_assignees.values())
            for department in target_departments:
                for assignee in assignees:
                    self.manager.assign_user_to_department(assignee.id, department.id, "Member")
                task = self.manager.create_task(
                    title=title,
                    description=description,
                    department_id=department.id,
                    created_by=current_user.id,
                    assignee_ids=[assignee.id for assignee in assignees],
                    priority=PRIORITY_BY_LABEL.get(priority_var.get().strip(), TaskPriority.MEDIUM),
                    due_date=due_date,
                )
                if task.assignee_id is not None:
                    self.manager.accept_task(task.id, task.assignee_id)
            self.refresh_view()
            self.new_task_window.destroy()

        buttons = ttk.Frame(self.new_task_window)
        buttons.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(buttons, text="Create Task", command=save_task).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text="Cancel", command=self.new_task_window.destroy).pack(side="right")

        self.new_task_window.protocol("WM_DELETE_WINDOW", self.new_task_window.destroy)
        self.new_task_window.bind("<Escape>", lambda event: self.new_task_window.destroy())

        department_var.set(self._default_department_name(current_user))
        refresh_assignees()
        due_date_var.set(selectable_dates[0])
        due_time_var.set(selectable_times[18])
        priority_var.set(PRIORITY_LABELS[TaskPriority.MEDIUM])

        self.new_task_window.focus_set()

    def _accessible_task_chats(self, current_user):
        tasks = list(self.manager.tasks.values())
        if current_user.role == UserRole.ADMIN:
            return sorted(tasks, key=lambda task: (task.title.lower(), task.created_at))
        return [
            task for task in tasks
            if task.created_by == current_user.id
            or current_user.id in (task.assignee_ids or ([task.assignee_id] if task.assignee_id else []))
            or any(
                current_user.id in department.members
                for department in self.manager.departments.values()
                if department.id == task.department_id
            )
        ]

    def open_chat_window(self):
        current_user = self._get_current_user()
        if current_user is None:
            messagebox.showwarning("Access Denied", "No active user found for this session.")
            return

        task_options = self._accessible_task_chats(current_user)
        if not task_options:
            messagebox.showwarning("No Chats", "You are not assigned to any task chat yet.")
            return

        selected_task = self._selected_task()
        if selected_task is None and current_user.role != UserRole.ADMIN:
            selected_task = task_options[0]

        def open_task_chat(task):
            try:
                task_group = self.manager.get_or_create_task_group(task.id)
            except ValueError as exc:
                messagebox.showwarning("Validation", str(exc))
                return

            allowed_contacts = [
                self.manager.users[user_id]
                for user_id in task_group["participants"]
                if user_id in self.manager.users and user_id != current_user.id
            ]
            if current_user.role == UserRole.ADMIN and not allowed_contacts:
                allowed_contacts = [user for user in self.manager.users.values() if user.id != current_user.id]

            chat_window = tk.Toplevel(self)
            chat_window.title(f"Task Chat - {task.title}")
            chat_window.geometry("820x700")
            chat_window.configure(bg="#e5ddd5")
            chat_window.transient(self.winfo_toplevel())
            chat_window.grab_set()

            header = tk.Frame(chat_window, bg="#075e54", height=86)
            header.pack(fill="x")
            header.pack_propagate(False)

            ttk.Label(header, text=f"Task Group: {task.title}", background="#075e54", foreground="white", font=("Helvetica", 13, "bold")).pack(anchor="w", padx=16, pady=(12, 0))
            ttk.Label(header, text=f"Participants: {len(task_group['participants'])}   •   Department: {self.manager.departments.get(task.department_id).name if self.manager.departments.get(task.department_id) else 'Unknown'}", background="#075e54", foreground="#dfeae7", font=("Helvetica", 9)).pack(anchor="w", padx=16, pady=(4, 0))

            selected_attachment = {"message": None}

            def select_attachment(chat_message):
                selected_attachment["message"] = chat_message
                attachment_status_var.set(f"Selected: {chat_message.get('attachment') or 'file'}")
                open_attachment_button.configure(state="normal")
                download_attachment_button.configure(state="normal")

            def refresh_chat():
                selected_attachment["message"] = None
                attachment_status_var.set("No file selected")
                open_attachment_button.configure(state="disabled")
                download_attachment_button.configure(state="disabled")
                messages_text.configure(state="normal")
                messages_text.delete("1.0", tk.END)
                for chat_message in self.manager.get_group_chat_messages(task_group["id"]):
                    sender = self.manager.users.get(chat_message["sender_id"], current_user)
                    if chat_message.get("message"):
                        label = chat_message["message"]
                    elif chat_message.get("attachment"):
                        label = f"[File] {os.path.basename(chat_message['attachment'])}"
                    elif chat_message.get("call_type"):
                        label = f"[Call] {chat_message['call_type']}"
                    else:
                        label = f"[Reaction] {chat_message.get('reaction') or '👍'}"
                    tag = "me" if sender.id == current_user.id else "other"
                    messages_text.insert(tk.END, f"{sender.name}\n", "meta")
                    message_start = messages_text.index(tk.END)
                    messages_text.insert(tk.END, f"{label}\n\n", tag)
                    if chat_message.get("attachment"):
                        attachment_tag = f"attachment_{chat_message['id']}"
                        messages_text.tag_configure(attachment_tag, foreground="#075e54", underline=True)
                        messages_text.tag_add(attachment_tag, message_start, f"{message_start} lineend")
                        messages_text.tag_bind(attachment_tag, "<Button-1>", lambda event, item=chat_message: select_attachment(item))
                        messages_text.tag_bind(attachment_tag, "<Double-Button-1>", lambda event, item=chat_message: self._open_chat_attachment(item, chat_window))
                messages_text.configure(state="disabled")
                messages_text.see(tk.END)

            action_frame = tk.Frame(chat_window, bg="#f1f1f1")
            action_frame.pack(fill="x", padx=10, pady=(8, 4))
            ttk.Button(action_frame, text="Upload File", command=lambda: self._handle_chat_action(current_user, task, "file", refresh_chat)).pack(side="left", padx=(0, 6))
            open_attachment_button = ttk.Button(action_frame, text="Open Selected", state="disabled", command=lambda: self._open_chat_attachment(selected_attachment["message"], chat_window))
            open_attachment_button.pack(side="left", padx=(0, 6))
            download_attachment_button = ttk.Button(action_frame, text="Download Selected", state="disabled", command=lambda: self._download_chat_attachment(selected_attachment["message"], chat_window))
            download_attachment_button.pack(side="left", padx=(0, 6))
            ttk.Button(action_frame, text="React 👍", command=lambda: self._handle_chat_action(current_user, task, "reaction", refresh_chat)).pack(side="left", padx=(0, 6))
            ttk.Button(action_frame, text="Audio Call", command=lambda: self._handle_chat_action(current_user, task, "call", refresh_chat)).pack(side="left", padx=(0, 6))
            ttk.Button(action_frame, text="Refresh", command=lambda: refresh_chat()).pack(side="left", padx=(0, 6))
            attachment_status_var = tk.StringVar(value="No file selected")
            ttk.Label(action_frame, textvariable=attachment_status_var, background="#f1f1f1", foreground="#5a5a5a").pack(side="right")

            chat_body = tk.Frame(chat_window, bg="#e5ddd5")
            chat_body.pack(fill="both", expand=True)

            messages_scroll = ttk.Scrollbar(chat_body, orient="vertical")
            messages_scroll.pack(side="right", fill="y")

            messages_text = tk.Text(
                chat_body,
                wrap="word",
                state="disabled",
                bg="#e5ddd5",
                fg="#111111",
                relief="flat",
                highlightthickness=0,
                padx=12,
                pady=12,
                yscrollcommand=messages_scroll.set,
                font=("Helvetica", 10),
            )
            messages_text.pack(side="left", fill="both", expand=True)
            messages_text.tag_configure("me", justify="right", foreground="#111111", background="#dcf8c6", lmargin1=90, rmargin=10, spacing1=6, spacing3=6)
            messages_text.tag_configure("other", justify="left", foreground="#111111", background="#ffffff", lmargin1=10, rmargin=90, spacing1=6, spacing3=6)
            messages_text.tag_configure("meta", foreground="#5a5a5a", font=("Helvetica", 8))
            messages_scroll.configure(command=messages_text.yview)

            input_panel = tk.Frame(chat_window, bg="#f3f4f6")
            input_panel.pack(fill="x", padx=0, pady=0)

            mention_frame = tk.Frame(input_panel, bg="#f3f4f6", padx=12, pady=(10))
            mention_frame.pack(fill="x")
            ttk.Label(mention_frame, text="Mention:", background="#f3f4f6").pack(side="left")
            mention_values = [user.name for user in sorted(allowed_contacts, key=lambda user: user.name.lower())]
            mention_var = tk.StringVar()
            mention_combo = ttk.Combobox(mention_frame, textvariable=mention_var, values=mention_values, state="readonly", width=30)
            mention_combo.pack(side="left", padx=(8, 0))
            if mention_values:
                mention_combo.current(0)

            input_frame = tk.Frame(input_panel, bg="#f3f4f6", padx=12, pady=(0, 10))
            input_frame.pack(fill="x")
            message_var = tk.StringVar()
            message_entry = ttk.Entry(input_frame, textvariable=message_var, width=64)
            message_entry.pack(side="left", fill="x", expand=True)
            message_entry.focus_set()

            def add_mention_to_message():
                if mention_combo.get().strip():
                    current_text = message_var.get().strip()
                    mention_text = f"@{mention_combo.get().strip()}"
                    if current_text:
                        message_var.set(f"{current_text} {mention_text}")
                    else:
                        message_var.set(mention_text)
                    message_entry.focus_set()
                    mention_combo.set("")

            ttk.Button(input_frame, text="Add Mention", command=add_mention_to_message).pack(side="left", padx=(8, 0))
            send_button = tk.Button(
                input_frame,
                text="➤",
                command=lambda: send_message(),
                bg="#128c7e",
                fg="white",
                activebackground="#075e54",
                activeforeground="white",
                relief="flat",
                bd=0,
                width=3,
                font=("Helvetica", 12, "bold"),
                cursor="hand2",
            )
            send_button.pack(side="right", padx=(8, 0))

            def send_message():
                text = message_var.get().strip()
                if not text:
                    messagebox.showwarning("Validation", "Type a message before sending.", parent=chat_window)
                    return
                try:
                    self.manager.send_group_message(current_user.id, task_group["id"], text)
                    message_var.set("")
                    mention_combo.set("")
                    refresh_chat()
                    message_entry.focus_set()
                except ValueError as exc:
                    messagebox.showwarning("Validation", str(exc), parent=chat_window)
                except PermissionError as exc:
                    messagebox.showwarning("Access Denied", str(exc), parent=chat_window)

            message_entry.bind("<Return>", lambda event: send_message())

            refresh_chat()
            chat_window.protocol("WM_DELETE_WINDOW", chat_window.destroy)

        if selected_task is not None:
            if current_user.role != UserRole.ADMIN and current_user.id not in (selected_task.assignee_ids or ([selected_task.assignee_id] if selected_task.assignee_id else [])) and selected_task.created_by != current_user.id:
                messagebox.showwarning("Access Denied", "You do not have access to this task chat group.")
                return
            open_task_chat(selected_task)
            return

        if current_user.role == UserRole.ADMIN:
            selector = tk.Toplevel(self)
            selector.title("Open Task Chat")
            selector.geometry("420x420")
            selector.transient(self.winfo_toplevel())
            selector.grab_set()

            ttk.Label(selector, text="Select a task chat to open", font=("Helvetica", 11, "bold")).pack(anchor="w", padx=12, pady=(12, 8))
            task_list = tk.Listbox(selector, height=18, width=52, exportselection=False)
            task_list.pack(fill="both", expand=True, padx=12, pady=(0, 10))
            for task in task_options:
                assignee_ids = task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])
                assignee_names = [
                    self.manager.users[user_id].name
                    for user_id in assignee_ids
                    if user_id in self.manager.users
                ]
                assignees = ", ".join(assignee_names) or "Unassigned"
                status = task.status.value.replace("_", " ").title()
                task_list.insert(tk.END, f"{task.title}  |  {status}  |  {assignees}")

            def open_selected_task_chat():
                selection = task_list.curselection()
                if not selection:
                    messagebox.showwarning("Selection Required", "Select a task first.", parent=selector)
                    return
                task = task_options[selection[0]]
                selector.destroy()
                open_task_chat(task)

            ttk.Button(selector, text="Open Selected Chat", command=open_selected_task_chat).pack(pady=(0, 12))
            return

        open_task_chat(task_options[0])

    def _handle_chat_action(self, current_user, selected_task, action_type: str, refresh_chat=None):
        if selected_task is None:
            messagebox.showwarning("Task Required", "Please select a task before using the task chat actions.")
            return
        if action_type == "file":
            file_path = filedialog.askopenfilename(title="Choose a file to upload to task chat")
            if not file_path:
                return
            try:
                task_group = self.manager.get_or_create_task_group(selected_task.id)
                attachment_dir = os.path.join(config.CSV_DIR, "chat_attachments")
                os.makedirs(attachment_dir, exist_ok=True)
                stored_path = os.path.join(attachment_dir, f"{uuid4().hex}_{os.path.basename(file_path)}")
                shutil.copy2(file_path, stored_path)
                self.manager.send_group_message(
                    current_user.id,
                    task_group["id"],
                    "",
                    attachment=os.path.basename(file_path),
                    attachment_path=stored_path,
                )
                if refresh_chat:
                    refresh_chat()
                messagebox.showinfo("Upload File", f"File uploaded: {os.path.basename(file_path)}")
            except (OSError, ValueError, PermissionError) as exc:
                messagebox.showwarning("Validation", str(exc))
        elif action_type == "reaction":
            try:
                task_group = self.manager.get_or_create_task_group(selected_task.id)
                self.manager.send_group_message(current_user.id, task_group["id"], "", reaction="👍")
                if refresh_chat:
                    refresh_chat()
                messagebox.showinfo("Reaction", "Reaction sent: 👍")
            except (ValueError, PermissionError) as exc:
                messagebox.showwarning("Validation", str(exc))
        elif action_type == "call":
            try:
                task_group = self.manager.get_or_create_task_group(selected_task.id)
                self.manager.send_group_message(current_user.id, task_group["id"], "", call_type="audio")
                if refresh_chat:
                    refresh_chat()
                messagebox.showinfo("Audio Call", "Audio call started and shared in the task group.")
            except (ValueError, PermissionError) as exc:
                messagebox.showwarning("Validation", str(exc))

    @staticmethod
    def _chat_attachment_path(chat_message):
        if not chat_message:
            return None
        stored_path = chat_message.get("attachment_path")
        if stored_path and os.path.isfile(stored_path):
            return stored_path
        legacy_path = chat_message.get("attachment")
        return legacy_path if legacy_path and os.path.isfile(legacy_path) else None

    def _open_chat_attachment(self, chat_message, parent=None):
        path = self._chat_attachment_path(chat_message)
        if not path or not os.path.isfile(path):
            messagebox.showwarning("File Not Available", "This attachment is no longer available.", parent=parent)
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(path)
            else:
                webbrowser.open(os.path.abspath(path))
        except OSError as exc:
            messagebox.showerror("Open Failed", f"Could not open the attachment:\n{exc}", parent=parent)

    def _download_chat_attachment(self, chat_message, parent=None):
        path = self._chat_attachment_path(chat_message)
        if not path or not os.path.isfile(path):
            messagebox.showwarning("File Not Available", "This attachment is no longer available.", parent=parent)
            return
        destination = filedialog.asksaveasfilename(
            parent=parent,
            title="Download chat attachment",
            initialfile=os.path.basename(chat_message.get("attachment") or path),
        )
        if not destination:
            return
        try:
            shutil.copy2(path, destination)
            messagebox.showinfo("Download Complete", f"Attachment saved to:\n{destination}", parent=parent)
        except OSError as exc:
            messagebox.showerror("Download Failed", f"Could not save the attachment:\n{exc}", parent=parent)

    def _create_group_chat_window(self, current_user, contact_var, refresh_chat):
        allowed_contacts = self.manager.available_chat_users(current_user.id)
        if current_user.role == UserRole.ADMIN:
            allowed_contacts = [user for user in self.manager.users.values() if user.id != current_user.id]
        if not allowed_contacts:
            messagebox.showwarning("No Access", "No assigned contacts are available to form a group.")
            return

        group_window = tk.Toplevel(self)
        group_window.title("Create Group Chat")
        group_window.geometry("350x350")
        group_window.transient(self.winfo_toplevel())
        group_window.grab_set()

        ttk.Label(group_window, text="Group Name").pack(anchor="w", padx=12, pady=(12, 6))
        group_name_var = tk.StringVar(value=f"{current_user.name}'s Team")
        ttk.Entry(group_window, textvariable=group_name_var).pack(fill="x", padx=12)

        ttk.Label(group_window, text="Select members").pack(anchor="w", padx=12, pady=(10, 6))
        members_list = tk.Listbox(group_window, selectmode="extended", height=12, width=40)
        members_list.pack(fill="both", expand=True, padx=12)
        for user in allowed_contacts:
            members_list.insert(tk.END, user.name)

        def create_group():
            selected_names = [members_list.get(index) for index in members_list.curselection()]
            if not selected_names:
                messagebox.showwarning("Validation", "Choose at least one team member for the group.")
                return
            participants = [user.id for user in allowed_contacts if user.name in selected_names]
            group = self.manager.create_group_chat(current_user.id, participants, title=group_name_var.get())
            contact_var.set(group["name"])
            refresh_chat()
            group_window.destroy()

        ttk.Button(group_window, text="Create Chat Group", command=create_group).pack(pady=(8, 12))

    def add_task(self):
        self.open_new_task_window()

    def add_task(self):
        self.open_new_task_window()

    def open_notifications_window(self):
        current_user = self._get_current_user()
        if current_user is None:
            messagebox.showwarning("Access Denied", "No active user found.")
            return

        window = tk.Toplevel(self)
        window.title(f"Notifications - {current_user.name}")
        window.geometry("520x420")
        window.transient(self.winfo_toplevel())
        window.grab_set()

        ttk.Label(window, text="Notifications & Email Alerts", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 8))
        listbox = tk.Listbox(window, width=80, height=18, exportselection=False)
        listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        notifications = self.manager.notifications_for_user(current_user.id)
        email_notifications = self.manager.email_notifications_for_user(current_user.id)
        all_items = []
        for item in notifications:
            all_items.append(f"[In-App] {item.get('type', 'notification').title()}: {item.get('message', '')}")
        for item in email_notifications:
            all_items.append(f"[Mail] {item.get('subject', 'Email')}: {item.get('body', '')}")
        if not all_items:
            listbox.insert(tk.END, "No notifications available.")
        else:
            for entry in all_items:
                listbox.insert(tk.END, entry)

    def _selected_task(self) -> Optional[Task]:
        selection = self.tree.selection()
        if not selection:
            return None
        values = self.tree.item(selection[0], "values")
        for task in self.manager.tasks.values():
            if task.title == values[0]:
                return task
        return None

    def mark_in_progress(self):
        task = self._selected_task()
        if not task:
            messagebox.showwarning("Selection Required", "Please select a task first.")
            return
        current_user_id = self._current_user_id()
        if current_user_id is None or current_user_id not in (task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])):
            messagebox.showwarning("Access Denied", "Only an assignee can move a task to in progress.")
            return
        self.manager.accept_task(task.id, current_user_id)
        self.refresh_view()

    def send_to_review(self):
        task = self._selected_task()
        if not task:
            messagebox.showwarning("Selection Required", "Please select a task first.")
            return
        current_user_id = self._current_user_id()
        if current_user_id is None or current_user_id not in (task.assignee_ids or ([task.assignee_id] if task.assignee_id else [])):
            messagebox.showwarning("Access Denied", "Only an assignee can send the task for review.")
            return
        self.manager.submit_for_review(task.id, current_user_id)
        self.refresh_view()

    def complete_task(self):
        task = self._selected_task()
        if not task:
            messagebox.showwarning("Selection Required", "Please select a task first.")
            return
        current_user_id = self._current_user_id()
        if current_user_id is None:
            messagebox.showwarning("Access Denied", "No active user found.")
            return
        if task.reviewer_id == current_user_id or self.user_data.get("role") == "Admin":
            self.manager.complete_task(task.id, current_user_id)
            self.refresh_view()
            return
        messagebox.showwarning("Access Denied", "Only the reviewer or admin can complete this task.")
