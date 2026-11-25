"""Adapters: one small module per scanner, loaded by name from scanners.yaml."""

import importlib

from .base import ScannerAdapter


def load_adapter(scanner_id, spec, scanners_dir):
    """Build the adapter named in a registry entry (spec['adapter'])."""
    module = importlib.import_module("scanners.adapters." + spec["adapter"])
    for obj in vars(module).values():
        if (isinstance(obj, type) and issubclass(obj, ScannerAdapter)
                and obj is not ScannerAdapter and getattr(obj, "id", "") == scanner_id):
            return obj(spec, scanners_dir)
    raise ImportError("no adapter with id %r in scanners.adapters.%s" % (scanner_id, spec["adapter"]))
