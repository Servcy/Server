from project.models import Project


class ProjectRepository:
    def __init__(self):
        pass

    def create(self, **kwargs) -> Project:
        """Creates a new project."""
        return Project.objects.create(
            name=kwargs["name"],
            description=kwargs["description"],
            uid=kwargs["uid"],
            user_id=kwargs["user_id"],
            user_integration_id=kwargs["user_integration_id"],
        )

    def create_bulk(self, projects: list) -> list:
        """Creates bulk projects."""
        return Project.objects.bulk_create(projects)
