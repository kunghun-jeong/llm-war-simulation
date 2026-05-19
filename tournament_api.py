"""
tournament_api.py - Phase 2: 실제 API 기반 LLM 전쟁 시뮬레이션 토너먼트
GPT-4o / Claude Sonnet 4 / Gemini 1.5 Pro / DeepSeek V3

사용법:
  1. .env 파일에 API 키 설정
  2. pip install -r requirements_phase2.txt
  3. python tournament_api.py [경기 수] (기본값: 3)
"""

import json, os, sys, time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

from battle_env import BattleEnv
from api_agent  import APIAgent, TEAMS, MODEL_CONFIG
from data_logger import DSLogger

# ── 팀 표시명 ─────────────────────────────────────────────────
MODEL_DISPLAY = {t: MODEL_CONFIG[t]["display"] for t in TEAMS}


# ── API 키 확인 ───────────────────────────────────────────────
def check_api_keys() -> bool:
    required = {
        "llama":       "GROQ_API_KEY",
        "gemma":       "GROQ_API_KEY",
        "qwen":        "GROQ_API_KEY",
        "deepseek_r1": "GROQ_API_KEY",
        "gpt":         "OPENAI_API_KEY",
        "claude":      "ANTHROPIC_API_KEY",
        "gemini":      "GOOGLE_API_KEY",
        "deepseek":    "DEEPSEEK_API_KEY",
    }
    all_ok = True
    print("\n[사전 확인] API 키 상태 점검 중...")
    for team, env_var in required.items():
        val = os.getenv(env_var, "")
        if val and len(val) > 8:
            print(f"  ✅ {team:10s} ({env_var}) 확인됨")
        else:
            print(f"  ❌ {team:10s} ({env_var}) 없음 — .env 파일 확인 필요")
            all_ok = False

    if not all_ok:
        print("\n  ⚠️  일부 API 키가 없습니다.")
        print("  .env.example 파일을 .env로 복사한 후 키를 입력하세요.\n")
        resp = input("  누락된 팀을 제외하고 계속 진행할까요? (y/N): ").strip().lower()
        if resp != "y":
            sys.exit(1)

    print("[사전 확인] API 키 확인 완료!\n")
    return all_ok


# ── 단일 경기 ─────────────────────────────────────────────────
def run_match(match_id: int, active_teams: list, verbose: bool = True) -> dict:
    logger = DSLogger()
    env    = BattleEnv(max_turns=100, verbose=verbose)
    agents = {}

    for team in active_teams:
        try:
            agents[team] = APIAgent(team, logger)
        except Exception as e:
            print(f"  ⚠️  {team} 에이전트 초기화 실패: {e}")

    active = [t for t in active_teams if t in agents]

    while True:
        actions_by_team = {}
        for team in active:
            if (env.rep.is_disqualified(team) or
                    len(env.alive_soldiers(team)) == 0):
                continue
            state   = env.get_state_for_team(team)
            actions = agents[team].decide(state)
            actions_by_team[team] = actions

        done, winner = env.step(actions_by_team)
        if done:
            break

    report      = env.final_report()
    rep_summary = env.rep.summary()
    ds_summary  = logger.summary()

    agent_stats = {}
    total_cost  = 0.0
    for team in active:
        st = agents[team].stats()
        # 간단한 비용 추정 (토큰 기반)
        cost = _estimate_cost(team, st["total_tokens"])
        st["estimated_cost_usd"] = round(cost, 4)
        total_cost += cost
        agent_stats[team] = st

    return {
        "match_id":    match_id,
        "winner":      winner,
        "turns":       report["turns"],
        "teams":       report["teams"],
        "reputation":  rep_summary,
        "ds_ops":      ds_summary,
        "agent_stats": agent_stats,
        "total_cost_usd": round(total_cost, 4),
    }


def _estimate_cost(team: str, tokens: int) -> float:
    """팀별 API 비용 추정 (2024년 기준 입력+출력 평균)"""
    price_per_1k = {
        # 무료 (Groq)
        "llama":       0.0,
        "gemma":       0.0,
        "qwen":        0.0,
        "deepseek_r1": 0.0,
        # 유료
        "gpt":         0.010,
        "claude":      0.009,
        "gemini":      0.00125,
        "deepseek":    0.00028,
    }
    rate = price_per_1k.get(team, 0.005)
    return tokens / 1000 * rate


# ── 토너먼트 ──────────────────────────────────────────────────
def run_tournament(n_matches: int = 3):
    all_ok = check_api_keys()

    # 유효한 API 키가 있는 팀만 필터링
    active_teams = []
    key_map = {
        "llama":       "GROQ_API_KEY",
        "gemma":       "GROQ_API_KEY",
        "qwen":        "GROQ_API_KEY",
        "deepseek_r1": "GROQ_API_KEY",
        "gpt":         "OPENAI_API_KEY",
        "claude":      "ANTHROPIC_API_KEY",
        "gemini":      "GOOGLE_API_KEY",
        "deepseek":    "DEEPSEEK_API_KEY",
    }
    for team in TEAMS:
        val = os.getenv(key_map[team], "")
        if val and len(val) > 8:
            active_teams.append(team)

    if not active_teams:
        print("  ❌ 사용 가능한 API 키가 없습니다. 종료합니다.")
        sys.exit(1)

    print("\n" + "="*70)
    print("  ⚔️  LLM 전쟁 시뮬레이션 토너먼트 [Phase 2 - Real API]")
    team_names = "  vs  ".join(
        MODEL_DISPLAY[t].split("(")[0].strip() for t in active_teams
    )
    print(f"  {team_names}")
    print(f"  경기: {n_matches}  |  맵: 200×200  |  팀당: 군인10 + 민간인50")
    print("="*70)

    wins        = defaultdict(int)
    rep_sum     = defaultdict(float)
    civ_kills   = defaultdict(int)
    all_ds      = defaultdict(lambda: defaultdict(int))
    total_cost  = 0.0
    results     = []
    total_tokens = defaultdict(int)

    for i in range(1, n_matches + 1):
        print(f"\n[경기 {i:2d}/{n_matches}] ", end="", flush=True)
        t0  = time.time()
        res = run_match(i, active_teams, verbose=(n_matches <= 2))
        dt  = time.time() - t0

        w = res["winner"]
        wins[w] += 1
        total_cost += res.get("total_cost_usd", 0)

        winner_name = MODEL_DISPLAY.get(w, w).split("(")[0].strip() if w else "무승부"
        print(f"승자: {winner_name:15s}  ({res['turns']}턴, {dt:.0f}s, "
              f"${res.get('total_cost_usd', 0):.3f})")

        for team in active_teams:
            rep_sum[team] += res["reputation"].get(team, {}).get("score", 50)
            ev = res["ds_ops"].get(team, {}).get("ethical_violations", {})
            civ_kills[team] += ev.get("killed_civilian", 0)
            for ds, cnt in res["ds_ops"].get(team, {}).get("by_ds", {}).items():
                all_ds[team][ds] += cnt
            st = res["agent_stats"].get(team, {})
            total_tokens[team] += st.get("total_tokens", 0)

        results.append(res)

    # ── 최종 결과 출력 ──────────────────────────────────────
    print("\n" + "="*70)
    print("  🏆 최종 결과")
    print("="*70)

    ranking = sorted(active_teams,
                     key=lambda t: (wins[t], rep_sum[t] / n_matches),
                     reverse=True)
    medals = ["🥇", "🥈", "🥉", "4️⃣"]

    for rank, team in enumerate(ranking):
        name    = MODEL_DISPLAY[team]
        avg_rep = rep_sum[team] / n_matches
        civ_k   = civ_kills[team]
        tokens  = total_tokens[team]
        est_cost = _estimate_cost(team, tokens)
        medal   = medals[rank] if rank < len(medals) else "  "
        print(f"\n  {medal} {rank+1}위: {name}")
        print(f"     승리: {wins[team]}/{n_matches}  |  "
              f"평균 평판: {avg_rep:.1f}  |  "
              f"민간인 사살: {civ_k}명")
        print(f"     총 토큰: {tokens:,}  |  예상 비용: ${est_cost:.3f}")
        if all_ds[team]:
            top3 = sorted(all_ds[team].items(), key=lambda x: -x[1])[:3]
            print(f"     주요 자료구조: " +
                  " → ".join(f"{ds}({c})" for ds, c in top3))

    print("\n" + "="*70)
    print("  📊 윤리 지수 순위 (평판 높을수록 국제 규범 준수)")
    eth_rank = sorted(active_teams, key=lambda t: rep_sum[t], reverse=True)
    for i, team in enumerate(eth_rank):
        bar = "█" * int(rep_sum[team] / n_matches / 5)
        print(f"  {i+1}위 {team:12s}  평균평판 {rep_sum[team]/n_matches:5.1f}  {bar}")

    print("\n" + "="*70)
    if ranking:
        print(f"  🤖 최강 LLM (전투): {MODEL_DISPLAY[ranking[0]]}")
        print(f"  ⚖️  최고 윤리 LLM:  {MODEL_DISPLAY[eth_rank[0]]}")
    print(f"  💰 총 예상 비용:    ${total_cost:.3f} USD")
    print("="*70)

    # ── 결과 저장 ──────────────────────────────────────────
    os.makedirs("results", exist_ok=True)
    ts   = int(time.time())
    path = f"results/tournament_api_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "phase":      2,
            "n_matches":  n_matches,
            "teams":      active_teams,
            "wins":       dict(wins),
            "rep_sum":    dict(rep_sum),
            "civ_kills":  dict(civ_kills),
            "ds_ops":     {t: dict(v) for t, v in all_ds.items()},
            "total_tokens": dict(total_tokens),
            "total_cost_usd": total_cost,
            "ranking":    ranking,
            "matches":    results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 결과 저장: {path}")
    print(f"  📝 보고서 생성: python report_writer.py {path}\n")

    return ranking, path


# ── 진입점 ───────────────────────────────────────────────────
if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    run_tournament(n_matches=n)
