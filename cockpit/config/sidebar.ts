import {
  LayoutDashboard,
  CandlestickChart,
  FlaskConical,
  Brain,
  Activity,
  BookOpen,
  Settings,
  Trophy,
  FileText,
  PlusCircle,
  BarChart3,
  Calendar,
  SlidersHorizontal,
  History,
  ShieldCheck,
} from "lucide-react";

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
      title: "Copa BTG",
      items: [
        { title: "Painel Copa", url: "/copa", icon: Trophy },
        { title: "Pré-Sessão", url: "/copa/pre-sessao", icon: FileText },
        { title: "Novo Trade", url: "/copa/novo", icon: PlusCircle },
        { title: "Trades", url: "/copa/trades", icon: History },
        { title: "Fase", url: "/copa/fase", icon: Calendar },
        { title: "Estatística", url: "/copa/stats", icon: BarChart3 },
        { title: "Estratégias", url: "/copa/estrategias", icon: Activity },
        { title: "Config", url: "/copa/config", icon: SlidersHorizontal },
      ],
    },
    {
      title: "Dashboard",
      items: [{ title: "Visão Geral", url: "/", icon: LayoutDashboard }],
    },
    {
      title: "Trading",
      items: [
        { title: "Banco de Trades", url: "/trades", icon: CandlestickChart },
        { title: "Checklist Pregão", url: "/checklist", icon: ShieldCheck },
        { title: "Estratégias", url: "/estrategias", icon: Activity },
        { title: "Backtests", url: "/backtests", icon: FlaskConical },
      ],
    },
    {
      title: "Inteligência",
      items: [
        { title: "Segundo Cérebro", url: "/cerebro", icon: Brain },
        { title: "Pesquisa", url: "/pesquisa", icon: BookOpen },
      ],
    },
    {
      title: "Sistema",
      items: [{ title: "Configurações", url: "/config", icon: Settings }],
    },
  ],
};
