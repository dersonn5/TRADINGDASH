import { Activity, BarChart3, FileText, History, ShieldCheck } from "lucide-react";

export interface NavItem {
  title: string;
  url: string;
  icon?: React.ElementType;
  badge?: string;
  items?: NavItem[];
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const sidebarData: { navGroups: NavGroup[] } = {
  navGroups: [
    {
      title: "Pregão",
      items: [
        { title: "Visão Geral", url: "/", icon: BarChart3 },
        { title: "Pré-Sessão", url: "/pre-sessao", icon: FileText },
        { title: "Checklist", url: "/checklist", icon: ShieldCheck },
      ],
    },
    {
      title: "Registro",
      items: [
        { title: "Histórico", url: "/trades", icon: History },
        { title: "Estratégias", url: "/estrategias", icon: Activity },
      ],
    },
  ],
};
