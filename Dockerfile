# Usa una imagen base de Python
FROM python:3.12.5-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala las dependencias
RUN pip install discord.py python-dotenv redis

# Copia el resto del código
COPY . .

# Comando para ejecutar el bot
CMD ["python", "main.py"]
