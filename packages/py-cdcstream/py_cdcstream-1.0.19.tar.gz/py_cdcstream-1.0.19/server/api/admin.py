from __future__ import annotations

from django.contrib import admin

from .models import DataSource, NotificationChannel, Rule, TriggerLog


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "channel_type", "is_active", "created_at")
	search_fields = ("name", "channel_type")
	list_filter = ("channel_type", "is_active")


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "connector_type", "topic", "status", "created_at")
	search_fields = ("name", "connector_type", "topic", "status")
	list_filter = ("connector_type", "status")


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "is_active", "created_at")
	search_fields = ("name", "description")
	list_filter = ("is_active",)


@admin.register(TriggerLog)
class TriggerLogAdmin(admin.ModelAdmin):
	list_display = ("id", "rule", "status", "created_at")
	search_fields = ("rule__name",)
	list_filter = ("status", "created_at")


