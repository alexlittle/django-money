from django.conf import settings


def base_currency(request):
    return {'BASE_CURRENCY': settings.BASE_CURRENCY}
