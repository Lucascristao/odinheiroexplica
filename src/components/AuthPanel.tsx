import {FormEvent, useState} from "react";
import {LockKeyhole} from "lucide-react";
import {supabase} from "../lib/supabase";

export function AuthPanel() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!supabase) return;

    setBusy(true);
    setMessage(null);

    const result = await supabase.auth.signInWithPassword({email, password});

    if (result.error) {
      setMessage("E-mail ou senha inválidos.");
    }

    setBusy(false);
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-mark" aria-hidden="true">
          <LockKeyhole size={28} />
        </div>
        <p className="eyebrow">O Dinheiro Explica</p>
        <h1>Painel editorial</h1>
        <p className="muted">
          Acesso privado para pesquisa, roteiro, produção e acompanhamento dos vídeos.
        </p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            E-mail
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            Senha
            <input
              type="password"
              autoComplete="current-password"
              minLength={6}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {message && <div className="notice">{message}</div>}

          <button className="primary-button" disabled={busy}>
            {busy ? "Aguarde..." : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}
