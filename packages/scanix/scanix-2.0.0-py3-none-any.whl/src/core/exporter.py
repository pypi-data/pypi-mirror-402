"""
Exporteur de rapports de sécurité
Formats: JSON, HTML, TXT
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List
import html


class ExporteurVulnérabilités:
    """Exporte les résultats de scan"""
    
    @staticmethod
    def vers_json(vulnérabilités: List, chemin: str = None) -> str:
        """Export JSON structuré"""
        if not chemin:
            chemin = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        rapport = {
            "metadata": {
                "date": datetime.now().isoformat(),
                "scanner": "SecureCode AI Scanner",
                "version": "1.0",
                "total": len(vulnérabilités)
            },
            "statistiques": {
                "critique": sum(1 for v in vulnérabilités if v.gravité == "critique"),
                "élevée": sum(1 for v in vulnérabilités if v.gravité == "élevée"),
                "moyenne": sum(1 for v in vulnérabilités if v.gravité == "moyenne"),
                "faible": sum(1 for v in vulnérabilités if v.gravité == "faible")
            },
            "vulnérabilités": [
                {
                    "type": v.type,
                    "gravité": v.gravité,
                    "fichier": str(Path(v.fichier).name),
                    "chemin_complet": v.fichier,
                    "ligne": v.ligne,
                    "description": v.description,
                    "code": v.code_vulnérable,
                    "recommandation": v.recommandation,
                    "cwe": v.cwe_id,
                    "owasp": v.catégorie_owasp
                }
                for v in vulnérabilités
            ]
        }
        
        with open(chemin, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)
        
        return chemin
    
    @staticmethod
    def vers_html(vulnérabilités: List, chemin: str = None) -> str:
        """Export HTML avec design propre"""
        if not chemin:
            chemin = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        from src.core.explications import ExplicationsVulnérabilités
        
        # Calcul des statistiques
        stats = {
            "total": len(vulnérabilités),
            "critique": sum(1 for v in vulnérabilités if v.gravité == "critique"),
            "élevée": sum(1 for v in vulnérabilités if v.gravité == "élevée"),
            "moyenne": sum(1 for v in vulnérabilités if v.gravité == "moyenne"),
            "faible": sum(1 for v in vulnérabilités if v.gravité == "faible")
        }
        
        # Génération HTML
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de Scan - {datetime.now().strftime('%d/%m/%Y')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4a6fa5; padding-bottom: 10px; }}
        .stats {{ display: flex; gap: 20px; margin: 30px 0; flex-wrap: wrap; }}
        .stat-card {{ flex: 1; min-width: 150px; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card.critical {{ background: #ffebee; color: #c62828; border: 2px solid #c62828; }}
        .stat-card.high {{ background: #fff3e0; color: #e65100; border: 2px solid #e65100; }}
        .stat-card.medium {{ background: #fff9c4; color: #f57f17; border: 2px solid #f57f17; }}
        .stat-card.low {{ background: #e8f5e9; color: #2e7d32; border: 2px solid #2e7d32; }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; margin: 10px 0; }}
        .vuln-card {{ margin: 20px 0; padding: 20px; border-radius: 8px; border-left: 5px solid; }}
        .vuln-card.critical {{ border-color: #c62828; background: #ffebee; }}
        .vuln-card.high {{ border-color: #e65100; background: #fff3e0; }}
        .vuln-card.medium {{ border-color: #f57f17; background: #fff9c4; }}
        .vuln-card.low {{ border-color: #2e7d32; background: #e8f5e9; }}
        .code {{ background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; margin: 10px 0; font-family: 'Courier New', monospace; overflow-x: auto; }}
        .bad-code {{ border-left: 5px solid #c62828; }}
        .good-code {{ border-left: 5px solid #2e7d32; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #ddd; color: #666; text-align: center; }}
        @media (max-width: 768px) {{ .stats {{ flex-direction: column; }} .stat-card {{ min-width: 100%; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Rapport de Scan de Sécurité</h1>
        <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        <p><strong>Scanner:</strong> SecureCode AI Scanner</p>
        
        <div class="stats">
            <div class="stat-card critical">
                <div class="stat-number">{stats['critique']}</div>
                <div>Critiques</div>
            </div>
            <div class="stat-card high">
                <div class="stat-number">{stats['élevée']}</div>
                <div>Élevées</div>
            </div>
            <div class="stat-card medium">
                <div class="stat-number">{stats['moyenne']}</div>
                <div>Moyennes</div>
            </div>
            <div class="stat-card low">
                <div class="stat-number">{stats['faible']}</div>
                <div>Faibles</div>
            </div>
        </div>
        
        <h2>📊 Vulnérabilités Détectées ({stats['total']})</h2>
"""
        
        # Ajouter chaque vulnérabilité
        for i, vuln in enumerate(vulnérabilités):
            exp = ExplicationsVulnérabilités.pour_type(vuln.type)
            gravité_class = vuln.gravité.lower()
            
            html_content += f"""
        <div class="vuln-card {gravité_class}">
            <h3>#{i+1} {vuln.type} ({vuln.gravité.upper()})</h3>
            <p><strong>📍 Fichier:</strong> {html.escape(str(Path(vuln.fichier).name))} (Ligne {vuln.ligne})</p>
            <p><strong>📝 Description:</strong> {html.escape(vuln.description)}</p>
            
            <p><strong>❌ Code vulnérable:</strong></p>
            <div class="code bad-code">{html.escape(vuln.code_vulnérable)}</div>
            
            <p><strong>✅ Recommandation:</strong> {html.escape(vuln.recommandation)}</p>
            
            <p><strong>💡 Exemples:</strong></p>
            <p><em>Code vulnérable:</em></p>
            <div class="code">{html.escape(exp['exemple']['vulnérable'])}</div>
            
            <p><em>Code sécurisé:</em></p>
            <div class="code good-code">{html.escape(exp['exemple']['sécurisé'])}</div>
            
            <p><strong>📚 CWE:</strong> {vuln.cwe_id} | <strong>OWASP:</strong> {vuln.catégorie_owasp}</p>
        </div>
"""
        
        html_content += """
        <div class="footer">
            <p>Généré par SecureCode AI Scanner</p>
            <p>Pour plus d'informations sur les vulnérabilités: https://owasp.org</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return chemin
    
    @staticmethod
    def vers_txt(vulnérabilités: List, chemin: str = None) -> str:
        """Export texte simple"""
        if not chemin:
            chemin = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write(" " * 20 + "RAPPORT DE SCAN DE SÉCURITÉ\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"Total vulnérabilités: {len(vulnérabilités)}\n\n")
            
            # Statistiques
            stats = ["critique", "élevée", "moyenne", "faible"]
            for gravité in stats:
                count = sum(1 for v in vulnérabilités if v.gravité == gravité)
                if count > 0:
                    f.write(f"{gravité.upper()}: {count}\n")
            
            f.write("\n" + "="*70 + "\n\n")
            
            # Détails
            for i, vuln in enumerate(vulnérabilités, 1):
                f.write(f"{i}. {vuln.type} ({vuln.gravité.upper()})\n")
                f.write(f"   Fichier: {Path(vuln.fichier).name}:{vuln.ligne}\n")
                f.write(f"   Code: {vuln.code_vulnérable}\n")
                f.write(f"   Description: {vuln.description}\n")
                f.write(f"   Recommandation: {vuln.recommandation}\n")
                f.write(f"   CWE: {vuln.cwe_id}\n")
                f.write("-"*50 + "\n")
        
        return chemin
    
    @staticmethod
    def vers_csv(vulnérabilités: List, chemin: str = None) -> str:
        """Export CSV pour Excel/Tableurs"""
        if not chemin:
            chemin = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(chemin, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(['Gravité', 'Type', 'Fichier', 'Ligne', 'Description', 'Code', 'Recommandation', 'CWE', 'OWASP'])
            
            for vuln in vulnérabilités:
                writer.writerow([
                    vuln.gravité,
                    vuln.type,
                    Path(vuln.fichier).name,
                    vuln.ligne,
                    vuln.description,
                    vuln.code_vulnérable,
                    vuln.recommandation,
                    vuln.cwe_id,
                    vuln.catégorie_owasp
                ])
        
        return chemin