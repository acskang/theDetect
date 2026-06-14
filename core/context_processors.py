from django.conf import settings


def chat_widget(request):
    return {
        'chat_widget_enabled': getattr(settings, 'CHAT_WIDGET_ENABLED', True),
    }
