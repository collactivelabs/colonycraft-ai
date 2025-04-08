# src/api/v1/endpoints/files.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.models import File, User
from src.core.database import get_db
from src.core.auth import get_current_user

router = APIRouter()

@router.get("/files/{file_id}")
async def get_file(file_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieve metadata for a generated file.
    """
    file = db.query(File).filter(File.id == file_id, File.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.delete("/files/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Delete a generated file.
    """
    file = db.query(File).filter(File.id == file_id, File.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete the file from Google Cloud Storage (if needed)
    # You can implement this logic in the storage service.

    db.delete(file)
    db.commit()
    return {"message": "File deleted successfully"}