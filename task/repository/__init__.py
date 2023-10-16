import uuid

from task.models import Task


class TaskRepository:
    @staticmethod
    def create(name, description, user_id, project_uid, file_ids, meta_data={}) -> Task:
        """
        Creates a new task.
        """
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
    def create_bulk(tasks: list) -> list:
        """
        Creates bulk tasks.
        """
        Task.objects.bulk_create(tasks)

    @staticmethod
    def delete_bulk(task_uids: list) -> None:
        """
        Deletes bulk tasks.
        """
        Task.objects.filter(uid__in=task_uids).delete()
