# Step 23 Auth Real-device Test Preparation Result

Date: 2026-06-14

## Purpose

Step 23 prepares the Android real-device authentication flow test after Step 22 implemented signup, admin approval, username/password login, 7-day refresh token lifetime, device-token session restore, and connected/disconnected status.

## Server API Smoke Result

Smoke user:

```text
auth_smoke_20260614052616
```

Result:

| Check | Result |
| --- | --- |
| `GET /api/health/` | 200 |
| `POST /api/auth/signup/` | 201 |
| Signup approval status | `pending` |
| Pending login reject | 400 |
| Shell approval | OK |
| `approved_at` auto set | OK |
| Approved login | 200 |
| Login response includes access | OK |
| Login response includes refresh | OK |
| Login response includes user | OK |
| Login response includes device_token | OK |
| Login response includes message | OK |
| `POST /api/auth/session/refresh/` | 200, `connected=true` |
| Wrong device token refresh | 403, `connected=false` |
| `POST /api/auth/refresh/` | 200 |
| `GET /api/auth/protected-test/` | 200 |
| Refresh token lifetime | 7 days |

## Admin Approval Procedure

1. Open Django Admin.
2. Open `Accounts` > `Account profiles`.
3. Select the signup user.
4. Change `approval_status` to `approved`.
5. Save.

Bulk action:

1. Open `Account profiles`.
2. Select one or more pending profiles.
3. Choose `Approve selected profiles`.
4. Run the action.

Emergency shell approval:

```bash
python manage.py shell -c "from accounts.models import AccountProfile; p=AccountProfile.objects.get(user__username='USERNAME'); p.approval_status='approved'; p.save(update_fields=['approval_status','updated_at'])"
```

When `approval_status` becomes `approved`, `approved_at` is set automatically if it was empty. `approved_by` is set when the Django Admin approve action is used.

## APK

Build command:

```bash
cd mobile/MDetect
./gradlew assembleDebug
```

APK path:

```text
mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk
```

Install with adb:

```bash
adb install -r mobile/MDetect/app/build/outputs/apk/debug/app-debug.apk
```

Manual install:

1. Copy `app-debug.apk` to the phone.
2. Open it from a file manager.
3. Allow installing unknown apps.
4. Install.
5. Launch MDetect.

## Scenario A: New Signup, Approval, Login

1. Install and launch the app.
2. Confirm initial status is `Disconnected`.
3. Confirm the landing button says `로그인`.
4. Tap `로그인`.
5. Tap `회원가입`.
6. Enter username.
7. Enter phone number.
8. Enter password.
9. Enter confirm password.
10. Tap `가입 신청`.
11. Confirm the approval-pending signup message.
12. Approve the user in Django Admin.
13. Return to the app login screen.
14. Enter username/password.
15. Tap `로그인`.
16. Confirm `{{username}}님, 반갑습니다`.
17. Confirm Home opens.
18. Confirm `Connected`.

## Scenario B: Pending Login Reject

1. Create a new signup user.
2. Do not approve the profile.
3. Try login.
4. Confirm the app stays on login.
5. Confirm approval/pending error text is visible.

## Scenario C: App Restart Session Restore

1. Login successfully with an approved account.
2. Close the app.
3. Reopen the app within 7 days.
4. Confirm automatic session restore using `refresh_token + device_token`.
5. Confirm Home opens or status remains `Connected`.
6. Confirm password entry is not required.

## Scenario D: Reset App Auth State

There is no logout screen yet. Reset the app by clearing Android app data:

```text
Android Settings -> Apps -> MDetect -> Storage -> Clear data
```

or reinstall the APK.

## Failure Checklist

- Server URL wrong: fix Android Settings server URL.
- Signup returns duplicate error: use a new username/phone number.
- Login fails after signup: approve `AccountProfile`.
- Session restore fails: confirm the same app install still has the saved `device_token`.
- Device token mismatch: clear app data and log in again.
- Server token expired: log in again.
- Admin page missing: log in as a staff/superuser account.

## Next Improvements

- Add explicit logout.
- Add clearer parsed server validation errors on Android.
- Add encrypted token storage before broader distribution.
