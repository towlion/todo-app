import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Todo

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/app_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="TODO App")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TodoCreate(BaseModel):
    title: str


class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool

    model_config = {"from_attributes": True}


@app.get("/health")
def health():
    return {"status": "ok", "preview": True}


@app.get("/")
def root():
    return {"message": "Welcome to the TODO app"}


@app.get("/todos", response_model=list[TodoResponse])
def list_todos(db: Session = Depends(get_db)):
    return db.query(Todo).order_by(Todo.created_at.desc()).all()


@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = Todo(title=todo.title)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.patch("/todos/{todo_id}", response_model=TodoResponse)
def toggle_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.completed = not todo.completed
    db.commit()
    db.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
