import { useState } from "react";

const API = import.meta.env.VITE_API_BASE_URL || "";

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [lyrics, setLyrics] = useState("");
  const [token, setToken] = useState("");
  const [duration, setDuration] = useState(30);
  const [language, setLanguage] = useState("so");
  const [format, setFormat] = useState("mp3");
  const [task, setTask] = useState(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function generate(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setTask(null);
    try {
      const response = await fetch(`${API}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-App-Token": token },
        body: JSON.stringify({ prompt, lyrics, duration: Number(duration), vocal_language: language, audio_format: format })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "La demande n'a pas abouti.");
      setTask({ id: data.task_id, status: "queued" });
      setMessage("Demande envoyée. La génération peut prendre plusieurs minutes.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function checkStatus() {
    if (!task?.id) return;
    setBusy(true);
    try {
      const response = await fetch(`${API}/api/tasks/${encodeURIComponent(task.id)}`, {
        headers: { "X-App-Token": token }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Impossible de lire le statut.");
      setTask(data);
      setMessage(data.status === 1 ? "Création terminée. Consulte le résultat renvoyé par ACE-Step." : data.status === 2 ? "La génération a échoué. Réessaie avec une description plus simple." : "Création en cours…");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header className="top">
        <div className="mark">DJ<span>♪</span></div>
        <div><p className="eyebrow">STUDIO MUSICAL IA</p><h1>Djibouti Music AI</h1></div>
        <span className="status">BÊTA</span>
      </header>
      <section className="intro">
        <p className="eyebrow">TON IDÉE, TON UNIVERS</p>
        <h2>Donne vie à tes idées musicales.</h2>
        <p>Décris une ambiance, un rythme ou un instrument. Le moteur ACE-Step transforme ta description en projet musical.</p>
      </section>
      <form className="panel" onSubmit={generate}>
        <label>Clé d’accès de l’application
          <input value={token} onChange={e => setToken(e.target.value)} type="password" autoComplete="off" placeholder="Fournie par l’administrateur" required />
        </label>
        <label>Description musicale
          <textarea value={prompt} onChange={e => setPrompt(e.target.value)} maxLength={2000} rows={4} required minLength={3} placeholder="Ex. : instrumental chaleureux, oud, kaban, percussions légères, ambiance paisible…" />
        </label>
        <label>Paroles (facultatif)
          <textarea value={lyrics} onChange={e => setLyrics(e.target.value)} maxLength={4000} rows={3} placeholder="Ajoute tes propres paroles…" />
        </label>
        <div className="controls">
          <label>Durée
            <select value={duration} onChange={e => setDuration(e.target.value)}>
              <option value="30">30 secondes</option><option value="60">1 minute</option><option value="90">1 min 30</option><option value="120">2 minutes</option><option value="180">3 minutes</option>
            </select>
          </label>
          <label>Langue
            <select value={language} onChange={e => setLanguage(e.target.value)}>
              <option value="so">Somali</option><option value="ar">Arabe</option><option value="fr">Français</option><option value="en">Anglais</option><option value="am">Amharique</option>
            </select>
          </label>
          <label>Format
            <select value={format} onChange={e => setFormat(e.target.value)}>
              <option value="mp3">MP3</option><option value="wav">WAV</option><option value="flac">FLAC</option>
            </select>
          </label>
        </div>
        <button disabled={busy || prompt.trim().length < 3 || !token.trim()}>{busy ? "Patiente…" : "Lancer la création  →"}</button>
        {message && <p className="message" role="status">{message}</p>}
        {task?.id && <div className="task"><div><b>Projet : {task.id}</b><small>Statut ACE-Step : {task.status === 1 ? "terminé" : task.status === 2 ? "échec" : "en attente / en cours"}</small></div><button type="button" className="secondary" onClick={checkStatus} disabled={busy}>Vérifier le statut</button></div>}
      </form>
      <footer>Propulsé par ACE-Step 1.5 · Le service GPU doit être configuré séparément.</footer>
    </main>
  );
}
