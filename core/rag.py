import os
from pathlib import Path
from datetime import datetime
import config

# ICT Brain (YouTube) — importação lazy para não bloquear inicialização
_ict_brain = None

def _get_ict_brain():
    """Retorna instância singleton do ICTBrainQuery, ou None se indisponível."""
    global _ict_brain
    if _ict_brain is None:
        try:
            from core.ict_brain.query import ICTBrainQuery
            _ict_brain = ICTBrainQuery()
        except Exception:
            pass
    return _ict_brain

class ObsidianRAG:
    """
    Motor RAG Local de Baixa Latência para o Obsidian.
    Lê e formata as anotações do trader, regras de ICT e histórico recente de diário.
    """

    @staticmethod
    def score_content(content: str, keywords: list) -> int:
        """Retorna uma pontuação de relevância baseada na contagem de ocorrências de palavras-chave."""
        if not keywords:
            return 0
        content_lower = content.lower()
        score = 0
        for kw in keywords:
            if len(kw) > 2:  # Ignora palavras muito curtas
                score += content_lower.count(kw.lower())
        return score

    @staticmethod
    def read_markdown_files(directory: Path, keywords: list = None, limit: int = None) -> str:
        """Lê os arquivos .md de um diretório, pontua sua relevância e retorna os mais relevantes."""
        if not directory.exists():
            return "Nenhuma anotação encontrada neste diretório."
            
        compiled_notes = []
        files = list(directory.glob("*.md"))
        
        # Se keywords forem fornecidas, pontuamos cada arquivo
        scored_files = []
        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                score = ObsidianRAG.score_content(content, keywords) if keywords else 0
                scored_files.append((score, filepath, content))
            except Exception as e:
                print(f"[RAG] Erro ao ler {filepath.name}: {e}")
                
        # Ordena decrescente por score, depois alfabético por nome de arquivo se empate
        if keywords:
            scored_files.sort(key=lambda x: (-x[0], x[1].name))
        else:
            scored_files.sort(key=lambda x: x[1].name)
            
        # Aplica limite se houver
        selected_files = scored_files[:limit] if limit else scored_files
        
        for score, filepath, content in selected_files:
            filename = filepath.stem.replace("_", " ").upper()
            relevance_msg = f" [Relevância: {score}]" if keywords else ""
            compiled_notes.append(f"--- REGRA: {filename}{relevance_msg} ---\n{content}\n")
            
        return "\n".join(compiled_notes) if compiled_notes else "Nenhuma anotação disponível."

    @classmethod
    def get_ict_rules(cls, keywords: list = None) -> str:
        """Recupera os 3 arquivos de regras de ICT mais relevantes."""
        return cls.read_markdown_files(config.ICT_RULES_DIR, keywords=keywords, limit=3)

    @classmethod
    def get_lessons_learned(cls, keywords: list = None) -> str:
        """Recupera as 3 notas de lições aprendidas mais relevantes."""
        return cls.read_markdown_files(config.LESSONS_LEARNED_DIR, keywords=keywords, limit=3)

    @classmethod
    def get_ict_youtube_knowledge(cls, query: str, n_results: int = 4) -> str:
        """
        Busca trechos relevantes das transcrições do YouTube do ICT.
        Requer que o ICT Brain tenha sido construído via build_ict_brain.py.
        """
        brain = _get_ict_brain()
        if brain is None or not brain.is_ready():
            return (
                "[ICT Brain YouTube] Base não disponível.\n"
                "Execute: python build_ict_brain.py --max 50 (para teste rápido)"
            )
        return brain.get_context_for_agent(query, n_results=n_results)

    @classmethod
    def get_recent_journal_entries(cls, limit: int = 3) -> str:
        """Recupera os diários de trade mais recentes para a IA ter memória recente."""
        if not config.TRADE_JOURNAL_DIR.exists():
            return "Nenhum histórico de diário disponível."
            
        files = sorted(
            config.TRADE_JOURNAL_DIR.glob("*.md"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        compiled_entries = []
        for filepath in files[:limit]:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    compiled_entries.append(f"--- HISTÓRICO DE TRADE ({filepath.stem}) ---\n{content}\n")
            except Exception as e:
                compiled_entries.append(f"Erro ao ler diário {filepath.name}: {str(e)}\n")
                
        return "\n".join(compiled_entries) if compiled_entries else "Nenhum trade recente registrado."

    @classmethod
    def compile_brain_context(cls, setup_data: dict = None) -> str:
        """Compila o cérebro completo em um único prompt de contexto rico:
           Obsidian (regras locais) + YouTube ICT (segundo cérebro do Michael)."""
        print("[RAG] Compilando cérebro do Obsidian + ICT YouTube...")
        keywords = []
        if setup_data:
            for key, value in setup_data.items():
                if isinstance(value, str):
                    words = [w.strip(".,!?()[]{}\"'").lower() for w in value.replace("_", " ").replace("-", " ").split()]
                    keywords.extend([w for w in words if len(w) > 2])
                elif isinstance(value, (int, float)):
                    keywords.append(str(value))

        ict_rules = cls.get_ict_rules(keywords=keywords)
        lessons = cls.get_lessons_learned(keywords=keywords)
        recent_trades = cls.get_recent_journal_entries(limit=3)

        # Busca no segundo cérebro ICT (YouTube)
        youtube_query = " ".join(keywords[:15]) if keywords else "ICT trading concept"
        ict_youtube = cls.get_ict_youtube_knowledge(youtube_query, n_results=4)

        compiled_prompt = f"""
==================================================
CÉREBRO DO OBSIDIAN (CONHECIMENTO DO TRADER & ICT)
==================================================

As seções a seguir contêm as regras operacionais estritas que você DEVE respeitar e a sua própria sabedoria de trade acumulada:

{ict_rules}

==================================================
LIÇÕES OPERACIONAIS & ERROS A EVITAR
==================================================
{lessons}

==================================================
MEMÓRIA DOS ÚLTIMOS TRADES EXECUTADOS
==================================================
{recent_trades}

==================================================
SEGUNDO CÉREBRO ICT — TRANSCRIÇÕES YOUTUBE
==================================================
Os trechos abaixo são palavras LITERAIS do Michael J. Huddleston (ICT)
extraídas dos vídeos do YouTube, semanticamente selecionadas para este setup:

{ict_youtube}

Instrução Rígida para a IA: Você deve se comportar como um Trader de elite. Use as regras de ICT acima para validar o setup. Se o setup atual violar QUALQUER lição ou erro operacional listado nas seções de "LIÇÕES OPERACIONAIS & ERROS A EVITAR", aborte a operação imediatamente!
==================================================
"""
        return compiled_prompt

    @staticmethod
    def write_trade_to_journal(trade_data: dict, is_backtest: bool = False) -> Path:
        """Grava uma nota de trade visualmente linda no Obsidian Vault."""
        if is_backtest:
            # Retorna None para evitar a criação de logs individuais poluindo o cérebro
            return None
            
        timestamp = trade_data.get("timestamp", datetime.now().isoformat())
        # Nome do arquivo amigável: ex: 2026-05-18_XAUUSD_BUY_WIN.md
        date_str = timestamp[:10]
        time_str = timestamp[11:19].replace(":", "-")
        symbol = trade_data.get("symbol", "UNKNOWN")
        # Remover caracteres especiais invalidos no Windows (como dois pontos ':')
        symbol_clean = symbol.replace(":", "_").replace("/", "_").replace("\\", "_")
        action = trade_data.get("action", "PASS")
        result = trade_data.get("result", "PENDING").upper()
        
        filename = f"{date_str}_{time_str}_{symbol_clean}_{action}_{result}.md"
        target_dir = config.BACKTEST_JOURNAL_DIR if is_backtest else config.TRADE_JOURNAL_DIR
        filepath = target_dir / filename
        
        status_emoji = "✅ WIN" if result == "WIN" else ("❌ LOSS" if result == "LOSS" else "⏳ PENDING")
        action_emoji = "🟢 BUY" if action == "BUY" else ("🔴 SELL" if action == "SELL" else "⚪ PASS")
        
        reasoning_text = trade_data.get('reasoning', 'N/A')
        applied = trade_data.get("applied_rules", [])
        
        # Determinar dinamicamente quais regras foram utilizadas baseando-se estritamente na escolha cognitiva da IA
        used_rules = []
        has_strategy = False
        for rule in applied:
            if rule == "Silver_Bullet_Algoritmica":
                used_rules.append("  - [[01_Regras_ICT/Silver_Bullet_Algoritmica|Silver Bullet Algorítmica]]")
                has_strategy = True
                break
            elif rule == "Modelo_Mentoria_2022":
                used_rules.append("  - [[01_Regras_ICT/Modelo_Mentoria_2022|Modelo Mentoria 2022]]")
                has_strategy = True
                break

        if not has_strategy:
            if "erro" in reasoning_text.lower() or "evitar" in reasoning_text.lower() or action == "PASS":
                used_rules.append("  - [[02_Licoes_Aprendidas/Erros_Evitar|Lições Aprendidas & Erros a Evitar]]")
            else:
                used_rules.append("  - [[00_Mapas_de_Conteudo/MOC_Estrategias|MOC Estratégias]]")

        rules_str = "\n".join(used_rules)
        
        # Se for um backtest, isolamos completamente as sinapses!
        # O diário de backtest NÃO apontará para o Cerebro_ICT nem para as notas de regras!
        # Ele se conectará apenas ao arquivo central "Relatorio_Curadoria_Backtest", funcionando como uma pasta.
        if is_backtest:
            connections_block = """## 🔗 Conexões Neurais
- **Retornar ao Relatório Central (Pasta de Backtests)**: [[04_Backtests/Relatorio_Curadoria_Backtest|Relatório Geral de Backtest]]"""
        else:
            month_str = timestamp[5:7] if len(timestamp) > 7 else "06"
            year_str = timestamp[:4] if len(timestamp) > 4 else "2026"
            month_name = {
                "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
                "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
                "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
            }.get(month_str, "Mês")
            monthly_journal_link = f"[[03_Diario_Trades/Diario_{year_str}_{month_str}|Diário de {month_name} de {year_str}]]"
            
            connections_block = f"""## 🔗 Conexões Neurais
- **MOC de Diários**: {monthly_journal_link}
- **Regra Principal Utilizada**:
{rules_str}"""
        
        content = f"""# Relatório de Trade - {symbol} ({action_emoji}) - {status_emoji}
 
---
 
## 1. Informações Gerais
- **Data e Hora**: {timestamp}
- **Ativo**: {symbol}
- **Direção**: {action}
- **Tempo Gráfico**: {trade_data.get('timeframe', 'N/A')}
- **Preço de Entrada**: {trade_data.get('entry_price', 'N/A')}
- **Stop Loss**: {trade_data.get('stop_loss', 'N/A')}
- **Take Profit**: {trade_data.get('take_profit', 'N/A')}
- **Relação Risco:Retorno (R:R)**: {trade_data.get('risk_reward_ratio', 'N/A')}
- **Lote / Tamanho do Trade**: {trade_data.get('size_units', 'N/A')} (Equivale a 1% de risco)
 
---
 
## 2. Raciocínio da IA (Chain-of-Thought)
{reasoning_text}
 
---
 
## 3. Checklist de Filtros
- **Killzone**: {trade_data.get('checklist_killzone', 'N/A')}
- **Varredura de Liquidez**: {trade_data.get('checklist_sweep', 'N/A')}
- **MSS Confirmado**: {trade_data.get('checklist_mss', 'N/A')}
- **Payout Mínimo Atendido**: {trade_data.get('checklist_payout', 'N/A')}
 
---
 
## 4. Observações do Trader
*(Escreva aqui seus sentimentos, aprendizados ou observações sobre esta operação. O robô lerá este campo no próximo trade!)*
 
[Escreva suas notas aqui...]
 
---
 
{connections_block}
 
---
*Relatório gerado de forma automática pelo Super Agente ICT AI.*
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"[RAG] Diário de trade gravado com sucesso no Obsidian: {filepath.name}")
        return filepath
