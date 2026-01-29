# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-21

### Added

- Global CLI installation instructions (`pipx`, `uv tool`)

## [1.0.0] - 2025-01-18

### Added

- Initial public release
- Environment file generation from template + override
- Support for `.env.{environment}` naming convention
- Support for `.env.{environment}.local` override files
- Built-in aliases: `dev` -> `development`, `prod` -> `production`, `stage` -> `staging`
- Auto-detection when single environment file exists
- Strict mode for key validation (`-s` flag)
- Colored terminal output with diff display
- Python 3.8+ support

### Features

- **Template-based generation**: Start with `.env.example` as your template
- **Environment overrides**: Create `.env.development`, `.env.production`, etc.
- **Local overrides**: Use `.env.{env}.local` for machine-specific settings
- **Smart merging**: Values from override files replace template values
- **Additional keys**: Keys not in template are appended with warnings
- **Always regenerate**: Output file is always written for consistency

---

Born from [MochatAI](https://mochatai.com) team's production experience.
