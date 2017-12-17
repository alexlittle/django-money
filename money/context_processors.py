from django.conf import settings # import the settings file

def base_currency(request):
    return {'BASE_CURRENCY': settings.BASE_CURRENCY}