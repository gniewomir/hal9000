#!/usr/bin/env bash
#
# Apply the Ollama + Nginx (Basic auth) LAN setup described in ollama-nginx-lan-setup.md
# Target OS: Ubuntu 24.04 LTS only.
#
# Usage (run with sudo):
#   sudo ./setup-ollama-nginx-lan.sh [options]
#
# Non-interactive (recommended for automation; keep secrets out of shell history when possible):
#   export OLLAMA_BASIC_USER='alice'
#   export OLLAMA_BASIC_PASSWORD='secret'
#   sudo -E ./setup-ollama-nginx-lan.sh --install-ollama
#
# Options:
#   --install-ollama          Run the official Ollama installer (curl | sh) if not present
#   --pull-model NAME         After install, run: ollama pull NAME (optional; default: skip)
#   --skip-ollama             Do not install/configure Ollama (only Nginx + auth + optional ufw)
#   --nginx-port PORT         Port for Nginx HTTP reverse proxy (default: 80)
#   --ufw-cidr CIDR           If set, allow TCP to --nginx-port from this CIDR (e.g. 192.168.1.0/24)
#   --htpasswd PATH           Basic auth file (default: /etc/nginx/.htpasswd)
#
set -euo pipefail

readonly UBUNTU_VERSION_ID='24.04'
readonly NGINX_MAP_CONF='/etc/nginx/conf.d/ollama-lan-connection-upgrade.conf'
readonly NGINX_SITE_AVAILABLE='/etc/nginx/sites-available/ollama-lan-proxy'
readonly NGINX_SITE_ENABLED='/etc/nginx/sites-enabled/ollama-lan-proxy'
readonly OLLAMA_DROPIN_DIR='/etc/systemd/system/ollama.service.d'
readonly OLLAMA_DROPIN_CONF="${OLLAMA_DROPIN_DIR}/override.conf"

INSTALL_OLLAMA=0
SKIP_OLLAMA=0
PULL_MODEL=''
NGINX_PORT='80'
UFW_CIDR=''
HTPASSWD_PATH='/etc/nginx/.htpasswd'

die() {
  echo "error: $*" >&2
  exit 1
}

require_root() {
  if [[ "${EUID:-0}" -ne 0 ]]; then
    die "run this script as root (e.g. sudo $0 ...)"
  fi
}

require_ubuntu_2404() {
  [[ -r /etc/os-release ]] || die "cannot read /etc/os-release"
  # shellcheck source=/dev/null
  . /etc/os-release
  [[ "${ID:-}" == 'ubuntu' ]] || die "this script supports Ubuntu only (found ID=${ID:-})"
  [[ "${VERSION_ID:-}" == "${UBUNTU_VERSION_ID}" ]] || die "this script supports Ubuntu ${UBUNTU_VERSION_ID} only (found VERSION_ID=${VERSION_ID:-})"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --install-ollama)
        INSTALL_OLLAMA=1
        shift
        ;;
      --skip-ollama)
        SKIP_OLLAMA=1
        shift
        ;;
      --pull-model)
        [[ $# -ge 2 ]] || die "--pull-model requires a value"
        PULL_MODEL="$2"
        shift 2
        ;;
      --nginx-port)
        [[ $# -ge 2 ]] || die "--nginx-port requires a value"
        NGINX_PORT="$2"
        shift 2
        ;;
      --ufw-cidr)
        [[ $# -ge 2 ]] || die "--ufw-cidr requires a value"
        UFW_CIDR="$2"
        shift 2
        ;;
      --htpasswd)
        [[ $# -ge 2 ]] || die "--htpasswd requires a path"
        HTPASSWD_PATH="$2"
        shift 2
        ;;
      -h|--help)
        cat <<'HELP'
Usage: sudo ./setup-ollama-nginx-lan.sh [options]

Ubuntu 24.04 only. Configures Ollama on 127.0.0.1:11434, Nginx reverse proxy with
HTTP Basic auth, optional ufw rule for the LAN.

Options:
  --install-ollama     Run https://ollama.com/install.sh if ollama is missing
  --skip-ollama        Do not install or configure Ollama (Nginx + auth only)
  --pull-model NAME    After Ollama setup, run: ollama pull NAME
  --nginx-port PORT    Nginx listen port (default: 80)
  --ufw-cidr CIDR      Allow TCP to nginx port from CIDR (e.g. 192.168.1.0/24)
  --htpasswd PATH      Basic auth file (default: /etc/nginx/.htpasswd)

Credentials (or you will be prompted):
  export OLLAMA_BASIC_USER=...
  export OLLAMA_BASIC_PASSWORD=...
HELP
        exit 0
        ;;
      *)
        die "unknown argument: $1"
        ;;
    esac
  done

  if [[ "${INSTALL_OLLAMA}" -eq 1 && "${SKIP_OLLAMA}" -eq 1 ]]; then
    die "choose at most one of --install-ollama and --skip-ollama"
  fi
}

prompt_basic_auth_if_needed() {
  if [[ -z "${OLLAMA_BASIC_USER:-}" ]]; then
    read -r -p "Basic auth username: " OLLAMA_BASIC_USER
  fi
  if [[ -z "${OLLAMA_BASIC_USER// }" ]]; then
    die "OLLAMA_BASIC_USER is required"
  fi
  if [[ -z "${OLLAMA_BASIC_PASSWORD:-}" ]]; then
    read -r -s -p "Basic auth password: " OLLAMA_BASIC_PASSWORD
    echo
  fi
  if [[ -z "${OLLAMA_BASIC_PASSWORD}" ]]; then
    die "OLLAMA_BASIC_PASSWORD is required"
  fi
}

install_ollama_if_requested() {
  if [[ "${SKIP_OLLAMA}" -eq 1 ]]; then
    return 0
  fi
  if command -v ollama >/dev/null 2>&1; then
    echo "ollama already installed"
    return 0
  fi
  if [[ "${INSTALL_OLLAMA}" -ne 1 ]]; then
    die "ollama not found; install it first or pass --install-ollama"
  fi
  echo "installing Ollama via official script..."
  curl -fsSL https://ollama.com/install.sh | sh
}

configure_ollama_localhost() {
  if [[ "${SKIP_OLLAMA}" -eq 1 ]]; then
    return 0
  fi
  if ! command -v ollama >/dev/null 2>&1; then
    die "ollama not available after install step"
  fi
  if ! systemctl cat ollama.service >/dev/null 2>&1; then
    die "ollama.service not found; is Ollama installed correctly?"
  fi

  install -d -m 0755 "${OLLAMA_DROPIN_DIR}"
  cat >"${OLLAMA_DROPIN_CONF}" <<'EOF'
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
EOF
  chmod 0644 "${OLLAMA_DROPIN_CONF}"

  systemctl daemon-reload
  systemctl restart ollama.service

  if [[ -n "${PULL_MODEL}" ]]; then
    echo "pulling model: ${PULL_MODEL}"
    if id -u ollama >/dev/null 2>&1; then
      sudo -u ollama ollama pull "${PULL_MODEL}"
    else
      ollama pull "${PULL_MODEL}"
    fi
  fi
}

install_nginx_packages() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y nginx apache2-utils
}

write_nginx_map() {
  cat >"${NGINX_MAP_CONF}" <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
EOF
  chmod 0644 "${NGINX_MAP_CONF}"
}

write_nginx_site() {
  local port="$1"
  cat >"${NGINX_SITE_AVAILABLE}" <<EOF
server {
    listen ${port};
    server_name _;

    location / {
        auth_basic           "Ollama";
        auth_basic_user_file ${HTPASSWD_PATH};

        proxy_pass http://127.0.0.1:11434;

        proxy_http_version 1.1;
        proxy_set_header Host              localhost:11434;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade           \$http_upgrade;
        proxy_set_header Connection        \$connection_upgrade;

        proxy_buffering off;
        proxy_read_timeout  3600s;
        proxy_send_timeout  3600s;
    }
}
EOF
  chmod 0644 "${NGINX_SITE_AVAILABLE}"
}

enable_nginx_site() {
  if [[ "${NGINX_PORT}" == '80' ]] && [[ -e /etc/nginx/sites-enabled/default ]]; then
    echo "disabling default nginx site (port 80 conflict); /etc/nginx/sites-available/default is unchanged"
    rm -f /etc/nginx/sites-enabled/default
  fi
  ln -sf "${NGINX_SITE_AVAILABLE}" "${NGINX_SITE_ENABLED}"
}

create_htpasswd() {
  if [[ ! -f "${HTPASSWD_PATH}" ]]; then
    htpasswd -b -B -c "${HTPASSWD_PATH}" "${OLLAMA_BASIC_USER}" "${OLLAMA_BASIC_PASSWORD}"
  else
    htpasswd -b -B "${HTPASSWD_PATH}" "${OLLAMA_BASIC_USER}" "${OLLAMA_BASIC_PASSWORD}"
  fi
  chmod 0640 "${HTPASSWD_PATH}"
  chown root:www-data "${HTPASSWD_PATH}"
}

maybe_ufw() {
  if [[ -z "${UFW_CIDR}" ]]; then
    return 0
  fi
  if ! command -v ufw >/dev/null 2>&1; then
    apt-get install -y ufw
  fi
  echo "configuring ufw: allow TCP ${NGINX_PORT} from ${UFW_CIDR}"
  ufw allow from "${UFW_CIDR}" to any port "${NGINX_PORT}" proto tcp comment 'Ollama Nginx LAN'
  ufw reload
}

test_and_reload_nginx() {
  nginx -t
  systemctl enable --now nginx
  systemctl reload nginx
}

main() {
  parse_args "$@"
  require_root
  require_ubuntu_2404
  prompt_basic_auth_if_needed

  install_ollama_if_requested
  configure_ollama_localhost

  install_nginx_packages
  write_nginx_map
  write_nginx_site "${NGINX_PORT}"
  enable_nginx_site
  create_htpasswd
  maybe_ufw
  test_and_reload_nginx

  echo
  echo "Done. Quick checks on this host:"
  echo "  ss -tlnp | grep 11434    # expect 127.0.0.1:11434"
  echo "  curl -sS http://127.0.0.1:11434/api/tags"
  echo "  curl -u '${OLLAMA_BASIC_USER}:****' http://127.0.0.1:${NGINX_PORT}/api/tags"
}

main "$@"
