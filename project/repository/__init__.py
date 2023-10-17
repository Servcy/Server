from django.db import IntegrityError

from project.models import Project


class ProjectRepository:
    @staticmethod
    def create(**kwargs) -> Project:
        """Creates a new project."""
        try:
            return Project.objects.update_or_create(
                name=kwargs["name"],
                description=kwargs["description"],
                uid=kwargs["uid"],
                user_id=kwargs["user_id"],
                user_integration_id=kwargs["user_integration_id"],
            )
        except IntegrityError:
            return Project.objects.get(uid=kwargs["uid"])

    @staticmethod
    def create_bulk(projects: list) -> list:
        """Creates bulk projects."""
        return Project.objects.bulk_create(projects)
