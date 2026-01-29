# Changelog

All notable changes to NorthServing will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.2] - 2026-01-15

### Changed
- **BREAKING**: Configuration now uses environment variables instead of config file
  - Use `INFRAWAVES_USERNAME` and `INFRAWAVES_PASSWORD` environment variables
  - Removed `~/.config/northjob/userinfo.conf` config file support
  - See [ENV_CONFIG.md](ENV_CONFIG.md) for migration guide

### Added
- Environment variable configuration support
- `migrate_config.sh` script to help migrate from old config file
- `test_env_config.py` script to verify configuration
- Comprehensive environment configuration documentation (ENV_CONFIG.md)

### Improved
- Better error messages when credentials are not configured
- Simplified credential management for Docker/Kubernetes deployments
- More secure credential handling (no files to protect)

### Migration Guide
See [ENV_CONFIG.md](ENV_CONFIG.md) for detailed migration instructions.

Quick migration:
```bash
# Set environment variables
export INFRAWAVES_USERNAME='your_username'
export INFRAWAVES_PASSWORD='your_password'

# Add to shell config for persistence
echo 'export INFRAWAVES_USERNAME="your_username"' >> ~/.bashrc
echo 'export INFRAWAVES_PASSWORD="your_password"' >> ~/.bashrc
source ~/.bashrc
```

Or use the migration script:
```bash
./migrate_config.sh
```

## [2.0.1] - 2026-01-14

### Fixed
- Fixed static file packaging in wheel distribution
- YAML templates, configs, and benchmark files now correctly included in package
- Updated path resolution for installed packages

### Changed
- Improved `pyproject.toml` configuration for package data
- Simplified build process by removing `prepare_package.sh`
- Updated `build_wheel.py` to work with new packaging approach

## [2.0.0] - 2026-01-13

### Added
- Complete Python refactoring from shell scripts
- Modern CLI using Click framework
- Comprehensive test suite with pytest
- Modular architecture:
  - `commands/`: CLI command implementations
  - `core/`: Core business logic
  - `clients/`: API clients (Infrawave, Kubernetes)
  - `models/`: Data models
  - `utils/`: Utility functions
- Type hints and documentation
- Packaging support with wheel distribution
- Build automation with `build_wheel.py`

### Changed
- **BREAKING**: All commands now use Python instead of shell scripts
- Configuration management using YAML and Jinja2 templates
- Improved error handling and logging
- Better code organization and maintainability

### Removed
- Shell script implementations (moved to `tools/` for reference)
- Legacy configuration format

### Migration from 1.x
The 1.x shell-based version is preserved in the `tools/` directory.
All functionality has been ported to Python with improved design.

To upgrade:
1. Install the new Python package: `pip install -e .`
2. Update your configuration (see Configuration section in README.md)
3. Use `northserve` command instead of `./northserve`

## [1.x] - Legacy Shell Version

The original shell-based implementation is available in the `tools/` directory:
- `northserve.sh`: Main entry point
- `tools/launch.sh`: Launch deployments
- `tools/stop.sh`: Stop deployments
- `tools/list.sh`: List deployments
- And other helper scripts

This version is deprecated but preserved for reference.

---

For the complete change history of the 1.x shell version, refer to the git history.
