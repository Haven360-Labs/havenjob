"""Pytest configuration. Ensures Django is configured before collecting tests."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()
