import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "";

async function api(path, opt = {}) {
  const r = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opt,
  });
  let d = {};
  try {
    d = await r.json();
  } catch {
    /* noop */
  }
  if (!r.ok) throw new Error(d.detail || d.message || "Request failed");
  return d;
}

/* ------------------------------------------------------------------ */
/* App shell + routing                                                  */
/* ------------------------------------------------------------------ */

const PAGES = [
  { id: "home", label: "Home" },
  { id: "chat", label: "AI Counsellor" },
  { id: "finder", label: "College Finder" },
  { id: "calculator", label: "Cutoff Calculator" },
];

function App() {
  const [page, setPage] = useState("home");
  const [meta, setMeta] = useState(null);
  const [metaErr, setMetaErr] = useState("");

  useEffect(() => {
    api("/api/meta")
      .then(setMeta)
      .catch(() => setMetaErr("Backend offline — starting the live chat requires the FastAPI service. The static preview still works."));
  }, []);

  return (
    <div className="shell">
      <Header page={page} setPage={setPage} />
      {metaErr && <div className="notice">{metaErr}</div>}
      <main className="view">
        {page === "home" && <Home meta={meta} setPage={setPage} />}
        {page === "chat" && <Chat meta={meta} />}
        {page === "finder" && <Finder meta={meta} />}
        {page === "calculator" && <Calculator meta={meta} setPage={setPage} />}
      </main>
      <Footer setPage={setPage} />
    </div>
  );
}

function Header({ page, setPage }) {
  const [open, setOpen] = useState(false);
  return (
    <header className="header">
      <button className="brand" onClick={() => setPage("home")}>
        <span className="brandMark">CA</span>
        <span className="brandText">
          <b>Campus AI</b>
          <small>TNEA Counselling</small>
        </span>
      </button>
      <nav className="nav">
        {PAGES.map((p) => (
          <button
            key={p.id}
            className={`navLink ${page === p.id ? "active" : ""}`}
            onClick={() => {
              setPage(p.id);
              setOpen(false);
            }}
          >
            {p.label}
          </button>
        ))}
      </nav>
      <button className="hamburger" onClick={() => setOpen((o) => !o)} aria-label="Menu">
        {open ? "✕" : "☰"}
      </button>
      {open && (
        <div className="mobileNav">
          {PAGES.map((p) => (
            <button key={p.id} onClick={() => { setPage(p.id); setOpen(false); }}>
              {p.label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
}

function Footer({ setPage }) {
  const links = [
    { label: "AI Counsellor", page: "chat" },
    { label: "College Finder", page: "finder" },
    { label: "Cutoff Calculator", page: "calculator" },
  ];
  return (
    <footer className="footer">
      <div className="footerInner">
        <div className="footerCol">
          <div className="footerBrand">
            <span className="brandMark small">CA</span>
            <b>Campus AI</b>
          </div>
          <p>Dataset-grounded TNEA 2025 counselling assistant. Built for students, by students.</p>
        </div>
        <div className="footerCol">
          <b>Platform</b>
          {links.map((l) => (
            <span key={l.page} className="footerLink" onClick={() => setPage(l.page)}>
              {l.label}
            </span>
          ))}
        </div>
        <div className="footerCol">
          <b>Data</b>
          <span>3,474 branch records</span>
          <span>438 colleges</span>
          <span>38 districts · 106 branches</span>
        </div>
        <div className="footerCol">
          <b>Language</b>
          <span>English</span>
          <span>தமிழ்</span>
          <span>Tanglish</span>
        </div>
      </div>
      <div className="footerBar">
        <span>© 2026 Campus AI · TNEA 2025 · Dataset grounded · No invented facts</span>
      </div>
    </footer>
  );
}

/* ------------------------------------------------------------------ */
/* Home                                                                */
/* ------------------------------------------------------------------ */

function Home({ meta, setPage }) {
  const stats = useMemo(
    () => ({
      colleges: meta?.colleges ?? "438",
      records: meta?.records ?? "3,474",
      districts: meta?.districts?.length ?? "38",
      branches: meta?.branches?.length ?? "106",
    }),
    [meta]
  );

  return (
    <div className="home">
      <section className="hero">
        <div className="heroBg" />
        <div className="heroGrid">
          <div className="heroCopy">
            <div className="pill">
              <span className="dot" />
              TNEA 2025 · OFFICIAL CUTOFF FORMULA
            </div>
            <h1>
              Find every eligible college.
              <br />
              <span className="gradient">Zero guesswork.</span>
            </h1>
            <p>
              Campus AI is your dataset-grounded TNEA counselling partner. Calculate your
              cutoff, explore every eligible branch, and chat naturally in English,
              தமிழ் or Tanglish — with no fabricated answers.
            </p>
            <div className="heroActions">
              <button className="btnPrimary" onClick={() => setPage("chat")}>
                Start chatting <span className="arrow">→</span>
              </button>
              <button className="btnGhost" onClick={() => setPage("finder")}>
                Explore colleges
              </button>
            </div>
            <div className="trust">
              <span><i className="tick">✓</i> Community-wise cutoffs</span>
              <span><i className="tick">✓</i> Every eligible result shown</span>
              <span><i className="tick">✓</i> No invented facts</span>
            </div>
          </div>

          <div className="heroCardWrap">
            <div className="heroCard">
              <div className="heroCardTop">
                <div className="heroAvatar">CA</div>
                <div className="heroCardTitle">
                  <b>Campus AI</b>
                  <small>AI Counsellor · online</small>
                </div>
                <span className="onlineDot" title="Live">●</span>
              </div>
              <div className="heroMsg user">My cutoff is 185, BC, CSE, Chennai — enna colleges?</div>
              <div className="heroMsg ai">
                Got it. For BC in Chennai, 106 eligible matches found across all
                branches — here are the best ones, sorted by margin.
              </div>
              <div className="heroMsg ai mini">
                <span className="recPill ok">#1201 · Anna University</span>
                <span className="recPill">#2123 · MIT, Chennai</span>
                <span className="recPill">#3321 · CEG Campus</span>
                <button className="heroCta" onClick={() => setPage("chat")}>
                  Try the full conversation →
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="statsBand">
        <Stat value={stats.colleges} label="Colleges" />
        <Stat value={stats.records} label="Branch records" />
        <Stat value={stats.districts} label="Districts" />
        <Stat value={stats.branches} label="Branches" />
      </section>

      <section className="features">
        <div className="secHead">
          <span className="secEyebrow">TOOLS</span>
          <h2>Everything you need to decide</h2>
          <p>Three focused tools backed by the complete TNEA 2025 dataset.</p>
        </div>
        <div className="featureGrid">
          <Card
            icon="⌁"
            title="AI Counsellor"
            tag="Conversational"
            text="NLP across English, Tamil and Tanglish with multi-turn memory for cutoff, community, district and branch."
            onClick={() => setPage("chat")}
          />
          <Card
            icon="∑"
            title="Cutoff Calculator"
            tag="Official formula"
            text="Mathematics + Physics/2 + Chemistry/2, out of 200 — the exact TNEA method."
            onClick={() => setPage("calculator")}
          />
          <Card
            icon="⌕"
            title="College Finder"
            tag="Full dataset"
            text="Filter all 3,474 records by cutoff, community, district and branch. Every eligible record is returned."
            onClick={() => setPage("finder")}
          />
        </div>
      </section>

      <section className="how">
        <div className="secHead">
          <span className="secEyebrow">HOW IT WORKS</span>
          <h2>Three steps to your shortlist</h2>
          <p>From marks to a ranked list of eligible colleges in minutes.</p>
        </div>
        <div className="howSteps">
          <Step
            n="01"
            t="Enter your cutoff"
            d="Maths + Physics/2 + Chemistry/2. Or just tell the AI your subject marks."
          />
          <Step
            n="02"
            t="Choose your community"
            d="OC, BC, BCM, MBC, SC, SCA or ST — TNEA cutoffs are community-wise."
          />
          <Step
            n="03"
            t="Filter and explore"
            d="By district and branch, or ask Campus AI in natural language for a shortlist."
          />
        </div>
      </section>

      <section className="ctaBand">
        <div>
          <h2>Ready to find where you belong?</h2>
          <p>Chat with Campus AI now and get your complete, honest eligible list.</p>
        </div>
        <button className="btnLight" onClick={() => setPage("chat")}>
          Talk to Campus AI →
        </button>
      </section>
    </div>
  );
}

function Stat({ value, label }) {
  return (
    <div className="stat">
      <b>{value}</b>
      <span>{label}</span>
    </div>
  );
}

function Card({ icon, title, tag, text, onClick }) {
  return (
    <button className="featureCard" onClick={onClick}>
      <span className="featureIcon">{icon}</span>
      <div className="featureBody">
        <div className="featureHead">
          <b>{title}</b>
          <span className="tag">{tag}</span>
        </div>
        <p>{text}</p>
        <span className="link">Open tool →</span>
      </div>
    </button>
  );
}

function Step({ n, t, d }) {
  return (
    <div className="step">
      <span className="stepNum">{n}</span>
      <b>{t}</b>
      <p>{d}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Chat (AI Counsellor)                                                */
/* ------------------------------------------------------------------ */

const SUGGESTIONS = [
  "My cutoff is 180, BC, CSE, Chennai",
  "Enakku 175 cutoff iruku, Chennai la ECE venum",
  "maths 92 physics 84 chemistry 88",
  "What documents do I need for TNEA?",
  "MBC 185 cutoff, AI & DS, Coimbatore",
];

function Chat({ meta }) {
  const STORAGE = "campus-ai-conversations-v2";
  const makeId = () => `${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
  const welcome = {
    role: "ai",
    text: "Vanakkam! 👋 I'm Campus AI, your TNEA counselling assistant. Ask me anything about cutoff, community, district, branch, colleges, comparisons, admission or counselling — in English, தமிழ் or Tanglish.",
  };

  const [messages, setMessages] = useState([welcome]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [profile, setProfile] = useState({});
  const [records, setRecords] = useState([]);
  const [colleges, setColleges] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [pageSize, setPageSize] = useState(5);
  const [conversations, setConversations] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE) || "[]"); } catch { return []; }
  });

  useEffect(() => {
    const meaningful = messages.filter(m => m.role === "user");
    if (!meaningful.length || !sessionId) return;
    const id = sessionId;
    const item = {
      id,
      title: meaningful[0].text.slice(0, 46),
      messages,
      profile,
      updatedAt: Date.now()
    };
    setConversations(prev => {
      const next = [item, ...prev.filter(x => x.id !== id)].slice(0, 20);
      localStorage.setItem(STORAGE, JSON.stringify(next));
      return next;
    });
  }, [messages, profile, sessionId]);

  const send = async (textOverride) => {
    const q = (textOverride ?? input).trim();
    if (!q || busy) return;
    setInput(""); setErr("");
    setMessages(m => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const d = await api("/api/chat", {
        method: "POST",
        body: JSON.stringify({
          message: q,
          session_id: sessionId,
          cutoff: profile.cutoff ?? null,
          community: profile.community ?? null,
          district: profile.district ?? null,
          branch: profile.branch ?? null,
          profile,
          history: messages.map(m => ({ role: m.role === "ai" ? "assistant" : "user", content: m.text })).slice(-20),
        }),
      });
      setSessionId(d.session_id);
      setProfile(d.profile || {});
      setRecords(d.records || []);
      setColleges(d.colleges || []);
      setPageSize(5);
      setMessages(m => [...m, { role: "ai", text: d.reply }]);
    } catch (e) {
      setErr(e.message || "I couldn't reach the counselling service.");
    } finally { setBusy(false); }
  };

  const newConversation = async () => {
    if (sessionId) {
      try { await api("/api/chat/reset", { method: "POST", body: JSON.stringify({ session_id: sessionId }) }); } catch {}
    }
    setSessionId(null); setProfile({}); setRecords([]); setColleges([]); setPageSize(5);
    setMessages([{ ...welcome, text: "Started a new conversation! 🎓 Tell me what you want to know about TNEA." }]);
  };

  const deleteConversation = () => {
    if (!sessionId) return;
    setConversations(prev => {
      const next = prev.filter(x => x.id !== sessionId);
      localStorage.setItem(STORAGE, JSON.stringify(next));
      return next;
    });
    newConversation();
  };

  const loadConversation = async (item) => {
    setSessionId(item.id);
    setMessages(item.messages || [welcome]);
    setProfile(item.profile || {});
    setRecords([]); setColleges([]); setErr("");
    // The backend session may expire/restart; follow-up will still work from the saved profile.
  };

  const shareConversation = async () => {
    const text = messages.map(m => `${m.role === "user" ? "You" : "Campus AI"}: ${m.text}`).join("\n\n");
    try {
      if (navigator.share) await navigator.share({ title: "Campus AI TNEA Counselling", text });
      else await navigator.clipboard.writeText(text);
      setErr("Conversation copied/shared successfully.");
      setTimeout(() => setErr(""), 1800);
    } catch {}
  };

  const profileChips = useMemo(() => {
    const chips = [];
    if (profile.cutoff != null) chips.push({ k: "Cutoff", v: String(profile.cutoff) });
    if (profile.community) chips.push({ k: "Community", v: profile.community });
    if (profile.district) chips.push({ k: "District", v: profile.district === "ALL" ? "All districts" : profile.district });
    if (profile.branch) chips.push({ k: "Branch", v: profile.branch === "ALL" ? "All branches" : profile.branch });
    if (profile.college_type) chips.push({ k: "College type", v: profile.college_type === "ALL" ? "All colleges" : profile.college_type });
    return chips;
  }, [profile]);

  const showRecords = records.slice(0, pageSize);
  const naCount = records.filter(r => !r.eligible).length;

  const clearChat = async () => {
    if (sessionId) {
      try { await api("/api/chat/reset", { method: "POST", body: JSON.stringify({ session_id: sessionId }) }); } catch {}
    }
    setSessionId(null); setProfile({}); setRecords([]); setColleges([]); setPageSize(5);
    setMessages([welcome]);
    setErr("");
  };

  return (
    <div className="chatPage chatPageLayout">
      <aside className="chatSidebar">
        <div className="sidebarHead">
          <div>
            <b>Conversations</b>
            <span>{conversations.length} saved</span>
          </div>
          <button className="moreBtnIcon" onClick={() => setMenuOpen((v) => !v)} aria-label="Chat actions">⋮</button>
          {menuOpen && (
            <div className="chatMenu">
              <button onClick={() => { setMenuOpen(false); newConversation(); }}>＋ New chat</button>
              <button onClick={() => { setMenuOpen(false); clearChat(); }}>Clear chat</button>
              <button onClick={() => { setMenuOpen(false); shareConversation(); }} disabled={!messages.some(m => m.role === "user")}>↗ Share</button>
              <button onClick={() => { setMenuOpen(false); deleteConversation(); }} disabled={!sessionId}>Delete</button>
            </div>
          )}
        </div>
        <button className="newChatSide" onClick={newConversation}>＋ New chat</button>
        <div className="historyList">
          {conversations.length === 0 && <div className="historyEmpty">Previous conversations will appear here.</div>}
          {conversations.map((x) => (
            <button key={x.id} className={`historyItem ${x.id === sessionId ? "active" : ""}`} onClick={() => loadConversation(x)}>
              <b>{x.title || "New conversation"}</b>
              <span>{new Date(x.updatedAt || Date.now()).toLocaleDateString()}</span>
            </button>
          ))}
        </div>
        <div className="sidebarHint">Your counselling profile is remembered until you clear the chat.</div>
      </aside>

      <section className="chatWorkspace">
        <div className="chatTop">
          <div>
            <h2>AI Counsellor</h2>
            <p>Dataset-grounded · English · தமிழ் · Tanglish · context-aware</p>
          </div>
          <button className="moreBtnIcon workspaceMore" onClick={() => setMenuOpen((v) => !v)} aria-label="Chat actions">⋮</button>
        </div>

        {profileChips.length > 0 && (
          <div className="profileBar">
            <span className="profileLabel">Your profile</span>
            {profileChips.map((c, i) => <span className="chip" key={i}><b>{c.k}:</b> {c.v}</span>)}
          </div>
        )}

        <div className="chatPanel">
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                {m.role === "ai" && <span className="miniAvatar">CA</span>}
                <div className="bubbleWrap">
                  <div className="bubbleText">{m.text}</div>
                  {m.role === "ai" && i === messages.length - 1 && records.length > 0 &&
                    <ResultList records={records} naCount={naCount} pageSize={pageSize} setPageSize={setPageSize} />}
                </div>
              </div>
            ))}
            {busy && <div className="msg ai"><span className="miniAvatar">CA</span><div className="bubbleWrap"><div className="typing"><span/><span/><span/></div></div></div>}
          </div>

          {err && <div className="chatErr">{err}</div>}
          <div className="suggestions">
            {SUGGESTIONS.map(s => <button key={s} onClick={() => send(s)}>{s}</button>)}
          </div>
          <div className="composer">
            <input value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send()}
              placeholder="Ask any TNEA counselling question…" />
            <button className="sendBtn" onClick={() => send()} disabled={busy || !input.trim()}>Send</button>
          </div>
        </div>
      </section>
    </div>
  );
}

function ResultList({ records, naCount, pageSize, setPageSize }) {
  if (!records.length) return null;
  const eligible = records.filter((r) => r.eligible);
  const na = records.filter((r) => !r.eligible);
  const shown = [...eligible, ...na].slice(0, pageSize);
  return (
    <div className="resultList">
      <div className="resultMeta">
        <span>✓ {eligible.length} eligible</span><span>· showing {Math.min(pageSize, eligible.length)} first</span>
        {naCount > 0 && <span>· {naCount} cutoff not published</span>}
        <span>· sorted by margin</span>
      </div>
      {shown.map((r, i) => (
        <div className={`recCard ${r.eligible ? "" : "naCard"}`} key={i}>
          <div className="recHead">
            <span className="recCode">#{r.college_code}</span>
            <span className={`status ${r.eligible ? "ok" : "na"}`}>{r.status}</span>
          </div>
          <div className="recName">{r.college_name}</div>
          <div className="recMeta">
            <span>{r.district} · {r.branch}</span>
            <span className="cutoff">
              {r.eligible ? (
                <>Closing <b>{r.closing_cutoff}</b> · margin <b>+{r.margin}</b></>
              ) : r.cutoffs ? (
                <span className="cutoffGrid">
                  {Object.entries(r.cutoffs).map(([k, v]) => <span key={k}><b>{k}</b> {v ?? "—"}</span>)}
                </span>
              ) : (
                <span className="naText">No published cutoff in dataset</span>
              )}
            </span>
          </div>
        </div>
      ))}
      {records.length > pageSize && (
        <div className="resultActions">
          <button className="moreBtn" onClick={() => setPageSize((n) => Math.min(n + 5, records.length))}>
            Show more eligible colleges · {records.length - pageSize} remaining
          </button>
          {pageSize < records.length && records.length > 10 && (
            <button className="allResultsBtn" onClick={() => setPageSize(records.length)}>
              View all {eligible.length} eligible colleges
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* College Finder                                                      */
/* ------------------------------------------------------------------ */

function Finder({ meta }) {
  const [cutoff, setCutoff] = useState("");
  const [community, setCommunity] = useState("OC");
  const [district, setDistrict] = useState("ALL");
  const [branch, setBranch] = useState("ALL");
  const [search, setSearch] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [pageSize, setPageSize] = useState(30);

  const branches = useMemo(
    () => ["ALL", ...(meta?.branches || [])].slice(0, 200),
    [meta]
  );

  const run = async () => {
    setErr("");
    setLoading(true);
    try {
      const d = await api("/api/recommend", {
        method: "POST",
        body: JSON.stringify({
          cutoff: parseFloat(cutoff),
          community,
          district,
          branch,
          search,
          include_na: true,
          limit: 2000,
        }),
      });
      setResult(d);
      setPageSize(30);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  const allRecords = [...(result?.records || []), ...(result?.na_records || [])];
  const shown = allRecords.slice(0, pageSize);

  return (
    <div className="page">
      <div className="pageHead">
        <div>
          <h2>College Finder</h2>
          <p>Filter the complete TNEA dataset by cutoff, community, district and branch.</p>
        </div>
        {meta && <span className="dataBadge">● {meta.records} records</span>}
      </div>

      <div className="filterPanel">
        <div className="filterGrid">
          <label className="field">
            <span>Cutoff (out of 200)</span>
            <input
              type="number" min="0" max="200" step="0.5"
              value={cutoff} onChange={(e) => setCutoff(e.target.value)}
              placeholder="e.g. 180" required
            />
          </label>
          <label className="field">
            <span>Community</span>
            <select value={community} onChange={(e) => setCommunity(e.target.value)}>
              {(meta?.communities || ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]).map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>District</span>
            <select value={district} onChange={(e) => setDistrict(e.target.value)}>
              <option value="ALL">All districts</option>
              {(meta?.districts || []).map((d) => <option key={d}>{d}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Branch</span>
            <select value={branch} onChange={(e) => setBranch(e.target.value)}>
              {branches.map((b) => <option key={b}>{b === "ALL" ? "All branches" : b}</option>)}
            </select>
          </label>
          <label className="field wide">
            <span>Search college name</span>
            <input
              value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="e.g. Anna University"
            />
          </label>
          <button
            className="btnPrimary findBtn"
            onClick={run}
            disabled={!cutoff || loading}
          >
            {loading ? "Searching…" : "Find matching colleges →"}
          </button>
        </div>
      </div>

      {err && <div className="notice">{err}</div>}

      {result && (
        <div className="resultsHead">
          <b>{result.eligible_count} eligible records</b>
          {result.na_count > 0 && <span>· {result.na_count} without a published {community} cutoff</span>}
          <span>· closing cutoff ≤ your cutoff</span>
        </div>
      )}

      {result && shown.length > 0 && (
        <div className="results">
          {shown.map((r, i) => (
            <div className={`recCard ${r.eligible ? "" : "naCard"}`} key={i}>
              <div className="recHead">
                <span className="recCode">#{r.college_code}</span>
                <span className={`status ${r.eligible ? "ok" : "na"}`}>{r.status}</span>
              </div>
              <div className="recName">{r.college_name}</div>
              <div className="recMeta">
                <span>{r.district} · {r.branch}</span>
                {r.eligible ? (
                  <span className="cutoff">
                    Closing <b>{r.closing_cutoff}</b> · margin <b>+{r.margin}</b>
                  </span>
                ) : (
                  <span className="naText">No {community} cutoff published</span>
                )}
              </div>
            </div>
          ))}
          {allRecords.length > pageSize && (
            <button className="moreBtn" onClick={() => setPageSize((n) => n + 30)}>
              Show more ({allRecords.length - pageSize} remaining)
            </button>
          )}
        </div>
      )}

      {result && shown.length === 0 && (
        <div className="empty">
          No matching records for cutoff {cutoff}, {community}
          {district !== "ALL" && `, ${district}`}.
          Try a higher cutoff or remove a filter.
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Cutoff Calculator                                                   */
/* ------------------------------------------------------------------ */

function Calculator({ setPage }) {
  const [m, setM] = useState("");
  const [p, setP] = useState("");
  const [c, setC] = useState("");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  const calc = async () => {
    setErr("");
    const a = parseFloat(m), b = parseFloat(p), d = parseFloat(c);
    if ([a, b, d].some((x) => Number.isNaN(x))) {
      setErr("Enter marks for all three subjects.");
      return;
    }
    try {
      const r = await api("/api/calculate-cutoff", {
        method: "POST",
        body: JSON.stringify({ mathematics: a, physics: b, chemistry: d }),
      });
      setResult(r);
    } catch (e) {
      setErr(e.message);
    }
  };

  return (
    <div className="page">
      <div className="pageHead">
        <div>
          <h2>Cutoff Calculator</h2>
          <p>Official TNEA formula: Mathematics + Physics/2 + Chemistry/2 (out of 200).</p>
        </div>
      </div>

      <div className="calcLayout">
        <div className="calcPanel">
          <NumberField label="Mathematics" value={m} set={setM} />
          <NumberField label="Physics" value={p} set={setP} />
          <NumberField label="Chemistry" value={c} set={setC} />
          {err && <div className="notice">{err}</div>}
          <button className="btnPrimary wide" onClick={calc}>Calculate cutoff</button>
        </div>

        <div className="calcResult">
          <span>Your TNEA cutoff</span>
          <strong>{result ? result.cutoff : "—"}</strong>
          <small>out of 200</small>
          {result && (
            <div className="calcBreakdown">
              <div><span>Maths</span><b>{result.breakdown.mathematics}</b></div>
              <div><span>Physics ÷ 2</span><b>{result.breakdown.physics_half}</b></div>
              <div><span>Chemistry ÷ 2</span><b>{result.breakdown.chemistry_half}</b></div>
            </div>
          )}
          {result && (
            <button className="btnPrimary small" onClick={() => setPage("finder")}>
              Use in College Finder →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function NumberField({ label, value, set }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number" min="0" max="100" step="0.5"
        value={value} onChange={(e) => set(e.target.value)}
        placeholder="0 – 100"
      />
    </label>
  );
}

createRoot(document.getElementById("root")).render(<App />);
