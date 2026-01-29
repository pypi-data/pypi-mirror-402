"""
Scanner de Vulnérabilités Statique - Version Complète
Détecte 25+ types de vulnérabilités avec explications détaillées
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from pathlib import Path
import re


@dataclass
class Vulnérabilité:
    """Vulnérabilité détectée avec toutes les informations"""
    type: str
    gravité: str  # critique, élevée, moyenne, faible
    fichier: str
    ligne: int
    description: str
    code_vulnérable: str
    recommandation: str
    cwe_id: str = ""
    catégorie_owasp: str = ""
    confiance: float = 0.9


class ScannerStatique:
    """Scanner statique complet - 25+ vulnérabilités"""
    
    def __init__(self):
        self.patterns = self._initialiser_patterns()
        self.langages_supportés = ['.py', '.js', '.ts', '.php', '.java', '.cpp', '.cs', '.go', '.rb', '.json', '.yml', '.yaml', '.xml', '.sql']
    
    def _initialiser_patterns(self) -> Dict[str, List[Tuple]]:
        """Initialise tous les patterns de détection"""
        
        return {
            # === 1. SECRETS EN DUR ===
            "secret_en_dur": [
                (r'password\s*=\s*["\'][^"\']{3,}["\']', "critique", "Mot de passe en dur"),
                (r'mot_de_passe\s*=\s*["\'][^"\']{3,}["\']', "critique", "Mot de passe en dur"),
                (r'api_key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', "critique", "Clé API en dur"),
                (r'secret_key\s*=\s*["\'][^"\']{10,}["\']', "critique", "Clé secrète en dur"),
                (r'private_key\s*=\s*["\'].*BEGIN.*PRIVATE', "critique", "Clé privée exposée"),
                (r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', "critique", "Token en dur"),
                (r'AWS_SECRET_ACCESS_KEY', "critique", "Clé AWS exposée"),
                (r'GITHUB_TOKEN', "critique", "Token GitHub exposé"),
                (r'DATABASE_PASSWORD', "critique", "Mot de passe DB exposé"),
            ],
            
            # === 2. INJECTION SQL ===
            "injection_sql": [
                (r'f["\'].*SELECT.*{', "critique", "Injection SQL via f-string"),
                (r'\.format\(.*\).*SELECT', "critique", "Injection SQL via format()"),
                (r'["\'].*\+.*\+.*SELECT', "critique", "Injection SQL par concaténation"),
                (r'\.execute\(.*%s.*\+', "critique", "Injection SQL avec %s"),
                (r'cursor\.execute\(.*f["\']', "critique", "Requête SQL non sécurisée"),
                (r'\$_GET\[.*\].*SELECT', "critique", "Injection SQL PHP GET"),
                (r'\$_POST\[.*\].*SELECT', "critique", "Injection SQL PHP POST"),
                (r'mysql_query\(.*\$', "critique", "mysql_query non sécurisé"),
            ],
            
            # === 3. INJECTION DE COMMANDE ===
            "injection_commande": [
                (r'os\.system\(', "critique", "os.system() dangereux"),
                (r'subprocess.*shell\s*=\s*True', "critique", "shell=True dangereux"),
                (r'exec\(.*os\.', "critique", "exec avec os"),
                (r'eval\(.*input', "critique", "eval avec input utilisateur"),
                (r'system\(.*\$', "critique", "Commande système PHP"),
                (r'shell_exec\(', "critique", "shell_exec PHP"),
                (r'passthru\(', "critique", "passthru PHP"),
                (r'Runtime\.getRuntime\(\)\.exec', "critique", "Runtime.exec Java"),
            ],
            
            # === 4. CROSS-SITE SCRIPTING (XSS) ===
            "xss": [
                (r'\.innerHTML\s*=', "élevée", "XSS via innerHTML"),
                (r'document\.write\(', "élevée", "XSS via document.write"),
                (r'\.outerHTML\s*=', "élevée", "XSS via outerHTML"),
                (r'v-html\s*=', "élevée", "XSS via v-html Vue.js"),
                (r'dangerouslySetInnerHTML', "élevée", "XSS React dangerouslySetInnerHTML"),
                (r'echo\s+\$_GET', "élevée", "XSS PHP echo GET"),
                (r'print\(.*request\.', "élevée", "XSS Python Flask/Django"),
                (r'\$\{.*\}.*</', "élevée", "XSS template injection"),
            ],
            
            # === 5. INJECTION DE CODE ===
            "injection_code": [
                (r'eval\(', "critique", "eval() dangereux"),
                (r'exec\(', "critique", "exec() dangereux"),
                (r'Function\s*\(', "critique", "Function() constructor"),
                (r'setTimeout\([^)]*\+', "élevée", "setTimeout avec concaténation"),
                (r'setInterval\([^)]*\+', "élevée", "setInterval avec concaténation"),
                (r'new Function', "critique", "new Function() dangereux"),
                (r'compile\(.*input', "critique", "compile avec input"),
            ],
            
            # === 6. DÉPASSEMENT DE TAMPON ===
            "dépassement_tampon": [
                (r'strcpy\(', "critique", "strcpy sans vérification"),
                (r'strcat\(', "critique", "strcat sans vérification"),
                (r'sprintf\(', "critique", "sprintf dangereux"),
                (r'gets\(', "critique", "gets() obsolète et dangereux"),
                (r'scanf\(.*%s', "critique", "scanf sans limite"),
                (r'memcpy\(.*sizeof', "moyenne", "memcpy potentiellement dangereux"),
            ],
            
            # === 7. GESTION DES ERREURS ===
            "gestion_erreurs": [
                (r'except\s*:\s*$', "moyenne", "except trop général"),
                (r'except\s*:\s*pass', "moyenne", "Exception ignorée"),
                (r'catch\s*\(.*\)\s*\{\s*\}', "moyenne", "Catch vide"),
                (r'printStackTrace\(\)', "faible", "Stack trace exposée"),
                (r'console\.log\(.*error', "faible", "Erreur loguée en console"),
                (r'throw\s+e;?\s*$', "faible", "Exception non enrichie"),
            ],
            
            # === 8. CONFIGURATION FAIBLE ===
            "config_faible": [
                (r'DEBUG\s*=\s*True', "moyenne", "Mode DEBUG activé"),
                (r'display_errors\s*=\s*On', "moyenne", "Affichage erreurs PHP activé"),
                (r'AllowOverride\s+All', "moyenne", "Apache AllowOverride All"),
                (r'cors.*allow.*\*', "élevée", "CORS trop permissif"),
                (r'X-Frame-Options.*ALLOW', "moyenne", "X-Frame-Options permissif"),
                (r'verify\s*=\s*False', "élevée", "SSL verify désactivé"),
            ],
            
            # === 9. CRYPTOGRAPHIE FAIBLE ===
            "crypto_faible": [
                (r'md5\(', "élevée", "MD5 obsolète"),
                (r'sha1\(', "élevée", "SHA1 obsolète"),
                (r'hashlib\.md5', "élevée", "hashlib MD5"),
                (r'hashlib\.sha1', "élevée", "hashlib SHA1"),
                (r'DES\.', "critique", "DES obsolète"),
                (r'RC4\.', "critique", "RC4 vulnérable"),
                (r'ECB', "élevée", "Mode ECB non sécurisé"),
                (r'random\.random\(', "moyenne", "random non cryptographique"),
            ],
            
            # === 10. INJECTION DE FICHIER (PATH TRAVERSAL) ===
            "injection_fichier": [
                (r'open\(.*\+', "élevée", "Ouverture fichier avec concaténation"),
                (r'include\(.*\$', "critique", "PHP include non sécurisé"),
                (r'require\(.*\$', "critique", "PHP require non sécurisé"),
                (r'\.\./', "élevée", "Path traversal détecté"),
                (r'file_get_contents\(.*\$', "élevée", "Lecture fichier non sécurisée"),
                (r'readFile\(.*\+', "élevée", "Node.js readFile non sécurisé"),
            ],
            
            # === 11. AUTHENTIFICATION FAIBLE ===
            "auth_faible": [
                (r'password\s*==\s*["\']', "critique", "Comparaison mot de passe en dur"),
                (r'if.*==.*admin', "critique", "Vérification admin simpliste"),
                (r'session\.timeout\s*=\s*[0-9]{6,}', "faible", "Session timeout trop long"),
                (r'remember_me.*permanent', "moyenne", "Remember me permanent"),
                (r'auth.*Basic', "moyenne", "Basic Auth non sécurisé"),
            ],
            
            # === 12. CSRF (Cross-Site Request Forgery) ===
            "csrf": [
                (r'<form.*method=["\']post["\'](?!.*csrf)', "moyenne", "Formulaire sans token CSRF"),
                (r'@app\.route.*methods=\[["\']POST', "moyenne", "Route POST sans protection CSRF"),
                (r'\.post\(.*headers\s*:', "faible", "POST sans vérification CSRF"),
            ],
            
            # === 13. INJECTION XML (XXE) ===
            "injection_xml": [
                (r'etree\.parse\(', "élevée", "XML parsing non sécurisé"),
                (r'parseString\(', "élevée", "XML parseString dangereux"),
                (r'DocumentBuilder(?!.*setFeature)', "élevée", "DocumentBuilder sans features"),
                (r'XMLReader(?!.*setFeature)', "élevée", "XMLReader non sécurisé"),
            ],
            
            # === 14. DÉSÉRIALISATION NON SÉCURISÉE ===
            "deserialisation": [
                (r'pickle\.loads\(', "critique", "pickle.loads dangereux"),
                (r'yaml\.load\((?!.*Loader=)', "critique", "yaml.load non sécurisé"),
                (r'unserialize\(', "critique", "PHP unserialize dangereux"),
                (r'JSON\.parse\(.*eval', "critique", "JSON.parse avec eval"),
            ],
            
            # === 15. INJECTION LDAP ===
            "injection_ldap": [
                (r'ldap\.search\(.*\+', "élevée", "LDAP injection"),
                (r'DirectorySearcher.*Filter.*\+', "élevée", "LDAP filter injection"),
            ],
            
            # === 16. INJECTION NOSQL ===
            "injection_nosql": [
                (r'collection\.find\(\{.*\$', "élevée", "NoSQL injection MongoDB"),
                (r'where\(.*\+', "élevée", "NoSQL where injection"),
                (r'\$regex.*user', "moyenne", "NoSQL regex injection"),
            ],
            
            # === 17. REDIRECTION NON VALIDÉE ===
            "redirection": [
                (r'redirect\(.*request\.', "moyenne", "Redirection non validée"),
                (r'location\.href\s*=\s*.*\+', "moyenne", "Redirection JavaScript non validée"),
                (r'header\(["\']Location:.*\$', "moyenne", "Redirection PHP non validée"),
            ],
            
            # === 18. EXPOSITION D'INFORMATIONS ===
            "exposition_info": [
                (r'print\(.*password', "faible", "Mot de passe affiché"),
                (r'console\.log\(.*token', "faible", "Token loggé"),
                (r'phpinfo\(\)', "élevée", "phpinfo() exposé"),
                (r'\.stack', "faible", "Stack trace exposée"),
            ],
            
            # === 19. RACE CONDITION ===
            "race_condition": [
                (r'open\(.*["\']w["\'].*\).*if\s+os\.path\.exists', "moyenne", "TOCTOU race condition"),
                (r'mkdir\(.*if\s+not\s+os\.path\.exists', "moyenne", "Race condition mkdir"),
            ],
            
            # === 20. INJECTION TEMPLATE ===
            "injection_template": [
                (r'render_template_string\(.*\+', "critique", "Template injection Flask"),
                (r'Template\(.*\+', "critique", "Template injection"),
                (r'\{\{.*request\.', "élevée", "Template injection Jinja2"),
            ],
            
            # === 21. LOGICIELS OBSOLÈTES ===
            "obsolete": [
                (r'jquery-1\.', "faible", "jQuery 1.x obsolète"),
                (r'angular\.js', "faible", "AngularJS obsolète"),
                (r'python2', "moyenne", "Python 2 obsolète"),
                (r'<\?php.*mysql_', "élevée", "mysql_* obsolète"),
            ],
            
            # === 22. INJECTION EMAIL ===
            "injection_email": [
                (r'mail\(.*\$_GET', "élevée", "Email injection PHP"),
                (r'sendmail\(.*\+', "élevée", "Sendmail injection"),
            ],
            
            # === 23. MASS ASSIGNMENT ===
            "mass_assignment": [
                (r'Model\.objects\.create\(\*\*request\.', "moyenne", "Mass assignment Django"),
                (r'\.update\(request\.', "moyenne", "Mass assignment update"),
            ],
            
            # === 24. INSECURE RANDOMNESS ===
            "random_faible": [
                (r'random\.randint', "faible", "random non cryptographique"),
                (r'Math\.random\(\)', "faible", "Math.random non cryptographique"),
                (r'rand\(\)', "faible", "rand() PHP non sécurisé"),
            ],
            
            # === 25. TIMING ATTACK ===
            "timing_attack": [
                (r'==.*password', "moyenne", "Comparaison vulnérable timing attack"),
                (r'\.equals\(.*password', "moyenne", "String equals timing attack"),
            ],
        }
    
    def scanner_fichier(self, chemin_fichier: str) -> List[Vulnérabilité]:
        """Scanne un fichier pour toutes les vulnérabilités"""
        vulnérabilités = []
        
        try:
            with open(chemin_fichier, 'r', encoding='utf-8', errors='ignore') as f:
                lignes = f.readlines()
            
            extension = Path(chemin_fichier).suffix.lower()
            
            for numéro, ligne in enumerate(lignes, 1):
                ligne_propre = ligne.strip()
                
                if not ligne_propre or self._est_commentaire(ligne_propre, extension):
                    continue
                
                for catégorie, patterns in self.patterns.items():
                    for pattern, gravité, description in patterns:
                        if re.search(pattern, ligne, re.IGNORECASE):
                            vuln = Vulnérabilité(
                                type=self._get_type_français(catégorie),
                                gravité=gravité,
                                fichier=chemin_fichier,
                                ligne=numéro,
                                description=description,
                                code_vulnérable=ligne.rstrip(),
                                recommandation=self._get_recommandation(catégorie),
                                cwe_id=self._get_cwe_id(catégorie),
                                catégorie_owasp=self._get_owasp(catégorie)
                            )
                            vulnérabilités.append(vuln)
                            break
            
            return vulnérabilités
            
        except Exception as e:
            print(f"Erreur scan {chemin_fichier}: {e}")
            return []
    
    def _est_commentaire(self, ligne: str, extension: str) -> bool:
        """Vérifie si la ligne est un commentaire"""
        if extension == '.py':
            return ligne.startswith('#')
        elif extension in ['.js', '.ts', '.java', '.cpp', '.cs', '.go']:
            return ligne.startswith('//') or ligne.startswith('/*')
        elif extension == '.php':
            return ligne.startswith('//') or ligne.startswith('#') or ligne.startswith('/*')
        elif extension == '.rb':
            return ligne.startswith('#')
        elif extension in ['.yml', '.yaml']:
            return ligne.startswith('#')
        return False
    
    def _get_type_français(self, catégorie: str) -> str:
        """Retourne le type en français"""
        types = {
            "secret_en_dur": "Secret en Dur",
            "injection_sql": "Injection SQL",
            "injection_commande": "Injection de Commande",
            "xss": "Cross-Site Scripting (XSS)",
            "injection_code": "Injection de Code",
            "dépassement_tampon": "Dépassement de Tampon",
            "gestion_erreurs": "Mauvaise Gestion des Erreurs",
            "config_faible": "Configuration Faible",
            "crypto_faible": "Cryptographie Faible",
            "injection_fichier": "Injection de Fichier (Path Traversal)",
            "auth_faible": "Authentification Faible",
            "csrf": "Cross-Site Request Forgery (CSRF)",
            "injection_xml": "Injection XML (XXE)",
            "deserialisation": "Désérialisation Non Sécurisée",
            "injection_ldap": "Injection LDAP",
            "injection_nosql": "Injection NoSQL",
            "redirection": "Redirection Non Validée",
            "exposition_info": "Exposition d'Informations Sensibles",
            "race_condition": "Race Condition",
            "injection_template": "Injection de Template",
            "obsolete": "Logiciel Obsolète",
            "injection_email": "Injection Email",
            "mass_assignment": "Mass Assignment",
            "random_faible": "Génération Aléatoire Non Sécurisée",
            "timing_attack": "Vulnérable aux Timing Attacks"
        }
        return types.get(catégorie, "Vulnérabilité Générique")
    
    def _get_recommandation(self, catégorie: str) -> str:
        """Retourne la recommandation"""
        recommandations = {
            "secret_en_dur": "Utilisez des variables d'environnement (os.getenv)",
            "injection_sql": "Utilisez des requêtes préparées avec paramètres (?)",
            "injection_commande": "Évitez shell=True, utilisez des listes",
            "xss": "Utilisez textContent ou échappez le HTML",
            "injection_code": "N'utilisez jamais eval/exec avec input utilisateur",
            "dépassement_tampon": "Utilisez strncpy/snprintf avec limites",
            "gestion_erreurs": "Gérez spécifiquement chaque exception",
            "config_faible": "Désactivez DEBUG en production",
            "crypto_faible": "Utilisez SHA-256, AES-256-GCM, bcrypt",
            "injection_fichier": "Validez et sanitisez les chemins de fichiers",
            "auth_faible": "Utilisez des sessions sécurisées",
            "csrf": "Ajoutez des tokens CSRF",
            "injection_xml": "Désactivez les entités externes",
            "deserialisation": "Validez avant de désérialiser",
            "injection_ldap": "Échappez les caractères spéciaux LDAP",
            "injection_nosql": "Validez et typez les entrées",
            "redirection": "Validez les URLs de redirection",
            "exposition_info": "Ne loggez pas d'informations sensibles",
            "race_condition": "Utilisez des verrous/locks",
            "injection_template": "N'utilisez pas render_template_string",
            "obsolete": "Mettez à jour vers une version récente",
            "injection_email": "Validez les adresses email",
            "mass_assignment": "Utilisez des whitelists de champs",
            "random_faible": "Utilisez secrets.SystemRandom()",
            "timing_attack": "Utilisez hmac.compare_digest()"
        }
        return recommandations.get(catégorie, "Corrigez cette vulnérabilité")
    
    def _get_cwe_id(self, catégorie: str) -> str:
        """Retourne l'ID CWE"""
        cwes = {
            "secret_en_dur": "CWE-798",
            "injection_sql": "CWE-89",
            "injection_commande": "CWE-78",
            "xss": "CWE-79",
            "injection_code": "CWE-94",
            "dépassement_tampon": "CWE-120",
            "gestion_erreurs": "CWE-209",
            "config_faible": "CWE-16",
            "crypto_faible": "CWE-327",
            "injection_fichier": "CWE-22",
            "auth_faible": "CWE-287",
            "csrf": "CWE-352",
            "injection_xml": "CWE-611",
            "deserialisation": "CWE-502",
            "injection_ldap": "CWE-90",
            "injection_nosql": "CWE-943",
            "redirection": "CWE-601",
            "exposition_info": "CWE-200",
            "race_condition": "CWE-362",
            "injection_template": "CWE-1336",
            "obsolete": "CWE-1104",
            "injection_email": "CWE-94",
            "mass_assignment": "CWE-915",
            "random_faible": "CWE-330",
            "timing_attack": "CWE-208"
        }
        return cwes.get(catégorie, "CWE-Unknown")
    
    def _get_owasp(self, catégorie: str) -> str:
        """Retourne la catégorie OWASP Top 10 2021"""
        owasp = {
            "secret_en_dur": "A02:2021 - Cryptographic Failures",
            "injection_sql": "A03:2021 - Injection",
            "injection_commande": "A03:2021 - Injection",
            "xss": "A03:2021 - Injection",
            "injection_code": "A03:2021 - Injection",
            "dépassement_tampon": "A04:2021 - Insecure Design",
            "gestion_erreurs": "A09:2021 - Security Logging Failures",
            "config_faible": "A05:2021 - Security Misconfiguration",
            "crypto_faible": "A02:2021 - Cryptographic Failures",
            "injection_fichier": "A03:2021 - Injection",
            "auth_faible": "A07:2021 - Authentication Failures",
            "csrf": "A01:2021 - Broken Access Control",
            "injection_xml": "A03:2021 - Injection",
            "deserialisation": "A08:2021 - Software Integrity Failures",
            "injection_ldap": "A03:2021 - Injection",
            "injection_nosql": "A03:2021 - Injection",
            "redirection": "A01:2021 - Broken Access Control",
            "exposition_info": "A09:2021 - Security Logging Failures",
            "race_condition": "A04:2021 - Insecure Design",
            "injection_template": "A03:2021 - Injection",
            "obsolete": "A06:2021 - Vulnerable Components",
            "injection_email": "A03:2021 - Injection",
            "mass_assignment": "A01:2021 - Broken Access Control",
            "random_faible": "A02:2021 - Cryptographic Failures",
            "timing_attack": "A04:2021 - Insecure Design"
        }
        return owasp.get(catégorie, "OWASP Unknown")