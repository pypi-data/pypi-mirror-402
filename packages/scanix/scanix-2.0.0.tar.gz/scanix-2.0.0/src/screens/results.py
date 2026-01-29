"""
Écran des résultats - Version Finale Corrigée
src/screens/results.py
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Label, Static, DataTable, Header, Footer
from textual.containers import Container, ScrollableContainer, Vertical
from pathlib import Path
import json
from datetime import datetime
import csv


class ResultsScreen(Screen):
    """Affichage des résultats avec filtrage et export"""
    
    BINDINGS = [
        ("escape", "back", "Retour"),
        ("n", "new_scan", "Nouveau scan"),
        ("s", "toggle_sort", "Trier"),
        ("c", "copy_details", "Copier détails"),
    ]
    
    CSS = """
    ResultsScreen {
        background: $surface;
    }
    
    .main-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    .header-container {
        height: 3;
        background: $primary;
        padding: 0 1;
        margin: 0 0 1 0;
        border: solid $accent;
        layout: horizontal;
    }
    
    .header-title {
        width: 1fr;
        text-style: bold;
        color: $text;
        content-align: left middle;
    }
    
    .header-stats {
        width: auto;
        content-align: right middle;
    }
    
    .filter-container {
        height: auto;
        background: $panel;
        padding: 1;
        margin: 0 0 1 0;
        border: solid $primary-lighten-1;
    }
    
    .filter-label {
        height: auto;
        margin: 0 0 1 0;
    }
    
    .filter-grid {
        layout: grid;
        grid-size: 5;
        grid-gutter: 1;
        height: auto;
    }
    
    .filter-grid Button {
        width: 100%;
        min-height: 3;
    }
    
    .stat-critical { border: solid red; }
    .stat-high { border: solid orange; }
    .stat-medium { border: solid yellow; }
    .stat-low { border: solid green; }
    .stat-all { border: solid $primary; }
    
    .table-container {
        height: 1fr;
        margin: 0 0 1 0;
        border: solid $primary;
    }
    
    DataTable {
        height: 100%;
    }
    
    .details-container {
        height: 20;
        margin: 0 0 1 0;
        border: solid white;
        background: black;
    }
    
    .details-header {
        height: auto;
        background: black;
        padding: 1;
        border-bottom: solid white;
    }
    
    .details-title {
        color: white;
        text-style: bold;
    }
    
    .details-scroll {
        height: 1fr;
        padding: 1;
        background: black;
    }
    
    .details-content {
        color: white;
        background: black;
    }
    
    .actions-container {
        height: auto;
    }
    
    .actions-grid {
        layout: grid;
        grid-size: 6;
        grid-gutter: 1;
        height: auto;
    }
    
    Button {
        width: 100%;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose l'interface"""
        yield Header(show_clock=False)
        
        with Vertical(classes="main-container"):
            # En-tête compact
            with Container(classes="header-container"):
                yield Label("🔒 Résultats du Scan", classes="header-title")
                yield Static("", id="header-stats", classes="header-stats")
            
            # Filtres avec statistiques
            with Container(classes="filter-container"):
                yield Static("🔍 Filtrer par gravité:", classes="filter-label")
                with Container(classes="filter-grid"):
                    yield Button("Tous", id="filter-all", variant="primary", classes="stat-all")
                    yield Button("🔴 Critiques", id="filter-critical", variant="default", classes="stat-critical")
                    yield Button("🟠 Élevées", id="filter-high", variant="default", classes="stat-high")
                    yield Button("🟡 Moyennes", id="filter-medium", variant="default", classes="stat-medium")
                    yield Button("🟢 Faibles", id="filter-low", variant="default", classes="stat-low")
            
            # Table des vulnérabilités
            with Container(classes="table-container"):
                yield DataTable(id="vuln-table", zebra_stripes=True, cursor_type="row", show_cursor=True)
            
            # Zone de détails
            with Container(classes="details-container"):
                with Container(classes="details-header"):
                    yield Static("📋 Détails de la vulnérabilité (Appuyez sur C pour copier)", classes="details-title")
                with ScrollableContainer(classes="details-scroll"):
                    yield Static("👆 Sélectionnez une vulnérabilité dans le tableau ci-dessus pour voir les détails", 
                               id="details", 
                               classes="details-content")
            
            # Actions
            with Container(classes="actions-container"):
                with Container(classes="actions-grid"):
                    yield Button("← Retour", id="back", variant="default")
                    yield Button("📄 JSON", id="export-json", variant="success")
                    yield Button("🌐 HTML", id="export-html", variant="success")
                    yield Button("📝 TXT", id="export-txt", variant="success")
                    yield Button("📊 CSV", id="export-csv", variant="success")
                    yield Button("🔄 Nouveau", id="new-scan", variant="primary")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialisation"""
        raw_results = getattr(self.app, 'scan_results', [])
        self.scan_mode = getattr(self.app, 'scan_mode', 'quick')
        self.selected_files = getattr(self.app, 'selected_files', [])
        
        self.current_filter = "all"
        self.sort_order = "severity"
        self.current_vuln_details = None
        
        self.all_vulnerabilities = self.parse_vulnerabilities(raw_results)
        self.filtered_vulnerabilities = self.all_vulnerabilities.copy()
        self.stats = self.calculate_statistics()
        
        self.update_header_info()
        self.update_filter_buttons()
        self.display_table()
        
        try:
            self.query_one("#vuln-table", DataTable).focus()
        except:
            pass
    
    def calculate_statistics(self) -> dict:
        """Calcule les stats"""
        stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}
        for v in self.all_vulnerabilities:
            severity = v['severity']
            if severity in stats:
                stats[severity] += 1
            stats['total'] += 1
        return stats
    
    def update_header_info(self) -> None:
        """Met à jour l'en-tête"""
        mode_icon = "🚀" if self.scan_mode == "quick" else "🔬"
        mode_text = "Rapide" if self.scan_mode == "quick" else "Complet"
        nb_files = len(self.selected_files)
        
        header_text = f"{mode_icon} {mode_text} | 📁 {nb_files} fichier(s) | ⚠️ {self.stats['total']} trouvée(s)"
        self.query_one("#header-stats", Static).update(header_text)
    
    def update_filter_buttons(self) -> None:
        """Met à jour les boutons de filtre"""
        filter_texts = {
            "all": f"Tous ({self.stats['total']})",
            "critical": f"🔴 Critiques ({self.stats['critical']})",
            "high": f"🟠 Élevées ({self.stats['high']})",
            "medium": f"🟡 Moyennes ({self.stats['medium']})",
            "low": f"🟢 Faibles ({self.stats['low']})"
        }
        
        for filter_type, text in filter_texts.items():
            try:
                btn = self.query_one(f"#filter-{filter_type}", Button)
                btn.label = text
                btn.variant = "primary" if filter_type == self.current_filter else "default"
            except:
                pass
    
    def parse_vulnerabilities(self, raw_results: list) -> list:
        """Parse les vulnérabilités"""
        structured = []
        
        for item in raw_results:
            try:
                if isinstance(item, dict):
                    vuln = {
                        'type': str(item.get('type', 'Unknown'))[:50],
                        'severity': str(item.get('severity', item.get('gravité', 'medium'))).lower(),
                        'file': str(item.get('file', item.get('fichier', 'Unknown')))[:100],
                        'line': int(item.get('line', item.get('ligne', 0)) or 0),
                        'description': str(item.get('description', 'No description'))[:200],
                        'code': str(item.get('code', item.get('code_vulnérable', '')))[:150],
                        'recommendation': str(item.get('recommendation', item.get('recommandation', '')))[:200],
                        'cwe': str(item.get('cwe', item.get('cwe_id', 'N/A')))[:20],
                        'owasp': str(item.get('owasp', item.get('catégorie_owasp', 'N/A')))[:50]
                    }
                else:
                    vuln = {
                        'type': str(getattr(item, 'type', 'Unknown'))[:50],
                        'severity': str(getattr(item, 'gravité', getattr(item, 'severity', 'medium'))).lower(),
                        'file': str(getattr(item, 'fichier', getattr(item, 'file', 'Unknown')))[:100],
                        'line': int(getattr(item, 'ligne', getattr(item, 'line', 0)) or 0),
                        'description': str(getattr(item, 'description', 'No description'))[:200],
                        'code': str(getattr(item, 'code_vulnérable', getattr(item, 'code', '')))[:150],
                        'recommendation': str(getattr(item, 'recommandation', getattr(item, 'recommendation', '')))[:200],
                        'cwe': str(getattr(item, 'cwe_id', getattr(item, 'cwe', 'N/A')))[:20],
                        'owasp': str(getattr(item, 'catégorie_owasp', getattr(item, 'owasp', 'N/A')))[:50]
                    }
                
                severity_map = {
                    'critique': 'critical', 'critical': 'critical',
                    'élevée': 'high', 'high': 'high', 'elevee': 'high',
                    'moyenne': 'medium', 'medium': 'medium',
                    'faible': 'low', 'low': 'low'
                }
                vuln['severity'] = severity_map.get(vuln['severity'], 'medium')
                structured.append(vuln)
            except:
                continue
        
        return self.sort_vulnerabilities(structured, "severity")
    
    def sort_vulnerabilities(self, vulns: list, sort_by: str) -> list:
        """Trie les vulnérabilités"""
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        if sort_by == "severity":
            return sorted(vulns, key=lambda v: severity_order.get(v['severity'], 4))
        elif sort_by == "file":
            return sorted(vulns, key=lambda v: v['file'])
        elif sort_by == "type":
            return sorted(vulns, key=lambda v: v['type'])
        return vulns
    
    def apply_filter(self, filter_type: str) -> None:
        """Applique un filtre"""
        self.current_filter = filter_type
        
        if filter_type == "all":
            self.filtered_vulnerabilities = self.all_vulnerabilities.copy()
        else:
            self.filtered_vulnerabilities = [
                v for v in self.all_vulnerabilities 
                if v['severity'] == filter_type
            ]
        
        self.update_filter_buttons()
        self.display_table()
        
        count = len(self.filtered_vulnerabilities)
        self.app.notify(f"🔍 {count} vulnérabilité(s) affichée(s)", timeout=2)
    
    def action_toggle_sort(self) -> None:
        """Change le tri"""
        sorts = ["severity", "type", "file"]
        current_idx = sorts.index(self.sort_order)
        self.sort_order = sorts[(current_idx + 1) % len(sorts)]
        
        self.filtered_vulnerabilities = self.sort_vulnerabilities(
            self.filtered_vulnerabilities, 
            self.sort_order
        )
        
        self.display_table()
        
        sort_names = {"severity": "Gravité", "type": "Type", "file": "Fichier"}
        self.app.notify(f"📊 Trié par: {sort_names[self.sort_order]}", timeout=2)
    
    def display_table(self) -> None:
        """Affiche la table"""
        table = self.query_one("#vuln-table", DataTable)
        table.clear(columns=True)
        
        table.add_columns("N°", "Type", "Gravité", "Fichier", "Ligne", "CWE")
        
        if not self.filtered_vulnerabilities:
            table.add_row("", "Aucun résultat trouvé", "", "", "", "")
            return
        
        severity_icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        
        for i, vuln in enumerate(self.filtered_vulnerabilities):
            icon = severity_icons.get(vuln['severity'], "⚪")
            
            table.add_row(
                str(i + 1),
                vuln['type'][:25],
                f"{icon} {vuln['severity'][:4].upper()}",
                Path(vuln['file']).name[:20],
                str(vuln['line']) if vuln['line'] > 0 else "?",
                vuln['cwe'][:10]
            )
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Affiche les détails quand on sélectionne une ligne"""
        if not self.filtered_vulnerabilities:
            return
        
        try:
            cursor_row = event.cursor_row
            
            if cursor_row is not None and 0 <= cursor_row < len(self.filtered_vulnerabilities):
                vuln = self.filtered_vulnerabilities[cursor_row]
                self.show_vulnerability_details(vuln)
        except Exception as e:
            self.app.notify(f"⚠️ Erreur: {str(e)[:50]}", severity="warning")
    
    def show_vulnerability_details(self, vuln: dict) -> None:
        """Affiche les détails d'une vulnérabilité"""
        try:
            details_widget = self.query_one("#details", Static)
            
            severity_labels = {
                "critical": "🔴 CRITIQUE",
                "high": "🟠 ÉLEVÉE",
                "medium": "🟡 MOYENNE",
                "low": "🟢 FAIBLE"
            }
            
            # Construction du texte des détails
            text_lines = []
            text_lines.append("═" * 70)
            text_lines.append(f"  TYPE: {vuln['type']}")
            text_lines.append("═" * 70)
            text_lines.append("")
            text_lines.append(f"⚠️  GRAVITÉ: {severity_labels.get(vuln['severity'], vuln['severity'])}")
            text_lines.append("")
            text_lines.append(f"📄 FICHIER: {vuln['file']}")
            text_lines.append(f"📍 LIGNE: {vuln['line']}")
            text_lines.append(f"📚 CWE: {vuln['cwe']}")
            text_lines.append(f"🔐 OWASP: {vuln['owasp']}")
            text_lines.append("")
            text_lines.append("─" * 70)
            text_lines.append("DESCRIPTION:")
            text_lines.append("─" * 70)
            text_lines.append(vuln['description'])
            text_lines.append("")
            
            if vuln['code']:
                text_lines.append("─" * 70)
                text_lines.append("CODE VULNÉRABLE:")
                text_lines.append("─" * 70)
                text_lines.append(vuln['code'])
                text_lines.append("")
            
            if vuln['recommendation']:
                text_lines.append("─" * 70)
                text_lines.append("✅ RECOMMANDATION:")
                text_lines.append("─" * 70)
                text_lines.append(vuln['recommendation'])
                text_lines.append("")
            
            text_lines.append("═" * 70)
            
            details_text = "\n".join(text_lines)
            
            # Mettre à jour le widget
            details_widget.update(details_text)
            
            # Sauvegarder pour la copie
            self.current_vuln_details = details_text
            
        except Exception as e:
            self.app.notify(f"⚠️ Erreur affichage: {str(e)[:50]}", severity="warning")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Gestion des boutons"""
        btn_id = event.button.id
        
        if btn_id.startswith("filter-"):
            filter_type = btn_id.replace("filter-", "")
            self.apply_filter(filter_type)
        elif btn_id == "back":
            self.action_back()
        elif btn_id == "new-scan":
            self.action_new_scan()
        elif btn_id.startswith("export-"):
            format_type = btn_id.replace("export-", "")
            self.export_results(format_type)
    
    def action_back(self) -> None:
        """Retour à l'écran précédent"""
        self.app.pop_screen()
    
    def action_copy_details(self) -> None:
        """Copie les détails dans le presse-papier"""
        if self.current_vuln_details:
            try:
                import pyperclip
                pyperclip.copy(self.current_vuln_details)
                self.app.notify("✅ Détails copiés dans le presse-papier!", timeout=3)
            except ImportError:
                try:
                    import subprocess
                    subprocess.run(['xclip', '-selection', 'clipboard'], 
                                 input=self.current_vuln_details.encode('utf-8'), 
                                 check=True)
                    self.app.notify("✅ Détails copiés!", timeout=3)
                except:
                    self.app.notify("⚠️ Installez pyperclip: pip install pyperclip", 
                                  severity="warning", timeout=5)
            except Exception as e:
                self.app.notify(f"❌ Erreur: {str(e)[:30]}", severity="error")
        else:
            self.app.notify("⚠️ Sélectionnez d'abord une vulnérabilité", severity="warning")
    
    def action_new_scan(self) -> None:
        """Démarre un nouveau scan"""
        try:
            self.app.selected_files = []
            self.app.scan_results = []
            self.app.scan_mode = "quick"
            
            from src.screens.welcome import WelcomeScreen
            
            while len(self.app.screen_stack) > 0:
                try:
                    self.app.pop_screen()
                except:
                    break
            
            self.app.push_screen(WelcomeScreen())
            self.app.notify("🔄 Nouveau scan prêt", timeout=2)
        except:
            try:
                self.app.pop_screen()
            except:
                pass
    
    def get_export_dir(self) -> Path:
        """Retourne le dossier d'export"""
        export_dir = Path.home() / "SecureCode_Exports"
        export_dir.mkdir(exist_ok=True)
        return export_dir
    
    def export_results(self, format_type: str) -> None:
        """Exporte les résultats"""
        if not self.filtered_vulnerabilities:
            self.app.notify("❌ Aucune vulnérabilité à exporter", severity="warning")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode_suffix = "rapide" if self.scan_mode == "quick" else "complet"
            filter_suffix = f"_{self.current_filter}" if self.current_filter != "all" else ""
            filename = f"scan_{mode_suffix}{filter_suffix}_{timestamp}.{format_type}"
            
            export_dir = self.get_export_dir()
            filepath = export_dir / filename
            
            if format_type == "json":
                self.export_json(filepath)
            elif format_type == "html":
                self.export_html(filepath)
            elif format_type == "txt":
                self.export_txt(filepath)
            elif format_type == "csv":
                self.export_csv(filepath)
            
            self.app.notify(f"✅ Exporté: {filename}", timeout=5)
        except Exception as e:
            self.app.notify(f"❌ Erreur export: {str(e)[:40]}", severity="error")
    
    def export_json(self, filepath: Path) -> None:
        """Export JSON"""
        data = {
            "scan_info": {
                "mode": self.scan_mode,
                "date": datetime.now().isoformat(),
                "files_scanned": len(self.selected_files),
                "filter": self.current_filter,
                "total_vulnerabilities": len(self.filtered_vulnerabilities),
                "statistics": self.stats
            },
            "vulnerabilities": self.filtered_vulnerabilities
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export_html(self, filepath: Path) -> None:
        """Export HTML"""
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport SecureCode - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f5f5f5; 
            padding: 20px;
        }}
        .header {{ 
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white; 
            padding: 30px; 
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-bottom: 20px; 
        }}
        .stat-box {{ 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid;
        }}
        .stat-box h3 {{ font-size: 2em; margin-bottom: 5px; }}
        .stat-box.critical {{ border-color: #dc2626; color: #dc2626; }}
        .stat-box.high {{ border-color: #ea580c; color: #ea580c; }}
        .stat-box.medium {{ border-color: #eab308; color: #eab308; }}
        .stat-box.low {{ border-color: #16a34a; color: #16a34a; }}
        .vuln {{ 
            background: white; 
            margin: 15px 0; 
            padding: 20px; 
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid;
        }}
        .vuln.critical {{ border-color: #dc2626; }}
        .vuln.high {{ border-color: #ea580c; }}
        .vuln.medium {{ border-color: #eab308; }}
        .vuln.low {{ border-color: #16a34a; }}
        .vuln h3 {{ color: #1f2937; margin-bottom: 15px; }}
        .vuln-meta {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 10px;
            margin: 15px 0;
            padding: 15px;
            background: #f9fafb;
            border-radius: 5px;
        }}
        .vuln-meta strong {{ color: #374151; }}
        .section {{ margin: 15px 0; }}
        .section-title {{ 
            font-weight: bold; 
            color: #1f2937; 
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 2px solid #e5e7eb;
        }}
        code {{ 
            background: #f3f4f6; 
            padding: 10px; 
            display: block; 
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Rapport de Scan de Sécurité</h1>
        <p><strong>Mode:</strong> {self.scan_mode.upper()} | 
           <strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
           <strong>Fichiers scannés:</strong> {len(self.selected_files)} | 
           <strong>Filtre:</strong> {self.current_filter.upper()}</p>
    </div>
    
    <div class="stats">
        <div class="stat-box critical">
            <h3>{self.stats['critical']}</h3>
            <p>Critiques</p>
        </div>
        <div class="stat-box high">
            <h3>{self.stats['high']}</h3>
            <p>Élevées</p>
        </div>
        <div class="stat-box medium">
            <h3>{self.stats['medium']}</h3>
            <p>Moyennes</p>
        </div>
        <div class="stat-box low">
            <h3>{self.stats['low']}</h3>
            <p>Faibles</p>
        </div>
    </div>
    
    <h2 style="color: #1f2937; margin: 20px 0;">Vulnérabilités Détectées ({len(self.filtered_vulnerabilities)})</h2>
"""
        
        for i, vuln in enumerate(self.filtered_vulnerabilities, 1):
            html += f"""
    <div class="vuln {vuln['severity']}">
        <h3>#{i} - {vuln['type']}</h3>
        <div class="vuln-meta">
            <div><strong>Gravité:</strong> {vuln['severity'].upper()}</div>
            <div><strong>Fichier:</strong> {Path(vuln['file']).name}</div>
            <div><strong>Ligne:</strong> {vuln['line']}</div>
            <div><strong>CWE:</strong> {vuln['cwe']}</div>
            <div><strong>OWASP:</strong> {vuln['owasp']}</div>
        </div>
        <div class="section">
            <div class="section-title">Description</div>
            <p>{vuln['description']}</p>
        </div>
"""
            if vuln['code']:
                html += f"""
        <div class="section">
            <div class="section-title">Code Vulnérable</div>
            <code>{vuln['code']}</code>
        </div>
"""
            if vuln['recommendation']:
                html += f"""
        <div class="section">
            <div class="section-title">✅ Recommandation</div>
            <p>{vuln['recommendation']}</p>
        </div>
"""
            html += "    </div>\n"
        
        html += """
</body>
</html>
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def export_txt(self, filepath: Path) -> None:
        """Export TXT"""
        lines = []
        lines.append("=" * 80)
        lines.append("RAPPORT DE SCAN DE SÉCURITÉ - SECURECODE")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Mode de scan: {self.scan_mode.upper()}")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Fichiers scannés: {len(self.selected_files)}")
        lines.append(f"Filtre appliqué: {self.current_filter.upper()}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("STATISTIQUES")
        lines.append("-" * 80)
        lines.append(f"🔴 Critiques: {self.stats['critical']}")
        lines.append(f"🟠 Élevées: {self.stats['high']}")
        lines.append(f"🟡 Moyennes: {self.stats['medium']}")
        lines.append(f"🟢 Faibles: {self.stats['low']}")
        lines.append(f"📊 TOTAL: {self.stats['total']}")
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"VULNÉRABILITÉS DÉTECTÉES ({len(self.filtered_vulnerabilities)})")
        lines.append("=" * 80)
        lines.append("")
        
        for i, vuln in enumerate(self.filtered_vulnerabilities, 1):
            lines.append(f"#{i} - {vuln['type']}")
            lines.append("-" * 80)
            lines.append(f"  Gravité: {vuln['severity'].upper()}")
            lines.append(f"  Fichier: {vuln['file']}")
            lines.append(f"  Ligne: {vuln['line']}")
            lines.append(f"  CWE: {vuln['cwe']}")
            lines.append(f"  OWASP: {vuln['owasp']}")
            lines.append("")
            lines.append("  Description:")
            lines.append(f"    {vuln['description']}")
            lines.append("")
            
            if vuln['code']:
                lines.append("  Code vulnérable:")
                lines.append(f"    {vuln['code']}")
                lines.append("")
            
            if vuln['recommendation']:
                lines.append("  ✅ Recommandation:")
                lines.append(f"    {vuln['recommendation']}")
                lines.append("")
            
            lines.append("=" * 80)
            lines.append("")
        
        lines.append("")
        lines.append("Rapport généré par SecureCode")
        lines.append(f"https://github.com/votre-projet/securecode")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def export_csv(self, filepath: Path) -> None:
        """Export CSV"""
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # En-tête du fichier
            writer.writerow(['RAPPORT DE SCAN - SECURECODE'])
            writer.writerow([f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([f'Mode: {self.scan_mode.upper()}'])
            writer.writerow([f'Fichiers scannés: {len(self.selected_files)}'])
            writer.writerow([f'Filtre: {self.current_filter.upper()}'])
            writer.writerow([])
            
            # Statistiques
            writer.writerow(['STATISTIQUES'])
            writer.writerow(['Gravité', 'Nombre'])
            writer.writerow(['Critiques', self.stats['critical']])
            writer.writerow(['Élevées', self.stats['high']])
            writer.writerow(['Moyennes', self.stats['medium']])
            writer.writerow(['Faibles', self.stats['low']])
            writer.writerow(['TOTAL', self.stats['total']])
            writer.writerow([])
            
            # En-tête du tableau des vulnérabilités
            writer.writerow([
                'N°',
                'Type',
                'Gravité',
                'Fichier',
                'Ligne',
                'CWE',
                'OWASP',
                'Description',
                'Code vulnérable',
                'Recommandation'
            ])
            
            # Données des vulnérabilités
            for i, vuln in enumerate(self.filtered_vulnerabilities, 1):
                writer.writerow([
                    i,
                    vuln['type'],
                    vuln['severity'].upper(),
                    vuln['file'],
                    vuln['line'],
                    vuln['cwe'],
                    vuln['owasp'],
                    vuln['description'],
                    vuln['code'],
                    vuln['recommendation']
                ])