# Android Logout Result

Date: 2026-06-14

## Purpose

Step 24 added an in-app local logout/token clear action to MDetect Android. Step 25 extends logout so Android first calls the server logout API and then clears local app state.

## Local Logout Behavior

Logout deletes the Android DataStore values for:

```text
access_token
refresh_token
device_token
user_id
auth_username
phone_number
approval_status
connected_status
auth_message
legacy username/password settings
```

After logout:

- Auth status becomes `Disconnected` or `Login required`.
- User info is cleared from Home.
- Welcome message is cleared.
- Detections and history are cleared from current UI state.
- The app navigates back to the landing screen.
- Relaunching the app should not restore the previous session because `refresh_token + device_token` are gone.

## UI

Logout is available from:

- Home: `로그아웃`
- Settings: `로그아웃`

The app shows a confirmation dialog:

```text
로그아웃하시겠습니까?
저장된 세션 정보가 삭제되고 다시 로그인해야 합니다.
```

Buttons:

```text
취소
로그아웃
```

## Server Logout

Step 25 adds:

```text
POST /api/auth/logout/
```

Android sends the stored `refresh_token + device_token`. The server blacklists the refresh token and clears the matching server-side `device_token`.

If server logout fails, Android still clears local tokens and shows:

```text
로컬 로그아웃되었습니다. 서버 세션 해제는 실패했을 수 있습니다.
```

Keystore-backed encrypted token storage remains a future hardening task.

## Manual Test A: Login Then Logout

1. Launch the app.
2. Login with an approved account.
3. Confirm Home shows `Connected`.
4. Tap `로그아웃` from Home or Settings.
5. Confirm the dialog.
6. Confirm the app returns to the landing screen.
7. Confirm status is `Disconnected` or `Login required`.
8. Confirm user info and welcome message are not shown.

## Manual Test B: Restart After Logout

1. Complete logout.
2. Close the app.
3. Reopen the app.
4. Confirm automatic session restore does not occur because local tokens are gone and the server device session was revoked.
5. Confirm the login button is shown.

## Manual Test C: Auth API After Logout

1. Complete logout.
2. Try Model Update or Server Mode.
3. Confirm the app shows login/auth failure messaging.
4. Confirm the app does not crash.
