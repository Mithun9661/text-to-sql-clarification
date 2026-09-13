import { useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function App() {
  const [question, setQuestion] = useState('');
  const [originalQuestion, setOriginalQuestion] = useState('');
  const [messages, setMessages] = useState([{type:'assistant', text:'Ask a question about your company data. I will clarify ambiguous requests before generating SQL.'}]);
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);

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
    setOptions([]); setLoading(true);
    try {
      const res = await fetch(`${API_URL}/query`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:baseQuestion, clarification})});
      const data = await res.json();
      if (data.status === 'clarification_required') {
        setMessages(m => [...m, {type:'assistant', text:data.question}]);
        setOptions(data.options || []);
      } else if (data.status === 'success') {
        setMessages(m => [...m, {type:'assistant', text:data.answer, sql:data.sql, result:data.result}]);
      } else {
        setMessages(m => [...m, {type:'assistant', text:data.message || 'Unable to answer this question.'}]);
      }
    } catch {
      setMessages(m => [...m, {type:'assistant', text:'Could not connect to the backend API.'}]);
    } finally { setLoading(false); }
  }

  return <main className="shell">
    <header><div className="brand">ClarifySQL <span>AI</span></div><div className="badge">Safe Text-to-SQL</div></header>
    <section className="hero"><p className="eyebrow">CLARIFICATION-AWARE ANALYTICS</p><h1>Ask your database.<br/><em>Without the guessing.</em></h1><p>Natural language questions become safe SQL. If your request has multiple meanings, the AI asks first.</p></section>
    <section className="chat">
      <div className="messages">{messages.map((m,i)=><div key={i} className={`message ${m.type}`}><div className="bubble">{m.text}{m.sql && <details><summary>View generated SQL</summary><pre>{m.sql}</pre></details>}</div></div>)}{loading && <div className="thinking">Analyzing schema and intent...</div>}</div>
      {options.length > 0 && <div className="options">{options.map(o=><button key={o.id} onClick={()=>ask(originalQuestion,o.id)}>{o.label}</button>)}</div>}
      <form onSubmit={e=>{e.preventDefault();ask();}}><input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="e.g. Show me last month's best customer"/><button disabled={loading}>Ask →</button></form>
    </section>
    <footer>Ambiguity detection · Read-only SQL · Schema-aware AI</footer>
  </main>;
}
