"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    let mounted = true;

    // A rota de login nunca passa pelo gate
    if (pathname === "/login") {
      setLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!mounted) return;
      if (session) {
        setHasSession(true);
        setLoading(false);
      } else {
        setHasSession(false);
        setLoading(false);
        router.replace("/login");
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!mounted) return;
      if (session) {
        setHasSession(true);
        setLoading(false);
      } else if (pathname !== "/login") {
        setHasSession(false);
        setLoading(false);
        router.replace("/login");
      }
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [pathname, router]);

  // Se for a página de login, renderiza diretamente sem bloquear
  if (pathname === "/login") {
    return <>{children}</>;
  }

  // Estado carregando ou sem sessão: fundo --inst-bg sem flash de UI
  if (loading || !hasSession) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ background: "var(--inst-bg, #0C0E10)" }}
      />
    );
  }

  // Com sessão autenticada: renderiza children normalmente
  return <>{children}</>;
}
