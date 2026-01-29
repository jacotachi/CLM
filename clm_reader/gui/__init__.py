"""Module interface graphique pour CLM Reader."""

# Pas d'import au niveau du module pour eviter les erreurs circulaires
__all__ = ["MainWindow", "main"]

def get_main_window():
    """Retourne la classe MainWindow."""
    from .main_window import MainWindow
    return MainWindow

def main():
    """Lance l'application."""
    from .main_window import main as _main
    _main()
