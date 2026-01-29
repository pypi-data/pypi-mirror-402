#!/usr/bin/env python3
"""
RAG Memory Web - Production Process Management Script
Handles port discovery, configuration, service orchestration, and health checks.

Commands:
  setup [--seed]  - One-time initialization (dependencies, database, migrations, optional seed data)
  start           - Start services only (requires setup to be done first)
  stop            - Stop all services
  restart         - Stop and start services (no migrations, no seeding)
  migrate         - Run pending Alembic migrations
  seed [--clear]  - Seed or re-seed starter prompts data
  status          - Show service status
  logs            - Tail all log files
"""

import os
import sys
import subprocess
import signal
import time
import json
import socket
from pathlib import Path
from typing import Dict, Optional, List


# State file for port allocation
STATE_FILE = Path(".service-state.json")
PID_FILE = Path(".service-pids.json")


def find_free_port(start_port: int, exclude_ports: List[int] = None) -> int:
    """Find a free port starting from start_port."""
    exclude_ports = exclude_ports or []
    port = start_port
    while port < start_port + 100:  # Try 100 ports
        if port in exclude_ports:
            port += 1
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError(f"Could not find free port starting from {start_port}")


def check_port_in_use(port: int) -> bool:
    """Check if a port is currently in use (tries both IPv4 and IPv6)."""
    # Try IPv4 first
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # 1 second timeout to avoid blocking
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
    except:
        pass

    # Try IPv6
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # 1 second timeout to avoid blocking
            if s.connect_ex(("::1", port)) == 0:
                return True
    except:
        pass

    return False


def load_state() -> Dict:
    """Load service state (ports and config)."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: Dict):
    """Save service state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_pids() -> Dict:
    """Load process PIDs."""
    if PID_FILE.exists():
        with open(PID_FILE) as f:
            return json.load(f)
    return {}


def save_pids(pids: Dict):
    """Save process PIDs."""
    with open(PID_FILE, "w") as f:
        json.dump(pids, f, indent=2)


def allocate_ports() -> Dict[str, int]:
    """Allocate ports for web app services only."""
    print("🔍 Finding free ports...")

    allocated = []
    ports = {}

    # Only allocate ports for web app services (not RAG Memory)
    port_configs = [
        ("BACKEND_PORT", 8000),
        ("FRONTEND_PORT", 5173),
        ("WEB_POSTGRES_PORT", 5433),
    ]

    for name, preferred_port in port_configs:
        port = find_free_port(preferred_port, exclude_ports=allocated)
        ports[name] = port
        allocated.append(port)
        if port != preferred_port:
            print(f"  {name}: {preferred_port} in use, using {port} instead")
        else:
            print(f"  {name}: {port} ✓")

    return ports


def update_backend_env(ports: Dict[str, int]):
    """Update backend/.env with correct ports and CORS origins (preserves exact formatting)."""
    backend_env = Path("backend/.env")

    if not backend_env.exists():
        print(f"⚠️  backend/.env not found - skipping update")
        return

    # Variables we need to update
    updates = {
        "DATABASE_URL": f"postgresql+asyncpg://postgres:postgres@localhost:{ports['WEB_POSTGRES_PORT']}/rag_memory_web",
        "HOST": "0.0.0.0",
        "PORT": str(ports["BACKEND_PORT"]),
        "CORS_ORIGINS": f"http://localhost:{ports['FRONTEND_PORT']}"
    }

    # Read file, update only the specific variables, preserve everything else
    lines = []
    with open(backend_env) as f:
        for line in f:
            line_stripped = line.strip()

            # Check if this line is one of our target variables
            if "=" in line_stripped and not line_stripped.startswith("#"):
                key = line_stripped.split("=", 1)[0].strip()
                if key in updates:
                    # Replace just this variable's value, preserve formatting
                    lines.append(f"{key}={updates[key]}\n")
                    continue

            # Keep line exactly as-is (comments, blank lines, other variables)
            lines.append(line)

    # Write back with exact formatting preserved
    with open(backend_env, "w") as f:
        f.writelines(lines)

    print(f"✓ Updated backend/.env (DATABASE_URL, HOST, PORT, CORS_ORIGINS only - formatting preserved)")


def update_frontend_env(ports: Dict[str, int]):
    """Update frontend/.env with correct API URL."""
    frontend_env = Path("frontend/.env")

    with open(frontend_env, "w") as f:
        f.write("# Auto-generated by manage.py - DO NOT EDIT MANUALLY\n")
        f.write(f"VITE_API_URL=http://localhost:{ports['BACKEND_PORT']}\n")

    print(f"✓ Updated frontend/.env with API URL")


def update_docker_compose_ports(ports: Dict[str, int]):
    """Update docker-compose.web.yml with correct port mappings."""
    import re
    web_compose_file = Path("docker-compose.web.yml")
    if web_compose_file.exists():
        content = web_compose_file.read_text()
        # Update PostgreSQL port using regex to match any existing port
        content = re.sub(
            r'- "\d+:5432"',
            f'- "{ports["WEB_POSTGRES_PORT"]}:5432"',
            content
        )
        web_compose_file.write_text(content)
        print(f"✓ Updated docker-compose.web.yml with port {ports['WEB_POSTGRES_PORT']}")
    else:
        print(f"⚠️  docker-compose.web.yml not found")


def check_mcp_server() -> bool:
    """Check if MCP server from mcp.json is reachable."""
    mcp_config_file = Path("backend/mcp.json")
    if not mcp_config_file.exists():
        print("⚠️  backend/mcp.json not found - cannot verify MCP server")
        return False

    try:
        with open(mcp_config_file) as f:
            mcp_config = json.load(f)

        mcp_url = mcp_config.get("rag_memory", {}).get("url")
        if not mcp_url:
            print("⚠️  No MCP server URL found in mcp.json")
            return False

        # Extract host and port from URL
        import urllib.parse
        parsed = urllib.parse.urlparse(mcp_url)
        host = parsed.hostname or "localhost"
        port = parsed.port

        if not port:
            print(f"⚠️  Could not determine port from {mcp_url}")
            return False

        # Check if port is reachable (socket-level check, no HTTP protocol issues)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((host, port))
            print(f"✓ MCP server reachable at {mcp_url}")
            return True
        except Exception as e:
            print(f"⚠️  MCP server at {mcp_url} is not reachable: {e}")
            print("   The web app will start but won't be able to use RAG features")
            return False
    except Exception as e:
        print(f"⚠️  Error checking MCP server: {e}")
        return False


def run_command(cmd: str, cwd=None, capture=False) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    if capture:
        return subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
    else:
        return subprocess.run(cmd, shell=True, cwd=cwd)


def start_service_background(name: str, cmd: str, log_file: str, cwd=None) -> int:
    """Start a service in background and return PID."""
    log_path = Path(log_file)
    process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=open(log_path, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(f"  Started {name} (PID: {process.pid})")
    return process.pid


def verify_docker_container(container_name: str, max_retries: int = 30) -> bool:
    """Verify a Docker container is healthy."""
    print(f"  Verifying {container_name}...", end="", flush=True)
    for i in range(max_retries):
        result = subprocess.run(
            f"docker inspect --format='{{{{.State.Health.Status}}}}' {container_name}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and "healthy" in result.stdout:
            print(f" ✓ (took {i+1}s)")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    print(f" ✗ FAILED")
    return False


def verify_service(name: str, port: int, max_retries: int = 30) -> bool:
    """Verify a service is responding on its port."""
    print(f"  Verifying {name} on port {port}...", end="", flush=True)
    for i in range(max_retries):
        if check_port_in_use(port):
            print(f" ✓ (took {i+1}s)")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    print(f" ✗ FAILED")
    return False


def kill_process_on_port(port: int) -> bool:
    """Find and kill any process using the specified port."""
    # Use lsof to find process using port
    result = subprocess.run(
        f"lsof -ti tcp:{port}",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and result.stdout.strip():
        pids = result.stdout.strip().split('\n')
        for pid_str in pids:
            try:
                pid = int(pid_str)
                print(f"  Found stale process {pid} on port {port}, killing...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            except (ValueError, ProcessLookupError):
                pass
        return True
    return False


def setup(seed_data: bool = False):
    """
    ONE-TIME SETUP: Initialize environment for first use.

    This command:
    - Installs dependencies (uv sync)
    - Allocates and configures ports
    - Starts database container
    - Runs Alembic migrations (our app schema)
    - Runs LangGraph schema setup
    - Optionally seeds starter prompts (--seed flag)

    Run this once when first setting up the project.
    """
    print("=" * 60)
    print("🔧 RAG Memory Web - One-Time Setup")
    print("=" * 60)

    # Allocate ports
    ports = allocate_ports()
    save_state({"ports": ports})

    # Update configuration files
    print("\n📝 Updating configuration files...")
    update_backend_env(ports)
    update_frontend_env(ports)
    update_docker_compose_ports(ports)

    # Check MCP server (warn if unreachable but continue)
    print("\n🔌 Checking RAG Memory MCP server...")
    check_mcp_server()  # Just warns, doesn't block

    # Start web app PostgreSQL
    print("\n🐳 Starting web app database...")
    run_command("docker-compose -f docker-compose.web.yml down", capture=False)
    time.sleep(1)
    run_command("docker-compose -f docker-compose.web.yml up -d")

    # Verify web PostgreSQL using container health check
    if not verify_docker_container("rag-memory-web-postgres"):
        print("❌ Web PostgreSQL failed to start or become healthy")
        print("   Check: docker logs rag-memory-web-postgres")
        sys.exit(1)

    # Install dependencies using uv (from pyproject.toml)
    print("\n⚙️  Installing dependencies...")
    root_venv = Path(".venv")
    if not root_venv.exists() or not (root_venv / "lib").exists():
        print("  Running uv sync...")
        result = run_command("uv sync", capture=True)
        if result.returncode != 0:
            print(f"❌ Failed to install dependencies:")
            print(result.stderr)
            sys.exit(1)
        print("  ✓ Dependencies installed")
    else:
        print("  ✓ Dependencies already installed")

    # Run database migrations (our app schema)
    print("\n📊 Setting up database schema...")

    # Check if this is first-time setup (no migration files exist)
    versions_dir = Path("backend/alembic/versions")
    migration_files = [f for f in versions_dir.glob("*.py") if f.name != "__pycache__"]

    if not migration_files:
        print("  No migrations found - generating initial schema...")
        result = run_command("alembic revision --autogenerate -m 'initial_schema'", cwd="backend", capture=True)
        if result.returncode != 0:
            print(f"❌ Failed to generate initial migration:")
            print(result.stderr)
            sys.exit(1)
        print("  ✓ Initial migration generated")

    # Apply migrations
    print("  Applying migrations...")
    result = run_command("alembic upgrade head", cwd="backend", capture=True)
    if result.returncode != 0:
        print(f"❌ Failed to run migrations:")
        print(result.stderr)
        sys.exit(1)
    print("  ✓ Database schema up to date")

    # Setup LangGraph database schema (idempotent)
    print("\n🔧 Setting up LangGraph database schema...")
    result = run_command("python scripts/setup_langgraph_schema.py", cwd="backend", capture=True)
    if result.returncode != 0:
        print(f"❌ Failed to setup LangGraph schema:")
        print(result.stderr)
        sys.exit(1)
    print("  ✓ LangGraph checkpoint tables ready")

    # Optionally seed initial data
    if seed_data:
        print("\n🌱 Seeding initial data...")
        result = run_command("python seed_data.py", cwd="backend", capture=True)
        if result.returncode != 0:
            print(f"❌ Failed to seed data:")
            print(result.stderr)
            sys.exit(1)
        print("  ✓ Seed data ready")

    # Install frontend dependencies
    print("\n⚙️  Setting up frontend...")
    frontend_modules = Path("frontend/node_modules")
    if not frontend_modules.exists():
        print("  Installing dependencies...")
        result = run_command("npm install", cwd="frontend", capture=True)
        if result.returncode != 0:
            print(f"❌ Failed to install frontend dependencies:")
            print(result.stderr)
            sys.exit(1)
        print("  ✓ Frontend dependencies installed")
    else:
        print("  ✓ Frontend dependencies already installed")

    # Mark setup as complete
    state = load_state()
    state["setup_complete"] = True
    save_state(state)

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n💡 Next step: python manage.py start")
    print()


def start_all():
    """
    RECURRING: Start all services (requires setup to be done first).

    This command only starts services - no migrations, no seeding.
    Run 'python manage.py setup' first if you haven't already.
    """
    print("=" * 60)
    print("🚀 Starting RAG Memory Web")
    print("=" * 60)

    # Check if setup has been done
    state = load_state()
    if not state.get("setup_complete"):
        print("\n❌ Setup not complete. Run 'python manage.py setup' first")
        sys.exit(1)

    # Check if already running
    pids = load_pids()
    if pids:
        print("⚠️  Services may already be running. Checking...")
        for name, pid in pids.items():
            try:
                os.kill(pid, 0)
                print(f"  {name} (PID: {pid}) is still running")
                print("\n❌ Use 'python manage.py stop' first or 'python manage.py restart'")
                sys.exit(1)
            except ProcessLookupError:
                pass

    ports = state.get("ports", {})
    if not ports:
        print("\n❌ No port configuration found. Run 'python manage.py setup' first")
        sys.exit(1)

    # Kill any stale processes on our ports (idempotent cleanup)
    print("\n🧹 Cleaning up stale processes...")
    for port_name, port in ports.items():
        if port_name in ["BACKEND_PORT", "FRONTEND_PORT"]:
            kill_process_on_port(port)
    print("  ✓ Ports clean")

    new_pids = {}

    # Start web app PostgreSQL (if not already running)
    print("\n🐳 Starting web app database...")
    result = subprocess.run(
        "docker inspect rag-memory-web-postgres",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        # Container doesn't exist, start it
        run_command("docker-compose -f docker-compose.web.yml up -d")
        if not verify_docker_container("rag-memory-web-postgres"):
            print("❌ Web PostgreSQL failed to start")
            sys.exit(1)
    else:
        print("  ✓ Database already running")

    # Start Backend
    print("\n🔧 Starting Backend...")
    pid = start_service_background(
        "Backend",
        f"uvicorn app.main:app --reload --host 0.0.0.0 --port {ports['BACKEND_PORT']}",
        "backend.log",
        cwd="backend"
    )
    new_pids["backend"] = pid

    if not verify_service("Backend", ports["BACKEND_PORT"]):
        print("❌ Backend failed to start. Check backend.log")
        sys.exit(1)

    # Start Frontend
    print("\n🎨 Starting Frontend...")
    pid = start_service_background(
        "Frontend",
        "npm run dev",
        "frontend.log",
        cwd="frontend"
    )
    new_pids["frontend"] = pid

    if not verify_service("Frontend", ports["FRONTEND_PORT"]):
        print("❌ Frontend failed to start. Check frontend.log")
        sys.exit(1)

    # Save PIDs
    save_pids(new_pids)

    # Success!
    print("\n" + "=" * 60)
    print("✅ All services started successfully!")
    print("=" * 60)
    print(f"\n🌐 Frontend:     http://localhost:{ports['FRONTEND_PORT']}")
    print(f"🔧 Backend:      http://localhost:{ports['BACKEND_PORT']}")
    print(f"📚 API Docs:     http://localhost:{ports['BACKEND_PORT']}/docs")
    print("\n💡 Use 'python manage.py logs' to view logs")
    print("💡 Use 'python manage.py status' to check status")
    print()


def stop_all():
    """Stop all services."""
    print("=" * 60)
    print("🛑 Stopping RAG Memory Web")
    print("=" * 60)

    # Load state to get ports
    state = load_state()
    ports = state.get("ports", {})

    # Stop processes by PID first
    pids = load_pids()
    for name, pid in pids.items():
        print(f"  Stopping {name} (PID: {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            # Wait for graceful shutdown
            time.sleep(1)
            try:
                os.kill(pid, 0)
                # Still running, force kill
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            print(f"    ✓ Stopped")
        except ProcessLookupError:
            print(f"    Already stopped")

    # Kill any remaining processes on our ports (aggressive cleanup)
    if ports:
        print("\n🧹 Cleaning up any remaining processes on ports...")
        for port_name, port in ports.items():
            if port_name in ["BACKEND_PORT", "FRONTEND_PORT"]:
                kill_process_on_port(port)

    # Stop web app Docker service (NOT RAG Memory)
    print("\n  Stopping web app database...")
    run_command("docker-compose -f docker-compose.web.yml down")

    # Clean up PID file
    if PID_FILE.exists():
        PID_FILE.unlink()

    print("\n✅ All services stopped")


def migrate():
    """
    MAINTENANCE: Run pending Alembic migrations.

    Use this when you have new migration files to apply.
    """
    print("=" * 60)
    print("📊 Running Database Migrations")
    print("=" * 60)

    result = run_command("alembic upgrade head", cwd="backend", capture=True)
    if result.returncode != 0:
        print(f"❌ Failed to run migrations:")
        print(result.stderr)
        sys.exit(1)

    print("✅ Database migrations complete")


def seed(clear: bool = False):
    """
    MAINTENANCE: Seed or re-seed starter prompts data.

    Args:
        clear: If True, clears existing data before seeding
    """
    print("=" * 60)
    print("🌱 Seeding Starter Prompts Data")
    print("=" * 60)

    cmd = "python seed_data.py"
    if clear:
        cmd += " --clear"
        print("\n⚠️  Clearing existing data before seeding...")

    result = run_command(cmd, cwd="backend", capture=True)
    if result.returncode != 0:
        print(f"❌ Failed to seed data:")
        print(result.stderr)
        sys.exit(1)

    print("✅ Seed data ready")


def status():
    """Show detailed status of all services."""
    print("=" * 60)
    print("📊 RAG Memory Web - Service Status")
    print("=" * 60)

    state = load_state()
    pids = load_pids()
    ports = state.get("ports", {})

    if not state.get("setup_complete"):
        print("\n⚠️  Setup not complete. Run 'python manage.py setup'")
        return

    if not ports:
        print("\n⚠️  No services configured. Run 'python manage.py setup'")
        return

    print("\n🔌 Port Allocations:")
    for name, port in sorted(ports.items()):
        in_use = "✓" if check_port_in_use(port) else "✗"
        print(f"  {name:20s} {port:5d} {in_use}")

    print("\n🐳 Web App Database:")
    run_command("docker-compose -f docker-compose.web.yml ps")

    print("\n🔧 Web App Processes:")
    for name, pid in pids.items():
        try:
            os.kill(pid, 0)
            port_name = {
                "backend": "BACKEND_PORT",
                "frontend": "FRONTEND_PORT",
            }.get(name)
            port = ports.get(port_name, "?")
            port_status = "✓" if check_port_in_use(port) else "✗"
            print(f"  {name:15s} PID:{pid:6d}  Port:{port:5d} {port_status}")
        except ProcessLookupError:
            print(f"  {name:15s} ✗ Not running (stale PID)")


def logs():
    """Tail all log files."""
    log_files = []
    for log in ["backend.log", "frontend.log"]:
        if Path(log).exists():
            log_files.append(log)

    if log_files:
        print(f"📜 Tailing logs: {', '.join(log_files)}")
        print("   Press Ctrl+C to exit\n")
        subprocess.run(f"tail -f {' '.join(log_files)}", shell=True)
    else:
        print("⚠️  No log files found")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    flags = sys.argv[2:] if len(sys.argv) > 2 else []

    try:
        if command == "setup":
            seed_data = "--seed" in flags
            setup(seed_data=seed_data)
        elif command == "start":
            start_all()
        elif command == "stop":
            stop_all()
        elif command == "restart":
            stop_all()
            time.sleep(2)
            start_all()
        elif command == "migrate":
            migrate()
        elif command == "seed":
            clear = "--clear" in flags
            seed(clear=clear)
        elif command == "status":
            status()
        elif command == "logs":
            logs()
        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
