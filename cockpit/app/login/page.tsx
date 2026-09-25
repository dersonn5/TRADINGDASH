"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setErrorMessage(error.message);
        setLoading(false);
        return;
      }

      if (data.session) {
        router.replace("/checklist");
      }
    } catch (err: any) {
      setErrorMessage(err?.message || "Erro inesperado ao autenticar");
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "var(--inst-bg, #0C0E10)", color: "var(--inst-text, #E8ECEF)" }}
    >
      <div
        className="w-full max-w-sm rounded p-6 shadow-2xl"
        style={{
          background: "var(--inst-panel, #0F1215)",
          border: "1px solid var(--inst-line, #1E2327)",
        }}
      >
        <div className="mb-6">
          <span
            className="mono tabular block text-xs tracking-widest uppercase"
            style={{ color: "var(--inst-dim, #8A949C)" }}
          >
            INSTRUMENTO DE CONTROLE · COPA BTG
          </span>
          <h1
            className="mono text-lg font-semibold mt-1 tracking-tight"
            style={{ color: "var(--inst-text, #E8ECEF)" }}
          >
            Acesso ao Cockpit
          </h1>
        </div>

        {errorMessage && (
          <div
            className="mb-4 rounded p-3 text-xs mono leading-relaxed"
            style={{
              background: "var(--inst-block-bg, #150F0E)",
              border: "1px solid var(--inst-block-line, #3A1F1C)",
              color: "var(--inst-block, #E0574A)",
            }}
          >
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              className="mono tabular block text-xs mb-1.5 font-medium"
              style={{ color: "var(--inst-dim, #8A949C)" }}
            >
              E-MAIL
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operador@copa.btg"
              disabled={loading}
              className="w-full rounded px-3 py-2 text-sm mono outline-none transition-colors"
              style={{
                background: "var(--inst-bg, #0C0E10)",
                border: "1px solid var(--inst-line, #1E2327)",
                color: "var(--inst-text, #E8ECEF)",
              }}
            />
          </div>

          <div>
            <label
              className="mono tabular block text-xs mb-1.5 font-medium"
              style={{ color: "var(--inst-dim, #8A949C)" }}
            >
              SENHA
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
              className="w-full rounded px-3 py-2 text-sm mono outline-none transition-colors"
              style={{
                background: "var(--inst-bg, #0C0E10)",
                border: "1px solid var(--inst-line, #1E2327)",
                color: "var(--inst-text, #E8ECEF)",
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded py-2.5 px-4 text-xs font-semibold mono tracking-wider uppercase transition-opacity cursor-pointer mt-2"
            style={{
              background: "var(--inst-ok, #3FB27F)",
              color: "var(--onac)",
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? "AUTENTICANDO..." : "ENTRAR"}
          </button>
        </form>
      </div>
    </div>
  );
}
