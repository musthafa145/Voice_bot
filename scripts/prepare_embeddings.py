import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Paths
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'synthetic_myg_products.csv')
DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
MODEL_NAME = 'all-MiniLM-L6-v2'  # small, fast SBERT model


def clean_text(s):
    if pd.isna(s):
        return ''
    return str(s).strip()


def create_document(row):
    # Build a useful text representation for embedding
    parts = []
    parts.append(f"Name: {clean_text(row.get('product_name'))}")
    parts.append(f"Brand: {clean_text(row.get('brand'))}")
    parts.append(f"Category: {clean_text(row.get('category'))}")
    parts.append(f"Price: {clean_text(row.get('price'))}")
    features = clean_text(row.get('features'))
    highlights = clean_text(row.get('highlights'))
    if features:
        parts.append(f"Features: {features}")
    if highlights:
        parts.append(f"Highlights: {highlights}")
    return ' | '.join(parts)


def main():
    print('Loading CSV...')
    df = pd.read_csv(CSV_PATH)
    print(f'Read {len(df)} rows')

    # Minimal cleaning
    df = df.drop_duplicates(subset=['product_id'])
    df['document'] = df.apply(create_document, axis=1)

    texts = df['document'].tolist()
    ids = df['product_id'].astype(str).tolist()

    print('Loading embedding model...')
    model = SentenceTransformer(MODEL_NAME)

    print('Creating embeddings...')
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # Create Chroma client (use PersistentClient for the current Chroma API)
    print('Storing embeddings to Chroma DB...')
    client = chromadb.PersistentClient(path=DB_DIR)

    collection_name = 'products'
    if collection_name in [c.name for c in client.list_collections()]:
        collection = client.get_collection(collection_name)
    else:
        collection = client.create_collection(name=collection_name)

    # Upsert embeddings
    collection.upsert(ids=ids, embeddings=embeddings.tolist(), metadatas=df.to_dict(orient='records'), documents=texts)

    # PersistentClient writes to disk automatically. Confirm completion.
    print(f'Done. Stored {len(ids)} embeddings in {DB_DIR}')


if __name__ == '__main__':
    main()
