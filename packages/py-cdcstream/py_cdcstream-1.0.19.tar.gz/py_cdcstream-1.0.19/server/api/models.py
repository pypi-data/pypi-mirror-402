from __future__ import annotations

from django.db import models


class NotificationChannel(models.Model):
	TYPE_SLACK = "slack"
	TYPE_WEBHOOK = "webhook"
	TYPE_SMTP = "email"
	TYPE_CHOICES = [
		(TYPE_SLACK, "Slack"),
		(TYPE_WEBHOOK, "Webhook"),
		(TYPE_SMTP, "Email (SMTP)"),
	]

	name = models.CharField(max_length=200, unique=True)
	channel_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
	config = models.JSONField(default=dict)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"{self.name} ({self.channel_type})"


class DataSource(models.Model):
	CONNECTOR_POSTGRES = "postgres"
	CONNECTOR_MYSQL = "mysql"
	CONNECTOR_SQLSERVER = "sqlserver"
	CONNECTOR_MONGODB = "mongodb"

	name = models.CharField(max_length=200)
	connector_type = models.CharField(max_length=50)
	connector_config = models.JSONField(default=dict)
	topic = models.CharField(max_length=200, blank=True, default="")
	status = models.CharField(max_length=50, blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.name


class Rule(models.Model):
	name = models.CharField(max_length=200, unique=True)
	description = models.TextField(blank=True, default="")
	is_active = models.BooleanField(default=True)

	# Data source configuration
	datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="rules", null=True, blank=True)
	schema_name = models.CharField(max_length=200, blank=True, default="")
	table_name = models.CharField(max_length=200, blank=True, default="")
	object_type = models.CharField(max_length=20, default="table", choices=[("table", "Table"), ("view", "View")])
	# For views: store the base tables that we need to monitor
	base_tables = models.JSONField(default=list, blank=True)

	# Filters and conditions
	filters = models.JSONField(default=list, blank=True)
	condition = models.JSONField(default=dict)

	# Log retention
	log_retention_days = models.PositiveIntegerField(default=30)

	# Notification channels (stored as JSON for alert-specific channel configs)
	notification_channels = models.JSONField(default=list, blank=True)
	target_channels = models.ManyToManyField(NotificationChannel, related_name="rules", blank=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return self.name


class TriggerLog(models.Model):
	STATUS_SUCCESS = "success"
	STATUS_FILTER_ONLY = "filter_only"
	STATUS_FAILED = "failed"
	STATUS_CHOICES = [
		(STATUS_SUCCESS, "Success"),
		(STATUS_FILTER_ONLY, "Filter Only"),
		(STATUS_FAILED, "Failed"),
	]

	rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="trigger_logs")
	event = models.JSONField(default=dict)
	dispatch_results = models.JSONField(default=dict)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
	error_message = models.TextField(blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"{self.rule_id} {self.status} {self.created_at.isoformat()}"


class CDCEvent(models.Model):
	"""Stores CDC events for the Watch Live UI feature."""
	rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="cdc_events")
	stage = models.CharField(max_length=50)  # received, filter, condition, notification
	event_data = models.JSONField(default=dict)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['rule', '-created_at']),
		]

	def __str__(self) -> str:
		return f"Rule {self.rule_id} - {self.stage} @ {self.created_at.isoformat()}"


class RestApiTestLog(models.Model):
	"""Stores incoming requests to the mock REST API test endpoint."""
	method = models.CharField(max_length=10)  # GET, POST, PUT, PATCH, DELETE
	path = models.CharField(max_length=500)
	query_params = models.JSONField(default=dict)
	headers = models.JSONField(default=dict)
	body = models.TextField(blank=True, default="")
	body_json = models.JSONField(default=dict, blank=True, null=True)
	source_ip = models.CharField(max_length=50, blank=True, default="")
	response_status = models.IntegerField(default=200)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['-created_at']),
		]

	def __str__(self) -> str:
		return f"{self.method} {self.path} @ {self.created_at.isoformat()}"


class AnomalyDetector(models.Model):
	"""Anomaly detection configuration for CDC events."""
	ALGORITHM_ZSCORE = "zscore"
	ALGORITHM_ISOLATION_FOREST = "isolation_forest"
	ALGORITHM_MAHALANOBIS = "mahalanobis"
	ALGORITHM_ECOD = "ecod"
	ALGORITHM_HBOS = "hbos"

	ALGORITHM_CHOICES = [
		(ALGORITHM_ZSCORE, "Z-Score (Standart Sapma)"),
		(ALGORITHM_ISOLATION_FOREST, "Isolation Forest (Çok Boyutlu)"),
		(ALGORITHM_MAHALANOBIS, "Mahalanobis Distance (Korelasyon)"),
		(ALGORITHM_ECOD, "ECOD (Parametresiz)"),
		(ALGORITHM_HBOS, "HBOS (Hızlı Histogram)"),
	]

	name = models.CharField(max_length=200, unique=True)
	description = models.TextField(blank=True, default="")
	is_active = models.BooleanField(default=True)

	# Data source configuration
	datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="anomaly_detectors")
	schema_name = models.CharField(max_length=200, blank=True, default="")
	table_name = models.CharField(max_length=200)

	# Algorithm configuration
	algorithm = models.CharField(max_length=50, choices=ALGORITHM_CHOICES, default=ALGORITHM_ZSCORE)
	target_columns = models.JSONField(default=list)  # ["salary", "amount", "price"]

	# Algorithm-specific parameters
	parameters = models.JSONField(default=dict)
	# Z-Score: {"threshold": 3.0, "window_size": 1000}
	# Isolation Forest: {"contamination": 0.1, "n_estimators": 100}
	# Mahalanobis: {"threshold": 3.0}
	# ECOD: {"contamination": 0.1}
	# HBOS: {"n_bins": 10, "alpha": 0.1}

	# Trained model state (mean, std, histograms, etc.)
	model_state = models.JSONField(default=dict)
	last_trained_at = models.DateTimeField(null=True, blank=True)
	training_sample_count = models.IntegerField(default=0)

	# Notification channels
	notification_channels = models.JSONField(default=list, blank=True)
	target_channels = models.ManyToManyField(NotificationChannel, related_name="anomaly_detectors", blank=True)

	# Operation filter (INSERT, UPDATE, DELETE, or empty for all)
	operations = models.JSONField(default=list, blank=True)  # ["INSERT", "UPDATE"]

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		return f"{self.name} ({self.get_algorithm_display()})"


class FieldStats(models.Model):
	"""Stores rolling statistics for fields used in anomaly detection."""
	detector = models.ForeignKey(AnomalyDetector, on_delete=models.CASCADE, related_name="field_stats")
	field_name = models.CharField(max_length=200)

	# Rolling statistics
	count = models.BigIntegerField(default=0)
	sum_value = models.FloatField(default=0.0)
	sum_squared = models.FloatField(default=0.0)
	min_value = models.FloatField(null=True, blank=True)
	max_value = models.FloatField(null=True, blank=True)

	# For histogram-based methods (HBOS)
	histogram = models.JSONField(default=dict)  # {"bins": [...], "counts": [...]}

	# For ECOD (empirical CDF)
	value_samples = models.JSONField(default=list)  # Last N values for CDF

	# Covariance data for Mahalanobis (stored at detector level, but referenced here)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ['detector', 'field_name']
		indexes = [
			models.Index(fields=['detector', 'field_name']),
		]

	@property
	def mean(self) -> float:
		if self.count == 0:
			return 0.0
		return self.sum_value / self.count

	@property
	def variance(self) -> float:
		if self.count < 2:
			return 0.0
		mean = self.mean
		return (self.sum_squared / self.count) - (mean * mean)

	@property
	def std(self) -> float:
		import math
		return math.sqrt(max(0, self.variance))

	def __str__(self) -> str:
		return f"{self.detector.name}.{self.field_name} (n={self.count})"


class AnomalyLog(models.Model):
	"""Logs detected anomalies."""
	detector = models.ForeignKey(AnomalyDetector, on_delete=models.CASCADE, related_name="anomaly_logs")
	event_data = models.JSONField(default=dict)
	anomaly_score = models.FloatField()  # Z-score, distance, etc.
	anomaly_fields = models.JSONField(default=list)  # Which fields triggered the anomaly
	threshold_used = models.FloatField()
	dispatch_results = models.JSONField(default=dict)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['detector', '-created_at']),
		]

	def __str__(self) -> str:
		return f"Anomaly on {self.detector.name}: score={self.anomaly_score:.2f}"


