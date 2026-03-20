from django.apps import AppConfig


class CryptoConfig(AppConfig):
    name = 'crypto'

    def ready(self):
        import sys
        import crypto.signals
        
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            return

        from .services import load_configs
        try:
            load_configs()
        except Exception:
            pass
