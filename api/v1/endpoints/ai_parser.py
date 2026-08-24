from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import io
import PyPDF2
import docx

from app.api.deps import get_current_user
from app.models.user import User
from app.services.ai_service import extract_questions_with_gemini

router = APIRouter()

@router.post("/parse-document")
async def parse_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    ext = file.filename.split('.')[-1].lower()
    raw_text = ""
    
    try:
        content = await file.read()
        
        if ext == 'pdf':
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                raw_text += page.extract_text() + "\n"
                
        elif ext == 'docx':
            doc = docx.Document(io.BytesIO(content))
            raw_text = "\n".join([para.text for para in doc.paragraphs])
            
        elif ext == 'txt':
            raw_text = content.decode('utf-8')
            
        else:
            raise HTTPException(400, "Chỉ hỗ trợ file PDF, DOCX, TXT")
            
        if not raw_text.strip():
            raise HTTPException(400, "Không thể đọc trích xuất được chữ trong file này.")
            
        # Nạp vào lò AI
        json_questions = await extract_questions_with_gemini(raw_text)
        
        return {"filename": file.filename, "extracted_count": len(json_questions), "data": json_questions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
