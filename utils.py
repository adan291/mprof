# config.py

# Lista de categorías válidas
VALID_CATEGORIES = [
    "alquimista",
    "herrero",
    "sastrería",
    "ingeniería",
    "encantamiento",
    "joyero",
    "peletero",
    "inscripción",
    # Añade aquí otras categorías si es necesario
]
import unicodedata

def normalize_text(text):
    """Normaliza el texto eliminando tildes y convirtiendo a minúsculas."""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()
