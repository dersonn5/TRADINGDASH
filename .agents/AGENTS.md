# REGRAS E DIRETRIZES DE COMPORTAMENTO DO AGENTE (Trading AI & Cérebro Obsidian)

> Este arquivo define as diretrizes persistentes para o Agente de IA.
> Sempre que iniciar uma nova sessão ou retomar uma tarefa neste repositório, o agente deve seguir estritamente as regras aqui descritas.

---

## 1. Estrutura e Organização do Segundo Cérebro (Obsidian)

O vault do Obsidian está estruturado em **Camadas Cognitivas Hierárquicas** que replicam a forma como o cérebro humano processa informações. Todo conhecimento armazenado deve respeitar esta hierarquia:

```
CAMADA 5 — SABEDORIA       Experiência, erros a evitar, logs do diário
     ↑
CAMADA 4 — SISTEMA         Mapeamento do fluxo de operações (B05 Trade System/)
     ↑
CAMADA 3 — MODELO          Estratégias validadas (Silver Bullet, Prop Firm)
     ↑
CAMADA 2 — REGRAS          Condições de combinação de conceitos técnicos
     ↑
CAMADA 1 — CONCEITOS       Conceitos atômicos (FVG, Order Blocks, Liquidez)
```

### Regras de Escrita de Notas:
- **Camada 1 (B03 Regras ICT/)**: Notas focadas em definições puras de termos.
- **Camada 3 e 4 (B05 Trade System/)**: Notas contendo os fluxos do sistema operacional e de estratégias validadas (estritamente organizadas sob as subpastas `Estrategias Validadas/`, `Gerenciamento Validado/`, `Conducao de Trade/`, `Mentalidade Pre-Trade/`, `Durante o Trade/`, e `Pos-Trade/`).
- **Camada 5 (C02 Licoes Aprendidas/ & A04 Diario de Trades/)**: Casos episódicos de trade e erros práticos a evitar.

### Regra do Frontmatter Obrigatório:
Toda nota criada ou reestruturada pelo Agente de IA deve incluir o seguinte bloco YAML:
```yaml
---
tags: [camada-X, categoria, subcategoria]
camada: X  # 1=conceito, 2=regra, 3=modelo, 4=sistema, 5=sabedoria
categoria: ICT | B05 Trade System | BACKTEST | DIARIO
status: validado | em_teste | monitorando
ultima_revisao: YYYY-MM-DD
---
```

### Regra dos 5 Links Mínimos:
Toda nota md adicionada no vault deve conter no mínimo 5 wikilinks cruzados direcionados para outras notas, garantindo que o Graph View do Obsidian mantenha-se redondo, denso e sem notas isoladas (órfãs).

---

## 2. Processo de Extração Cautelosa do YouTube (Fase 1)

A extração de transcrições do canal ICT no YouTube (`core/ict_brain/extractor.py`) está sujeita a bloqueios de IP (Erros 429) por parte do Google.
Para evitar que o robô seja bloqueado:
- **Delay entre vídeos**: Manter delays aleatórios de **35 a 65 segundos** por vídeo.
- **Cooldown**: A cada **5 vídeos extraídos**, acionar uma pausa de resfriamento (cooldown) aleatória entre **120 e 240 segundos**.
- **Log de Progresso**: O arquivo `data/ict_brain/extraction_progress.json` gerencia o estado.
- **Diferenciação de Falhas**:
  - `failed`: Falhas temporárias (rede/cooldown). Podem ser limpos para nova tentativa.
  - `no_transcript`: Falhas definitivas (vídeo sem legenda/desativado). Devem ser ignorados para sempre.

---

## 3. Script de Vinculação e Enriquecimento (Linker)

Sempre que a Fase 3 (Distiller) gerar novas notas a partir de transcrições, ou quando novas notas do sistema forem adicionadas manualmente, o agente deve rodar o script de enriquecimento de conexões neurais:
```bash
python scratch/obsidian_brain_linker.py
```
Esse script varre o vault, identifica termos-chave e insere wikilinks automaticamente nas seções `## 🔗 Conexões Neurais`.

---

## 4. Ordem e Fluxo do RAG no Trading

Ao ler o cérebro para tomar decisões de mercado em tempo real, a lógica do robô deve seguir a hierarquia executiva de cima para baixo:
1. **Filtros e Checklist** (`Mentalidade Pre-Trade/`)
2. **Parâmetros de Risco** (`Gerenciamento Validado/`)
3. **Estratégia Escolhida** (`Estrategias Validadas/`)
4. **Execução e Condução** (`Conducao de Trade/`)
5. **Vigilância no Trade** (`Durante o Trade/`)
6. **Protocolo Pós-Operação** (`Pos-Trade/`)
