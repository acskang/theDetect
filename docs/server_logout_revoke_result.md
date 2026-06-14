# Step 25 Server Logout / Revoke Result

Date: 2026-06-14

## Purpose

Step 25 adds server-side logout for the Android auth flow. Step 24 only cleared local Android tokens. Step 25 also invalidates the server session state so a logged-out app cannot restore the same session with the old `refresh_token + device_token`.

## Endpoint

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

## Revoke Policy

- Refresh tokens are blacklisted with SimpleJWT `token_blacklist`.
- `SIMPLE_JWT.BLACKLIST_AFTER_ROTATION` is enabled, so rotated refresh tokens cannot be reused.
- On logout, the matching `AccountProfile.device_token` is cleared.
- `/api/auth/session/refresh/` rejects empty, missing, or mismatched device tokens.
- Logout currently requires a valid refresh token, an approved profile, and a matching device token.

## Android Fallback

Android calls `/api/auth/logout/` during logout, then clears local DataStore state whether the server call succeeds or fails.

If the server revoke call fails, the app still logs out locally and shows:

```text
로컬 로그아웃되었습니다. 서버 세션 해제는 실패했을 수 있습니다.
```

This keeps the phone usable for testing even when the network is unavailable.

## Smoke Result

Local Django API smoke test result:

```text
login_status: 200
logout_status: 200
logged_out: true
device_token_cleared: true
session_refresh_status_after_logout: 401
jwt_refresh_status_after_logout: 401
```

This confirms the old session cannot be restored after logout.

## Curl Manual Test

```bash
TOKEN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"mdetect_smoke","password":"local-smoke-password"}')

REFRESH=$(echo "$TOKEN_RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['refresh'])")
DEVICE=$(echo "$TOKEN_RESPONSE" | python -c "import sys,json; print(json.load(sys.stdin)['device_token'])")

curl -X POST http://127.0.0.1:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\",\"device_token\":\"$DEVICE\"}"

curl -X POST http://127.0.0.1:8000/api/auth/session/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\",\"device_token\":\"$DEVICE\"}"
```

The final session refresh must fail.

## Manual Android Scenario

1. Login from the Android app.
2. Confirm Home shows `Connected`.
3. Tap `로그아웃`.
4. Confirm the logout dialog.
5. Android calls the server logout API.
6. Android clears local tokens/user/device state.
7. Restart the app.
8. Confirm automatic session restore fails.
9. Confirm the app shows login-required or disconnected state.

## Deferred Hardening

Keystore-backed token storage and full device-session audit history are deferred to a later security hardening step.
