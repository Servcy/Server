from django.db import transaction

from task.models import Task


class TaskRepository:
    @staticmethod
    def create(**kwargs):
        task = Task.objects.get_or_create(
            uid=kwargs["uid"],
            user_id=kwargs["user_id"],
            defaults={
                "name": kwargs["name"],
                "description": kwargs["description"],
                "meta_data": kwargs["meta_data"],
                "project_uid": kwargs["project_uid"],
            },
        )
        return task

    @staticmethod
    def update(filters: dict, updates: dict):
        """Updates a task."""
        Task.objects.filter(**filters).update(**updates)

    @staticmethod
    @transaction.atomic
    def delete_bulk(task_uids: list, user_id: int):
        Task.objects.filter(
            uid__in=task_uids, is_deleted=False, user_id=user_id
        ).update(is_deleted=True)

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
