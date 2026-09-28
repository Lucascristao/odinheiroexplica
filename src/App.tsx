import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { AuthPanel } from "./components/AuthPanel";
import { Dashboard } from "./components/Dashboard";
import { isSupabaseConfigured, supabase } from "./lib/supabase";

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [checking, setChecking] = useState(true);
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (!supabase) {
      setChecking(false);
      return;
    }

    async function resolveAccess(nextSession: Session | null) {
      setSession(nextSession);

      if (!nextSession) {
        setAuthorized(false);
        setChecking(false);
        return;
      }

      const {data, error} = await supabase.auth.getUser();
      const isAdmin = !error && data.user?.app_metadata?.role === "admin";

      if (!isAdmin) {
        await supabase.auth.signOut();
        setSession(null);
        setAuthorized(false);
      } else {
        setAuthorized(true);
      }

      setChecking(false);
    }

    void supabase.auth.getSession().then(({data}) => {
      void resolveAccess(data.session);
    });

    const {
      data: {subscription},
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      void resolveAccess(nextSession);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!isSupabaseConfigured) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Configuração necessária</p>
          <h1>Conecte o Supabase</h1>
          <p className="muted">
            A configuração do Supabase ainda não está disponível neste deploy.
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

  return session && authorized ? <Dashboard /> : <AuthPanel />;
}
