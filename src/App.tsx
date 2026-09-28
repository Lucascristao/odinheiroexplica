import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { AuthPanel } from "./components/AuthPanel";
import { Dashboard } from "./components/Dashboard";
import { RenderStatusPanel } from "./components/RenderStatusPanel";
import { isSupabaseConfigured, supabase } from "./lib/supabase";

function ProductionStatus() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand-title">
            <span className="brand-dot" />
            O Dinheiro Explica
          </div>
          <span className="muted small">Produção automática</span>
        </div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">Status de produção</p>
          <h1>Acompanhe o vídeo sem abrir o GitHub Actions.</h1>
          <p className="muted hero-copy">
            O painel atualiza sozinho enquanto a narração, timeline, render,
            thumbnail e publicação são processados.
          </p>
        </div>
      </section>

      <RenderStatusPanel />
    </main>
  );
}

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [checking, setChecking] = useState(true);

  const isAdminPage =
    window.location.pathname === "/admin" ||
    window.location.pathname === "/admin/";

  useEffect(() => {
    if (!isAdminPage) {
      setChecking(false);
      return;
    }

    if (!supabase) {
      setChecking(false);
      return;
    }

    void supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setChecking(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setChecking(false);
    });

    return () => subscription.unsubscribe();
  }, [isAdminPage]);

  if (!isAdminPage) {
    return <ProductionStatus />;
  }

  if (!isSupabaseConfigured) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Configuração necessária</p>
          <h1>Conecte o Supabase</h1>
          <p className="muted">
            Crie um arquivo <code>.env.local</code> usando o modelo
            <code> .env.example</code> e informe a publishable key do projeto.
          </p>
        </section>
      </main>
    );
  }

  if (checking) {
    return (
      <main className="auth-shell">
        <p className="muted">Carregando painel...</p>
      </main>
    );
  }

  return session ? <Dashboard /> : <AuthPanel />;
}
