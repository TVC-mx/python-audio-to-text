FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para audio
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    libsoxr0 \
    libsoxr-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
# Instalar numpy primero para evitar conflictos de versión
RUN pip install --no-cache-dir "numpy<2.0.0"
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios para audios y textos
RUN mkdir -p /app/audios /app/textos

# Comando por defecto
CMD ["python", "main.py"]
