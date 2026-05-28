import uuid
from django.db import models

class Organization(models.Model):
    """
    Represents the tenant (enterprise client).
    Ensures complete multi-tenancy isolation at the database layer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Legal name of the organization")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DataSource(models.Model):
    """
    Defines configuration templates for data feeds ingested from external systems.
    Allows dynamic checking of schemas and layouts.
    """
    class SourceType(models.TextChoices):
        SAP_FUEL = "SAP_FUEL", "SAP Fuel & Procurement CSV"
        UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility Electricity Portal CSV"
        CORP_TRAVEL = "CORP_TRAVEL", "Corporate Travel JSON"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name="data_sources",
        help_text="Tenant that owns this configured data source"
    )
    name = models.CharField(max_length=255, help_text="Friendly label for this feed")
    source_type = models.CharField(
        max_length=50, 
        choices=SourceType.choices,
        help_text="Expected format / adapter to use during validation"
    )
    expected_schema = models.JSONField(
        default=dict, 
        blank=True,
        help_text="JSON mapping rules for parsing fields (e.g. source to destination fields)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Data Source"
        verbose_name_plural = "Data Sources"
        unique_together = (("organization", "name"),)
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
