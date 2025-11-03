from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware # CORS를 위해 임포트
from google import genai
from env.settings import CONFIG # API KEY 설정 파일 임포트

# 크롤링 라이브러리
from trafilatura import fetch_url, extract
import json

client = genai.Client(api_key=CONFIG["KEY"])

# 빠른 응답 속도
MODEL_FLASH = "gemini-2.5-flash"
# 높은 성능
MODEL_PRO = "gemini-2.5-pro"

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"], # 모든 HTTP 메소드 허용
    allow_headers=["*"], # 모든 HTTP 헤더 허용
)

# 프론트엔드(HTML)에서 보낸 'text' 데이터를 받기 위한 모델
class TextIn(BaseModel):
    text: str

# 요약 API
@app.post("/summarize")
async def summarize_text(text: TextIn):
    # 요약할 텍스트가 없는 경우 예외 처리
    if not text.text.strip():
        raise HTTPException(status_code=400, detail="요약할 텍스트가 없습니다.")
    
    result = ""

    # URL인 경우 크롤링 수행
    if text.text.startswith("http://") or text.text.startswith("https://"):
        result = crawler(text.text)
    # 일반 텍스트인 경우 바로 사용
    else:
        result = text.text.strip()

    return {"summary": generate_summary(result, select_summary_model(result))}

# URL 크롤링 함수
def crawler(url: str) -> str:
    try:
        downloaded = fetch_url(url)
        extracted_result = extract(downloaded, output_format='json', with_metadata=True, deduplicate=True)
        text = json.loads(extracted_result)['text'].strip()

        if not text:
            raise ValueError("URL에서 텍스트를 추출 실패")
        
        return text
    except Exception as e:
        raise HTTPException(status_code=422, detail="크롤링 실패")

# 요약 생성 AI 모델 선택 함수 (텍스트 길이에 따라 모델 선택)
def select_summary_model(text: str) -> str:
    if len(text) > 20000:
        return MODEL_PRO
    
    return MODEL_FLASH

# 요약 생성 함수
def generate_summary(text: str, MODEL: str) -> str:
    prompt = """
        당신은 주어진 텍스트의 핵심 내용을 정확하게 파악하여 요약하는 AI 어시스턴트입니다.
        당신의 임무는 사용자가 제공한 텍스트를 정확히 3개의 문장으로 요약하는 것입니다.

        출력 규칙:
        반드시 3개의 문장으로만 구성되어야 합니다.
        각 문장은 번호 매기기 목록 형식으로 시작해야 합니다.
        문장과 문장 사이에는 빈 줄이 하나씩 있어야 합니다.
        텍스트를 요약할 때, 원본 텍스트의 의미를 왜곡하거나 변경하지 마십시오.
        1번 (텍스트의 초반부 요약), 2번 (중간 부분 요약), 3번 (끝부분 요약) 순서로 작성하십시오.

        출력 형식:
        1. [요약된 첫 번째 문장]

        2. [요약된 두 번째 문장]

        3. [요약된 세 번째 문장]

        입력된 텍스트와 동일한 언어로 요약해야 합니다.
        입력은 다음과 같습니다: \n"""
    try:
        result = client.models.generate_content(
            model=MODEL,
            contents=[prompt + text]
        )
        return result.text
    except Exception as e:
        raise HTTPException(status_code=502, detail = "AI 요약 생성에 실패했습니다.")
