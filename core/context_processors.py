def system_context(request):
    from django.conf import settings
    return {'SYSTEM_NAME': settings.SYSTEM_NAME}
