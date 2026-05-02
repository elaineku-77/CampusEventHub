from django import forms
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from .models import Event, User

def normalize_phone_number(phone_number):
    if not phone_number:
        return ''

    phone_number = phone_number.strip()

    # Remove common formatting characters
    phone_number = phone_number.replace(' ', '')
    phone_number = phone_number.replace('-', '')
    phone_number = phone_number.replace('(', '')
    phone_number = phone_number.replace(')', '')

    # Allow + only at the beginning
    if phone_number.startswith('+'):
        digits_only = phone_number[1:]
    else:
        digits_only = phone_number

    if not digits_only.isdigit():
        raise forms.ValidationError(
            'Phone number must contain digits only, with optional country code.'
        )

    if len(digits_only) < 7 or len(digits_only) > 15:
        raise forms.ValidationError(
            'Phone number must be between 7 and 15 digits.'
        )

    return phone_number

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'category',
            'event_date',
            'event_time',
            'venue',
            'max_participants',
            'status',
            'event_image',
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'event_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'event_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        min_length=settings.MIN_PASSWORD_LENGTH,
        error_messages={
            'min_length': f'Password must be at least {settings.MIN_PASSWORD_LENGTH} characters.'
        },
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Create password',
            'autocomplete': 'new-password',
        }),
        help_text=f'Password must be at least {settings.MIN_PASSWORD_LENGTH} characters.',
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
        })
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '')
        return normalize_phone_number(phone_number)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'profile_picture', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control auth-input',
                'placeholder': 'Enter your full name',
                'autocomplete': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control auth-input',
                'placeholder': 'Enter your UM e-mail',
                'autocomplete': 'email',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control auth-input',
                'placeholder': 'Enter your phone number',
                'type': 'tel',
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control auth-input',
                'accept': 'image/*',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if '@' not in email:
            raise forms.ValidationError('Enter a valid email address.')

        domain = email.split('@')[-1]

        if domain not in settings.ALLOWED_UM_EMAIL_DOMAINS:
            raise forms.ValidationError('Use valid UM email address to sign up.')

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email address is already registered.')

        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].strip().lower()
        user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control auth-input',
        'placeholder': 'Enter your e-mail',
        'autocomplete': 'email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control auth-input js-password-field',
        'placeholder': 'Enter password',
        'autocomplete': 'current-password',
    }))

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class AdminLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control auth-input',
        'placeholder': 'Enter admin e-mail',
        'autocomplete': 'email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control auth-input js-password-field',
        'placeholder': 'Enter admin password',
        'autocomplete': 'current-password',
    }))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').strip().lower()
        password = cleaned_data.get('password', '')

        if email and password and (email != settings.CUSTOM_ADMIN_EMAIL or password != settings.CUSTOM_ADMIN_PASSWORD):
            raise forms.ValidationError('Invalid admin email or password.')

        cleaned_data['email'] = email
        return cleaned_data


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control auth-input',
        'placeholder': 'Enter your registered e-mail',
        'autocomplete': 'email',
    }))

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('No account exists for this email address.')

        return email

class ProfileUpdateForm(forms.ModelForm):
    remove_profile_picture = forms.BooleanField(
        required=False,
        label='Remove profile picture',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '')
        return normalize_phone_number(phone_number)

    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'profile_picture']

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control auth-input',
                'placeholder': 'Enter your full name',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control auth-input',
                'placeholder': 'Enter your phone number',
                'type': 'tel',
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control auth-input',
                'accept': 'image/*',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

class PasswordUpdateForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Enter current password',
            'autocomplete': 'off',
            'readonly': 'readonly',
            'onfocus': "this.removeAttribute('readonly');",
        })
    )

    new_password = forms.CharField(
        min_length=settings.MIN_PASSWORD_LENGTH,
        error_messages={
            'min_length': f'Password must be at least {settings.MIN_PASSWORD_LENGTH} characters.'
        },
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
        }),
        help_text=f'Password must be at least {settings.MIN_PASSWORD_LENGTH} characters.',
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control auth-input',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
        })
    )

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')

        if self.current_user and not password_matches(current_password, self.current_user.password):
            raise forms.ValidationError('Current password is incorrect.')

        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'New passwords do not match.')

        return cleaned_data

    def save(self):
        self.current_user.password = make_password(self.cleaned_data['new_password'])
        self.current_user.save(update_fields=['password'])
        return self.current_user

def password_matches(raw_password, stored_password):
    """Validate hashed passwords."""
    if check_password(raw_password, stored_password):
        return True
    return raw_password == stored_password
