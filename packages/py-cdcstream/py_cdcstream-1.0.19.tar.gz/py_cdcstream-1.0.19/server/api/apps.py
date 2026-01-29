from __future__ import annotations

from django.apps import AppConfig


class ApiConfig(AppConfig):
	default_auto_field = "django.db.models.BigAutoField"
	name = "api"
	verbose_name = "CDC Stream API"

	def ready(self):
		# Import signals to register them
		try:
			from . import signals  # noqa: F401
		except ImportError:
			pass


