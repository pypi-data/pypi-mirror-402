"""
Navigateur de fichiers moderne - Scanix
src/screens/file_select.py
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, DirectoryTree, Header, Footer, Input
from textual.containers import Vertical, Horizontal, Container
from pathlib import Path


class FileSelectScreen(Screen):
    """Navigateur de fichiers moderne avec arborescence"""
    
    BINDINGS = [("escape", "back", "Retour")]
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .main-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    .header-section {
        height: auto;
        background: $primary;
        padding: 1;
        margin: 0 0 1 0;
        border: solid $accent;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        color: $text;
        height: auto;
    }
    
    .subtitle {
        text-align: center;
        color: $text-muted;
        height: auto;
        margin: 0 0 1 0;
    }
    
    .quick-access {
        height: auto;
        margin: 0 0 1 0;
    }
    
    .quick-buttons {
        layout: grid;
        grid-size: 5;
        grid-gutter: 1;
        height: auto;
    }
    
    .quick-buttons Button {
        width: 100%;
    }
    
    .browser-section {
        height: 1fr;
        border: solid $primary;
        margin: 0 0 1 0;
    }
    
    DirectoryTree {
        height: 100%;
        padding: 1;
    }
    
    .path-display {
        height: auto;
        background: $panel;
        padding: 1;
        margin: 0 0 1 0;
        border: solid $primary-lighten-1;
    }
    
    .current-path {
        color: $accent;
        text-style: bold;
        height: auto;
    }
    
    .manual-input {
        height: auto;
        margin: 0 0 1 0;
    }
    
    Input {
        width: 100%;
    }
    
    .actions {
        height: auto;
    }
    
    .action-buttons {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
        height: auto;
    }
    
    .action-buttons Button {
        width: 100%;
    }
    """
    
    def __init__(self, mode="folder"):
        super().__init__()
        self.mode = mode
        self.current_selection = None
        self.start_path = Path.home()
    
    def compose(self) -> ComposeResult:
        """Interface moderne avec navigateur"""
        yield Header(show_clock=True)
        
        mode_icon = "📄" if self.mode == "single" else "📁"
        mode_text = "fichier" if self.mode == "single" else "dossier"
        
        with Vertical(classes="main-container"):
            # En-tête
            with Container(classes="header-section"):
                yield Static(f"{mode_icon} Sélection de {mode_text}", classes="title")
                yield Static("Naviguez ou entrez un chemin manuellement", classes="subtitle")
            
            # Accès rapide
            with Container(classes="quick-access"):
                yield Static("🚀 Accès Rapide:")
                with Container(classes="quick-buttons"):
                    yield Button("🏠 Home", id="quick-home", variant="primary")
                    yield Button("🖥️ Bureau", id="quick-desktop", variant="primary")
                    yield Button("📄 Documents", id="quick-docs", variant="primary")
                    yield Button("⬇️ Téléchargements", id="quick-downloads", variant="primary")
                    yield Button("💻 Racine", id="quick-root", variant="primary")
            
            # Navigateur d'arborescence
            with Container(classes="browser-section"):
                yield DirectoryTree(str(self.start_path), id="file-tree")
            
            # Affichage du chemin actuel
            with Container(classes="path-display"):
                yield Static("📍 Sélection actuelle:", id="selection-label")
                yield Static("Aucune sélection", id="current-path", classes="current-path")
            
            # Entrée manuelle
            with Container(classes="manual-input"):
                yield Static("✏️ Ou entrez un chemin manuellement:")
                yield Input(
                    placeholder=f"Ex: /home/user/projet/{mode_text}.py" if self.mode == "single" else "/home/user/projet",
                    id="manual-path"
                )
            
            # Actions
            with Container(classes="actions"):
                with Container(classes="action-buttons"):
                    yield Button("← Retour", id="back", variant="default")
                    yield Button("🔄 Actualiser", id="refresh", variant="default")
                    yield Button("✅ Continuer", id="continue", variant="success")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Au montage"""
        self.query_one("#file-tree", DirectoryTree).focus()
    
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Quand un fichier est sélectionné"""
        if self.mode == "single":
            self.current_selection = event.path
            self.query_one("#current-path", Static).update(f"📄 {event.path}")
            self.query_one("#manual-path", Input).value = str(event.path)
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Quand un dossier est sélectionné"""
        if self.mode == "folder":
            self.current_selection = event.path
            self.query_one("#current-path", Static).update(f"📁 {event.path}")
            self.query_one("#manual-path", Input).value = str(event.path)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestion des boutons"""
        btn_id = event.button.id
        
        # Accès rapide
        if btn_id == "quick-home":
            self.navigate_to(Path.home())
        elif btn_id == "quick-desktop":
            desktop = Path.home() / "Bureau"
            if not desktop.exists():
                desktop = Path.home() / "Desktop"
            if desktop.exists():
                self.navigate_to(desktop)
            else:
                self.app.notify("❌ Bureau introuvable", severity="warning")
        elif btn_id == "quick-docs":
            docs = Path.home() / "Documents"
            if docs.exists():
                self.navigate_to(docs)
            else:
                self.app.notify("❌ Documents introuvable", severity="warning")
        elif btn_id == "quick-downloads":
            downloads = Path.home() / "Téléchargements"
            if not downloads.exists():
                downloads = Path.home() / "Downloads"
            if downloads.exists():
                self.navigate_to(downloads)
            else:
                self.app.notify("❌ Téléchargements introuvable", severity="warning")
        elif btn_id == "quick-root":
            self.navigate_to(Path("/"))
        
        # Actions
        elif btn_id == "back":
            self.app.pop_screen()
        elif btn_id == "refresh":
            self.refresh_tree()
        elif btn_id == "continue":
            self.validate_selection()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Quand Enter est pressé dans l'input"""
        self.validate_selection()
    
    def navigate_to(self, path: Path) -> None:
        """Naviguer vers un dossier"""
        try:
            tree = self.query_one("#file-tree", DirectoryTree)
            tree.path = str(path)
            tree.reload()
            self.app.notify(f"📂 {path.name}", timeout=1)
        except Exception as e:
            self.app.notify(f"❌ Erreur: {str(e)[:30]}", severity="error")
    
    def refresh_tree(self) -> None:
        """Actualiser l'arborescence"""
        try:
            tree = self.query_one("#file-tree", DirectoryTree)
            tree.reload()
            self.app.notify("🔄 Actualisé", timeout=1)
        except Exception as e:
            self.app.notify(f"❌ Erreur: {str(e)[:30]}", severity="error")
    
    def validate_selection(self) -> None:
        """Valider la sélection"""
        # Priorité à l'input manuel
        manual_input = self.query_one("#manual-path", Input).value.strip()
        
        if manual_input:
            path = Path(manual_input).expanduser()
        elif self.current_selection:
            path = Path(self.current_selection)
        else:
            self.app.notify("⚠️ Aucune sélection", severity="warning")
            return
        
        # Vérifications
        if not path.exists():
            self.app.notify("❌ Chemin introuvable", severity="error")
            return
        
        if self.mode == "single":
            # Mode fichier
            if not path.is_file():
                self.app.notify("❌ Sélectionnez un fichier", severity="warning")
                return
            
            # Fichier valide
            self.app.set_selected_files([str(path)])
            self.app.notify(f"✅ Fichier: {path.name}", timeout=2)
            
            # Navigation vers scan mode
            try:
                from src.screens.scan_mode import ScanModeScreen
                self.app.push_screen(ScanModeScreen())
            except ImportError as e:
                self.app.notify(f"❌ Erreur: {str(e)[:40]}", severity="error")
        
        else:
            # Mode dossier
            if not path.is_dir():
                self.app.notify("❌ Sélectionnez un dossier", severity="warning")
                return
            
            # Dossier valide
            self.app.notify(f"✅ Dossier: {path.name}", timeout=2)
            
            # Navigation vers folder select
            try:
                from src.screens.folder_select import FolderSelectScreen
                self.app.push_screen(FolderSelectScreen(folder_path=str(path)))
            except ImportError as e:
                self.app.notify(f"❌ Erreur: {str(e)[:40]}", severity="error")
    
    def action_back(self) -> None:
        """Action retour"""
        self.app.pop_screen()