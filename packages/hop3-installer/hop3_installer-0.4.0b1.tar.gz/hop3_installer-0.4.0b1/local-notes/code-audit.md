# hop3-installer Security Code Audit

**Date:** 2026-01-08
**Package:** `packages/hop3-installer`
**Reviewer:** Claude Code (Automated Review)

## Executive Summary

The hop3-installer package provides installation and deployment tools for the Hop3 PaaS platform. This audit identified several security concerns, primarily around **command injection vulnerabilities**, **unverified downloads**, and **SSH host key handling**. While many issues are mitigated by the trusted context (installer runs as root on target systems), they should be addressed for defense-in-depth.

**Risk Level:** Medium-High (in context of privileged installer)

---

## Fixes Applied (2026-01-08)

The following issues from this audit have been addressed:

### Security Fixes

| Issue | Fix Applied |
|-------|-------------|
| Command Injection (server/installer.py) | Added `shlex.quote()` for `package_spec` in `install_package()` |
| Command Injection (deployer/deploy.py) | Added `shlex.quote()` for branch, domain, user, email, password in all shell commands |
| Password Exposure in Logs | Password now masked by default; full password only shown with `--verbose` |
| Predictable Temp Files | Changed `/tmp/root_authorized_keys` to use `tempfile.mkstemp()` with secure permissions |

### Code Quality Fixes

| Issue | Fix Applied |
|-------|-------------|
| Bug: `print_step()` wrong arguments | Changed to `print_info("Configuring Redis...")` in `server/installer.py:276` |
| Duplicate `Colors` class | Consolidated to `common.py`; `testing/common.py` now imports from common |
| Duplicate `CommandResult` class | Moved to `common.py`; `deployer/backends/base.py` and `testing/common.py` now import from common |
| Duplicate `_find_project_root()` | Moved to `common.py` as `find_project_root()`; updated `deployer/config.py`, `testing/cli.py`, `testing/backends/vagrant.py` |
| Redundant `import secrets` | Removed the redundant import inside `setup_environment_file()` |

### Type Errors Fixed

| Issue | Fix Applied |
|-------|-------------|
| `deploy.py:355`: domain can be None | Added early guard in `_setup_admin()` to return `True` if domain is None |
| `common.py:run_cmd`: missing timeout | Added `timeout: float \| None = None` parameter with `TimeoutExpired` handling |
| `server/installer.py:1103`: mysql_root_cmd can be None | Added assertion and captured in local `root_cmd` variable for type checker |

### Remaining Items (Deferred)

| Issue | Status |
|-------|--------|
| Unverified Downloads | Deferred - requires maintaining checksum database |
| SSH TOFU | Deferred - acceptable for development; consider making configurable for testing |
| Privileged Docker | Acceptable - development/testing only |
| Inconsistent logging names (`print_*` vs `log_*`) | Low priority - cosmetic |
| Excessive `check=False` (106 usages) | Requires case-by-case audit |
| Broad `except Exception` (18 usages) | Requires case-by-case refactoring |

---

## Critical Issues

### 1. Command Injection Vulnerabilities

**Severity:** HIGH
**Locations:** Multiple files

The codebase frequently passes user-controlled strings directly to shell commands without proper escaping.

#### 1.1 `server/installer.py:94-96` - `run_as_hop3()`

```python
def run_as_hop3(cmd: str) -> subprocess.CompletedProcess:
    """Run a command as the hop3 user."""
    return run_cmd(["su", "-", HOP3_USER, "-c", cmd])
```

**Issue:** The `cmd` parameter is passed directly to `su -c`, which executes it in a shell. If `cmd` contains shell metacharacters from user input (e.g., `config.local_path`), this could lead to command injection.

**Attack Vector:** If an attacker controls `--local-path`, they could inject commands:
```bash
--local-path "/tmp/foo; rm -rf /"
```

**Affected calls:**
- `installer.py:342` - rustup installation
- `installer.py:356` - cargo version check
- `installer.py:531` - venv creation
- `installer.py:542-562` - pip install with `config.local_path`
- `installer.py:571-572` - hop3-server setup
- `installer.py:601` - SSH key setup

#### 1.2 `deployer/backends/ssh.py:47-54` - SSH command execution

```python
def run(self, command: str, *, check: bool = True) -> CommandResult:
    ssh_cmd = [
        "ssh",
        *self._ssh_opts,
        self.config.ssh_target,
        command,  # Raw command string passed to remote shell
    ]
```

**Issue:** Commands are passed as raw strings to SSH, which executes them in a remote shell.

#### 1.3 `deployer/backends/docker.py:176-185` - Docker exec

```python
docker_cmd = [
    "docker",
    "exec",
    self.container_name,
    "bash",
    "-c",
    command,  # Raw command string
]
```

**Issue:** Same pattern - raw command string to `bash -c`.

#### 1.4 Partial mitigation in `testing/backends/ssh.py:67-68`

```python
if sudo:
    command = f"sudo bash -c {shlex.quote(command)}"
```

**Good:** Uses `shlex.quote()` for sudo commands. This pattern should be applied elsewhere.

**Recommendations:**
1. Use `shlex.quote()` consistently for all shell command arguments
2. Where possible, use list-based subprocess calls instead of shell strings
3. Validate/sanitize user inputs before use in commands

---

### 2. Unverified Downloads

**Severity:** HIGH
**Locations:** Multiple files

Several scripts download and execute code from the internet without integrity verification.

#### 2.1 `cli/installer.py:125-129` - get-pip.py

```python
get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
get_pip_path = INSTALL_DIR / "get-pip.py"
urllib.request.urlretrieve(get_pip_url, get_pip_path)
# ...
run_cmd([str(venv_python), str(get_pip_path), "--quiet"])
```

**Issue:** Downloads and executes pip installer without verifying checksum or signature.

#### 2.2 `server/installer.py:341-344` - Rustup installation

```python
run_as_hop3(
    'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y'
)
```

**Issue:** Classic pipe-to-shell pattern without verification.

#### 2.3 `server/installer.py:1187-1191` - acme.sh installation

```python
run_as_hop3(
    "curl -fsSL https://raw.githubusercontent.com/Neilpang/acme.sh/master/acme.sh -o /tmp/acme.sh"
)
run_as_hop3("cd /tmp && bash acme.sh --install")
```

**Issue:** Downloads and executes acme.sh without verification.

#### 2.4 `server/installer.py:407-422` - Microsoft .NET repository

```python
run_cmd([
    "wget", "-q",
    "https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb",
    "-O", "/tmp/packages-microsoft-prod.deb",
], check=False)
run_cmd(["dpkg", "-i", "/tmp/packages-microsoft-prod.deb"], check=False)
```

**Issue:** Downloads and installs .deb package without verification.

**Recommendations:**
1. Add checksum verification for all downloaded files
2. Consider using package managers where possible (apt, dnf)
3. Pin versions of downloaded scripts
4. Document the trust model for each download source

---

### 3. SSH Host Key Handling

**Severity:** MEDIUM
**Location:** `deployer/backends/ssh.py:24-31`

```python
self._ssh_opts = [
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=10",
]
```

**Issue:** `StrictHostKeyChecking=accept-new` automatically accepts unknown host keys on first connection. This is vulnerable to MITM attacks on first connection (TOFU - Trust On First Use).

**Same pattern in:**
- `testing/backends/ssh.py:74-76`

**Recommendations:**
1. Document the TOFU risk clearly
2. Consider requiring explicit key acceptance for production use
3. Provide option to pre-populate known_hosts

---

## Medium Issues

### 4. Privileged Docker Containers

**Severity:** MEDIUM
**Location:** `deployer/backends/docker.py:82-106`

```python
privileged_result = subprocess.run([
    "docker", "run", "-d",
    "--name", self.container_name,
    "--privileged",  # Full host capabilities
    "-v", "/sys/fs/cgroup:/sys/fs/cgroup:rw",
    # ...
])
```

**Issue:** Runs containers with `--privileged` flag, granting full host capabilities. While this is for development/testing with systemd support, it's dangerous if the container is compromised.

**Recommendation:** Document the risk clearly; consider alternatives for CI environments.

---

### 5. Temporary File Handling

**Severity:** MEDIUM
**Location:** `server/installer.py:591-607`

```python
temp_keys = Path("/tmp/root_authorized_keys")
shutil.copy2(root_keys, temp_keys)
# ... use file ...
temp_keys.unlink()
```

**Issue:** Uses predictable temp file path in /tmp. While the file contains only public keys (not sensitive), this pattern could lead to race conditions or symlink attacks.

**Recommendations:**
1. Use `tempfile.mkstemp()` or `tempfile.NamedTemporaryFile()` for secure temp file creation
2. Set restrictive permissions immediately after creation

---

### 6. Password/Secret Exposure in Logs

**Severity:** MEDIUM
**Locations:** Multiple

#### 6.1 `deployer/deploy.py:179-183` - Prints admin password

```python
print(f"Admin user: {self.config.admin_user}")
print(f"Admin password: {self.config.admin_password}")
```

**Issue:** Prints generated password to terminal, which may be captured in CI logs.

#### 6.2 Partial mitigation exists

`deployer/backends/ssh.py:1066-1069` properly redacts passwords:
```python
if debian_creds and debian_creds[1] in display_cmd:
    display_cmd = display_cmd.replace(debian_creds[1], "***")
```

**Recommendation:** Apply consistent redaction across all password handling.

---

## Low Issues

### 7. Weak Input Validation

**Severity:** LOW
**Locations:** Various config parsing

User-provided values like hostnames, branches, and paths are used with minimal validation:

```python
# deployer/config.py
host = os.environ.get("HOP3_DEV_HOST")
branch = os.environ.get("HOP3_BRANCH", DEFAULT_BRANCH)
```

**Recommendation:** Add basic validation for:
- Hostnames (alphanumeric, dots, hyphens)
- Branch names (alphanumeric, underscores, hyphens, slashes)
- Paths (no null bytes, reasonable length)

---

### 8. Sudoers Configuration

**Severity:** LOW (Properly Scoped)
**Location:** `server/config.py:252-258`

```python
SUDOERS_CONTENT = """# Hop3 service management permissions
hop3 ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload nginx
hop3 ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
hop3 ALL=(ALL) NOPASSWD: /usr/sbin/nginx -s reload
hop3 ALL=(ALL) NOPASSWD: /usr/sbin/nginx -t
"""
```

**Assessment:** This is properly scoped to only allow nginx operations. No wildcard commands. This is acceptable.

---

### 9. File Permission Handling

**Severity:** LOW (Properly Handled)

The codebase generally handles permissions correctly:

- `server/installer.py:713-714`: SSL key 0o600, cert 0o644 ✓
- `server/installer.py:643`: Environment file 0o600 ✓
- `server/installer.py:1266`: Config file 0o600 ✓
- `deployer/config.py:102`: Generated installer 0o755 ✓

---

### 10. Secret Generation

**Severity:** LOW (Properly Handled)

Secrets are generated using cryptographically secure methods:

```python
# server/installer.py:636
secret_key = secrets.token_urlsafe(32)  # 256 bits

# server/installer.py:893
pg_password = "hop3_" + secrets.token_hex(16)  # 128 bits

# deployer/config.py:63
admin_password = secrets.token_urlsafe(16)  # 128 bits
```

All use the `secrets` module, which is cryptographically secure.

---

## Architecture Observations

### Good Practices Found

1. **Stdlib-only constraint** for bundled installers ensures auditability
2. **Proper secret generation** using `secrets` module
3. **Restrictive file permissions** for sensitive files
4. **Limited sudoers scope** - no wildcard commands
5. **HTTPS everywhere** for downloads
6. **Partial command escaping** in testing SSH backend

### Areas for Improvement

1. **Inconsistent command escaping** - apply `shlex.quote()` everywhere
2. **No download verification** - add checksums for all downloaded files
3. **TOFU SSH model** - document or mitigate first-connection risk
4. **Temp file handling** - use secure temp file creation
5. **Log sanitization** - consistently redact secrets from output

---

## Recommendations Summary

| Priority | Issue | Recommendation |
|----------|-------|----------------|
| HIGH | Command injection | Use `shlex.quote()` for all shell arguments |
| HIGH | Unverified downloads | Add checksum verification |
| MEDIUM | SSH TOFU | Document risk, consider key pinning |
| MEDIUM | Privileged Docker | Document risk, consider alternatives |
| MEDIUM | Temp files | Use `tempfile` module |
| MEDIUM | Password logging | Consistent redaction |
| LOW | Input validation | Add basic sanitization |

---

## Appendix: File-by-File Summary

| File | Lines | Risk Areas |
|------|-------|------------|
| `common.py` | 278 | `run_cmd()` - subprocess handling |
| `cli/installer.py` | 530 | get-pip download, path handling |
| `cli/config.py` | 63 | Env var parsing |
| `server/installer.py` | 1704 | Multiple shell commands, downloads |
| `server/config.py` | 352 | Sudoers, package lists |
| `deployer/cli.py` | 353 | Config parsing |
| `deployer/config.py` | 202 | Path handling |
| `deployer/deploy.py` | 445 | Password logging |
| `deployer/backends/ssh.py` | 196 | SSH options, command execution |
| `deployer/backends/docker.py` | 305 | Privileged containers |
| `bundler.py` | 479 | Code generation (trusted) |
| `testing/` | ~800 | Same patterns as deployer |

---

## Conclusion

The hop3-installer codebase has a **medium-high security risk profile** primarily due to command injection vulnerabilities and unverified downloads. Given that this is a privileged installer that runs as root, these issues should be addressed.

The codebase shows good security practices in several areas (secret generation, file permissions, scoped sudoers) but needs improvement in shell command handling and download integrity verification.

**Recommended priority:**
1. Fix command injection (shlex.quote everywhere)
2. Add download verification
3. Document SSH TOFU risk
4. Apply consistent log sanitization

---

# Code Quality Audit (Non-Security)

**Date:** 2026-01-08

## Bugs

### 1. Wrong Function Call - `print_step()` with incorrect arguments ✅ FIXED

**Location:** `server/installer.py:276`
**Severity:** BUG
**Status:** Fixed - changed to `print_info("Configuring Redis...")`

```python
def _configure_redis() -> None:
    ...
    print_step("Configuring Redis...")  # BUG: Wrong arguments!
```

The function signature is `print_step(step: int, total: int, message: str)` but it's called with just one string. This would cause a runtime error if this code path is executed.

---

## Duplicate Code

### 2. `Colors` class duplicated ✅ FIXED

**Locations:**
- `common.py:31` - Canonical implementation
- `testing/common.py` - Now imports from `common.py`

**Status:** Fixed - `testing/common.py` now imports `Colors` from `common.py` and uses `C = Colors` as an alias for the log functions.

### 3. `CommandResult` class duplicated ✅ FIXED

**Locations:**
- `common.py` - Canonical implementation (moved here)
- `deployer/backends/base.py` - Now imports from `common.py` and re-exports for backwards compatibility
- `testing/common.py` - Now imports from `common.py`

**Status:** Fixed - `CommandResult` is now defined in `common.py` and imported elsewhere.

### 4. `_find_project_root()` function duplicated (3x) ✅ FIXED

**Locations:**
- `common.py` - Canonical implementation as `find_project_root(start_path: Path | None = None)`
- `deployer/config.py` - Now imports from `common.py`
- `testing/cli.py` - Now imports from `common.py`
- `testing/backends/vagrant.py` - Now delegates to `common.find_project_root()`

**Status:** Fixed - All locations now use the shared implementation from `common.py`.

---

## Redundant Code

### 5. Redundant import of `secrets` ✅ FIXED

**Location:** `server/installer.py:21` and `server/installer.py:631`
**Status:** Fixed - removed the redundant import inside `setup_environment_file()`

```python
# Line 21 - at top of file
import secrets

# Line 631 - inside function (REMOVED)
def setup_environment_file() -> str:
    # import secrets  # Was redundant, now removed
    ...
    secret_key = secrets.token_urlsafe(32)
```

---

## Inconsistent Patterns

### 6. Different logging function naming conventions

| Module | Pattern | Example |
|--------|---------|---------|
| `common.py` | `print_*` | `print_success()`, `print_error()`, `print_info()` |
| `testing/common.py` | `log_*` | `log_success()`, `log_error()`, `log_info()` |

This makes it confusing which to use and prevents code sharing.

**Fix:** Standardize on one naming convention.

### 7. Inconsistent `Colors` implementation ✅ FIXED

**Status:** Fixed - `testing/common.py` now imports `Colors` from `common.py` instead of defining its own.

The canonical implementation in `common.py` uses class attributes with a `disable()` method. This pattern was chosen because it's simpler and works well for the installer's needs (global color disable for non-TTY output).

---

## Code Smell: Excessive `check=False`

**Count:** 106 occurrences across 10 files

Many subprocess calls use `check=False` to ignore errors. While sometimes intentional (e.g., checking if a command exists), excessive use can mask real problems.

**Examples that should probably check errors:**
```python
# server/installer.py - These seem important
run_cmd(["systemctl", "enable", "hop3-server"], check=False)
run_cmd(["systemctl", "start", "hop3-server"], check=False)
```

**Recommendation:** Audit each `check=False` usage and add error handling or logging where appropriate.

---

## Broad Exception Handling

**Count:** 18 uses of `except Exception`

Many locations catch the broad `Exception` class rather than specific exceptions:

| File | Line | Context |
|------|------|---------|
| `server/installer.py` | 861 | sudoers setup |
| `server/installer.py` | 950 | config write |
| `server/installer.py` | 1683 | server config |
| `cli/installer.py` | 280, 527 | shell setup, main |
| `testing/backends/vagrant.py` | 62, 105, 115, 123 | VM operations |
| `deployer/deploy.py` | 194 | deployment |
| `bundler.py` | 355, 445, 470 | bundling |

**Recommendation:** Catch specific exceptions (`FileNotFoundError`, `subprocess.CalledProcessError`, etc.) to:
1. Avoid masking unexpected errors
2. Provide better error messages
3. Allow proper debugging

---

## Magic Numbers

### SSL Certificate Validity

**Location:** `server/installer.py:709`

```python
"-days", "3650",  # 10 years - magic number
```

**Fix:** Define as a named constant (e.g., `SSL_CERT_VALIDITY_DAYS = 3650`).

---

## Missing Type Annotations

Several functions are missing return type annotations:

```python
# deployer/backends/docker.py
def _container_exists(self):  # Should be -> bool
def _container_running(self): # Should be -> bool
```

---

## Unused Variables

### `nginx_enabled_path` initialized to `None` unnecessarily

**Location:** `server/installer.py:754`

```python
nginx_enabled_path: Path | None = Path("/etc/nginx/sites-enabled/hop3")
```

The explicit `Path | None` type hint is immediately contradicted by assigning a `Path`.

---

## Recommendations Summary (Code Quality)

| Priority | Issue | Status |
|----------|-------|--------|
| **HIGH** | Bug in `print_step()` call | ✅ Fixed |
| **MEDIUM** | Duplicate `Colors` class | ✅ Fixed |
| **MEDIUM** | Duplicate `CommandResult` class | ✅ Fixed |
| **MEDIUM** | Duplicate `_find_project_root()` | ✅ Fixed |
| **LOW** | Redundant import | ✅ Fixed |
| **LOW** | Inconsistent logging names | Deferred (cosmetic) |
| **LOW** | Excessive `check=False` | Deferred (needs case-by-case audit) |
| **LOW** | Broad exception catching | Deferred (needs case-by-case refactor) |
| **LOW** | Magic numbers | Deferred (low impact) |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Python files | 20 |
| Total lines of code | ~5,000 |
| Duplicate code instances | 4 major → **0 (all fixed)** |
| `check=False` usages | 106 |
| `except Exception` usages | 18 |
| Bugs found | 1 → **0 (fixed)** |
| Inconsistent patterns | 2 → **1 (Colors fixed, logging names deferred)** |
| Type errors found | 3 → **0 (all fixed)** |

---

## Files Modified During This Audit

| File | Changes |
|------|---------|
| `common.py` | Added `CommandResult`, `find_project_root()`, `timeout` param to `run_cmd()` |
| `server/installer.py` | Security fixes (shlex.quote, tempfile), bug fix (print_info), removed redundant import, type fix (mysql_root_cmd assertion) |
| `deployer/deploy.py` | Security fixes (shlex.quote, password masking), type fix (domain guard) |
| `deployer/config.py` | Now imports `find_project_root` from common |
| `deployer/backends/base.py` | Now imports `CommandResult` from common |
| `testing/common.py` | Now imports `Colors` and `CommandResult` from common |
| `testing/cli.py` | Now imports `find_project_root` from common |
| `testing/backends/vagrant.py` | Now delegates to common `find_project_root()` |
