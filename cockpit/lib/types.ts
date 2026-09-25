export type Mercado = "WIN" | "WDO";
export type ItemTipo = "KILL" | "PONTO";
export type Ambiente = "FAVORAVEL" | "NEUTRA" | "DESFAVORAVEL";

export interface HorarioJanela {
  inicio: string;
  fim: string;
}

export interface ChecklistItem {
  id: string;
  tipo: ItemTipo;
  peso: number;
  label: string;
  ajuda: string;
}

export interface RegraAmbiente {
  campo: string;
  op: string;
  valor: any;
  efeito: Ambiente;
  motivo: string;
}

export interface Strategy {
  id: string;
  ordem?: number;
  nome: string;
  mercado: Mercado[];
  descricao: string;
  score_minimo: number;
  ambiente_favoravel: string[];
  ambiente_desfavoravel: string[];
  horarios_validos: HorarioJanela[];
  regras_ambiente: RegraAmbiente[];
  checklist: ChecklistItem[];
  calibracao?: {
    status?: string;
    observacao?: string;
    atualizado_em?: string;
    [key: string]: any;
  };
  [key: string]: any;
}
