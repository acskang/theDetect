from django.contrib import admin

from .models import AccountProfile


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone_number',
        'approval_status',
        'approved_at',
        'approved_by',
        'has_device_token',
        'last_login_device_at',
    )
    list_filter = ('approval_status', 'created_at', 'last_login_device_at')
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'device_token_created_at', 'last_login_device_at')
    actions = ('approve_profiles',)

    @admin.display(boolean=True, description='Device token')
    def has_device_token(self, obj):
        return bool(obj.device_token)

    @admin.action(description='Approve selected profiles')
    def approve_profiles(self, request, queryset):
        for profile in queryset:
            profile.approval_status = AccountProfile.ApprovalStatus.APPROVED
            profile.approved_by = request.user
            profile.save(update_fields=['approval_status', 'approved_at', 'approved_by', 'updated_at'])
