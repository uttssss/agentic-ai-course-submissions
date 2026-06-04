import { useState, useMemo, useRef, useEffect, useCallback } from "react";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

// ── constants ─────────────────────────────────────────────────────────────────

const CATEGORIES = [
  "Food & Dining","Groceries","Transport","Travel","Shopping",
  "Health & Medical","Entertainment","Utilities","Housing","Insurance",
  "Education","Personal Care","Subscriptions","Fees & Charges","Other"
];
const AUTO_CATEGORIES = ["Transfers","Investment","Income"];
const ALL_CATEGORIES = [...CATEGORIES, ...AUTO_CATEGORIES];

const CAT_COLORS = {
  "Food & Dining":"#e8845a","Groceries":"#d4a843","Transport":"#5a9be8",
  "Travel":"#7c6fd4","Shopping":"#e85a8a","Health & Medical":"#5ad4a0",
  "Entertainment":"#d45a9b","Utilities":"#5ab8d4","Housing":"#9b7cd4",
  "Insurance":"#d4c25a","Education":"#5ad48a","Personal Care":"#e8a05a",
  "Subscriptions":"#a05ae8","Fees & Charges":"#d45a5a","Other":"#8a8a8a",
  "Transfers":"#5a7ce8","Investment":"#5ae8c8","Income":"#7ed45a",
};

const ACCOUNT_TYPES = ["checking","savings","credit_card","investment","cash","loan"];

const TX_TYPES = ["expense","income","transfer","investment"];

const TYPE_COLORS = {
  expense:"#e07070", income:"#5dbf7a", transfer:"#7090e0", investment:"#e0b870"
};

// ── storage ───────────────────────────────────────────────────────────────────

const STORAGE_KEY = "fintrack_v0";

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch { return null; }
}

function saveState(state) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
}

const DEFAULT_STATE = {
  accounts: [],
  transactions: [],
  formatProfiles: {},
  nextId: 1,
};

// ── CSV parsing ───────────────────────────────────────────────────────────────

function parseCSVText(text) {
  const lines = [];
  let cur = "", inQ = false, row = [];
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (inQ && text[i+1] === '"') { cur += '"'; i++; }
      else inQ = !inQ;
    } else if (c === ',' && !inQ) {
      row.push(cur.trim()); cur = "";
    } else if ((c === '\n' || c === '\r') && !inQ) {
      if (c === '\r' && text[i+1] === '\n') i++;
      row.push(cur.trim()); cur = "";
      if (row.some(v => v !== "")) lines.push(row);
      row = [];
    } else {
      cur += c;
    }
  }
  row.push(cur.trim());
  if (row.some(v => v !== "")) lines.push(row);
  return lines;
}

function normaliseDate(raw) {
  if (!raw) return null;
  raw = raw.trim();
  // MM/DD/YYYY or M/D/YYYY
  const m1 = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (m1) return `${m1[3]}-${m1[1].padStart(2,"0")}-${m1[2].padStart(2,"0")}`;
  // YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  // M/D/YY
  const m2 = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2})$/);
  if (m2) return `20${m2[3]}-${m2[1].padStart(2,"0")}-${m2[2].padStart(2,"0")}`;
  return null;
}

function parseAmount(raw) {
  if (!raw && raw !== 0) return NaN;
  const s = String(raw).trim();
  const neg = s.startsWith("(") && s.endsWith(")");
  const cleaned = s.replace(/[()$,\s]/g, "");
  const n = parseFloat(cleaned);
  return isNaN(n) ? NaN : (neg ? -n : n);
}

// ── transfer matching ─────────────────────────────────────────────────────────

const MATCH_TOLERANCE_ABS = 5.0;
const MATCH_TOLERANCE_PCT = 0.005;
const MATCH_WINDOW_DAYS = 5;

function amountsMatch(a, b) {
  const diff = Math.abs(Math.abs(a) - Math.abs(b));
  const pct = diff / Math.max(Math.abs(a), Math.abs(b));
  return diff <= MATCH_TOLERANCE_ABS || pct <= MATCH_TOLERANCE_PCT;
}

function daysBetween(d1, d2) {
  return Math.abs((new Date(d1) - new Date(d2)) / 86400000);
}

function runTransferMatching(transactions) {
  // Reset all auto-matched transfers first, keep manual matches
  const txs = transactions.map(t => ({
    ...t,
    matchId: t._manualMatch ? t.matchId : null,
    type: t._manualMatch ? t.type : (t._originalType || t.type),
  }));

  // candidates: outflows from one account paired with inflows to another
  const unmatched = txs.filter(t => !t.matchId && !t._manualMatch);
  const outflows = unmatched.filter(t => t.amount < 0);
  const inflows = unmatched.filter(t => t.amount > 0);
  const usedIds = new Set();

  outflows.forEach(out => {
    if (usedIds.has(out.id)) return;
    const candidates = inflows.filter(inf =>
      !usedIds.has(inf.id) &&
      inf.accountId !== out.accountId &&
      amountsMatch(out.amount, inf.amount) &&
      daysBetween(out.date, inf.date) <= MATCH_WINDOW_DAYS
    );
    if (!candidates.length) return;
    candidates.sort((a, b) => daysBetween(a.date, out.date) - daysBetween(b.date, out.date));
    const best = candidates[0];
    const matchId = `match_${out.id}_${best.id}`;
    const nearMatch = Math.abs(Math.abs(out.amount) - Math.abs(best.amount)) > 0.01;
    out.matchId = matchId;
    out.type = "transfer";
    out._nearMatch = nearMatch;
    best.matchId = matchId;
    best.type = "transfer";
    best._nearMatch = nearMatch;
    usedIds.add(out.id);
    usedIds.add(best.id);
  });

  return txs;
}

// ── format profiles ───────────────────────────────────────────────────────────

const KNOWN_PROFILES = {
  boa_checking: {
    name: "BoA Checking",
    skipRows: 6,
    dateCol: "date",
    descCol: "description",
    amountCol: "amount",
    balanceCol: "running bal.",
    signConv: "pos_is_credit",
  },
  boa_credit: {
    name: "BoA Credit Card",
    skipRows: 0,
    dateCol: "posted date",
    descCol: "payee",
    amountCol: "amount",
    balanceCol: null,
    signConv: "neg_is_debit",
  },
};

function guessMapping(headers) {
  const h = headers.map(x => x.toLowerCase());
  const find = (...cands) => {
    for (const c of cands) {
      const i = h.findIndex(x => x.includes(c));
      if (i >= 0) return headers[i];
    }
    return "";
  };
  return {
    dateCol: find("date","posted"),
    descCol: find("description","payee","memo","narration"),
    amountCol: find("amount","value","debit","credit"),
    balanceCol: find("balance","bal"),
  };
}

// ── helpers ───────────────────────────────────────────────────────────────────

const fmt = n => {
  if (n === null || n === undefined || isNaN(n)) return "$0";
  return new Intl.NumberFormat("en-US", { style:"currency", currency:"USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(Math.abs(n));
};
const fmtFull = n => new Intl.NumberFormat("en-US", { style:"currency", currency:"USD" }).format(n);
const today = () => new Date().toISOString().slice(0,10);

function uuid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

// ── styles ────────────────────────────────────────────────────────────────────

const C = {
  bg: "#0c0d0f",
  surface: "#13141a",
  surfaceHover: "#1a1b24",
  border: "#1e2030",
  borderLight: "#252840",
  text: "#e2dfd8",
  textMuted: "#6b6f88",
  textDim: "#3a3d52",
  accent: "#c8a96e",
  accentDim: "#c8a96e22",
  green: "#5dbf7a",
  red: "#e07070",
  blue: "#7090e0",
  gold: "#e0b870",
};

const css = {
  app: {
    fontFamily: "'DM Mono', 'Fira Code', 'Courier New', monospace",
    minHeight: "100vh",
    background: C.bg,
    color: C.text,
    display: "flex",
  },
  sidebar: {
    width: 220,
    minHeight: "100vh",
    background: C.surface,
    borderRight: `1px solid ${C.border}`,
    display: "flex",
    flexDirection: "column",
    padding: "24px 0",
    flexShrink: 0,
  },
  logo: {
    padding: "0 20px 24px",
    borderBottom: `1px solid ${C.border}`,
    marginBottom: 8,
  },
  logoText: {
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: "0.15em",
    textTransform: "uppercase",
    color: C.accent,
  },
  logoSub: {
    fontSize: 9,
    color: C.textMuted,
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    marginTop: 3,
  },
  navItem: (active) => ({
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "9px 20px",
    fontSize: 11,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    cursor: "pointer",
    color: active ? C.accent : C.textMuted,
    background: active ? C.accentDim : "transparent",
    borderLeft: active ? `2px solid ${C.accent}` : "2px solid transparent",
    transition: "all 0.15s",
    userSelect: "none",
  }),
  main: {
    flex: 1,
    minHeight: "100vh",
    overflow: "auto",
  },
  pageHeader: {
    padding: "32px 40px 24px",
    borderBottom: `1px solid ${C.border}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  pageTitle: {
    fontSize: 11,
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    color: C.textMuted,
  },
  pageContent: {
    padding: "32px 40px",
  },
  card: {
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 2,
    padding: "20px 24px",
  },
  cardTitle: {
    fontSize: 9,
    letterSpacing: "0.2em",
    textTransform: "uppercase",
    color: C.textMuted,
    marginBottom: 12,
  },
  btn: {
    background: C.accent,
    color: "#0c0d0f",
    border: "none",
    borderRadius: 2,
    padding: "8px 16px",
    fontSize: 10,
    letterSpacing: "0.15em",
    textTransform: "uppercase",
    fontWeight: 700,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "opacity 0.15s",
  },
  btnGhost: {
    background: "transparent",
    color: C.textMuted,
    border: `1px solid ${C.border}`,
    borderRadius: 2,
    padding: "8px 16px",
    fontSize: 10,
    letterSpacing: "0.15em",
    textTransform: "uppercase",
    cursor: "pointer",
    fontFamily: "inherit",
  },
  btnDanger: {
    background: "transparent",
    color: C.red,
    border: `1px solid ${C.red}33`,
    borderRadius: 2,
    padding: "6px 12px",
    fontSize: 10,
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    cursor: "pointer",
    fontFamily: "inherit",
  },
  input: {
    background: C.bg,
    border: `1px solid ${C.border}`,
    borderRadius: 2,
    padding: "8px 12px",
    fontSize: 12,
    color: C.text,
    fontFamily: "inherit",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
  },
  select: {
    background: C.bg,
    border: `1px solid ${C.border}`,
    borderRadius: 2,
    padding: "8px 12px",
    fontSize: 12,
    color: C.text,
    fontFamily: "inherit",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
    appearance: "none",
  },
  label: {
    fontSize: 9,
    letterSpacing: "0.15em",
    textTransform: "uppercase",
    color: C.textMuted,
    display: "block",
    marginBottom: 5,
  },
  grid2: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
  grid3: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 },
  grid4: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16 },
};

// ── components ────────────────────────────────────────────────────────────────

function KPICard({ label, value, sub, color }) {
  return (
    <div style={{ ...css.card }}>
      <div style={css.cardTitle}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 700, color: color || C.text, letterSpacing: "-0.02em" }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function TypeBadge({ type }) {
  const color = TYPE_COLORS[type] || C.textMuted;
  return (
    <span style={{
      fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase",
      padding: "2px 7px", borderRadius: 2,
      background: color + "22", color,
    }}>{type}</span>
  );
}

function CatBadge({ cat }) {
  const color = CAT_COLORS[cat] || C.textMuted;
  return (
    <span style={{
      fontSize: 9, letterSpacing: "0.1em", textTransform: "uppercase",
      padding: "2px 7px", borderRadius: 2,
      background: color + "18", color: color + "cc",
    }}>{cat || "—"}</span>
  );
}

const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 2, padding: "8px 12px", fontSize: 11 }}>
      {label && <div style={{ color: C.textMuted, marginBottom: 4, fontSize: 10 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || C.text }}>{p.name ? `${p.name}: ` : ""}{fmtFull(p.value)}</div>
      ))}
    </div>
  );
};

// ── pages ─────────────────────────────────────────────────────────────────────

function AccountsPage({ state, dispatch }) {
  const [form, setForm] = useState({ name: "", type: "checking", openingBalance: "", openingDate: today() });
  const [err, setErr] = useState("");

  function addAccount() {
    if (!form.name.trim()) { setErr("Name required"); return; }
    const bal = parseFloat(form.openingBalance) || 0;
    dispatch({ type: "ADD_ACCOUNT", payload: { id: uuid(), name: form.name.trim(), type: form.type, openingBalance: bal, openingDate: form.openingDate } });
    setForm({ name: "", type: "checking", openingBalance: "", openingDate: today() });
    setErr("");
  }

  function removeAccount(id) {
    if (state.transactions.some(t => t.accountId === id)) {
      alert("Cannot delete account with transactions. Archive instead (coming in V1).");
      return;
    }
    dispatch({ type: "REMOVE_ACCOUNT", payload: id });
  }

  return (
    <div>
      <div style={css.pageHeader}>
        <div style={css.pageTitle}>Accounts</div>
      </div>
      <div style={css.pageContent}>
        {state.accounts.length > 0 && (
          <div style={{ ...css.card, marginBottom: 24 }}>
            <div style={css.cardTitle}>Your accounts</div>
            {state.accounts.map(a => {
              const balance = a.openingBalance + state.transactions.filter(t => t.accountId === a.id && t.type !== "transfer").reduce((s, t) => s + t.amount, 0);
              return (
                <div key={a.id} style={{ display:"flex", alignItems:"center", gap:16, padding:"10px 0", borderBottom:`1px solid ${C.border}` }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:13 }}>{a.name}</div>
                    <div style={{ fontSize:10, color:C.textMuted, marginTop:2, letterSpacing:"0.1em", textTransform:"uppercase" }}>{a.type} · opened {a.openingDate}</div>
                  </div>
                  <div style={{ fontSize:15, fontWeight:700, color: balance >= 0 ? C.text : C.red }}>{balance < 0 ? "-" : ""}{fmt(balance)}</div>
                  <button style={css.btnDanger} onClick={() => removeAccount(a.id)}>×</button>
                </div>
              );
            })}
          </div>
        )}

        <div style={css.card}>
          <div style={css.cardTitle}>Add account</div>
          <div style={{ ...css.grid2, marginBottom:16 }}>
            <div>
              <label style={css.label}>Account name</label>
              <input style={css.input} value={form.name} onChange={e => setForm(f=>({...f,name:e.target.value}))} placeholder="e.g. BoA Checking" />
            </div>
            <div>
              <label style={css.label}>Type</label>
              <select style={css.select} value={form.type} onChange={e => setForm(f=>({...f,type:e.target.value}))}>
                {ACCOUNT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div style={{ ...css.grid2, marginBottom:16 }}>
            <div>
              <label style={css.label}>Opening balance ($)</label>
              <input style={css.input} type="number" value={form.openingBalance} onChange={e => setForm(f=>({...f,openingBalance:e.target.value}))} placeholder="0.00" step="0.01" />
            </div>
            <div>
              <label style={css.label}>As of date</label>
              <input style={css.input} type="date" value={form.openingDate} onChange={e => setForm(f=>({...f,openingDate:e.target.value}))} />
            </div>
          </div>
          {err && <div style={{ color:C.red, fontSize:11, marginBottom:12 }}>{err}</div>}
          <button style={css.btn} onClick={addAccount}>+ Add account</button>
        </div>
      </div>
    </div>
  );
}

// ── import page ───────────────────────────────────────────────────────────────

function ImportPage({ state, dispatch }) {
  const [step, setStep] = useState("upload"); // upload|map|preview|done
  const [selectedAccount, setSelectedAccount] = useState(state.accounts[0]?.id || "");
  const [csvRows, setCsvRows] = useState([]);
  const [rawHeaders, setRawHeaders] = useState([]);
  const [mapping, setMapping] = useState({});
  const [skipRows, setSkipRows] = useState(0);
  const [preview, setPreview] = useState([]);
  const [importedCount, setImportedCount] = useState(0);
  const [dupCount, setDupCount] = useState(0);
  const [matchCount, setMatchCount] = useState(0);
  const [err, setErr] = useState("");
  const fileRef = useRef();

  useEffect(() => {
    if (selectedAccount && state.formatProfiles[selectedAccount]) {
      const p = state.formatProfiles[selectedAccount];
      setSkipRows(p.skipRows || 0);
    }
  }, [selectedAccount]);

  function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      const lines = parseCSVText(ev.target.result);
      setCsvRows(lines);
      // try to find header row after skip
      const headerRow = lines[skipRows] || [];
      setRawHeaders(headerRow);
      const guessed = guessMapping(headerRow);
      // apply saved profile if exists
      const saved = state.formatProfiles[selectedAccount];
      setMapping(saved ? { dateCol: saved.dateCol, descCol: saved.descCol, amountCol: saved.amountCol, balanceCol: saved.balanceCol || "" } : guessed);
      setErr("");
      setStep("map");
    };
    reader.readAsText(file);
  }

  function handleSkipChange(n) {
    setSkipRows(n);
    const headerRow = csvRows[n] || [];
    setRawHeaders(headerRow);
    const guessed = guessMapping(headerRow);
    setMapping(guessed);
  }

  function buildPreview() {
    if (!mapping.dateCol || !mapping.amountCol || !mapping.descCol) { setErr("Map Date, Description and Amount to continue."); return; }
    const headers = rawHeaders.map(h => h.toLowerCase());
    const col = name => headers.indexOf(name?.toLowerCase());
    const dateI = col(mapping.dateCol);
    const descI = col(mapping.descCol);
    const amtI = col(mapping.amountCol);
    const balI = mapping.balanceCol ? col(mapping.balanceCol) : -1;

    if (dateI < 0 || amtI < 0 || descI < 0) { setErr("Column not found in header. Check mapping."); return; }

    const dataRows = csvRows.slice(skipRows + 1);
    const rows = dataRows.map((row, i) => {
      const rawAmt = parseAmount(row[amtI]);
      const date = normaliseDate(row[dateI]);
      const desc = row[descI] || "";
      const balance = balI >= 0 ? parseAmount(row[balI]) : null;
      // skip footer/summary rows
      if (!date || isNaN(rawAmt) || rawAmt === 0) return null;
      // skip rows that look like summaries
      if (desc.toLowerCase().includes("beginning balance") || desc.toLowerCase().includes("ending balance")) return null;
      return { _idx: i, date, description: desc, amount: rawAmt, balance, _skip: false };
    }).filter(Boolean);

    // derive opening balance from first row's balance column if available
    const firstWithBalance = rows.find(r => r.balance !== null);
    if (firstWithBalance && !state.accounts.find(a => a.id === selectedAccount)?.openingBalance) {
      // would set opening balance — noted in preview
    }

    setPreview(rows);
    setErr("");
    setStep("preview");
  }

  function confirmImport() {
    const account = state.accounts.find(a => a.id === selectedAccount);
    if (!account) return;

    // dedup against existing
    const existing = new Set(state.transactions.filter(t => t.accountId === selectedAccount).map(t => `${t.date}|${t.description}|${t.amount}`));
    let dups = 0;
    const newTxs = [];

    preview.filter(r => !r._skip).forEach(r => {
      const key = `${r.date}|${r.description}|${r.amount}`;
      if (existing.has(key)) { dups++; return; }
      // infer type from amount and account type
      let type = "expense";
      if (account.type === "credit_card") {
        type = r.amount < 0 ? "expense" : "income"; // positive on CC = payment/credit
      } else {
        type = r.amount < 0 ? "expense" : "income";
      }
      newTxs.push({
        id: uuid(),
        accountId: selectedAccount,
        date: r.date,
        description: r.description,
        amount: r.amount,
        type,
        _originalType: type,
        category: "Other",
        matchId: null,
        source: "imported",
      });
    });

    // save format profile
    dispatch({
      type: "SAVE_FORMAT_PROFILE",
      payload: { accountId: selectedAccount, profile: { skipRows, dateCol: mapping.dateCol, descCol: mapping.descCol, amountCol: mapping.amountCol, balanceCol: mapping.balanceCol || null } }
    });

    dispatch({ type: "IMPORT_TRANSACTIONS", payload: newTxs });
    setDupCount(dups);
    setImportedCount(newTxs.length);
    setStep("done");
  }

  function reset() {
    setStep("upload");
    setCsvRows([]); setRawHeaders([]); setMapping({}); setPreview([]);
    setErr("");
    if (fileRef.current) fileRef.current.value = "";
  }

  const colOptions = ["", ...rawHeaders];

  if (state.accounts.length === 0) return (
    <div style={css.pageContent}>
      <div style={{ ...css.card, textAlign:"center", padding:"40px" }}>
        <div style={{ color:C.textMuted, fontSize:12 }}>Add an account first before importing.</div>
      </div>
    </div>
  );

  return (
    <div>
      <div style={css.pageHeader}>
        <div style={css.pageTitle}>Import CSV</div>
        <div style={{ display:"flex", gap:6 }}>
          {["upload","map","preview","done"].map((s,i) => {
            const done = ["upload","map","preview","done"].indexOf(step) > i;
            const active = step === s;
            return (
              <span key={s} style={{ fontSize:9, letterSpacing:"0.12em", textTransform:"uppercase", padding:"4px 10px", borderRadius:2, background: active ? C.accentDim : done ? "#1a2a1a" : C.surface, color: active ? C.accent : done ? C.green : C.textDim, border:`1px solid ${active ? C.accent+"44" : done ? C.green+"33" : C.border}` }}>
                {done ? "✓ " : ""}{s}
              </span>
            );
          })}
        </div>
      </div>
      <div style={css.pageContent}>

        {step === "upload" && (
          <div style={css.card}>
            <div style={{ marginBottom:20 }}>
              <label style={css.label}>Account</label>
              <select style={{ ...css.select, maxWidth:300 }} value={selectedAccount} onChange={e => setSelectedAccount(e.target.value)}>
                {state.accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div style={{ border:`1px dashed ${C.borderLight}`, borderRadius:2, padding:"40px", textAlign:"center", cursor:"pointer" }} onClick={() => fileRef.current?.click()}>
              <div style={{ fontSize:20, marginBottom:8 }}>↑</div>
              <div style={{ fontSize:11, color:C.textMuted, letterSpacing:"0.1em" }}>click to upload .csv</div>
              <input ref={fileRef} type="file" accept=".csv" style={{ display:"none" }} onChange={handleFile} />
            </div>
            {err && <div style={{ color:C.red, fontSize:11, marginTop:12 }}>{err}</div>}
            <div style={{ marginTop:20, fontSize:10, color:C.textDim }}>
              Supported: BoA Checking, BoA Credit Card, Amex, Venmo, HSA, Robinhood
            </div>
          </div>
        )}

        {step === "map" && (
          <div style={css.card}>
            <div style={{ fontSize:11, color:C.textMuted, marginBottom:20 }}>
              Found <strong style={{ color:C.text }}>{csvRows.length}</strong> rows · <strong style={{ color:C.text }}>{rawHeaders.length}</strong> columns
            </div>
            <div style={{ ...css.grid2, marginBottom:16 }}>
              <div>
                <label style={css.label}>Header rows to skip</label>
                <input style={css.input} type="number" min="0" max="20" value={skipRows} onChange={e => handleSkipChange(parseInt(e.target.value)||0)} />
              </div>
              <div />
            </div>
            <div style={{ ...css.grid2, marginBottom:16 }}>
              {[["dateCol","Date *"],["descCol","Description *"],["amountCol","Amount *"],["balanceCol","Balance (optional)"]].map(([key,label]) => (
                <div key={key}>
                  <label style={css.label}>{label}</label>
                  <select style={css.select} value={mapping[key]||""} onChange={e => setMapping(m=>({...m,[key]:e.target.value}))}>
                    {colOptions.map(o => <option key={o} value={o}>{o || "— skip —"}</option>)}
                  </select>
                </div>
              ))}
            </div>
            {err && <div style={{ color:C.red, fontSize:11, marginBottom:12 }}>{err}</div>}
            <div style={{ display:"flex", gap:10 }}>
              <button style={css.btnGhost} onClick={reset}>← back</button>
              <button style={css.btn} onClick={buildPreview}>Preview →</button>
            </div>
          </div>
        )}

        {step === "preview" && (
          <div style={css.card}>
            <div style={{ fontSize:11, color:C.textMuted, marginBottom:16 }}>
              <strong style={{ color:C.text }}>{preview.filter(r=>!r._skip).length}</strong> transactions to import · <strong style={{ color:C.textMuted }}>{preview.filter(r=>r._skip).length}</strong> skipped
            </div>
            <div style={{ overflowX:"auto", maxHeight:400, overflowY:"auto", marginBottom:16 }}>
              <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
                <thead>
                  <tr>{["skip","date","description","amount"].map(h => <th key={h} style={{ textAlign:"left", padding:"6px 8px", color:C.textMuted, borderBottom:`1px solid ${C.border}`, fontSize:9, letterSpacing:"0.12em", textTransform:"uppercase" }}>{h}</th>)}</tr>
                </thead>
                <tbody>
                  {preview.map(r => (
                    <tr key={r._idx} style={{ opacity: r._skip ? 0.3 : 1 }}>
                      <td style={{ padding:"6px 8px", borderBottom:`1px solid ${C.border}` }}>
                        <input type="checkbox" checked={r._skip} onChange={() => setPreview(p => p.map(x => x._idx===r._idx ? {...x,_skip:!x._skip} : x))} />
                      </td>
                      <td style={{ padding:"6px 8px", borderBottom:`1px solid ${C.border}`, color:C.textMuted }}>{r.date}</td>
                      <td style={{ padding:"6px 8px", borderBottom:`1px solid ${C.border}`, maxWidth:280, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{r.description}</td>
                      <td style={{ padding:"6px 8px", borderBottom:`1px solid ${C.border}`, textAlign:"right", fontWeight:600, color: r.amount < 0 ? C.red : C.green }}>{fmtFull(r.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display:"flex", gap:10 }}>
              <button style={css.btnGhost} onClick={() => setStep("map")}>← back</button>
              <button style={css.btn} onClick={confirmImport}>Import {preview.filter(r=>!r._skip).length} transactions →</button>
            </div>
          </div>
        )}

        {step === "done" && (
          <div style={{ ...css.card, textAlign:"center", padding:"48px" }}>
            <div style={{ fontSize:28, marginBottom:12, color:C.green }}>✓</div>
            <div style={{ fontSize:16, fontWeight:700, marginBottom:8 }}>{importedCount} transactions imported</div>
            <div style={{ fontSize:11, color:C.textMuted, marginBottom:24 }}>
              {dupCount > 0 && <span>{dupCount} duplicates skipped · </span>}
              Transfer matching applied automatically.
            </div>
            <div style={{ display:"flex", gap:10, justifyContent:"center" }}>
              <button style={css.btnGhost} onClick={reset}>Import another</button>
              <button style={css.btn} onClick={() => {}}>View ledger →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── ledger page ───────────────────────────────────────────────────────────────

function LedgerPage({ state, dispatch }) {
  const [filterAccount, setFilterAccount] = useState("all");
  const [filterType, setFilterType] = useState("all");
  const [filterCat, setFilterCat] = useState("all");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState({ accountId: state.accounts[0]?.id||"", date: today(), description:"", amount:"", type:"expense", category:"Other" });

  const filtered = useMemo(() => {
    return state.transactions.filter(t => {
      if (filterAccount !== "all" && t.accountId !== filterAccount) return false;
      if (filterType !== "all" && t.type !== filterType) return false;
      if (filterCat !== "all" && t.category !== filterCat) return false;
      if (search && !t.description.toLowerCase().includes(search.toLowerCase())) return false;
      if (dateFrom && t.date < dateFrom) return false;
      if (dateTo && t.date > dateTo) return false;
      return true;
    }).sort((a,b) => b.date.localeCompare(a.date));
  }, [state.transactions, filterAccount, filterType, filterCat, search, dateFrom, dateTo]);

  function startEdit(t) {
    setEditId(t.id);
    setEditForm({ description: t.description, amount: t.amount, type: t.type, category: t.category, date: t.date });
  }

  function saveEdit() {
    dispatch({ type:"UPDATE_TRANSACTION", payload: { id: editId, changes: { ...editForm, amount: parseFloat(editForm.amount) } } });
    setEditId(null);
  }

  function deleteTx(id) {
    dispatch({ type:"DELETE_TRANSACTION", payload: id });
  }

  function unmatch(matchId) {
    dispatch({ type:"UNMATCH", payload: matchId });
  }

  function addTx() {
    if (!addForm.description || !addForm.amount) return;
    dispatch({ type:"ADD_MANUAL_TRANSACTION", payload: { id: uuid(), ...addForm, amount: parseFloat(addForm.amount), source:"manual", matchId: null } });
    setShowAdd(false);
    setAddForm({ accountId: state.accounts[0]?.id||"", date: today(), description:"", amount:"", type:"expense", category:"Other" });
  }

  const accountName = id => state.accounts.find(a => a.id === id)?.name || id;

  if (state.transactions.length === 0) return (
    <div>
      <div style={css.pageHeader}><div style={css.pageTitle}>Ledger</div></div>
      <div style={css.pageContent}>
        <div style={{ ...css.card, textAlign:"center", padding:"40px", color:C.textMuted, fontSize:12 }}>
          No transactions yet — import a CSV or add one manually.
        </div>
      </div>
    </div>
  );

  return (
    <div>
      <div style={css.pageHeader}>
        <div style={css.pageTitle}>Ledger <span style={{ color:C.textDim }}>({filtered.length})</span></div>
        <button style={css.btn} onClick={() => setShowAdd(!showAdd)}>+ Add</button>
      </div>
      <div style={css.pageContent}>

        {/* filters */}
        <div style={{ ...css.card, marginBottom:16, display:"flex", gap:12, flexWrap:"wrap", alignItems:"flex-end" }}>
          <div style={{ flex:1, minWidth:140 }}>
            <label style={css.label}>Search</label>
            <input style={css.input} value={search} onChange={e => setSearch(e.target.value)} placeholder="description..." />
          </div>
          <div style={{ minWidth:130 }}>
            <label style={css.label}>Account</label>
            <select style={css.select} value={filterAccount} onChange={e => setFilterAccount(e.target.value)}>
              <option value="all">All accounts</option>
              {state.accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
          <div style={{ minWidth:110 }}>
            <label style={css.label}>Type</label>
            <select style={css.select} value={filterType} onChange={e => setFilterType(e.target.value)}>
              <option value="all">All types</option>
              {TX_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div style={{ minWidth:140 }}>
            <label style={css.label}>Category</label>
            <select style={css.select} value={filterCat} onChange={e => setFilterCat(e.target.value)}>
              <option value="all">All categories</option>
              {ALL_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ minWidth:120 }}>
            <label style={css.label}>From</label>
            <input style={css.input} type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          </div>
          <div style={{ minWidth:120 }}>
            <label style={css.label}>To</label>
            <input style={css.input} type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
          </div>
        </div>

        {/* add form */}
        {showAdd && (
          <div style={{ ...css.card, marginBottom:16, background: C.bg, border:`1px solid ${C.accent}44` }}>
            <div style={css.cardTitle}>Add transaction</div>
            <div style={{ display:"flex", gap:12, flexWrap:"wrap", alignItems:"flex-end" }}>
              <div style={{ flex:2, minWidth:160 }}>
                <label style={css.label}>Description</label>
                <input style={css.input} value={addForm.description} onChange={e => setAddForm(f=>({...f,description:e.target.value}))} placeholder="e.g. Coffee" />
              </div>
              <div style={{ flex:1, minWidth:100 }}>
                <label style={css.label}>Amount</label>
                <input style={css.input} type="number" value={addForm.amount} onChange={e => setAddForm(f=>({...f,amount:e.target.value}))} placeholder="0.00" step="0.01" />
              </div>
              <div style={{ minWidth:120 }}>
                <label style={css.label}>Date</label>
                <input style={css.input} type="date" value={addForm.date} onChange={e => setAddForm(f=>({...f,date:e.target.value}))} />
              </div>
              <div style={{ minWidth:110 }}>
                <label style={css.label}>Type</label>
                <select style={css.select} value={addForm.type} onChange={e => setAddForm(f=>({...f,type:e.target.value}))}>
                  {TX_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div style={{ minWidth:140 }}>
                <label style={css.label}>Category</label>
                <select style={css.select} value={addForm.category} onChange={e => setAddForm(f=>({...f,category:e.target.value}))}>
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div style={{ minWidth:130 }}>
                <label style={css.label}>Account</label>
                <select style={css.select} value={addForm.accountId} onChange={e => setAddForm(f=>({...f,accountId:e.target.value}))}>
                  {state.accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              <button style={css.btn} onClick={addTx}>Save</button>
              <button style={css.btnGhost} onClick={() => setShowAdd(false)}>Cancel</button>
            </div>
          </div>
        )}

        {/* table */}
        <div style={css.card}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
            <thead>
              <tr>{["date","description","account","type","category","amount",""].map(h => (
                <th key={h} style={{ textAlign: h==="amount" ? "right" : "left", padding:"6px 8px", color:C.textMuted, borderBottom:`1px solid ${C.border}`, fontSize:9, letterSpacing:"0.12em", textTransform:"uppercase" }}>{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                editId === t.id ? (
                  <tr key={t.id} style={{ background: C.bg }}>
                    <td style={{ padding:"6px 8px" }}><input style={{ ...css.input, padding:"4px 8px", fontSize:11 }} type="date" value={editForm.date} onChange={e => setEditForm(f=>({...f,date:e.target.value}))} /></td>
                    <td style={{ padding:"6px 8px" }}><input style={{ ...css.input, padding:"4px 8px", fontSize:11 }} value={editForm.description} onChange={e => setEditForm(f=>({...f,description:e.target.value}))} /></td>
                    <td style={{ padding:"6px 8px" }}><span style={{ color:C.textMuted, fontSize:10 }}>{accountName(t.accountId)}</span></td>
                    <td style={{ padding:"6px 8px" }}>
                      <select style={{ ...css.select, padding:"4px 8px", fontSize:11 }} value={editForm.type} onChange={e => setEditForm(f=>({...f,type:e.target.value}))}>
                        {TX_TYPES.map(tp => <option key={tp} value={tp}>{tp}</option>)}
                      </select>
                    </td>
                    <td style={{ padding:"6px 8px" }}>
                      <select style={{ ...css.select, padding:"4px 8px", fontSize:11 }} value={editForm.category} onChange={e => setEditForm(f=>({...f,category:e.target.value}))}>
                        {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </td>
                    <td style={{ padding:"6px 8px" }}><input style={{ ...css.input, padding:"4px 8px", fontSize:11, textAlign:"right" }} type="number" value={editForm.amount} onChange={e => setEditForm(f=>({...f,amount:e.target.value}))} step="0.01" /></td>
                    <td style={{ padding:"6px 8px" }}>
                      <div style={{ display:"flex", gap:6 }}>
                        <button style={{ ...css.btn, padding:"4px 10px", fontSize:9 }} onClick={saveEdit}>✓</button>
                        <button style={{ ...css.btnGhost, padding:"4px 10px", fontSize:9 }} onClick={() => setEditId(null)}>✕</button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  <tr key={t.id} style={{ cursor:"pointer" }} onDoubleClick={() => startEdit(t)}>
                    <td style={{ padding:"8px 8px", borderBottom:`1px solid ${C.border}`, color:C.textMuted, whiteSpace:"nowrap" }}>{t.date}</td>
                    <td style={{ padding:"8px 8px", borderBottom:`1px solid ${C.border}`, maxWidth:240, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                      {t.description}
                      {t.matchId && <span style={{ marginLeft:6, fontSize:8, color:C.blue, letterSpacing:"0.1em" }}>{t._nearMatch ? "≈match" : "↔match"}</span>}
                    </td>
                    <td style={{ padding:"8px 8px", borderBottom:`1px solid ${C.border}`, color:C.textMuted, fontSize:10 }}>{accountName(t.accountId)}</td>
                    <td style={{ padding:"8px 8px", borderBottom:`1px solid ${C.border}` }}><TypeBadge type={t.type} /></td>
                    <td style={{ padding:"8px 8px", borderBottom:`1px solid ${C.border}` }}><CatBadge cat={t.category} /></td>
                    <td style={{ padding:"8px 8px", borderBottom:`1px solid ${C.border}`, textAlign:"right", fontWeight:600, color: t.amount < 0 ? C.red : C.green, whiteSpace:"nowrap" }}>{fmtFull(t.amount)}</td>
                    <td style={{ padding:"8px 8px", borderBottom:`1px solid ${C.border}` }}>
                      <div style={{ display:"flex", gap:6, justifyContent:"flex-end" }}>
                        {t.matchId && <button style={{ ...css.btnGhost, padding:"3px 8px", fontSize:8, color:C.blue, borderColor:C.blue+"44" }} onClick={() => unmatch(t.matchId)}>unmatch</button>}
                        <button style={{ ...css.btnGhost, padding:"3px 8px", fontSize:8 }} onClick={() => startEdit(t)}>edit</button>
                        <button style={{ ...css.btnDanger, padding:"3px 8px", fontSize:8 }} onClick={() => deleteTx(t.id)}>×</button>
                      </div>
                    </td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── dashboard page ────────────────────────────────────────────────────────────

function DashboardPage({ state }) {
  const [filterAccount, setFilterAccount] = useState("all");
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date(); d.setMonth(d.getMonth()-3);
    return d.toISOString().slice(0,10);
  });
  const [dateTo, setDateTo] = useState(today());
  const [granularity, setGranularity] = useState("month");

  const filtered = useMemo(() => state.transactions.filter(t => {
    if (filterAccount !== "all" && t.accountId !== filterAccount) return false;
    if (dateFrom && t.date < dateFrom) return false;
    if (dateTo && t.date > dateTo) return false;
    return true;
  }), [state.transactions, filterAccount, dateFrom, dateTo]);

  const netWorth = useMemo(() => state.accounts.reduce((s, a) => {
    const txTotal = state.transactions.filter(t => t.accountId === a.id && t.type !== "transfer").reduce((acc, t) => acc + t.amount, 0);
    return s + a.openingBalance + txTotal;
  }, 0), [state.accounts, state.transactions]);

  const realTxs = filtered.filter(t => t.type !== "transfer" && t.type !== "investment");
  const netIn = realTxs.filter(t => t.amount > 0).reduce((s,t) => s + t.amount, 0);
  const netOut = realTxs.filter(t => t.amount < 0).reduce((s,t) => s + Math.abs(t.amount), 0);

  // monthly series
  const monthlySeries = useMemo(() => {
    const map = {};
    state.transactions.filter(t => t.type !== "transfer" && t.type !== "investment").forEach(t => {
      const key = t.date.slice(0, granularity === "month" ? 7 : 4);
      if (!map[key]) map[key] = { key, in: 0, out: 0 };
      if (t.amount > 0) map[key].in += t.amount;
      else map[key].out += Math.abs(t.amount);
    });
    return Object.values(map).sort((a,b) => a.key.localeCompare(b.key)).slice(-18);
  }, [state.transactions, granularity]);

  // net worth over time
  const netWorthSeries = useMemo(() => {
    if (!monthlySeries.length) return [];
    let running = state.accounts.reduce((s,a) => s + a.openingBalance, 0);
    return monthlySeries.map(m => {
      const txsInPeriod = state.transactions.filter(t => t.type !== "transfer" && t.date.startsWith(m.key));
      running += txsInPeriod.reduce((s,t) => s + t.amount, 0);
      return { key: m.key, netWorth: Math.round(running) };
    });
  }, [monthlySeries, state.accounts, state.transactions]);

  const combinedSeries = monthlySeries.map((m, i) => ({
    key: m.key,
    "Net In": Math.round(m.in),
    "Net Out": Math.round(m.out),
    "Net Worth": netWorthSeries[i]?.netWorth || 0,
  }));

  // by category
  const byCategory = useMemo(() => {
    const map = {};
    filtered.filter(t => t.type === "expense" || (t.type !== "transfer" && t.type !== "investment" && t.amount < 0)).forEach(t => {
      const cat = t.category || "Other";
      map[cat] = (map[cat] || 0) + Math.abs(t.amount);
    });
    return Object.entries(map).sort((a,b) => b[1]-a[1]).map(([name,value]) => ({ name, value: Math.round(value) }));
  }, [filtered]);

  const accountBars = state.accounts.map(a => {
    const bal = a.openingBalance + state.transactions.filter(t => t.accountId === a.id && t.type !== "transfer").reduce((s,t) => s+t.amount, 0);
    return { name: a.name, balance: Math.round(bal) };
  });

  if (state.accounts.length === 0) return (
    <div style={css.pageContent}>
      <div style={{ ...css.card, textAlign:"center", padding:"40px", color:C.textMuted, fontSize:12 }}>
        Add accounts and import transactions to see your dashboard.
      </div>
    </div>
  );

  return (
    <div>
      <div style={css.pageHeader}>
        <div style={css.pageTitle}>Dashboard</div>
        <div style={{ display:"flex", gap:10, alignItems:"center" }}>
          <select style={{ ...css.select, width:"auto" }} value={filterAccount} onChange={e => setFilterAccount(e.target.value)}>
            <option value="all">All accounts</option>
            {state.accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
          <input style={{ ...css.input, width:130 }} type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          <span style={{ color:C.textDim, fontSize:11 }}>→</span>
          <input style={{ ...css.input, width:130 }} type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
          <select style={{ ...css.select, width:"auto" }} value={granularity} onChange={e => setGranularity(e.target.value)}>
            <option value="month">Monthly</option>
            <option value="year">Yearly</option>
          </select>
        </div>
      </div>
      <div style={css.pageContent}>

        {/* KPIs */}
        <div style={{ ...css.grid4, marginBottom:24 }}>
          <KPICard label="Net Worth" value={`${netWorth < 0 ? "-" : ""}${fmt(netWorth)}`} color={netWorth >= 0 ? C.text : C.red} />
          <KPICard label="Net In" value={fmt(netIn)} color={C.green} sub="income · transfers excluded" />
          <KPICard label="Net Out" value={fmt(netOut)} color={C.red} sub="expenses · transfers excluded" />
          <KPICard label="Net Flow" value={`${netIn - netOut >= 0 ? "+" : "-"}${fmt(Math.abs(netIn - netOut))}`} color={netIn >= netOut ? C.green : C.red} sub="in minus out" />
        </div>

        {/* time series */}
        <div style={{ ...css.card, marginBottom:24 }}>
          <div style={css.cardTitle}>Net In / Out / Net Worth over time</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={combinedSeries} margin={{ top:4, right:8, left:-10, bottom:0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis dataKey="key" tick={{ fill:C.textMuted, fontSize:9 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill:C.textMuted, fontSize:9 }} axisLine={false} tickLine={false} tickFormatter={v => `$${Math.round(v/1000)}k`} />
              <Tooltip content={<ChartTooltip />} />
              <Legend iconType="circle" iconSize={6} formatter={v => <span style={{ color:C.textMuted, fontSize:9, letterSpacing:"0.1em" }}>{v}</span>} />
              <Line type="monotone" dataKey="Net In" stroke={C.green} dot={false} strokeWidth={1.5} />
              <Line type="monotone" dataKey="Net Out" stroke={C.red} dot={false} strokeWidth={1.5} />
              <Line type="monotone" dataKey="Net Worth" stroke={C.accent} dot={false} strokeWidth={2} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{ ...css.grid2, marginBottom:24 }}>
          {/* spending by category */}
          <div style={css.card}>
            <div style={css.cardTitle}>Spending by category</div>
            {byCategory.length === 0 ? <div style={{ color:C.textDim, fontSize:11 }}>No expense data.</div> : (
              <>
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie data={byCategory} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={2}>
                      {byCategory.map(e => <Cell key={e.name} fill={CAT_COLORS[e.name] || C.textMuted} />)}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ marginTop:8 }}>
                  {byCategory.slice(0,6).map(e => {
                    const total = byCategory.reduce((s,x) => s+x.value, 0);
                    return (
                      <div key={e.name} style={{ display:"flex", alignItems:"center", gap:8, marginBottom:6 }}>
                        <div style={{ width:6, height:6, borderRadius:1, background: CAT_COLORS[e.name] || C.textMuted, flexShrink:0 }} />
                        <div style={{ fontSize:10, flex:1, color:C.textMuted }}>{e.name}</div>
                        <div style={{ fontSize:10, fontWeight:600 }}>{fmt(e.value)}</div>
                        <div style={{ fontSize:9, color:C.textDim, width:32, textAlign:"right" }}>{Math.round(e.value/total*100)}%</div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* account balances */}
          <div style={css.card}>
            <div style={css.cardTitle}>Account balances</div>
            {accountBars.length === 0 ? <div style={{ color:C.textDim, fontSize:11 }}>No accounts.</div> : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={accountBars} layout="vertical" margin={{ top:4, right:8, left:0, bottom:0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} horizontal={false} />
                  <XAxis type="number" tick={{ fill:C.textMuted, fontSize:9 }} axisLine={false} tickLine={false} tickFormatter={v => `$${Math.round(v/1000)}k`} />
                  <YAxis type="category" dataKey="name" tick={{ fill:C.textMuted, fontSize:10 }} axisLine={false} tickLine={false} width={100} />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="balance" radius={[0,2,2,0]}>
                    {accountBars.map((e,i) => <Cell key={i} fill={e.balance >= 0 ? C.green : C.red} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}

            {/* monthly bar */}
            <div style={{ marginTop:16 }}>
              <div style={css.cardTitle}>Monthly spend</div>
              <ResponsiveContainer width="100%" height={120}>
                <BarChart data={combinedSeries.slice(-8)} margin={{ top:4, right:0, left:-20, bottom:0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false} />
                  <XAxis dataKey="key" tick={{ fill:C.textMuted, fontSize:9 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill:C.textMuted, fontSize:8 }} axisLine={false} tickLine={false} tickFormatter={v => `$${Math.round(v/1000)}k`} />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar dataKey="Net Out" fill={C.red} radius={[2,2,0,0]} opacity={0.8} />
                  <Bar dataKey="Net In" fill={C.green} radius={[2,2,0,0]} opacity={0.8} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── data export/restore ───────────────────────────────────────────────────────

function SettingsPage({ state, dispatch }) {
  const fileRef = useRef();

  function exportData() {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type:"application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `fintrack_backup_${today()}.json`;
    a.click(); URL.revokeObjectURL(url);
  }

  function importData(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        const data = JSON.parse(ev.target.result);
        if (!data.accounts || !data.transactions) { alert("Invalid backup file."); return; }
        dispatch({ type:"RESTORE", payload: data });
        alert(`Restored: ${data.accounts.length} accounts, ${data.transactions.length} transactions.`);
      } catch { alert("Could not parse file."); }
    };
    reader.readAsText(file);
  }

  function clearAll() {
    if (window.confirm("Delete ALL data? This cannot be undone.")) {
      dispatch({ type:"RESET" });
    }
  }

  const txCount = state.transactions.length;
  const matchedCount = new Set(state.transactions.filter(t => t.matchId).map(t => t.matchId)).size;

  return (
    <div>
      <div style={css.pageHeader}><div style={css.pageTitle}>Settings</div></div>
      <div style={css.pageContent}>
        <div style={{ ...css.card, marginBottom:16 }}>
          <div style={css.cardTitle}>Data summary</div>
          <div style={{ fontSize:12, color:C.textMuted, lineHeight:2 }}>
            <div>{state.accounts.length} accounts · {txCount} transactions · {matchedCount} transfer pairs matched</div>
            <div style={{ fontSize:10, color:C.textDim }}>Stored in browser localStorage</div>
          </div>
        </div>

        <div style={{ ...css.card, marginBottom:16 }}>
          <div style={css.cardTitle}>Backup & restore</div>
          <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
            <button style={css.btn} onClick={exportData}>Export JSON backup</button>
            <button style={css.btnGhost} onClick={() => fileRef.current?.click()}>Restore from JSON</button>
            <input ref={fileRef} type="file" accept=".json" style={{ display:"none" }} onChange={importData} />
          </div>
          <div style={{ fontSize:10, color:C.textDim, marginTop:10 }}>Export regularly to avoid data loss if browser storage is cleared.</div>
        </div>

        <div style={css.card}>
          <div style={css.cardTitle}>Danger zone</div>
          <button style={css.btnDanger} onClick={clearAll}>Clear all data</button>
        </div>
      </div>
    </div>
  );
}

// ── reducer ───────────────────────────────────────────────────────────────────

function reducer(state, action) {
  let next;
  switch (action.type) {
    case "ADD_ACCOUNT":
      next = { ...state, accounts: [...state.accounts, action.payload] };
      break;
    case "REMOVE_ACCOUNT":
      next = { ...state, accounts: state.accounts.filter(a => a.id !== action.payload) };
      break;
    case "SAVE_FORMAT_PROFILE":
      next = { ...state, formatProfiles: { ...state.formatProfiles, [action.payload.accountId]: action.payload.profile } };
      break;
    case "IMPORT_TRANSACTIONS": {
      const merged = [...state.transactions, ...action.payload];
      const matched = runTransferMatching(merged);
      next = { ...state, transactions: matched };
      break;
    }
    case "ADD_MANUAL_TRANSACTION": {
      const merged = [...state.transactions, action.payload];
      const matched = runTransferMatching(merged);
      next = { ...state, transactions: matched };
      break;
    }
    case "UPDATE_TRANSACTION":
      next = { ...state, transactions: state.transactions.map(t => t.id === action.payload.id ? { ...t, ...action.payload.changes } : t) };
      break;
    case "DELETE_TRANSACTION":
      next = { ...state, transactions: state.transactions.filter(t => t.id !== action.payload) };
      break;
    case "UNMATCH":
      next = { ...state, transactions: state.transactions.map(t => t.matchId === action.payload ? { ...t, matchId: null, type: t._originalType || "expense", _nearMatch: false } : t) };
      break;
    case "RESTORE":
      next = { ...DEFAULT_STATE, ...action.payload };
      break;
    case "RESET":
      next = { ...DEFAULT_STATE };
      break;
    default:
      return state;
  }
  saveState(next);
  return next;
}

// ── app ───────────────────────────────────────────────────────────────────────

const NAV = [
  { id:"dashboard", label:"Dashboard", icon:"◈" },
  { id:"accounts",  label:"Accounts",  icon:"⊞" },
  { id:"import",    label:"Import CSV", icon:"↑" },
  { id:"ledger",    label:"Ledger",     icon:"≡" },
  { id:"settings",  label:"Settings",   icon:"⚙" },
];

export default function App() {
  const [state, dispatch] = useState(() => loadState() || DEFAULT_STATE);
  const dispatchFn = useCallback((action) => {
    dispatch(prev => reducer(prev, action));
  }, []);

  const [view, setView] = useState("dashboard");

  return (
    <div style={css.app}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap" rel="stylesheet" />

      {/* sidebar */}
      <div style={css.sidebar}>
        <div style={css.logo}>
          <div style={css.logoText}>fintrack</div>
          <div style={css.logoSub}>v0 · personal finance</div>
        </div>
        <nav>
          {NAV.map(n => (
            <div key={n.id} style={css.navItem(view === n.id)} onClick={() => setView(n.id)}>
              <span style={{ fontSize:12 }}>{n.icon}</span>
              <span>{n.label}</span>
            </div>
          ))}
        </nav>
        <div style={{ marginTop:"auto", padding:"16px 20px", borderTop:`1px solid ${C.border}` }}>
          <div style={{ fontSize:9, color:C.textDim, letterSpacing:"0.1em" }}>{state.accounts.length} accounts · {state.transactions.length} txs</div>
        </div>
      </div>

      {/* main */}
      <div style={css.main}>
        {view === "dashboard" && <DashboardPage state={state} />}
        {view === "accounts"  && <AccountsPage state={state} dispatch={dispatchFn} />}
        {view === "import"    && <ImportPage state={state} dispatch={dispatchFn} />}
        {view === "ledger"    && <LedgerPage state={state} dispatch={dispatchFn} />}
        {view === "settings"  && <SettingsPage state={state} dispatch={dispatchFn} />}
      </div>
    </div>
  );
}
