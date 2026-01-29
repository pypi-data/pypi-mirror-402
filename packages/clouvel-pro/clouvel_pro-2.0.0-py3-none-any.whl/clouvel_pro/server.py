# -*- coding: utf-8 -*-
"""
⚠️ DEPRECATED: clouvel-pro is deprecated. Use 'clouvel' instead.

This server now redirects to clouvel.
"""

import warnings

# Show deprecation warning
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


def main():
    """Redirect to clouvel server"""
    print("=" * 60)
    print("⚠️  clouvel-pro is DEPRECATED")
    print("=" * 60)
    print()
    print("All Pro features are now included in 'clouvel' v1.0.0+")
    print()
    print("Migration:")
    print("  pip uninstall clouvel-pro")
    print("  pip install clouvel")
    print()
    print("Starting clouvel instead...")
    print("=" * 60)

    # Try to run clouvel
    try:
        from clouvel import main as clouvel_main
        clouvel_main()
    except ImportError:
        print()
        print("ERROR: clouvel is not installed.")
        print("Please run: pip install clouvel")


if __name__ == "__main__":
    main()
