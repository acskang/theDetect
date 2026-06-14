from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import AccountProfile, normalize_phone_number


class PhoneOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login_value = attrs.get(self.username_field, '')
        normalized_phone = normalize_phone_number(login_value)
        if normalized_phone:
            profile = AccountProfile.objects.select_related('user').filter(phone_number=normalized_phone).first()
            if profile:
                attrs[self.username_field] = getattr(profile.user, get_user_model().USERNAME_FIELD)
        return super().validate(attrs)
