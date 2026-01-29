# -*- coding: utf-8 -*-
"""
⚠️ DEPRECATED: clouvel-pro is deprecated. Use 'clouvel' instead.

All Pro features are now included in clouvel v1.0.0+

Migration:
    pip uninstall clouvel-pro
    pip install clouvel
"""

import warnings

__version__ = "2.0.0"

# Show deprecation warning on import
warnings.warn(
    "\n"
    "=" * 60 + "\n"
    "⚠️  clouvel-pro is DEPRECATED\n"
    "=" * 60 + "\n"
    "All Pro features are now included in 'clouvel' v1.0.0+\n\n"
    "Migration:\n"
    "  pip uninstall clouvel-pro\n"
    "  pip install clouvel\n"
    "=" * 60,
    DeprecationWarning,
    stacklevel=2
)

# Re-export from clouvel for backwards compatibility
try:
    from clouvel import *
except ImportError:
    pass
