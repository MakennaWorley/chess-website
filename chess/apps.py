from django.apps import AppConfig

class Chess(AppConfig):
    name = 'chess'

    def ready(self):
        import chess.signals