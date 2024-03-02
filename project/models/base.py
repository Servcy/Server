from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel


class ProjectBaseModel(CreatorUpdaterModel, TimeStampedModel):
    project = models.ForeignKey(
        "project.Project", on_delete=models.CASCADE, related_name="project_%(class)s"
    )
    workspace = models.ForeignKey(
        "iam.Workspace", models.CASCADE, related_name="workspace_%(class)s"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.project:
            self.workspace = self.project.workspace
        super(ProjectBaseModel, self).save(*args, **kwargs)
