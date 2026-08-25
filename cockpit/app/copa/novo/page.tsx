import { Suspense } from "react";
import { TradeForm } from "@/components/copa/trade-form";

export const metadata = {
  title: "Novo Trade & Checklist | Copa BTG",
  description: "Checklist interativo com gate físico de liberação para WIN e WDO",
};

export default function NovoTradePage() {
  return (
    <div className="container py-6">
      <Suspense fallback={<div className="text-muted-foreground text-center py-12">Carregando checklist...</div>}>
        <TradeForm />
      </Suspense>
    </div>
  );
}
