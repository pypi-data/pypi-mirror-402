from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
	initial = True

	dependencies = []

	operations = [
		migrations.CreateModel(
			name="NotificationChannel",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("name", models.CharField(max_length=200, unique=True)),
				("channel_type", models.CharField(choices=[("slack", "Slack"), ("webhook", "Webhook"), ("smtp", "SMTP")], max_length=20)),
				("config", models.JSONField(default=dict)),
				("is_active", models.BooleanField(default=True)),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
			],
		),
		migrations.CreateModel(
			name="DataSource",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("name", models.CharField(max_length=200, unique=True)),
				("connector_type", models.CharField(max_length=50)),
				("connector_config", models.JSONField(default=dict)),
				("topic", models.CharField(blank=True, default="", max_length=200)),
				("status", models.CharField(blank=True, default="", max_length=50)),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
			],
		),
		migrations.CreateModel(
			name="Rule",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("name", models.CharField(max_length=200, unique=True)),
				("description", models.TextField(blank=True, default="")),
				("is_active", models.BooleanField(default=True)),
				("condition", models.JSONField(default=dict)),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("updated_at", models.DateTimeField(auto_now=True)),
			],
		),
		migrations.CreateModel(
			name="TriggerLog",
			fields=[
				("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
				("event", models.JSONField(default=dict)),
				("dispatch_results", models.JSONField(default=dict)),
				("status", models.CharField(choices=[("success", "Success"), ("failed", "Failed")], default="success", max_length=20)),
				("created_at", models.DateTimeField(auto_now_add=True)),
				("rule", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="trigger_logs", to="api.rule")),
			],
		),
		migrations.AddField(
			model_name="rule",
			name="target_channels",
			field=models.ManyToManyField(blank=True, related_name="rules", to="api.notificationchannel"),
		),
	]


