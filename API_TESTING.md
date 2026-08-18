# API Testing Guide

Step-by-step examples for exercising every endpoint with `curl`, using the
sample team seeded by `python manage.py seed_demo`:

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
`MgrPass123`, `alice` / `bob` / `carol` / `dave` / `UserPass123`.

All examples assume the server is running at `http://127.0.0.1:8000`
(`python manage.py runserver`). Every endpoint except `/api/token/` requires
an `Authorization: Bearer <access_token>` header.

A ready-made Postman collection covering the same requests lives in
[`postman/`](postman/) — see the README's **Postman collection** section for
how to import and run it.

---

## 1. Authentication

### 1.1 Login — `POST /api/token/`

Works for any role; returns an `access` token (send on every request) and a
`refresh` token.

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "AdminPass123"}'
```

```json
{
  "refresh": "eyJhbGciOi...",
  "access": "eyJhbGciOi..."
}
```

Save the access token to a shell variable to reuse below:

```bash
ADMIN=$(curl -s -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "AdminPass123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access'])")

MGR_SALES=$(curl -s -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "mgr_sales", "password": "MgrPass123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access'])")

ALICE=$(curl -s -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "UserPass123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access'])")

BOB=$(curl -s -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "UserPass123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access'])")
```

**Failure case** — wrong password:

```bash
curl -i -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "wrong"}'
# 401 Unauthorized — {"detail": "No active account found with the given credentials"}
```

### 1.2 Refresh token — `POST /api/token/refresh/`

```bash
curl -X POST http://127.0.0.1:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH_TOKEN\"}"
```

Returns a new `access` token (and a new `refresh` token, since
`ROTATE_REFRESH_TOKENS` is on).

---

## 2. Registration — Admin only

### 2.1 `POST /api/register/`

**Create a Manager** (no `manager` field — Managers don't report to anyone):

```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Authorization: Bearer $ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"username": "mgr_ops", "password": "MgrPass123", "role": "MANAGER"}'
# 201 Created — {"id": 8, "username": "mgr_ops", ..., "role": "MANAGER", "manager": null}
```

**Create a User under a Manager** (replace `2` with `mgr_sales`'s id from
`GET /api/users/`):

```bash
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Authorization: Bearer $ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"username": "erin", "password": "UserPass123", "role": "USER", "manager": 2}'
# 201 Created
```

**Failure — non-admin tries to register a user:**

```bash
curl -i -X POST http://127.0.0.1:8000/api/register/ \
  -H "Authorization: Bearer $MGR_SALES" \
  -H "Content-Type: application/json" \
  -d '{"username": "x", "password": "UserPass123", "role": "USER"}'
# 403 Forbidden
```

**Failure — assigning a `manager` to a non-USER role:**

```bash
curl -i -X POST http://127.0.0.1:8000/api/register/ \
  -H "Authorization: Bearer $ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"username": "mgr_bad", "password": "MgrPass123", "role": "MANAGER", "manager": 2}'
# 400 Bad Request — {"manager": ["Only accounts with role=USER may be assigned to a manager."]}
```

---

## 3. Users

### 3.1 List users — `GET /api/users/`

```bash
# Admin — sees everyone
curl http://127.0.0.1:8000/api/users/ -H "Authorization: Bearer $ADMIN"

# Manager — sees only their own team (alice, bob)
curl http://127.0.0.1:8000/api/users/ -H "Authorization: Bearer $MGR_SALES"

# User — forbidden
curl -i http://127.0.0.1:8000/api/users/ -H "Authorization: Bearer $ALICE"
# 403 Forbidden
```

### 3.2 Retrieve a specific user — `GET /api/users/{id}/`

```bash
# Manager viewing their own team member (alice's id, e.g. 4) — OK
curl http://127.0.0.1:8000/api/users/4/ -H "Authorization: Bearer $MGR_SALES"

# Manager viewing someone outside their team (carol's id, e.g. 6) — denied
curl -i http://127.0.0.1:8000/api/users/6/ -H "Authorization: Bearer $MGR_SALES"
# 403 Forbidden
```

### 3.3 Own profile — `GET/PUT/PATCH /api/profile/`

Every role manages their own profile here (role/manager stay read-only, even
for the user themself):

```bash
curl http://127.0.0.1:8000/api/profile/ -H "Authorization: Bearer $ALICE"

curl -X PATCH http://127.0.0.1:8000/api/profile/ \
  -H "Authorization: Bearer $ALICE" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Alice", "last_name": "Nguyen"}'
# 200 OK

# Attempting to self-promote is silently ignored (role is read-only)
curl -X PATCH http://127.0.0.1:8000/api/profile/ \
  -H "Authorization: Bearer $ALICE" \
  -H "Content-Type: application/json" \
  -d '{"role": "ADMIN"}'
# 200 OK — role in the response is still "USER"
```

---

## 4. Tasks

### 4.1 List tasks — `GET /api/tasks/`

```bash
curl http://127.0.0.1:8000/api/tasks/ -H "Authorization: Bearer $ADMIN"       # all tasks
curl http://127.0.0.1:8000/api/tasks/ -H "Authorization: Bearer $MGR_SALES"   # own + team's tasks
curl http://127.0.0.1:8000/api/tasks/ -H "Authorization: Bearer $ALICE"       # only alice's tasks
```

### 4.2 Create a task — `POST /api/tasks/`

```bash
# User creates their own task (assigned_to must be themselves)
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Bearer $ALICE" \
  -H "Content-Type: application/json" \
  -d '{"title": "Prep demo", "description": "Slides for Friday", "assigned_to": 4}'
# 201 Created

# Manager creates a task for a team member
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Bearer $MGR_SALES" \
  -H "Content-Type: application/json" \
  -d '{"title": "Follow up with lead", "assigned_to": 5}'
# 201 Created (bob, id 5, is on mgr_sales's team)
```

**Failure — assigning outside your scope:**

```bash
# alice tries to create a task for bob
curl -i -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Bearer $ALICE" \
  -H "Content-Type: application/json" \
  -d '{"title": "Not mine", "assigned_to": 5}'
# 400 Bad Request — {"assigned_to": ["You may only assign tasks to yourself."]}

# mgr_sales tries to create a task for carol (on mgr_support's team)
curl -i -X POST http://127.0.0.1:8000/api/tasks/ \
  -H "Authorization: Bearer $MGR_SALES" \
  -H "Content-Type: application/json" \
  -d '{"title": "Not my team", "assigned_to": 6}'
# 400 Bad Request
```

### 4.3 Retrieve/update a task — `GET / PUT / PATCH /api/tasks/{id}/`

```bash
# Owner updates their own task's status
curl -X PATCH http://127.0.0.1:8000/api/tasks/1/ \
  -H "Authorization: Bearer $ALICE" \
  -H "Content-Type: application/json" \
  -d '{"status": "DONE"}'
# 200 OK

# That task's manager can also update it
curl -X PATCH http://127.0.0.1:8000/api/tasks/1/ \
  -H "Authorization: Bearer $MGR_SALES" \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'
# 200 OK
```

**Failure — accessing a task outside your scope** (queryset filtering makes
this a 404, not a 403 — you can't even tell the row exists):

```bash
curl -i http://127.0.0.1:8000/api/tasks/1/ -H "Authorization: Bearer $BOB"
# 404 Not Found
```

### 4.4 Delete a task — `DELETE /api/tasks/{id}/` — Admin only

```bash
# Manager tries to delete a visible task — denied
curl -i -X DELETE http://127.0.0.1:8000/api/tasks/1/ -H "Authorization: Bearer $MGR_SALES"
# 403 Forbidden

# Admin deletes it
curl -i -X DELETE http://127.0.0.1:8000/api/tasks/1/ -H "Authorization: Bearer $ADMIN"
# 204 No Content
```

---

## 5. Interactive docs

Swagger UI (browse and try every endpoint from the browser, with the same
"Authorize" flow for the access token):

```
http://127.0.0.1:8000/api/docs/
```

Click **Authorize**, paste `Bearer <access_token>`, and every request below
runs with that role.

---

## 6. Running the automated test suite

All of the scenarios above (plus more edge cases) are codified as automated
tests:

```bash
python manage.py test -v 2
```

23 tests cover registration restrictions, user-list/detail scoping, profile
self-service, task-assignment validation, task queryset scoping, and
delete-is-admin-only — the same access rules demonstrated with curl above.
