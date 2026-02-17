# Image légère Python
FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY src/ .

# Port standard Flask
EXPOSE 5000

# Lancement
CMD ["python", "app.py"]