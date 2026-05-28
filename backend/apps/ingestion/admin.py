from django.contrib import admin
from .models import UploadBatch, EmissionRecord

@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ("file_name", "organization", "data_source", "status", "total_rows", "created_at")
    list_filter = ("status", "organization", "data_source")
    search_fields = ("file_name",)
    readonly_fields = ("id", "created_at", "updated_at")

@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "batch", "row_index", "status", "normalized_value", "normalized_unit", "scope_category", "is_suspicious")
    list_filter = ("status", "scope_category", "is_suspicious", "organization")
    search_fields = ("batch__file_name", "id")
    readonly_fields = ("id", "created_at", "updated_at")
