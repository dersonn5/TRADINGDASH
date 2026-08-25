"""
ICT Brain — Extractor
=====================
Responsável por:
  1. Listar todos os vídeos do canal ICT usando yt-dlp
  2. Baixar transcrições via youtube-transcript-api (sem autenticar)
  3. Salvar em JSON incremental em data/ict_brain/transcripts/

Uso standalone:
    python -m core.ict_brain.extractor
"""

import json
import re
import sys
import io
import time
from pathlib import Path
from datetime import datetime

# Forçar UTF-8 no terminal Windows (evita UnicodeEncodeError com símbolos especiais)
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer') and sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ─── Configurações ──────────────────────────────────────────────────────────

# Canais do ICT — usamos /videos para pegar direto os uploads
ICT_CHANNEL_URLS = [
    "https://www.youtube.com/@InnerCircleTrader/videos",
    "https://www.youtube.com/@ICTMentorship2022/videos",
]

# Diretório de saída
BASE_DIR = Path(__file__).resolve().parents[2]  # raiz do TRADING AI
TRANSCRIPTS_DIR = BASE_DIR / "data" / "ict_brain" / "transcripts"
METADATA_FILE   = BASE_DIR / "data" / "ict_brain" / "videos_metadata.json"
PROGRESS_FILE   = BASE_DIR / "data" / "ict_brain" / "extraction_progress.json"

# Idiomas preferidos para transcrição (ICT fala em inglês)
PREFERRED_LANGS = ["en", "en-US", "en-GB"]

# Delay entre requisições (emula comportamento humano com variação aleatória para evitar bloqueios)
import random as _random
def get_human_delay():
    return _random.uniform(35.0, 65.0)


class ICTExtractor:
    """Extrai e persiste transcrições dos vídeos do ICT."""

    def __init__(self, transcripts_dir: Path = None):
        self.transcripts_dir = transcripts_dir or TRANSCRIPTS_DIR
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Carrega progresso anterior (extração incremental)
        self.progress = self._load_progress()

    # ─── Progresso ──────────────────────────────────────────────────────────

    def _load_progress(self) -> dict:
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Migração: garante a chave 'no_transcript' em arquivos antigos
            if "no_transcript" not in data:
                data["no_transcript"] = []
            return data
        return {"extracted": [], "failed": [], "no_transcript": [], "last_run": None}

    def _save_progress(self):
        self.progress["last_run"] = datetime.now().isoformat()
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    # ─── Listagem de vídeos ─────────────────────────────────────────────────

    def list_channel_videos(self, channel_url: str) -> list[dict]:
        """Usa yt-dlp para listar todos os vídeos do canal sem baixar mídia."""
        print(f"\n[Extractor] Listando vídeos de: {channel_url}")

        # Estratégia: --flat-playlist + --print para obter IDs e títulos linha a linha
        cmd_ids = [
            sys.executable, "-m", "yt_dlp",
            "--flat-playlist",
            "--print", "%(id)s|||%(title)s|||%(duration)s|||%(upload_date)s",
            "--no-warnings",
            "--quiet",
            "--ignore-errors",
            channel_url
        ]
        try:
            result = subprocess.run(
                cmd_ids,
                capture_output=True,
                text=True,
                timeout=180,
                encoding="utf-8",
                errors="replace"
            )

            videos = []
            seen = set()
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or "|||" not in line:
                    continue
                parts = line.split("|||", 3)
                if len(parts) < 2:
                    continue
                vid_id    = parts[0].strip()
                title     = parts[1].strip() if len(parts) > 1 else "Unknown"
                duration  = parts[2].strip() if len(parts) > 2 else None
                upload_dt = parts[3].strip() if len(parts) > 3 else None

                # Filtra entradas que não são IDs válidos de vídeo (11 chars alfanuméricos)
                import re as _re
                if not _re.match(r'^[A-Za-z0-9_\-]{11}$', vid_id):
                    continue
                if vid_id in seen:
                    continue
                seen.add(vid_id)

                videos.append({
                    "id":          vid_id,
                    "title":       title,
                    "url":         f"https://www.youtube.com/watch?v={vid_id}",
                    "duration":    duration,
                    "upload_date": upload_dt,
                    "channel":     channel_url,
                })

            if not videos and result.returncode != 0:
                print(f"[Extractor] ⚠ yt-dlp stderr: {result.stderr[:300]}")

            print(f"[Extractor] → {len(videos)} vídeos encontrados")
            return videos

        except subprocess.TimeoutExpired:
            print("[Extractor] ⚠ Timeout ao listar canal")
            return []
        except Exception as e:
            print(f"[Extractor] ⚠ Erro inesperado: {e}")
            return []

    def list_all_videos(self) -> list[dict]:
        """Lista vídeos de todos os canais ICT configurados."""
        all_videos = []
        seen_ids = set()
        for url in ICT_CHANNEL_URLS:
            videos = self.list_channel_videos(url)
            for v in videos:
                if v["id"] not in seen_ids:
                    seen_ids.add(v["id"])
                    all_videos.append(v)

        # Salva metadados
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(all_videos, f, ensure_ascii=False, indent=2)
        print(f"\n[Extractor] Total único: {len(all_videos)} vídeos → {METADATA_FILE.name}")
        return all_videos

    # ─── Transcrição ────────────────────────────────────────────────────────

    # Nomes de exceção permanentes da youtube-transcript-api
    # (importados dinamicamente para não falhar se a lib não estiver instalada)
    _PERMANENT_EXCEPTIONS = (
        "TranscriptsDisabled",
        "NoTranscriptFound",
        "VideoUnavailable",
        "NotTranslatable",
        "NoTranscriptAvailable",
    )

    def get_transcript(self, video_id: str) -> tuple[list[dict] | None, str | None]:
        """Baixa a transcrição de um vídeo.

        Retorna:
            (segments, None)            — sucesso
            (None, 'no_transcript')     — vídeo sem legenda (falha PERMANENTE)
            (None, 'failed')            — erro de rede / bloqueio (falha TEMPORÁRIA)

        Compatível com youtube-transcript-api >= 1.0 (nova API com instância).
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            import requests
            import http.cookiejar
        except ImportError:
            print("[Extractor] ⚠ youtube-transcript-api ou requests não instalado!")
            return None, "failed"

        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Referer": "https://www.youtube.com/"
            })

            cookies_file = BASE_DIR / "youtube_cookies.txt"
            if cookies_file.exists():
                try:
                    cj = http.cookiejar.MozillaCookieJar(str(cookies_file))
                    cj.load(ignore_discard=True, ignore_expires=True)
                    session.cookies = cj
                except Exception as e:
                    print(f"[Extractor] ⚠ Erro ao carregar cookies do YouTube: {e}")

            api = YouTubeTranscriptApi(http_client=session)

            # Tenta via list() para escolher idioma
            try:
                transcript_list = api.list(video_id)
                transcript = None

                # Prefere manual (melhor qualidade)
                try:
                    transcript = transcript_list.find_manually_created_transcript(PREFERRED_LANGS)
                except Exception:
                    pass

                # Fallback: gerado automaticamente
                if transcript is None:
                    try:
                        transcript = transcript_list.find_generated_transcript(PREFERRED_LANGS)
                    except Exception:
                        pass

                # Último recurso: qualquer disponível
                if transcript is None:
                    for t in transcript_list:
                        transcript = t
                        break

                if transcript is None:
                    return None, "no_transcript"

                raw = transcript.fetch()

            except Exception as inner_exc:
                exc_name = type(inner_exc).__name__
                if exc_name in self._PERMANENT_EXCEPTIONS:
                    # Falha permanente confirmada: vídeo não tem legenda
                    return None, "no_transcript"
                # Tenta fallback direto antes de desistir
                try:
                    raw = api.fetch(video_id)
                except Exception as fetch_exc:
                    fetch_name = type(fetch_exc).__name__
                    if fetch_name in self._PERMANENT_EXCEPTIONS:
                        return None, "no_transcript"
                    return None, "failed"

            # Normaliza para lista de dicts
            segments = []
            for item in raw:
                if hasattr(item, 'text'):
                    # Objeto FetchedTranscriptSnippet (v1.x)
                    segments.append({
                        "text":     getattr(item, 'text', ''),
                        "start":    getattr(item, 'start', 0),
                        "duration": getattr(item, 'duration', 0),
                    })
                elif isinstance(item, dict):
                    segments.append(item)

            return (segments, None) if segments else (None, "no_transcript")

        except Exception as outer_exc:
            exc_name = type(outer_exc).__name__
            if exc_name in self._PERMANENT_EXCEPTIONS:
                return None, "no_transcript"
            return None, "failed"

    def extract_video(self, video: dict) -> bool:
        """Extrai e salva a transcrição de um único vídeo."""
        video_id = video["id"]

        # Já extraído anteriormente?
        if video_id in self.progress["extracted"]:
            return True

        # Já confirmado sem transcrição (falha permanente)?
        if video_id in self.progress.get("no_transcript", []):
            return False

        transcript, fail_reason = self.get_transcript(video_id)
        if transcript is None:
            if fail_reason == "no_transcript":
                # Falha permanente: não tem legenda, não adianta retentar
                if video_id not in self.progress.get("no_transcript", []):
                    self.progress.setdefault("no_transcript", []).append(video_id)
                # Remove de 'failed' se estava lá de execuções antigas
                if video_id in self.progress["failed"]:
                    self.progress["failed"].remove(video_id)
            else:
                # Falha temporária: rede, bloqueio, etc. — pode retentar depois
                if video_id not in self.progress["failed"]:
                    self.progress["failed"].append(video_id)
            return False

        # Concatena os segmentos em texto limpo com timestamps
        segments = []
        full_text_parts = []
        for seg in transcript:
            # Compatibilidade com diferentes versões da API (dict ou objeto)
            if isinstance(seg, dict):
                text  = seg.get("text", "")
                start = seg.get("start", 0)
                dur   = seg.get("duration", 0)
            else:
                text  = getattr(seg, "text", "")
                start = getattr(seg, "start", 0)
                dur   = getattr(seg, "duration", 0)

            text = text.strip().replace("\n", " ")
            if text:
                segments.append({
                    "text":     text,
                    "start":    round(start, 1),
                    "duration": round(dur, 1),
                })
                full_text_parts.append(text)

        # Salva arquivo JSON da transcrição
        out = {
            "video_id":    video_id,
            "title":       video.get("title", "Unknown"),
            "url":         video.get("url", f"https://www.youtube.com/watch?v={video_id}"),
            "channel":     video.get("channel", ""),
            "upload_date": video.get("upload_date", ""),
            "duration":    video.get("duration"),
            "segments":    segments,
            "full_text":   " ".join(full_text_parts),
            "extracted_at": datetime.now().isoformat(),
        }

        out_path = self.transcripts_dir / f"{video_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        self.progress["extracted"].append(video_id)
        return True

    # ─── Extração em lote ───────────────────────────────────────────────────

    def run(self, max_videos: int = None, resume: bool = True) -> dict:
        """
        Pipeline completo: lista vídeos → extrai transcrições.

        Args:
            max_videos: Limitar quantos vídeos processar (None = todos)
            resume: Se True, pula vídeos já extraídos

        Returns:
            Resumo com contagens
        """
        print("=" * 60)
        print("ICT BRAIN — EXTRATOR DE TRANSCRIÇÕES YOUTUBE")
        print("=" * 60)

        # 1. Listar vídeos (ou usar cache)
        if METADATA_FILE.exists() and resume:
            print(f"\n[Extractor] Usando cache de vídeos: {METADATA_FILE.name}")
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                all_videos = json.load(f)
        else:
            all_videos = self.list_all_videos()

        if not all_videos:
            print("[Extractor] ⚠ Nenhum vídeo encontrado. Verifique URLs dos canais.")
            return {"total": 0, "extracted": 0, "failed": 0, "skipped": 0}

        # 2. Filtrar já extraídos
        already_done = set(self.progress["extracted"])
        pending = [v for v in all_videos if v["id"] not in already_done]

        if max_videos:
            pending = pending[:max_videos]

        skipped = len(all_videos) - len(pending) - len([v for v in all_videos if v["id"] in set(self.progress["failed"])])

        no_transcript_ids = set(self.progress.get("no_transcript", []))
        pending = [v for v in pending if v["id"] not in no_transcript_ids]

        print(f"\n[Extractor] Total: {len(all_videos)} | Pendentes: {len(pending)} | Ja extraidos: {len(already_done)} | Sem legenda (skip): {len(no_transcript_ids)}")
        print(f"[Extractor] Iniciando extracao...\n")

        ok = 0
        fail = 0

        for i, video in enumerate(pending, 1):
            title_short = video["title"][:60]
            success = self.extract_video(video)

            status = "[OK]  " if success else "[FAIL]"
            print(f"  [{i:4d}/{len(pending)}] {status} {title_short}")

            if success:
                ok += 1
                # Salva o progresso a cada extração bem-sucedida para garantir persistência imediata
                self._save_progress()

                # Cooldown a cada 5 extrações com sucesso para resfriar a sessão
                if ok % 5 == 0 and i < len(pending):
                    cooldown_time = _random.uniform(120.0, 240.0)
                    print(f"\n[Extractor] ⏳ Pausa de resfriamento (cooldown) de {cooldown_time:.1f}s para evitar bloqueio do YouTube...")
                    time.sleep(cooldown_time)
            else:
                fail += 1

            time.sleep(get_human_delay())

        self._save_progress()

        summary = {
            "total":     len(all_videos),
            "extracted": len(self.progress["extracted"]),
            "failed":    fail,
            "skipped":   skipped,
            "new_this_run": ok,
        }

        print(f"\n{'=' * 60}")
        print(f"EXTRAÇÃO CONCLUÍDA")
        print(f"  Total de vídeos: {summary['total']}")
        print(f"  Extraídos (total): {summary['extracted']}")
        print(f"  Novos nesta execução: {summary['new_this_run']}")
        print(f"  Falhas: {fail}")
        print(f"{'=' * 60}\n")

        return summary


# ─── Execução standalone ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ICT Brain Extractor")
    parser.add_argument("--max",    type=int, default=None, help="Máximo de vídeos a processar")
    parser.add_argument("--fresh",  action="store_true",    help="Ignorar cache e relistar canal")
    parser.add_argument("--list-only", action="store_true", help="Apenas lista vídeos, sem extrair")
    args = parser.parse_args()

    extractor = ICTExtractor()

    if args.list_only:
        videos = extractor.list_all_videos()
        print(f"\nTotal: {len(videos)} vídeos encontrados.")
    else:
        extractor.run(max_videos=args.max, resume=not args.fresh)
