import { supabase } from "./supabase";
import { Strategy } from "@/lib/types";
import { getDataSaoPaulo } from "./copa-db";

export interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
  weight: number;
  tipo: "KILL" | "PONTO";
  ajuda?: string;
  origem?: "MEDIDO" | "ESTIMADO";
  category?: "pre_market" | "bias" | "technical" | "risk" | "emotional";
}

export interface LiveChecklist {
  id?: string;
  strategy_id?: string;
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
// CHECKLIST AO VIVO NO PREGÃO
// -------------------------------------------------------------

export async function fetchTodayChecklist(strategy: Strategy): Promise<LiveChecklist> {
  // Dia em Sao Paulo: toISOString() daria o dia seguinte depois das 21h
  const today = getDataSaoPaulo();
  const defaultChecklist = getDefaultChecklist(today, strategy);
  try {
    const { data, error } = await supabase
      .from("trading_live_checklist")
      .select("*")
      .eq("session_date", today)
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error || !data) {
      return defaultChecklist;
    }

    const loaded = data as LiveChecklist;
    const defaultIds = new Set(defaultChecklist.items.map((i) => i.id));
    const loadedItems = loaded.items || [];
    const isOutdated =
      (loaded.strategy_id && loaded.strategy_id !== strategy.id) ||
      loadedItems.length !== defaultChecklist.items.length ||
      loadedItems.some((i) => !i.tipo || !defaultIds.has(i.id));

    if (isOutdated) {
      return {
        ...defaultChecklist,
        bias: loaded.bias || defaultChecklist.bias,
        notes: loaded.notes || defaultChecklist.notes,
      };
    }

    return loaded;
  } catch (err) {
    console.error("Erro ao buscar checklist:", err);
    return defaultChecklist;
  }
}

export async function saveChecklist(checklist: LiveChecklist): Promise<boolean> {
  try {
    const today = checklist.session_date || getDataSaoPaulo();
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
        strategy_id: checklist.strategy_id,
        updated_at: new Date().toISOString(),
      },
      // user_id vem do default auth.uid() da tabela; um checklist por usuario por dia
      { onConflict: "user_id,session_date" }
    );

    if (error) throw error;
    return true;
  } catch (err) {
    console.error("Erro ao salvar checklist:", err);
    return false;
  }
}

export function getDefaultChecklist(date: string, strategy: Strategy): LiveChecklist {
  const sortedChecklist = [
    ...strategy.checklist.filter((i) => i.tipo === "KILL"),
    ...strategy.checklist.filter((i) => i.tipo === "PONTO"),
  ];
  const items: ChecklistItem[] = sortedChecklist.map((item) => ({
    id: item.id,
    label: item.label,
    checked: false,
    weight: item.peso,
    tipo: item.tipo as "KILL" | "PONTO",
    ajuda: item.ajuda,
    origem: (item as any).origem || "ESTIMADO",
  }));

  return {
    strategy_id: strategy.id,
    session_date: date,
    session_name: "Sessão Pregão Ao Vivo",
    market: "B3 WIN",
    bias: "NEUTRO",
    items,
    score: 0,
    risk_approved: false,
    notes: "",
  };
}
