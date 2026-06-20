# theDetect App Auth Flow Design

## Overview

Step 22 replaces the MVP auto-login assumption with an app authentication flow for signup, administrator approval, first login, device-bound session restore, and connected/disconnected status.

## Signup

Android sends:

```text
username
phone_number
password
confirm_password
```

The server validates required fields, duplicate username, duplicate normalized phone number, password confirmation, and Django password validators. Successful signup creates a Django user and `AccountProfile` with:

```text
approval_status=pending
```

No JWT is issued at signup.

## Approval

Administrators approve users in Django admin by editing `AccountProfile.approval_status` to `approved` or using the approve action. Only approved users can log in.

## First Login

The app logs in with `username/password` through:

```text
POST /api/auth/login/
```

The server returns access, refresh, user profile payload, welcome message, and a server-generated `device_token`.

## Session Restore

On app startup, Android sends:

```text
refresh_token + device_token
```

to:

```text
POST /api/auth/session/refresh/
```

If the refresh token is valid, the user is approved, and the device token matches the profile, the server issues new access and refresh tokens and the app enters `Connected`.

## JWT Lifetime

Access tokens are short-lived:

```text
30 minutes
```

Refresh tokens last:

```text
7 days
```

Refresh rotation is enabled, so successful refresh returns a new refresh token and extends the app session while the user keeps opening the app within the valid window.

## Phone Number Policy

Phone number is stored as member information and a login/signup identifier. It is not used as proof of device ownership. Android does not read the phone number from the device. Device-bound restore uses `refresh_token + device_token`.

## Status Definitions

- `Connected`: session restore or login succeeded.
- `Disconnected`: no valid app session is available.
- `Login required`: stored token is missing or expired.
- `Approval pending`: signup succeeded, but admin approval has not been granted.
- `Session expired`: refresh token is invalid or expired.

## Logout

Step 24 added Android local logout. Step 25 extends it with server logout:

```text
POST /api/auth/logout/
```

Android sends the stored `refresh_token + device_token`. The server blacklists the refresh token and clears the matching `AccountProfile.device_token`. Android then clears local `access_token`, `refresh_token`, `device_token`, user id, username, phone number, approval status, connected state, and welcome message from DataStore. The last successful username/password stays saved so the next login form can be prefilled.

If server logout fails because of network or server state, Android still performs local logout. The user must log in again from that phone.
