"""
Mode de scan - Interface sobre et centrée
src/screens/scan_mode.py
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Vertical, Container, Center


class ScanModeScreen(Screen):
    """Choix du mode de scan avec explications"""
    
    BINDINGS = [("escape", "back", "Retour")]
    
    CSS = """
    Screen {
        background: $surface;
        align: center middle;
    }
    
    .main-container {
        width: 80%;
        max-width: 100;
        height: auto;
        padding: 2;
        background: $panel;
        border: solid $primary;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        height: auto;
        content-align: center middle;
        color: $accent;
        margin: 0 0 1 0;
    }
    
    .file-count {
        text-align: center;
        height: auto;
        margin: 0 0 2 0;
        color: $success;
        text-style: bold;
    }
    
    .modes-container {
        width: 100%;
        height: auto;
        layout: grid;
        grid-size: 2;
        grid-gutter: 2;
        margin: 0 0 2 0;
    }
    
    .mode-card {
        width: 100%;
        height: auto;
        padding: 2;
        background: $surface;
        border: solid $primary-lighten-1;
    }
    
    .mode-card:hover {
        background: $primary 10%;
        border: solid $accent;
    }
    
    .mode-title {
        text-style: bold;
        color: $accent;
        height: auto;
        text-align: center;
        margin: 0 0 1 0;
    }
    
    .mode-desc {
        color: $text-muted;
        height: auto;
        text-align: center;
        margin: 0 0 1 0;
    }
    
    .mode-features {
        color: $text;
        height: auto;
        margin: 0 0 1 0;
    }
    
    .mode-card Button {
        width: 100%;
        margin: 1 0 0 0;
    }
    
    .actions {
        width: 100%;
        height: auto;
    }
    
    .actions Button {
        width: 100%;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        
        with Center():
            with Vertical(classes="main-container"):
                yield Static("🔍 Choisir le Mode de Scan", classes="title")
                
                files_count = len(getattr(self.app, "selected_files", []))
                yield Static(
                    f"✅ {files_count} fichier(s) sélectionné(s)", 
                    classes="file-count"
                )
                
                # Grille de modes
                with Container(classes="modes-container"):
                    # Mode Rapide
                    with Container(classes="mode-card"):
                        yield Static("🚀 Mode Rapide", classes="mode-title")
                        yield Static(
                            "Analyse rapide des vulnérabilités critiques",
                            classes="mode-desc"
                        )
                        yield Static(
                            "• Injection SQL, XSS, CSRF\n"
                            "• Secrets exposés (API keys)\n"
                            "• Path Traversal\n"
                            "• Timeout: 2s/fichier",
                            classes="mode-features"
                        )
                        yield Button("🚀 Lancer", id="quick", variant="success")
                    
                    # Mode Complet
                    with Container(classes="mode-card"):
                        yield Static("🔬 Mode Complet", classes="mode-title")
                        yield Static(
                            "Analyse approfondie complète",
                            classes="mode-desc"
                        )
                        yield Static(
                            "• Toutes les vulnérabilités\n"
                            "• OWASP Top 10 complet\n"
                            "• Analyse des dépendances\n"
                            "• Timeout: 5s/fichier",
                            classes="mode-features"
                        )
                        yield Button("🔬 Lancer", id="full", variant="primary")
                
                # Actions
                with Vertical(classes="actions"):
                    yield Button("← Retour à la sélection", id="back", variant="default")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Focus sur le bouton rapide au démarrage"""
        self.query_one("#quick", Button).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestion des clics"""
        btn_id = event.button.id
        
        if btn_id == "back":
            self.app.pop_screen()
        
        elif btn_id == "quick":
            # Mode rapide : timeout court, vulnérabilités critiques
            self.app.scan_mode = "quick"
            self.app.scan_timeout = 2.0
            self.app.scan_categories = [
                "secret_en_dur",
                "injection_sql",
                "injection_commande",
                "xss",
                "csrf",
                "injection_fichier"
            ]
            self.app.notify("🚀 Mode Rapide activé", timeout=2, severity="information")
            self.launch_scan()
        
        elif btn_id == "full":
            # Mode complet : timeout long, toutes les vulnérabilités
            self.app.scan_mode = "full"
            self.app.scan_timeout = 5.0
            self.app.scan_categories = "all"
            self.app.notify("🔬 Mode Complet activé", timeout=2, severity="information")
            self.launch_scan()
    
    def launch_scan(self) -> None:
        """Lancer le scan"""
        try:
            from src.screens.scanning import ScanningScreen
            self.app.push_screen(ScanningScreen())
        except ImportError as e:
            self.app.notify(f"❌ Erreur: {str(e)[:40]}", severity="error")
    
    def action_back(self) -> None:
        """Action de retour"""
        self.app.pop_screen()