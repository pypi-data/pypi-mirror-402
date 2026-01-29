#!/usr/bin/env python3
"""
RAG Memory Instance Teardown Script

Completely removes RAG Memory instances and optionally the entire config directory.

Usage:
    python scripts/teardown.py <instance-name>     # Remove single instance
    python scripts/teardown.py --all               # Remove ALL instances
    python scripts/teardown.py --nuke              # Nuclear option: remove EVERYTHING

What gets removed per instance:
1. Docker containers (postgres, neo4j, mcp server, backup)
2. Docker volumes (THIS DELETES ALL DATA)
3. Instance entry from config.yaml
4. Instance entry from instances.json
5. Backup directory for the instance

What --nuke additionally removes:
6. Shared config files (docker-compose.yml, .env, init.sql, etc.)
7. The entire config directory (~/.config/rag-memory or equivalent)
8. Docker images (optional)

Safety features:
- Requires explicit confirmation before data deletion
- Shows exactly what will be deleted before proceeding
- Last instance teardown offers to nuke entire config directory

CRITICAL: Container naming convention is rag-memory-mcp-{service}-{instance}
This prevents accidental deletion of non-MCP containers like rag-memory-web-*
"""

import argparse
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from typing import Tuple, List, Optional, Set


class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def run_command(cmd: list, check: bool = True, timeout: int = None) -> Tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def get_config_dir() -> Path:
    """Get the RAG Memory config directory (OS-specific)"""
    import platformdirs
    return Path(platformdirs.user_config_dir('rag-memory', appauthor=False))


def load_instances_json(config_dir: Path) -> dict:
    """Load instances.json registry"""
    instances_file = config_dir / 'instances.json'
    if not instances_file.exists():
        return {"version": 1, "instances": []}

    with open(instances_file, 'r') as f:
        return json.load(f)


def save_instances_json(config_dir: Path, data: dict):
    """Save instances.json registry"""
    instances_file = config_dir / 'instances.json'
    with open(instances_file, 'w') as f:
        json.dump(data, f, indent=2)


def load_config_yaml(config_dir: Path) -> dict:
    """Load config.yaml"""
    import yaml
    config_file = config_dir / 'config.yaml'
    if not config_file.exists():
        return {"instances": {}}

    with open(config_file, 'r') as f:
        return yaml.safe_load(f) or {"instances": {}}


def save_config_yaml(config_dir: Path, data: dict):
    """Save config.yaml"""
    import yaml
    config_file = config_dir / 'config.yaml'

    config_header = """# RAG Memory Configuration
# =============================================================================
# Multi-instance configuration file. Each instance has its own complete
# configuration including API keys, database connections, mounts, and settings.
#
# Structure:
#   instances:
#     instance-name:
#       openai_api_key: "sk-..."
#       database_url: "postgresql://..."
#       neo4j_uri: "bolt://..."
#       mounts:
#         - path: /path/to/directory
#           read_only: true
#       ... other settings ...
# =============================================================================

"""
    with open(config_file, 'w') as f:
        f.write(config_header)
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get_instance_containers_new_naming(instance_name: str) -> List[str]:
    """Get container names using NEW naming convention: rag-memory-mcp-{service}-{instance}

    CRITICAL: This is the correct naming convention that distinguishes MCP stack
    containers from other rag-memory containers.
    """
    return [
        f"rag-memory-mcp-postgres-{instance_name}",
        f"rag-memory-mcp-neo4j-{instance_name}",
        f"rag-memory-mcp-server-{instance_name}",
        f"rag-memory-mcp-backup-{instance_name}",
    ]


def get_instance_containers_old_naming(instance_name: str) -> List[str]:
    """Get container names using OLD naming convention: rag-memory-{service}-{instance}

    These are LEGACY containers from before the naming convention fix.
    This function exists to help clean up old deployments.
    """
    return [
        f"rag-memory-postgres-{instance_name}",
        f"rag-memory-neo4j-{instance_name}",
        f"rag-memory-mcp-{instance_name}",  # Old MCP naming (without 'server')
        f"rag-memory-backup-{instance_name}",
    ]


def get_instance_volumes_new_naming(instance_name: str) -> List[str]:
    """Get volume names using NEW naming convention: rag-memory-mcp-{instance}_{volume}

    The project name prefix (rag-memory-mcp-{instance}) is set in docker-compose.
    """
    return [
        f"rag-memory-mcp-{instance_name}_postgres_data",
        f"rag-memory-mcp-{instance_name}_neo4j_data",
        f"rag-memory-mcp-{instance_name}_neo4j_logs",
    ]


def get_instance_volumes_old_naming(instance_name: str) -> List[str]:
    """Get volume names using OLD naming convention.

    These are LEGACY volumes from before the naming convention fix.
    """
    # Old volumes used different project name patterns
    return [
        f"rag-memory-{instance_name}_postgres_data",
        f"rag-memory-{instance_name}_neo4j_data",
        f"rag-memory-{instance_name}_neo4j_logs",
        # Also check for compose/ prefix pattern
        f"compose_postgres_data",
        f"compose_neo4j_data",
        f"compose_neo4j_logs",
    ]


def check_containers_exist(instance_name: str) -> List[str]:
    """Check which containers exist for this instance (both old and new naming)"""
    existing = []

    # Check both old and new naming conventions
    expected = (
        get_instance_containers_new_naming(instance_name) +
        get_instance_containers_old_naming(instance_name)
    )

    for container in expected:
        code, stdout, _ = run_command([
            "docker", "ps", "-a", "--filter", f"name=^{container}$",
            "--format", "{{.Names}}"
        ])
        if code == 0 and container in stdout:
            existing.append(container)

    return existing


def check_volumes_exist(instance_name: str) -> List[str]:
    """Check which volumes exist for this instance (both old and new naming)"""
    existing = []

    # Check both old and new naming conventions
    expected = (
        get_instance_volumes_new_naming(instance_name) +
        get_instance_volumes_old_naming(instance_name)
    )

    code, stdout, _ = run_command(["docker", "volume", "ls", "--format", "{{.Name}}"])
    if code == 0:
        volume_list = stdout.strip().split('\n')
        for volume in expected:
            if volume in volume_list:
                existing.append(volume)

    return existing


def discover_all_mcp_containers() -> Set[str]:
    """Discover ALL RAG Memory MCP containers (both old and new naming).

    Returns set of instance names found from container names.
    """
    instances = set()

    # Get all rag-memory containers
    code, stdout, _ = run_command([
        "docker", "ps", "-a", "--filter", "name=rag-memory",
        "--format", "{{.Names}}"
    ])

    if code != 0 or not stdout.strip():
        return instances

    for container in stdout.strip().split('\n'):
        if not container:
            continue

        parts = container.split('-')

        # NEW naming: rag-memory-mcp-{service}-{instance}
        # e.g., rag-memory-mcp-postgres-primary -> instance = primary
        if len(parts) >= 5 and parts[0:3] == ['rag', 'memory', 'mcp']:
            instance_name = '-'.join(parts[4:])  # Handle instance names with hyphens
            instances.add(instance_name)

        # OLD naming: rag-memory-{service}-{instance}
        # e.g., rag-memory-postgres-primary -> instance = primary
        elif len(parts) >= 4 and parts[0:2] == ['rag', 'memory']:
            # Skip if it matches new pattern (already handled above)
            if parts[2] == 'mcp':
                continue
            # Service is parts[2], instance is everything after
            instance_name = '-'.join(parts[3:])
            instances.add(instance_name)

    return instances


def discover_all_mcp_volumes() -> Set[str]:
    """Discover ALL RAG Memory MCP volumes (both old and new naming).

    Returns set of instance names found from volume names.
    """
    instances = set()

    code, stdout, _ = run_command([
        "docker", "volume", "ls", "--filter", "name=rag-memory",
        "--format", "{{.Name}}"
    ])

    if code != 0 or not stdout.strip():
        return instances

    for volume in stdout.strip().split('\n'):
        if not volume:
            continue

        # NEW naming: rag-memory-mcp-{instance}_{volume_type}
        if volume.startswith('rag-memory-mcp-') and '_' in volume:
            # e.g., rag-memory-mcp-primary_postgres_data
            prefix = volume.split('_')[0]  # rag-memory-mcp-primary
            instance_name = prefix.replace('rag-memory-mcp-', '')
            if instance_name:
                instances.add(instance_name)

        # OLD naming: rag-memory-{instance}_{volume_type}
        elif volume.startswith('rag-memory-') and '_' in volume:
            prefix = volume.split('_')[0]  # rag-memory-primary
            instance_name = prefix.replace('rag-memory-', '')
            # Skip 'mcp' since that's part of new naming
            if instance_name and instance_name != 'mcp':
                instances.add(instance_name)

    return instances


def stop_and_remove_containers(containers: List[str]) -> bool:
    """Stop and remove Docker containers"""
    success = True

    for container in containers:
        # Stop container
        print_info(f"Stopping {container}...")
        code, _, stderr = run_command(["docker", "stop", container], timeout=30)
        if code != 0 and "No such container" not in stderr:
            print_warning(f"Could not stop {container}: {stderr}")

        # Remove container
        print_info(f"Removing {container}...")
        code, _, stderr = run_command(["docker", "rm", container], timeout=30)
        if code != 0 and "No such container" not in stderr:
            print_error(f"Failed to remove {container}: {stderr}")
            success = False
        else:
            print_success(f"Removed {container}")

    return success


def remove_volumes(volumes: List[str]) -> bool:
    """Remove Docker volumes"""
    success = True

    for volume in volumes:
        print_info(f"Removing volume {volume}...")
        code, _, stderr = run_command(["docker", "volume", "rm", volume], timeout=30)
        if code != 0:
            if "No such volume" in stderr:
                print_info(f"Volume {volume} already removed")
            else:
                print_error(f"Failed to remove {volume}: {stderr}")
                success = False
        else:
            print_success(f"Removed volume {volume}")

    return success


def remove_from_instances_json(config_dir: Path, instance_name: str) -> bool:
    """Remove instance from instances.json registry"""
    try:
        data = load_instances_json(config_dir)
        original_count = len(data.get('instances', []))

        data['instances'] = [
            inst for inst in data.get('instances', [])
            if inst.get('name') != instance_name
        ]

        if len(data['instances']) < original_count:
            save_instances_json(config_dir, data)
            print_success(f"Removed '{instance_name}' from instances.json")
            return True
        else:
            print_info(f"Instance '{instance_name}' not found in instances.json")
            return True
    except Exception as e:
        print_error(f"Failed to update instances.json: {e}")
        return False


def remove_from_config_yaml(config_dir: Path, instance_name: str) -> bool:
    """Remove instance from config.yaml"""
    try:
        data = load_config_yaml(config_dir)

        if instance_name in data.get('instances', {}):
            del data['instances'][instance_name]
            save_config_yaml(config_dir, data)
            print_success(f"Removed '{instance_name}' from config.yaml")
            return True
        else:
            print_info(f"Instance '{instance_name}' not found in config.yaml")
            return True
    except Exception as e:
        print_error(f"Failed to update config.yaml: {e}")
        return False


def remove_backup_directory(config_dir: Path, instance_name: str) -> bool:
    """Remove backup directory for instance"""
    backup_dir = config_dir / 'backups' / instance_name

    if not backup_dir.exists():
        print_info(f"Backup directory does not exist: {backup_dir}")
        return True

    try:
        shutil.rmtree(backup_dir)
        print_success(f"Removed backup directory: {backup_dir}")
        return True
    except Exception as e:
        print_error(f"Failed to remove backup directory: {e}")
        return False


def remove_config_directory(config_dir: Path) -> bool:
    """Remove the entire config directory - NUCLEAR OPTION"""
    if not config_dir.exists():
        print_info(f"Config directory does not exist: {config_dir}")
        return True

    try:
        shutil.rmtree(config_dir)
        print_success(f"Removed entire config directory: {config_dir}")
        return True
    except Exception as e:
        print_error(f"Failed to remove config directory: {e}")
        return False


def remove_docker_images() -> bool:
    """Remove RAG Memory Docker images"""
    print_info("Checking for RAG Memory Docker images...")

    code, stdout, _ = run_command([
        "docker", "images", "--filter", "reference=rag-memory*",
        "--format", "{{.ID}} {{.Repository}}:{{.Tag}}"
    ])

    if code != 0 or not stdout.strip():
        print_info("No RAG Memory images found")
        return True

    images = stdout.strip().split('\n')
    success = True

    for image_line in images:
        if not image_line:
            continue
        parts = image_line.split(' ', 1)
        image_id = parts[0]
        image_name = parts[1] if len(parts) > 1 else image_id

        print_info(f"Removing image {image_name}...")
        code, _, stderr = run_command(["docker", "rmi", "-f", image_id])
        if code != 0:
            print_warning(f"Could not remove image {image_name}: {stderr}")
            success = False
        else:
            print_success(f"Removed image {image_name}")

    return success


def instance_exists(config_dir: Path, instance_name: str) -> bool:
    """Check if instance exists in registry, config, or as containers"""
    # Check instances.json
    data = load_instances_json(config_dir)
    for inst in data.get('instances', []):
        if inst.get('name') == instance_name:
            return True

    # Check config.yaml
    config = load_config_yaml(config_dir)
    if instance_name in config.get('instances', {}):
        return True

    # Check for containers (both old and new naming)
    containers = check_containers_exist(instance_name)
    if containers:
        return True

    return False


def get_all_instances(config_dir: Path) -> List[str]:
    """Get all known instance names from all sources"""
    instances = set()

    # From instances.json
    data = load_instances_json(config_dir)
    for inst in data.get('instances', []):
        if inst.get('name'):
            instances.add(inst.get('name'))

    # From config.yaml
    config = load_config_yaml(config_dir)
    for name in config.get('instances', {}).keys():
        instances.add(name)

    # From Docker containers (both old and new naming)
    instances.update(discover_all_mcp_containers())

    # From Docker volumes (both old and new naming)
    instances.update(discover_all_mcp_volumes())

    return list(instances)


def teardown_single_instance(instance_name: str, config_dir: Path, skip_confirm: bool = False) -> bool:
    """Tear down a single instance. Returns True if successful."""

    # Check what exists
    containers = check_containers_exist(instance_name)
    volumes = check_volumes_exist(instance_name)
    backup_dir = config_dir / 'backups' / instance_name
    backup_exists = backup_dir.exists()

    print(f"\n{Colors.BOLD}Instance: {instance_name}{Colors.RESET}\n")

    print(f"{Colors.YELLOW}Docker Containers:{Colors.RESET}")
    if containers:
        for c in containers:
            print(f"  • {c}")
    else:
        print("  (none found)")

    print(f"\n{Colors.RED}{Colors.BOLD}Docker Volumes (DATA WILL BE LOST):{Colors.RESET}")
    if volumes:
        for v in volumes:
            print(f"  • {v}")
    else:
        print("  (none found)")

    if backup_exists:
        backup_files = list(backup_dir.glob('*.tar.gz'))
        print(f"\n{Colors.YELLOW}Backup Directory:{Colors.RESET}")
        print(f"  • {backup_dir} ({len(backup_files)} backup files)")

    # Confirm if not skipping
    if not skip_confirm:
        print()
        confirm = input(f"{Colors.CYAN}Type '{instance_name}' to confirm: {Colors.RESET}").strip()
        if confirm != instance_name:
            print_error("Confirmation did not match. Skipping this instance.")
            return False

    # Remove containers
    if containers:
        stop_and_remove_containers(containers)

    # Remove volumes
    if volumes:
        remove_volumes(volumes)

    # Remove from config files
    remove_from_instances_json(config_dir, instance_name)
    remove_from_config_yaml(config_dir, instance_name)

    # Remove backup directory
    if backup_exists:
        remove_backup_directory(config_dir, instance_name)

    print_success(f"Instance '{instance_name}' removed")
    return True


def teardown_all_instances(config_dir: Path) -> bool:
    """Tear down ALL instances. Returns True if successful."""
    all_instances = get_all_instances(config_dir)

    if not all_instances:
        print_info("No instances found")
        return True

    print_header("TEARDOWN ALL INSTANCES")

    print(f"{Colors.RED}{Colors.BOLD}The following instances will be PERMANENTLY DELETED:{Colors.RESET}\n")
    for inst in sorted(all_instances):
        print(f"  • {inst}")

    print()
    print(f"{Colors.RED}{Colors.BOLD}⚠  THIS WILL DELETE ALL DATA IN ALL INSTANCES  ⚠{Colors.RESET}")
    print()

    confirm = input(f"{Colors.CYAN}Type 'DELETE ALL' to confirm: {Colors.RESET}").strip()
    if confirm != "DELETE ALL":
        print_error("Confirmation did not match. Aborting.")
        return False

    print()

    # Tear down each instance
    for instance_name in sorted(all_instances):
        print_header(f"Removing: {instance_name}")
        teardown_single_instance(instance_name, config_dir, skip_confirm=True)

    return True


def nuke_everything(config_dir: Path) -> bool:
    """Nuclear option: remove EVERYTHING including config directory."""

    print_header("NUCLEAR TEARDOWN - REMOVE EVERYTHING")

    all_instances = get_all_instances(config_dir)

    print(f"{Colors.RED}{Colors.BOLD}This will PERMANENTLY DELETE:{Colors.RESET}\n")

    if all_instances:
        print(f"{Colors.YELLOW}All instances:{Colors.RESET}")
        for inst in sorted(all_instances):
            print(f"  • {inst}")

    print(f"\n{Colors.YELLOW}Config directory:{Colors.RESET}")
    print(f"  • {config_dir}")
    if config_dir.exists():
        # List contents
        for item in sorted(config_dir.iterdir()):
            if item.is_dir():
                print(f"    └── {item.name}/")
            else:
                print(f"    └── {item.name}")

    print(f"\n{Colors.YELLOW}Docker images (optional):{Colors.RESET}")
    code, stdout, _ = run_command([
        "docker", "images", "--filter", "reference=rag-memory*",
        "--format", "  • {{.Repository}}:{{.Tag}}"
    ])
    if code == 0 and stdout.strip():
        print(stdout.strip())
    else:
        print("  (none found)")

    print()
    print(f"{Colors.RED}{Colors.BOLD}⚠  THIS CANNOT BE UNDONE - ALL DATA WILL BE LOST  ⚠{Colors.RESET}")
    print()

    confirm = input(f"{Colors.CYAN}Type 'NUKE EVERYTHING' to confirm: {Colors.RESET}").strip()
    if confirm != "NUKE EVERYTHING":
        print_error("Confirmation did not match. Aborting.")
        return False

    print()

    # Step 1: Tear down all instances
    if all_instances:
        print_header("Step 1: Removing All Instances")
        for instance_name in sorted(all_instances):
            teardown_single_instance(instance_name, config_dir, skip_confirm=True)
    else:
        print_header("Step 1: No Instances to Remove")
        print_info("No instances found")

    # Step 2: Remove config directory
    print_header("Step 2: Removing Config Directory")
    remove_config_directory(config_dir)

    # Step 3: Ask about Docker images
    print_header("Step 3: Docker Images")
    remove_images = input(
        f"{Colors.CYAN}Also remove Docker images? (yes/no, default: no): {Colors.RESET}"
    ).strip().lower()

    if remove_images == 'yes':
        remove_docker_images()
    else:
        print_info("Keeping Docker images")

    print_header("Nuclear Teardown Complete")
    print_success("All RAG Memory data has been removed")
    print_info("Run 'python scripts/setup.py' to start fresh")

    return True


def main():
    """Main teardown flow"""
    parser = argparse.ArgumentParser(
        description="RAG Memory Instance Teardown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/teardown.py primary           # Remove single instance
  python scripts/teardown.py --all             # Remove ALL instances
  python scripts/teardown.py --nuke            # Nuclear: remove EVERYTHING
  python scripts/teardown.py --list            # List all instances
"""
    )

    parser.add_argument(
        'instance',
        nargs='?',
        help="Instance name to tear down"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Tear down ALL instances"
    )
    parser.add_argument(
        '--nuke',
        action='store_true',
        help="Nuclear option: remove EVERYTHING including config directory"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="List all instances without removing anything"
    )

    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{Colors.RED}RAG Memory Teardown{Colors.RESET}\n")

    config_dir = get_config_dir()

    # List mode
    if args.list:
        instances = get_all_instances(config_dir)
        if instances:
            print_info("Available instances:")
            for inst in sorted(instances):
                print(f"  • {inst}")
        else:
            print_info("No instances found")
        print()
        print_info(f"Config directory: {config_dir}")
        return

    # Nuclear mode
    if args.nuke:
        if not nuke_everything(config_dir):
            sys.exit(1)
        return

    # All instances mode
    if args.all:
        if not teardown_all_instances(config_dir):
            sys.exit(1)

        # After removing all instances, offer to nuke config directory
        print()
        remaining = get_all_instances(config_dir)
        if not remaining:
            nuke_config = input(
                f"{Colors.CYAN}All instances removed. Delete config directory too? (yes/no, default: no): {Colors.RESET}"
            ).strip().lower()

            if nuke_config == 'yes':
                print_header("Removing Config Directory")
                remove_config_directory(config_dir)

        return

    # Single instance mode
    if not args.instance:
        print_error("Usage: python scripts/teardown.py <instance-name>")
        print_info("       python scripts/teardown.py --all")
        print_info("       python scripts/teardown.py --nuke")
        print_info("       python scripts/teardown.py --list")
        print()

        instances = get_all_instances(config_dir)
        if instances:
            print_info("Available instances:")
            for inst in sorted(instances):
                print(f"  • {inst}")
        sys.exit(1)

    instance_name = args.instance

    # Verify instance exists
    if not instance_exists(config_dir, instance_name):
        print_error(f"Instance '{instance_name}' does not exist")
        print()
        instances = get_all_instances(config_dir)
        if instances:
            print_info("Available instances:")
            for inst in sorted(instances):
                print(f"  • {inst}")
        sys.exit(1)

    # Check if this is the last instance
    all_instances = get_all_instances(config_dir)
    is_last_instance = len(all_instances) == 1 and instance_name in all_instances

    print_header(f"TEARDOWN: {instance_name}")

    if is_last_instance:
        print_warning("This is your LAST instance!")
        print_warning("Deleting it will leave you with no RAG Memory instances.")
        print()

    print(f"{Colors.RED}{Colors.BOLD}⚠  THIS ACTION CANNOT BE UNDONE  ⚠{Colors.RESET}")
    print(f"{Colors.RED}All data in PostgreSQL and Neo4j for this instance will be lost!{Colors.RESET}")
    print()

    # Tear down the instance
    if not teardown_single_instance(instance_name, config_dir):
        sys.exit(1)

    # Summary
    print_header("Teardown Complete")

    remaining = get_all_instances(config_dir)
    if remaining:
        print_info("Remaining instances:")
        for inst in sorted(remaining):
            print(f"  • {inst}")
    else:
        print_info("No instances remaining")
        print()

        # Offer to nuke config directory
        nuke_config = input(
            f"{Colors.CYAN}Delete config directory too? (yes/no, default: no): {Colors.RESET}"
        ).strip().lower()

        if nuke_config == 'yes':
            print_header("Removing Config Directory")
            remove_config_directory(config_dir)
            print()
            print_info("Run 'python scripts/setup.py' to start fresh")
        else:
            print_info("Config directory preserved (contains empty config files)")
            print_info("Run 'python scripts/teardown.py --nuke' to remove everything")
            print_info("Run 'python scripts/setup.py' to create a new instance")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nTeardown cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
