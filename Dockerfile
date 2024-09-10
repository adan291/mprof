# Usa una imagen base de Python
FROM python:3.12.5-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copiar el archivo requirements.txt al contenedor
COPY requirements.txt .

# Instala las dependencias
#RUN pip install discord.py python-dotenv redis
# Instalar las dependencias necesarias desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Comando para ejecutar el bot
CMD ["python", "main.py"]
