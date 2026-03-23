from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

app = FastAPI()

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    return {"message": "OK", "database": "connected"}
    

