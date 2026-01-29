"""
Écran de scan - Interface Moderne avec Feedback en Temps Réel
src/screens/scanning.py
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, ProgressBar, Header, Footer, DataTable
from textual.containers import Vertical, Horizontal, Container
import asyncio
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
import signal


def scan_single_file(file_path: str, scan_mode: str = "quick", categories=None):
    """Fonction pour scanner UN fichier - Sera exécutée dans un processus séparé"""
    try:
        import sys
        from pathlib import Path
        
        # Ajouter le chemin du projet
        project_root = Path(__file__).parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from src.core.scanner import ScannerStatique
        
        # Timeout interne adapté au mode
        timeout_seconds = 2 if scan_mode == "quick" else 5
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Scan timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            scanner = ScannerStatique()
            result = scanner.scanner_fichier(file_path)
            signal.alarm(0)
            
            # Filtrer les résultats selon le mode
            if scan_mode == "quick" and categories and categories != "all":
                filtered_result = []
                for vuln in result:
                    vuln_category = getattr(vuln, 'type', '').lower()
                    if any(cat.replace('_', ' ') in vuln_category.lower() for cat in categories):
                        filtered_result.append(vuln)
                result = filtered_result
            
            # Convertir tous les objets en dicts pour le retour
            serialized_result = []
            for vuln in result:
                if hasattr(vuln, '__dict__'):
                    serialized_result.append({
                        'type': vuln.type,
                        'severity': vuln.gravité,
                        'file': vuln.fichier,
                        'line': vuln.ligne,
                        'description': vuln.description,
                        'code': vuln.code_vulnérable,
                        'recommendation': vuln.recommandation,
                        'cwe': vuln.cwe_id,
                        'owasp': vuln.catégorie_owasp
                    })
                else:
                    serialized_result.append(vuln)
            
            return {"success": True, "vulnerabilities": serialized_result, "mode": scan_mode}
        except Exception as e:
            signal.alarm(0)
            return {"success": False, "error": str(e)[:50]}
            
    except Exception as e:
        return {"success": False, "error": str(e)[:50]}


class ScanningScreen(Screen):
    """Écran de scan avec interface moderne et tableau en temps réel"""
    
    BINDINGS = [("escape", "cancel_scan", "Annuler")]
    
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
    
    .mode-badge {
        text-align: center;
        text-style: bold;
        height: auto;
        margin: 0 0 1 0;
    }
    
    .mode-quick {
        color: $success;
    }
    
    .mode-full {
        color: $primary;
    }
    
    .progress-section {
        height: auto;
        margin: 0 0 1 0;
    }
    
    ProgressBar {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
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
        grid-size: 5;
        grid-gutter: 1;
        height: auto;
    }
    
    .stat-box {
        text-align: center;
        height: auto;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }
    
    .stat-label {
        color: $text-muted;
        height: auto;
    }
    
    .stat-value {
        text-style: bold;
        color: $accent;
        height: auto;
    }
    
    .table-section {
        height: 1fr;
        margin: 0 0 1 0;
        border: solid $primary;
    }
    
    DataTable {
        height: 100%;
    }
    
    .status-section {
        height: auto;
        background: $panel;
        padding: 1;
        margin: 0 0 1 0;
        border: solid $primary-lighten-1;
    }
    
    .current-file {
        text-style: bold;
        color: $accent;
        height: auto;
    }
    
    .actions {
        height: auto;
    }
    
    Button {
        width: 100%;
    }
    
    .warning {
        color: $warning;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Interface moderne avec tableau"""
        yield Header(show_clock=True)
        
        scan_mode = getattr(self.app, "scan_mode", "quick")
        mode_icon = "🚀" if scan_mode == "quick" else "🔬"
        mode_text = "Mode Rapide" if scan_mode == "quick" else "Mode Complet"
        mode_class = "mode-quick" if scan_mode == "quick" else "mode-full"
        
        with Vertical(classes="main-container"):
            # En-tête
            with Container(classes="header-section"):
                yield Static("🔍 Analyse de Sécurité en Cours", classes="title")
                yield Static(
                    f"{mode_icon} {mode_text}",
                    id="mode-badge",
                    classes=f"mode-badge {mode_class}"
                )
            
            # Progression
            with Container(classes="progress-section"):
                yield ProgressBar(total=100, show_percentage=True, id="progress")
                yield Static("Initialisation...", id="progress-text")
            
            # Statistiques
            with Container(classes="stats-bar"):
                with Container(classes="stats-grid"):
                    yield Container(
                        Static("Fichiers", classes="stat-label"),
                        Static("0/0", id="stat-files", classes="stat-value"),
                        classes="stat-box"
                    )
                    yield Container(
                        Static("Vulnérabilités", classes="stat-label"),
                        Static("0", id="stat-vulns", classes="stat-value"),
                        classes="stat-box"
                    )
                    yield Container(
                        Static("Timeouts", classes="stat-label"),
                        Static("0", id="stat-timeouts", classes="stat-value"),
                        classes="stat-box"
                    )
                    yield Container(
                        Static("Erreurs", classes="stat-label"),
                        Static("0", id="stat-errors", classes="stat-value"),
                        classes="stat-box"
                    )
                    yield Container(
                        Static("Temps", classes="stat-label"),
                        Static("0s", id="stat-time", classes="stat-value"),
                        classes="stat-box"
                    )
            
            # Table des résultats en temps réel
            with Container(classes="table-section"):
                yield DataTable(
                    id="results-table",
                    zebra_stripes=True,
                    show_cursor=False
                )
            
            # Statut actuel
            with Container(classes="status-section"):
                yield Static("📄 En attente...", id="current-file", classes="current-file")
                yield Static("", id="status-details")
            
            # Actions
            with Container(classes="actions"):
                yield Button("🛑 Annuler le Scan", id="cancel", variant="error")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialisation"""
        self.scanning = True
        self.scan_task = None
        self.timeouts = 0
        self.errors = 0
        self.total_vulns = 0
        self.start_time = asyncio.get_event_loop().time()
        
        # Initialiser la table
        table = self.query_one("#results-table", DataTable)
        table.add_columns("Fichier", "Statut", "Vulnérabilités", "Temps")
        
        # Démarrer le scan
        self.set_timer(0.5, self.start_scanning)
    
    def start_scanning(self) -> None:
        """Démarrer le scan"""
        files = getattr(self.app, "selected_files", [])
        
        if not files:
            self.app.notify("❌ Aucun fichier", severity="error")
            self.app.pop_screen()
            return
        
        scan_mode = getattr(self.app, "scan_mode", "quick")
        mode_text = "🚀 Rapide" if scan_mode == "quick" else "🔬 Complet"
        
        self.query_one("#progress-text", Static).update(f"{len(files)} fichiers - {mode_text}")
        self.scan_task = asyncio.create_task(self.perform_scan(files))
    
    async def perform_scan(self, files: list) -> None:
        """Effectuer le scan avec feedback en temps réel"""
        all_vulnerabilities = []
        
        # Paramètres
        scan_mode = getattr(self.app, "scan_mode", "quick")
        base_timeout = getattr(self.app, "scan_timeout", 2.0)
        scan_categories = getattr(self.app, "scan_categories", "all")
        
        # Ajuster le timeout
        if scan_mode == "quick":
            timeout_per_file = 2.0 if len(files) <= 50 else 1.5
        else:
            timeout_per_file = 5.0 if len(files) <= 50 else 3.0
        
        # Executor
        try:
            executor = ProcessPoolExecutor(max_workers=1)
        except:
            from concurrent.futures import ThreadPoolExecutor
            executor = ThreadPoolExecutor(max_workers=1)
            self.app.notify("⚠️ Mode thread", timeout=2, severity="warning")
        
        loop = asyncio.get_event_loop()
        table = self.query_one("#results-table", DataTable)
        
        for i, file_path in enumerate(files, 1):
            if not self.scanning:
                break
            
            # Mise à jour UI
            percent = int((i / len(files)) * 100)
            self.query_one("#progress", ProgressBar).update(progress=percent)
            self.query_one("#stat-files", Static).update(f"{i}/{len(files)}")
            
            filename = Path(file_path).name
            self.query_one("#current-file", Static).update(f"📄 {filename}")
            self.query_one("#status-details", Static).update("⏳ Analyse en cours...")
            
            # Temps écoulé
            elapsed_total = asyncio.get_event_loop().time() - self.start_time
            self.query_one("#stat-time", Static).update(f"{int(elapsed_total)}s")
            
            await asyncio.sleep(0.05)
            
            if not Path(file_path).exists():
                self.errors += 1
                self.query_one("#stat-errors", Static).update(str(self.errors))
                table.add_row(filename[:30], "⚠️ Introuvable", "0", "0s")
                continue
            
            # Scanner le fichier
            file_start = asyncio.get_event_loop().time()
            
            try:
                future = loop.run_in_executor(
                    executor,
                    scan_single_file,
                    file_path,
                    scan_mode,
                    scan_categories
                )
                
                result = None
                scan_time = 0
                
                while True:
                    try:
                        result = await asyncio.wait_for(asyncio.shield(future), timeout=0.2)
                        break
                    except asyncio.TimeoutError:
                        scan_time = asyncio.get_event_loop().time() - file_start
                        
                        if scan_time > timeout_per_file:
                            self.timeouts += 1
                            self.query_one("#stat-timeouts", Static).update(str(self.timeouts))
                            table.add_row(
                                filename[:30],
                                f"⏱️ Timeout",
                                "0",
                                f"{timeout_per_file:.1f}s"
                            )
                            future.cancel()
                            result = None
                            break
                        
                        await asyncio.sleep(0)
                
                # Traiter le résultat
                scan_time = asyncio.get_event_loop().time() - file_start
                
                if result and isinstance(result, dict) and result.get("success"):
                    vulnerabilities = result.get("vulnerabilities", [])
                    all_vulnerabilities.extend(vulnerabilities)
                    self.total_vulns += len(vulnerabilities)
                    
                    self.query_one("#stat-vulns", Static).update(str(self.total_vulns))
                    
                    if vulnerabilities:
                        status_icon = "🔴"
                        status_text = f"{len(vulnerabilities)} vuln."
                    else:
                        status_icon = "✅"
                        status_text = "OK"
                    
                    table.add_row(
                        filename[:30],
                        f"{status_icon} {status_text}",
                        str(len(vulnerabilities)),
                        f"{scan_time:.1f}s"
                    )
                    
                    self.query_one("#status-details", Static).update(
                        f"✅ {len(vulnerabilities)} vulnérabilité(s) trouvée(s)"
                    )
                else:
                    self.errors += 1
                    self.query_one("#stat-errors", Static).update(str(self.errors))
                    error_msg = result.get("error", "Erreur") if result else "Erreur"
                    table.add_row(
                        filename[:30],
                        f"⚠️ {error_msg[:20]}",
                        "0",
                        f"{scan_time:.1f}s"
                    )
                
            except Exception as e:
                self.errors += 1
                self.query_one("#stat-errors", Static).update(str(self.errors))
                table.add_row(filename[:30], f"❌ Erreur", "0", "0s")
            
            await asyncio.sleep(0.05)
        
        # Nettoyage
        executor.shutdown(wait=False)
        
        if not self.scanning:
            self.query_one("#current-file", Static).update("🛑 Scan annulé")
            await asyncio.sleep(1)
            self.app.pop_screen()
            return
        
        # Finalisation
        self.query_one("#progress", ProgressBar).update(progress=100)
        
        mode_icon = "🚀" if scan_mode == "quick" else "🔬"
        self.query_one("#current-file", Static).update(f"✅ Scan {mode_icon} terminé !")
        
        total_time = int(asyncio.get_event_loop().time() - self.start_time)
        self.query_one("#stat-time", Static).update(f"{total_time}s")
        
        # Message final
        if self.total_vulns > 0:
            severity_text = "critiques" if scan_mode == "quick" else "trouvées"
            self.query_one("#status-details", Static).update(
                f"🔍 {self.total_vulns} vulnérabilité(s) {severity_text}"
            )
        else:
            self.query_one("#status-details", Static).update("✅ Aucune vulnérabilité détectée")
        
        # Warnings
        if self.timeouts > 0 or self.errors > 0:
            warnings = []
            if self.timeouts > 0:
                warnings.append(f"{self.timeouts} timeout(s)")
            if self.errors > 0:
                warnings.append(f"{self.errors} erreur(s)")
            self.app.notify(f"⚠️ " + " | ".join(warnings), severity="warning")
        
        # Sauvegarder et naviguer
        self.app.set_scan_results(all_vulnerabilities)
        await asyncio.sleep(2)
        
        try:
            from src.screens.results import ResultsScreen
            self.app.push_screen(ResultsScreen())
        except ImportError:
            self.app.notify("❌ Erreur résultats", severity="error")
            self.app.pop_screen()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestion des boutons"""
        if event.button.id == "cancel":
            self.action_cancel_scan()
    
    def action_cancel_scan(self) -> None:
        """Annuler le scan"""
        self.scanning = False
        
        if self.scan_task and not self.scan_task.done():
            self.scan_task.cancel()
        
        self.query_one("#current-file", Static).update("🛑 Annulation...")
        
        async def return_to_previous():
            await asyncio.sleep(0.5)
            self.app.pop_screen()
        
        asyncio.create_task(return_to_previous())