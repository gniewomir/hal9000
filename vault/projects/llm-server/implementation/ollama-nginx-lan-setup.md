
# Ollama on localhost + Nginx (Basic auth) for LAN access

**Target OS: Ubuntu 24.04 LTS only.** This guide is written for that release: package names, service layout, and paths match Ubuntu 24.04. Do not assume other Ubuntu versions or distributions without checking differences yourself.

This document describes **option 1**: keep the Ollama API on **localhost only**, expose a single **Nginx** port to your LAN with **HTTP Basic authentication**, and use your **laptop** (same network) as the client. Nothing on the LAN should talk to Ollama’s raw port `11434`; only Nginx should.

---

## What you end up with

| Component | Role |
|-----------|------|
| **Ollama** | Listens on `127.0.0.1:11434` (not directly reachable from other machines). |
| **Nginx** | Listens on a LAN-facing port (e.g. `443` or `80`), enforces Basic auth, proxies to Ollama. |
| **Your laptop** | Calls `http(s)://<server-ip-or-hostname>:<nginx-port>/...` with username/password. |

---

## Prerequisites

- **Ubuntu 24.04** machine with Ollama (GPU optional).
- **sudo** for installing packages and writing under `/etc`.
- Your laptop on the **same LAN** as the server.
- Optional but recommended: **static DHCP reservation** for the server and/or laptop so bookmarks and firewall rules stay stable.

---

## 1. Install Ollama (if not already installed)

Use the official installer (see [ollama.com](https://ollama.com/download/)):

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Pull at least one model for testing:

```bash
ollama pull llama3.2
```

---

## 2. Bind Ollama to localhost only

**Goal:** Ollama must accept connections **only** from the same machine (so only Nginx on that host can reach it).

- **Default:** Many installs already listen on `127.0.0.1:11434` only.
- **If you previously set LAN binding**, remove or override it so the listen address is **not** `0.0.0.0`.

On **systemd**, check or set the service environment (example drop-in):

```ini
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**Verify** (on the server):

```bash
ss -tlnp | grep 11434
```

You want something bound to **127.0.0.1:11434** (not `0.0.0.0:11434`).

**Sanity check:**

```bash
curl -sS http://127.0.0.1:11434/api/tags
```

---

## 3. Install Nginx and password tools

On **Ubuntu 24.04**:

```bash
sudo apt update
sudo apt install -y nginx apache2-utils
```

`apache2-utils` provides `htpasswd` for Basic auth.

---

## 4. Create Basic auth credentials

Pick a path owned by root, readable by Nginx (common: `/etc/nginx/.htpasswd`).

**First user** (creates the file):

```bash
sudo htpasswd -c /etc/nginx/.htpasswd YOUR_USERNAME
```

**Additional users** (do **not** use `-c`):

```bash
sudo htpasswd /etc/nginx/.htpasswd OTHER_USER
```

Lock down permissions:

```bash
sudo chmod 640 /etc/nginx/.htpasswd
sudo chown root:www-data /etc/nginx/.htpasswd
```

On Ubuntu 24.04, Nginx runs as `www-data`; the group above matches that layout.

---

## 5. Nginx: reverse proxy + Basic auth + streaming

Create a site config (path varies: `conf.d/*.conf` or `sites-available` + symlink). Below is a **template**; adjust `server_name`, paths, and ports.

**Important:** Ollama’s docs recommend setting the upstream `Host` header when proxying (see [Ollama FAQ – proxy server](https://docs.ollama.com/faq#how-can-i-use-ollama-with-a-proxy-server)).

### HTTP only (simplest LAN lab)

Use only on a network you fully trust; credentials travel in **clear text** on the wire unless you add TLS.

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 80;
    server_name _;   # or your hostname

    location / {
        auth_basic           "Ollama";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://127.0.0.1:11434;

        proxy_http_version 1.1;
        proxy_set_header Host              localhost:11434;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade           $http_upgrade;
        proxy_set_header Connection        $connection_upgrade;

        proxy_buffering off;
        proxy_read_timeout  3600s;
        proxy_send_timeout  3600s;
    }
}
```

### HTTPS (recommended even on LAN)

- Obtain certificates (e.g. **Let’s Encrypt** if you have a public DNS name, or **mkcert** / internal CA for LAN hostnames).
- Add `listen 443 ssl http2;`, `ssl_certificate`, `ssl_certificate_key`, and optionally redirect HTTP → HTTPS.

Example **redirect** server block:

```nginx
server {
    listen 80;
    server_name your.host.name;
    return 301 https://$host$request_uri;
}
```

Enable the site, test config, reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Firewall

- **Allow** the port Nginx listens on (e.g. **TCP 80/443**) from **your LAN** (or only your laptop’s IP if you use a stricter rule).
- **Do not** expose **TCP 11434** to the LAN if Ollama is localhost-only (it should not be listening on `0.0.0.0` anyway).

On **Ubuntu 24.04**, **ufw** is the usual front end (backed by netfilter). Example:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 443 proto tcp comment 'Nginx HTTPS for LAN'
sudo ufw reload
```

Adjust the subnet and port to match your LAN and whether you use HTTP, HTTPS, or both.

---

## 7. Client usage (laptop)

### curl

```bash
curl -u YOUR_USERNAME:YOUR_PASSWORD http://SERVER_IP/api/tags
```

For HTTPS:

```bash
curl -u YOUR_USERNAME:YOUR_PASSWORD https://your.host.name/api/tags
```

### Apps (Open WebUI, IDE extensions, etc.)

Point the **base URL** to Nginx (`http://SERVER_IP` or `https://your.host.name`), not to `:11434`. Configure **Basic auth** in the app if it supports it; otherwise the app may not work through this proxy.

### Environment variable (CLI tools that read it)

Some tools use `OLLAMA_HOST`. For Basic auth you often set:

```bash
export OLLAMA_HOST=http://YOUR_USERNAME:YOUR_PASSWORD@SERVER_IP
```

(URL-encode special characters in the password.) Not every client supports credentials in `OLLAMA_HOST`; prefer native Basic-auth support when available.

---

## 8. Verification checklist

| Step | Command / check |
|------|------------------|
| Ollama local only | `ss -tlnp \| grep 11434` → `127.0.0.1:11434` |
| Ollama responds locally | `curl -sS http://127.0.0.1:11434/api/tags` |
| Nginx listens on LAN | From laptop: `curl -u user:pass http://SERVER_IP/api/tags` |
| Streaming OK | Long `generate` request does not 504; if it does, increase `proxy_read_timeout` |

---

## 9. Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| **502 Bad Gateway** | Ollama not running or not on `127.0.0.1:11434`. |
| **401** on `/api/*` | Wrong user/password or wrong `auth_basic_user_file` path/permissions. |
| **504** on long replies | Increase `proxy_read_timeout` / `proxy_send_timeout`. |
| **Buffered / delayed tokens** | Ensure `proxy_buffering off;`. |
| **Browser UI CORS errors** | Host UI on same origin as Nginx, or configure Ollama `OLLAMA_ORIGINS` / proxy CORS (see [Ollama FAQ – origins](https://docs.ollama.com/faq#how-can-i-allow-additional-web-origins-to-access-ollama)). |

---

## 10. Security notes (short)

- **Basic auth over HTTP** exposes credentials to passive sniffing on the LAN; prefer **HTTPS** on Nginx when practical.
- This setup is appropriate for a **home LAN**; for access from the **internet**, add stricter controls (TLS, rate limits, VPN, or OIDC).
- Keep the host and Nginx **updated**.

---

## References

- [Ollama FAQ – configure server / expose on network / proxy / origins](https://docs.ollama.com/faq)
- [Nginx `auth_basic` module](http://nginx.org/en/docs/http/ngx_http_auth_basic_module.html)
