---
id: 019da1c6-5288-73bb-a784-14d5ca926e4e
references: []
---

# Automated setup (`setup-ollama-nginx-lan.sh`)

The script [`setup-ollama-nginx-lan.sh`](setup-ollama-nginx-lan.sh) applies the same layout as [ollama-nginx-lan-setup.md](ollama-nginx-lan-setup.md): Ollama on `127.0.0.1:11434`, Nginx on a LAN-facing port with HTTP Basic auth, optional **ufw** allow rule. Read that document for the security model, HTTPS notes, and client usage.

## Requirements

- **Ubuntu 24.04 LTS** (the script checks `/etc/os-release`).
- Run as **root** (e.g. `sudo`).
- **Basic auth** username and password: set environment variables (below) or let the script prompt you.

## Quick start (example)

Full example: install Ollama if missing, pull a model, allow the LAN subnet on the Nginx port, non-interactive credentials:

```bash
cd /path/to/lan-ollama

export OLLAMA_BASIC_USER='alice'
export OLLAMA_BASIC_PASSWORD='your-secret-password'

sudo -E ./setup-ollama-nginx-lan.sh \
  --install-ollama \
  --pull-model llama3.2 \
  --ufw-cidr 192.168.1.0/24
```

Use `-E` with `sudo` so `OLLAMA_BASIC_*` are visible to the root process.

Simpler interactive run (you will be prompted for username and password; Ollama must already be installed unless you add `--install-ollama`):

```bash
sudo ./setup-ollama-nginx-lan.sh --install-ollama
```

## Options

| Option | Meaning |
|--------|---------|
| `--install-ollama` | Run the [official Ollama installer](https://ollama.com/download) if `ollama` is not on `PATH`. |
| `--skip-ollama` | Only configure Nginx + Basic auth (and optional ufw). Does **not** install or reconfigure Ollama. Use when Ollama is already installed and you only want the proxy. |
| `--pull-model NAME` | After Ollama is configured, run `ollama pull NAME` (as the `ollama` user when that account exists). |
| `--nginx-port PORT` | Port Nginx listens on (default: `80`). If you use `80`, the script disables the default `sites-enabled/default` site to avoid a port clash. |
| `--ufw-cidr CIDR` | If set, installs **ufw** if needed, adds `allow from CIDR to any port <nginx-port> tcp`, and runs `ufw reload`. Omit to leave the firewall unchanged. |
| `--htpasswd PATH` | Path for the htpasswd file (default: `/etc/nginx/.htpasswd`). |

`--install-ollama` and `--skip-ollama` cannot be used together.

Help:

```bash
./setup-ollama-nginx-lan.sh --help
```

## Credentials

- **Non-interactive:** set `OLLAMA_BASIC_USER` and `OLLAMA_BASIC_PASSWORD` before `sudo -E`.
- **Interactive:** omit them; the script asks for username and password (password is read without echo).

Avoid putting secrets on the command line (`--password` is not supported); they can show up in process listings.

## What the script configures (reference)

| Piece | Location / action |
|-------|-------------------|
| Ollama bind | Systemd drop-in: `/etc/systemd/system/ollama.service.d/override.conf` with `OLLAMA_HOST=127.0.0.1:11434` |
| Nginx `map` | `/etc/nginx/conf.d/ollama-lan-connection-upgrade.conf` |
| Nginx site | `/etc/nginx/sites-available/ollama-lan-proxy` → symlink in `sites-enabled/` |
| Basic auth file | Default `/etc/nginx/.htpasswd` (see `--htpasswd`) |

Then: `nginx -t`, enable/reload **nginx**.

## Verification (on the server)

```bash
ss -tlnp | grep 11434    # expect 127.0.0.1:11434
curl -sS http://127.0.0.1:11434/api/tags
curl -u 'USER:PASSWORD' http://127.0.0.1:PORT/api/tags
```

Use the Nginx `PORT` you chose (default `80`).

From another machine on the LAN, use the host’s IP or hostname instead of `127.0.0.1`.

## See also

- [ollama-nginx-lan-setup.md](ollama-nginx-lan-setup.md) — full walkthrough, HTTPS, troubleshooting, and client notes.
