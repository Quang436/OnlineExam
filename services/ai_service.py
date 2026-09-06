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
    
    # Dùng model gemini-2.5-flash
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
Bạn là chuyên gia phân tích và bóc tách đề thi trắc nghiệm hàng đầu.
Nhiệm vụ của bạn là đọc kỹ tài liệu thô dưới đây và chuyển đổi thành một mảng JSON các câu hỏi trắc nghiệm chuẩn xác.

Định dạng JSON yêu cầu:
[
    {{
        "content": "Nội dung câu hỏi đầy đủ",
        "points": 10,
        "options": {{
            "A": "Nội dung chi tiết phương án A",
            "B": "Nội dung chi tiết phương án B",
            "C": "Nội dung chi tiết phương án C",
            "D": "Nội dung chi tiết phương án D"
        }},
        "correct_answer": "A"
    }}
]

QUY TẮC BẮT BUỘC:
1. CHỈ trả về dữ liệu là một mảng JSON thuần túy (bắt đầu bằng [ và kết thúc bằng ]). Không thêm bất kỳ lời dẫn hay giải thích nào khác ngoài JSON.
2. NỘI DUNG CÁC PHƯƠNG ÁN (options):
   - Phải trích xuất đầy đủ, chính xác câu chữ của từng phương án A, B, C, D từ tài liệu.
   - TUYỆT ĐỐI KHÔNG ĐƯỢC đặt các giá trị placeholder vô nghĩa như "Option A", "Option B", "Đáp án A", "Đáp án B"...
   - Nếu trong tài liệu có câu hỏi mà không có các lựa chọn A, B, C, D sẵn, bạn HÃY TỰ SOẠN 4 phương án lựa chọn A, B, C, D thật sự có nghĩa và mang tính chuyên môn cao phù hợp với câu hỏi (gồm 1 đáp án đúng và 3 phương án gây nhiễu hợp lý).
3. XÁC ĐỊNH ĐÁP ÁN ĐÚNG (correct_answer):
   - Bước 1: Tìm kiếm trong tài liệu các dấu hiệu đáp án: bảng đáp án ở cuối/đầu tài liệu (ví dụ: "1A 2B 3C", "1. A, 2. B..."), hoặc đáp án được ghi chú cạnh câu hỏi (ví dụ: "Đáp án: B", "Đ/A: B", "[B]", "[ĐÁP ÁN: ...]"), hoặc phương án có đánh dấu (*, [x], in đậm, gạch chân). Nếu có, hãy dùng đáp án đó.
   - Bước 2: Nếu trong tài liệu hoàn toàn KHÔNG CÓ bất kỳ dấu hiệu đáp án nào, bạn PHẢI TỰ DÙNG KIẾN THỨC CHUYÊN MÔN CỦA MÌNH ĐỂ GIẢI CÂU HỎI VÀ CHỌN ĐÁP ÁN CHÍNH XÁC NHẤT (A, B, C hoặc D). TUYỆT ĐỐI KHÔNG được mặc định chọn "A".
4. Bóc tách TOÀN BỘ tất cả các câu hỏi có trong tài liệu, không được bỏ sót câu nào.

Tài liệu thô cần bóc tách:
{raw_text}
"""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # Xử lý làm mượt JSON (bỏ markdown thừa)
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    # Tìm mảng JSON bắt đầu bằng [ và kết thúc bằng ]
    match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
    if match:
        text = match.group(0)
        
    try:
        data = json.loads(text)
        return data
    except json.JSONDecodeError:
        raise ValueError(f"AI không thể xuất JSON chuẩn: {text[:150]}...")
