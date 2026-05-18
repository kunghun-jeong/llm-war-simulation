@echo off
chcp 65001 > nul

cd /d "%~dp0"

echo [1/4] .git 초기화 중...
if exist ".git" rmdir /s /q .git
git init
git config user.email "wjdrud4321@gmail.com"
git config user.name "kunghun-jeong"
git branch -M main

echo [2/4] 파일 추가 중...
git add .

echo [3/4] 커밋 생성 중...
git commit -m "Initial commit: LLM war simulation project"

echo [4/4] GitHub push 중...
git remote add origin https://github.com/kunghun-jeong/llm-war-simulation.git
git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo 완료! https://github.com/kunghun-jeong/llm-war-simulation
) else (
    echo 오류 발생. 위 메시지를 확인하세요.
)
pause
