# RAG Memory Web - Setup Guide

## Fresh Setup (Brand New Developer)

You just cloned the repo. Here's what you run:

```bash
# 1. Create backend/.env with your API keys
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY

# 2. One-time setup (creates database, migrations, schema, optional seed data)
python manage.py setup --seed

# 3. Start services
python manage.py start
```

That's it. Visit http://localhost:5173

## Daily Development

```bash
# Start services (after setup is done once)
python manage.py start

# Stop services
python manage.py stop

# Restart services (no migrations, no seeding)
python manage.py restart

# View logs
python manage.py logs

# Check status
python manage.py status
```

## Making Database Schema Changes

```bash
# 1. Edit models in backend/app/rag/models.py

# 2. Generate migration
cd backend
alembic revision --autogenerate -m "add_user_table"

# 3. Review the generated migration file in backend/alembic/versions/

# 4. Apply the migration
cd ..
python manage.py migrate

# 5. Restart backend to pick up changes
python manage.py restart
```

## Maintenance Commands

```bash
# Run pending migrations only
python manage.py migrate

# Seed or re-seed starter prompts data
python manage.py seed
python manage.py seed --clear  # Clear first, then seed
```

## Complete Reset (Nuclear Option)

Start over from pristine state:

```bash
# 1. Stop everything
python manage.py stop

# 2. Delete ALL artifacts
docker-compose -f docker-compose.web.yml down -v
rm -f .service-state.json .service-pids.json
rm -f backend.log frontend.log

# 3. Run setup again
python manage.py setup --seed
```

## What Each Command Does

**`python manage.py setup [--seed]`** - ONE-TIME initialization:
- Installs dependencies (uv sync)
- Allocates and configures ports
- Starts database container
- Auto-generates initial Alembic migration (if none exists)
- Runs migrations (creates our app tables)
- Sets up LangGraph checkpoint tables
- Optionally seeds starter prompts data (--seed flag)
- Installs frontend dependencies

**`python manage.py start`** - RECURRING (daily use):
- Starts database container (if not running)
- Starts backend process
- Starts frontend process
- NO migrations, NO seeding - just starts services

**`python manage.py stop`** - Stop all services

**`python manage.py restart`** - Stop then start (NO migrations, NO seeding)

**`python manage.py migrate`** - MAINTENANCE:
- Runs pending Alembic migrations only
- Use after creating new migration files

**`python manage.py seed [--clear]`** - MAINTENANCE:
- Seeds or re-seeds starter prompts data
- Use --clear to wipe and re-seed

## Architecture

**Our App Schema** (Alembic manages):
- conversations
- messages
- starter_prompts
- alembic_version (Alembic's tracking table)

**LangGraph Schema** (AsyncPostgresSaver manages via script):
- checkpoints
- checkpoint_writes
- checkpoint_blobs
- checkpoint_migrations

**Migration Files:**
- `backend/alembic/versions/` - All migration files
- Auto-generated on first setup if directory is empty
- New migrations created with: `alembic revision --autogenerate -m "description"`

**State Files (gitignored):**
- `.service-state.json` - Port allocations and setup completion flag
- `.service-pids.json` - Running process IDs
- Safe to delete anytime (forces fresh setup)
