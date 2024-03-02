from django.db import models

from project.models.base import ProjectBaseModel


class State(ProjectBaseModel):
    name = models.CharField(max_length=255, verbose_name="State Name")
    description = models.TextField(verbose_name="State Description", blank=True)
    color = models.CharField(max_length=255, verbose_name="State Color")
    group = models.CharField(
        choices=(
            ("backlog", "Backlog"),
            ("unstarted", "Unstarted"),
            ("started", "Started"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ),
        default="backlog",
        max_length=20,
    )

    class Meta:
        unique_together = ["name", "project"]
        verbose_name = "State"
        verbose_name_plural = "States"
        db_table = "state"
