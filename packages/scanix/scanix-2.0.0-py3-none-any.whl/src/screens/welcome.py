"""
Écran d'accueil - Scanix
src/screens/welcome.py
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Center, Container


class WelcomeScreen(Screen):
    """Menu principal Scanix"""
    
    CSS = """
    Screen {
        background: $surface;
        align: center middle;
    }
    
    .welcome-container {
        width: 60;
        height: auto;
        padding: 2;
        background: $panel;
        border: solid $primary;
    }
    
    .logo {
        text-align: center;
        height: auto;
        text-style: bold;
        color: $accent;
        margin: 0 0 1 0;
    }
    
    .subtitle {
        text-align: center;
        height: auto;
        color: $text-muted;
        margin: 0 0 2 0;
    }
    
    .menu-section {
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }
    
    .section-title {
        text-align: center;
        height: auto;
        text-style: bold;
        color: $primary;
        margin: 0 0 1 0;
    }
    
    Button {
        width: 100%;
        margin: 0 0 1 0;
    }
    
    .footer-info {
        text-align: center;
        height: auto;
        color: $text-muted;
        margin: 1 0 0 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Interface simple"""
        yield Header(show_clock=False)
        
        with Center():
            with Vertical(classes="welcome-container"):
                # Logo et titre
                yield Static("⚡ Scanix", classes="logo")
                yield Static("Static Code Security Scanner", classes="subtitle")
                
                # Menu principal
                with Container(classes="menu-section"):
                    yield Static("📊 Analyse", classes="section-title")
                    yield Button("📄 Scanner un fichier", id="single-file", variant="primary")
                    yield Button("📁 Scanner un dossier", id="folder", variant="primary")
                
                # Autres options
                with Container(classes="menu-section"):
                    yield Static("ℹ️ Informations", classes="section-title")
                    yield Button("📖 À propos", id="about", variant="default")
                
                # Quitter
                yield Button("🚪 Quitter", id="quit", variant="error")
                
                # Footer
                yield Static("v2.0 - OWASP Top 10 2021", classes="footer-info")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Focus initial"""
        self.query_one("#single-file", Button).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestion des boutons"""
        btn_id = event.button.id
        
        if btn_id == "single-file":
            try:
                from src.screens.file_select import FileSelectScreen
                self.app.push_screen(FileSelectScreen(mode="single"))
            except ImportError as e:
                self.app.notify(f"❌ Erreur: {str(e)[:40]}", severity="error")
        
        elif btn_id == "folder":
            try:
                from src.screens.file_select import FileSelectScreen
                self.app.push_screen(FileSelectScreen(mode="folder"))
            except ImportError as e:
                self.app.notify(f"❌ Erreur: {str(e)[:40]}", severity="error")
        
        elif btn_id == "about":
            self.show_about()
        
        elif btn_id == "quit":
            self.app.exit()
    
    def show_about(self) -> None:
        """Affiche les informations"""
        about_text = """
⚡ Scanix v2.0

Static Code Security Scanner
Détecte 25+ types de vulnérabilités

Modes:
🚀 Rapide  - 6 catégories critiques
🔬 Complet - 25+ catégories

Exports: JSON, HTML, TXT, CSV

Basé sur OWASP Top 10 2021
Développé par Riyad ODJOUADE
        """
        self.app.notify(about_text.strip(), timeout=8)