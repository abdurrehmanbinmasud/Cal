from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
import statistics

# --- Database Setup ---
DATABASE_URL = "sqlite:///./calculator.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CalculationHistory(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    inputs = Column(JSON)
    operation = Column(String)
    result = Column(Float)

Base.metadata.create_all(bind=engine)

# --- Data Models ---
class CalculationRequest(BaseModel):
    numbers: List[float]
    operation: str

# --- App Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.post("/calculate")
def perform_calculation(req: CalculationRequest, db: Session = Depends(get_db)):
    if not req.numbers:
        raise HTTPException(status_code=400, detail="Please provide at least one number.")
    
    result = 0.0
    nums = req.numbers

    if req.operation == "SUM":
        result = sum(nums)
    elif req.operation == "AVG":
        result = statistics.mean(nums)
    elif req.operation == "MAX":
        result = max(nums)
    elif req.operation == "MIN":
        result = min(nums)
    elif req.operation == "MULTIPLY":
        result = 1
        for n in nums:
            result *= n
    elif req.operation == "MOD":
        if len(nums) < 2:
            raise HTTPException(status_code=400, detail="Modulo needs at least 2 numbers.")
        result = nums[0]
        for i in range(1, len(nums)):
            if nums[i] == 0:
                    raise HTTPException(status_code=400, detail="Cannot divide by zero.")
            result %= nums[i]
    
    # Save to DB
    db_record = CalculationHistory(inputs=nums, operation=req.operation, result=result)
    db.add(db_record)
    db.commit()

    return {"result": result, "message": "Success"}

# [NEW] Endpoint to get history
@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    # Get all records, ordered by newest first
    return db.query(CalculationHistory).order_by(CalculationHistory.id.desc()).all()