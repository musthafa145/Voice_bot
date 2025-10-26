# api_server.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
import sqlite3
from typing import List, Optional
import uvicorn

DB = "myg_products.db"
app = FastAPI(title="MYG Synthetic Product API")

class Product(BaseModel):
    id: int
    product_name: str
    category: str
    brand: str
    price: int
    features: str
    highlights: str
    stock_status: str

def query_db(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/product/{product_id}", response_model=Product)
def get_product(product_id: int):
    rows = query_db("SELECT * FROM product WHERE id = ?", (product_id,))
    if not rows:
        return {}
    return rows[0]

@app.get("/search", response_model=List[Product])
def search(q: Optional[str] = Query(None), category: Optional[str] = Query(None),
           max_price: Optional[int] = Query(None), limit: int = 5):
    where_clauses = []
    params = []
    if q:
        q_like = f"%{q}%"
        where_clauses.append("(product_name LIKE ? OR features LIKE ? OR highlights LIKE ? OR brand LIKE ?)")
        params.extend([q_like, q_like, q_like, q_like])
    if category:
        where_clauses.append("category = ?")
        params.append(category)
    if max_price:
        where_clauses.append("price <= ?")
        params.append(max_price)
    where = (" AND ".join(where_clauses)) if where_clauses else "1=1"
    sql = f"SELECT * FROM product WHERE {where} ORDER BY price ASC LIMIT ?"
    params.append(limit)
    rows = query_db(sql, tuple(params))
    return rows

# <-- NEW: default route for quick testing
@app.get("/products", response_model=List[Product])
def list_products(limit: int = 10):
    return query_db("SELECT * FROM product ORDER BY id ASC LIMIT ?", (limit,))

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
