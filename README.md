# JWT Auth RBAC API

A Django REST Framework API with JWT authentication and role-based access
control across three roles: **Admin**, **Manager**, **User**.

## Stack

- Python 3.x, Django 4.2
- Django REST Framework
- djangorestframework-simplejwt (JWT auth)
- drf-spectacular (OpenAPI schema + Swagger UI)
- SQLite (default; swap `DATABASES` in `config/settings.py` for Postgres)

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # optional, defaults work out of the box

python manage.py makemigrations
python manage.py migrate

# Either create your own superuser...
python manage.py createsuperuser

# ...or seed a ready-made sample team structure:
python manage.py seed_demo

python manage.py runserver
```

Swagger UI: `http://127.0.0.1:8000/api/docs/`
Django admin: `http://127.0.0.1:8000/admin/`

Run tests:

```bash
python manage.py test
```

For a full walkthrough of every endpoint with runnable `curl` examples
(success and failure cases for each role), see
[API_TESTING.md](API_TESTING.md).

## Roles & permission logic

Role lives on a custom `User` model (`accounts.User.role`), one of
`ADMIN` / `MANAGER` / `USER`. Team structure is a single self-referential
`manager` field on `User`: each `USER` points at the `MANAGER` they report to.
Managers and Admins leave `manager` null.

| Action | Admin | Manager | User |
|---|---|---|---|
| Register a new user | ✅ any role | ❌ | ❌ |
| List users | ✅ all users | ✅ own team only | ❌ (use `/api/profile/`) |
| View a specific user | ✅ any | ✅ own team member only | ❌ |
| View/edit own profile | ✅ | ✅ | ✅ |
| List tasks | ✅ all | ✅ own + team's | ✅ own only |
| Create task | ✅ (any assignee) | ✅ (self or team member) | ✅ (self only) |
| Update task | ✅ any | ✅ own or team member's | ✅ own only |
| Delete task | ✅ | ❌ | ❌ |

Enforcement happens in two layers:

1. **Queryset filtering** (`get_queryset` in `accounts/views.py` and
   `tasks/views.py`) — a role never even sees rows outside its scope, so an
   out-of-scope object lookup returns `404`, not `403`.
2. **Object/action permissions** (`accounts/permissions.py`,
   `tasks/permissions.py`) — govern what a role may do to a row it can see
   (e.g. only Admin may `DELETE` a task).

`accounts/signals.py` uses a `pre_save` signal to guarantee every user always
has a valid role, defaulting to `USER` if left blank.

## Endpoints

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/token/` | Login — returns `access` + `refresh` JWT |
| POST | `/api/token/refresh/` | Refresh an access token |
| POST | `/api/register/` | Admin only — create a user, assign role/manager |
| GET | `/api/users/` | Admin: all. Manager: own team. User: 403 |
| GET | `/api/users/{id}/` | Admin: any. Manager: own team member only |
| GET/PUT/PATCH | `/api/profile/` | Every role — their own profile |
| GET | `/api/tasks/` | All roles, filtered per table above |
| POST | `/api/tasks/` | Manager, User (Admin too) |
| GET | `/api/tasks/{id}/` | Owner, owner's Manager, or Admin |
| PUT/PATCH | `/api/tasks/{id}/` | Owner, owner's Manager, or Admin |
| DELETE | `/api/tasks/{id}/` | Admin only |
| GET | `/api/docs/` | Swagger UI |

## Sample team structure (from `seed_demo`)

```
admin (ADMIN)
├─ mgr_sales (MANAGER)
│   ├─ alice (USER)
│   └─ bob   (USER)
└─ mgr_support (MANAGER)
    ├─ carol (USER)
    └─ dave  (USER)
```

Credentials: `admin` / `AdminPass123`, `mgr_sales` & `mgr_support` /
`MgrPass123`, `alice`/`bob`/`carol`/`dave` / `UserPass123`.

## Example usage

**Login**

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "mgr_sales", "password": "MgrPass123"}'
```

**Admin registers a new user under a manager**

```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "erin", "password": "UserPass123", "role": "USER", "manager": 3}'
```

**Manager lists their team** — returns only `alice` and `bob`, never `carol`/`dave`:

```bash
curl http://127.0.0.1:8000/api/users/ -H "Authorization: Bearer <mgr_sales_access_token>"
```

**User creates their own task**

```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Bearer <alice_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Prep demo", "assigned_to": 4}'
```

Attempting the same request with `"assigned_to"` set to `bob`'s id returns
`400 Bad Request` — a User may only assign tasks to themselves.

**Access-denied examples**

- `carol` (User) calling `GET /api/tasks/{bob's task id}/` → `404 Not Found`
  (outside her queryset).
- `mgr_sales` (Manager) calling `DELETE /api/tasks/{alice's task id}/` →
  `403 Forbidden` (visible, but only Admin may delete).
- `bob` (User) calling `GET /api/users/` → `403 Forbidden`.

## Postman collection

A ready-to-import collection and environment live in [`postman/`](postman/):

- `Django-JWT-RBAC.postman_collection.json`
- `Django-JWT-RBAC.postman_environment.json`

Import both into Postman, select the "Django JWT RBAC - Local" environment, and:

1. Run `python manage.py seed_demo` first so the default credentials
   (`admin`/`mgr_sales`/`alice`, passwords as in the environment file) exist.
2. Run the three requests in **Auth** (`Login - Admin`, `Login - Manager`,
   `Login - User`) — each has a test script that saves its access token into
   `admin_access` / `manager_access` / `user_access` collection variables
   used by every other request.
3. Set the `user_id` and `manager_id` collection variables to `alice`'s and
   `mgr_sales`'s ids (visible in the `List Users - as Admin` response) before
   running the **Users** → *Register User* and **Tasks** → *Create Task*
   requests.
4. Run the **Users** and **Tasks** folders to see the same role-scoping and
   403/404 behavior documented above, straight from Postman.

## Project layout

```
config/     settings, root urls, wsgi/asgi
accounts/   custom User model, roles, team (manager FK), auth-adjacent endpoints
tasks/      Task model + role-scoped CRUD API
```
# Django-JWT-role-based-API
