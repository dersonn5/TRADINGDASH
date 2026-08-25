"""
ICT Brain — Pipeline Completo com Retry Automático
====================================================
Roda as 3 fases em sequência:
  Fase 1: Extrator   — baixa transcrições do YouTube (com retry dos 'failed')
  Fase 2: Indexer    — indexa chunks no ChromaDB
  Fase 3: Distiller  — destila regras ICT no Obsidian via LLM

Uso:
    python run_pipeline.py                          # pipeline completo (extrator + indexer + distiller)
    python run_pipeline.py --extract-only           # só extração
    python run_pipeline.py --index-only             # só indexação
    python run_pipeline.py --distill-only           # só destilação
    python run_pipeline.py --max 20                 # extrai até 20 vídeos (teste)
    python run_pipeline.py --retry-failed           # inclui vídeos que falharam antes
    python run_pipeline.py --cat fair_value_gap     # destila só uma categoria
    python run_pipeline.py --stats                  # mostra status do banco
    python run_pipeline.py --loop                   # loop contínuo (extrai → indexa → destila → aguarda → repete)

Dica: Para rodar em segundo plano no Windows, use:
    start /B python run_pipeline.py --loop > logs_pipeline.txt 2>&1
"""

import sys
import io
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

# ─── Forçar UTF-8 no Windows ───────────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

PROGRESS_FILE = BASE_DIR / "data" / "ict_brain" / "extraction_progress.json"
METADATA_FILE = BASE_DIR / "data" / "ict_brain" / "videos_metadata.json"
PIPELINE_LOG  = BASE_DIR / "data" / "ict_brain" / "pipeline_log.json"

# Intervalo entre ciclos no modo --loop (em segundos)
LOOP_INTERVAL_HOURS = 4
LOOP_INTERVAL_S = LOOP_INTERVAL_HOURS * 3600


# ─── Utilitários ─────────────────────────────────────────────────────────────

def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _banner(title: str):
    print("\n" + "=" * 64, flush=True)
    print(f"  {title}", flush=True)
    print("=" * 64, flush=True)


def _append_pipeline_log(entry: dict):
    """Salva log de execução do pipeline em JSON para auditoria."""
    log = []
    if PIPELINE_LOG.exists():
        try:
            log = json.load(open(PIPELINE_LOG, encoding="utf-8"))
        except Exception:
            log = []
    log.append(entry)
    # Mantém apenas os últimos 50 registros
    log = log[-50:]
    PIPELINE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PIPELINE_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ─── Retry de vídeos com falha ───────────────────────────────────────────────

def clear_failed(max_retry: int = None):
    """
    Move vídeos da lista 'failed' de volta para a fila (não-extraídos),
    permitindo que sejam retentados na próxima execução.

    Args:
        max_retry: Quantidade máxima de IDs para remover dos 'failed'
                   (None = limpa todos)
    """
    if not PROGRESS_FILE.exists():
        _log("[retry] Nenhum arquivo de progresso encontrado.")
        return 0

    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)

    failed_before = len(progress.get("failed", []))
    if failed_before == 0:
        _log("[retry] Nenhum vídeo na lista de falhas.")
        return 0

    if max_retry:
        # Remove apenas os N primeiros falhos (para retry controlado)
        removed = progress["failed"][:max_retry]
        progress["failed"] = progress["failed"][max_retry:]
    else:
        # Limpa todos
        removed = progress["failed"]
        progress["failed"] = []

    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

    _log(f"[retry] {len(removed)} vídeos removidos de 'failed' → voltaram para a fila.")
    return len(removed)


def show_status():
    """Exibe status detalhado do pipeline."""
    _banner("ICT BRAIN — STATUS DO PIPELINE")

    # Extração
    if METADATA_FILE.exists():
        meta = json.load(open(METADATA_FILE, encoding="utf-8"))
        _log(f"[status] Videos no canal (metadata): {len(meta)}")
    else:
        _log("[status] Metadata não encontrado — rode o extrator primeiro.")

    if PROGRESS_FILE.exists():
        prog = json.load(open(PROGRESS_FILE, encoding="utf-8"))
        extracted = len(prog.get("extracted", []))
        failed = len(prog.get("failed", []))
        _log(f"[status] Extraidos com sucesso: {extracted}")
        _log(f"[status] Falhos (sem transcricao disponivel): {failed}")
        _log(f"[status] Ultimo run: {prog.get('last_run', 'N/A')}")
    else:
        _log("[status] Nenhum progresso registrado ainda.")

    # Transcrições em disco
    transcripts_dir = BASE_DIR / "data" / "ict_brain" / "transcripts"
    if transcripts_dir.exists():
        jsons = list(transcripts_dir.glob("*.json"))
        _log(f"[status] Transcricoes em disco: {len(jsons)} arquivos")

    # ChromaDB
    try:
        from core.ict_brain.indexer import CHROMA_DIR, COLLECTION_NAME, PROFITABLE_COLLECTION
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        col = client.get_or_create_collection(COLLECTION_NAME)
        pcol = client.get_or_create_collection(PROFITABLE_COLLECTION)
        _log(f"[status] ChromaDB — colecao geral: {col.count()} chunks")
        _log(f"[status] ChromaDB — cerebro lucrativo: {pcol.count()} chunks")
    except Exception as e:
        _log(f"[status] ChromaDB nao disponivel: {e}")

    # Obsidian — arquivos destilados
    from core.ict_brain.taxonomy import CATEGORIES
    obsidian_ict = BASE_DIR / "Cerebro_Obsidian" / "Trading AI" / "01_Regras_ICT"
    destilados = 0
    _log(f"[status] Obsidian — regras destiladas:")
    for cat_id, cat in CATEGORIES.items():
        arquivo = obsidian_ict / cat["arquivo"]
        status = "✓" if arquivo.exists() else "✗"
        _log(f"          [{status}] {cat['arquivo']}")
        if arquivo.exists():
            destilados += 1
    _log(f"[status] Total destilado: {destilados}/{len(CATEGORIES)} categorias")

    # Log do pipeline
    if PIPELINE_LOG.exists():
        logs = json.load(open(PIPELINE_LOG, encoding="utf-8"))
        if logs:
            last = logs[-1]
            _log(f"[status] Ultimo ciclo do pipeline: {last.get('timestamp', 'N/A')}")
            _log(f"[status]   -> novos videos extraidos: {last.get('new_extracted', 0)}")
            _log(f"[status]   -> chunks indexados: {last.get('new_chunks', 0)}")
            _log(f"[status]   -> categorias destiladas: {last.get('distilled', 0)}")


# ─── Fases do Pipeline ───────────────────────────────────────────────────────

def phase1_extract(max_videos: int = None, fresh: bool = False) -> dict:
    """Fase 1: Extração de transcrições do YouTube."""
    _banner("FASE 1 — EXTRATOR DE TRANSCRICOES")
    from core.ict_brain.extractor import ICTExtractor
    extractor = ICTExtractor()
    return extractor.run(max_videos=max_videos, resume=not fresh)


def phase2_index(rebuild: bool = False) -> dict:
    """Fase 2: Indexação vetorial (ChromaDB)."""
    _banner("FASE 2 — INDEXACAO VETORIAL (ChromaDB)")
    from core.ict_brain.indexer import ICTIndexer
    indexer = ICTIndexer()
    return indexer.run(rebuild=rebuild)


def phase3_distill(cat: str = None, rebuild: bool = False) -> dict:
    """Fase 3: Destilação com LLM → arquivos Markdown no Obsidian."""
    _banner("FASE 3 — DESTILACAO LLM -> OBSIDIAN")
    from core.ict_brain.distiller import ICTDistiller
    from core.ict_brain.taxonomy import CATEGORIES

    distiller = ICTDistiller()
    cat_ids = [cat] if cat else None

    if cat_ids:
        _log(f"[distiller] Categoria selecionada: {cat}")
    else:
        _log(f"[distiller] Destilando todas as {len(CATEGORIES)} categorias...")

    return distiller.run(cat_ids=cat_ids, rebuild=rebuild)


# ─── Pipeline principal ──────────────────────────────────────────────────────

def run_once(args) -> dict:
    """
    Executa um ciclo completo do pipeline.
    Retorna dict com resumo do que foi feito.
    """
    start_ts = datetime.now()
    summary = {
        "timestamp":     start_ts.isoformat(),
        "new_extracted": 0,
        "new_chunks":    0,
        "distilled":     0,
        "errors":        [],
    }

    # Retry de falhos se solicitado
    if args.retry_failed:
        retried = clear_failed(max_retry=args.retry_max)
        summary["retried_failed"] = retried

    # ─── Só extração ──────────────────────────────────────
    if args.extract_only:
        r = phase1_extract(max_videos=args.max, fresh=args.fresh)
        summary["new_extracted"] = r.get("new_this_run", 0)
        return summary

    # ─── Só indexação ─────────────────────────────────────
    if args.index_only:
        r = phase2_index(rebuild=args.rebuild)
        summary["new_chunks"] = r.get("indexed", 0)
        return summary

    # ─── Só destilação ────────────────────────────────────
    if args.distill_only:
        r = phase3_distill(cat=args.cat, rebuild=args.rebuild)
        summary["distilled"] = sum(1 for v in r.values() if v["success"])
        return summary

    # ─── Pipeline completo ────────────────────────────────
    _log("[pipeline] Iniciando pipeline completo: Extrator -> Indexer -> Distiller")

    # Fase 1
    try:
        r1 = phase1_extract(max_videos=args.max, fresh=args.fresh)
        summary["new_extracted"] = r1.get("new_this_run", 0)
    except Exception as e:
        _log(f"[pipeline] ERRO na Fase 1 (extrator): {e}")
        summary["errors"].append(f"fase1: {e}")

    # Fase 2 — só indexa se tiver transcrições
    transcripts_dir = BASE_DIR / "data" / "ict_brain" / "transcripts"
    if transcripts_dir.exists() and any(transcripts_dir.glob("*.json")):
        try:
            r2 = phase2_index(rebuild=args.rebuild)
            summary["new_chunks"] = r2.get("indexed", 0)
        except Exception as e:
            _log(f"[pipeline] ERRO na Fase 2 (indexer): {e}")
            summary["errors"].append(f"fase2: {e}")
    else:
        _log("[pipeline] Fase 2 pulada — nenhuma transcricao em disco ainda.")

    # Fase 3 — destila se houver chunks no banco
    try:
        from core.ict_brain.indexer import CHROMA_DIR, COLLECTION_NAME
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        col = client.get_or_create_collection(COLLECTION_NAME)
        total_chunks = col.count()
    except Exception:
        total_chunks = 0

    if total_chunks > 0:
        try:
            r3 = phase3_distill(cat=args.cat, rebuild=args.rebuild)
            summary["distilled"] = sum(1 for v in r3.values() if v["success"])
            
            # --- Fase 4: Enriquecimento Neural (Linker) ---
            _banner("FASE 4 — LINKADOR NEURAL (OBSIDIAN LINKER)")
            try:
                from scratch.obsidian_brain_linker import run as run_linker
                _log("[linker] Iniciando enriquecimento de wikilinks...")
                run_linker()
                _log("[linker] Enriquecimento concluido com sucesso!")
            except Exception as e:
                _log(f"[linker] Falha ao rodar o linkador: {e}")
                summary["errors"].append(f"linker: {e}")
        except Exception as e:
            _log(f"[pipeline] ERRO na Fase 3 (distiller): {e}")
            summary["errors"].append(f"fase3: {e}")
    else:
        _log("[pipeline] Fase 3 pulada — ChromaDB vazio.")

    elapsed = (datetime.now() - start_ts).total_seconds()
    summary["elapsed_s"] = round(elapsed)

    _banner("PIPELINE CONCLUIDO")
    _log(f"  Novos videos extraidos: {summary['new_extracted']}")
    _log(f"  Novos chunks indexados: {summary['new_chunks']}")
    _log(f"  Categorias destiladas:  {summary['distilled']}")
    _log(f"  Tempo total:            {elapsed:.0f}s ({elapsed/60:.1f} min)")
    if summary["errors"]:
        _log(f"  Erros: {', '.join(summary['errors'])}")

    return summary


def run_loop(args):
    """Modo loop contínuo: roda o pipeline, aguarda, repete."""
    cycle = 0
    while True:
        cycle += 1
        _banner(f"CICLO {cycle} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        summary = run_once(args)
        _append_pipeline_log(summary)

        _log(f"[loop] Ciclo {cycle} concluido. Proximo ciclo em {LOOP_INTERVAL_HOURS}h...")
        _log(f"[loop] Aguardando {LOOP_INTERVAL_S}s... (Ctrl+C para interromper)")

        try:
            time.sleep(LOOP_INTERVAL_S)
        except KeyboardInterrupt:
            _log("[loop] Interrompido pelo usuario.")
            break


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ICT Brain — Pipeline Extrator + Indexer + Distiller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run_pipeline.py                        # pipeline completo
  python run_pipeline.py --extract-only         # só extração
  python run_pipeline.py --extract-only --max 10  # extrai 10 vídeos (teste)
  python run_pipeline.py --retry-failed         # limpa falhos e retenta
  python run_pipeline.py --retry-failed --retry-max 50  # retenta 50 falhos
  python run_pipeline.py --index-only           # só indexa
  python run_pipeline.py --distill-only         # só destila
  python run_pipeline.py --distill-only --cat fair_value_gap  # destila 1 categoria
  python run_pipeline.py --stats                # status detalhado
  python run_pipeline.py --loop                 # loop contínuo a cada 4h
        """
    )

    # Modos de execução
    parser.add_argument("--extract-only",  action="store_true", help="Só a fase de extração")
    parser.add_argument("--index-only",    action="store_true", help="Só a fase de indexação")
    parser.add_argument("--distill-only",  action="store_true", help="Só a fase de destilação")
    parser.add_argument("--stats",         action="store_true", help="Status detalhado do pipeline")
    parser.add_argument("--loop",          action="store_true", help=f"Modo loop (repete a cada {LOOP_INTERVAL_HOURS}h)")

    # Opções de extração
    parser.add_argument("--max",           type=int,   default=None, help="Máximo de vídeos a extrair por ciclo")
    parser.add_argument("--fresh",         action="store_true",      help="Ignora cache (relista o canal do zero)")
    parser.add_argument("--retry-failed",  action="store_true",      help="Inclui vídeos que falharam antes no retry")
    parser.add_argument("--retry-max",     type=int,   default=None, help="Máx. de falhos para retentar (None = todos)")

    # Opções de destilação
    parser.add_argument("--cat",           type=str,   default=None, help="Categoria específica para destilar")
    parser.add_argument("--rebuild",       action="store_true",      help="Reconstrói índice/destilação do zero")

    args = parser.parse_args()

    _banner("ICT BRAIN PIPELINE")
    _log(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.stats:
        show_status()
        return

    if args.loop:
        run_loop(args)
    else:
        summary = run_once(args)
        _append_pipeline_log(summary)


if __name__ == "__main__":
    main()
