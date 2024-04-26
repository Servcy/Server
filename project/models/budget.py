from django.conf import settings
from django.db import models

from .base import ProjectBaseModel


class ProjectBudget(ProjectBaseModel):
    """
    ProjectBudget (model): To store all the budget of the project
    """

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    class Meta:
        verbose_name = "Project Budget"
        verbose_name_plural = "Project Budgets"
        db_table = "project_budget"
        ordering = ("-created_at",)


class ProjectMemberRate(ProjectBaseModel):
    """
    ProjectMemberRate (model): To store all the rates of the project members
    """

    project_member = models.ForeignKey(
        "project.ProjectMember",
        on_delete=models.CASCADE,
        related_name="project_member_rate",
    )
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    per_hour_or_per_project = models.BooleanField(
        default=True, help_text="Is rate per hour or per project, default is per hour"
    )

    class Meta:
        verbose_name = "Project Member Rate"
        verbose_name_plural = "Project Member Rates"
        db_table = "project_member_rate"
        ordering = ("-created_at",)


class ProjectExpense(ProjectBaseModel):
    """
    ProjectExpense (model): To store all the expenses of the project
    """

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    description = models.TextField(blank=True, null=True)
    recurring = models.CharField(
        max_length=30,
        choices=(
            ("yearly", "Yearly"),
            ("monthly", "Monthly"),
            ("weekly", "Weekly"),
            ("daily", "Daily"),
        ),
        verbose_name="Recurrence Type",
        default="monthly",
    )

    class Meta:
        verbose_name = "Project Expense"
        verbose_name_plural = "Project Expenses"
        db_table = "project_expense"
        ordering = ("-created_at",)
