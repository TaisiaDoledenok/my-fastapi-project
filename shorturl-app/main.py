from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import sqlite3
import string
import random
from pydantic import BaseModel

app = FastAPI(title="URL Shortener", docs_url="/docs")

class URLRequest(BaseModel):
    url: str

def init_db():
    conn = sqlite3.connect('/data/urls.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_id TEXT UNIQUE,
            full_url TEXT NOT NULL,
            click_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_id(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

init_db()

@app.post("/shorten")
def shorten_url(data: URLRequest):
    """Создать короткую ссылку"""
    url = data.url
    
    # Проверяем, есть ли уже такая ссылка
    conn = sqlite3.connect('/data/urls.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT short_id FROM urls WHERE full_url = ?", (url,))
    result = cursor.fetchone()
    
    if result:
        short_id = result[0]
        conn.close()
        return {
            "short_id": short_id,
            "short_url": f"http://localhost:80/{short_id}"
        }
    
    # Создаем новую короткую ссылку
    while True:
        short_id = generate_short_id()
        cursor.execute("SELECT 1 FROM urls WHERE short_id = ?", (short_id,))
        if not cursor.fetchone():
            break
    
    cursor.execute(
        "INSERT INTO urls (short_id, full_url) VALUES (?, ?)",
        (short_id, url)
    )
    conn.commit()
    conn.close()
    
    return {
        "short_id": short_id,
        "short_url": f"http://localhost:80/{short_id}"
    }

@app.get("/{short_id}")
def redirect_url(short_id: str):
    """Перенаправить по короткой ссылке"""
    conn = sqlite3.connect('/data/urls.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT full_url FROM urls WHERE short_id = ?",
        (short_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Увеличиваем счетчик кликов
    cursor.execute(
        "UPDATE urls SET click_count = click_count + 1 WHERE short_id = ?",
        (short_id,)
    )
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=result[0])

@app.get("/stats/{short_id}")
def get_stats(short_id: str):
    """Получить статистику по короткой ссылке"""
    conn = sqlite3.connect('/data/urls.db')
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT short_id, full_url, click_count, created_at 
           FROM urls WHERE short_id = ?""",
        (short_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return {
        "short_id": result[0],
        "full_url": result[1],
        "click_count": result[2],
        "created_at": result[3],
        "short_url": f"http://localhost:80/{result[0]}"
    }

@app.get("/")
def home():
    return {"message": "URL Shortener Service", "docs": "/docs"}
