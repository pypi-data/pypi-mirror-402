# Django SaaS Domain Agent Guide

This document is designed to help AI agents (and human developers) understand and work with `django-saas-domain`.

## Project Overview

`django-saas-domain` is a Django app that provides domain management capabilities for SaaS platforms. It enables tenants to connect their own custom domains to the SaaS application, handling verification, SSL provisioning (via providers like Cloudflare), and tenant resolution via middleware.

## Core Architecture

### 1. Data Model (`src/saas_domain/models.py`)
- **`Domain`**: The central model.
    - `tenant`: ForeignKey to the tenant model (configurable via `SAAS_TENANT_MODEL`).
    - `hostname`: The custom domain (e.g., `app.example.com`).
    - `provider`: String identifier for the provider (e.g., `cloudflare`).
    - `verified`, `ssl`, `active`: Status flags.
    - `instrument_id`, `instrument`: JSON fields to store provider-specific metadata (e.g., Cloudflare custom hostname ID and verification records).
- **`DomainManager`**: Includes caching and helper methods like `get_tenant_id(hostname)`.

### 2. Providers (`src/saas_domain/providers/`)
The system is designed to be extensible via providers.
- **`BaseProvider`**: Abstract base class defining the interface:
    - `add_domain(domain)`
    - `verify_domain(domain)`
    - `remove_domain(domain)`
- **`CloudflareProvider`**: A concrete implementation using Cloudflare's "Custom Hostnames" for SaaS.

### 3. Middleware (`src/saas_domain/middleware.py`)
- **`DomainTenantIdMiddleware`**:
    - Resolves the current tenant based on the request's hostname.
    - Sets `request.tenant_id`.
    - Uses caching for performance.

## Development & Usage

### Installation
Typically installed via pip:
```bash
pip install django-saas-domain
```

### Configuration
In `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    "saas_base",
    "saas_domain",
]

SAAS_DOMAIN = {
    'PROVIDERS': {
        'null': {
            'backend': 'saas_domain.providers.NullProvider',
            'options': {},
        },
        'cloudflare': {
            'backend': 'saas_domain.providers.CloudflareProvider',
            'options': {'zone_id': '123', 'auth_key': 'auth-key', 'ignore_hostnames': ['localtest.me']},
        },
    },
}
```

### Running Tests
The project uses `pytest`.
```bash
pytest
```
Note: External API calls (like Cloudflare) should be mocked in tests. See `tests/test_cloudflare_provider.py` for examples using `requests-mock`.

## Common Tasks for Agents

1.  **Adding a New Provider**:
    -   Create a new file in `src/saas_domain/providers/`.
    -   Inherit from `BaseProvider`.
    -   Implement `add_domain`, `verify_domain`, and `remove_domain`.
    -   Add tests in `tests/`.

2.  **Modifying Domain Logic**:
    -   Check `src/saas_domain/models.py` for schema changes.
    -   Ensure `DomainManager` caching is updated if logic changes.

3.  **Debugging Tenant Resolution**:
    -   Investigate `src/saas_domain/middleware.py`.
    -   Verify that `request.get_host()` is returning the expected value (check `ALLOWED_HOSTS` and proxy headers).

## File Structure Highlights

- `src/saas_domain/`: Source code.
    - `api_urls/`: Django REST Framework URL configurations.
    - `endpoints/`: API views/viewsets.
    - `providers/`: Provider implementations.
- `tests/`: Test suite.
- `demo/`: A minimal Django project for demonstration and testing purposes.
