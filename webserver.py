from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def index():
    return "Hello im alive mplux"

def run():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8001))  # Usar el puerto proporcionado por la plataforma o el predeterminado


def keep_alive():
    server = Thread(target=run)
    server.start()