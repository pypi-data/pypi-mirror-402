# Project Context

`django-saas-auth` is a reusable Django application designed to provide authentication and profile management features for SaaS products. It integrates with `django-saas-base` and provides Django Rest Framework (DRF) APIs.

## Project Overview

**Key Features:**
- **User Authentication:** Integration with Django's auth system.
- **Session Management:** Tracking user sessions with location and user agent info.
- **API Tokens:** Scoped API tokens for programmatic access (`UserToken`).
- **MFA Support:** Multi-Factor Authentication via TOTP and WebAuthn.
- **Location Resolution:** Resolving user location from IP (supports Cloudflare, etc.).

## Architecture & Structure

The project follows a standard Django app layout within `src/saas_auth`.

### Key Directories

- **`src/saas_auth/models/`**: Domain models.
    - `mfa.py`: TOTP, WebAuthn, and Backup Codes.
    - `session.py`: `Session` tracking.
    - `token.py`: `UserToken` for API access.
- **`src/saas_auth/api_urls/`**: URL routing for APIs.
    - Separated by domain (`session.py`, `token.py`).
- **`src/saas_auth/endpoints/`**: DRF Views/Endpoints.
- **`src/saas_auth/drf/`**: DRF specific integration (e.g., Authentication classes).
- **`src/saas_auth/location/`**: Logic for resolving IP addresses to locations.
- **`tests/`**: Pytest-based test suite.

## Data Models

When working with data, be aware of these core models:

- **`Session`**: Tracks active sessions. fields: `user`, `session_key`, `user_agent`, `location`, `expiry_date`.
- **`UserToken`**: Long-lived tokens for API access. fields: `user`, `tenant`, `key`, `scope`.
- **`MFASettings`**: Toggles for TOTP/WebAuthn on a per-user basis.
- **`TOTPDevice`** & **`WebAuthnDevice`**: Credential storage for MFA.

## Development Guidelines

### Dependencies
- **Core**: `Django`, `djangorestframework`, `django-saas-base`.
- **Dev**: `pytest`, `ruff`.

### Configuration
- The app uses a custom settings mechanism via `saas_base.settings`.
- Defaults are defined in `src/saas_auth/settings.py`.
- **Important**: When adding new settings, ensure they are registered in `DEFAULTS` and documented.

### Testing
- Run tests using `pytest`.
- Ensure new features have corresponding tests in `tests/`.
- Do not rely on database migrations in tests (`--no-migrations` is default).

### Code Style
- Follow PEP 8.
- Use `ruff` for linting and formatting.

## Common Tasks for Agents

1.  **Adding API Endpoints**:
    - Create a view in `endpoints/`.
    - Register the URL in `api_urls/`.
    - Ensure permissions and serializers are correctly defined.

2.  **Extending Models**:
    - Update `admin.py` if necessary.

3.  **MFA Enhancements**:
    - `mfa.py` contains the core logic. Ensure crypto best practices when touching this file.

4.  **Location Services**:
    - To add a new location provider, extend `saas_auth.location.base` and register it in `src/saas_auth/settings.py`.
