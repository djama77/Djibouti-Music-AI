import "./style.css";

const DEMO_URL = "https://huggingface.co/spaces/ACE-Step/Ace-Step-v1.5";

export default function App() {
  return (
    <main className="shell">
      <header className="top">
        <div className="mark" aria-hidden="true">♪</div>
        <div>
          <p className="eyebrow">STUDIO MUSICAL OPEN SOURCE</p>
          <h1>Djibouti Music AI</h1>
          <p className="sub">Tes paroles. Tes langues. Ta musique.</p>
        </div>
      </header>

      <section className="panel">
        <div className="section-title">
          <span>01</span>
          <div>
            <h2>Créer gratuitement une chanson</h2>
            <p>Depuis ton téléphone Android ou ton ordinateur.</p>
          </div>
        </div>

        <div className="intro">
          <p>
            Djibouti Music AI te donne accès à la démonstration publique
            d’ACE-Step 1.5, un modèle open source de génération musicale.
            Aucun logiciel à installer.
          </p>
          <a className="primary-link" href={DEMO_URL} target="_blank" rel="noreferrer">
            ♫ Ouvrir l’atelier de création
          </a>
          <p className="hint">
            L’atelier s’ouvre dans un nouvel onglet. Tu pourras y décrire ton
            morceau, ajouter tes paroles, choisir les paramètres disponibles
            et lancer la génération.
          </p>
        </div>

        <div className="section-title secondary-title">
          <span>02</span>
          <div>
            <h2>Idées musicales</h2>
            <p>Quelques inspirations à essayer dans l’atelier.</p>
          </div>
        </div>
        <div className="ideas">
          <div><strong>Somali traditionnel</strong><span>Oud, kaban, percussions et mélodie chaleureuse</span></div>
          <div><strong>Afar traditionnel</strong><span>Rythmes régionaux et ambiance acoustique</span></div>
          <div><strong>Afrobeat</strong><span>Rythme dansant, basse et instruments modernes</span></div>
          <div><strong>Rap djiboutien</strong><span>Flow énergique et paroles en français ou somali</span></div>
        </div>

        <div className="notice">
          <strong>À savoir sur le mode gratuit</strong>
          <p>
            La démonstration est hébergée par un service externe. Elle peut
            être momentanément occupée, se mettre en veille ou imposer des
            limites d’utilisation. La disponibilité gratuite n’est pas garantie
            en continu.
          </p>
        </div>
        <div className="notice privacy">
          <strong>Respecte ta vie privée</strong>
          <p>
            Les textes envoyés à la démonstration sont traités par son
            hébergeur. N’y saisis pas d’informations personnelles ou
            confidentielles.
          </p>
        </div>
      </section>

      <footer>
        <p>Djibouti Music AI · Projet communautaire indépendant</p>
        <p>
          Modèle : <a href="https://github.com/ACE-Step/ACE-Step-1.5" target="_blank" rel="noreferrer">ACE-Step 1.5</a>
          {" · "}
          <a href="https://huggingface.co/spaces/ACE-Step/Ace-Step-v1.5" target="_blank" rel="noreferrer">Démonstration officielle</a>
        </p>
      </footer>
    </main>
  );
}
