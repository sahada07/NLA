# NLA Backend

This reposjitory contains the backend for the NLA project — a Django REST API for managing users, betting, lotto, and related resources.

Contents
- `NLA/` - Django project settings and entrypoints
- `betting/` - App that provides betting-related models, views and API routes
- `users/` - App for user management
- `lotto/` - Virtualenv folder used for local development (do not commit)

Prerequisites
- Python 3.11+ (the project was run in a Python 3.13 environment in the original workspace)
- pip
- A virtual environment (recommended)

Quick setup

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Apply migrations and create a superuser:

```powershell
python manage.py migrate; python manage.py createsuperuser
```

4. Collect static files (if needed) and run the development server:

```powershell
python manage.py collectstatic --noinput; python manage.py runserver
```

Running tests

```powershell
python manage.py test
```

API overview

This project uses Django REST Framework and exposes several API endpoints via routers. Example routes (from `betting/urls.py`):

- `GET /game-types/` — game types list (registered as `game-types` ViewSet)
- `GET /subsscriptions/` — subscriptions list (note: route name in the code is spelled `subsscriptions`)
- `GET /notifications/` — notifications list

Note about a route typo

While inspecting `betting/urls.py` the repository contains a likely typo:

```python
router.register('subsscriptions',SubscriptionViewSet,basename='subscriptions')
```

The path segment `subsscriptions` has an extra `s`. If you expect the endpoint to be `/subscriptions/`, change it to:

```python
router.register('subscriptions', SubscriptionViewSet, basename='subscriptions')
```

Contributing

1. Create a branch for your changes
2. Run tests locally
3. Open a pull request with a clear description of changes

Notes
- Do not commit the `lotto/` virtualenv folder. If you see it in the repository, consider removing it from source control and adding it to `.gitignore`.
- If you change Python versions, re-create the virtual environment and reinstall dependencies.

Contact

For questions about architecture or API design, refer to the `betting/` and `users/` apps or contact the project maintainer.
