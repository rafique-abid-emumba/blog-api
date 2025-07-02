from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from sqlalchemy import text
from app.api.user import router as user_router

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    # Try a simple query
    db.execute(text('SELECT 1'))
    return {"status": "Database connected"}


app.include_router(user_router)