# MDetect App Auth API Guide

## Signup

```http
POST /api/auth/signup/
Content-Type: application/json
```

```json
{
  "username": "user01",
  "phone_number": "01012345678",
  "password": "StrongPass123!",
  "confirm_password": "StrongPass123!"
}
```

Success:

```json
{
  "registered": true,
  "approval_status": "pending",
  "message": "가입 신청이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다."
}
```

Step 23 smoke result confirmed signup returns HTTP 201 and creates a pending profile.

## Login

```http
POST /api/auth/login/
```

```json
{
  "username": "user01",
  "password": "StrongPass123!"
}
```

Approved users receive:

```json
{
  "access": "...",
  "refresh": "...",
  "user": {
    "id": 1,
    "username": "user01",
    "phone_number": "01012345678",
    "approval_status": "approved"
  },
  "device_token": "...",
  "message": "user01님, 반갑습니다"
}
```

Pending, rejected, suspended, or profile-missing users cannot log in.

Step 23 smoke result confirmed pending users are rejected and approved users receive `access`, `refresh`, `user`, `device_token`, and `message`.

## App Session Refresh

```http
POST /api/auth/session/refresh/
```

Step 23 smoke result confirmed valid `refresh + device_token` returns `connected=true`, while a wrong `device_token` returns `connected=false` with HTTP 403.

```json
{
  "refresh": "...",
  "device_token": "..."
}
```

Success:

```json
{
  "connected": true,
  "access": "...",
  "refresh": "...",
  "user": {
    "id": 1,
    "username": "user01",
    "phone_number": "01012345678",
    "approval_status": "approved"
  },
  "message": "user01님, 반갑습니다"
}
```

Failure examples:

```json
{
  "connected": false,
  "reason": "session_expired",
  "message": "세션이 만료되었습니다. 다시 로그인하세요."
}
```

## Existing JWT Refresh

The existing endpoint remains available:

```text
POST /api/auth/refresh/
```

Android uses `/api/auth/session/refresh/` for startup restore because it validates the app `device_token`.

## Logout

```http
POST /api/auth/logout/
```

Request:

```json
{
  "refresh": "...",
  "device_token": "..."
}
```

Success:

```json
{
  "logged_out": true,
  "message": "로그아웃되었습니다."
}
```

Behavior:

- The refresh token is blacklisted with SimpleJWT `token_blacklist`.
- The matching `AccountProfile.device_token` is cleared.
- Later `/api/auth/session/refresh/` calls with the old token pair fail.
- Wrong or missing `device_token` returns an error and does not revoke another device session.

Step 25 smoke confirmed logout returns HTTP 200, clears `device_token`, and makes both app session refresh and JWT refresh fail with the old refresh token.

## Smoke Test Command Pattern

Use a unique username such as:

```text
auth_smoke_<timestamp>
```

Required checks:

- signup success creates `pending`
- pending login fails
- approval allows login
- login returns access/refresh/user/device_token/message
- session refresh succeeds
- wrong device token fails
- default JWT refresh succeeds
- protected-test succeeds with the access token
- logout succeeds
- session refresh after logout fails
- blacklisted refresh reuse fails
