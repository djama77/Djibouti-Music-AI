import { useEffect, useState } from "react";

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
  const [audioBlobUrl, setAudioBlobUrl] = useState("");

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
      setTask({ id: data.task_id, status: 0, result: [], audio_url: null });
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
      setTask({ ...data, id: task.id });
      setMessage(data.status === 1 ? (data.audio_url ? "Ta création est prête. Tu peux l’écouter ou la télécharger." : "Génération terminée, mais aucun fichier audio n’a été fourni.") : data.status === 2 ? "La génération a échoué. Réessaie avec une description différente." : "Création en cours…");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!task?.audio_url || !token) {
      setAudioBlobUrl("");
      return undefined;
    }

    const controller = new AbortController();
    let objectUrl;

    setAudioBlobUrl("");
    fetch(`${API}${task.audio_url}`, {
      headers: { "X-App-Token": token },
      signal: controller.signal,
    })
      .then(async response => {
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.detail || "Impossible de récupérer le fichier audio.");
        }
        return response.blob();
      })
      .then(blob => {
        objectUrl = URL.createObjectURL(blob);
        setAudioBlobUrl(objectUrl);
      })
      .catch(error => {
        if (!controller.signal.aborted) setMessage(error.message);
      });

    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [task?.audio_url, token]);

  const audioSrc = audioBlobUrl;

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
              <option value="so">Somali</option><option value="aa">Afar</option><option value="ar">Arabe</option><option value="fr">Français</option><option value="en">Anglais</option><option value="am">Amharique</option>
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
        {task?.id && <div className="task">
          <div><b>Projet : {task.id}</b><small>Statut : {task.status === 1 ? "terminé" : task.status === 2 ? "échec" : "en attente / en cours"}</small></div>
          <button type="button" className="secondary" onClick={checkStatus} disabled={busy}>Vérifier le statut</button>
        </div>}
        {task?.audio_url && <section className="audio-result" aria-label="Résultat audio">
          <h3>Ta création musicale</h3>
          {audioSrc ? (
            <>
              <audio controls preload="metadata" src={audioSrc}>Ton navigateur ne prend pas en charge la lecture audio.</audio>
              <a className="download" href={audioSrc} download={`djibouti-music-${task.id}`}>↓ Télécharger le fichier audio</a>
            </>
          ) : <p className="message">Chargement du fichier audio…</p>}
          <small>Le fichier est récupéré avec le jeton d’accès, puis lu depuis le navigateur.</small>
        </section>}
        {task?.result?.length > 0 && <details className="metadata">
          <summary>Détails de la génération</summary>
          <pre>{JSON.stringify(task.result[0].metas || {}, null, 2)}</pre>
        </details>}
      </form>
      <footer>Propulsé par ACE-Step 1.5 · Le service GPU doit être configuré séparément.</footer>
    </main>
  );
}
