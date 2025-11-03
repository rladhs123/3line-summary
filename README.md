# 3line-summary

## 프로젝트 설명

URL 또는 텍스트를 입력으로 받아 정확히 3문장으로 요약해주는 FastAPI 기반의 AI 서비스

## 실행 방법

```bash
# 1) 의존성 설치
conda create -n sejulcut python=3.11 -y
conda activate 3line-summary

# 2) API 키 설정 (예시)
# env/settings.py
# CONFIG = {"KEY": "YOUR_API_KEY"}

# 3) 서버 실행 (app.py 파일에 app = FastAPI())
uvicorn app:app --reload
```
