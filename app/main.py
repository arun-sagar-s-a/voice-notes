from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.groq_client import transcribe_audio, parse_expense
from app.database import save_expense, get_all_expenses, get_summary, get_expense, delete_expense

app = FastAPI()
FRONTEND = Path(__file__).parent.parent / "frontend" / "index.html"

@app.get("/")
async def root():
    return FileResponse(FRONTEND)

@app.get("/health")
async def get_health():
    return {"status":"Running"}

@app.post("/api/expenses", status_code=201)
async def create_expense(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(400, "Audio size too large. Max 25mb")
    
    transcription = await transcribe_audio(audio_bytes, audio.filename or "audio.webm")
    transcript = transcription["text"]

    if not transcript.strip():
        raise HTTPException(400, "No speech detected in the audio.")
    
    parsed = await parse_expense(transcript)
    expenses = parsed.get("expenses",[])

    if not expenses:
        raise HTTPException(400, "No expenses detected in the recording.")
    
    saved_ids = []
    for expense in expenses:
        expense_id = save_expense(
            transcript=transcript,
            amount=expense["amount"],
            store=expense.get("store"),
            category=expense.get("category"),
            notes=expense.get("notes")
        )
        saved_ids.append(expense_id)

    return {
        "ids": saved_ids,
        "transcript":transcript,
        "expenses": expenses
    }

@app.get("/api/expenses",status_code=200)
async def list_expenses(limit: int = 25, offset: int =0):
    expenses = get_all_expenses(limit, offset)
    return {"expenses":expenses, "count":len(expenses)}

@app.get("/api/expenses/summary",status_code=200)
async def expenses_summary(days: int = 30):
    summary = get_summary(days)
    return summary

@app.get("/api/expenses/{expense_id}",status_code=200)
async def list_expense(expense_id: int):
    expense = get_expense(expense_id)
    if not expense:
        raise HTTPException(404,"Expense not found.")
    
    return expense

@app.delete("/api/expenses/{expense_id}", status_code=204)
async def remove_expense(expense_id: int):
    if not delete_expense(expense_id):
        raise HTTPException(404, "Expense not found.")
    
    return None