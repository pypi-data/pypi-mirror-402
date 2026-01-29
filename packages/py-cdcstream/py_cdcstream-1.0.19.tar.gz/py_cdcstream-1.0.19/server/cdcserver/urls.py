from __future__ import annotations

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
from api.views import ConfigView  # ensure /api/config is reachable even if app urls miss it
import json


def health(_request):
	return JsonResponse({"status": "ok"})


@csrf_exempt
def webhook_test_receiver(request):
	"""Universal webhook test receiver - accepts POST at any configured path"""
	if request.method == "POST":
		try:
			data = json.loads(request.body) if request.body else {}
		except json.JSONDecodeError:
			data = {"raw_body": request.body.decode("utf-8", errors="ignore")}

		from django.utils import timezone
		return JsonResponse({
			"success": True,
			"message": "Webhook received successfully!",
			"received_data": data,
			"timestamp": timezone.now().isoformat(),
		})
	return JsonResponse({"error": "Only POST method allowed"}, status=405)

def spa_index(_request):
	index_path: Path = settings.FRONTEND_OUT_DIR / "index.html"
	if index_path.exists():
		return FileResponse(open(index_path, "rb"))
	return JsonResponse({"message": "UI not built. Run: cd web && npm install && npm run build"}, status=200)

def spa_page(request, page=""):
	"""Serve Next.js exported HTML pages"""
	# Try exact page match first (e.g., alerts.html)
	if page:
		page_path = settings.FRONTEND_OUT_DIR / f"{page}.html"
		if page_path.exists():
			return FileResponse(open(page_path, "rb"), content_type="text/html")
		# Try nested path (e.g., alerts/new.html)
		nested_path = settings.FRONTEND_OUT_DIR / page / "index.html"
		if nested_path.exists():
			return FileResponse(open(nested_path, "rb"), content_type="text/html")
		# Try with .html extension for nested paths
		nested_html = settings.FRONTEND_OUT_DIR / f"{page}.html"
		if nested_html.exists():
			return FileResponse(open(nested_html, "rb"), content_type="text/html")
	# Fallback to index.html for SPA routing
	return spa_index(request)


urlpatterns = [
	path("admin/", admin.site.urls),
	path("api/health/", health, name="health"),
	path("api/", include("api.urls")),
	# Direct binding for config to avoid 404 due to trailing slash or routing issues
	path("api/config/", ConfigView.as_view(), name="config-direct"),
	path("api/config", ConfigView.as_view(), name="config-direct-noslash"),
	# Webhook test receivers - for testing webhook configurations
	path("webhook-test/", webhook_test_receiver, name="webhook-test-root"),
	path("webhook-test", webhook_test_receiver, name="webhook-test-root-noslash"),
	path("alert/", webhook_test_receiver, name="alert-webhook"),
	path("alert", webhook_test_receiver, name="alert-webhook-noslash"),
	# Serve Next.js export static files (_next, assets, public)
	re_path(r"^_next/(?P<path>.*)$", static_serve, {"document_root": settings.FRONTEND_OUT_DIR / "_next"}),
	re_path(r"^assets/(?P<path>.*)$", static_serve, {"document_root": settings.FRONTEND_OUT_DIR / "assets"}),
	re_path(r"^dbicons/(?P<path>.*)$", static_serve, {"document_root": settings.FRONTEND_OUT_DIR / "dbicons"}),
	re_path(r"^notificationchannelicons/(?P<path>.*)$", static_serve, {"document_root": settings.FRONTEND_OUT_DIR / "notificationchannelicons"}),
	# Serve root-level static files (mp4, png, etc.)
	re_path(r"^(?P<path>[\w\-]+\.(mp4|png|jpg|jpeg|gif|svg|ico|webp))$", static_serve, {"document_root": settings.FRONTEND_OUT_DIR}),
	# SPA routes - serve HTML pages
	path("", spa_index, name="spa-index"),
	re_path(r"^(?P<page>[\w\-/]+)/?$", spa_page, name="spa-page"),
]


