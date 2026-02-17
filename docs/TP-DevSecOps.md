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
    * **Techno :** Node.js

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