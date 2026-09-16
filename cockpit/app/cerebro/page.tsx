"use client";

import { useEffect, useState } from "react";
import { fetchNotes, saveNote, deleteNote, TradingNote } from "@/lib/trading-db";
import {
  InstPage,
  InstCard,
  InstLabel,
  InstBadge,
  InstEmpty,
} from "@/components/inst";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Plus, Search, Trash2 } from "lucide-react";

const CAMADA_INFO: Record<number, { name: string; desc: string }> = {
  1: {
    name: "Camada 1 — Conceitos Atômicos",
    desc: "Definições puras de mercado: FVG, Order Blocks, Liquidez BSL/SSL",
  },
  2: {
    name: "Camada 2 — Regras & Filtros",
    desc: "Condições de combinação, horários de Killzones, filtros macro",
  },
  3: {
    name: "Camada 3 — Modelos & Setups",
    desc: "Estratégias validadas: Silver Bullet, Judas Swing, Breaker Block",
  },
  4: {
    name: "Camada 4 — Sistema & Execução",
    desc: "Mapeamento operacional, condução de trade e circuit breakers",
  },
  5: {
    name: "Camada 5 — Sabedoria & Diário",
    desc: "Casos reais de mercado, lições aprendidas e erros evitados",
  },
};

export default function CerebroPage() {
  const [notes, setNotes] = useState<TradingNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCamada, setSelectedCamada] = useState<number | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Form State
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newCamada, setNewCamada] = useState<number>(1);
  const [newCategoria, setNewCategoria] = useState("ICT");
  const [newTags, setNewTags] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadNotes();
  }, []);

  async function loadNotes() {
    setLoading(true);
    const data = await fetchNotes();
    setNotes(data);
    setLoading(false);
  }

  async function handleCreateNote() {
    if (!newTitle.trim() || !newContent.trim()) return;
    setSaving(true);
    const tagsArray = newTags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    await saveNote({
      title: newTitle.trim(),
      content: newContent.trim(),
      camada: newCamada,
      categoria: newCategoria,
      status: "validado",
      tags: tagsArray,
      linked_notes: [],
    });

    // Reset Form
    setNewTitle("");
    setNewContent("");
    setNewTags("");
    setNewCamada(1);
    setIsDialogOpen(false);
    setSaving(false);
    await loadNotes();
  }

  async function handleDelete(id: string) {
    if (confirm("Tem certeza que deseja excluir esta nota do Segundo Cérebro?")) {
      await deleteNote(id);
      await loadNotes();
    }
  }

  const filteredNotes = notes.filter((n) => {
    const matchesSearch =
      n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCamada = selectedCamada === null || n.camada === selectedCamada;
    return matchesSearch && matchesCamada;
  });

  const inputStyle: React.CSSProperties = {
    background: "var(--inst-panel-2)",
    border: "1px solid var(--inst-line)",
    color: "var(--inst-text)",
    borderRadius: "3px",
    padding: "8px 12px",
    fontSize: "13px",
    outline: "none",
    width: "100%",
  };

  return (
    <InstPage
      eyebrow="OBSIDIAN · BASE COGNITIVA"
      title="Segundo Cérebro · Base Cognitiva"
      right={
        <button
          type="button"
          onClick={() => setIsDialogOpen(true)}
          className="mono tabular"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            background: "var(--inst-ok)",
            border: "1px solid var(--inst-ok)",
            color: "var(--inst-on-ok)",
            borderRadius: "3px",
            padding: "6px 14px",
            fontSize: "11px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          <Plus style={{ width: "14px", height: "14px" }} /> Nova Nota Neural
        </button>
      }
    >
      {/* Header */}
      <div style={{ fontSize: "12px", color: "var(--inst-dim)", marginTop: "-12px", marginBottom: "8px" }}>
        Conhecimento arquitetado em 5 camadas neurais (Conceitos, Regras, Modelos, Sistema e Sabedoria).
      </div>

      {/* Botão e Modal de Nova Nota */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg">
            Registrar no Segundo Cérebro
          </DialogTitle>
        </DialogHeader>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px", paddingTop: "8px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <InstLabel>Título do Conceito / Regra</InstLabel>
            <input
              placeholder="Ex: Fair Value Gap Institucional"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Camada Cognitiva</InstLabel>
              <select
                className="mono"
                style={{ ...inputStyle, height: "37px" }}
                value={newCamada}
                onChange={(e) => setNewCamada(Number(e.target.value))}
              >
                <option value={1}>Camada 1 — Conceito Atômico</option>
                <option value={2}>Camada 2 — Regra & Filtro</option>
                <option value={3}>Camada 3 — Modelo & Setup</option>
                <option value={4}>Camada 4 — Sistema & Condução</option>
                <option value={5}>Camada 5 — Sabedoria & Diário</option>
              </select>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <InstLabel>Categoria</InstLabel>
              <input
                placeholder="ICT, B05 Trade System, DIARIO"
                value={newCategoria}
                onChange={(e) => setNewCategoria(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <InstLabel>Tags (separadas por vírgula)</InstLabel>
            <input
              placeholder="Ex: FVG, Liquidez, Sweep, Killzone"
              value={newTags}
              onChange={(e) => setNewTags(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <InstLabel>Conteúdo da Nota (Markdown)</InstLabel>
            <textarea
              placeholder="Descreva a regra, lógica operacional, gatilho ou lição aprendida..."
              rows={6}
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              className="mono"
              style={{ ...inputStyle, fontSize: "12px", lineHeight: 1.5 }}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", paddingTop: "8px" }}>
            <button
              type="button"
              onClick={() => setIsDialogOpen(false)}
              className="mono tabular"
              style={{
                background: "transparent",
                border: "1px solid var(--inst-line)",
                color: "var(--inst-dim)",
                borderRadius: "3px",
                padding: "8px 16px",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleCreateNote}
              disabled={saving || !newTitle.trim() || !newContent.trim()}
              className="mono tabular"
              style={{
                background: "var(--inst-ok)",
                border: "1px solid var(--inst-ok)",
                color: "var(--inst-on-ok)",
                borderRadius: "3px",
                padding: "8px 16px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: saving || !newTitle.trim() || !newContent.trim() ? "not-allowed" : "pointer",
                opacity: saving || !newTitle.trim() || !newContent.trim() ? 0.6 : 1,
              }}
            >
              {saving ? "Salvando no Supabase..." : "Salvar Conhecimento"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Camadas Filter Bar */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "8px" }}>
        <button
          type="button"
          onClick={() => setSelectedCamada(null)}
          style={{
            borderRadius: "3px",
            border: selectedCamada === null ? "1px solid var(--inst-text)" : "1px solid var(--inst-line)",
            background: selectedCamada === null ? "var(--inst-panel-2)" : "var(--inst-panel)",
            padding: "10px 12px",
            textAlign: "left",
            cursor: "pointer",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--inst-text)" }}>Todas as Camadas</span>
          <span className="mono tabular" style={{ fontSize: "10px", color: "var(--inst-dim)", marginTop: "4px" }}>
            {notes.length} notas
          </span>
        </button>

        {[1, 2, 3, 4, 5].map((lvl) => {
          const info = CAMADA_INFO[lvl];
          const count = notes.filter((n) => n.camada === lvl).length;
          const isSelected = selectedCamada === lvl;
          return (
            <button
              key={lvl}
              type="button"
              onClick={() => setSelectedCamada(isSelected ? null : lvl)}
              style={{
                borderRadius: "3px",
                border: isSelected ? "1px solid var(--inst-text)" : "1px solid var(--inst-line)",
                background: isSelected ? "var(--inst-panel-2)" : "var(--inst-panel)",
                padding: "10px 12px",
                textAlign: "left",
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--inst-text)" }}>Camada {lvl}</span>
              <div
                className="mono tabular"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginTop: "4px",
                  fontSize: "10px",
                  color: "var(--inst-dim)",
                }}
              >
                <span>{info.name.split("—")[1]?.trim()}</span>
                <span>{count}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Busca */}
      <div style={{ position: "relative", maxWidth: "420px" }}>
        <Search
          style={{
            position: "absolute",
            left: "12px",
            top: "50%",
            transform: "translateY(-50%)",
            width: "14px",
            height: "14px",
            color: "var(--inst-dim)",
          }}
        />
        <input
          placeholder="Pesquisar conceito, tag ou regra..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ ...inputStyle, paddingLeft: "34px" }}
        />
      </div>

      {/* Grid de Notas */}
      {loading ? (
        <InstEmpty>Carregando conexões neurais do Supabase...</InstEmpty>
      ) : filteredNotes.length === 0 ? (
        <InstEmpty>
          {searchQuery
            ? "Nenhum resultado corresponde à sua pesquisa atual."
            : "Comece criando uma nova nota para alimentar a inteligência do seu trading."}
        </InstEmpty>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
          {filteredNotes.map((note) => {
            return (
              <InstCard key={note.id}>
                <div style={{ display: "flex", flexDirection: "column", height: "100%", justifyContent: "space-between", gap: "12px" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                      <InstBadge tom="neutro">
                        Camada {note.camada} · {note.categoria}
                      </InstBadge>
                      <button
                        type="button"
                        onClick={() => handleDelete(note.id)}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--inst-dim)",
                          cursor: "pointer",
                          padding: "2px",
                          display: "flex",
                          alignItems: "center",
                        }}
                        title="Excluir nota"
                      >
                        <Trash2 style={{ width: "13px", height: "13px" }} />
                      </button>
                    </div>
                    <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--inst-text)", marginTop: "8px" }}>
                      {note.title}
                    </div>
                    <div
                      style={{
                        fontSize: "12px",
                        color: "var(--inst-dim)",
                        lineHeight: 1.5,
                        marginTop: "6px",
                        whiteSpace: "pre-line",
                      }}
                    >
                      {note.content}
                    </div>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {note.tags && note.tags.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                        {note.tags.map((tag, idx) => (
                          <InstBadge key={idx} tom="neutro">
                            {tag}
                          </InstBadge>
                        ))}
                      </div>
                    )}

                    <div
                      className="mono tabular"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        paddingTop: "8px",
                        borderTop: "1px solid var(--inst-line-2)",
                        fontSize: "10px",
                        color: "var(--inst-dim)",
                      }}
                    >
                      <span>{new Date(note.created_at).toLocaleDateString("pt-BR")}</span>
                      <span style={{ color: "var(--inst-ok)" }}>{note.status}</span>
                    </div>
                  </div>
                </div>
              </InstCard>
            );
          })}
        </div>
      )}
    </InstPage>
  );
}
