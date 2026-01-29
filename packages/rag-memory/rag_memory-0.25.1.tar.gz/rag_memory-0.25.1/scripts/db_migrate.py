#!/usr/bin/env python3
"""
RAG Memory Database Migration Tool

A reliable, repeatable process for managing Alembic migrations across
all PostgreSQL instances.

Commands:
    status    - Show migration status of all databases
    create    - Create a new migration file
    apply     - Apply pending migrations to all databases
    rollback  - Rollback one migration on all databases

Usage:
    uv run python scripts/db_migrate.py status
    uv run python scripts/db_migrate.py create "add_user_preferences"
    uv run python scripts/db_migrate.py apply
    uv run python scripts/db_migrate.py rollback

This tool ensures:
    - Migrations are created with proper revision chains
    - All databases are migrated together
    - Status is verified before and after changes
    - Clear reporting of what happened
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# =============================================================================
# Configuration
# =============================================================================

# All RAG Memory Postgres instances (port -> name)
INSTANCES = {
    54320: "ctf-ops",
    54321: "primary",
    54322: "dev-support",
    54323: "test",
}

# Connection settings (same across all instances)
DB_USER = "raguser"
DB_PASS = "ragpassword"
DB_NAME = "rag_memory"
DB_HOST = "localhost"

# Project paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
ALEMBIC_INI = PROJECT_ROOT / "deploy" / "alembic" / "alembic.ini"
VERSIONS_DIR = PROJECT_ROOT / "deploy" / "alembic" / "versions"


# =============================================================================
# Helpers
# =============================================================================

def get_database_url(port: int) -> str:
    """Build DATABASE_URL for a given port."""
    return f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{port}/{DB_NAME}"


def run_alembic(port: int, *args) -> tuple[int, str, str]:
    """
    Run an alembic command against a specific database.

    Returns: (return_code, stdout, stderr)
    """
    env = os.environ.copy()
    env["DATABASE_URL"] = get_database_url(port)

    cmd = ["uv", "run", "alembic", "-c", str(ALEMBIC_INI)] + list(args)

    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    return result.returncode, result.stdout, result.stderr


def get_current_revision(port: int) -> Optional[str]:
    """Get the current revision for a database."""
    code, stdout, stderr = run_alembic(port, "current")
    if code == 0:
        # First line of output is the revision (may have " (head)" suffix)
        lines = stdout.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("INFO"):
                # Extract just the revision ID (first word)
                return line.split()[0] if line else None
    return None


def get_head_revision() -> Optional[str]:
    """Get the head revision from alembic history."""
    # Use any port, we just need the history
    code, stdout, stderr = run_alembic(54320, "heads")
    if code == 0:
        lines = stdout.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("INFO"):
                # Format: "004_rename_topic (head)"
                return line.split()[0] if line else None
    return None


# =============================================================================
# Commands
# =============================================================================

def cmd_status():
    """Show migration status of all databases."""
    print("=" * 60)
    print("RAG Memory - Database Migration Status")
    print("=" * 60)
    print()

    # Get head revision
    head = get_head_revision()
    print(f"Head revision: {head}")
    print()

    # Check each database
    print(f"{'Instance':<15} {'Port':<8} {'Current Revision':<25} {'Status'}")
    print("-" * 60)

    all_current = True
    for port, name in sorted(INSTANCES.items()):
        current = get_current_revision(port)

        if current == head:
            status = "✅ Up to date"
        elif current is None:
            status = "❌ Error or no migrations"
            all_current = False
        else:
            status = "⚠️  Needs migration"
            all_current = False

        print(f"{name:<15} {port:<8} {current or 'unknown':<25} {status}")

    print()
    if all_current:
        print("All databases are up to date.")
    else:
        print("Some databases need migration. Run: uv run python scripts/db_migrate.py apply")

    return 0 if all_current else 1


def cmd_create(description: str):
    """Create a new migration file."""
    print("=" * 60)
    print("RAG Memory - Create New Migration")
    print("=" * 60)
    print()

    # Sanitize description for filename
    safe_desc = description.lower().replace(" ", "_").replace("-", "_")
    safe_desc = "".join(c for c in safe_desc if c.isalnum() or c == "_")

    print(f"Creating migration: {description}")
    print()

    # Run alembic revision
    code, stdout, stderr = run_alembic(54320, "revision", "-m", description)

    # Show output
    if stdout.strip():
        print(stdout)
    if stderr.strip():
        print(stderr)

    if code == 0:
        print()
        print("✅ Migration created successfully!")
        print()
        print("Next steps:")
        print(f"  1. Edit the new migration file in: {VERSIONS_DIR}/")
        print("  2. Implement upgrade() and downgrade() functions")
        print("  3. Test with: uv run python scripts/db_migrate.py apply")
        print()
        print("⚠️  IMPORTANT: Once applied, NEVER edit the migration file.")
        print("    Create a new migration for any changes.")
    else:
        print()
        print("❌ Failed to create migration")
        return 1

    return 0


def cmd_apply():
    """Apply pending migrations to all databases."""
    print("=" * 60)
    print("RAG Memory - Apply Migrations")
    print("=" * 60)
    print()

    # Show status before
    print("BEFORE:")
    print("-" * 40)
    head = get_head_revision()
    print(f"Head revision: {head}")
    print()

    statuses_before = {}
    for port, name in sorted(INSTANCES.items()):
        current = get_current_revision(port)
        statuses_before[port] = current
        needs = "needs migration" if current != head else "up to date"
        print(f"  {name}: {current} ({needs})")

    print()
    print("APPLYING MIGRATIONS:")
    print("-" * 40)

    succeeded = []
    failed = []

    for port, name in sorted(INSTANCES.items()):
        print(f"\n[{name}] Port {port}")

        code, stdout, stderr = run_alembic(port, "upgrade", "head")

        # Show output (indented)
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                print(f"    {line}")
        if stderr.strip():
            for line in stderr.strip().split("\n"):
                print(f"    {line}")

        if code == 0:
            print(f"    ✅ Success")
            succeeded.append(name)
        else:
            print(f"    ❌ Failed (exit code {code})")
            failed.append(name)

    # Show status after
    print()
    print("AFTER:")
    print("-" * 40)

    for port, name in sorted(INSTANCES.items()):
        current = get_current_revision(port)
        before = statuses_before[port]

        if before == current:
            change = "(no change)"
        else:
            change = f"(was: {before})"

        print(f"  {name}: {current} {change}")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Succeeded: {', '.join(succeeded) if succeeded else 'none'}")
    print(f"Failed: {', '.join(failed) if failed else 'none'}")

    if failed:
        print()
        print("⚠️  Some migrations failed. Check errors above.")
        return 1
    else:
        print()
        print("✅ All migrations applied successfully!")
        return 0


def cmd_rollback():
    """Rollback one migration on all databases."""
    print("=" * 60)
    print("RAG Memory - Rollback Migration")
    print("=" * 60)
    print()

    # Show status before
    print("BEFORE:")
    print("-" * 40)

    statuses_before = {}
    for port, name in sorted(INSTANCES.items()):
        current = get_current_revision(port)
        statuses_before[port] = current
        print(f"  {name}: {current}")

    # Confirm
    print()
    response = input("⚠️  This will rollback ONE migration on ALL databases. Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled.")
        return 0

    print()
    print("ROLLING BACK:")
    print("-" * 40)

    succeeded = []
    failed = []

    for port, name in sorted(INSTANCES.items()):
        print(f"\n[{name}] Port {port}")

        code, stdout, stderr = run_alembic(port, "downgrade", "-1")

        # Show output (indented)
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                print(f"    {line}")
        if stderr.strip():
            for line in stderr.strip().split("\n"):
                print(f"    {line}")

        if code == 0:
            print(f"    ✅ Success")
            succeeded.append(name)
        else:
            print(f"    ❌ Failed (exit code {code})")
            failed.append(name)

    # Show status after
    print()
    print("AFTER:")
    print("-" * 40)

    for port, name in sorted(INSTANCES.items()):
        current = get_current_revision(port)
        before = statuses_before[port]
        print(f"  {name}: {current} (was: {before})")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Succeeded: {', '.join(succeeded) if succeeded else 'none'}")
    print(f"Failed: {', '.join(failed) if failed else 'none'}")

    return 1 if failed else 0


# =============================================================================
# Main
# =============================================================================

def print_usage():
    """Print usage information."""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        return 1

    command = sys.argv[1].lower()

    if command == "status":
        return cmd_status()

    elif command == "create":
        if len(sys.argv) < 3:
            print("Error: create requires a description")
            print("Usage: uv run python scripts/db_migrate.py create \"description\"")
            return 1
        return cmd_create(sys.argv[2])

    elif command == "apply":
        return cmd_apply()

    elif command == "rollback":
        return cmd_rollback()

    elif command in ("-h", "--help", "help"):
        print_usage()
        return 0

    else:
        print(f"Unknown command: {command}")
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
