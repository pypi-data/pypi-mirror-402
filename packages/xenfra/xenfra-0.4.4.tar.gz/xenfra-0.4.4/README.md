# Xenfra CLI (The Interface) 🖥️

[![PyPI](https://img.shields.io/pypi/v/xenfra)](https://pypi.org/project/xenfra/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The official command-line interface for **Xenfra** (The Sovereign Cloud OS). It empowers developers to deploy, monitor, and manage applications on their own infrastructure (DigitalOcean) with the ease of Heroku.

## 🚀 Features

- **Zero-Config Deployment**: `xenfra deploy` detects your stack (Python, Node.js) and ships it.
- **Sovereign Auth**: `xenfra auth login` connects securely to your cloud provider.
- **Live Logs**: `xenfra logs` streams colorized, PII-scrubbed logs from your servers.
- **Doctor**: `xenfra doctor` runs a battery of health checks on your deployment environment.
- **Zen Mode**: Automatically applies fix patches when deployments fail.

## 📦 Installation

```bash
# Recommended: Install via uv
uv tool install xenfra

# Or via pip
pip install xenfra
```

## 🛠️ Quick Start

### 1. Login

Authenticate with your cloud provider (DigitalOcean via Xenfra Platform).

```bash
xenfra auth login
```

### 2. Deploy Your App

Navigate to your project directory and blast off.

```bash
cd ~/my-projects/awesome-api
xenfra deploy
```

_That's it._ Xenfra handles Dockerfile generation, server provisioning, SSL (Caddy), and database connections.

### 3. Check Status

```bash
xenfra status
```

## 🎛️ Command Reference

| Command             | Description                             |
| :------------------ | :-------------------------------------- |
| `xenfra auth login` | Start the OAuth flow                    |
| `xenfra deploy`     | Deploy current directory                |
| `xenfra logs`       | Tail logs (Ctrl+C to stop)              |
| `xenfra status`     | Show health metrics (CPU/RAM)           |
| `xenfra list`       | List all your projects                  |
| `xenfra init`       | Generate config files without deploying |

## 🔗 The Xenfra Ecosystem

This CLI is the "Interface" of the Xenfra Open Core architecture:

- **[xenfra-sdk](https://github.com/xenfracloud/xenfra-sdk)**: The Core Engine (Used by this CLI).
- **[xenfra-mcp](https://github.com/xenfracloud/xenfra-mcp)**: The AI Agent Interface.
- **xenfra-platform**: The Private SaaS Backend.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT © [Xenfra Cloud](https://xenfra.tech)
