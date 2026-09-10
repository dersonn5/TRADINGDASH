"use client";

import { useEffect, useState } from "react";
import { fetchNotes, saveNote, deleteNote, TradingNote } from "@/lib/trading-db";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Brain, Plus, Search, Layers, Tag, Trash2, BookOpen, ShieldAlert, Sparkles, CheckCircle2 } from "lucide-react";

const CAMADA_INFO: Record<number, { name: string; desc: string; color: string; bg: string; border: string }> = {
  1: {
    name: "Camada 1 — Conceitos Atômicos",
    desc: "Definições puras de mercado: FVG, Order Blocks, Liquidez BSL/SSL",
    color: "text-blue-400",
    bg: "bg-blue-950/20",
    border: "border-blue-800/40",
  },
  2: {
    name: "Camada 2 — Regras & Filtros",
    desc: "Condições de combinação, horários de Killzones, filtros macro",
    color: "text-cyan-400",
    bg: "bg-cyan-950/20",
    border: "border-cyan-800/40",
  },
  3: {
    name: "Camada 3 — Modelos & Setups",
    desc: "Estratégias validadas: Silver Bullet, Judas Swing, Breaker Block",
    color: "text-purple-400",
    bg: "bg-purple-950/20",
    border: "border-purple-800/40",
  },
  4: {
    name: "Camada 4 — Sistema & Execução",
    desc: "Mapeamento operacional, condução de trade e circuit breakers",
    color: "text-amber-400",
    bg: "bg-amber-950/20",
    border: "border-amber-800/40",
  },
  5: {
    name: "Camada 5 — Sabedoria & Diário",
    desc: "Casos reais de mercado, lições aprendidas e erros evitados",
    color: "text-emerald-400",
    bg: "bg-emerald-950/20",
    border: "border-emerald-800/40",
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Brain className="size-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Segundo Cérebro · Base Cognitiva</h1>
            <Badge variant="outline" className="text-cyan-400 border-cyan-800/40 bg-cyan-950/20">
              Supabase Live
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Conhecimento arquitetado em 5 camadas neurais (Conceitos, Regras, Modelos, Sistema e Sabedoria).
          </p>
        </div>

        {/* Botão e Modal de Nova Nota */}
        <Button
          onClick={() => setIsDialogOpen(true)}
          className="gap-2 bg-gradient-to-r from-primary to-cyan-600 hover:from-primary/90 hover:to-cyan-600/90 text-primary-foreground shadow-lg shadow-primary/20"
        >
          <Plus className="size-4" />
          Nova Nota Neural
        </Button>

        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="size-5 text-primary" />
              Registrar no Segundo Cérebro
            </DialogTitle>
          </DialogHeader>

            <div className="space-y-4 py-2">
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Título do Conceito / Regra</label>
                <Input
                  placeholder="Ex: Fair Value Gap Institucional"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Camada Cognitiva</label>
                  <select
                    className="w-full h-9 mt-1 rounded-md border border-input bg-card text-foreground px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring [&_option]:bg-[#18181b] [&_option]:text-[#f4f4f5]"
                    style={{ colorScheme: "dark" }}
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

                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Categoria</label>
                  <Input
                    placeholder="ICT, B05 Trade System, DIARIO"
                    value={newCategoria}
                    onChange={(e) => setNewCategoria(e.target.value)}
                    className="mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Tags (separadas por vírgula)</label>
                <Input
                  placeholder="Ex: FVG, Liquidez, Sweep, Killzone"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Conteúdo da Nota (Markdown)</label>
                <Textarea
                  placeholder="Descreva a regra, lógica operacional, gatilho ou lição aprendida..."
                  rows={6}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  className="mt-1 font-mono text-sm leading-relaxed"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button onClick={handleCreateNote} disabled={saving || !newTitle.trim() || !newContent.trim()}>
                  {saving ? "Salvando no Supabase..." : "Salvar Conhecimento"}
                </Button>
              </div>
            </div>
        </Dialog>
      </div>

      {/* Camadas Filter Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <button
          onClick={() => setSelectedCamada(null)}
          className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all text-left flex flex-col justify-between ${
            selectedCamada === null
              ? "bg-primary/20 border-primary text-primary-foreground shadow-sm"
              : "bg-card/60 border-border/40 text-muted-foreground hover:bg-card hover:text-foreground"
          }`}
        >
          <span>Todas as Camadas</span>
          <span className="text-[10px] opacity-70 font-mono mt-1">{notes.length} notas</span>
        </button>

        {[1, 2, 3, 4, 5].map((lvl) => {
          const info = CAMADA_INFO[lvl];
          const count = notes.filter((n) => n.camada === lvl).length;
          const isSelected = selectedCamada === lvl;
          return (
            <button
              key={lvl}
              onClick={() => setSelectedCamada(isSelected ? null : lvl)}
              className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all text-left flex flex-col justify-between ${
                isSelected
                  ? `${info.bg} ${info.border} ${info.color} ring-1 ring-primary/40 shadow-sm`
                  : "bg-card/60 border-border/40 text-muted-foreground hover:bg-card hover:text-foreground"
              }`}
            >
              <span className="truncate">Camada {lvl}</span>
              <div className="flex items-center justify-between mt-1 text-[10px] opacity-70 font-mono">
                <span className="truncate">{info.name.split("—")[1]?.trim()}</span>
                <span>{count}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Busca */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder="Pesquisar conceito, tag ou regra..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 bg-card/60 border-border/50"
        />
      </div>

      {/* Grid de Notas */}
      {loading ? (
        <div className="py-20 text-center text-muted-foreground flex flex-col items-center gap-3">
          <Brain className="size-8 animate-pulse text-primary" />
          <span>Carregando conexões neurais do Supabase...</span>
        </div>
      ) : filteredNotes.length === 0 ? (
        <div className="p-12 text-center border border-dashed rounded-2xl bg-card/20 space-y-3">
          <BookOpen className="size-10 text-muted-foreground mx-auto" />
          <h3 className="font-semibold text-foreground">Nenhuma nota encontrada</h3>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            {searchQuery
              ? "Nenhum resultado corresponde à sua pesquisa atual."
              : "Comece criando uma nova nota para alimentar a inteligência do seu trading."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredNotes.map((note) => {
            const camadaMeta = CAMADA_INFO[note.camada] || CAMADA_INFO[1];
            return (
              <Card
                key={note.id}
                className="group relative flex flex-col justify-between border-border/60 bg-card/70 hover:bg-card hover:border-primary/40 transition-all duration-200 shadow-sm hover:shadow-md"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md border ${camadaMeta.bg} ${camadaMeta.border} ${camadaMeta.color}`}
                    >
                      Camada {note.camada} · {note.categoria}
                    </span>
                    <button
                      onClick={() => handleDelete(note.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-red-400 p-1"
                      title="Excluir nota"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                  <CardTitle className="text-base font-semibold mt-2 group-hover:text-primary transition-colors">
                    {note.title}
                  </CardTitle>
                </CardHeader>

                <CardContent className="space-y-4">
                  <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-line line-clamp-4">
                    {note.content}
                  </p>

                  {note.tags && note.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {note.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-muted/60 text-muted-foreground border border-border/40"
                        >
                          <Tag className="size-2.5 opacity-60" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[10px] text-muted-foreground/70 font-mono">
                    <span>{new Date(note.created_at).toLocaleDateString("pt-BR")}</span>
                    <span className="flex items-center gap-1 text-emerald-400">
                      <CheckCircle2 className="size-3" />
                      {note.status}
                    </span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
