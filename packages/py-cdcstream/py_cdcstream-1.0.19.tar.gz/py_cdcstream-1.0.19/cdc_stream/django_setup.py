from __future__ import annotations

import os
import sys
from pathlib import Path

_DJANGO_READY = False


def setup_django_if_needed() -> None:
	global _DJANGO_READY
	if _DJANGO_READY:
		return
	# Prefer local 'server' directory in development to avoid stale installed package
	here = Path(__file__).resolve()
	root = here.parent.parent
	server_dir = root / "server"
	if server_dir.exists():
		sys.path.insert(0, str(server_dir))
	# Configure settings and setup Django
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cdcserver.settings")
	try:
		import django  # type: ignore

		django.setup()
		_DJANGO_READY = True
	except Exception as exc:
		raise RuntimeError(f"Could not initialize Django: {exc}") from exc


