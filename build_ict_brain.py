"""
ICT Brain Builder — Pipeline Completo
======================================
Executa as 3 fases em sequência:
  Fase 1: Extração de transcrições (yt-dlp + youtube-transcript-api)
  Fase 2: Indexação vetorial (sentence-transformers + ChromaDB)
  Fase 3: Teste de consulta

Uso:
    python build_ict_brain.py                   # pipeline completo
    python build_ict_brain.py --extract-only    # só extração
    python build_ict_brain.py --index-only      # só indexação
    python build_ict_brain.py --test            # teste de busca
    python build_ict_brain.py --max 50          # extrai só 50 vídeos (teste)
    python build_ict_brain.py --stats           # status do banco

Dica: Para extrair todos os vídeos (pode demorar horas), rode:
    python build_ict_brain.py

E deixe rodando em segundo plano. É incremental — pode interromper e
continuar de onde parou.
"""

"""
ICT Brain Builder -- Pipeline Completo
======================================
Executa as 3 fases em sequencia:
  Fase 1: Extracao de transcricoes (yt-dlp + youtube-transcript-api)
  Fase 2: Indexacao vetorial (sentence-transformers + ChromaDB)
  Fase 3: Teste de consulta

Uso:
    python build_ict_brain.py                   # pipeline completo
    python build_ict_brain.py --extract-only    # so extracao
    python build_ict_brain.py --index-only      # so indexacao
    python build_ict_brain.py --test            # teste de busca
    python build_ict_brain.py --max 50          # extrai so 50 videos (teste)
    python build_ict_brain.py --stats           # status do banco
"""

import sys
import io
import argparse
from pathlib import Path

# Forcar UTF-8 no stdout/stderr do Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


def check_dependencies():
    """Verifica e instala dependencias necessarias."""
    missing = []
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        missing.append("youtube-transcript-api")

    try:
        import chromadb
    except ImportError:
        missing.append("chromadb")

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        missing.append("sentence-transformers")

    if missing:
        print(f"[!] Dependencias faltando: {', '.join(missing)}")
        print(f"Instalando...")
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet", *missing
        ])
        print("[OK] Dependencias instaladas!\n")


def phase1_extract(max_videos: int = None, fresh: bool = False):
    """Fase 1: Extracao de transcricoes do YouTube."""
    print("\n" + "=" * 60)
    print("[FASE 1] EXTRACAO DE TRANSCRICOES")
    print("=" * 60)
    from core.ict_brain.extractor import ICTExtractor
    extractor = ICTExtractor()
    return extractor.run(max_videos=max_videos, resume=not fresh)


def phase2_index(rebuild: bool = False):
    """Fase 2: Indexacao vetorial."""
    print("\n" + "=" * 60)
    print("[FASE 2] INDEXACAO VETORIAL")
    print("=" * 60)
    from core.ict_brain.indexer import ICTIndexer
    indexer = ICTIndexer()
    return indexer.run(rebuild=rebuild)


def phase3_test():
    """Fase 3: Teste de busca semantica."""
    print("\n" + "=" * 60)
    print("[FASE 3] TESTE DE BUSCA")
    print("=" * 60)
    from core.ict_brain.query import ICTBrainQuery
    brain = ICTBrainQuery()

    test_queries = [
        "fair value gap trading setup",
        "market structure shift killzone",
        "liquidity sweep buy side sell side",
        "silver bullet 10am 11am",
        "optimal trade entry OTE fibonacci",
    ]

    stats = brain.get_stats()
    print(f"\n[INFO] Banco vetorial geral: {stats.get('total_chunks', 0)} chunks")

    # Mostra stats do cerebro lucrativo tambem
    p_chunks = stats.get("profitable_chunks", 0)
    if p_chunks > 0:
        print(f"[INFO] Cerebro Lucrativo (filtrado): {p_chunks} chunks tecnicos")

    if stats.get("total_chunks", 0) == 0:
        print("[AVISO] Banco vazio! Execute a extracao e indexacao primeiro.")
        return

    for query in test_queries:
        print(f"\n[BUSCA] {query}")
        results = brain.search(query, n_results=2)
        for i, r in enumerate(results, 1):
            print(f"   [{i}] {r['relevance']:.0%} | {r['video_title'][:50]} @ {r['timestamp']}")
            print(f"        > {r['text'][:120]}...")


def phase4_distill(cat: str = None, rebuild: bool = False):
    """Fase 4: Destilacao com Gemini -- cria regras em Portugues no Obsidian."""
    print("\n" + "=" * 60)
    print("[FASE 4] DESTILACAO COM GEMINI --> OBSIDIAN")
    print("Extraindo o MELHOR dos ensinamentos do ICT")
    print("=" * 60)
    from core.ict_brain.distiller import ICTDistiller
    from core.ict_brain.taxonomy import CATEGORIES

    distiller = ICTDistiller()
    cat_ids = [cat] if cat else None

    if cat_ids:
        print(f"[Distiller] Categoria selecionada: {cat}")
    else:
        print(f"[Distiller] Destilando todas as {len(CATEGORIES)} categorias...")

    return distiller.run(cat_ids=cat_ids, rebuild=rebuild)


def show_stats():
    """Mostra status completo do ICT Brain."""
    from core.ict_brain.query import ICTBrainQuery
    from core.ict_brain.extractor import TRANSCRIPTS_DIR, PROGRESS_FILE, METADATA_FILE
    from core.ict_brain.taxonomy import CATEGORIES
    import json

    brain = ICTBrainQuery()
    stats = brain.get_stats()

    print("\n" + "=" * 60)
    print("ICT BRAIN -- STATUS COMPLETO")
    print("=" * 60)

    transcript_count = len(list(TRANSCRIPTS_DIR.glob("*.json"))) if TRANSCRIPTS_DIR.exists() else 0
    print(f"\n[EXTRACAO]")
    print(f"  Videos mapeados: ", end="")

    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            meta = json.load(f)
        print(len(meta))
    else:
        print("0 (liste o canal primeiro)")

    print(f"  Transcricoes baixadas: {transcript_count}")

    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            prog = json.load(f)
        print(f"  Extraidos com sucesso: {len(prog['extracted'])}")
        print(f"  Falhas (sem transcricao): {len(prog['failed'])}")
        print(f"  Ultima execucao: {prog.get('last_run', 'N/A')}")

    print(f"\n[BANCO VETORIAL]")
    print(f"  Colecao geral (ict_brain): {stats.get('total_chunks', 0)} chunks")
    p_chunks = stats.get("profitable_chunks", 0)
    pct = f"{p_chunks / stats['total_chunks'] * 100:.0f}%" if stats.get('total_chunks', 0) > 0 else "N/A"
    print(f"  Cerebro Lucrativo (filtrado): {p_chunks} chunks ({pct} do total)")

    print(f"\n[OBSIDIAN -- REGRAS DESTILADAS]")
    from pathlib import Path
    obsidian_ict = Path("Cerebro_Obsidian") / "Trading AI" / "B03 Regras ICT"
    for cat_id, cat in CATEGORIES.items():
        arquivo = obsidian_ict / cat["arquivo"]
        status = "OK" if arquivo.exists() else "--"
        print(f"  [{status}] {cat['arquivo']}")


def main():
    parser = argparse.ArgumentParser(
        description="ICT Brain Builder -- Segundo Cerebro do Michael J. Huddleston",
    )
    parser.add_argument("--extract-only",  action="store_true", help="So a fase de extracao")
    parser.add_argument("--index-only",    action="store_true", help="So a fase de indexacao")
    parser.add_argument("--distill-only",  action="store_true", help="So a fase de destilacao (requer transcricoes)")
    parser.add_argument("--distill",       action="store_true", help="Inclui destilacao no pipeline")
    parser.add_argument("--cat",           type=str, default=None, help="Categoria para destilar (ex: fair_value_gap)")
    parser.add_argument("--test",          action="store_true", help="Testa a busca semantica")
    parser.add_argument("--stats",         action="store_true", help="Status completo do banco")
    parser.add_argument("--max",           type=int, default=None, help="Maximo de videos a extrair")
    parser.add_argument("--fresh",         action="store_true", help="Ignora cache de videos")
    parser.add_argument("--rebuild",       action="store_true", help="Reconstroi o indice do zero")
    parser.add_argument("--skip-deps",     action="store_true", help="Pula verificacao de dependencias")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("ICT BRAIN BUILDER")
    print("Segundo Cerebro Lucrativo de Michael J. Huddleston (ICT)")
    print("=" * 60)

    if not args.skip_deps:
        check_dependencies()

    if args.stats:
        show_stats()
        return

    if args.test:
        phase3_test()
        return

    if args.extract_only:
        phase1_extract(max_videos=args.max, fresh=args.fresh)
        return

    if args.index_only:
        phase2_index(rebuild=args.rebuild)
        return

    if args.distill_only:
        phase4_distill(cat=args.cat, rebuild=args.rebuild)
        return

    # Pipeline completo
    print(f"\n[START] Iniciando pipeline completo...")
    if args.max:
        print(f"   (Limitado a {args.max} videos -- modo teste)")

    summary1 = phase1_extract(max_videos=args.max, fresh=args.fresh)
    summary2 = phase2_index(rebuild=args.rebuild)
    phase3_test()

    if args.distill:
        summary3 = phase4_distill(cat=args.cat, rebuild=args.rebuild)
        distilled_ok = sum(1 for r in summary3.values() if r["success"])
    else:
        distilled_ok = 0
        print("\n[INFO] Para destilar regras no Obsidian, rode:")
        print("       python build_ict_brain.py --distill-only")

    print("\n" + "=" * 60)
    print("[OK] ICT BRAIN CONCLUIDO!")
    print(f"  Videos processados: {summary1.get('extracted', 0)}")
    print(f"  Chunks no banco (geral): {summary2.get('total_chunks', 0)}")
    if distilled_ok:
        print(f"  Categorias destiladas no Obsidian: {distilled_ok}")
    print(f"\n  Cerebro Lucrativo ativo -- agente consultara conhecimento")
    print(f"  filtrado do ICT antes de cada trade.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
