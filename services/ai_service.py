import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from app.core.config import settings
import json
import re

async def extract_questions_with_gemini(raw_text: str):
    if not settings.GEMINI_API_KEY:
        raise ValueError("Chưa cấu hình GEMINI_API_KEY trên Server!")
        
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # Dùng model gemini-2.5-flash (Model hiện đại nhất năm 2026)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Bạn là một trợ lý ảo phân tích đề thi trắc nghiệm siêu việt.
    Hãy đọc tài liệu thô dưới đây và phân tách nó thành một mảng các câu hỏi với định dạng JSON chuẩn mực.
    Yêu cầu định dạng CHÍNH XÁC:
    [
        {{
            "content": "Nội dung câu hỏi",
            "points": 10,
            "options": {{"A": "Đáp án 1", "B": "Đáp án 2", "C": "Đáp án 3", "D": "Đáp án 4"}},
            "correct_answer": "A"
        }}
    ]
    
    LUẬT BẮT BUỘC:
    1. Tuyệt đối chỉ trả về dữ liệu là một mảng JSON thuần túy, không bọc trong dấu ```json hay bất kỳ chữ nào khác.
    2. Nếu tài liệu không ghi sẵn câu trả lời đúng, hãy tự động đánh là A.
    3. Bóc tách TOÀN BỘ (tất cả) các câu hỏi có trong tài liệu, TUYỆT ĐỐI không được bỏ sót câu nào.

    Tài liệu thô cần bóc tách:
    {raw_text}
    """
    
    response = model.generate_content(prompt)
    text = response.text
    
    # Xử lý làm mượt JSON (bỏ markdown thừa)
    text = text.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(text)
        return data
    except json.JSONDecodeError:
        raise ValueError(f"AI không thể xuất JSON chuẩn: {text[:100]}...")
