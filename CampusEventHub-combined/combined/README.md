# Member 1 — Authentication & User Profile (Irene)

## Completed
- user registration
- user login/logout
- user forgot password
- profile viewing/update
- admin login/logout (one admin acc)

## Implemented Remarks
- Registration must validate that the same email cannot be used twice. 
- UM email domain only for registration.
- Password should have a minimum length for security.  Minimum password length: 8 characters
- Login must verify the correct email and password.
- Passwords created through registration/reset are hashed with Django hashers.
- Forgot password can be kept simple, for example reset by entering email and setting a new password.  email temporary password, user need change the password after login
- Profile page should only show the currently logged-in user’s own information.  Profile data is loaded from `request.session['user_id']`, so only the logged-in user's account information is shown.
- When User A logs in and registers for an event, then logs out, and User B logs in, User B must not see User A’s registered events.  My Events queries `Registration.objects.filter(user=current_user)`, so User B cannot see User A's event registrations.
- This means every registration and profile must be linked to the currently logged-in account only.  request.session['user_id']
- Admin login can use one fixed admin account to reduce complexity.  Admin pages are protected by admin session

## Files changed
- core/forms.py
- core/views.py 
- core/urls.py 
- core/templates/base.html 
- core/templates/base_admin.html 
- core/templates/auth/login.html 
- core/templates/auth/register.html 
- core/templates/auth/forgot_password.html 
- core/templates/auth/admin_login.html 
- core/templates/user/profile.html 
- core/templates/events/my_events.html 
- core/static/css/auth.css 
- core/static/js/auth.js 
- core/static/images/umlogin.png
- campuseventhub/settings.py 
- core/models.py 
- core/migrations/
- .gitignore