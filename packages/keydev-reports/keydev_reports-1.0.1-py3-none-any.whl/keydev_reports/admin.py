from django.contrib import admin

from .models import ReportTemplate


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'related_model', 'file')
    search_fields = ('name', 'related_model', 'file')
    list_filter = ('name', 'related_model')
    list_per_page = 10
