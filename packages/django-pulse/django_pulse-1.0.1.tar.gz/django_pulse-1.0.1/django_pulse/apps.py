from django.apps import AppConfig

class DjangoPulseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_pulse'

    def ready(self):
        import django_pulse.signals