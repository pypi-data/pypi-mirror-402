# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Package Overview

hop3-installer provides installation and deployment tools for the Hop3 PaaS platform. It contains two distinct entry points with different purposes:

| Command | Purpose | User |
|---------|---------|------|
| `hop3-install` | Production installer for fresh systems | End users, sysadmins |
| `hop3-deploy` | Developer deployment tool | Developers |

**Critical constraint**: The installers (`cli/` and `server/`) use **only Python stdlib** - no external dependencies allowed. This enables single-file distribution via curl.

## Commands

### Development

```bash
# Install for development (from package directory)
uv pip install -e ".[dev]"

# Run linting
uv run ruff check src/
uv run ruff format src/

# Run tests
uv run pytest tests/ -v
```

### Bundling Single-File Installers

```bash
# Generate both installers
hop3-install bundle --all --output-dir dist/

# Generate specific installer
hop3-install bundle --type server --output install-server.py
hop3-install bundle --type cli --output install-cli.py
```

### Deployment (Developer Use)

```bash
# Deploy to SSH target
export HOP3_DEV_HOST=server.example.com
hop3-deploy

# Deploy with local code changes
hop3-deploy --host server.example.com --local

# Deploy to Docker container
hop3-deploy --docker

# Clean install then deploy
hop3-deploy --clean

# Teardown Docker container
hop3-deploy --docker --teardown
```

### Testing Installers

```bash
# Test on Docker
hop3-install test docker --distro ubuntu

# Test on remote server
hop3-install test ssh --host user@server.example.com
```

## Architecture

```
src/hop3_installer/
├── main.py              # Unified entry point for hop3-install
├── common.py            # Shared utilities (Colors, Spinner, run_cmd)
├── bundler.py           # Single-file installer bundler
├── cli/                 # CLI installer (hop3-install cli)
│   ├── config.py        # CLIInstallerConfig dataclass
│   └── installer.py     # Installation logic
├── server/              # Server installer (hop3-install server)
│   ├── config.py        # ServerInstallerConfig + system packages
│   └── installer.py     # Full server setup (1700+ lines)
├── deployer/            # Developer deployment (hop3-deploy)
│   ├── cli.py           # CLI interface with argparse
│   ├── config.py        # DeployConfig dataclass
│   ├── deploy.py        # Deployer class orchestration
│   └── backends/
│       ├── base.py      # DeployBackend protocol
│       ├── ssh.py       # SSHDeployBackend
│       └── docker.py    # DockerDeployBackend
└── testing/             # Installer validation
    ├── runner.py        # InstallerTestRunner
    ├── validators.py    # InstallationValidator
    └── backends/        # Docker, SSH, Vagrant test targets
```

## Key Design Decisions

### Bundler Architecture

The bundler (`bundler.py`) combines multiple modules into single-file scripts:
1. Extracts imports from each module
2. Removes relative imports (code is inlined)
3. Deduplicates stdlib imports
4. Validates resulting Python with `ast.parse()`

Module order matters - `common.py` must come first as other modules depend on it.

### Server Installer Flow

The server installer (`server/installer.py`) runs 11 steps:
1. System dependencies (apt/dnf packages)
2. Create hop3 user/group
3. Create Python venv
4. Install hop3-server package
5. Run initial setup
6. Configure SSH keys
7. Setup systemd services
8. Generate SSL certificates
9. Configure nginx
10. Setup PostgreSQL
11. Setup MySQL (if requested)

### Deployment Backends

Both SSH and Docker backends implement the same interface:
- `setup()` - Establish connection
- `run(cmd)` - Execute command
- `upload_file()` / `upload_dir()` - Transfer files
- `is_hop3_installed()` - Check existing installation
- `clean()` - Remove existing installation

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HOP3_DEV_HOST` | Target server hostname |
| `HOP3_SSH_USER` | SSH user (default: root) |
| `HOP3_BRANCH` | Git branch (default: devel) |
| `HOP3_LOCAL` | Use local code instead of git |
| `HOP3_CLEAN` | Clean before install |
| `HOP3_DOCKER` | Use Docker backend |
| `HOP3_DOMAIN` | Server domain for SSL |

## Common Debugging

| Issue | Check |
|-------|-------|
| Bundle syntax error | Run `hop3-install bundle --validate` |
| SSH connection fails | `ssh -v user@host` |
| Docker container won't start | `docker logs hop3-dev` |
| Service not starting | `journalctl -u hop3-server` |
| Permissions errors | Check hop3 user ownership |

When modifying installer code, always regenerate and test the bundled output - the bundler can fail silently on import issues.
