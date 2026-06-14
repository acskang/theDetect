# Android Auth Manual Test Guide

## Prerequisites

1. Run Django server.
2. Install the latest debug APK.
3. Confirm the Android app server URL points to the server.
4. Keep Django Admin open with a staff/superuser account for profile approval.

See `docs/auth_real_device_test_result.md` for the Step 23 server smoke result and APK path.

## Signup Test

1. Launch MDetect.
2. Confirm the landing page status starts as `Disconnected`.
3. Tap `로그인`.
4. Tap `회원가입`.
5. Enter username, phone number, password, and confirm password.
6. Tap `가입 신청`.
7. Confirm the app shows:

```text
가입 신청이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다.
```

## Admin Approval

1. Open Django Admin.
2. Open `Account profiles`.
3. Find the new user profile.
4. Set `approval_status=approved` or run the approve action.
5. Save.

Emergency shell approval:

```bash
python manage.py shell -c "from accounts.models import AccountProfile; p=AccountProfile.objects.get(user__username='USERNAME'); p.approval_status='approved'; p.save(update_fields=['approval_status','updated_at'])"
```

`approved_at` is set automatically when the profile is saved as approved. `approved_by` is set when the Django Admin approve action is used.

## First Login

1. Return to the Android login screen.
2. Enter username/password.
3. Tap `로그인`.
4. Confirm the welcome message:

```text
{{username}}님, 반갑습니다
```

5. Confirm Home shows `Auth Status: Connected`.

## Session Restore

1. Close the app.
2. Reopen the app within 7 days.
3. The app sends stored `refresh_token + device_token` to the server.
4. Confirm it opens as connected without entering the password again.

## Pending Login Reject

1. Create a new signup user.
2. Do not approve the profile.
3. Try login.
4. Confirm the app does not move to Home.
5. Confirm an approval-required or login failure message is visible.

## Logout / Reset App State

Step 25 logout calls the server revoke API and then clears local Android state.

1. Login successfully.
2. Open Home or Settings.
3. Tap `로그아웃`.
4. Confirm the dialog.
5. Confirm status changes to `Disconnected` or `Login required`.
6. Confirm user info and welcome message are gone.
7. Close and reopen the app.
8. Confirm automatic session restore does not occur.

If a full reset is still needed:

```text
Android Settings -> Apps -> MDetect -> Storage -> Clear data
```

If the server logout call fails, the app still clears local tokens. In that case the app may show:

```text
로컬 로그아웃되었습니다. 서버 세션 해제는 실패했을 수 있습니다.
```

Server-side logout blacklists the refresh token and clears the matching `device_token`. After successful logout, the old `refresh_token + device_token` must not restore the session.

## Failure Checks

- Pending user login should fail with an approval message.
- Wrong password should stay on login and show an error.
- Invalid or missing `device_token` should show login required.
- Phone number is never used as device proof; it is only member information.
