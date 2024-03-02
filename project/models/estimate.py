from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .base import ProjectBaseModel


class Estimate(ProjectBaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(verbose_name="Estimate Description", blank=True)

    class Meta:
        unique_together = ["name", "project"]
        verbose_name = "Estimate"
        verbose_name_plural = "Estimates"
        db_table = "estimate"
        ordering = ("name",)


class EstimatePoint(ProjectBaseModel):
    estimate = models.ForeignKey(
        Estimate,
        on_delete=models.CASCADE,
        related_name="points",
    )
    key = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(7)]
    )
    description = models.TextField(blank=True)
    value = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Estimate Point"
        verbose_name_plural = "Estimate Points"
        db_table = "estimate_point"
        ordering = ("value",)
