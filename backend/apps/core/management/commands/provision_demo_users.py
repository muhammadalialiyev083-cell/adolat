"""Compatibility alias; the former password-resetting seeder is retired."""

from apps.core.management.commands.seed_demo_data import Command  # noqa: F401
