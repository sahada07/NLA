## NLA - Project Documentation

Last updated: 2025-10-29

This document summarizes the repository structure, key apps and models, management commands, and how to run and test the project locally. It is intended as a developer-facing reference so you can quickly start the project and run the management command that creates test betting data.

## Repository layout (important files)

- `manage.py` — Django CLI entrypoint.
- `NLA/settings.py` — Django settings and environment configuration (uses `dj-database-url` and dotenv).
- `requirements.txt` — Python dependencies for the project.
- `betting/` — Main betting app (models, views, serializers, admin, management commands):
  - `models.py` — Domain models (GameType, BetType, GameOdds, Draw, Bet, BetTransaction, UserSubscription, Notification, helper functions).
  - `views.py` — DRF ViewSets and API endpoints (GameType, Draw, Subscription, Notification, Bet endpoints).
  - `serializers.py` — DRF serializers for API input/output and validation (including `PlaceBetSerializer`).
  - `admin.py` — Django admin customization for models.
  - `service.py` — Notification helper/service.
  - `management/commands/` — custom management commands. Current commands:
    - `create_test_betting_data.py` — idempotent command that seeds a small set of test data (test user, game type, bet type, odds, draw, bet, notification, transaction).
    - `check_draw_results.py` — (existing) management command used to create/check draws (previously debugged).

- `users/` — Custom user model and user-related code:
  - `models.py` — `User` (extends `AbstractUser`) and `UserProfile`.

## Key models (brief)

- GameType (db_table: `game_types`)
  - Fields: `name`, `code`, `category`, `min_numbers`, `max_numbers`, `number_range_start`, `number_range_end`, `draw_time`, `draw_days`, `min_stake`, `max_stake`, `is_active`.
- BetType (db_table: `bet_type`)
  - Fields: `name` (choice like `direct`, `perm`), `display_name`, `base_odds`, `min_numbers_required`, `max_numbers_allowed`.
- GameOdds (db_table: `game_odds`)
  - Payout multipliers per game/bet/numbers combination.
- Draw (db_table: `draws`)
  - Represents a scheduled game: `draw_number`, `game_type`, `draw_date`, `draw_time`, `status`, `betting_opens_at`, `betting_closes_at`, `winning_numbers`, stats fields.
- Bet (db_table: `bets`)
  - `user`, `draw`, `bet_type`, `bet_number`, `selected_numbers`, `stake_amount`, `potential_winnings`, `actual_winnings`, `status`.
- BetTransaction (db_table: `bet_transactions`)
  - Records money movements related to bets.
- User (db_table: `users`) — custom user with `account_balance` and other attributes.

See the model files for full field lists and methods.

## Management commands

- `python manage.py create_test_betting_data`
  - Location: `betting/management/commands/create_test_betting_data.py`
  - Purpose: create an idempotent set of test data. Creates user `testuser`, `GameType` with code `TEST_GAME`, `BetType` named `direct`, `GameOdds`, one `Draw` and one active `Bet` for `testuser`, a `Notification` and a `BetTransaction` record. Prints a summary of created/located records.
  - Use it to quickly populate a local database for development/testing.

- `python manage.py check_draw_results` (existing command)
  - Used to create draws and perform draw-related checks. It was edited during debugging to ensure timezone-aware datetimes and correct ORM usage.

## How to run the project locally (developer quick-start)

Prerequisites:
- Python 3.11+ (project uses Django 4.2.7 in `requirements.txt`)
- A virtualenv — the repository previously used `lotto/` virtualenv in the workspace, but you can create a new one.

Recommended local flow (PowerShell)

```powershell
# 1) Activate the project's virtualenv (adjust path if different)
C:\Users\SAHADA\Desktop\Backend\NLA\lotto\Scripts\Activate.ps1

# 2) Install dependencies (if not already installed)
pip install -r requirements.txt

# 3) For local testing point DATABASE_URL to a sqlite file (this avoids remote DB connectivity issues)
$env:DATABASE_URL = 'sqlite:///C:/Users/SAHADA/Desktop/Backend/NLA/db.sqlite3'

# 4) Run migrations
python manage.py migrate

# 5) (Optional) Create a superuser to access admin
python manage.py createsuperuser

# 6) Run the dev server
python manage.py runserver
```

Notes:
- `NLA/settings.py` loads environment variables via `dotenv` and uses `dj_database_url` — the project expects a `DATABASE_URL` environment variable in production. For local testing override as shown above.
- If the remote Postgres host in `DATABASE_URL` is unreachable, migrations will fail. Use the sqlite override to test locally.

## How to test the new management command

1. Activate the virtualenv (see above).
2. Ensure migrations have been applied (see above). If not, run `python manage.py migrate`.
3. Run the command:

```powershell
python manage.py create_test_betting_data
```

Expected output: the command will print progress and then a short counts summary, e.g.:

```
Creating test betting data...
Test data creation complete
users: 1
game_types: 1
bet_types: 1
game_odds: 1
draws: 1
bets: 1
notifications: 1
You can now run `python manage.py create_test_betting_data` to recreate this data (idempotent).
```

If you get ORM errors like `relation "bet_types" does not exist`, it means migrations haven't been applied or you're pointed at a different DB. Use the sqlite override and rerun `migrate`.

## API overview (high level)

- `GameTypeViewSet` (read-only): list game types, categories, and game odds.
- `DrawViewSet` (read-only): list/retrieve draws, open draws and results endpoints.
- `SubscriptionViewSet`: subscribe/unsubscribe to game types.
- `NotificationViewSet`: list notifications and mark as read.
- `BetViewSet`: place bets (via `PlaceBetSerializer`), view active/history bets, check individual bet results.

The viewsets live in `betting/views.py` and use serializers in `betting/serializers.py`. The `PlaceBetSerializer` performs validation including draw open status, number ranges, stake limits and user balance.

## Important developer notes & caveats

- Timezones: `USE_TZ = True` is set in `settings.py`. Management commands and draw datetimes use `django.utils.timezone` — ensure your environment timezone handling is consistent.
- Tests & automation: There is no dedicated test file for the management command yet. Consider adding a `TestCase` using `call_command('create_test_betting_data')` and assert the created objects.
- Environment variables: `NLA/settings.py` expects several env vars (JWT secret, cloudinary keys, DATABASE_URL). For local dev you can set minimal env vars or rely on local sqlite as shown.
- Dependencies: `requirements.txt` pins Django 4.2.7 and supporting libraries. If your local Python is different, create a fresh virtualenv and install the requirements.

## Next steps / recommended improvements

- Add a simple Django TestCase for `create_test_betting_data` and `check_draw_results` under `betting/tests.py`.
- Add CI pipeline that runs migrations and the basic test case against sqlite.
- Add a README section linking to this file and wiring up developer setup steps.

## Where to find things (quick pointers)

- Models: `betting/models.py`
- APIs: `betting/views.py`, `betting/serializers.py`
- Admin: `betting/admin.py`
- Commands: `betting/management/commands/`

----
If you want, I can:
- add an automated test that calls `create_test_betting_data` and asserts the counts, or
- create a short `docs/DEV_SETUP.md` with more detailed environment setup and debugging steps (for remote DB issues).
Tell me which of those you'd like next.

## API endpoints — examples

Base path for API: `/api/` (see `NLA/urls.py` and `betting/urls.py`). Most endpoints require authentication (Bearer JWT) except read-only endpoints configured with `AllowAny`.

Authentication (JWT)
- Obtain tokens (access + refresh):

  POST /api/token/
  Request body:

  ```json
  {"username": "testuser", "password": "password"}
  ```

  Response:

  ```json
  {
    "access": "<JWT_ACCESS_TOKEN>",
    "refresh": "<JWT_REFRESH_TOKEN>"
  }
  ```

Include the access token in requests that require auth:

  Authorization: Bearer <JWT_ACCESS_TOKEN>

Game types
- List game types (public):

  GET /api/games-types/

  Sample response (array shortened):

  ```json
  [
    {
      "id": 1,
      "name": "Quick 5/11",
      "code": "TEST_GAME",
      "category": "other_games",
      "min_stake": "1.00",
      "max_stake": "100.00",
      "is_active": true
    }
  ]
  ```

- Retrieve details:

  GET /api/games-types/{id}/

Draws
- List draws (filterable):

  GET /api/draws/?upcoming=true

  Sample response item:

  ```json
  {
    "id": 5,
    "game_type": 1,
    "game_name": "Quick 5/11",
    "draw_number": "TEST-20251029120000",
    "draw_date": "2025-10-29",
    "draw_time": "12:00:00",
    "status": "open",
    "betting_opens_at": "2025-10-29T11:00:00Z",
    "betting_closes_at": "2025-10-29T13:00:00Z",
    "is_betting_open": true
  }
  ```

- Get draws that are currently open:

  GET /api/draws/open/

- Retrieve draw results (only available if draw.status == "completed"):

  GET /api/draws/{id}/results/

  Sample successful response:

  ```json
  {
    "draw_number": "TEST-20251029120000",
    "game_name": "Quick 5/11",
    "draw_date": "2025-10-29",
    "winning_numbers": [5, 12, 23, 45, 67],
    "machine_number": "M-1234",
    "total_bets": 42,
    "total_payout": "4200.00"
  }
  ```

Subscriptions
- Toggle subscription (authenticated):

  POST /api/subscriptions/toggle_subscription/
  Request body:

  ```json
  {"game_type_id": 1, "subscribe": true}
  ```

  Response: serialized subscription object (see `UserSubscriptionSerializer`).

- List my subscriptions:

  GET /api/subscriptions/my_subscriptions/

Notifications
- List notifications (authenticated):

  GET /api/notifications/

- Mark a notification read:

  POST /api/notifications/{id}/mark_read/

- Get unread count:

  GET /api/notifications/unread_count/

Bets
- List (user's bets, authenticated):

  GET /api/bets/

- Place a bet (authenticated):

  POST /api/bets/
  Request body (PlaceBetSerializer):

  ```json
  {
    "draw_id": 5,
    "bet_type_id": 1,
    "selected_numbers": [1, 2, 3, 4, 5],
    "stake_amount": "1.00"
  }
  ```

  On success returns the created bet representation (see `BetDetailSerializer` / `BetSerializer`). Example snippet:

  ```json
  {
    "id": 12,
    "bet_number": "BET20251029123456ABCDEF",
    "game_name": "Quick 5/11",
    "bet_type_name": "Direct",
    "draw_number": "TEST-20251029120000",
    "selected_numbers": [1,2,3,4,5],
    "stake_amount": "1.00",
    "potential_winnings": "100.00",
    "status": "active"
  }
  ```

- Active bets endpoint:

  GET /api/bets/active/

- Bet history:

  GET /api/bets/history/

- Check result for a bet (action on bet viewset):

  GET /api/bets/{id}/check_result/

  Response includes `won` boolean and `winnings` amount where applicable.

Auth note: most write actions require a valid JWT `Authorization` header. For testing with `create_test_betting_data` you can use the created `testuser` and password `password` to obtain tokens.

If you want, I can also generate a small Postman collection (JSON) or OpenAPI-compatible spec that lists these endpoints and example payloads — which would you prefer? 
