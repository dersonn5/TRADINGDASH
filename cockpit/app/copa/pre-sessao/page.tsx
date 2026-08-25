import { Suspense } from "react";
import { PreSessaoForm } from "@/components/copa/pre-sessao-form";

export const metadata = {
  title: "Pré-Sessão Diária | Copa BTG",
  description: "Ambiente qualitativo, marcação de liquidez e parâmetros de risco do dia",
};

export default function PreSessaoPage() {
  return (
    <div className="container py-6">
      <Suspense fallback={<div className="text-muted-foreground text-center py-12">Carregando formulário...</div>}>
        <PreSessaoForm />
      </Suspense>
    </div>
  );
}
