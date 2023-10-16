from project.models import Project


class ProjectRepository:
    def __init__(self):
        pass

    def create(self, **kwargs) -> Project:
        """Creates a new project."""
        return Project.objects.create(**kwargs)

    def create_bulk(self, projects: list) -> list:
        """Creates bulk projects."""
        return Project.objects.bulk_create(projects)
