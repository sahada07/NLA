# NLA Backend

<<<<<<< HEAD
A Django REST API backend for managing users, betting, lotto, and related resources.
=======
This reposjitory contains the backend for the NLA project — a Django REST API for managing users, betting, lotto, and related resources.
>>>>>>> 0677d42e109de9b5d953f1f4302844ff5ccfa09d

## Contents

- `NLA/` — Django project settings and entrypoints
- `betting/` — Betting app with models, serializers, views, and API routes
- `users/` — User management and authentication

## Prerequisites

- Python 3.11+ (developed with Python 3.13)
- pip
- virtualenv or venv 

## Quick Start (Windows PowerShell)

1. **Create and activate a virtual environment:**

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. **Install dependencies:**

```powershell
pip install -r requirements.txt
```

3. **Apply migrations and create a superuser:**

```powershell
python manage.py migrate; python manage.py createsuperuser
```

4. **Start the development server:**

```powershell
python manage.py runserver
```

5. **Run tests:**

```powershell
python manage.py test
```

## API Overview

# User Authentication System Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
5. [Serializers](#serializers)
6. [Security Features](#security-features)
7. [Installation & Setup](#installation--setup)
8. [Usage Examples](#usage-examples)
9. [Error Handling](#error-handling)
10.[Testing](#testing)
11.[PostmanCollection](#postman-collection)

---

## Overview
The Lottery API is a Django REST Framework-based system that provides:

User authentication and management
Lottery betting functionality
Game subscription system
Real-time notifications
Wallet management

Base URL: http://localhost:8000/api


### Key Features
- ✅ User registration with age verification
- ✅ Password change functionality
- ✅ Three user roles: Player, Agent, Administrator
- ✅ Account balance tracking
- ✅ Identity verification status
- ✅ Security question/answer for account recovery

---

## System Architecture

```
┌─────────────────┐
│   Client App    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Endpoints  │
│  (Views)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Serializers    │
│  (Validation)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Models         │
│  - User         │
│  - UserProfile
   - Notification
   - Subscription 
   - Games
│  - Wallet
└─────────────────┘
```

---

## Data Models

### User Model
Extends Django's `AbstractUser` with betting-specific fields.

**Fields:**
| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `user_type` | CharField | User role (player/agent/admin) | Yes |
| `date_of_birth` | DateField | User's date of birth | No |
| `phone_number` | CharField(15) | Contact number | No |
| `address` | TextField | Physical address | No |
| `id_verified` | BooleanField | KYC verification status | Yes (default: False) |
| `account_balance` | DecimalField | Current balance | Yes (default: 0.00) |
| `created_at` | DateTimeField | Account creation timestamp | Auto |
| `updated_at` | DateTimeField | Last update timestamp | Auto |

**Inherited Fields from AbstractUser:**
- `username` (unique)
- `email`
- `first_name`
- `last_name`
- `password` (hashed)
- `is_active`
- `is_staff`
- `is_superuser`

### UserProfile Model
One-to-One relationship with User for security features.

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `user` | OneToOneField | Link to User model |
| `security_question` | CharField(255) | Recovery question |
| `security_answer` | CharField(255) | Answer (should be hashed) |
| `failed_login_attempts` | IntegerField | Counter for failed logins |
| `account_locked_until` | DateTimeField | Lockout expiration time |

---

## API Endpoints

### 1. User Registration
**Endpoint:** `POST /api/auth/register/`

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1995-06-15",
  "phone_number": "+233501234567",
  "user_type": "player"
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "player",
  "created_at": "2025-10-03T10:30:00Z"
}
```

**Error Response (400):**
```json
{
  "password": ["Password fields didn't match."],
  "date_of_birth": ["You must be 18 years or older to register."]
}
```

---

### 2. User Login
**Endpoint:** `POST /api/auth/login/`

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "user_type": "player",
    "account_balance": "0.00"
  }
}
```

**Error Responses:**
- `400`: Invalid credentials
- `403`: Account temporarily locked

---

### 3. Get User Profile
**Endpoint:** `GET /api/auth/profile/`

**Headers:**
```
Authorization: Bearer <token>
```

**Success Response (200):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1995-06-15",
  "phone_number": "+233501234567",
  "user_type": "player",
  "account_balance": "150.00"
}
``

### 4. Change Password
**Endpoint:** `POST /api/auth/change-password/`

**Request Body:**
```json
{
  "old_password": "SecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

## Serializers

### UserRegistrationSerializer
**Purpose:** Validates and creates new user accounts

**Validations:**
1. Password confirmation match
2. Age verification (18+)
3. Django's built-in password validators:
   - Minimum length
   - Common password check
   - Numeric-only check
   - Similarity to user attributes

**Custom Validation Logic:**
```python
# Age calculation
age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
if age < 18:
    raise ValidationError("You must be 18 years or older")
```

### UserLoginSerializer
**Purpose:** Authenticates users and checks account status

**Validations:**
1. Username and password provided
2. Credentials are valid
3. Account is not locked

### UserProfileSerializer
**Purpose:** Serializes user profile data for display

**Fields:** Read-only representation of user data

### ChangePasswordSerializer
**Purpose:** Validates password change requests

**Validations:**
1. Old password is correct
2. New password meets Django's password requirements

---

## Security Features

### 1. Age Verification
- **Requirement:** Users must be 18+ years old
- **Implementation:** Date of birth validation during registration
- **Legal Compliance:** Required for betting/gambling platforms

### 2. Account Lockout Protection
- **Purpose:** Prevent brute-force attacks
- **Mechanism:** 
  - Tracks failed login attempts in `UserProfile.failed_login_attempts`
  - Locks account after threshold (e.g., 5 failed attempts)
  - Sets `account_locked_until` timestamp
  - Automatically unlocks after timeout period

### 3. Password Security
- Uses Django's built-in password hashing (PBKDF2)
- Password validation rules enforced
- Old password verification required for changes

### 4. Authentication Tokens
- Implement JWT or Django Rest Framework tokens
- Token-based authentication for API requests

---

## Installation & Setup

### Prerequisites
```bash
Python 3.8+
Django 4.0+
Django Rest Framework 3.14+
```

### Installation Steps

1. **Install dependencies:**
```bash
pip install django djangorestframework
```

2. **Add to `settings.py`:**
```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'your_auth_app',
]

AUTH_USER_MODEL = 'your_auth_app.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

3. **Create migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create signal for UserProfile (in models.py):**
```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
```

---

## Usage Examples

### Example 1: Register a New User

**Python (requests):**
```python
import requests

url = "http://localhost:8000/api/auth/register/"
data = {
    "username": "newplayer",
    "email": "player@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "New",
    "last_name": "Player",
    "date_of_birth": "2000-01-01",
    "phone_number": "+233501234567",
    "user_type": "player"
}

response = requests.post(url, json=data)
print(response.json())
```

**JavaScript (fetch):**
```javascript
fetch('http://localhost:8000/api/auth/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'newplayer',
    email: 'player@example.com',
    password: 'SecurePass123!',
    password_confirm: 'SecurePass123!',
    first_name: 'New',
    last_name: 'Player',
    date_of_birth: '2000-01-01',
    phone_number: '+233501234567',
    user_type: 'player'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Example 2: Login

**cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newplayer",
    "password": "SecurePass123!"
  }'
```

### Example 3: Get Profile (Authenticated)

**Python:**
```python
import requests

url = "http://localhost:8000/api/auth/profile/"
headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE"
}

response = requests.get(url, headers=headers)
print(response.json())
```

---

## Error Handling

### Common Error Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 400 | Bad Request | Invalid data, validation errors |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Account locked, insufficient permissions |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Server Error | Database issues, code errors |

### Error Response Format
```json
{
  "field_name": ["Error message"],
  "another_field": ["Another error message"]
}
```

---

## Testing

### Unit Test Example

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta

User = get_user_model()

class UserRegistrationTests(TestCase):
    def test_user_creation(self):
        """Test user can be created with valid data"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            date_of_birth=date.today() - timedelta(days=365*20)
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('TestPass123!'))
    
    def test_underage_registration(self):
        """Test that users under 18 cannot register"""
        from rest_framework.test import APIClient
        
        client = APIClient()
        data = {
            'username': 'younguser',
            'email': 'young@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'date_of_birth': date.today() - timedelta(days=365*16),
            'phone_number': '+233501234567',
            'user_type': 'player'
        }
        
        response = client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('date_of_birth', response.data)
```

## Additional Notes

### Future Enhancements
1. Two-factor authentication (2FA)
2. Email verification
3. Password reset via email
4. Session management
5. IP-based rate limiting
6. Logging and audit trails

### Security Recommendations
1. Hash security answers (don't store plain text)
2. Implement HTTPS in production
3. Set proper CORS policies
4. Use environment variables for secrets
5. Regular security audits
6. Implement CAPTCHA for login

### Compliance Considerations
- GDPR compliance for user data
- Age verification audit trail
- Data retention policies
- Right to be forgotten implementation

---

## Support & Maintenance

**Contact:** [Your contact information]  
**Last Updated:** October 3, 2025  
**Version:** 1.0.0

The project uses Django REST Framework with DRF routers to register ViewSets. The `betting` app exposes several endpoints in `betting/urls.py`:

- `GET /game-types/` — List and retrieve game types
- `GET /subsscriptions/` — List and retrieve subscriptions (note: spelled `subsscriptions` in code)
- `GET /notifications/` — List and retrieve notifications

### Known Typo

In `betting/urls.py`, the subscription route is registered as:

```python
router.register('subsscriptions', SubscriptionViewSet, basename='subscriptions')
```

If you want the endpoint to be `/subscriptions/`, change it to:

```python
router.register('subscriptions', SubscriptionViewSet, basename='subscriptions')
```

## Developer Notes

- **Virtual environments:** Do not commit virtual environment folders (e.g., `lotto/`, `.venv/`) — add them to `.gitignore`
- **Secrets management:** Keep secrets, API keys, and database URLs out of source control. Use environment variables or a `.env` file
- **Deployment:** Follow Django best practices for production (static files, `ALLOWED_HOSTS`, secure settings, HTTPS)

## Contributing

1. Create a branch for your changes
2. Run tests locally to ensure nothing breaks
3. Open a pull request with a clear description of what changed and why

## License

[Add your license information here]

---

**Last Updated:** October 2025  
**Python Version:** 3.13  
**Django Version:** [Add version from requirements.txt]