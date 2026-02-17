# Image légère Python (et non plus Node)
FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances Python
# On copie requirements.txt (que tu as créé juste avant)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
# Attention : on copie le contenu du dossier src/ dans le dossier courant /app
COPY src/ .

# Port standard Flask
EXPOSE 5000

# Lancement du serveur Python
CMD ["python", "app.py"]