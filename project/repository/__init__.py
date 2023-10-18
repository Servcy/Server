from project.models import Project


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
            },
        )

    @staticmethod
    def create_bulk(projects: list) -> list:
        """Creates bulk projects."""
        return Project.objects.bulk_create(projects)
