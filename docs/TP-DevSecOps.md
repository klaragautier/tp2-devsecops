# TP DevSecOps - Projet "BookStore Secure"

**Membres du groupe :** Gautier Klara, Eloire Elodie
**Lien du dépôt :** https://github.com/HelloDitE/ecommerce-devsecops.git

---

## 1. Architecture Applicative

### Description Générale
L'application est une plateforme e-commerce de vente de livres. Elle repose sur une architecture **microservices** où chaque fonctionnalité métier est isolée.
Le service Catalog (Flask) agit comme point d'entrée principal.

### Microservices et Rôles
Le système complet est conçu autour de 3 services. Pour ce rendu, le développement actif est sur le Catalogue (Python).

1.  **Catalog Service (Interne : 5000) :**
    * **Rôle :** Point d'entrée de l'application et gestion de l'inventaire des livres.
    * **Techno :** **Python / Flask** (Choisi pour la démonstration des vulnérabilités SAST/DAST).
    * **Fonction Gateway :** Il expose directement les API REST aux clients et intègre la logique métier.
    * **Base de données :** SQLite (embarquée pour le prototypage).
2.  **Auth Service & Order Service (Architecture Cible) :**
    * **Rôle :** Services tiers (Authentification et Commandes).
    * **Techno :** Flask

### Points d'entrée exposés (Surface d'attaque)
Le service Flask est exposé directement sur le port 5000.

| Route Publique | Méthode | Description | Auth Requise ? | Risque Identifié |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | GET | Vérification de l'état du service (Healthcheck) | Non | Faible |
| `/search?q=...` | GET | Recherche de livres | Non | **Critique** (Injection SQL possible) |
| `/debug/run` | GET | Interface admin de debug | Non | **Critique** (RCE - Command Injection) |
| `/discount` | POST | Calcul de réduction | Non | Moyen (Bug logique / Déni de service) |

### Flux de Données Sensibles
* **Secrets d'API :** Tokens et clés (SECRET_KEY) présents en dur dans le code Flask.
* **Commandes Système :** Exécution arbitraire possible via la route /debug/run exposée publiquement par le service Flask.

### Dépendances Critiques
L'analyse des risques (SCA - Software Composition Analysis) se porte sur ces composants :

* **Image Docker de base :** `python:3.11-slim` (Version Debian allégée).
* **Bibliothèques Python (requirements.txt) :**
    * `flask` (Framework Web)
    * `requests` (Appels HTTP)
* **Infrastructure :** Docker Compose pour l'orchestration locale et Staging.

---

## 2. Description détaillée du pipeline CI/CD

Le pipeline est orchestré via **GitHub Actions** et se déclenche à chaque push. Il est conçu pour bloquer le déploiement si une faille de sécurité critique est détectée.

### Les Étapes (Jobs)
1.  **Tests Unitaires (`unit-tests`) :**
    * Installation des dépendances Python.
    * Exécution de `pytest` pour vérifier la logique métier (ex: calcul des réductions).
    * *Gate Quality :* Le pipeline s'arrête si le code plante.

2.  **Sécurité Statique (`security-static`) :**
    * **Gitleaks :** Scanne l'historique git pour trouver des secrets (mots de passe, clés API) committés par erreur.
    * **Semgrep (SAST) :** Analyse le code source Python pour détecter des patterns dangereux (Injections SQL, RCE, Shell=True).
    * *Gate Security :* Bloque le pipeline immédiatement si une faille est trouvée.

3.  **Build & Container Scan (`deploy-staging-and-scan`) :**
    * Construction de l'image Docker `catalog-service`.
    * **Trivy (SCA) :** Scanne l'image Docker pour trouver des vulnérabilités connues dans l'OS (Debian/Alpine) et les paquets système.
    * *Gate Security :* Bloque si une vulnérabilité "CRITICAL" ou "HIGH" est détectée.

4.  **Staging & DAST :**
    * Déploiement de l'environnement de staging via `docker compose`.
    * Exécution des scripts de supervision (`smoke.sh`).
    * **OWASP ZAP (DAST) :** Attaque l'application en cours d'exécution pour détecter des failles Web (Headers manquants, XSS...).

---

## 3. Preuve d'efficacité (Vuln-Demo)

Pour démontrer l'efficacité des gates de sécurité, nous maintenons deux branches :

| Branche | État du Code | Résultat Pipeline | Explication |
| :--- | :--- | :--- | :--- |
| **`vuln-demo`** | Contient des failles (Secret en dur, SQLi, RCE) | 🔴 **ÉCHEC** | Bloqué par Semgrep (RCE/SQLi) et Gitleaks (Secrets). Le code n'est pas déployé. |
| **`main`** | Code corrigé et sécurisé | 🟢 **SUCCÈS** | Toutes les failles sont corrigées. Le code passe en staging et les tests ZAP sont exécutés. |


---

## 4. Analyse des risques (Mapping & Contrôles)

Cette section identifie les menaces spécifiques pesant sur notre architecture microservices de librairie en ligne et définit les barrières automatisées (Gates) mises en place pour les contrer.

### Tableau 1 : Mapping des Risques et Contrôles Automatisés

| Risque | Exemple Concret dans le projet BookStore | Impact | Probabilité | Contrôle Automatisé (Outil) | Gate (Seuil de blocage) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Injection SQL** | L'endpoint `/search` concatène directement le paramètre `q` dans la requête SQL sans nettoyage. | **Critique** : Exfiltration de la base de données (clients, stocks, prix). | **Forte** (Code legacy fréquent) | **SAST** (Semgrep) | 🔴 Bloque si `findings > 0` |
| **Injection de Commande (RCE)** | L'endpoint `/debug/run` utilise `subprocess` avec `shell=True`, permettant d'exécuter des commandes système sur le conteneur. | **Critique** : Prise de contrôle totale du serveur et accès au réseau Docker interne. | **Moyenne** (Oubli de route de debug) | **SAST** (Semgrep) | 🔴 Bloque si `findings > 0` |
| **Secrets Committés** | Présence de `SECRET_KEY` ou de tokens API en dur dans le fichier `app.py`. | **Élevée** : Usurpation de session admin ou accès aux services tiers. | **Forte** (Erreur humaine fréquente) | **Secret Scanning** (Gitleaks) | 🔴 Bloque immédiatement |
| **Bug Logique Métier** | L'endpoint `/discount` ne valide pas les pourcentages (ex: réduction > 100% ou négative) ou plante sur des variables non définies. | **Moyenne** : Perte financière (livres gratuits) ou crash du service (Déni de service). | **Moyenne** | **Tests Unitaires** (Pytest) | 🔴 Bloque si échec du test |
| **Vulnérabilité Dépendance** | Utilisation d'une version obsolète de `Flask` ou `Requests` contenant des CVE connues. | **Moyenne/Élevée** : Risque d'exploitation publique si la faille est connue. | **Moyenne** | **SCA** (Trivy fs) | 🔴 Bloque si `CRITICAL` ou `HIGH` |
| **Vulnérabilité Image Docker** | L'image de base `python:3.11-slim` peut contenir des failles système (paquets OS Debian). | **Moyenne** : Possibilité d'escalade de privilèges dans le conteneur. | **Moyenne** | **Container Scan** (Trivy image) | 🔴 Bloque si `CRITICAL` |
| **Mauvaise Config Web** | Absence de headers de sécurité (HSTS, XSS-Protection) sur le serveur Flask exposé directement. | **Faible** : Attaques client-side (XSS, Clickjacking). | **Forte** (Config par défaut) | **DAST** (OWASP ZAP) | 🟠 Avertissement (Warn) |

### Tableau 2 : Limites de l'automatisation et Mesures Compensatoires

L'automatisation ne couvre pas 100% des risques. Voici les limites identifiées pour notre projet et comment nous les gérons par des processus humains.

| Risque | Limite de l'outil (Point aveugle) | Mesure Compensatoire (Humain/Process) |
| :--- | :--- | :--- |
| **Logique Métier Complexe** | Les scanners (SAST/DAST) ne savent pas qu'une réduction de 200% sur un livre est "anormale". Ils cherchent des failles techniques, pas métier. | **Revue de code (Code Review)** systématique et écriture de scénarios de tests fonctionnels par les développeurs. |
| **Faux Négatifs SAST** | Semgrep peut rater une injection SQL si la requête est construite de manière très complexe ou obscurcie. | **Pentest manuel** périodique et formation continue de l'équipe aux pratiques de codage sécurisé (Secure Coding). |
| **Secrets Obfusqués** | Gitleaks ne détecte pas un secret s'il est découpé en plusieurs variables ou encodé (ex: base64) pour le cacher. | **Rotation régulière des clés** et interdiction stricte de committer des fichiers de configuration locale (`.env`). |
| **Couverture du DAST (ZAP)** | Le scanner dynamique (ZAP) ne teste que les liens qu'il trouve. Si la route `/debug/run` n'est référencée nulle part dans le HTML, il ne la testera pas. | Fournir une **spécification OpenAPI (Swagger)** au scanner ou maintenir une liste exhaustive des routes à tester dans le script de supervision. |

---


## 5. Configuration Technique des Gates (Barrières)

Pour respecter la consigne d'automatisation, nous avons configuré nos scanners dans GitHub Actions pour qu'ils agissent comme des barrières (**Gates**).

Nous avons défini deux comportements :
* **Bloquant (🔴) :** Si une faille critique est trouvée, le pipeline s'arrête (Exit Code 1) et empêche la suite.
* **Informatif (🟠) :** Le scanner signale des alertes mais laisse passer le pipeline (pour éviter de bloquer sur des faux positifs).

Voici le résumé de notre configuration :

| Outil | Type | Configuration de la Gate | Preuve (Artefact généré) |
| :--- | :--- | :--- | :--- |
| **Gitleaks** | Secret Scanning | **Bloquant 🔴** <br> Analyse chaque commit. S'arrête net si un mot de passe ou une clé API est détecté. | Logs de la console GitHub (onglet Actions). |
| **Semgrep** | SAST (Code) | **Bloquant 🔴** <br> Analyse le code Python. Nous avons dû ignorer l'alerte sur l'écoute `0.0.0.0` (nécessaire pour Docker) via le commentaire `# nosemgrep`. | `semgrep.json` |
| **Trivy** | Conteneur | **Bloquant 🔴** <br> Scanne l'image Docker finale. Configure pour bloquer uniquement sur les failles `CRITICAL` afin de ne pas être bloqué par des mises à jour mineures de l'OS. | `trivy-report.json` |
| **OWASP ZAP** | DAST (Web) | **Informatif 🟠** <br> Scanne le site en fonctionnement (Staging). Configuré en mode "Baseline" pour générer un rapport sans casser le pipeline, car cet outil génère souvent des fausses alertes. | `zap-scan-report` (HTML) |

---

## 6. Guide de déploiement et supervision

L'objectif est que n'importe qui puisse lancer le projet sans connaître le code. Tout est conteneurisé avec Docker.

### Pré-requis
* Avoir `git` installé.
* Avoir `Docker Desktop` installé et lancé.

### Procédure de lancement (Local)
1.  **Récupérer le projet :**
    ```bash
    git clone [https://github.com/HelloDitE/ecommerce-devsecops.git](https://github.com/HelloDitE/ecommerce-devsecops.git)
    cd ecommerce-devsecops
    ```

2.  **Lancer l'environnement complet :**
    Nous utilisons un fichier Compose qui lance les 3 services (Catalog, Auth, Order) et le Frontend.
    ```bash
    docker compose -f compose.staging.yml up --build -d
    ```

3.  **Accéder à l'application :**
    Ouvrez votre navigateur sur : [http://localhost:5000](http://localhost:5000)

### Supervision
Pour vérifier que l'application est en bonne santé une fois lancée, nous utilisons des scripts de "Smoke Test" (Tests de fumée) :

* **Vérification automatique :** Le script `monitoring/supervision.sh` interroge les endpoints `/health` de nos services.
    ```bash
    bash monitoring/supervision.sh
    ```
* **Résultat attendu :** Le script doit afficher "OK" pour chaque service. Si un service est KO, le code de retour HTTP sera différent de 200.

---

## 7. Retour d'expérience (REX)

Ce projet nous a permis de mettre en pratique l'approche **DevSecOps** : intégrer la sécurité dès le développement plutôt que d'attendre la fin du projet.

### Ce qui a bien fonctionné
* **L'automatisation :** C'est très satisfaisant de voir GitHub Actions lancer tout seul les tests, la construction de l'image Docker et les scans de sécurité à chaque `git push`.
* **La détection précoce :** Les outils comme **Semgrep** et **Gitleaks** sont très efficaces. Ils nous ont permis de voir immédiatement nos erreurs (injections SQL, secrets oubliés) avant même de déployer.
* **La portabilité :** Grâce à Docker, le projet tourne exactement de la même façon sur nos machines et sur le serveur d'intégration continue (CI).

### Les difficultés rencontrées
* **La syntaxe YAML :** Configurer le pipeline `.github/workflows/ci.yml` a été l'étape la plus chronophage. La moindre erreur d'indentation (espace en trop) faisait échouer le pipeline, ce qui a demandé beaucoup d'essais/erreurs.
* **La gestion des Faux Positifs :** Les scanners de sécurité sont parfois trop stricts. Par exemple, Semgrep refusait que notre application écoute sur toutes les interfaces (`0.0.0.0`), ce qui est pourtant obligatoire dans un conteneur Docker. Nous avons appris à gérer ces exceptions proprement.
* **Comprendre les outils :** Au début, la différence entre l'analyse statique (SAST) et dynamique (DAST) n'était pas claire, mais la mise en place de Semgrep (sur le code) et ZAP (sur le site lancé) a concrétisé ces notions.

### Améliorations possibles
Si nous avions plus de temps, nous pourrions :
* [cite_start]Ajouter des **notifications automatiques** (sur Slack ou Teams) quand le pipeline échoue[cite: 229].
* [cite_start]Mettre en place la **signature des images Docker** (avec Cosign) pour garantir que personne ne modifie notre code entre le build et la production[cite: 227].
* Passer les échanges en **HTTPS** (actuellement en HTTP) pour sécuriser les données des clients.