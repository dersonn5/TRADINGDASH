"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { usePathname } from "next/navigation";
import { Search, Moon, Sun, User, LogOut, Bot } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const TITLES: Record<string, string> = {
  "/": "Visão Geral",
  "/trades": "Trades",
  "/estrategias": "Estratégias",
  "/backtests": "Backtests",
  "/cerebro": "Cérebro ICT",
  "/pesquisa": "Pesquisa",
  "/config": "Configurações",
};

export function DashboardHeader() {
  const pathname = usePathname();
  const title = TITLES[pathname] ?? "Dashboard";
  const [dark, setDark] = useState(true);

  function toggleTheme() {
    setDark((d) => {
      document.documentElement.classList.toggle("dark", !d);
      return !d;
    });
  }

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b bg-background px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="h-4" />
      <h2 className="text-sm font-semibold">{title}</h2>

      <div className="relative flex-1 max-w-sm ml-4">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
        <Input
          placeholder="Buscar trade, ativo..."
          className="pl-8 h-8 text-sm bg-muted/50 border-0 focus-visible:ring-1"
        />
      </div>

      <div className="ml-auto flex items-center gap-1">
        <div className="hidden sm:flex items-center gap-1.5 mr-2 text-xs text-muted-foreground">
          <span className="relative flex size-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-amber-500 opacity-75 animate-ping" />
            <span className="relative inline-flex size-2 rounded-full bg-amber-500" />
          </span>
          bot idle
        </div>
        <Button variant="ghost" size="icon" className="size-8" onClick={toggleTheme}>
          {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>
        <Separator orientation="vertical" className="h-4 mx-1" />
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center justify-center rounded-full cursor-pointer border-0 p-0 bg-transparent focus:outline-none">
            <Avatar className="size-7 select-none">
              <AvatarFallback className="text-xs bg-primary text-primary-foreground">IC</AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuGroup>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">Trader</p>
                  <p className="text-xs leading-none text-muted-foreground">ICT Cognitive Cockpit</p>
                </div>
              </DropdownMenuLabel>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem><User className="mr-2 size-4" /><span>Perfil</span></DropdownMenuItem>
            <DropdownMenuItem><Bot className="mr-2 size-4" /><span>Status do robô</span></DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive focus:bg-destructive/10 focus:text-destructive cursor-pointer">
              <LogOut className="mr-2 size-4" /><span>Sair</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
