import uuid

from django.db import transaction

from task.models import Task


class TaskRepository:
    @staticmethod
    def create(name, description, user_id, project_uid, file_ids, meta_data={}):
        task = Task(
            name=name,
            description=description,
            uid=uuid.uuid4().hex,
            user_id=user_id,
            project_uid=project_uid,
            file_ids=file_ids,
            meta_data=meta_data,
        )
        task.save()
        return task

    @staticmethod
    @transaction.atomic
    def create_bulk(tasks: list):
        Task.objects.bulk_create(tasks)

    @staticmethod
    @transaction.atomic
    def delete_bulk(task_uids: list):
        Task.objects.filter(uid__in=task_uids, is_deleted=False).update(is_deleted=True)

    @staticmethod
    def mark_complete(task_uid: str):
        Task.objects.filter(uid=task_uid, is_completed=False).update(is_completed=True)

    @staticmethod
    def update_task(task_uid: str, name: str, description: str, meta_data: dict):
        Task.objects.filter(uid=task_uid).update(
            name=name, description=description, meta_data=meta_data
        )

    @staticmethod
    def undelete(task_uid: str):
        Task.objects.filter(uid=task_uid, is_deleted=True).update(is_deleted=False)

    @staticmethod
    @transaction.atomic
    def update_bulk(task_data: list):
        task_uids = [task["uid"] for task in task_data]
        tasks_to_update = list(Task.objects.filter(uid__in=task_uids))
        uid_to_data = {task["uid"]: task for task in task_data}

        # Update the task objects based on the dictionaries
        for task in tasks_to_update:
            data = uid_to_data[task.uid]
            task.name = data["name"]
            task.description = data["description"]
            task.meta_data = data["meta_data"]

        # Now use bulk_update
        fields = ["name", "description", "meta_data"]
        Task.objects.bulk_update(tasks_to_update, fields)
