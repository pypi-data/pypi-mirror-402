"""
⚡ Scanix - Application principale
Développé par Riyad ODJOUADE
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer


class SecureCodeApp(App):
    """Application Scanix - Scanner de vulnérabilités statique"""
    
    TITLE = "⚡ Scanix v2.0"
    SUB_TITLE = "Static Code Security Scanner | By Riyad ODJOUADE"
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quitter"),
        ("escape", "back", "Retour"),
    ]
    
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.scan_mode = "quick"
        self.scan_timeout = 2.0
        self.scan_categories = "all"
        self.scan_results = []
    
    def compose(self) -> ComposeResult:
        """Interface de base"""
        yield Header(show_clock=True)
        yield Footer()
    
    def on_mount(self) -> None:
        """Démarre sur l'écran d'accueil"""
        try:
            from src.screens.welcome import WelcomeScreen
            self.push_screen(WelcomeScreen())
        except ImportError as e:
            self.notify(f"❌ Erreur: {str(e)[:40]}", severity="error")
            self.exit()
    
    def set_selected_files(self, files: list) -> None:
        """Définit les fichiers sélectionnés"""
        self.selected_files = files
    
    def set_scan_mode(self, mode: str) -> None:
        """Définit le mode de scan"""
        self.scan_mode = mode
    
    def set_scan_results(self, results: list) -> None:
        """Définit les résultats du scan"""
        self.scan_results = results
    
    def action_back(self) -> None:
        """Action retour"""
        if len(self.screen_stack) > 1:
            self.pop_screen()
        else:
            self.notify("Déjà à l'accueil", timeout=2)
    
    def action_quit(self) -> None:
        """Action quitter"""
        self.exit()


if __name__ == "__main__":
    print("⚡ Scanix v2.0")
    print("Développé par Riyad ODJOUADE")
    print("\nDémarrage...")
    
    app = SecureCodeApp()
    app.run()