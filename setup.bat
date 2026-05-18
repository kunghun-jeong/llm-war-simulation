@echo off
echo ========================================
echo  LLM 전쟁 시뮬레이션 - 환경 세팅
echo ========================================

echo.
echo [1/3] Python 패키지 설치 중...
pip install -r requirements.txt

echo.
echo [2/3] Ollama 모델 확인 중...
ollama list

echo.
echo [3/3] 필요한 모델 다운로드 중...
echo  - llama3.1:8b   (Meta / Llama팀)
ollama pull llama3.1:8b
echo  - gemma3:4b     (Google / Gemma팀)
ollama pull gemma3:4b
echo  - qwen2.5:7b    (Alibaba / Qwen팀)
ollama pull qwen2.5:7b
echo  - deepseek-r1:8b (DeepSeek AI / DeepSeek팀)
ollama pull deepseek-r1:8b

echo.
echo ========================================
echo  세팅 완료!
echo  실행: python tournament.py
echo ========================================
pause
