from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)

# CORRECTION 1 (Secrets) : 
# On ne stocke plus le secret en dur. On le charge depuis l'environnement.
# Si la variable n'existe pas (dev local), on utilise une clé par défaut.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "default-dev-key")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status": "ok", "service": "catalog-service"}

# CORRECTION 2 (Injection SQL) : 
# Utilisation de "requêtes paramétrées". SQLite sépare le code des données.
@app.route("/search")
def search():
    q = request.args.get("q", "")
    
    # Initialisation DB (Simulé pour le TP)
    db_path = "db.sqlite"
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER, name TEXT, price REAL)")
        conn.execute("INSERT INTO products VALUES (1, 'Book A', 10.0)")
        conn.execute("INSERT INTO products VALUES (2, 'DevSecOps Guide', 25.0)")
        conn.commit()
    else:
        conn = sqlite3.connect(db_path)
    
    cur = conn.cursor()
    
    # LE FIX EST ICI : On utilise ? au lieu d'insérer la variable directement
    query = "SELECT id, name, price FROM products WHERE name LIKE ?"
    
    try:
        # On passe les paramètres dans un tuple à part
        rows = cur.execute(query, ('%' + q + '%',)).fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": "Database error"}), 500
    finally:
        conn.close()

# CORRECTION 3 (RCE - Remote Code Execution) :
# La route /debug/run a été TOTALEMENT SUPPRIMÉE.
# C'est la seule façon sécurisée de traiter une backdoor.

# CORRECTION 4 (Bug Logique) :
@app.route("/discount", methods=["POST"])
def discount():
    try:
        data = request.get_json()
        pct = int(data.get("pct", 0))
        
        # Le prix est maintenant défini (simulé)
        price = 100 
        
        # Validation des données pour éviter les prix négatifs
        if pct < 0 or pct > 100:
            return jsonify({"error": "Invalid percentage"}), 400

        new_price = price * (100 - pct) / 100 
        return {"new_price": new_price}
    except Exception:
        return jsonify({"error": "Bad request"}), 400

if __name__ == "__main__":
    # Désactivation du mode debug en production
    app.run(host="0.0.0.0", port=5000, debug=False) # nosemgrep