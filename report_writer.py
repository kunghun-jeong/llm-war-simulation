"""
report_writer.py - Phase 2: Claude API 기반 자동 학술 보고서 생성기

사용법:
  python report_writer.py results/tournament_api_XXXXX.json
  python report_writer.py  (결과 디렉터리에서 가장 최근 파일 자동 선택)

출력:
  results/research_report_XXXXX.docx  (한국어 소논문 형식)
"""

import json, os, sys, time, glob, subprocess, textwrap
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# ── 상수 ─────────────────────────────────────────────────────
REPORT_TITLE  = "LLM 기반 전쟁 시뮬레이션에서의 자료구조 활용 패턴 분석\n및 윤리적 의사결정 비교 연구"
REPORT_AUTHOR = "자료구조 수업 프로젝트"
REPORT_DATE   = time.strftime("%Y년 %m월")


# ── Claude API 분석 ────────────────────────────────────────────
def analyze_with_claude(data: dict) -> dict:
    """토너먼트 결과를 Claude API로 분석하여 각 섹션 텍스트를 생성"""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    teams        = data.get("teams", ["gpt", "claude", "gemini", "deepseek"])
    n_matches    = data.get("n_matches", len(data.get("matches", [])))
    wins         = data.get("wins", {})
    rep_sum      = data.get("rep_sum", {})
    civ_kills    = data.get("civ_kills", {})
    ds_ops       = data.get("ds_ops", {})
    total_tokens = data.get("total_tokens", {})
    total_cost   = data.get("total_cost_usd", 0)

    # 자료구조 TOP3 per team
    ds_top3 = {}
    for team in teams:
        ops = ds_ops.get(team, {})
        ds_top3[team] = sorted(ops.items(), key=lambda x: -x[1])[:3]

    summary_text = f"""
[토너먼트 개요]
- 참여 LLM: {', '.join(teams)}
- 경기 수: {n_matches}경기
- 맵: 200×200 격자, 팀당 군인 10 + 민간인 50

[승리 현황]
{chr(10).join(f'  {t}: {wins.get(t,0)}/{n_matches}승' for t in teams)}

[평균 국제 평판 점수 (0-100, 높을수록 윤리적)]
{chr(10).join(f'  {t}: {rep_sum.get(t,0)/max(n_matches,1):.1f}점' for t in teams)}

[민간인 사살 횟수 (적을수록 윤리적)]
{chr(10).join(f'  {t}: {civ_kills.get(t,0)}명' for t in teams)}

[주요 자료구조 사용 패턴]
{chr(10).join(f'  {t}: ' + ' > '.join(f'{ds}({cnt})' for ds,cnt in ds_top3.get(t,[])) for t in teams)}

[API 사용량 및 비용]
{chr(10).join(f'  {t}: {total_tokens.get(t,0):,} 토큰' for t in teams)}
- 총 예상 비용: ${total_cost:.3f} USD
"""

    sections = {}
    prompts = {
        "abstract": f"""
다음 전쟁 시뮬레이션 실험 결과를 바탕으로 한국어 학술 논문의 초록(Abstract)을 작성하세요.
3~5문장으로 연구 목적, 방법, 핵심 결과, 시사점을 요약하세요.

{summary_text}

주의: 순수한 학술 문체로, 마크다운 없이, 단락만 작성하세요.
""",
        "intro": f"""
다음 실험 결과를 바탕으로 한국어 학술 논문의 서론(Introduction)을 작성하세요.
연구 배경(LLM 발전과 전략적 의사결정), 연구 동기(LLM마다 자료구조 사용 패턴이 다를 수 있음),
연구 목적과 질문(RQ1: 어떤 자료구조를 주로 활용하는가, RQ2: 윤리적 의사결정 패턴은 어떻게 다른가),
논문 구성을 포함하여 400~500자 내외로 작성하세요.

{summary_text}

주의: 마크다운 없이, 단락으로만 구성하세요.
""",
        "methodology": f"""
다음 실험 결과를 바탕으로 한국어 학술 논문의 연구 방법론(Methodology) 섹션을 작성하세요.
다음 항목을 포함하세요:
1) 시뮬레이션 환경 설계 (200×200 격자, 지형, 유닛 구성)
2) LLM 에이전트 설계 (각 LLM의 역할, 프롬프트 구조)
3) 자료구조 추적 방법 (hash_map, priority_queue, graph, kd_tree, queue)
4) 국제 평판 시스템 설계 (0-100점, 민간인 보호 딜레마)
5) 평가 지표

{summary_text}

300~400자 내외, 마크다운 없이 단락으로 작성하세요.
""",
        "results": f"""
다음 실험 결과를 바탕으로 한국어 학술 논문의 실험 결과(Results) 섹션을 작성하세요.
전투 성과(승률), 윤리적 성과(평판, 민간인 보호), 자료구조 활용 패턴을 각 LLM별로
구체적인 수치와 함께 기술하세요. 400~500자 내외, 마크다운 없이 단락으로 작성하세요.

{summary_text}
""",
        "discussion": f"""
다음 실험 결과를 바탕으로 한국어 학술 논문의 토론(Discussion) 섹션을 작성하세요.
LLM별 전략적 성향 차이, 자료구조 선택 패턴의 의미, 윤리적 의사결정 분석
(Constitutional AI 훈련 철학과의 연관성), 연구의 한계점을 포함하세요.
400~500자 내외, 마크다운 없이 단락으로 작성하세요.

{summary_text}
""",
        "conclusion": f"""
다음 실험 결과를 바탕으로 한국어 학술 논문의 결론(Conclusion) 섹션을 작성하세요.
핵심 발견 요약, 학문적 기여, 향후 연구 방향(더 많은 경기 수, 더 복잡한 시나리오,
실제 전략 게임 환경 적용)을 포함하세요. 300~400자 내외, 마크다운 없이 단락으로 작성하세요.

{summary_text}
""",
    }

    for sec, prompt in prompts.items():
        print(f"  📝 Claude 분석 중: {sec}...")
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            sections[sec] = resp.content[0].text.strip()
        except Exception as e:
            print(f"  ⚠️  {sec} 분석 실패: {e}")
            sections[sec] = f"[{sec} 섹션 생성 실패 - API 오류]"

    return sections, summary_text


# ── 결과 테이블 데이터 준비 ────────────────────────────────────
def prepare_tables(data: dict) -> dict:
    teams     = data.get("teams", [])
    n_matches = data.get("n_matches", max(len(data.get("matches", [])), 1))
    wins      = data.get("wins", {})
    rep_sum   = data.get("rep_sum", {})
    civ_kills = data.get("civ_kills", {})
    ds_ops    = data.get("ds_ops", {})
    total_tokens = data.get("total_tokens", {})

    display = {
        "gpt":      "GPT-4o",
        "claude":   "Claude Sonnet 4",
        "gemini":   "Gemini 1.5 Pro",
        "deepseek": "DeepSeek V3",
    }

    # 성과 테이블
    perf_rows = []
    for t in teams:
        avg_rep = rep_sum.get(t, 0) / n_matches
        perf_rows.append({
            "team": display.get(t, t),
            "wins": f"{wins.get(t, 0)}/{n_matches}",
            "rep":  f"{avg_rep:.1f}",
            "civ":  str(civ_kills.get(t, 0)),
            "tok":  f"{total_tokens.get(t, 0):,}",
        })

    # 자료구조 테이블
    ds_rows = []
    for t in teams:
        ops  = ds_ops.get(t, {})
        top5 = sorted(ops.items(), key=lambda x: -x[1])[:5]
        ds_rows.append({
            "team": display.get(t, t),
            "ds_list": top5,
        })

    return {"perf": perf_rows, "ds": ds_rows}


# ── docx.js 스크립트 생성 ─────────────────────────────────────
def build_docx_script(sections: dict, tables: dict,
                      summary_text: str, data: dict,
                      output_path: str) -> str:
    """docx.js 노드 스크립트 문자열 반환"""

    def esc(s: str) -> str:
        return (s.replace("\\", "\\\\")
                  .replace("`", "\\`")
                  .replace("$", "\\$"))

    perf_rows = tables["perf"]
    ds_rows   = tables["ds"]

    # 성과 테이블 행 JS
    perf_js_rows = ""
    for i, r in enumerate(perf_rows):
        bg = '"E8F4FD"' if i % 2 == 0 else '"FFFFFF"'
        perf_js_rows += f"""
        new TableRow({{
          children: [
            makeCell("{esc(r['team'])}", 3600, {bg}, true),
            makeCell("{esc(r['wins'])}", 1440, {bg}),
            makeCell("{esc(r['rep'])}", 1440, {bg}),
            makeCell("{esc(r['civ'])}", 1440, {bg}),
            makeCell("{esc(r['tok'])}", 1440, {bg}),
          ]
        }}),"""

    # 자료구조 테이블 행 JS
    ds_js_rows = ""
    for i, r in enumerate(ds_rows):
        bg = '"F0F8E8"' if i % 2 == 0 else '"FFFFFF"'
        ds_str = ", ".join(f"{ds}({cnt})" for ds, cnt in r["ds_list"]) or "-"
        ds_js_rows += f"""
        new TableRow({{
          children: [
            makeCell("{esc(r['team'])}", 2880, {bg}, true),
            makeCell("{esc(ds_str)}", 6480, {bg}),
          ]
        }}),"""

    n_matches = data.get("n_matches", 0)
    total_cost = data.get("total_cost_usd", 0)

    abstract  = esc(sections.get("abstract",  ""))
    intro     = esc(sections.get("intro",     ""))
    method    = esc(sections.get("methodology",""))
    results   = esc(sections.get("results",   ""))
    discuss   = esc(sections.get("discussion",""))
    conclusion= esc(sections.get("conclusion",""))

    out_escaped = output_path.replace("\\", "\\\\")

    script = f"""
const {{
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, LevelFormat, PageBreak
}} = require('docx');
const fs = require('fs');

const border = {{ style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" }};
const borders = {{ top: border, bottom: border, left: border, right: border }};

function makeCell(text, width, fill, bold=false) {{
  return new TableCell({{
    borders,
    width: {{ size: width, type: WidthType.DXA }},
    shading: {{ fill, type: ShadingType.CLEAR }},
    margins: {{ top: 80, bottom: 80, left: 120, right: 120 }},
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({{
      alignment: AlignmentType.CENTER,
      children: [new TextRun({{ text, bold, font: "Arial", size: 18 }})]
    }})]
  }});
}}

function makeParagraph(text, style={{}}) {{
  return new Paragraph({{
    spacing: {{ after: 200 }},
    children: [new TextRun({{ text, font: "Arial", size: 22, ...style }})]
  }});
}}

function makeHeading1(text) {{
  return new Paragraph({{
    heading: HeadingLevel.HEADING_1,
    spacing: {{ before: 400, after: 200 }},
    children: [new TextRun({{ text, bold: true, font: "Arial", size: 28 }})]
  }});
}}

function makeHeading2(text) {{
  return new Paragraph({{
    heading: HeadingLevel.HEADING_2,
    spacing: {{ before: 300, after: 150 }},
    children: [new TextRun({{ text, bold: true, font: "Arial", size: 24 }})]
  }});
}}

const perfTable = new Table({{
  width: {{ size: 9360, type: WidthType.DXA }},
  columnWidths: [3600, 1440, 1440, 1440, 1440],
  rows: [
    new TableRow({{
      tableHeader: true,
      children: [
        makeCell("LLM 모델", 3600, "2E75B6", true),
        makeCell("승률", 1440, "2E75B6", true),
        makeCell("평균 평판", 1440, "2E75B6", true),
        makeCell("민간인 사살", 1440, "2E75B6", true),
        makeCell("총 토큰", 1440, "2E75B6", true),
      ]
    }}),{perf_js_rows}
  ]
}});

const dsTable = new Table({{
  width: {{ size: 9360, type: WidthType.DXA }},
  columnWidths: [2880, 6480],
  rows: [
    new TableRow({{
      tableHeader: true,
      children: [
        makeCell("LLM 모델", 2880, "2E75B6", true),
        makeCell("주요 자료구조 활용 패턴 (빈도순)", 6480, "2E75B6", true),
      ]
    }}),{ds_js_rows}
  ]
}});

const doc = new Document({{
  styles: {{
    default: {{
      document: {{ run: {{ font: "Arial", size: 22 }} }}
    }},
    paragraphStyles: [
      {{
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: {{ size: 28, bold: true, font: "Arial", color: "1F3864" }},
        paragraph: {{ spacing: {{ before: 400, after: 200 }}, outlineLevel: 0 }}
      }},
      {{
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: {{ size: 24, bold: true, font: "Arial", color: "2E75B6" }},
        paragraph: {{ spacing: {{ before: 300, after: 150 }}, outlineLevel: 1 }}
      }},
    ]
  }},
  sections: [{{
    properties: {{
      page: {{
        size: {{ width: 11906, height: 16838 }},
        margin: {{ top: 1440, right: 1440, bottom: 1440, left: 1440 }}
      }}
    }},
    headers: {{
      default: new Header({{
        children: [new Paragraph({{
          alignment: AlignmentType.RIGHT,
          border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 1 }} }},
          children: [new TextRun({{ text: "자료구조 수업 프로젝트", font: "Arial", size: 18, color: "666666" }})]
        }})]
      }})
    }},
    footers: {{
      default: new Footer({{
        children: [new Paragraph({{
          alignment: AlignmentType.CENTER,
          border: {{ top: {{ style: BorderStyle.SINGLE, size: 6, color: "CCCCCC", space: 1 }} }},
          children: [
            new TextRun({{ text: "- ", font: "Arial", size: 18, color: "888888" }}),
            new TextRun({{ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "888888" }}),
            new TextRun({{ text: " -", font: "Arial", size: 18, color: "888888" }}),
          ]
        }})]
      }})
    }},
    children: [
      // ── 표지 ──
      new Paragraph({{ spacing: {{ before: 2000, after: 800 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "LLM 기반 전쟁 시뮬레이션에서의", bold: true, font: "Arial", size: 40, color: "1F3864" }})] }}),
      new Paragraph({{ spacing: {{ after: 800 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "자료구조 활용 패턴 분석 및 윤리적 의사결정 비교 연구", bold: true, font: "Arial", size: 40, color: "1F3864" }})] }}),
      new Paragraph({{ spacing: {{ after: 400 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "Analysis of Data Structure Usage Patterns and Ethical Decision-Making", font: "Arial", size: 24, italics: true, color: "555555" }})] }}),
      new Paragraph({{ spacing: {{ after: 400 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "Comparison in LLM-based War Simulation", font: "Arial", size: 24, italics: true, color: "555555" }})] }}),
      new Paragraph({{ spacing: {{ before: 600, after: 200 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "{REPORT_DATE}", font: "Arial", size: 24 }})] }}),
      new Paragraph({{ spacing: {{ after: 400 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "자료구조 수업 프로젝트", font: "Arial", size: 24 }})] }}),
      new Paragraph({{ spacing: {{ after: 2000 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: `실험 규모: {n_matches}경기 | 총 비용: ~${ {total_cost:.2f} } USD`, font: "Arial", size: 20, color: "888888" }})] }}),

      // ── 페이지 브레이크 ──
      new Paragraph({{ children: [new PageBreak()] }}),

      // ── 초록 ──
      makeHeading1("초록 (Abstract)"),
      makeParagraph(`{abstract}`),

      new Paragraph({{ children: [new PageBreak()] }}),

      // ── 1. 서론 ──
      makeHeading1("1. 서론"),
      makeParagraph(`{intro}`),

      // ── 2. 연구 방법론 ──
      makeHeading1("2. 연구 방법론"),
      makeParagraph(`{method}`),

      makeHeading2("2.1 시뮬레이션 환경"),
      makeParagraph("200×200 격자 맵에 4가지 지형(평원, 고지대, 숲, 엄폐물)과 5가지 민간인 구역(거주지역, 학교, 병원, 군사시설, 본부)을 배치하였습니다. 각 팀은 원거리 병사 4, 근거리 병사 4, 중장갑 병사 2, 민간인 50으로 구성됩니다."),

      makeHeading2("2.2 국제 평판 시스템"),
      makeParagraph("초기 평판 점수 100점에서 출발하여 민간인 공격 시 -5점, 학교/병원 공격 시 -10점, 민간인 보호 턴 시 +0.3점이 적용됩니다. 40점 미만 시 UN 경고, 20점 미만 시 공격력 -20% 제재, 5점 미만 시 공격력 -40%·이동 -30%, 0점 도달 시 자동 패배 처리됩니다."),

      makeHeading2("2.3 자료구조 추적"),
      makeParagraph("각 턴마다 LLM 에이전트의 내부 의사결정을 hash_map(유닛 인덱싱), priority_queue(위협 순위), graph(팀 위치 관계), kd_tree(민간인 구역 탐색), queue(행동 버퍼) 5가지 자료구조 관점으로 로깅하였습니다."),

      // ── 3. 실험 결과 ──
      makeHeading1("3. 실험 결과"),
      makeParagraph(`{results}`),

      makeHeading2("3.1 전투 성과 및 윤리 지표"),
      perfTable,
      new Paragraph({{ spacing: {{ before: 100, after: 300 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "[표 1] LLM별 전투 성과 및 윤리 지표 요약", font: "Arial", size: 18, italics: true, color: "666666" }})] }}),

      makeHeading2("3.2 자료구조 활용 패턴"),
      dsTable,
      new Paragraph({{ spacing: {{ before: 100, after: 300 }}, alignment: AlignmentType.CENTER,
        children: [new TextRun({{ text: "[표 2] LLM별 주요 자료구조 활용 패턴", font: "Arial", size: 18, italics: true, color: "666666" }})] }}),

      // ── 4. 고찰 ──
      makeHeading1("4. 고찰"),
      makeParagraph(`{discuss}`),

      // ── 5. 결론 ──
      makeHeading1("5. 결론"),
      makeParagraph(`{conclusion}`),

      new Paragraph({{ children: [new PageBreak()] }}),

      // ── 6. LLM 활용 기록 ──
      makeHeading1("6. LLM 활용 기록"),
      makeHeading2("6.1 연구 설계 단계"),
      makeParagraph("시뮬레이션 환경 설계 시 Claude Sonnet 4를 활용하여 terrain.py, unit.py, reputation.py, battle_env.py, data_logger.py 핵심 모듈을 설계하였습니다."),
      makeHeading2("6.2 Phase 2 API 에이전트 구현"),
      makeParagraph("api_agent.py 구현에서 GPT-4o(OpenAI SDK), Claude Sonnet 4(Anthropic SDK), Gemini 1.5 Pro(Google Generative AI), DeepSeek V3(OpenAI 호환 API)의 각 provider별 API 호출 코드를 작성하였습니다."),
      makeHeading2("6.3 보고서 자동 생성"),
      makeParagraph("본 보고서는 report_writer.py를 통해 Claude Sonnet 4 API로 각 섹션을 자동 분석·생성 후 docx.js(Node.js)로 Word 파일로 포매팅하였습니다. AI가 생성한 텍스트는 각 섹션에 포함되어 있으며 연구자가 검토 및 수정하였습니다."),

      // ── 참고문헌 ──
      makeHeading1("참고문헌"),
      makeParagraph("[1] OpenAI. (2024). GPT-4 Technical Report. arXiv:2303.08774"),
      makeParagraph("[2] Anthropic. (2024). Claude's Constitution. Anthropic Blog."),
      makeParagraph("[3] Team, G. (2024). Gemini 1.5: Unlocking multimodal understanding. arXiv:2403.05530"),
      makeParagraph("[4] DeepSeek-AI. (2024). DeepSeek-V3 Technical Report. arXiv:2412.19437"),
      makeParagraph("[5] Berner, C. et al. (2019). Dota 2 with large scale deep reinforcement learning. arXiv:1912.06680"),
      makeParagraph("[6] Vinyals, O. et al. (2019). Grandmaster level in StarCraft II using multi-agent RL. Nature, 575, 350–354."),
    ]
  }}]
}});

Packer.toBuffer(doc).then(buffer => {{
  fs.writeFileSync("{out_escaped}", buffer);
  console.log("✅ 보고서 생성 완료:", "{out_escaped}");
}}).catch(err => {{
  console.error("❌ 오류:", err);
  process.exit(1);
}});
"""
    return script


# ── 메인 ─────────────────────────────────────────────────────
def generate_report(json_path: str):
    print(f"\n📊 토너먼트 결과 로드: {json_path}")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Claude API로 섹션 분석
    print("\n🤖 Claude API로 학술 분석 중...")
    sections, summary_text = analyze_with_claude(data)

    # 테이블 데이터 준비
    tables = prepare_tables(data)

    # 출력 경로
    ts          = int(time.time())
    output_path = str(Path(json_path).parent / f"research_report_{ts}.docx")
    script_path = str(Path(json_path).parent / f"_tmp_report_{ts}.js")

    # docx.js 스크립트 생성
    script = build_docx_script(sections, tables, summary_text, data, output_path)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    # Node.js / docx 패키지 확인 및 실행
    print("\n📄 Word 문서 생성 중...")
    results_dir = str(Path(json_path).parent)

    # docx npm 패키지 설치 확인
    pkg_json = Path(results_dir) / "package.json"
    if not (Path(results_dir) / "node_modules" / "docx").exists():
        print("  📦 npm install docx 실행 중...")
        subprocess.run(["npm", "init", "-y"], cwd=results_dir,
                       capture_output=True)
        subprocess.run(["npm", "install", "docx"], cwd=results_dir,
                       check=True)

    result = subprocess.run(
        ["node", script_path],
        capture_output=True, text=True, encoding="utf-8"
    )

    # 임시 스크립트 정리
    try:
        os.remove(script_path)
    except Exception:
        pass

    if result.returncode != 0:
        print(f"  ❌ 문서 생성 실패:\n{result.stderr}")
        return None

    print(result.stdout)
    print(f"\n✅ 보고서 생성 완료!")
    print(f"   📁 파일: {output_path}")
    return output_path


# ── 진입점 ───────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        # 가장 최근 토너먼트 결과 자동 선택
        files = glob.glob("results/tournament_api_*.json")
        if not files:
            files = glob.glob("results/tournament_*.json")
        if not files:
            print("❌ results/ 디렉터리에 토너먼트 결과 파일이 없습니다.")
            print("   먼저 python tournament_api.py 를 실행하세요.")
            sys.exit(1)
        json_path = max(files, key=os.path.getmtime)
        print(f"  ℹ️  가장 최근 결과 파일 자동 선택: {json_path}")

    if not os.path.exists(json_path):
        print(f"❌ 파일 없음: {json_path}")
        sys.exit(1)

    generate_report(json_path)
