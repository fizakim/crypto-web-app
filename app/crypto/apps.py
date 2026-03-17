from django.apps import AppConfig


class CryptoConfig(AppConfig):
    name = 'crypto'

    def ready(self):
        # load configs when app starts
        from .services import load_configs
        print("loading crypto configs...")
        load_configs()
