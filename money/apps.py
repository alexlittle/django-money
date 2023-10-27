from django.apps import AppConfig

class MoneyAppConfig(AppConfig):
    name = 'money'

    def ready(self):
        import money.signals