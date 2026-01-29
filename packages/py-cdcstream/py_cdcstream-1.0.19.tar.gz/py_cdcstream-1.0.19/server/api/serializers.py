from __future__ import annotations

from rest_framework import serializers

from .models import DataSource, NotificationChannel, Rule, TriggerLog, AnomalyDetector, AnomalyLog, FieldStats


class NotificationChannelSerializer(serializers.ModelSerializer):
	class Meta:
		model = NotificationChannel
		fields = "__all__"


class DataSourceSerializer(serializers.ModelSerializer):
	class Meta:
		model = DataSource
		fields = "__all__"


class RuleSerializer(serializers.ModelSerializer):
	target_channels = serializers.PrimaryKeyRelatedField(
		many=True, queryset=NotificationChannel.objects.all(), required=False
	)

	class Meta:
		model = Rule
		fields = "__all__"

	def _sanitize_topic_name(self, name):
		"""Sanitize topic name to only contain allowed characters: ASCII alphanumerics, '.', '_', '-'"""
		import re
		# Replace spaces and other illegal chars with underscore
		sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
		# Remove consecutive underscores
		sanitized = re.sub(r'_+', '_', sanitized)
		# Remove leading/trailing underscores
		return sanitized.strip('_')

	def _update_datasource_topic(self, datasource, schema_name, table_name):
		"""Automatically set topic on DataSource based on alert's schema/table"""
		if datasource and schema_name and table_name:
			# Get topic_prefix from connector_config, default to datasource name
			connector_config = datasource.connector_config or {}
			topic_prefix = (
				connector_config.get("topic_prefix") or
				connector_config.get("topic.prefix") or
				connector_config.get("database.server.name") or
				datasource.name
			)

			# Sanitize topic prefix to remove illegal characters (like spaces)
			topic_prefix = self._sanitize_topic_name(topic_prefix)

			# Generate topic in Debezium format: prefix.schema.table
			new_topic = f"{topic_prefix}.{schema_name}.{table_name}"

			# Update DataSource topic
			if not datasource.topic:
				datasource.topic = new_topic
			elif new_topic not in datasource.topic:
				# Append new topic (comma-separated for multiple tables)
				datasource.topic = f"{datasource.topic},{new_topic}"
			else:
				return  # Topic already exists, no need to update

			# Also save topic_prefix in connector_config for future use
			if "topic_prefix" not in connector_config:
				connector_config["topic_prefix"] = topic_prefix
				datasource.connector_config = connector_config
				datasource.save(update_fields=["topic", "connector_config"])
			else:
				datasource.save(update_fields=["topic"])

	def create(self, validated_data):
		instance = super().create(validated_data)
		# Auto-set topic on DataSource
		self._update_datasource_topic(
			instance.datasource,
			instance.schema_name,
			instance.table_name
		)
		return instance

	def update(self, instance, validated_data):
		instance = super().update(instance, validated_data)
		# Auto-set topic on DataSource
		self._update_datasource_topic(
			instance.datasource,
			instance.schema_name,
			instance.table_name
		)
		return instance


class TriggerLogSerializer(serializers.ModelSerializer):
	rule_name = serializers.SerializerMethodField()

	class Meta:
		model = TriggerLog
		fields = ["id", "rule", "rule_name", "event", "dispatch_results", "status", "error_message", "created_at"]

	def get_rule_name(self, obj):
		return obj.rule.name if obj.rule else "Unknown"


class FieldStatsSerializer(serializers.ModelSerializer):
	mean = serializers.FloatField(read_only=True)
	std = serializers.FloatField(read_only=True)

	class Meta:
		model = FieldStats
		fields = ["id", "field_name", "count", "sum_value", "sum_squared", "min_value", "max_value", "mean", "std", "updated_at"]


class AnomalyDetectorSerializer(serializers.ModelSerializer):
	target_channels = serializers.PrimaryKeyRelatedField(
		many=True, queryset=NotificationChannel.objects.all(), required=False
	)
	datasource_name = serializers.SerializerMethodField()
	algorithm_display = serializers.SerializerMethodField()
	stats_summary = serializers.SerializerMethodField()

	class Meta:
		model = AnomalyDetector
		fields = [
			"id", "name", "description", "is_active",
			"datasource", "datasource_name", "schema_name", "table_name",
			"algorithm", "algorithm_display", "target_columns", "parameters",
			"model_state", "last_trained_at", "training_sample_count",
			"notification_channels", "target_channels", "operations",
			"stats_summary", "created_at", "updated_at"
		]
		read_only_fields = ["model_state", "last_trained_at", "training_sample_count"]

	def get_datasource_name(self, obj):
		return obj.datasource.name if obj.datasource else None

	def get_algorithm_display(self, obj):
		return obj.get_algorithm_display()

	def get_stats_summary(self, obj):
		"""Return summary of field statistics."""
		stats = obj.field_stats.all()
		return {
			s.field_name: {
				"count": s.count,
				"mean": round(s.mean, 4) if s.count > 0 else None,
				"std": round(s.std, 4) if s.count > 1 else None,
				"min": s.min_value,
				"max": s.max_value,
			}
			for s in stats
		}


class AnomalyLogSerializer(serializers.ModelSerializer):
	detector_name = serializers.SerializerMethodField()
	algorithm = serializers.SerializerMethodField()

	class Meta:
		model = AnomalyLog
		fields = [
			"id", "detector", "detector_name", "algorithm",
			"event_data", "anomaly_score", "anomaly_fields",
			"threshold_used", "dispatch_results", "created_at"
		]

	def get_detector_name(self, obj):
		return obj.detector.name if obj.detector else None

	def get_algorithm(self, obj):
		return obj.detector.algorithm if obj.detector else None


