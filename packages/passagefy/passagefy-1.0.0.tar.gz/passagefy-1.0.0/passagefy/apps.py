from django.apps import AppConfig


class PassagefyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "passagefy"

    def ready(self):
        import passagefy.single
