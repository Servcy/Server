from project.models import Project
from django.db import transaction


class ProjectRepository:
    @staticmethod
    def create(**kwargs) -> Project:
        """Creates a new project."""
        return Project.objects.get_or_create(
            uid=kwargs["uid"],
            user_id=kwargs["user_id"],
            user_integration_id=kwargs["user_integration_id"],
            defaults={
                "name": kwargs["name"],
                "description": kwargs["description"],
                "meta_data": kwargs["meta_data"],
            },
        )

    @staticmethod
    def create_bulk(projects: list) -> list:
        """Creates bulk projects."""
        return Project.objects.bulk_create(projects)

    @staticmethod
    @transaction.atomic
    def delete_bulk(project_uids: list):
        Project.objects.filter(uid__in=project_uids, is_deleted=False).update(
            is_deleted=True
        )

    @staticmethod
    def undelete(project_uid: str):
        Project.objects.filter(uid=project_uid, is_deleted=True).update(
            is_deleted=False
        )

    @staticmethod
    @transaction.atomic
    def update_bulk(project_data: list):
        project_uids = [project["uid"] for project in project_data]
        projects_to_update = list(Project.objects.filter(uid__in=project_uids))
        uid_to_data = {project["uid"]: project for project in project_data}

        # Update the project objects based on the dictionaries
        for project in projects_to_update:
            data = uid_to_data[project.uid]
            project.name = data["name"]
            project.description = data["description"]
            project.meta_data = data["meta_data"]

        # Now use bulk_update
        fields = ["name", "description", "meta_data"]
        Project.objects.bulk_update(projects_to_update, fields)
