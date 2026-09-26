# Spec: Diferenciação Visual e Cores da Curva de Capital e Estratégias

## 1. Objetivo
Na tela Visão Geral, a Curva de Capital exibe 4 séries (Total, Varrida das 10, Continuidade, Reversão HTF).
Atualmente, todas as três estratégias utilizam variantes do mesmo tom de ciano (`var(--k1)`, `var(--k2)`, `var(--k3)`), e a legenda exibe apenas retângulos sólidos idênticos, tornando impossível distinguir visualmente qual linha corresponde a qual estratégia na curva.
O objetivo é dar identidade cromática única, harmônica e de alto contraste a cada estratégia (Ciano para Varrida das 10, Âmbar/Dourado para Continuidade, Violeta/Roxo para Reversão HTF), manter o Total em branco puro e de maior espessura, alinhar a legenda aos traços reais (sólido, tracejado e pontilhado), adicionar efeito de destaque/spotlight interativo ao passar o mouse e sincronizar essas cores com o card "Por estratégia" adjacente.

## 2. Arquivos (só estes)
- `cockpit/app/globals.css` (tokens `--strat-a`, `--strat-b`, `--strat-c` nos temas dark e light)
- `cockpit/components/v2/visao-geral-conteudo.tsx` (legenda com traços SVG reais, cores distintas por estratégia, efeito spotlight interativo e sincronia com as barras de "Por estratégia")
- `design/v2/Main.dc.html` (espelho no mockup do design canvas com as novas cores e legenda)

## 3. NÃO MEXER — com o motivo de cada item
- `cockpit/lib/visao-geral.ts`: Contratos de cálculo matemático e retorno de dados puros (`vg.curva`, `vg.estr`, `vg.kpis`) validados pelos testes unitários de `verify.ts`.
- `cockpit/scripts/verify.ts`: Suíte de testes automatizados de gating, limites, métricas e integridade do trade system.
- `cockpit/lib/metricas.ts` e `cockpit/lib/copa-db.ts`: Regras de negócio, cálculos de PnL e persistência no Supabase.
- Demais páginas (`/checklist`, `/trades`, `/pre-sessao`): Escopo restrito à curva de capital e identificação visual das estratégias na Visão Geral.

## 4. Contratos

### Tokens CSS (`globals.css`)
```css
/* Escuro (padrão) */
--strat-c: #22D3EE; /* Setup C: Varrida das 10 (Ciano elétrico) */
--strat-b: #F59E0B; /* Setup B: Continuidade (Âmbar / Dourado) */
--strat-a: #C084FC; /* Setup A: Reversão HTF (Violeta luminoso) */

/* Claro */
--strat-c: #0891B2; /* Setup C: Varrida das 10 (Ciano escuro) */
--strat-b: #D97706; /* Setup B: Continuidade (Âmbar escuro) */
--strat-a: #9333EA; /* Setup A: Reversão HTF (Violeta) */
```

### Curva de Capital (Renderização de Traços)
- **Total**: `stroke: var(--tx)` (Branco), `strokeWidth: 2.5`, linha contínua com ponto final `strokeWidth: 2.4` e raio `5`.
- **Varrida das 10 (C)**: `stroke: var(--strat-c)` (Ciano), `strokeWidth: 2.0`, contínua.
- **Continuidade (B)**: `stroke: var(--strat-b)` (Âmbar), `strokeWidth: 1.8`, tracejada (`strokeDasharray: "6 3"`).
- **Reversão HTF (A)**: `stroke: var(--strat-a)` (Violeta), `strokeWidth: 2.0`, pontilhada (`strokeDasharray: "2 4"`, `strokeLinecap: "round"`).

### Legenda Fiel aos Traços
A legenda exibe ícones SVG em miniatura (largura 20px, altura 10px) reproduzindo exatamente o traçado da linha no gráfico:
- Total: linha branca sólida com mini-círculo central
- Varrida das 10: linha ciano sólida
- Continuidade: linha âmbar tracejada
- Reversão HTF: linha violeta pontilhada
Ao passar o mouse sobre um item da legenda, a série correspondente entra em spotlight (opacidade 1.0, espessura aumentada) enquanto as outras estratégias são atenuadas para opacidade 0.25.

### Card "Por Estratégia"
As barras de volume e badges das estratégias utilizam as cores correspondentes (`var(--strat-c)`, `var(--strat-b)`, `var(--strat-a)`), consolidando a identidade visual entre os dois blocos.

## 5. Critério de aceite — mecânico, não interpretável
1. `node node_modules/typescript/lib/tsc.js --noEmit` → exit 0, nenhum erro de tipos.
2. `npx -y tsx scripts/verify.ts` → exit 0, todos os testes unitários passando.
3. As três estratégias possuem cores distintas (Ciano, Âmbar, Violeta), sem repetição de tonalidades ciano para as três.
4. A legenda exibe traçados correspondentes à linha no gráfico (contínuo, tracejado, pontilhado), não apenas blocos retangulares idênticos.
5. `git diff --stat` → apenas os arquivos autorizados (`cockpit/app/globals.css`, `cockpit/components/v2/visao-geral-conteudo.tsx`, `design/v2/Main.dc.html`, `cockpit/SPEC_CURVA_CAPITAL_CORES.md`).

## 6. Armadilhas já pagas nesta área
- Não usar vermelho ou verde para as estratégias: vermelho é reservado para perda/drawdown (`--negtx`, `--neg`) e verde é reservado para ganho/positivo (`--actx`, `--ac`).
- Preservar `vg.curva.vb`, `vg.curva.ticks`, `vg.curva.d`, `vg.curva.A`, `vg.curva.B`, `vg.curva.C` gerados por `lib/visao-geral.ts` sem alterar o contrato de saída.
- No SVG, `strokeLinecap="round"` com `strokeDasharray="0.1 4"` ou `"2 4"` gera pontos perfeitamente circulares, evitando traços feios ou borrados.
