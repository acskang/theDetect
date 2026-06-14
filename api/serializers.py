from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import AccountProfile, normalize_phone_number


def auth_user_payload(user, profile):
    return {
        'id': user.id,
        'username': user.get_username(),
        'phone_number': profile.phone_number,
        'approval_status': profile.approval_status,
    }


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_username(self, value):
        username = value.strip()
        if not username:
            raise serializers.ValidationError('username is required.')
        if get_user_model().objects.filter(username=username).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return username

    def validate_phone_number(self, value):
        phone_number = normalize_phone_number(value)
        if not phone_number:
            raise serializers.ValidationError('phone_number is required.')
        if not phone_number.isdigit() or len(phone_number) < 9:
            raise serializers.ValidationError('Enter a valid phone number.')
        if AccountProfile.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError('A user with this phone number already exists.')
        return phone_number

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        User = get_user_model()
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            is_active=True,
        )
        AccountProfile.objects.create(
            user=user,
            phone_number=validated_data['phone_number'],
            approval_status=AccountProfile.ApprovalStatus.PENDING,
        )
        return user


class PhoneOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login_value = attrs.get(self.username_field, '')
        normalized_phone = normalize_phone_number(login_value)
        if normalized_phone:
            profile = AccountProfile.objects.select_related('user').filter(phone_number=normalized_phone).first()
            if profile:
                attrs[self.username_field] = getattr(profile.user, get_user_model().USERNAME_FIELD)
        data = super().validate(attrs)
        profile = getattr(self.user, 'mdetect_profile', None)
        if profile is None:
            raise serializers.ValidationError('User profile is not registered.')
        if profile.approval_status != AccountProfile.ApprovalStatus.APPROVED:
            raise serializers.ValidationError('관리자 승인 후 로그인할 수 있습니다.')
        data['user'] = auth_user_payload(self.user, profile)
        data['device_token'] = profile.ensure_device_token()
        data['message'] = f'{self.user.get_username()}님, 반갑습니다'
        return data
