from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os

os.makedirs("/data", exist_ok=True)

conn = sqlite3.connect('/data/todo.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        completed INTEGER DEFAULT 0
    )
''')
conn.commit()

app = FastAPI(
    title="ToDo Service",
    docs_url="/docs"
)

class TodoItem(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoItemResponse(TodoItem):
    id: int

@app.post("/items", response_model=TodoItemResponse)
def create_item(item: TodoItem):
    cursor.execute(
        "INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
        (item.title, item.description, 1 if item.completed else 0)
    )
    conn.commit()
    
    item_id = cursor.lastrowid
    return {
        "id": item_id,
        "title": item.title,
        "description": item.description,
        "completed": item.completed
    }

@app.get("/items", response_model=List[TodoItemResponse])
def get_all_items():
    cursor.execute("SELECT id, title, description, completed FROM todos")
    rows = cursor.fetchall()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "completed": bool(row[3])
        })
    return items

@app.get("/items/{item_id}", response_model=TodoItemResponse)
def get_item(item_id: int):
    cursor.execute(
        "SELECT id, title, description, completed FROM todos WHERE id = ?",
        (item_id,)
    )
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": bool(row[3])
    }

@app.put("/items/{item_id}", response_model=TodoItemResponse)
def update_item(item_id: int, item: TodoItem):
    cursor.execute(
        """UPDATE todos 
        SET title = ?, description = ?, completed = ? 
        WHERE id = ?""",
        (item.title, item.description, 1 if item.completed else 0, item_id)
    )
    conn.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {
        "id": item_id,
        "title": item.title,
        "description": item.description,
        "completed": item.completed
    }

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    cursor.execute("DELETE FROM todos WHERE id = ?", (item_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}

@app.get("/")
def root():
    return {"message": "ToDo Service is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}
