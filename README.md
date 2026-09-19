# LLM War Simulation

A tactical battle simulation where LLM agents (GPT-4o, Claude, Gemini, DeepSeek, and local Ollama models) command armies on a 200×200 terrain map, evaluated on both combat performance and ethical behavior.

## What it does

- **Units & terrain**: RANGED / MELEE / HEAVY / CIVILIAN unit types on a generated terrain map.
- **LLM commanders**: each side's tactics are driven by an LLM agent — either local models via Ollama (Llama, Gemma, Qwen, DeepSeek-R1) or hosted APIs (GPT-4o, Claude, Gemini, DeepSeek).
- **Ethics tracking**: an international reputation score (0–100) penalizes civilian casualties, so agents are scored on more than just winning.
- **Data-structure instrumentation**: logs each agent's use of hash maps, priority queues, graphs, k-d trees, and queues during decision-making.
- **Automated reporting**: `report_writer.py` turns tournament results into an academic-style report (.docx) automatically.

## Two phases

| Phase | Agents | Cost |
|---|---|---|
| Phase 1 | Local models via Ollama | Free |
| Phase 2 | Hosted APIs (GPT-4o, Claude Sonnet 4, Gemini 1.5 Pro, DeepSeek V3) | ~$6 for a 3-match tournament |

## Tech stack

Python, Ollama, OpenAI/Anthropic/Google/DeepSeek APIs, Node.js + docx.js (for report generation)

## Run it

```bash
pip install -r requirements_phase2.txt
copy .env.example .env   # fill in API keys

python tournament_api.py 5     # run 5 matches
python report_writer.py        # auto-generate a report from the latest results
```

See [README_phase2.md](README_phase2.md) for the full setup and file-by-file breakdown.
