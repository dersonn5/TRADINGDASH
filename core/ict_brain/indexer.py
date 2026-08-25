"""
ICT Brain — Indexer
===================
Responsável por:
  1. Ler as transcrições JSON extraídas pelo extractor.py
  2. Dividir em chunks semânticos com metadados ricos
  3. Gerar embeddings com sentence-transformers (local, grátis)
  4. Persistir no ChromaDB local em data/ict_brain/chroma_db/

Uso standalone:
    python -m core.ict_brain.indexer
    python -m core.ict_brain.indexer --rebuild   # recria o índice do zero
"""

import json
import re
from pathlib import Path
from datetime import datetime

from core.ict_brain.taxonomy import score_chunk, classify_categories, MIN_SCORE_PROFITABLE

# ─── Configurações ──────────────────────────────────────────────────────────

import os
from pathlib import Path

BASE_DIR        = Path(__file__).resolve().parents[2]
TRANSCRIPTS_DIR = BASE_DIR / "data" / "ict_brain" / "transcripts"
CHROMA_DIR      = BASE_DIR / "data" / "ict_brain" / "chroma_db"
INDEX_LOG       = BASE_DIR / "data" / "ict_brain" / "index_log.json"

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

# Modelo de embedding leve e eficaz para inglês (baixa uma vez, roda offline)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Tamanho dos chunks (em palavras)
CHUNK_SIZE_WORDS   = 150
CHUNK_OVERLAP_WORDS = 30

# Coleção geral (todos os chunks)
COLLECTION_NAME = "ict_brain"
# Coleção filtrada (apenas chunks de alto score — Cerebro Lucrativo)
PROFITABLE_COLLECTION = "ict_profitable_brain"

# Batch size para inserção no ChromaDB
BATCH_SIZE = 50


class ICTIndexer:
    """Converte transcrições brutas em base vetorial pesquisável.
    
    Mantém dois índices:
      - ict_brain: todos os chunks
      - ict_profitable_brain: apenas chunks com score >= MIN_SCORE_PROFITABLE
    """

    def __init__(self):
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self._client                = None
        self._collection            = None
        self._profitable_collection = None
        self._embedder              = None

    # ─── Lazy initialization ─────────────────────────────────────────────

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
        """Inicializa ChromaDB na primeira chamada."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"[Indexer] ChromaDB inicializado → {CHROMA_DIR.name}")
            print(f"[Indexer] Documentos existentes: {self._collection.count()}")
        return self._collection

    @property
    def embedder(self):
        """Inicializa modelo de embedding na primeira chamada."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"[Indexer] Carregando modelo de embedding: {EMBEDDING_MODEL}")
                self._embedder = SentenceTransformer(EMBEDDING_MODEL)
                print("[Indexer] Modelo carregado OK")
            except ImportError:
                raise RuntimeError("sentence-transformers nao instalado. Execute: pip install sentence-transformers")
        return self._embedder

    @property
    def profitable_collection(self):
        """Inicializa a colecao do Cerebro Lucrativo na primeira chamada."""
        if self._profitable_collection is None:
            self._profitable_collection = self.client.get_or_create_collection(
                name=PROFITABLE_COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"[Indexer] Cerebro Lucrativo: {self._profitable_collection.count()} chunks")
        return self._profitable_collection


    # ─── Chunking ────────────────────────────────────────────────────────

    def _format_timestamp(self, seconds: float) -> str:
        """Converte segundos em formato MM:SS."""
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    def _clean_text(self, text: str) -> str:
        """Remove artefatos comuns de transcrições automáticas."""
        # Remove marcadores de música [Music], [Applause], etc.
        text = re.sub(r'\[.*?\]', '', text)
        # Remove múltiplos espaços
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def chunk_transcript(self, transcript_data: dict) -> list[dict]:
        """
        Divide a transcrição em chunks semânticos sobrepostos.
        Cada chunk tem: texto, metadados (vídeo, timestamp, etc.)
        """
        segments = transcript_data.get("segments", [])
        if not segments:
            # Fallback: usa full_text sem timestamps
            full = self._clean_text(transcript_data.get("full_text", ""))
            if not full:
                return []
            return self._chunk_plain_text(full, transcript_data)

        chunks = []
        words_buffer = []
        time_buffer  = []  # timestamps de cada palavra

        for seg in segments:
            text  = self._clean_text(seg.get("text", ""))
            start = seg.get("start", 0)
            if not text:
                continue

            words = text.split()
            for w in words:
                words_buffer.append(w)
                time_buffer.append(start)

            # Quando acumula palavras suficientes, cria um chunk
            while len(words_buffer) >= CHUNK_SIZE_WORDS:
                chunk_words = words_buffer[:CHUNK_SIZE_WORDS]
                chunk_times = time_buffer[:CHUNK_SIZE_WORDS]
                chunk_text  = " ".join(chunk_words)
                chunk_start = chunk_times[0]

                chunk_id = f"{transcript_data['video_id']}_{len(chunks):04d}"
                chunks.append({
                    "id":          chunk_id,
                    "text":        chunk_text,
                    "video_id":    transcript_data["video_id"],
                    "video_title": transcript_data.get("title", "Unknown"),
                    "video_url":   transcript_data.get("url", ""),
                    "timestamp":   self._format_timestamp(chunk_start),
                    "timestamp_s": chunk_start,
                    "upload_date": transcript_data.get("upload_date", ""),
                    "channel":     transcript_data.get("channel", ""),
                })

                # Overlap: mantém as últimas N palavras no buffer
                words_buffer = words_buffer[CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS:]
                time_buffer  = time_buffer[CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS:]

        # Processa o que sobrou no buffer
        if words_buffer:
            chunk_text  = " ".join(words_buffer)
            chunk_start = time_buffer[0] if time_buffer else 0
            chunk_id    = f"{transcript_data['video_id']}_{len(chunks):04d}"
            chunks.append({
                "id":          chunk_id,
                "text":        chunk_text,
                "video_id":    transcript_data["video_id"],
                "video_title": transcript_data.get("title", "Unknown"),
                "video_url":   transcript_data.get("url", ""),
                "timestamp":   self._format_timestamp(chunk_start),
                "timestamp_s": chunk_start,
                "upload_date": transcript_data.get("upload_date", ""),
                "channel":     transcript_data.get("channel", ""),
            })

        return chunks

    def _chunk_plain_text(self, text: str, meta: dict) -> list[dict]:
        """Chunking simples para textos sem timestamps."""
        words  = text.split()
        chunks = []
        i      = 0
        while i < len(words):
            chunk_words = words[i:i + CHUNK_SIZE_WORDS]
            chunk_text  = " ".join(chunk_words)
            chunk_id    = f"{meta['video_id']}_{len(chunks):04d}"
            chunks.append({
                "id":          chunk_id,
                "text":        chunk_text,
                "video_id":    meta["video_id"],
                "video_title": meta.get("title", "Unknown"),
                "video_url":   meta.get("url", ""),
                "timestamp":   "00:00",
                "timestamp_s": 0,
                "upload_date": meta.get("upload_date", ""),
                "channel":     meta.get("channel", ""),
            })
            i += CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS
        return chunks

    # ─── Indexação ───────────────────────────────────────────────────────

    def _get_indexed_ids(self) -> set:
        """Retorna IDs de chunks já indexados (para extração incremental)."""
        try:
            # Busca todos os IDs existentes
            existing = self.collection.get(include=[])
            return set(existing["ids"]) if existing and "ids" in existing else set()
        except Exception:
            return set()

    def index_transcript(self, transcript_path: Path, indexed_ids: set) -> int:
        """Indexa uma transcricao nas duas colecoes (geral + lucrativa).
        
        Retorna quantos chunks novos foram adicionados na colecao geral.
        """
        with open(transcript_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        video_id = data.get("video_id", transcript_path.stem)
        chunks   = self.chunk_transcript(data)

        if not chunks:
            return 0

        # Filtra chunks ja indexados
        new_chunks = [c for c in chunks if c["id"] not in indexed_ids]
        if not new_chunks:
            return 0

        # Calcula scores e categorias para cada chunk (filtro de relevancia)
        for chunk in new_chunks:
            chunk["score"]      = score_chunk(chunk["text"])
            chunk["categories"] = ",".join(classify_categories(chunk["text"])) or "none"

        # Gera embeddings em batch
        texts      = [c["text"] for c in new_chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=False).tolist()

        # ── Insere na colecao GERAL ──────────────────────────────────────
        added          = 0
        profitable_buf = []  # chunks de alto score para o cerebro lucrativo

        for i in range(0, len(new_chunks), BATCH_SIZE):
            batch       = new_chunks[i:i + BATCH_SIZE]
            batch_emb   = embeddings[i:i + BATCH_SIZE]
            batch_ids   = [c["id"] for c in batch]
            batch_texts = [c["text"] for c in batch]
            batch_meta  = [{
                "video_id":    c["video_id"],
                "video_title": c["video_title"],
                "video_url":   c["video_url"],
                "timestamp":   c["timestamp"],
                "timestamp_s": c["timestamp_s"],
                "upload_date": c["upload_date"],
                "channel":     c["channel"],
                "score":       c["score"],
                "categories":  c["categories"],
            } for c in batch]

            self.collection.add(
                ids=batch_ids,
                embeddings=batch_emb,
                documents=batch_texts,
                metadatas=batch_meta,
            )
            added += len(batch)

            # Separa chunks lucrativos para segundo indice
            for j, chunk in enumerate(batch):
                if chunk["score"] >= MIN_SCORE_PROFITABLE:
                    profitable_buf.append({
                        "id":   chunk["id"] + "_p",  # sufixo para evitar conflito de ID
                        "text": chunk["text"],
                        "emb":  batch_emb[j],
                        "meta": batch_meta[j],
                    })

        # ── Insere na colecao LUCRATIVA ──────────────────────────────────
        if profitable_buf:
            for i in range(0, len(profitable_buf), BATCH_SIZE):
                pbatch = profitable_buf[i:i + BATCH_SIZE]
                self.profitable_collection.add(
                    ids=[p["id"] for p in pbatch],
                    embeddings=[p["emb"] for p in pbatch],
                    documents=[p["text"] for p in pbatch],
                    metadatas=[p["meta"] for p in pbatch],
                )

        return added

    def run(self, rebuild: bool = False) -> dict:
        """
        Indexa todas as transcrições disponíveis.

        Args:
            rebuild: Se True, recria o índice do zero (apaga dados anteriores)
        """
        print("=" * 60)
        print("ICT BRAIN — INDEXADOR DE TRANSCRIÇÕES")
        print("=" * 60)

        transcript_files = list(TRANSCRIPTS_DIR.glob("*.json"))
        if not transcript_files:
            print(f"[Indexer] ⚠ Nenhuma transcrição encontrada em {TRANSCRIPTS_DIR}")
            print("[Indexer] Execute primeiro: python -m core.ict_brain.extractor")
            return {"indexed": 0, "skipped": 0, "errors": 0, "total_chunks": 0}

        print(f"[Indexer] {len(transcript_files)} transcrições para indexar")

        # Se rebuild, apaga coleções existentes
        if rebuild:
            print("[Indexer] Modo REBUILD: apagando índice existente...")
            try:
                try:
                    self.client.delete_collection(COLLECTION_NAME)
                except Exception:
                    pass
                try:
                    self.client.delete_collection(PROFITABLE_COLLECTION)
                except Exception:
                    pass
                self._collection = None
                self._profitable_collection = None
                print("[Indexer] Índice apagado ✓")
            except Exception as e:
                print(f"[Indexer] Aviso ao apagar: {e}")

        indexed_ids = self._get_indexed_ids()
        print(f"[Indexer] Chunks já no índice: {len(indexed_ids)}")

        total_added = 0
        skipped     = 0
        errors      = 0
        log_entries = []

        for i, path in enumerate(transcript_files, 1):
            try:
                added = self.index_transcript(path, indexed_ids)
                if added > 0:
                    total_added += added
                    indexed_ids.update([f"{path.stem}_{j:04d}" for j in range(added)])
                    status = f"✓ +{added} chunks"
                else:
                    skipped += 1
                    status = "→ já indexado"

                if i % 20 == 0 or i == len(transcript_files):
                    print(f"  [{i:4d}/{len(transcript_files)}] {path.stem[:40]} | {status}")

                log_entries.append({"file": path.stem, "chunks_added": added, "status": "ok"})

            except Exception as e:
                errors += 1
                print(f"  [{i:4d}/{len(transcript_files)}] ⚠ Erro em {path.name}: {e}")
                log_entries.append({"file": path.stem, "chunks_added": 0, "status": str(e)})

        total_in_db = self.collection.count()

        # Salva log de indexação
        log = {
            "indexed_at":   datetime.now().isoformat(),
            "total_files":  len(transcript_files),
            "new_chunks":   total_added,
            "total_in_db":  total_in_db,
            "skipped":      skipped,
            "errors":       errors,
            "entries":      log_entries,
        }
        with open(INDEX_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

        print(f"\n{'=' * 60}")
        print(f"INDEXAÇÃO CONCLUÍDA")
        print(f"  Novos chunks adicionados: {total_added}")
        print(f"  Total no banco vetorial:  {total_in_db}")
        print(f"  Arquivos pulados (já indexados): {skipped}")
        print(f"  Erros: {errors}")
        print(f"{'=' * 60}\n")

        return {"indexed": total_added, "skipped": skipped, "errors": errors, "total_chunks": total_in_db}


# ─── Execução standalone ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ICT Brain Indexer")
    parser.add_argument("--rebuild", action="store_true", help="Recria o índice do zero")
    args = parser.parse_args()

    indexer = ICTIndexer()
    indexer.run(rebuild=args.rebuild)
