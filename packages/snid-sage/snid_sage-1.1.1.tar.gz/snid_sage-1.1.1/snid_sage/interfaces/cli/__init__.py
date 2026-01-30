from __future__ import annotations

import argparse


def add_subcommands(parser: argparse.ArgumentParser) -> None:
    # Identify command
    try:
        from . import identify as _identify
        sub = parser.add_subparsers(dest="cmd")
        p_ident = sub.add_parser("identify", help="Identify a spectrum using SNID-SAGE")
        _identify.add_arguments(p_ident)
        p_ident.set_defaults(_entry=_identify.main)
    except Exception:
        pass

    # Batch command
    try:
        from . import batch as _batch
        p_batch = sub.add_parser("batch", help="Batch process spectra using SNID-SAGE")
        _batch.add_arguments(p_batch)
        p_batch.set_defaults(_entry=_batch.main)
    except Exception:
        pass

    # Templates command
    try:
        from . import templates as _templates
        p_tpl = sub.add_parser("templates", help="Template operations (import/export)")
        _templates.add_arguments(p_tpl)
        p_tpl.set_defaults(_entry=_templates.main)
    except Exception:
        pass


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="sage")
    add_subcommands(parser)
    args = parser.parse_args(argv)
    entry = getattr(args, "_entry", None)
    if entry is None:
        parser.print_help()
        return 1
    return int(entry(args) or 0)

"""
SNID SAGE CLI Interface
======================

Command-line interface for SNID SAGE spectrum analysis.

This module provides command-line tools for:
- Spectrum identification
- Batch processing
- Configuration management
"""

__version__ = "1.0.0"

# Import main CLI components
try:
    from .main import main
except ImportError:
    main = None

# Import command modules individually
try:
    from . import identify
except ImportError:
    identify = None

try:
    from . import batch
except ImportError:
    batch = None

try:
    from . import config
except ImportError:
    config = None

__all__ = ['main', 'identify', 'batch', 'config']