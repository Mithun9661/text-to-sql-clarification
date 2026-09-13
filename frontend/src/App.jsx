import { useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL ||
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000'
    : 'https://text-to-sql-clarification-api.onrender.com');

export default function App() {
  const [question, setQuestion] = useState('');
  const [originalQuestion, setOriginalQuestion] = useState('');
  const [messages, setMessages] = useState([{type:'assistant', text:'Ask a question about your company data. I will clarify ambiguous requests before generating SQL.'}]);
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [connectionId, setConnectionId] = useState('demo');
  const [connectionLabel, setConnectionLabel] = useState('Demo Company Database');
  const [databaseUrl, setDatabaseUrl] = useState('');
  const [companyLabel, setCompanyLabel] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [connectionMessage, setConnectionMessage] = useState('Using built-in demo database');

  async function connectDatabase(e) {
    e.preventDefault();
    if (!databaseUrl.trim() || connecting) return;
    setConnecting(true);
    setConnectionMessage('Connecting and reading schema...');
    try {
      const res = await fetch(`${API_URL}/connect`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({database_url: databaseUrl.trim(), label: companyLabel.trim() || null})
      });
      const data = await res.json();
      if (data.status === 'connected') {
        setConnectionId(data.connection_id);
        setConnectionLabel(data.label);
        setConnectionMessage(`${data.label} connected · ${data.dialect} · ${data.table_count} tables found`);
        setDatabaseUrl('');
        setMessages([{type:'assistant', text:`Connected to ${data.label}. Ask any question about this database.`}]);
        setOptions([]);
      } else {
        setConnectionMessage(data.message || 'Could not connect to the database.');
      }
    } catch {
      setConnectionMessage('Could not reach the backend while connecting the database.');
    } finally {
      setConnecting(false);
    }
  }

  function useDemo() {
    setConnectionId('demo');
    setConnectionLabel('Demo Company Database');
    setConnectionMessage('Using built-in demo database');
    setMessages([{type:'assistant', text:'Demo database selected. Ask a question about customers, orders, payments, or engagements.'}]);
    setOptions([]);
  }

  async function ask(text = question, clarification = null) {
    if (!text.trim() || loading) return;
    const baseQuestion = clarification ? originalQuestion : text.trim();
    if (!clarification) {
      setOriginalQuestion(baseQuestion);
      setMessages(m => [...m, {type:'user', text:baseQuestion}]);
      setQuestion('');
    } else {
      setMessages(m => [...m, {type:'user', text:clarification}]);
    }
    setOptions([]);
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/query`, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({question:baseQuestion, clarification, connection_id:connectionId})
      });
      const data = await res.json();
      if (data.status === 'clarification_required') {
        setMessages(m => [...m, {type:'assistant', text:data.question}]);
        setOptions(data.options || []);
      } else if (data.status === 'success') {
        setMessages(m => [...m, {type:'assistant', text:data.answer, sql:data.sql, result:data.result, explanation:data.explanation}]);
      } else {
        setMessages(m => [...m, {type:'assistant', text:data.message || 'Unable to answer this question.'}]);
      }
    } catch {
      setMessages(m => [...m, {type:'assistant', text:'Could not connect to the backend API.'}]);
    } finally {
      setLoading(false);
    }
  }

  return <main className="shell">
    <header><div className="brand">ClarifySQL <span>AI</span></div><div className="badge">Universal Safe Text-to-SQL</div></header>

    <section className="hero">
      <p className="eyebrow">CLARIFICATION-AWARE ANALYTICS</p>
      <h1>Connect any database.<br/><em>Ask without guessing.</em></h1>
      <p>Connect a PostgreSQL, MySQL, or SQLite database. The system reads its schema, detects ambiguity, generates safe SQL, and returns the answer.</p>
    </section>

    <section className="connect-card">
      <div className="connect-head">
        <div><span className="status-dot"></span><strong>{connectionLabel}</strong><p>{connectionMessage}</p></div>
        <button className="demo-btn" onClick={useDemo}>Use Demo DB</button>
      </div>
      <form className="connect-form" onSubmit={connectDatabase}>
        <input value={companyLabel} onChange={e=>setCompanyLabel(e.target.value)} placeholder="Company name (optional)" />
        <input type="password" value={databaseUrl} onChange={e=>setDatabaseUrl(e.target.value)} placeholder="postgresql://user:password@host:5432/database" autoComplete="off" />
        <button disabled={connecting}>{connecting ? 'Connecting...' : 'Connect Database'}</button>
      </form>
      <p className="hint">Supported: PostgreSQL, MySQL, SQLite. Connection credentials are used by the backend connection session and are not shown in the chat.</p>
    </section>

    <section className="chat">
      <div className="messages">
        {messages.map((m,i)=><div key={i} className={`message ${m.type}`}><div className="bubble">
          {m.text}
          {m.result?.length > 0 && <div className="result-wrap"><table><thead><tr>{Object.keys(m.result[0]).map(k=><th key={k}>{k.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{m.result.map((row,r)=><tr key={r}>{Object.keys(m.result[0]).map(k=><td key={k}>{String(row[k] ?? '')}</td>)}</tr>)}</tbody></table></div>}
          {m.sql && <details><summary>View generated SQL</summary><pre>{m.sql}</pre></details>}
        </div></div>)}
        {loading && <div className="thinking">Analyzing the selected database schema and intent...</div>}
      </div>
      {options.length > 0 && <div className="options">{options.map(o=><button key={o.id} onClick={()=>ask(originalQuestion,o.label)}>{o.label}</button>)}</div>}
      <form className="ask-form" onSubmit={e=>{e.preventDefault();ask();}}><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="e.g. Show me last month's best customer"/><button disabled={loading}>Ask →</button></form>
    </section>
    <footer>Dynamic schema discovery · Ambiguity detection · Read-only SQL · PostgreSQL · MySQL · SQLite</footer>
  </main>;
}
