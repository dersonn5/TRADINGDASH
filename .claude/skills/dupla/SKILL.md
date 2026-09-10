---
name: dupla
description: Versão local da dupla para o projeto TRADING AI. Contém a lista de arquivos proibidos deste repositório e a regra de conformidade da Copa BTG. Use junto com a skill global `dupla` — esta manda no que for específico daqui.
---

# Dupla — TRADING AI

A skill global descreve o processo. Este arquivo cobre só o que não se deriva de
fora: o que o Gemini **não** pode tocar neste repositório, e por quê.

## REGRA DE CONFORMIDADE — acima de todas as outras

O regulamento da Copa BTG Trader prevê desclassificação por "automações não
autorizadas, robôs, scripts, **ferramentas externas** ou qualquer mecanismo não
previsto ou não autorizado pela Promotora". O prêmio é R$ 1 milhão.

O app da Copa só é legítimo enquanto for **diário de bordo**. Em qualquer task,
sob qualquer justificativa, é proibido:

- integrar com Profit Pro / Ultra / Scalper Pro / Nelogica / BTG — inclusive ler
  tela, arquivo, DLL, log ou área de transferência dessas plataformas
- buscar cotação, candle ou qualquer dado de mercado, de qualquer fonte
- detectar setup, sugerir entrada ou gerar sinal
- enviar ordem, ou simular envio

Ver `COPA_BTG_PRD.md` §13. Se uma task parecer pedir isso, a spec foi lida errado
— pare e registre em "Bloqueios".

## NÃO MEXER — com o motivo

| Caminho | Por quê |
|---|---|
| `copa/risk.py` | É o gate. Autoridade de servidor sobre o que pode ser operado. Regra errada aqui = operar fora das próprias regras, com o sistema dizendo que está tudo bem. |
| `core/entry_quality.py` | Define a régua A+/A/B/C/D. `grade_for` é **importado**, nunca reimplementado. Reescrever muda toda nota histórica em silêncio e invalida comparação com trades passados. |
| `strategies/**` | Os detectores, com histórico de backtest. `playbook_anderson.py` carrega uma divergência **documentada e proposital** (stop ancorado no FVG, enquanto o operador ancora no topo do swing). "Corrigir" isso apaga a evidência de que são dois modelos diferentes. |
| `live_daemon_*.py` | Executam ordem de verdade. |
| `cockpit/supabase/schema.sql` | Migration. Irreversível em produção. |
| `.env`, `config.py` | Credenciais. |
| `COPA_BTG_PRD.md`, `COPA_BTG_BUILD_SPEC.md`, `COPA_BTG_PLAN_V2.md` | Documentos de decisão. Só o Claude edita, e só quando o Anderson aprova. |

Precisa mexer num desses? **O Claude implementa essa parte.** Delegue o resto.

## Armadilhas já pagas neste projeto

**Rótulo decorativo sobre geometria inventada.** `research/plot_ict_canonical.py`
rotula `window["high"].max()` como "RTH ORG High — swept". É a maior vela do
recorte, que por definição nunca foi varrida. O gráfico afirmava um sweep
matematicamente impossível.

Regra que nasceu daí: **toda marcação carrega o índice da vela que a originou.**
Sem âncora, não desenha. Gráfico vazio é honesto; gráfico decorado é fraude.

**Peso apresentado como medido sem ter sido medido.** `cockpit/data/strategies.ts`
declarou `calibracao.status: "EM_VALIDACAO"` com "calibrados para índice e dólar
B3". Nada foi calibrado. Todo peso carrega `origem: MEDIDO | ESTIMADO`, e a
interface mostra a diferença. Nunca promova `ESTIMADO` para `MEDIDO` sem N e
período.

**Checklist duplicado divergindo em silêncio.** Chegou a haver três listas
diferentes (JSON do Python, TS do app, defaults do `trading-db.ts`). O operador
abriria o pregão com o checklist errado. Uma fonte de verdade por superfície, e
a divergência tem que quebrar o build, não passar batido.

## Verify obrigatório

```bash
cd cockpit && npx tsc --noEmit
git diff --stat
git diff -U0 | grep "^-.*//"   # comentário apagado é desvio
```

`tsc` limpo não prova tela. Abrir e olhar faz parte do aceite.
