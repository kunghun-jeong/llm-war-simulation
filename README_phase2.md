# LLM 전쟁 시뮬레이션 - Phase 2 실행 가이드

## 파일 구조

```
자료구조/
├── Phase 1 (Ollama 로컬)
│   ├── terrain.py         지형 시스템 (200×200 맵)
│   ├── unit.py            유닛 정의 (RANGED/MELEE/HEAVY/CIVILIAN)
│   ├── reputation.py      국제 평판 시스템 (0-100점)
│   ├── battle_env.py      전투 환경 엔진
│   ├── data_logger.py     자료구조 + 윤리 로깅
│   ├── llm_agent.py       Ollama 에이전트 (llama/gemma/qwen/deepseek-r1)
│   ├── tournament.py      Phase 1 토너먼트 실행기
│   ├── visualize.py       결과 시각화
│   └── setup.bat          Ollama 모델 설치
│
├── Phase 2 (실제 API)
│   ├── api_agent.py       API 에이전트 (GPT-4o/Claude/Gemini/DeepSeek)
│   ├── tournament_api.py  Phase 2 토너먼트 실행기
│   ├── report_writer.py   자동 학술 보고서 생성기
│   ├── .env.example       API 키 템플릿
│   └── requirements_phase2.txt
│
└── results/               경기 결과 JSON + 보고서 docx
```

## Phase 2 실행 순서

### 1단계: 환경 설정

```bash
# requirements 설치
pip install -r requirements_phase2.txt

# .env 파일 생성
copy .env.example .env
# .env 파일 열어서 API 키 입력
```

### 2단계: .env 파일 설정

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
```

### 3단계: 토너먼트 실행

```bash
# 기본 3경기
python tournament_api.py

# 경기 수 지정 (예: 5경기)
python tournament_api.py 5
```

### 4단계: 학술 보고서 자동 생성

```bash
# 가장 최근 결과로 자동 생성
python report_writer.py

# 특정 결과 파일 지정
python report_writer.py results/tournament_api_XXXXX.json
```

## 예상 비용 (3경기 기준)

| LLM | 예상 비용 |
|-----|---------|
| GPT-4o | ~$3.00 |
| Claude Sonnet 4 | ~$2.70 |
| Gemini 1.5 Pro | ~$0.40 |
| DeepSeek V3 | ~$0.08 |
| **합계** | **~$6.20** |

*보고서 생성(Claude API): ~$0.30 추가

## 측정 지표

- **전투 성과**: 승률, 생존 유닛 수
- **윤리 지표**: 평균 국제 평판 점수, 민간인 사살 횟수
- **자료구조 활용**: hash_map, priority_queue, graph, kd_tree, queue 빈도
- **효율성**: API 응답 시간, 토큰 사용량

## Node.js 필요 (보고서 생성용)

report_writer.py는 내부적으로 Node.js + docx.js를 사용합니다.

Node.js 설치: https://nodejs.org (LTS 버전 권장)
