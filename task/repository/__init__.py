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
        Task.objects.filter(uid__in=task_uids).update(is_deleted=True)

    @staticmethod
    def mark_complete(task_uid: str) -> None:
        """
        Marks task as complete.
        """
        Task.objects.filter(uid=task_uid).update(is_completed=True)

    @staticmethod
    def update_task(
        task_uid: str, name: str, description: str, meta_data: dict
    ) -> None:
        """
        Updates task.
        """
        Task.objects.filter(uid=task_uid).update(
            name=name, description=description, meta_data=meta_data
        )

    @staticmethod
    def undelete(task_uid: str) -> None:
        """
        Undeletes task.
        """
        Task.objects.filter(uid=task_uid).update(is_deleted=False)

    @staticmethod
    def update_bulk(tasks: list) -> None:
        for task in tasks:
            Task.objects.filter(uid=task["uid"]).update(
                name=task["name"],
                description=task["description"],
                meta_data=task["meta_data"],
            )
