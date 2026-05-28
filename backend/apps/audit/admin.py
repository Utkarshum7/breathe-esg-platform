from django.contrib import admin
from .models import AuditTrail

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ("action", "organization", "record", "changed_by", "timestamp")
    list_filter = ("action", "organization", "timestamp")
    search_fields = ("action", "reason")
    readonly_fields = ("id", "organization", "record", "record_uuid_backup", "action", "changed_by", "changes", "reason", "timestamp")
    
    # Disable manual creation and deletion inside Django Admin for strict audit integrity
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
