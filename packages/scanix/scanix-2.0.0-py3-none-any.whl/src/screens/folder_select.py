"""
Sélection de fichiers dans un dossier - Interface Moderne
src/screens/folder_select.py
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer, DataTable, ProgressBar
from textual.containers import Vertical, Horizontal, Container, ScrollableContainer
from pathlib import Path
import asyncio


class FolderSelectScreen(Screen):
    """Sélection de fichiers avec filtres et prévisualisation"""
    
    BINDINGS = [
        ("escape", "back", "Retour"),
        ("ctrl+a", "select_all", "Tout sélectionner"),
        ("ctrl+d", "deselect_all", "Tout désélectionner")
    ]
    
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
    
    .folder-path {
        text-align: center;
        color: $text-muted;
        height: auto;
        margin: 0 0 1 0;
    }
    
    .filters-section {
        height: auto;
        background: $panel;
        padding: 1;
        margin: 0 0 1 0;
        border: solid $primary-lighten-1;
    }
    
    .filter-label {
        text-style: bold;
        color: $accent;
        height: auto;
        margin: 0 0 1 0;
    }
    
    .filter-grid {
        layout: grid;
        grid-size: 6;
        grid-gutter: 1;
        height: auto;
    }
    
    .filter-grid Button {
        width: 100%;
        min-height: 3;
    }
    
    .stats-bar {
        height: auto;
        background: $panel;
        padding: 1;
        margin: 0 0 1 0;
        border: solid $primary-lighten-1;
    }
    
    .stats-grid {
        layout: grid;
        grid-size: 4;
        grid-gutter: 2;
        height: auto;
    }
    
    .stat-item {
        text-align: center;
        height: auto;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }
    
    .stat-value {
        text-style: bold;
        color: $accent;
    }
    
    .table-section {
        height: 1fr;
        margin: 0 0 1 0;
        border: solid $primary;
    }
    
    DataTable {
        height: 100%;
    }
    
    .actions-section {
        height: auto;
    }
    
    .action-grid {
        layout: grid;
        grid-size: 5;
        grid-gutter: 1;
        height: auto;
    }
    
    .action-grid Button {
        width: 100%;
    }
    
    ProgressBar {
        margin: 0 0 1 0;
    }
    """
    
    def __init__(self, folder_path=None):
        super().__init__()
        self.folder_path = Path(folder_path) if folder_path else Path.home()
        self.all_files = []
        self.displayed_files = []
        self.selected_rows = set()
        
        # Filtres avec compteurs
        self.filters = {
            'py': {'active': True, 'count': 0, 'label': 'Python'},
            'js': {'active': True, 'count': 0, 'label': 'JavaScript'},
            'php': {'active': True, 'count': 0, 'label': 'PHP'},
            'html': {'active': True, 'count': 0, 'label': 'HTML'},
            'java': {'active': True, 'count': 0, 'label': 'Java'},
            'other': {'active': True, 'count': 0, 'label': 'Autre'}
        }
        
        self.ext_map = {
            'py': ['.py'],
            'js': ['.js', '.ts'],
            'php': ['.php'],
            'html': ['.html', '.htm'],
            'java': ['.java'],
            'other': ['.c', '.cpp', '.h', '.go', '.rb', '.sql', '.json', '.xml', '.yml', '.yaml']
        }
    
    def compose(self) -> ComposeResult:
        """Interface moderne avec table"""
        yield Header(show_clock=True)
        
        with Vertical(classes="main-container"):
            # En-tête
            with Container(classes="header-section"):
                yield Static("📂 Sélection des Fichiers", classes="title")
                yield Static(f"📍 {self.folder_path}", classes="folder-path")
            
            # Progression du scan
            yield ProgressBar(total=100, show_percentage=False, id="scan-progress")
            yield Static("⏳ Scan en cours...", id="scan-status")
            
            # Filtres
            with Container(classes="filters-section"):
                yield Static("🔍 Filtres par Type:", classes="filter-label")
                with Container(classes="filter-grid"):
                    for key, data in self.filters.items():
                        yield Button(
                            f"{data['label']} (0)",
                            id=f"filter-{key}",
                            variant="primary"
                        )
            
            # Statistiques
            with Container(classes="stats-bar"):
                with Container(classes="stats-grid"):
                    yield Container(
                        Static("Total", classes="stat-label"),
                        Static("0", id="stat-total", classes="stat-value"),
                        classes="stat-item"
                    )
                    yield Container(
                        Static("Affichés", classes="stat-label"),
                        Static("0", id="stat-displayed", classes="stat-value"),
                        classes="stat-item"
                    )
                    yield Container(
                        Static("Sélectionnés", classes="stat-label"),
                        Static("0", id="stat-selected", classes="stat-value"),
                        classes="stat-item"
                    )
                    yield Container(
                        Static("Taille", classes="stat-label"),
                        Static("0 KB", id="stat-size", classes="stat-value"),
                        classes="stat-item"
                    )
            
            # Table de fichiers
            with Container(classes="table-section"):
                yield DataTable(
                    id="files-table",
                    zebra_stripes=True,
                    cursor_type="row",
                    show_cursor=True
                )
            
            # Actions
            with Container(classes="actions-section"):
                with Container(classes="action-grid"):
                    yield Button("← Retour", id="back", variant="default")
                    yield Button("✅ Tout", id="select-all", variant="default")
                    yield Button("❌ Rien", id="deselect-all", variant="default")
                    yield Button("🔄 Actualiser", id="refresh", variant="default")
                    yield Button("🚀 Analyser", id="analyze", variant="success")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Au montage, lancer le scan"""
        asyncio.create_task(self.scan_folder())
    
    async def scan_folder(self) -> None:
        """Scanner le dossier de manière asynchrone"""
        try:
            progress = self.query_one("#scan-progress", ProgressBar)
            status = self.query_one("#scan-status", Static)
            
            # Initialiser
            self.all_files = []
            progress.update(total=100, progress=0)
            status.update("🔍 Recherche des fichiers...")
            
            await asyncio.sleep(0.1)
            
            # Scanner
            all_extensions = []
            for exts in self.ext_map.values():
                all_extensions.extend(exts)
            
            found_files = []
            for ext in all_extensions:
                try:
                    files = list(self.folder_path.rglob(f"*{ext}"))
                    for f in files:
                        if f.is_file() and not self.should_ignore(f):
                            found_files.append(f)
                            
                            if len(found_files) >= 1000:
                                break
                    
                    # Mise à jour progress
                    prog = int((all_extensions.index(ext) + 1) / len(all_extensions) * 100)
                    progress.update(progress=prog)
                    await asyncio.sleep(0.01)
                    
                    if len(found_files) >= 1000:
                        break
                        
                except Exception:
                    continue
            
            self.all_files = sorted(found_files)
            
            # Compter par catégorie
            for key, data in self.filters.items():
                exts = self.ext_map[key]
                count = sum(1 for f in self.all_files if f.suffix.lower() in exts)
                self.filters[key]['count'] = count
            
            # Mettre à jour l'interface
            progress.update(progress=100)
            status.update(f"✅ {len(self.all_files)} fichiers trouvés")
            
            if len(found_files) >= 1000:
                self.app.notify("⚠️ Limite de 1000 fichiers atteinte", severity="warning")
            
            self.update_filter_buttons()
            self.apply_filters()
            
            # Cacher la progress bar après 1 seconde
            await asyncio.sleep(1)
            progress.display = False
            status.display = False
            
        except Exception as e:
            self.app.notify(f"❌ Erreur scan: {str(e)[:40]}", severity="error")
    
    def should_ignore(self, filepath: Path) -> bool:
        """Fichiers/dossiers à ignorer"""
        ignore = ['.git', '__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build']
        return any(p in str(filepath) for p in ignore)
    
    def update_filter_buttons(self) -> None:
        """Mettre à jour les boutons de filtres"""
        for key, data in self.filters.items():
            try:
                btn = self.query_one(f"#filter-{key}", Button)
                btn.label = f"{data['label']} ({data['count']})"
                btn.variant = "primary" if data['active'] else "default"
            except:
                pass
    
    def apply_filters(self) -> None:
        """Appliquer les filtres et afficher la table"""
        # Filtrer les fichiers
        active_extensions = []
        for key, data in self.filters.items():
            if data['active']:
                active_extensions.extend(self.ext_map[key])
        
        self.displayed_files = [
            f for f in self.all_files 
            if f.suffix.lower() in active_extensions
        ]
        
        # Mettre à jour la table
        self.update_table()
        self.update_stats()
    
    def update_table(self) -> None:
        """Mettre à jour la table des fichiers"""
        table = self.query_one("#files-table", DataTable)
        table.clear(columns=True)
        
        # Colonnes
        table.add_columns("☑️", "N°", "Nom", "Type", "Taille", "Chemin")
        
        if not self.displayed_files:
            table.add_row("", "", "Aucun fichier", "", "", "")
            return
        
        # Lignes
        for i, filepath in enumerate(self.displayed_files):
            check = "✓" if i in self.selected_rows else " "
            name = filepath.name
            ext = filepath.suffix.upper() or "N/A"
            
            try:
                size_bytes = filepath.stat().st_size
                size = self.format_size(size_bytes)
            except:
                size = "N/A"
            
            try:
                rel_path = str(filepath.relative_to(self.folder_path))
            except:
                rel_path = str(filepath)
            
            table.add_row(check, str(i + 1), name[:40], ext, size, rel_path[:50])
    
    def format_size(self, size_bytes: int) -> str:
        """Formater la taille"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def update_stats(self) -> None:
        """Mettre à jour les statistiques"""
        self.query_one("#stat-total", Static).update(str(len(self.all_files)))
        self.query_one("#stat-displayed", Static).update(str(len(self.displayed_files)))
        self.query_one("#stat-selected", Static).update(str(len(self.selected_rows)))
        
        # Taille totale des fichiers sélectionnés
        total_size = 0
        for idx in self.selected_rows:
            if idx < len(self.displayed_files):
                try:
                    total_size += self.displayed_files[idx].stat().st_size
                except:
                    pass
        
        self.query_one("#stat-size", Static).update(self.format_size(total_size))
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Toggle sélection d'une ligne"""
        row_idx = event.cursor_row
        
        if row_idx in self.selected_rows:
            self.selected_rows.remove(row_idx)
        else:
            self.selected_rows.add(row_idx)
        
        self.update_table()
        self.update_stats()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestion des boutons"""
        btn_id = event.button.id
        
        # Filtres
        if btn_id and btn_id.startswith("filter-"):
            filter_key = btn_id.replace("filter-", "")
            if filter_key in self.filters:
                self.filters[filter_key]['active'] = not self.filters[filter_key]['active']
                self.update_filter_buttons()
                self.apply_filters()
        
        # Actions
        elif btn_id == "back":
            self.app.pop_screen()
        elif btn_id == "select-all":
            self.action_select_all()
        elif btn_id == "deselect-all":
            self.action_deselect_all()
        elif btn_id == "refresh":
            asyncio.create_task(self.scan_folder())
        elif btn_id == "analyze":
            self.analyze_files()
    
    def action_select_all(self) -> None:
        """Sélectionner tous les fichiers affichés"""
        self.selected_rows = set(range(len(self.displayed_files)))
        self.update_table()
        self.update_stats()
        self.app.notify(f"✅ {len(self.selected_rows)} fichiers sélectionnés", timeout=2)
    
    def action_deselect_all(self) -> None:
        """Désélectionner tous"""
        self.selected_rows.clear()
        self.update_table()
        self.update_stats()
        self.app.notify("❌ Sélection effacée", timeout=2)
    
    def analyze_files(self) -> None:
        """Lancer l'analyse"""
        # Fichiers à analyser
        if self.selected_rows:
            files_to_analyze = [
                self.displayed_files[i] 
                for i in sorted(self.selected_rows)
                if i < len(self.displayed_files)
            ]
        else:
            # Si rien sélectionné, prendre les 20 premiers
            files_to_analyze = self.displayed_files[:20]
        
        if not files_to_analyze:
            self.app.notify("❌ Aucun fichier à analyser", severity="warning")
            return
        
        # Avertissement si beaucoup de fichiers
        if len(files_to_analyze) > 100:
            self.app.notify(
                f"⚠️ {len(files_to_analyze)} fichiers - cela peut prendre du temps",
                severity="warning",
                timeout=3
            )
        
        # Sauvegarder et naviguer
        self.app.set_selected_files([str(f) for f in files_to_analyze])
        
        try:
            from src.screens.scan_mode import ScanModeScreen
            self.app.push_screen(ScanModeScreen())
        except ImportError as e:
            self.app.notify(f"❌ Erreur: {str(e)[:40]}", severity="error")
    
    def action_back(self) -> None:
        """Action retour"""
        self.app.pop_screen()