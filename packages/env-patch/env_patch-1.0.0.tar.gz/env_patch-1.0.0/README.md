# env-patch

[![PyPI version](https://badge.fury.io/py/env-patch.svg)](https://badge.fury.io/py/env-patch)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Environment file generator with template + override support.**

Born from [UpbrosAI](https://upbros.ai) team's production experience building cross-border e-commerce and AI-powered applications.

[中文文档](README.zh-CN.md)

## Why env-patch?

Most dotenv libraries load `.env` files at **runtime**. But what if you need to:

- **Build Docker images** with baked-in environment configs?
- **Deploy to platforms** that don't support dotenv loading?
- **Debug configuration** by seeing exactly what values will be used?

**env-patch** generates a single `.env` file at **build time** by merging your template with environment-specific overrides.

## Installation

```bash
# Using pip
pip install env-patch

# Using uv (recommended)
uv add env-patch

# Using pipx (for global CLI)
pipx install env-patch
```

## Quick Start

```bash
# 1. Create your template
cat > .env.example << 'EOF'
DATABASE_URL=postgres://localhost/myapp
REDIS_URL=redis://localhost:6379
DEBUG=false
EOF

# 2. Create environment-specific config
cat > .env.development << 'EOF'
DEBUG=true
EOF

# 3. Generate .env
env-patch -e development

# Result: .env contains DATABASE_URL, REDIS_URL from template + DEBUG=true from override
```

## File Hierarchy

```
.env.example              # Template (git tracked)
.env.development          # Development config (git tracked)
.env.development.local    # Local overrides (git ignored)
.env                      # Output (git ignored)
```

**Priority (highest to lowest):**
1. `.env.{env}.local` - Personal machine-specific overrides
2. `.env.{env}` - Environment-specific config
3. `.env.example` - Default template values

## Usage

### Basic Usage

```bash
# Auto-detect env file (when only one exists)
env-patch

# Specify environment
env-patch -e development
env-patch -e production
env-patch -e staging
```

### Aliases

Built-in aliases for common environments:

```bash
env-patch -e dev    # Same as: env-patch -e development
env-patch -e prod   # Same as: env-patch -e production
env-patch -e stage  # Same as: env-patch -e staging
```

### Custom Environments

```bash
# Use any environment name
env-patch -e uai-prod       # Uses .env.uai-prod
env-patch -e feature-auth   # Uses .env.feature-auth
```

### Options

```bash
env-patch -e <env>           # Environment name
env-patch -t <file>          # Template file (default: .env.example)
env-patch -o <file>          # Output file (default: .env)
env-patch -s                 # Strict mode: error on unknown keys
env-patch -h                 # Show help
env-patch -v                 # Show version
```

## Local Overrides

Create `.env.{env}.local` for machine-specific settings that shouldn't be committed:

```bash
# .env.development.local (git ignored)
DATABASE_URL=postgres://localhost:5433/myapp_local
API_KEY=my-personal-api-key
```

These values override both the template and the environment config.

## Recommended .gitignore

```gitignore
# Output file
.env

# Local overrides
.env.local
.env.*.local

# Keep these tracked
!.env.example
```

## CI/CD Integration

```yaml
# GitHub Actions example
steps:
  - name: Generate .env for production
    run: |
      pip install env-patch
      env-patch -e production
```

```dockerfile
# Dockerfile example
FROM python:3.12
RUN pip install env-patch
COPY .env.example .env.production ./
RUN env-patch -e production
```

## Why Not Just Use dotenv-flow?

| Feature | env-patch | dotenv-flow |
|---------|-----------|-------------|
| When it runs | Build time | Runtime |
| Output | Single `.env` file | In-memory only |
| Docker builds | Easy | Requires workaround |
| Debug visibility | Check `.env` directly | Add logging |
| Language | Python CLI | Node.js library |

**Use env-patch when you need a generated file. Use dotenv-flow when you want runtime loading.**

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with love by [UpbrosAI Team](https://upbros.ai)
