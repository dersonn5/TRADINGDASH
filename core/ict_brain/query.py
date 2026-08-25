"""
ICT Brain — Query Engine
========================
Motor de busca semântica sobre o banco vetorial do ICT.

Uso:
    from core.ict_brain.query import ICTBrainQuery
    brain = ICTBrainQuery()
    results = brain.search("how to trade fair value gap in killzone")
    context = brain.get_context_for_agent("fair value gap silver bullet")
"""

from pathlib import Path
from typing import Optional

# ─── Configurações ──────────────────────────────────────────────────────────

import os

BASE_DIR       = Path(__file__).resolve().parents[2]
CHROMA_DIR     = BASE_DIR / "data" / "ict_brain" / "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "ict_brain"

# Garantir que a pasta exista para poder obter o short path
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Se estiver no Windows, converte para short path 8.3 ASCII para evitar bug de acentuação no HNSW do C++
if os.name == "nt":
    try:
        import ctypes
        _buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetShortPathNameW(str(CHROMA_DIR), _buf, 1024)
        if _buf.value:
            CHROMA_DIR = Path(_buf.value)
    except Exception:
        pass

# Número padrão de resultados
DEFAULT_N_RESULTS = 5

# Limiar mínimo de relevância (distância cosine — menor = mais relevante)
MIN_RELEVANCE_DISTANCE = 0.6


class ICTBrainQuery:
    """Interface de busca semântica no cérebro ICT."""

    def __init__(self):
        self._client     = None
        self._collection = None
        self._profitable_collection = None
        self._embedder   = None

    @property
    def client(self):
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                self._client = chromadb.PersistentClient(
                    path=str(CHROMA_DIR),
                    settings=Settings(anonymized_telemetry=False)
                )
            except ImportError:
                raise RuntimeError("ChromaDB não instalado. Execute: pip install chromadb")
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    @property
    def profitable_collection(self):
        if self._profitable_collection is None:
            try:
                from core.ict_brain.indexer import PROFITABLE_COLLECTION
                self._profitable_collection = self.client.get_or_create_collection(
                    name=PROFITABLE_COLLECTION,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception:
                pass
        return self._profitable_collection

    @property
    def embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(EMBEDDING_MODEL)
            except ImportError:
                raise RuntimeError("sentence-transformers não instalado.")
        return self._embedder

    def is_ready(self) -> bool:
        """Verifica se o banco vetorial está disponível e populado."""
        try:
            return CHROMA_DIR.exists() and self.collection.count() > 0
        except Exception:
            return False

    def get_stats(self) -> dict:
        """Retorna estatísticas do banco vetorial."""
        if not CHROMA_DIR.exists():
            return {"status": "not_built", "total_chunks": 0, "profitable_chunks": 0}
        try:
            count = self.collection.count()
            p_count = 0
            if self.profitable_collection:
                p_count = self.profitable_collection.count()
            return {
                "status":            "ready" if count > 0 else "empty",
                "total_chunks":      count,
                "profitable_chunks": p_count,
                "db_path":           str(CHROMA_DIR),
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "total_chunks": 0, "profitable_chunks": 0}

    def search(self, query: str, n_results: int = DEFAULT_N_RESULTS) -> list[dict]:
        """
        Busca semântica no banco vetorial ICT.

        Args:
            query:     Pergunta ou trecho de conceito ICT (em inglês de preferência)
            n_results: Quantos resultados retornar

        Returns:
            Lista de resultados com texto, metadados e score de relevância
        """
        if not self.is_ready():
            return []

        # Gera embedding da query
        query_emb = self.embedder.encode([query]).tolist()

        # Busca no ChromaDB
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("ids"):
            return []

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            relevance = round(1.0 - dist, 3)  # converte distância em score (0-1)
            output.append({
                "text":        doc,
                "relevance":   relevance,
                "video_title": meta.get("video_title", "Unknown"),
                "video_url":   meta.get("video_url", ""),
                "timestamp":   meta.get("timestamp", "00:00"),
                "upload_date": meta.get("upload_date", ""),
                "source":      f"{meta.get('video_title', 'ICT')} @ {meta.get('timestamp', '?')}",
            })

        # Ordena por relevância decrescente
        output.sort(key=lambda x: x["relevance"], reverse=True)
        return output

    def get_context_for_agent(
        self,
        query: str,
        n_results: int = 4,
        max_chars: int = 3000
    ) -> str:
        """
        Formata resultados para injeção no contexto do agente ICT.
        Compatível com o formato do core/rag.py.

        Args:
            query:     Contexto do setup atual (conceitos ICT relevantes)
            n_results: Número de trechos a incluir
            max_chars: Limite de caracteres no contexto retornado

        Returns:
            String formatada para inserção no prompt do agente
        """
        if not self.is_ready():
            return (
                "[ICT Brain] ⚠ Base de conhecimento YouTube ainda não construída.\n"
                "Execute: python -m core.ict_brain.extractor && python -m core.ict_brain.indexer"
            )

        results = self.search(query, n_results=n_results)
        if not results:
            return "[ICT Brain] Nenhum trecho relevante encontrado para este setup."

        lines = ["=== CONHECIMENTO ICT (YouTube — Transcricoes Literais) ==="]
        char_count = 0

        for i, r in enumerate(results, 1):
            url_with_ts = r["video_url"]
            # Adiciona timestamp ao link do YouTube se disponivel
            ts = r.get("timestamp", "00:00")
            if ts and ts != "00:00":
                try:
                    m, s = ts.split(":")
                    total_s = int(m) * 60 + int(s)
                    url_with_ts = f"{r['video_url']}&t={total_s}s"
                except Exception:
                    pass

            block = (
                f"\n[Trecho {i} -- Relevancia: {r['relevance']:.0%}]\n"
                f"Video: {r['video_title']}\n"
                f"Timestamp: {ts} -> {url_with_ts}\n"
                f"Conteudo:\n\"{r['text']}\"\n"
            )

            if char_count + len(block) > max_chars:
                break

            lines.append(block)
            char_count += len(block)

        lines.append("\n=== FIM DO CONHECIMENTO ICT (YouTube) ===")
        return "\n".join(lines)


# ─── Execução standalone ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ICT Brain Query Engine")
    parser.add_argument("query", nargs="?", default="fair value gap killzone", help="Termo de busca")
    parser.add_argument("--n",   type=int, default=5, help="Número de resultados")
    parser.add_argument("--stats", action="store_true", help="Mostra estatísticas do banco")
    args = parser.parse_args()

    brain = ICTBrainQuery()

    if args.stats:
        stats = brain.get_stats()
        print(f"\n📊 ICT Brain Stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print(f"\n🔍 Buscando: \"{args.query}\"\n")
        results = brain.search(args.query, n_results=args.n)
        if not results:
            print("⚠ Sem resultados. O banco está vazio? Execute o extractor + indexer primeiro.")
        else:
            for i, r in enumerate(results, 1):
                print(f"[{i}] Relevância: {r['relevance']:.0%}")
                print(f"     📹 {r['video_title']}")
                print(f"     ⏱ {r['timestamp']} → {r['video_url']}")
                print(f"     📝 {r['text'][:200]}...")
                print()
