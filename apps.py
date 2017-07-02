from django.apps import AppConfig


class EvcsConfig(AppConfig):
    name = 'evcs'

    def ready(self):
        print()
        # TODO: load ports dynamically from config file and start listener
