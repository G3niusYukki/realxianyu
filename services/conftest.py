"""Pytest configuration for services directory."""
import os
import sys

# Ensure gateway-service and common are on the Python path for imports
_services_dir = os.path.dirname(os.path.abspath(__file__))
for _svc in ("common", "gateway-service"):
    _path = os.path.join(_services_dir, _svc)
    if _path not in sys.path:
        sys.path.insert(0, _path)
