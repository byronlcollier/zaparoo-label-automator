# Zaparoo Label Automator - AI Agent Instructions

## Project Overview
This Python project automates creation of Zaparoo labels using IGDB game database via Twitch API. The architecture centers around OAuth2 token management for Twitch's client credentials flow, with references to MiSTer FPGA core compatibility.

## Core Architecture

### Token Management System
- **`wrapper/twitch.py`** contains the main `TokenManager` class handling OAuth2 client credentials flow
- Uses file-based token persistence in `.config/` directory (excluded from git)
- Two key files: `api_credentials.json` (user-provided) and `token.json` (auto-generated)
- Token validation happens on every initialization before making API calls

### Configuration Pattern
```python
# TokenManager expects this specific pattern:
twitch_token = TokenManager(config_path="./.config")
twitch_token.initialise_token()
```

### File Structure Convention
- **Main entry**: `main.py` demonstrates the token workflow
- **Wrappers**: `wrapper/` module contains service integrations
- **Config**: `.config/` directory for sensitive credentials (gitignored)
- **Data**: `mister_supported_cores.csv` contains MiSTer FPGA compatibility data

## Development Conventions

### Python Environment
- **Python 3.13** required (see `.python-version`)
- Uses `uv` for dependency management (evidence: `uv.lock` file)
- Minimal dependencies: only `requests>=2.32.5`

### Code Style
- **Line length**: 120 characters (pylint configuration in `pyproject.toml`)
- **Error handling**: Comprehensive exception handling with descriptive messages
- **File operations**: Always use encoding='utf-8' for JSON operations

### Token Management Patterns
1. **Validation first**: Always check token validity before use
2. **File-based persistence**: Tokens saved to/loaded from JSON files
3. **Template generation**: Missing config files auto-create templates with helpful error messages
4. **Graceful degradation**: Automatically fetches new tokens when validation fails

## Critical Workflows

### Setup New Environment
```bash
# Create config directory and template files
python main.py  # Will create .config/api_credentials.json template on first run
# Fill in client_id and client_secret in .config/api_credentials.json
python main.py  # Now will generate and save token
```

### Adding New API Integrations
- Follow the `wrapper/twitch.py` pattern for new service integrations
- Implement similar config-based credential management
- Use the existing timeout and error handling patterns

## Integration Points

### Twitch/IGDB API Flow
- **Client Credentials Grant**: `https://id.twitch.tv/oauth2/token`
- **Token Validation**: `https://id.twitch.tv/oauth2/validate`  
- **Timeout**: 60 seconds for all API calls
- **Headers**: Requires both `Client-ID` and `Authorization: Bearer <token>`

### MiSTer FPGA Integration
- `mister_supported_cores.csv` maps computer/console names to MiSTer folder structures
- "Interested" column appears to filter which cores to process
- Home folder names are MiSTer-specific (e.g., "Amstrad", "AtariST", "C64")

## Common Pitfalls

### Token Management
- **Never commit** `.config/` contents to git - credentials are sensitive
- **Always validate** tokens before API calls - they expire
- **Handle template creation** - missing credential files should create helpful templates

### File Operations
- **Use absolute paths** when working with `.config/` directory
- **UTF-8 encoding** required for all JSON file operations
- **Error handling** should distinguish between missing files vs invalid content

## Testing Approach
- Run `python main.py` to test basic token flow
- Check `.config/token.json` gets created with valid token
- Verify token validation endpoint returns 200 status