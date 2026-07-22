import { FormEvent, useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { ApiError, api } from "./api";
import type { JobAnalysis, User, UserProfile } from "./types";

const TOKEN_KEY = "jobops_access_token";

function Landing() {
  return (
    <main className="landing-shell">
      <nav className="topbar">
        <Link className="brand" to="/">
          <span className="brand-mark" aria-hidden="true">J</span>
          JobOps Radar
        </Link>
        <Link className="button button-ghost" to="/auth">로그인</Link>
      </nav>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">EVIDENCE-BASED JOB ANALYSIS</p>
          <h1>공고와 내 경험 사이의<br />간격을 선명하게.</h1>
          <p className="hero-description">
            채용공고와 이력서를 근거 단위로 비교해 일치하는 역량, 부족한 부분,
            다음 준비 순서를 보여드립니다.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/auth?mode=register">무료로 시작하기</Link>
            <a className="text-link" href="#how">분석 방식 보기 <span>→</span></a>
          </div>
          <p className="fine-print">점수는 합격 확률이 아닌 이력서 문서 근거 일치도입니다.</p>
        </div>
        <div className="radar-card" aria-label="분석 결과 예시">
          <div className="radar-card-header">
            <span className="live-dot" /> 분석 완료
            <span className="muted">LLM + server validation</span>
          </div>
          <div className="score-orbit">
            <div className="score-ring"><strong>72</strong><span>match</span></div>
            <span className="orbit-dot orbit-one" />
            <span className="orbit-dot orbit-two" />
          </div>
          <div className="mini-results">
            <div><span className="status-dot good" /><b>FastAPI</b><small>프로젝트 근거 확인</small></div>
            <div><span className="status-dot good" /><b>SQLAlchemy</b><small>구현 근거 확인</small></div>
            <div><span className="status-dot gap" /><b>AWS 운영</b><small>보강이 필요해요</small></div>
          </div>
        </div>
      </section>

      <section className="how-section" id="how">
        <p className="eyebrow">HOW IT WORKS</p>
        <h2>세 단계면 충분합니다.</h2>
        <div className="step-grid">
          <article><span>01</span><h3>이력서 등록</h3><p>Markdown 이력서에서 기술과 프로젝트 근거를 구조화합니다.</p></article>
          <article><span>02</span><h3>공고 입력</h3><p>공개 URL을 넣거나 공고 본문을 직접 붙여넣습니다.</p></article>
          <article><span>03</span><h3>근거 확인</h3><p>점수보다 중요한 일치·부족 역량과 실제 근거를 확인합니다.</p></article>
        </div>
      </section>
    </main>
  );
}

function AuthPage({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">(
    new URLSearchParams(window.location.search).get("mode") === "register" ? "register" : "login",
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") await api.register(email, password);
      const result = await api.login(email, password);
      onAuthenticated(result.access_token);
      navigate("/app");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "인증 요청에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <Link className="brand auth-brand" to="/"><span className="brand-mark">J</span>JobOps Radar</Link>
      <section className="auth-card">
        <div className="auth-intro">
          <p className="eyebrow">YOUR NEXT MOVE</p>
          <h1>{mode === "login" ? "다시 만나 반가워요." : "지원 준비를 시작해볼까요?"}</h1>
          <p>{mode === "login" ? "저장한 프로필과 새로운 공고를 비교하세요." : "먼저 계정을 만들고 이력서 근거를 등록하세요."}</p>
        </div>
        <div className="auth-tabs" role="tablist">
          <button className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setError(""); }}>로그인</button>
          <button className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setError(""); }}>회원가입</button>
        </div>
        <form onSubmit={submit} className="stack-form">
          <label>이메일<input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" /></label>
          <label>비밀번호<input type="password" minLength={mode === "register" ? 12 : 1} required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="12자 이상" autoComplete={mode === "register" ? "new-password" : "current-password"} /></label>
          {error && <div className="alert alert-error" role="alert">{error}</div>}
          <button className="button button-primary button-full" disabled={busy}>{busy ? "처리 중..." : mode === "login" ? "로그인" : "계정 만들기"}</button>
        </form>
        <p className="privacy-note">이력서의 외부 AI 전송은 분석 요청마다 별도로 선택합니다.</p>
      </section>
    </main>
  );
}

const FALLBACK_MESSAGES: Record<string, string> = {
  llm_mock_mode: "현재 기본 분석 모드로 결과를 만들었습니다.",
  external_llm_consent_required: "외부 AI 전송 동의 없이 기본 분석을 사용했습니다.",
  provider_timeout: "AI 응답이 지연되어 기본 분석 결과를 표시합니다.",
  provider_capacity_exhausted: "AI 사용량이 많아 기본 분석 결과를 표시합니다.",
  schema_validation_failed: "AI 결과를 안전하게 검증할 수 없어 기본 분석을 사용했습니다.",
  provider_request_failed: "AI 연결을 사용할 수 없어 기본 분석 결과를 표시합니다.",
};

function Results({ analysis }: { analysis: JobAnalysis }) {
  return (
    <section className="results-panel" aria-labelledby="result-heading">
      <div className="result-summary">
        <div className="result-score"><strong>{analysis.match_score}</strong><span>문서 근거 일치도</span></div>
        <div>
          <p className="eyebrow">ANALYSIS RESULT</p>
          <h2 id="result-heading">공고와 프로필 비교가 끝났어요.</h2>
          <div className="method-row">
            <span className={`method-badge ${analysis.analysis_method}`}>{analysis.analysis_method === "llm" ? "AI 분석" : "기본 분석"}</span>
            <span>{analysis.requirements.length}개 요구사항 · {analysis.matched_skills.length}개 근거 일치</span>
          </div>
        </div>
      </div>

      {analysis.fallback_reason && (
        <div className="alert alert-info">
          {FALLBACK_MESSAGES[analysis.fallback_reason] ?? "AI 분석을 사용할 수 없어 기본 분석 결과를 표시합니다."}
        </div>
      )}

      <div className="result-columns">
        <div className="result-group"><h3>확인된 역량 <span>{analysis.matched_skills.length}</span></h3><div className="chip-list">{analysis.matched_skills.map((skill) => <span className="chip chip-good" key={skill}>✓ {skill}</span>)}</div></div>
        <div className="result-group"><h3>보강할 역량 <span>{analysis.missing_skills.length}</span></h3><div className="chip-list">{analysis.missing_skills.map((skill) => <span className="chip chip-gap" key={skill}>↗ {skill}</span>)}</div></div>
      </div>

      <div className="requirements-list">
        <h3>요구사항별 근거</h3>
        {analysis.requirements.map((item, index) => (
          <details key={`${item.name}-${index}`} className={item.matched ? "requirement matched" : "requirement missing"}>
            <summary><span>{item.matched ? "✓" : "○"}</span><b>{item.name}</b><small>{item.is_required ? "필수" : "관련"} · 중요도 {item.importance}</small></summary>
            <div className="evidence-grid"><div><h4>공고 근거</h4><p>{item.evidence}</p></div><div><h4>내 프로필 근거</h4><p>{item.profile_evidence || "직접 확인된 근거가 없습니다."}</p></div></div>
          </details>
        ))}
      </div>

      {analysis.action_plan.length > 0 && <div className="action-list"><h3>다음 준비 순서</h3>{analysis.action_plan.map((item, index) => <article key={`${item.skill}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><div><b>{item.skill}</b><p>{item.action}</p></div></article>)}</div>}
      <p className="score-disclaimer">이 결과는 이력서에 명시된 문서 근거의 일치도이며 합격 가능성이나 실제 숙련도의 절대 평가가 아닙니다.</p>
    </section>
  );
}

function Dashboard({ token, onLogout }: { token: string; onLogout: () => void }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [resume, setResume] = useState("");
  const [loading, setLoading] = useState(true);
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileError, setProfileError] = useState("");
  const [url, setUrl] = useState("");
  const [content, setContent] = useState("");
  const [consent, setConsent] = useState(false);
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [analysisError, setAnalysisError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      api.me(token),
      api.getProfile(token).catch((error) => {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }),
    ]).then(([me, storedProfile]) => {
      if (!active) return;
      setUser(me);
      setProfile(storedProfile);
      setResume(storedProfile?.resume_markdown ?? "");
    }).catch((error) => {
      if (error instanceof ApiError && error.status === 401) onLogout();
      else setProfileError(error instanceof Error ? error.message : "프로필을 불러오지 못했습니다.");
    }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [token, onLogout]);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setProfileBusy(true);
    setProfileError("");
    try {
      const saved = await api.saveProfile(token, resume);
      setProfile(saved);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "프로필을 저장하지 못했습니다.");
    } finally {
      setProfileBusy(false);
    }
  }

  async function removeProfile() {
    if (!window.confirm("저장된 이력서 원문과 구조화 프로필을 삭제할까요?")) return;
    setProfileBusy(true);
    try {
      await api.deleteProfile(token);
      setProfile(null);
      setResume("");
      setAnalysis(null);
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "프로필을 삭제하지 못했습니다.");
    } finally {
      setProfileBusy(false);
    }
  }

  async function runAnalysis(event: FormEvent) {
    event.preventDefault();
    if (!profile) { setAnalysisError("먼저 이력서를 등록해 주세요."); return; }
    if (!url.trim() && !content.trim()) { setAnalysisError("채용공고 URL 또는 본문을 입력해 주세요."); return; }
    setAnalysisBusy(true);
    setAnalysisError("");
    setAnalysis(null);
    try {
      const result = await api.analyze(token, {
        source_url: url.trim() || undefined,
        content: content.trim() || undefined,
        consent_to_external_llm: consent,
      });
      setAnalysis(result);
      window.setTimeout(() => document.getElementById("analysis-result")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (error) {
      if (error instanceof ApiError && error.status === 422) setAnalysisError(`${error.message} 공고 본문을 직접 붙여넣어 보세요.`);
      else setAnalysisError(error instanceof Error ? error.message : "분석에 실패했습니다.");
    } finally {
      setAnalysisBusy(false);
    }
  }

  if (loading) return <main className="loading-screen"><div className="spinner" /><p>JobOps를 준비하고 있어요.</p></main>;

  return (
    <main className="app-shell">
      <header className="app-header"><Link className="brand" to="/"><span className="brand-mark">J</span>JobOps Radar</Link><div className="user-menu"><span>{user?.email}</span><button className="text-button" onClick={onLogout}>로그아웃</button></div></header>
      <section className="dashboard-intro"><div><p className="eyebrow">WORKSPACE</p><h1>오늘의 지원 준비를<br />근거부터 시작하세요.</h1></div><div className={`profile-status ${profile ? "ready" : "empty"}`}><span>{profile ? "✓" : "!"}</span><div><b>{profile ? "프로필 준비 완료" : "프로필이 필요해요"}</b><small>{profile ? `${profile.skills.length}개 기술 · ${profile.projects.length}개 프로젝트` : "이력서를 먼저 등록하세요"}</small></div></div></section>

      <div className="workspace-grid">
        <section className="panel profile-panel">
          <div className="panel-heading"><div><span className="panel-number">01</span><h2>내 프로필</h2></div>{profile && <button className="text-button danger" disabled={profileBusy} onClick={removeProfile}>프로필 삭제</button>}</div>
          <form onSubmit={saveProfile} className="stack-form"><label>Markdown 이력서<textarea rows={13} value={resume} onChange={(event) => setResume(event.target.value)} placeholder={'## SUMMARY\nPython backend developer...\n\n## SKILLS\n- Python\n- FastAPI'} required /></label>{profileError && <div className="alert alert-error">{profileError}</div>}<button className="button button-dark" disabled={profileBusy}>{profileBusy ? "저장 중..." : profile ? "프로필 업데이트" : "프로필 저장"}</button></form>
          {profile && <div className="profile-preview"><h3>구조화된 프로필</h3>{profile.summary && <p>{profile.summary}</p>}<div className="preview-block"><span>SKILLS</span><div className="chip-list">{profile.skills.map((skill) => <span className="chip" key={skill}>{skill}</span>)}</div></div><div className="preview-block"><span>PROJECTS</span>{profile.projects.map((project) => <p key={project}>— {project}</p>)}</div></div>}
        </section>

        <section className="panel analysis-panel">
          <div className="panel-heading"><div><span className="panel-number">02</span><h2>공고 분석</h2></div></div>
          <form onSubmit={runAnalysis} className="stack-form"><label>채용공고 URL<input type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://company.com/jobs/backend" /></label><div className="or-divider"><span>또는</span></div><label>공고 본문<textarea rows={10} value={content} onChange={(event) => setContent(event.target.value)} placeholder="URL을 가져올 수 없다면 공고 내용을 붙여넣으세요." /></label><label className="consent-row"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /><span><b>외부 AI 분석 사용</b><small>공고와 이력서 section이 NVIDIA LLM으로 전송됩니다.</small></span></label>{analysisError && <div className="alert alert-error" role="alert">{analysisError}</div>}<button className="button button-primary button-full" disabled={analysisBusy || !profile}>{analysisBusy ? "공고와 프로필을 비교하는 중..." : "분석 시작"}</button>{analysisBusy && <p className="progress-note" aria-live="polite"><span className="spinner small" /> AI 응답에 최대 약 1분이 걸릴 수 있습니다.</p>}</form>
        </section>
      </div>
      {analysis && <div id="analysis-result"><Results analysis={analysis} /></div>}
    </main>
  );
}

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || "");

  function authenticate(nextToken: string) {
    sessionStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
  }

  function logout() {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken("");
  }

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={token ? <Navigate to="/app" replace /> : <AuthPage onAuthenticated={authenticate} />} />
      <Route path="/app" element={token ? <Dashboard token={token} onLogout={logout} /> : <Navigate to="/auth" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
