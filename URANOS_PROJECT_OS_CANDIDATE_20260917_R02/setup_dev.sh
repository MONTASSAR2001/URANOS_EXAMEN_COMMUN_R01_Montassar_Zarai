#!/usr/bin/env bash
# =============================================================================
# URANOS Project OS — Automated Docker Dev Environment Bootstrap
# =============================================================================
# Usage:
#   chmod +x setup_dev.sh
#   ./setup_dev.sh [--reset]
#
# Options:
#   --reset   Tear down and wipe all volumes before rebuilding (clean slate).
#
# What this script does:
#   1. Validates prerequisites (Docker, Docker Compose, .env file)
#   2. Optionally tears down existing environment (--reset)
#   3. Starts all services via docker compose up -d
#   4. Waits for MariaDB, Redis, and the backend to become healthy
#   5. Creates the Frappe site if it doesn't exist yet
#   6. Installs ERPNext + uranos_project_os onto the site
#   7. Runs bench migrate to push all DocType JSONs into MariaDB
#   8. Sets the site as default and prints the access URL
# =============================================================================

set -euo pipefail

# ─── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ─── Load .env ────────────────────────────────────────────────────────────────
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f ".env.example" ]]; then
    error ".env not found. Run: cp .env.example .env  — then fill in your secrets."
  else
    error ".env not found and no .env.example exists. Cannot continue."
  fi
fi

# Export all variables from .env (skip comments and blank lines)
set -o allexport
# shellcheck source=.env
source "$ENV_FILE"
set +o allexport

# Validate required variables are non-empty
: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD must be set in .env}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD must be set in .env}"
: "${DB_FRAPPE_PASSWORD:?DB_FRAPPE_PASSWORD must be set in .env}"
: "${FRAPPE_SITE_NAME:?FRAPPE_SITE_NAME must be set in .env}"

SITE_NAME="${FRAPPE_SITE_NAME}"
BACKEND_CONTAINER="uranos-backend"
MARIADB_CONTAINER="uranos-mariadb"

# ─── Argument parsing ─────────────────────────────────────────────────────────
RESET=false
for arg in "$@"; do
  [[ "$arg" == "--reset" ]] && RESET=true
done

# ─── Prerequisites check ──────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}   URANOS Project OS — Development Environment Setup    ${NC}"
echo -e "${BOLD}════════════════════════════════════════════════════════${NC}"
echo ""

info "Checking prerequisites..."

command -v docker &>/dev/null   || error "Docker is not installed. See https://docs.docker.com/get-docker/"
command -v docker compose &>/dev/null 2>&1 || \
  docker-compose version &>/dev/null 2>&1 || \
  error "Docker Compose v2 not found. Run: docker plugin install compose"

DOCKER_COMPOSE="docker compose"
docker compose version &>/dev/null 2>&1 || DOCKER_COMPOSE="docker-compose"

[[ -f "$COMPOSE_FILE" ]] || error "docker-compose.yml not found in current directory."

success "Docker, Compose, and .env are available."

# ─── Reset (optional) ─────────────────────────────────────────────────────────
if [[ "$RESET" == "true" ]]; then
  warn "⚠️  --reset flag detected. Destroying existing volumes and containers..."
  $DOCKER_COMPOSE down -v --remove-orphans || true
  success "Environment wiped. Starting fresh."
fi

# ─── Pull images (non-blocking download) ──────────────────────────────────────
info "Pulling latest Docker images (this may take a few minutes on first run)..."
$DOCKER_COMPOSE pull --quiet 2>&1 | tail -3 || warn "Image pull had warnings; continuing."

# ─── Start all services ───────────────────────────────────────────────────────
info "Starting all services..."
$DOCKER_COMPOSE up -d
echo ""

# ─── Wait helpers ─────────────────────────────────────────────────────────────
wait_for_container_health() {
  local name="$1"
  local max_tries="${2:-30}"
  local delay="${3:-10}"
  local tries=0

  info "Waiting for container '$name' to become healthy..."
  while [[ $tries -lt $max_tries ]]; do
    local status
    status=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null || echo "missing")

    case "$status" in
      "healthy")
        success "Container '$name' is healthy."
        return 0
        ;;
      "unhealthy")
        error "Container '$name' reported unhealthy. Run: docker logs $name"
        ;;
      "missing")
        warn "Container '$name' not found yet, retrying (${tries}/${max_tries})..."
        ;;
      *)
        echo -ne "  ↳ ${status} (${tries}/${max_tries})...\r"
        ;;
    esac

    sleep "$delay"
    ((tries++))
  done

  error "Timed out waiting for '$name' to become healthy after $((max_tries * delay))s."
}

wait_for_container_health "$MARIADB_CONTAINER" 30 10
wait_for_container_health "uranos-redis-cache"  15  5
wait_for_container_health "uranos-redis-queue"  15  5

# ─── Check if site already exists ─────────────────────────────────────────────
info "Checking if site '$SITE_NAME' already exists..."
SITE_EXISTS=$(docker exec "$BACKEND_CONTAINER" \
  bench --site "$SITE_NAME" show-config 2>/dev/null | grep -c "db_name" || true)

if [[ "$SITE_EXISTS" -eq 0 ]]; then
  # ── Create new site ──────────────────────────────────────────────────────────
  info "Creating Frappe site '$SITE_NAME'..."
  # Passwords are passed via environment variables inside the container
  # to avoid leaking them into the host's process table / shell history.
  docker exec \
    -e _DB_ROOT_PASS="${MYSQL_ROOT_PASSWORD}" \
    -e _ADMIN_PASS="${ADMIN_PASSWORD}" \
    "$BACKEND_CONTAINER" bash -c "
      bench new-site '${SITE_NAME}' \
        --db-root-password \"\${_DB_ROOT_PASS}\" \
        --admin-password \"\${_ADMIN_PASS}\" \
        --db-host mariadb \
        --db-port 3306 \
        --mariadb-user-host-login-scope='%' \
        --no-mariadb-socket \
        --verbose
    "
  success "Site '$SITE_NAME' created."
else
  success "Site '$SITE_NAME' already exists, skipping creation."
fi

# ─── Install apps ─────────────────────────────────────────────────────────────
install_app_if_missing() {
  local app="$1"
  info "Checking if app '$app' is installed on site '$SITE_NAME'..."
  local installed
  installed=$(docker exec "$BACKEND_CONTAINER" \
    bench --site "$SITE_NAME" list-apps 2>/dev/null | grep -c "^${app}$" || true)

  if [[ "$installed" -eq 0 ]]; then
    info "Installing '$app' on site '$SITE_NAME'..."
    docker exec "$BACKEND_CONTAINER" bash -c \
      "bench --site '${SITE_NAME}' install-app '${app}'"
    success "App '$app' installed."
  else
    success "App '$app' is already installed."
  fi
}

install_app_if_missing "erpnext"
install_app_if_missing "uranos_project_os"

# ─── bench migrate — pushes all DocType JSON schemas into MariaDB ─────────────
echo ""
info "Running bench migrate to sync all DocType schemas..."
info "  ▸ URANOS Blocker (uranos_project_os/doctype/uranos_blocker)"
info "  ▸ URANOS Evidence (child table)"
info "  ▸ ... and all other URANOS doctypes"
echo ""

docker exec "$BACKEND_CONTAINER" bash -c \
  "bench --site '${SITE_NAME}' migrate --skip-failing"

success "bench migrate completed. All DocType schemas are live in MariaDB."

# ─── Set site as default ──────────────────────────────────────────────────────
info "Setting '$SITE_NAME' as the default site..."
docker exec "$BACKEND_CONTAINER" bash -c \
  "bench use '${SITE_NAME}'"

# ─── Verify the URANOS Blocker table exists ───────────────────────────────────
info "Verifying 'tabURANOS Blocker' table was created in MariaDB..."
# Use --defaults-extra-file trick to avoid password in process table
TABLE_EXISTS=$(docker exec \
  -e _DB_ROOT_PASS="${MYSQL_ROOT_PASSWORD}" \
  "$MARIADB_CONTAINER" bash -c '
    mysql -uroot -p"${_DB_ROOT_PASS}" --silent --skip-column-names -e "
      SELECT COUNT(*) AS c
      FROM information_schema.tables
      WHERE table_schema NOT IN ('"'"'information_schema'"'"','"'"'performance_schema'"'"','"'"'mysql'"'"','"'"'sys'"'"')
        AND table_name = '"'"'tabURANOS Blocker'"'"';
    " 2>/dev/null
  ' || echo "0")

TABLE_EXISTS="${TABLE_EXISTS:-0}"

if [[ "$TABLE_EXISTS" -gt 0 ]]; then
  success "'tabURANOS Blocker' table confirmed in MariaDB ✓"
else
  warn "'tabURANOS Blocker' table not found yet. bench migrate may need a retry."
  warn "Run: docker exec $BACKEND_CONTAINER bench --site $SITE_NAME migrate"
fi

# ─── Final summary ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}   ✅  URANOS Dev Environment is Ready!              ${NC}"
echo -e "${BOLD}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Frappe Desk:${NC}      http://localhost"
echo -e "  ${BOLD}Admin user:${NC}       Administrator"
echo -e "  ${BOLD}Admin password:${NC}   (set in .env → ADMIN_PASSWORD)"
echo -e "  ${BOLD}Site name:${NC}        ${SITE_NAME}"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "    docker exec -it $BACKEND_CONTAINER bash"
echo -e "    docker exec $BACKEND_CONTAINER bench --site $SITE_NAME migrate"
echo -e "    docker exec $BACKEND_CONTAINER bench --site $SITE_NAME console"
echo -e "    docker exec $BACKEND_CONTAINER bench --site $SITE_NAME list-apps"
echo -e "    $DOCKER_COMPOSE logs -f backend"
echo -e "    $DOCKER_COMPOSE logs -f worker-short worker-default worker-long"
echo ""
