"""
tournament.py - 전쟁 시뮬레이션 토너먼트
4팀(Llama/Gemma/Qwen/DeepSeek) × 60유닛(군인10+민간인50)
국제 평판 + 민간인 보호 딜레마 포함
"""

import json, os, sys, time, subprocess, requests
from collections import defaultdict
from battle_env import BattleEnv, TEAMS
from llm_agent  import LLMAgent, OLLAMA_BASE, OLLAMA_CHECK, MODEL_DISPLAY
from data_logger import DSLogger

MODEL_PULL = {
    "llama":    "llama3.1:8b",
    "gemma":    "gemma3:4b",
    "qwen":     "qwen2.5:7b",
    "deepseek": "deepseek-r1:8b",
}


# ── 사전 점검 ──────────────────────────────────────────────────
def check_ollama_and_models():
    print("\n[사전 확인] Ollama 및 모델 상태 점검 중...")
    try:
        requests.get(OLLAMA_BASE, timeout=5)
    except Exception:
        print("  ❌ Ollama 서버 미실행. 시작 메뉴에서 Ollama를 실행하세요.")
        sys.exit(1)

    try:
        resp      = requests.get(OLLAMA_CHECK, timeout=10)
        installed = [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        installed = []

    for team, model in MODEL_PULL.items():
        found = any(model.split(":")[0] in m for m in installed)
        if found:
            print(f"  ✅ {model:25s} 설치됨")
        else:
            print(f"  ⬇️  {model:25s} 다운로드 중...")
            r = subprocess.run(["ollama", "pull", model])
            if r.returncode != 0:
                print(f"  ❌ {model} 다운로드 실패")
                sys.exit(1)
            print(f"  ✅ {model:25s} 완료")

    print("[사전 확인] 모든 모델 준비 완료!\n")


# ── 단일 경기 ─────────────────────────────────────────────────
def run_match(match_id: int, verbose: bool = True) -> dict:
    logger  = DSLogger()
    env     = BattleEnv(max_turns=100, verbose=verbose)
    agents  = {team: LLMAgent(team, logger) for team in TEAMS}

    while True:
        actions_by_team = {}
        for team in TEAMS:
            if (env.rep.is_disqualified(team) or
                    len(env.alive_soldiers(team)) == 0):
                continue
            state   = env.get_state_for_team(team)
            actions = agents[team].decide(state)
            actions_by_team[team] = actions

        done, winner = env.step(actions_by_team)
        if done:
            break

    report     = env.final_report()
    rep_summary = env.rep.summary()
    ds_summary  = logger.summary()

    return {
        "match_id":    match_id,
        "winner":      winner,
        "turns":       report["turns"],
        "teams":       report["teams"],
        "reputation":  rep_summary,
        "ds_ops":      ds_summary,
        "agent_stats": {t: agents[t].stats() for t in TEAMS},
    }


# ── 토너먼트 ──────────────────────────────────────────────────
def run_tournament(n_matches: int = 5):
    print("\n" + "="*70)
    print("  ⚔️  LLM 전쟁 시뮬레이션 토너먼트")
    print("  " + "  vs  ".join(MODEL_DISPLAY[t].split("(")[0].strip()
                                for t in TEAMS))
    print(f"  경기: {n_matches}  |  맵: 200×200  |  팀당: 군인10 + 민간인50")
    print("="*70)

    wins      = defaultdict(int)
    rep_sum   = defaultdict(float)
    civ_kills = defaultdict(int)
    all_ds    = defaultdict(lambda: defaultdict(int))
    results   = []

    for i in range(1, n_matches + 1):
        print(f"\n[경기 {i:2d}/{n_matches}] ", end="", flush=True)
        t0  = time.time()
        res = run_match(i, verbose=(n_matches <= 3))
        dt  = time.time() - t0

        w = res["winner"]
        wins[w] += 1
        print(f"승자: {MODEL_DISPLAY.get(w, w).split('(')[0].strip():15s}  "
              f"({res['turns']}턴, {dt:.0f}s)")

        for team in TEAMS:
            rep_sum[team]   += res["reputation"][team]["score"]
            ev = res["ds_ops"][team].get("ethical_violations", {})
            civ_kills[team] += ev.get("killed_civilian", 0)
            for ds, cnt in res["ds_ops"][team].get("by_ds", {}).items():
                all_ds[team][ds] += cnt

        results.append(res)

    # ── 최종 결과 ──────────────────────────────────
    print("\n" + "="*70)
    print("  🏆 최종 결과")
    print("="*70)

    ranking = sorted(TEAMS,
                     key=lambda t: (wins[t], rep_sum[t]/n_matches),
                     reverse=True)

    medals = ["🥇","🥈","🥉","4️⃣"]
    for rank, team in enumerate(ranking):
        name     = MODEL_DISPLAY[team]
        avg_rep  = rep_sum[team] / n_matches
        civ_k    = civ_kills[team]
        print(f"\n  {medals[rank]} {rank+1}위: {name}")
        print(f"     승리: {wins[team]}/{n_matches}  |  평균 평판: {avg_rep:.1f}  |  민간인 사살: {civ_k}명")
        if all_ds[team]:
            top3 = sorted(all_ds[team].items(), key=lambda x:-x[1])[:3]
            print(f"     주요 자료구조: " +
                  " → ".join(f"{ds}({c})" for ds, c in top3))

    print("\n" + "="*70)
    print("  📊 윤리 지수 순위 (평판 높을수록 국제 규범 준수)")
    eth_rank = sorted(TEAMS, key=lambda t: rep_sum[t], reverse=True)
    for i, team in enumerate(eth_rank):
        bar = "█" * int(rep_sum[team] / n_matches / 5)
        print(f"  {i+1}위 {team:12s}  평균평판 {rep_sum[team]/n_matches:5.1f}  {bar}")

    print("\n" + "="*70)
    print(f"  🤖 최강 LLM (전투): {MODEL_DISPLAY[ranking[0]]}")
    print(f"  ⚖️  최고 윤리 LLM:  {MODEL_DISPLAY[eth_rank[0]]}")
    print("="*70)

    # 결과 저장
    os.makedirs("results", exist_ok=True)
    path = f"results/tournament_{int(time.time())}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "wins":     dict(wins),
            "rep_sum":  dict(rep_sum),
            "civ_kills":dict(civ_kills),
            "ds_ops":   {t: dict(v) for t, v in all_ds.items()},
            "ranking":  ranking,
            "matches":  results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 결과 저장: {path}")
    return ranking


if __name__ == "__main__":
    check_ollama_and_models()
    run_tournament(n_matches=5)
