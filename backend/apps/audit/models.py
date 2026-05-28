import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.core.models import Organization

class AuditTrail(models.Model):
    """
    An immutable, append-only log capturing all state changes, analyst reviews,
    manual corrections, and system status adjustments for tracking and regulatory reviews.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="audit_trails",
        help_text="Tenant context of this audit log"
    )
    # Reference to original EmissionRecord. We set to SET_NULL so that the log
    # remains if a record is deleted, but we also save the direct record ID backup.
    record = models.ForeignKey(
        "ingestion.EmissionRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="Associated emission record transaction"
    )
    record_uuid_backup = models.UUIDField(
        null=True,
        blank=True,
        help_text="Immutable copy of the record ID to preserve history if record is deleted"
    )
    action = models.CharField(
        max_length=100,
        help_text="Type of action performed (e.g. RECORD_UPDATE, STATUS_CHANGE, AUDIT_LOCK)"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who executed this action"
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dictionary containing before/after states of changed fields"
    )
    reason = models.TextField(
        null=True,
        blank=True,
        help_text="Analyst-provided comment explaining this manual edit or status change"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit Trail Log"
        verbose_name_plural = "Audit Trail Logs"
        ordering = ["-timestamp"]

    def clean(self):
        super().clean()
        if self.pk and AuditTrail.objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit logs are read-only and cannot be altered or modified.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit logs are append-only and cannot be deleted.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.action} on {self.timestamp.strftime('%Y-%m-%d %H:%M')} by {self.changed_by}"
