"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Run = {
  id: string; workspace: string; prompt: string; status: string; mode: string;
  summary: string; logs: { type: string; tool?: string; ok?: boolean; message?: string; error?: string }[];
  changed_files: string[]; created_at: string;
};
type Session = { access_token: string; agency: { name: string; slug: string }; user: { full_name: string; email: string }; role: string };

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [token, setToken] = useState("");
  const [workspace, setWorkspace] = useState("my-first-project");
  const [prompt, setPrompt] = useState("");
  const [runs, setRuns] = useState<Run[]>([]);
  const [active, setActive] = useState<Run | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [register, setRegister] = useState(false);
  const [language, setLanguage] = useState<"ar" | "en">("ar");
  const [form, setForm] = useState({ agency_name: "", agency_slug: "", full_name: "", email: "", password: "" });
  const ar = language === "ar";
  const copy = useMemo(() => ar ? {
    eyebrow:"مهندس البرمجيات الشخصي", title:"حوّل فكرتك إلى برنامج حقيقي.",
    subtitle:"اكتب المطلوب. ATLAS يفحص مساحة العمل، يخطط، يكتب الملفات، ويعرض لك ما أنجزه.",
    workspace:"اسم مساحة المشروع", task:"ماذا تريد أن نبني؟", placeholder:"مثال: ابنِ لوحة تحكم لإدارة المخزون باستخدام React وFastAPI...",
    run:"ابدأ التنفيذ", running:"جاري التنفيذ...", history:"سجل التنفيذ", latest:"تفاصيل آخر مهمة",
    login:"تسجيل الدخول", create:"إنشاء مساحة جديدة", email:"البريد الإلكتروني", password:"كلمة المرور",
    agency:"اسم الشركة / مساحة العمل", slug:"رابط الشركة (بالإنجليزية)", fullname:"الاسم بالكامل",
    sign:"دخول", register:"إنشاء الحساب", noAccount:"ليس لديك حساب؟ أنشئ مساحة جديدة", haveAccount:"لديك حساب؟ سجل الدخول",
    logout:"تسجيل الخروج", noRuns:"لا توجد مهام بعد", changed:"الملفات التي تغيرت", logs:"سجل الأدوات",
    mock:"وضع تجريبي آمن", live:"نموذج ذكاء اصطناعي متصل", status:"الحالة", files:"ملفات",
    needs:"أضف إعدادات نموذج الذكاء الاصطناعي في الخادم لتفعيل البرمجة الحقيقية. الوضع الحالي لا يغيّر الملفات.",
    error:"حدث خطأ. تحقق من الاتصال أو بيانات الدخول."
  } : {
    eyebrow:"PERSONAL AI SOFTWARE ENGINEER", title:"Turn your idea into working software.",
    subtitle:"Describe the task. ATLAS inspects the workspace, plans, edits files and reports what it completed.",
    workspace:"Project workspace", task:"What should we build?", placeholder:"Example: Build an inventory dashboard with React and FastAPI...",
    run:"Start building", running:"Working...", history:"Run history", latest:"Latest task details",
    login:"Sign in", create:"Create a workspace", email:"Email address", password:"Password",
    agency:"Company / workspace name", slug:"Workspace URL slug", fullname:"Full name",
    sign:"Sign in", register:"Create account", noAccount:"New here? Create a workspace", haveAccount:"Already registered? Sign in",
    logout:"Sign out", noRuns:"No tasks yet", changed:"Changed files", logs:"Tool activity",
    mock:"Safe mock mode", live:"Live AI model", status:"Status", files:"Files",
    needs:"Configure the model provider on the server to enable real coding. Mock mode does not change files.",
    error:"Something went wrong. Check the connection or credentials."
  }, [ar]);

  useEffect(() => {
    const saved = window.localStorage.getItem("atlas_session");
    if (saved) {
      try { const parsed = JSON.parse(saved) as { token: string; session: Session }; setToken(parsed.token); setSession(parsed.session); }
      catch { window.localStorage.removeItem("atlas_session"); }
    }
  }, []);

  useEffect(() => {
    if (token) void loadRuns(token);
  }, [token]);

  async function loadRuns(auth: string) {
    try {
      const response = await fetch("/api/engineering/runs", { headers: { Authorization: `Bearer ${auth}` } });
      if (response.ok) setRuns(await response.json());
    } catch { /* The API may be starting; the page remains usable. */ }
  }

  async function authenticate(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const endpoint = register ? "/api/auth/register-agency" : "/api/auth/login";
      const payload = register ? form : { agency_slug: form.agency_slug, email: form.email, password: form.password };
      const response = await fetch(endpoint, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || copy.error);
      const next: Session = data;
      setSession(next); setToken(data.access_token);
      window.localStorage.setItem("atlas_session", JSON.stringify({ token:data.access_token, session:next }));
    } catch (e) { setError(e instanceof Error ? e.message : copy.error); }
    finally { setBusy(false); }
  }

  async function startRun(event: FormEvent) {
    event.preventDefault(); if (!token || !prompt.trim()) return;
    setBusy(true); setError(""); setActive(null);
    try {
      const response = await fetch("/api/engineering/runs", {
        method:"POST", headers:{"Content-Type":"application/json", Authorization:`Bearer ${token}`},
        body:JSON.stringify({ workspace, prompt, max_steps:12 })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || copy.error);
      setActive(data); setRuns(old => [data, ...old.filter(item => item.id !== data.id)]); setPrompt("");
    } catch (e) { setError(e instanceof Error ? e.message : copy.error); }
    finally { setBusy(false); }
  }

  function signOut() {
    window.localStorage.removeItem("atlas_session"); setSession(null); setToken(""); setRuns([]); setActive(null);
  }

  return <main className="shell">
    <header className="topbar">
      <a className="brand" href="#"><span className="brand-mark">A</span><span>ATLAS<span className="brand-ai">.AI</span><small>SOFTWARE ENGINEER</small></span></a>
      <div className="top-actions"><span className="system-pill"><i /> SYSTEM READY</span><button className="lang" onClick={() => setLanguage(ar ? "en" : "ar")}>{ar ? "EN" : "عربي"}</button>{session && <button className="ghost" onClick={signOut}>{copy.logout}</button>}</div>
    </header>

    {!session ? <section className="auth-layout">
      <div className="hero-copy"><span className="eyebrow">{copy.eyebrow}</span><h1>{copy.title}</h1><p>{copy.subtitle}</p>
        <div className="feature-row"><span>01 / PLAN</span><span>02 / BUILD</span><span>03 / VERIFY</span></div>
      </div>
      <form className="auth-card" onSubmit={authenticate}>
        <div className="card-kicker">ATLAS WORKSPACE</div><h2>{register ? copy.create : copy.login}</h2>
        {register && <><label>{copy.agency}<input required value={form.agency_name} onChange={e=>setForm({...form,agency_name:e.target.value})}/></label><label>{copy.slug}<input required value={form.agency_slug} onChange={e=>setForm({...form,agency_slug:e.target.value.toLowerCase().replace(/[^a-z0-9-]/g,"")})}/></label><label>{copy.fullname}<input required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/></label></>}
        {!register && <label>{copy.agency}<input required value={form.agency_slug} onChange={e=>setForm({...form,agency_slug:e.target.value})} placeholder="my-workspace"/></label>}
        <label>{copy.email}<input type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label>
        <label>{copy.password}<input type="password" minLength={register ? 12 : 1} required value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label>
        {error && <p className="error">{error}</p>}
        <button className="primary wide" disabled={busy}>{busy ? "..." : register ? copy.register : copy.sign}<span>↗</span></button>
        <button type="button" className="switch" onClick={()=>{setRegister(!register);setError("");}}>{register ? copy.haveAccount : copy.noAccount}</button>
      </form>
    </section> : <section className="app-layout">
      <div className="welcome-row"><div><span className="eyebrow">{copy.eyebrow}</span><h1>{ar ? `أهلاً، ${session.user.full_name}` : `Welcome, ${session.user.full_name}`}</h1><p>{session.agency.name} · {session.role}</p></div><div className="connection"><i /> API CONNECTED</div></div>
      <div className="workspace-grid">
        <section className="composer panel">
          <div className="panel-head"><div><span className="card-kicker">NEW ENGINEERING TASK</span><h2>{ar ? "ابدأ مشروعك التالي" : "Start your next project"}</h2></div><span className="spark">✳</span></div>
          <form onSubmit={startRun}>
            <label>{copy.workspace}<input value={workspace} onChange={e=>setWorkspace(e.target.value)} pattern="[a-zA-Z0-9][a-zA-Z0-9._-]*" required/></label>
            <label>{copy.task}<textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder={copy.placeholder} rows={7} required minLength={8}/></label>
            {error && <p className="error">{error}</p>}
            <div className="composer-footer"><span className="safe-note">⌁ HUMAN CONTROL · SAFE WORKSPACE</span><button className="primary" disabled={busy || prompt.trim().length < 8}>{busy ? copy.running : copy.run}<span>↗</span></button></div>
          </form>
          <p className="notice">{copy.needs}</p>
        </section>
        <aside className="side-panel">
          <div className="metric-card"><span>PROJECTS / RUNS</span><strong>{runs.length.toString().padStart(2,"0")}</strong><small>{ar ? "مهام محفوظة في مساحة العمل" : "Saved engineering runs"}</small></div>
          <div className="history panel"><div className="panel-head"><h3>{copy.history}</h3><span>{runs.length}</span></div>
            {runs.length === 0 ? <p className="empty">{copy.noRuns}</p> : runs.slice(0,8).map(run=><button className={active?.id===run.id ? "run-item selected" : "run-item"} key={run.id} onClick={()=>setActive(run)}><span className="run-dot"/><span className="run-copy"><b>{run.workspace}</b><small>{run.prompt}</small></span><em>{run.status}</em></button>)}
          </div>
        </aside>
      </div>
      {active && <section className="result panel"><div className="panel-head"><div><span className="card-kicker">{copy.latest}</span><h2>{active.workspace}</h2></div><span className={active.mode==="live" ? "mode live" : "mode"}>{active.mode==="live" ? copy.live : copy.mock}</span></div>
        <p className="result-summary">{active.summary}</p>
        <div className="result-columns"><div><h3>{copy.changed} · {active.changed_files.length}</h3>{active.changed_files.length ? active.changed_files.map(file=><code className="file" key={file}>{file}</code>) : <p className="empty">—</p>}</div><div><h3>{copy.logs}</h3>{active.logs.map((log,i)=><div className="log" key={i}><b>{log.tool || log.type}</b><span>{log.error || log.message || (log.ok ? "OK" : "")}</span></div>)}</div></div>
      </section>}
    </section>}
    <footer><span>ATLAS AI / PERSONAL SOFTWARE ENGINEER</span><span>BUILT FOR IDEAS THAT SHIP.</span></footer>
  </main>;
}
