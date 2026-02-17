# TP2 DevSecOps : Monitoring et Gate Runtime

## Partie A : Initialisation de l'environnement Staging

Nous avons mis en place un environnement minimaliste pour servir de base au monitoring.

### 1. Architecture
- **Service :** Catalog (Flask)
- **Port exposé :** 5001
- **Orchestration :** Docker Compose (`compose.staging.yml`)

### 2. Vérification du déploiement
Le service expose une route `/health` fonctionnelle.

**Preuve de fonctionnement :**
```bash
$ curl -i http://localhost:5001/health
HTTP/1.1 200 OK
...
{"status":"ok"}

(curl.exe -i http://localhost:5001/health sur windows)
```

## Partie B : Logs Structurés (JSON)

Pour permettre une analyse automatisée (Gate Runtime), nous avons remplacé les logs textuels par défaut de Flask par des logs structurés au format JSON.

### 1. Implémentation (`app.py`)
Nous avons utilisé les middlewares Flask `before_request` et `after_request` pour :
* **Générer un Request-ID :** Un UUID unique est attribué à chaque requête (ou récupéré via le header `X-Request-Id`) pour la traçabilité.
* **Mesurer la latence :** Calcul du temps d'exécution en millisecondes (`latency_ms`).
* **Formatter en JSON :** Chaque ligne de log contient désormais : `ts`, `level`, `service`, `request_id`, `method`, `path`, `status`, `latency_ms`.

### 2. Preuve de fonctionnement
Les logs du conteneur sont maintenant lisibles par une machine.

**Exemple de log capturé :**
```json
{
  "ts": "2026-02-10T10:00:00Z",
  "level": "INFO",
  "service": "catalog",
  "request_id": "a1b2c3d4-...",
  "method": "GET",
  "path": "/health",
  "status": 200,
  "latency_ms": 1,
  "query": ""
}
```


## Partie C : Générateur de Trafic

Pour alimenter les logs et tester nos détecteurs en conditions réelles, nous avons mis en place un générateur de trafic automatisé.

### 1. Script (`monitoring/traffic.sh`)
Ce script Bash permet de simuler deux types d'activité sur l'application :
* **Trafic Normal :** Une boucle de requêtes sur `/health` et `/search` pour simuler une utilisation légitime [cite: 318-321].
* **Trafic Suspect (Attaques) :** Activé via la variable d'environnement `SUSPECT_MODE=1`. Il envoie des requêtes malveillantes contenant des tentatives de **Path Traversal** (`../../etc/passwd`) et d'**Injection de Commande** (`cmd=id`) [cite: 324-328].

### 2. Validation
Nous avons validé que l'exécution du script génère bien des entrées correspondantes dans les logs JSON du conteneur.

**Commandes utilisées :**
```bash
# Trafic normal
bash monitoring/traffic.sh

# Trafic d'attaque
SUSPECT_MODE=1 bash monitoring/traffic.sh
```

## Partie D : Extraction des Métriques

Nous avons développé un script Python pour analyser les logs JSON et en extraire des indicateurs de sécurité et de performance.

### 1. Script d'analyse (`monitoring/log_metrics.py`)
Ce script lit le fichier de logs ligne par ligne et génère un rapport JSON contenant [cite: 366-373] :
* **`count_5xx`** : Nombre d'erreurs serveur (Codes HTTP 500+).
* **`p95_latency_ms`** : La latence en millisecondes en dessous de laquelle se trouvent 95% des requêtes (indicateur de performance critique).
* **`patterns`** : Détection de tentatives d'intrusion via Regex :
    * `path_traversal_hits` : Recherche de chaînes comme `../`
    * `cmd_param_hits` : Recherche de paramètres suspects comme `cmd=`

### 2. Test Local
Nous avons simulé une extraction de logs depuis l'environnement de staging pour valider le script.

**Procédure :**
1. Génération de trafic (Normal + Suspect).
2. Extraction des logs Docker vers un fichier :
   ```bash
   docker compose ... logs ... > reports/catalog_logs.jsonl
   ```

## Partie E : La Gate Runtime (Le Gardien)

Nous avons assemblé tous les composants (Smoke tests, Trafic, Logs, Métriques) dans un script d'orchestration unique : `monitoring/log_gate.sh`. Ce script sert de "barrière de qualité et de sécurité" automatisée [cite: 164-165].

### 1. Fonctionnement du script (`monitoring/log_gate.sh`)
Le script automatise la validation post-déploiement en 5 étapes séquentielles [cite: 166-172] :

1.  **Santé :** Vérifie que le service est vivant (`smoke.sh`) et stable (`supervision.sh`).
2.  **Simulation :** Génère du trafic via `traffic.sh`. Nous avons modifié ce script pour qu'il accepte le mode suspect en argument pour plus de robustesse.
3.  **Extraction :** Récupère les logs JSON du conteneur.
    * *Note importante :* Nous utilisons un timestamp (`START_TS`) et l'option `--since` pour n'analyser que les logs générés **durant** le test, ignorant ainsi l'historique précédent[cite: 183].
4.  **Analyse :** Calcule les métriques de sécurité et performance via `log_metrics.py`.
5.  **Décision (Gate) :** Compare les résultats aux seuils définis (0 attaque autorisée) et décide du succès ou de l'échec du pipeline [cite: 204-213].

### 2. Validation des Scénarios

Nous avons validé le bon fonctionnement de la Gate avec deux scénarios :

#### Scénario A : Trafic Nominal (Succès)
Le trafic est généré sans attaques. Les compteurs d'intrusion restent à 0.
* **Commande :** `bash monitoring/log_gate.sh`
* **Résultat obtenu :** `✅ GATE PASSED`

#### Scénario B : Simulation d'Attaque (Échec Volontaire)
Nous forçons le mode "suspect" pour simuler des tentatives de **Path Traversal** et d'**Injection de Commande**.
* **Commande :**
    ```bash
    bash -c "export SUSPECT_MODE=1; bash monitoring/log_gate.sh"
    ```
* **Résultat obtenu :**
    Le script détecte les motifs suspects dans les logs et bloque le déploiement.
    ```text
    [gate] 5. Verdict...
     - Path Traversal : 1
     - Command Injection : 1
    [gate] ❌ GATE FAILED
    ```

Cette validation prouve que notre chaîne de surveillance est capable de détecter et bloquer une version vulnérable de l'application en environnement de staging.


## Partie F : Intégration Continue (CI/CD)

Pour garantir que les contrôles de sécurité et de performance sont effectués systématiquement à chaque modification du code, nous avons intégré la Gate Runtime dans notre pipeline GitHub Actions.

### 1. Objectif
L'objectif est d'exécuter le script `monitoring/log_gate.sh` automatiquement après le déploiement en environnement de staging. Si la gate échoue (attaques détectées ou erreurs), le pipeline doit s'arrêter et fournir les logs pour analyse [cite: 232-233].

### 2. Configuration du Pipeline (`.github/workflows/ci.yml`)
Nous avons créé un workflow GitHub Actions qui orchestre le déploiement et la vérification.

**Extrait de la configuration :**

```yaml
jobs:
  runtime-gate:
    runs-on: ubuntu-latest
    steps:
      # 1. Démarrage de l'environnement Staging
      - name: Start Staging Environment
        run: docker compose -f compose.staging.yml up -d --build

      # 2. Exécution de la Gate (Script d'orchestration)
      - name: Run Log Gate
        run: |
          chmod +x monitoring/*.sh
          bash monitoring/log_gate.sh
        env:
          BASE_URL: http://localhost:5001
          SERVICE: catalog
          # Seuils stricts : aucune attaque tolérée
          MAX_5XX: 0
          MAX_TRAV: 0
          MAX_CMD: 0

      # 3. Sauvegarde des rapports (Artefacts)
      - name: Upload Security Reports
        if: always() # S'exécute même si la gate échoue
        uses: actions/upload-artifact@v4
        with:
          name: runtime-reports
          path: reports/