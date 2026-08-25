---
tags: [pos-trade, sinapse, template, diario, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🧬 Gravação Sináptica (Template do Diário)

> **Camada 4 — Padronização de Registro**
> A gravação de cada trade deve seguir este padrão rigoroso.
> Isso permite que a IA faça consultas cruzadas entre resultados e anotações.

---

## Template Obrigatório de Trade Log

Sempre que a IA ou o Trader registrar uma operação no diário mensal (ex: [[../../03_Diario_Trades/Diario_2026_06|Diario_2026_06.md]]), usar este template exato:

```markdown
### 🚀 Trade #[Número_Corrente] — YYYY-MM-DD [HH:MM]

- **Estratégia**: [[../../B05 Trade System/Estrategias Validadas/Silver_Bullet_BTC_USDT|Silver Bullet BTC]] / [[../../B05 Trade System/Estrategias Validadas/Silver_Bullet_ETH_USDT|Silver Bullet ETH]] / [[../../B05 Trade System/Estrategias Validadas/Prop_Firm_2024_BTC|Prop Firm 2024]]
- **Direção**: `LONG` / `SHORT`
- **Sessão/Killzone**: [[../../01_Regras_ICT/ICT_Killzones_YouTube_Distilled|NY AM SB]] / `NY PM SB` / `London Open`
- **Preços**: Entrada: $`[Preço]` | Stop: $`[Preço]` | Alvo: $`[Preço]`
- **Risco Aplicado**: `1.0%` (ou `0.5%`) | **Sizing**: `[Lote] BTC/ETH`
- **Resultado**: `WIN` / `LOSS` / `BE` | **P&L**: `+X.XX%` / `-X.XX%` | `+X.XR` / `-X.XR`

#### 📊 Evidência Gráfica
![Setup Screenshot](caminho_ou_link_da_imagem)

#### 📝 Checklist de Processo
- [ ] Daily Bias estava claro em H4?
- [ ] Varredura de liquidez identificada?
- [ ] MSS com deslocamento em M5?
- [ ] Entrada executada via Limit Order no CE da FVG?
- [ ] Nenhuma notícia pendente na janela?

#### 🧠 Análise Cognitiva (Sabedoria)
- **O que funcionou**: [Análise da execução e reação do preço]
- **Desvios ou Erros**: [[../../B05 Trade System/Pos-Trade/Licoes_e_Ajustes|Verificar se houve erro ou lição]]
- **Estado Mental durante a condução**: [[../../B05 Trade System/Mentalidade Pre-Trade/Estado_Mental_Ideal|Verificar classificação do estado]]
```

---

## 🔗 Conexões Neurais
- [[MOC_PosTrade|📊 MOC Pós-Trade]]
- [[Protocolo_de_Review|🔍 Protocolo de Review]]
- [[../../03_Diario_Trades/Diario_2026_06|📅 Diário de Trades]]
- [[../../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]