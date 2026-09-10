import { supabase } from "./supabase";

export interface TradingNote {
  id: string;
  title: string;
  content: string;
  camada: number; // 1 to 5
  categoria: string;
  status: "validado" | "em_teste" | "monitorando" | "rascunho";
  tags: string[];
  linked_notes: string[];
  created_at: string;
  updated_at?: string;
}

export interface TradingTrade {
  id: string;
  trade_date: string;
  symbol: string;
  direction: "BUY" | "SELL";
  strategy: string;
  session?: string;
  contracts?: number;
  entry_price: number;
  exit_price?: number;
  stop_loss: number;
  take_profit?: number;
  pnl?: number;
  result: "WIN" | "LOSS" | "BE" | "OPEN";
  rr_achieved?: number;
  confluence_score?: number;
  screenshot_url?: string;
  notes?: string;
  mistakes_learnings?: string;
  created_at?: string;
}

export interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
  category: "pre_market" | "bias" | "technical" | "risk" | "emotional";
  weight: number;
}

export interface LiveChecklist {
  id?: string;
  session_date: string;
  session_name: string;
  market: string;
  bias: "BULLISH" | "BEARISH" | "NEUTRO" | "NAO_OPERAR";
  items: ChecklistItem[];
  score: number;
  risk_approved: boolean;
  notes: string;
}

// -------------------------------------------------------------
// SEGUNDO CÉREBRO (NOTAS)
// -------------------------------------------------------------

export async function fetchNotes(): Promise<TradingNote[]> {
  try {
    const { data, error } = await supabase
      .from("trading_notes")
      .select("*")
      .order("camada", { ascending: true })
      .order("created_at", { ascending: false });

    if (error) {
      console.warn("Aviso ao buscar notas no Supabase:", error.message);
      return getSampleNotes();
    }
    return (data as TradingNote[]) || getSampleNotes();
  } catch (err) {
    console.error("Erro inesperado ao buscar notas:", err);
    return getSampleNotes();
  }
}

export async function saveNote(note: Partial<TradingNote>): Promise<TradingNote | null> {
  try {
    if (note.id) {
      const { data, error } = await supabase
        .from("trading_notes")
        .update({
          title: note.title,
          content: note.content,
          camada: note.camada,
          categoria: note.categoria,
          status: note.status,
          tags: note.tags,
          linked_notes: note.linked_notes,
          updated_at: new Date().toISOString(),
        })
        .eq("id", note.id)
        .select()
        .single();

      if (error) throw error;
      return data;
    } else {
      const { data, error } = await supabase
        .from("trading_notes")
        .insert([
          {
            title: note.title,
            content: note.content,
            camada: note.camada || 1,
            categoria: note.categoria || "ICT",
            status: note.status || "validado",
            tags: note.tags || [],
            linked_notes: note.linked_notes || [],
          },
        ])
        .select()
        .single();

      if (error) throw error;
      return data;
    }
  } catch (err) {
    console.error("Erro ao salvar nota:", err);
    return null;
  }
}

export async function deleteNote(id: string): Promise<boolean> {
  try {
    const { error } = await supabase.from("trading_notes").delete().eq("id", id);
    if (error) throw error;
    return true;
  } catch (err) {
    console.error("Erro ao excluir nota:", err);
    return false;
  }
}

// -------------------------------------------------------------
// BANCO DE TRADES
// -------------------------------------------------------------

export async function fetchTrades(): Promise<TradingTrade[]> {
  try {
    const { data, error } = await supabase
      .from("trading_trades")
      .select("*")
      .order("trade_date", { ascending: false });

    if (error) {
      console.warn("Aviso ao buscar trades no Supabase:", error.message);
      return getSampleTrades();
    }
    return (data as TradingTrade[]) || getSampleTrades();
  } catch (err) {
    console.error("Erro inesperado ao buscar trades:", err);
    return getSampleTrades();
  }
}

export async function saveTrade(trade: Partial<TradingTrade>): Promise<TradingTrade | null> {
  try {
    if (trade.id) {
      const { data, error } = await supabase
        .from("trading_trades")
        .update(trade)
        .eq("id", trade.id)
        .select()
        .single();

      if (error) throw error;
      return data;
    } else {
      const { data, error } = await supabase
        .from("trading_trades")
        .insert([trade])
        .select()
        .single();

      if (error) throw error;
      return data;
    }
  } catch (err) {
    console.error("Erro ao salvar trade:", err);
    return null;
  }
}

// -------------------------------------------------------------
// CHECKLIST AO VIVO NO PREGÃO
// -------------------------------------------------------------

export async function fetchTodayChecklist(): Promise<LiveChecklist> {
  const today = new Date().toISOString().split("T")[0];
  try {
    const { data, error } = await supabase
      .from("trading_live_checklist")
      .select("*")
      .eq("session_date", today)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error || !data) {
      return getDefaultChecklist(today);
    }
    return data as LiveChecklist;
  } catch (err) {
    console.error("Erro ao buscar checklist:", err);
    return getDefaultChecklist(today);
  }
}

export async function saveChecklist(checklist: LiveChecklist): Promise<boolean> {
  try {
    const today = checklist.session_date || new Date().toISOString().split("T")[0];
    const { error } = await supabase.from("trading_live_checklist").upsert(
      {
        session_date: today,
        session_name: checklist.session_name,
        market: checklist.market,
        bias: checklist.bias,
        items: checklist.items,
        score: checklist.score,
        risk_approved: checklist.risk_approved,
        notes: checklist.notes,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "session_date" }
    );

    if (error) throw error;
    return true;
  } catch (err) {
    console.error("Erro ao salvar checklist:", err);
    return false;
  }
}

// -------------------------------------------------------------
// DADOS DE AMOSTRA / INICIAIS
// -------------------------------------------------------------

function getSampleNotes(): TradingNote[] {
  return [
    {
      id: "sample-1",
      title: "Fair Value Gap (FVG) & Consequência",
      content: "Desequilíbrio de 3 velas onde a máxima da vela 1 não toca a mínima da vela 3. Atua como ímã de liquidez e ponto institucional de rebalanceamento de preço.",
      camada: 1,
      categoria: "ICT",
      status: "validado",
      tags: ["FVG", "Liquidez", "Imbalance"],
      linked_notes: ["Order Block", "Market Structure Shift"],
      created_at: new Date().toISOString(),
    },
    {
      id: "sample-2",
      title: "Regra de Ouro da Killzone NY AM",
      content: "Abertura das 09:30 às 11:00 NY (10:30 às 12:00 BRT). Não entrar antes do sweep da liquidez do Asian Range ou das 09:30 candle de abertura.",
      camada: 2,
      categoria: "ICT",
      status: "validado",
      tags: ["Killzone", "Horários", "Filtro"],
      linked_notes: ["Silver Bullet", "Judas Swing"],
      created_at: new Date().toISOString(),
    },
    {
      id: "sample-3",
      title: "Modelo Silver Bullet Intraday",
      content: "1. Sweep de BSL/SSL prévio.\n2. Deslocamento violento gerando FVG.\n3. MSS confirmado com fechamento de vela.\n4. Entrada no reteste do FVG com Stop além da máxima/mínima do swing.\n5. Alvo no próximo pool de liquidez (R:R mínimo 1:2).",
      camada: 3,
      categoria: "B05 Trade System",
      status: "validado",
      tags: ["Silver Bullet", "Modelo", "Setup"],
      linked_notes: ["FVG", "MSS", "Gestão de Risco"],
      created_at: new Date().toISOString(),
    },
    {
      id: "sample-4",
      title: "Protocolo de Circuit Breaker Diário",
      content: "Máximo de 3 operações no dia ou perda acumulada de 2R. Ao atingir o limite, a tela é bloqueada e o robô/operador entra em pausa até a sessão seguinte.",
      camada: 4,
      categoria: "B05 Trade System",
      status: "validado",
      tags: ["Gestao de Risco", "Stop Diario", "Disciplina"],
      linked_notes: ["Circuit Breaker", "Psicologia"],
      created_at: new Date().toISOString(),
    },
    {
      id: "sample-5",
      title: "Sabedoria: Nunca operar antes do CPI/FOMC",
      content: "Dias de divulgação de inflação americana (CPI) e taxas de juros (FOMC) produzem expansões erráticas e sweeps duplos. Ficar líquido 30 minutos antes e 15 minutos após o anúncio.",
      camada: 5,
      categoria: "DIARIO",
      status: "validado",
      tags: ["Noticias", "Licoes Aprendidas", "Protecao"],
      linked_notes: ["Calendario Economico", "Volatilidade"],
      created_at: new Date().toISOString(),
    },
  ];
}

function getSampleTrades(): TradingTrade[] {
  return [
    {
      id: "trade-1",
      trade_date: new Date(Date.now() - 3600000 * 24).toISOString(),
      symbol: "WIN",
      direction: "BUY",
      strategy: "Silver Bullet",
      session: "B3 Abertura",
      contracts: 2,
      entry_price: 131250,
      exit_price: 131750,
      stop_loss: 131050,
      take_profit: 131750,
      pnl: 200,
      result: "WIN",
      rr_achieved: 2.5,
      confluence_score: 85,
      notes: "Sweep perfeito da mínima das 09:15 com displacement claro.",
      mistakes_learnings: "Execução impecável dentro da regra.",
    },
    {
      id: "trade-2",
      trade_date: new Date(Date.now() - 3600000 * 48).toISOString(),
      symbol: "WDO",
      direction: "SELL",
      strategy: "Breaker Block",
      session: "NY AM",
      contracts: 1,
      entry_price: 5.620,
      exit_price: 5.605,
      stop_loss: 5.628,
      take_profit: 5.600,
      pnl: 150,
      result: "WIN",
      rr_achieved: 1.87,
      confluence_score: 80,
      notes: "Breaker testado com rejeição em vela de 5 minutos.",
    },
  ];
}

function getDefaultChecklist(date: string): LiveChecklist {
  return {
    session_date: date,
    session_name: "Sessão Pregão Ao Vivo",
    market: "B3 WIN",
    bias: "NEUTRO",
    items: [
      { id: "c1", label: "Calendário Econômico verificado (sem notícias de 3 touros nos próx. 30min)", checked: false, category: "pre_market", weight: 15 },
      { id: "c2", label: "Viés Diário Top-Down definido (HTF Bias alinhado)", checked: false, category: "bias", weight: 15 },
      { id: "c3", label: "Varredura de Liquidez confirmada (BSL ou SSL swept)", checked: false, category: "technical", weight: 20 },
      { id: "c4", label: "Displacement nítido com quebra de estrutura (MSS)", checked: false, category: "technical", weight: 20 },
      { id: "c5", label: "Fair Value Gap (FVG) respeitado para ponto de entrada", checked: false, category: "technical", weight: 15 },
      { id: "c6", label: "Risco calculado: R:R mínimo de 1:2 e perda máx. de 1% da conta", checked: false, category: "risk", weight: 10 },
      { id: "c7", label: "Estado Emocional: Calmo, descansado e sem sentimento de vingança", checked: false, category: "emotional", weight: 5 },
    ],
    score: 0,
    risk_approved: false,
    notes: "",
  };
}
