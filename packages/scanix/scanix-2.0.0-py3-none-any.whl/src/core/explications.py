"""
Explications détaillées pour toutes les vulnérabilités
Version professionnelle avec exemples concrets
"""

class ExplicationsVulnérabilités:
    """Explications claires et détaillées pour chaque vulnérabilité"""
    
    EXPLICATIONS = {
        "Secret en Dur": {
            "description": "Mot de passe, clé API, token ou secret écrit directement dans le code source.",
            "danger": "Le code est souvent versionné sur Git/GitHub, exposant tous les secrets à quiconque a accès au dépôt. Un attaquant peut utiliser ces credentials pour accéder aux systèmes.",
            "solution": "Stockez les secrets dans des variables d'environnement ou utilisez un gestionnaire de secrets (AWS Secrets Manager, HashiCorp Vault).",
            "exemple": {
                "vulnérable": "password = 'MonMotDePasse123!'\napi_key = 'sk_live_abc123xyz789'",
                "sécurisé": "import os\npassword = os.getenv('DB_PASSWORD')\napi_key = os.getenv('API_KEY')"
            },
            "cwe": "CWE-798"
        },
        
        "Injection SQL": {
            "description": "Entrée utilisateur concaténée ou insérée directement dans une requête SQL.",
            "danger": "Un attaquant peut modifier la requête SQL pour voler toutes les données, supprimer des tables, ou prendre le contrôle de la base de données.",
            "solution": "Utilisez toujours des requêtes préparées (prepared statements) avec des paramètres liés.",
            "exemple": {
                "vulnérable": "query = f\"SELECT * FROM users WHERE id = {user_id}\"\ncursor.execute(query)",
                "sécurisé": "query = \"SELECT * FROM users WHERE id = ?\"\ncursor.execute(query, (user_id,))"
            },
            "cwe": "CWE-89"
        },
        
        "Injection de Commande": {
            "description": "Entrée utilisateur utilisée pour construire une commande système.",
            "danger": "Permet d'exécuter des commandes arbitraires sur le serveur : vol de fichiers, installation de malware, destruction du système.",
            "solution": "N'utilisez jamais os.system() ou shell=True avec des entrées utilisateur. Utilisez des listes d'arguments.",
            "exemple": {
                "vulnérable": "os.system('rm ' + filename)\nsubprocess.run(f'ping {host}', shell=True)",
                "sécurisé": "subprocess.run(['rm', filename])\nsubprocess.run(['ping', '-c', '4', host])"
            },
            "cwe": "CWE-78"
        },
        
        "Cross-Site Scripting (XSS)": {
            "description": "HTML non échappé contenant des données utilisateur, permettant l'injection de JavaScript.",
            "danger": "Un attaquant peut voler les cookies de session, rediriger vers des sites malveillants, ou modifier le contenu de la page.",
            "solution": "Utilisez textContent au lieu de innerHTML, ou échappez le HTML avec une bibliothèque.",
            "exemple": {
                "vulnérable": "element.innerHTML = userInput\ndocument.write('<div>' + data + '</div>')",
                "sécurisé": "element.textContent = userInput\nconst div = document.createElement('div')\ndiv.textContent = data"
            },
            "cwe": "CWE-79"
        },
        
        "Injection de Code": {
            "description": "Utilisation de eval() ou exec() avec des données contrôlées par l'utilisateur.",
            "danger": "Permet l'exécution de code Python/JavaScript arbitraire dans l'application, donnant un contrôle total à l'attaquant.",
            "solution": "N'utilisez jamais eval() ou exec(). Pour parser du JSON, utilisez json.loads(). Pour évaluer des expressions mathématiques, utilisez ast.literal_eval().",
            "exemple": {
                "vulnérable": "eval(user_input)\nexec('result = ' + formula)",
                "sécurisé": "import ast\nresult = ast.literal_eval(user_input)  # Seulement littéraux\nimport json\ndata = json.loads(user_json)"
            },
            "cwe": "CWE-94"
        },
        
        "Dépassement de Tampon": {
            "description": "Écriture mémoire au-delà des limites d'un buffer alloué (principalement en C/C++).",
            "danger": "Peut causer des crashs, corruption de données, ou permettre l'exécution de code arbitraire (RCE).",
            "solution": "Utilisez des fonctions sécurisées avec limites : strncpy, snprintf, strlcpy.",
            "exemple": {
                "vulnérable": "char buffer[10];\nstrcpy(buffer, user_input);  // Pas de vérification",
                "sécurisé": "char buffer[10];\nstrncpy(buffer, user_input, sizeof(buffer) - 1);\nbuffer[sizeof(buffer) - 1] = '\\0';"
            },
            "cwe": "CWE-120"
        },
        
        "Mauvaise Gestion des Erreurs": {
            "description": "Exceptions non gérées ou messages d'erreur exposant des informations sensibles.",
            "danger": "Fuite d'informations sur la structure du code, les chemins de fichiers, les versions logicielles, facilitant les attaques.",
            "solution": "Gérez spécifiquement chaque exception et ne montrez jamais les détails aux utilisateurs.",
            "exemple": {
                "vulnérable": "try:\n    db.query(sql)\nexcept:\n    pass\n\nprint(f'Erreur: {e}')",
                "sécurisé": "import logging\ntry:\n    db.query(sql)\nexcept DatabaseError as e:\n    logging.error(f'Query failed: {e}')\n    return 'Une erreur est survenue'"
            },
            "cwe": "CWE-209"
        },
        
        "Configuration Faible": {
            "description": "Paramètres de développement ou configurations dangereuses activées en production.",
            "danger": "Exposition de debug traces, chemins de fichiers, informations système, facilitant les reconnaissances.",
            "solution": "Désactivez DEBUG, display_errors et tous les modes développement en production.",
            "exemple": {
                "vulnérable": "DEBUG = True\ndisplay_errors = On\nAllowOverride All",
                "sécurisé": "DEBUG = False\ndisplay_errors = Off\nAllowOverride None"
            },
            "cwe": "CWE-16"
        },
        
        "Cryptographie Faible": {
            "description": "Utilisation d'algorithmes de chiffrement ou de hachage obsolètes et cassables.",
            "danger": "MD5 et SHA1 sont vulnérables aux collisions. DES et RC4 peuvent être cassés rapidement. Les données peuvent être déchiffrées.",
            "solution": "Utilisez SHA-256 minimum pour hachage, bcrypt/Argon2 pour mots de passe, AES-256-GCM pour chiffrement.",
            "exemple": {
                "vulnérable": "import hashlib\nhash = hashlib.md5(password.encode()).hexdigest()",
                "sécurisé": "import bcrypt\nhash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())\n# Vérification\nbcrypt.checkpw(password.encode(), hash)"
            },
            "cwe": "CWE-327"
        },
        
        "Injection de Fichier (Path Traversal)": {
            "description": "Chemin de fichier contrôlé par l'utilisateur sans validation, permettant l'accès à des fichiers arbitraires.",
            "danger": "Un attaquant peut lire /etc/passwd, ~/.ssh/id_rsa, ou d'autres fichiers sensibles avec des chemins comme '../../../etc/passwd'.",
            "solution": "Validez les chemins, utilisez des whitelists, et n'autorisez pas '../' dans les chemins.",
            "exemple": {
                "vulnérable": "filename = request.GET['file']\nwith open(filename) as f:\n    content = f.read()",
                "sécurisé": "from pathlib import Path\nfilename = request.GET['file']\nbase = Path('/safe/directory')\nfull_path = (base / filename).resolve()\nif base in full_path.parents:\n    with open(full_path) as f:\n        content = f.read()"
            },
            "cwe": "CWE-22"
        },
        
        "Authentification Faible": {
            "description": "Mécanismes d'authentification peu sécurisés ou mal implémentés.",
            "danger": "Contournement de l'authentification, accès non autorisé aux comptes utilisateurs.",
            "solution": "Utilisez des frameworks d'authentification éprouvés, des sessions sécurisées, et du rate limiting.",
            "exemple": {
                "vulnérable": "if password == 'admin123':\n    logged_in = True",
                "sécurisé": "from werkzeug.security import check_password_hash\nif check_password_hash(stored_hash, password):\n    session['user_id'] = user.id\n    session.permanent = False"
            },
            "cwe": "CWE-287"
        },
        
        "Cross-Site Request Forgery (CSRF)": {
            "description": "Absence de protection contre les requêtes forgées provenant d'autres sites.",
            "danger": "Un attaquant peut faire effectuer des actions à l'insu de l'utilisateur : transfert d'argent, changement de mot de passe, etc.",
            "solution": "Ajoutez des tokens CSRF uniques et non-prédictibles à tous les formulaires et requêtes modifiant des données.",
            "exemple": {
                "vulnérable": "<form method='POST' action='/transfer'>\n    <input name='amount' value='1000'>\n</form>",
                "sécurisé": "<form method='POST' action='/transfer'>\n    <input type='hidden' name='csrf_token' value='{{ csrf_token }}'>\n    <input name='amount' value='1000'>\n</form>"
            },
            "cwe": "CWE-352"
        },
        
        "Injection XML (XXE)": {
            "description": "Parser XML qui résout les entités externes, permettant la lecture de fichiers locaux.",
            "danger": "Lecture de fichiers système, SSRF (Server-Side Request Forgery), ou déni de service via billion laughs attack.",
            "solution": "Désactivez les entités externes dans le parser XML.",
            "exemple": {
                "vulnérable": "from xml.etree import ElementTree\ntree = ElementTree.parse(xml_file)",
                "sécurisé": "from defusedxml import ElementTree\ntree = ElementTree.parse(xml_file)"
            },
            "cwe": "CWE-611"
        },
        
        "Désérialisation Non Sécurisée": {
            "description": "Désérialisation de données non fiables sans validation.",
            "danger": "Exécution de code arbitraire via des objets malveillants désérialisés (gadget chains).",
            "solution": "N'utilisez jamais pickle avec des données non fiables. Préférez JSON.",
            "exemple": {
                "vulnérable": "import pickle\ndata = pickle.loads(user_data)",
                "sécurisé": "import json\ndata = json.loads(user_data)\n# Validation\nif not isinstance(data, dict):\n    raise ValueError('Invalid data')"
            },
            "cwe": "CWE-502"
        },
        
        "Injection LDAP": {
            "description": "Caractères spéciaux LDAP non échappés dans les requêtes d'annuaire.",
            "danger": "Contournement de l'authentification, accès à des informations non autorisées dans l'annuaire.",
            "solution": "Échappez tous les caractères spéciaux LDAP : * ( ) \\ NUL",
            "exemple": {
                "vulnérable": "filter = f'(uid={username})'\nldap.search(filter)",
                "sécurisé": "import ldap\ndef escape_ldap(s):\n    return s.replace('*', '\\\\2a').replace('(', '\\\\28').replace(')', '\\\\29')\nfilter = f'(uid={escape_ldap(username)})'"
            },
            "cwe": "CWE-90"
        },
        
        "Injection NoSQL": {
            "description": "Données non validées dans les requêtes NoSQL (MongoDB, etc.).",
            "danger": "Contournement de l'authentification, accès non autorisé aux données.",
            "solution": "Validez et typez toutes les entrées utilisateur avant les requêtes.",
            "exemple": {
                "vulnérable": "db.users.find({username: req.body.username})",
                "sécurisé": "const username = String(req.body.username)\nif (!/^[a-zA-Z0-9_]+$/.test(username)) {\n    throw new Error('Invalid username')\n}\ndb.users.find({username: username})"
            },
            "cwe": "CWE-943"
        },
        
        "Redirection Non Validée": {
            "description": "Redirection vers une URL contrôlée par l'utilisateur sans validation.",
            "danger": "Phishing : redirection vers des sites malveillants qui semblent légitimes.",
            "solution": "Validez les URLs de redirection avec une whitelist.",
            "exemple": {
                "vulnérable": "return redirect(request.GET['next'])",
                "sécurisé": "ALLOWED_REDIRECTS = ['/home', '/profile', '/dashboard']\nnext_url = request.GET['next']\nif next_url in ALLOWED_REDIRECTS:\n    return redirect(next_url)\nelse:\n    return redirect('/home')"
            },
            "cwe": "CWE-601"
        },
        
        "Exposition d'Informations Sensibles": {
            "description": "Informations sensibles (mots de passe, tokens) loguées ou affichées.",
            "danger": "Fuite d'informations dans les logs, accessible aux administrateurs ou en cas de compromission des logs.",
            "solution": "Ne jamais logger ou afficher de données sensibles.",
            "exemple": {
                "vulnérable": "print(f'Login avec password: {password}')\nconsole.log('Token:', api_token)",
                "sécurisé": "logger.info(f'Login attempt for user: {username}')\n# Ne jamais logger le password ou token"
            },
            "cwe": "CWE-200"
        },
        
        "Race Condition": {
            "description": "Vérification puis utilisation (TOCTOU - Time Of Check, Time Of Use) sans protection.",
            "danger": "Un attaquant peut exploiter la fenêtre temporelle entre la vérification et l'utilisation pour modifier des fichiers ou des états.",
            "solution": "Utilisez des opérations atomiques ou des verrous.",
            "exemple": {
                "vulnérable": "if not os.path.exists(file):\n    with open(file, 'w') as f:\n        f.write(data)",
                "sécurisé": "import fcntl\ntry:\n    fd = os.open(file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)\n    with os.fdopen(fd, 'w') as f:\n        f.write(data)\nexcept FileExistsError:\n    pass"
            },
            "cwe": "CWE-362"
        },
        
        "Injection de Template": {
            "description": "Données utilisateur dans un template rendering sans échappement.",
            "danger": "Exécution de code arbitraire côté serveur (SSTI - Server-Side Template Injection).",
            "solution": "N'utilisez jamais render_template_string avec des données utilisateur.",
            "exemple": {
                "vulnérable": "from flask import render_template_string\nhtml = render_template_string('<h1>Hello ' + name + '</h1>')",
                "sécurisé": "from flask import render_template\nhtml = render_template('hello.html', name=name)\n# Dans hello.html: <h1>Hello {{ name }}</h1>"
            },
            "cwe": "CWE-1336"
        },
        
        "Logiciel Obsolète": {
            "description": "Utilisation de bibliothèques ou frameworks avec des versions obsolètes.",
            "danger": "Vulnérabilités connues et publiquement documentées non corrigées.",
            "solution": "Maintenez toutes les dépendances à jour. Utilisez pip-audit, npm audit.",
            "exemple": {
                "vulnérable": "jquery-1.12.4.min.js  # Vulnérable à XSS\npython==2.7  # Fin de support",
                "sécurisé": "jquery-3.7.0.min.js\npython>=3.11\n# Vérification régulière\npip-audit"
            },
            "cwe": "CWE-1104"
        },
        
        "Injection Email": {
            "description": "En-têtes d'email non validés permettant l'injection de headers.",
            "danger": "Envoi de spam, phishing en utilisant votre serveur mail.",
            "solution": "Validez strictement tous les en-têtes d'email.",
            "exemple": {
                "vulnérable": "mail('user@example.com', $_GET['subject'], $message)",
                "sécurisé": "import re\nif not re.match(r'^[a-zA-Z0-9\\s]+$', subject):\n    raise ValueError('Invalid subject')\nmail.send(to='user@example.com', subject=subject)"
            },
            "cwe": "CWE-94"
        },
        
        "Mass Assignment": {
            "description": "Assignation automatique de tous les champs reçus dans une requête.",
            "danger": "Modification de champs non autorisés (is_admin, role, etc.).",
            "solution": "Utilisez des whitelists de champs autorisés.",
            "exemple": {
                "vulnérable": "user.update(**request.POST)  # Tous les champs",
                "sécurisé": "ALLOWED_FIELDS = ['name', 'email', 'phone']\ndata = {k: v for k, v in request.POST.items() if k in ALLOWED_FIELDS}\nuser.update(**data)"
            },
            "cwe": "CWE-915"
        },
        
        "Génération Aléatoire Non Sécurisée": {
            "description": "Utilisation de générateurs pseudo-aléatoires non cryptographiques pour la sécurité.",
            "danger": "Prédictibilité des tokens de session, tokens CSRF, ou clés de chiffrement.",
            "solution": "Utilisez des générateurs cryptographiquement sûrs.",
            "exemple": {
                "vulnérable": "import random\ntoken = random.randint(1000, 9999)",
                "sécurisé": "import secrets\ntoken = secrets.token_urlsafe(32)\n# Ou\nimport os\nrandom_bytes = os.urandom(32)"
            },
            "cwe": "CWE-330"
        },
        
        "Vulnérable aux Timing Attacks": {
            "description": "Comparaison de chaînes (mots de passe, tokens) vulnérable aux attaques temporelles.",
            "danger": "Un attaquant peut deviner un secret caractère par caractère en mesurant le temps de réponse.",
            "solution": "Utilisez des fonctions de comparaison à temps constant.",
            "exemple": {
                "vulnérable": "if user_token == stored_token:\n    return True",
                "sécurisé": "import hmac\nif hmac.compare_digest(user_token, stored_token):\n    return True"
            },
            "cwe": "CWE-208"
        }
    }
    
    @staticmethod
    def pour_type(type_vuln: str) -> dict:
        """Retourne l'explication pour un type de vulnérabilité"""
        return ExplicationsVulnérabilités.EXPLICATIONS.get(type_vuln, {
            "description": "Vulnérabilité de sécurité détectée.",
            "danger": "Cette vulnérabilité présente un risque pour votre application.",
            "solution": "Consultez la documentation de sécurité OWASP.",
            "exemple": {
                "vulnérable": "Code vulnérable",
                "sécurisé": "Code sécurisé"
            },
            "cwe": "CWE-unknown"
        })
    
    @staticmethod
    def formater_pour_affichage(vuln) -> str:
        """Format professionnel pour l'affichage dans l'interface"""
        exp = ExplicationsVulnérabilités.pour_type(vuln.type)
        
        # Icône selon gravité
        icônes = {
            "critique": "🔴",
            "élevée": "🟠",
            "moyenne": "🟡",
            "faible": "🟢"
        }
        icône = icônes.get(vuln.gravité, "⚪")
        
        return f"""
{icône} {vuln.type} ({vuln.gravité.upper()})
{'═' * 60}

📁 Fichier: {vuln.fichier}
📄 Ligne {vuln.ligne}: {vuln.code_vulnérable}

📝 Description:
{exp['description']}

⚠️ Danger:
{exp['danger']}

🔐 Solution Recommandée:
{exp['solution']}

💡 Exemple de Code:

❌ VULNÉRABLE:
{exp['exemple']['vulnérable']}

✅ SÉCURISÉ:
{exp['exemple']['sécurisé']}

📚 Références:
• CWE: {exp.get('cwe', 'N/A')}
• OWASP: {vuln.catégorie_owasp}
• Recommandation: {vuln.recommandation}
"""