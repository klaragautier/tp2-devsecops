# On utilise une image officielle légère et maintenue
FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code sécurisé
COPY src/ .

# On expose le port 5000
EXPOSE 5000

# Création d'un utilisateur non-root pour la sécurité (Bonne pratique Docker)
RUN useradd -m appuser
USER appuser

CMD ["python", "app.py"]