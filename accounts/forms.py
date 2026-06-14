from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import AccountProfile, normalize_phone_number


class SignUpForm(UserCreationForm):
    phone_number = forms.CharField(
        label='Phone number',
        max_length=32,
        required=True,
        help_text='Required. You can use this phone number to log in from the mobile app.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('The two password fields did not match.')
        return password2

    def _post_clean(self):
        forms.ModelForm._post_clean(self)

    def clean_phone_number(self):
        phone_number = normalize_phone_number(self.cleaned_data['phone_number'])
        if not phone_number:
            raise forms.ValidationError('Phone number is required.')
        if not phone_number.isdigit() or len(phone_number) < 9:
            raise forms.ValidationError('Enter a valid phone number using digits, hyphens, or spaces.')
        if AccountProfile.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('A user with this phone number already exists.')
        return phone_number

    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            AccountProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
            )
        return user
