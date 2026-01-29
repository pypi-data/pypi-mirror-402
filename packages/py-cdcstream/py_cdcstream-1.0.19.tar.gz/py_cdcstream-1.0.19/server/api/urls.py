from __future__ import annotations

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
	DataSourceViewSet,
	NotificationChannelViewSet,
	RuleViewSet,
	TriggerLogViewSet,
	MetricsSummaryView,
	WorkerHealthView,
	ConfigView,
	WebhookTestReceiverView,
	CDCLiveStreamView,
	CDCEventsView,
	RestApiEchoView,
	RestApiTestLogsView,
	TestRestApiView,
	AnomalyDetectorViewSet,
	AnomalyLogViewSet,
)

router = DefaultRouter()
# Allow both /resource and /resource/ forms
router.trailing_slash = '/?'
router.register(r"channels", NotificationChannelViewSet, basename="channel")
router.register(r"datasources", DataSourceViewSet, basename="datasource")
router.register(r"rules", RuleViewSet, basename="rule")
router.register(r"trigger-logs", TriggerLogViewSet, basename="triggerlog")
router.register(r"anomaly-detectors", AnomalyDetectorViewSet, basename="anomaly-detector")
router.register(r"anomaly-logs", AnomalyLogViewSet, basename="anomaly-log")

urlpatterns = [
	# REST API test endpoint - MUST be before router to take priority
	path("channels/test_rest_api/", TestRestApiView.as_view(), name="test-rest-api"),
	path("channels/test_rest_api", TestRestApiView.as_view(), name="test-rest-api-no-slash"),
	# Router URLs
	path("", include(router.urls)),
	path("metrics/summary/", MetricsSummaryView.as_view(), name="metrics-summary"),
	path("worker-health/", WorkerHealthView.as_view(), name="worker-health"),
	path("worker-health", WorkerHealthView.as_view(), name="worker-health-no-slash"),
	# Support both with and without trailing slash
	path("config/", ConfigView.as_view(), name="config"),
	path("config", ConfigView.as_view(), name="config-no-slash"),
	# Webhook test receiver - for testing webhook configurations
	path("webhook-test/", WebhookTestReceiverView.as_view(), name="webhook-test"),
	path("webhook-test", WebhookTestReceiverView.as_view(), name="webhook-test-no-slash"),
	# CDC Live Stream endpoints
	path("cdc-stream/<int:rule_id>/", CDCLiveStreamView.as_view(), name="cdc-stream"),
	path("cdc-events/<int:rule_id>/", CDCEventsView.as_view(), name="cdc-events"),
	# REST API testing endpoints
	path("rest-echo/", RestApiEchoView.as_view(), name="rest-echo"),
	path("rest-echo", RestApiEchoView.as_view(), name="rest-echo-no-slash"),
	path("rest-api-logs/", RestApiTestLogsView.as_view(), name="rest-api-logs"),
	path("rest-api-logs", RestApiTestLogsView.as_view(), name="rest-api-logs-no-slash"),
]


