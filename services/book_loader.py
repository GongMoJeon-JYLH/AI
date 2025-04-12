import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer

BOOKS_JSON_PATH = "data/books.json"
VECTOR_DB_PATH = "data/book_vectors.npy"

model = SentenceTransformer("jhgan/ko-sbert-nli")

def load_books():
    if os.path.exists(BOOKS_JSON_PATH):
        with open(BOOKS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

def load_vectors():
    if os.path.exists(VECTOR_DB_PATH):
        return np.load(VECTOR_DB_PATH)
    else:
        return None
