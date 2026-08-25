"""
ICT Brain — Distiller
=====================
Uses Gemini/Groq API to distill technical chunks of ICT transcripts
into STRUCTURED OPERATIONAL RULES in native English.

Flow per category:
  1. Reads all relevant chunks of a category from ChromaDB
  2. Groups in batches of ~8 chunks (manageable context for LLM)
  3. LLM distills into actionable rules + entry/exit conditions
  4. Saves as Markdown in Obsidian (01_Regras_ICT/)

Standalone usage:
    python -m core.ict_brain.distiller                    # all categories
    python -m core.ict_brain.distiller --cat fair_value_gap
    python -m core.ict_brain.distiller --rebuild          # overwrite everything
"""

import json
import time
from pathlib import Path
from datetime import datetime

from core.ict_brain.taxonomy import CATEGORIES, score_chunk, classify_categories

# ─── Configurações ──────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).resolve().parents[2]
TRANSCRIPTS_DIR = BASE_DIR / "data" / "ict_brain" / "transcripts"
DISTILLED_DIR   = BASE_DIR / "data" / "ict_brain" / "distilled"
OBSIDIAN_ICT    = BASE_DIR / "Cerebro_Obsidian" / "Trading AI" / "B03 Regras ICT"

COLLECTION_NAME         = "ict_brain"
PROFITABLE_COLLECTION   = "ict_profitable_brain"

# Threshold mínimo de score para considerar um chunk "lucrativo"
MIN_SCORE_PROFITABLE = 40

# Chunks por lote enviado ao LLM.
# Local (Ollama) não cobra token → lotes grandes = menos chamadas.
CHUNKS_PER_BATCH = 30

# Delay entre lotes. 0 no local; cloud usa backoff próprio no _call_llm.
DELAY_API = 0.0

# Número máximo de chunks por categoria para destilar.
MAX_CHUNKS_PER_CATEGORY = 90


class ICTDistiller:
    """Distills technical ICT chunks into operational rules in native English.

    Motor de LLM (ordem de prioridade):
      1. Ollama LOCAL (qwen2.5:7b-instruct na GPU) — principal. Sem rate-limit, sem custo.
      2. Gemini (gemini-2.0-flash) — fallback se Ollama indisponível.
      3. Groq (llama-3.3-70b) — último fallback.
    """

    # Modelo Groq preferido — 128K contexto, excelente para resumo de transcricoes
    GROQ_MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        import config
        DISTILLED_DIR.mkdir(parents=True, exist_ok=True)
        OBSIDIAN_ICT.mkdir(parents=True, exist_ok=True)
        self._gemini_client = None
        self._groq_client   = None
        # Motor inicial: local se habilitado, senão cai pra cloud.
        self._active_llm    = "ollama" if getattr(config, "USE_LOCAL_LLM", True) else "groq"
        type(self)._gemini_exhausted = True
        self._ollama_ok     = None  # cache de health-check (None=não testado)

    # ─── Clientes LLM ────────────────────────────────────────────────────

    @property
    def gemini_client(self):
        if self._gemini_client is None:
            try:
                import config
                from google import genai
                self._gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
            except Exception as e:
                raise RuntimeError(f"Gemini nao configurado: {e}")
        return self._gemini_client

    @property
    def groq_client(self):
        if self._groq_client is None:
            try:
                import config
                from groq import Groq
                if not config.GROQ_API_KEY:
                    raise RuntimeError("GROQ_API_KEY nao configurada no .env")
                self._groq_client = Groq(api_key=config.GROQ_API_KEY)
            except ImportError:
                raise RuntimeError("groq nao instalado. Execute: pip install groq")
        return self._groq_client

    def _ollama_available(self) -> bool:
        """Health-check do servidor Ollama local (cacheado)."""
        if self._ollama_ok is not None:
            return self._ollama_ok
        try:
            import config, requests
            r = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=5)
            self._ollama_ok = (r.status_code == 200)
        except Exception as e:
            print(f"[Distiller]   [Ollama] indisponivel: {str(e)[:100]}")
            self._ollama_ok = False
        return self._ollama_ok

    def _call_ollama(self, prompt: str, model: str = None) -> str:
        """Chama Ollama local (GPU). Sem rate-limit, sem custo, sem sleeps."""
        import config, requests
        mdl = model or config.OLLAMA_MODEL
        resp = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model":   mdl,
                "prompt":  prompt,
                "stream":  False,
                "options": {"temperature": 0.2, "num_ctx": 8192},
            },
            timeout=config.OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        text = (resp.json().get("response") or "").strip()
        print(f"[Distiller]   [Ollama/{mdl}] OK ({len(text)} chars)")
        return text

    def _call_groq(self, prompt: str, max_retries: int = 5) -> str:
        """Chama Groq (Llama 3.3 70B) — 128K contexto, free tier generoso, LPU ultra-rapido."""
        import time
        import re as _re

        # Delay de cortesia preventiva (15s para llama-3.3-70b-versatile)
        time.sleep(15.0)

        for attempt in range(max_retries):
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=4096,
                )
                text = response.choices[0].message.content or ""
                print(f"[Distiller]   [Groq/{self.GROQ_MODEL[:16]}] OK ({len(text)} chars)")
                return text.strip()
            except Exception as e:
                err = str(e)
                if "rate_limit" in err.lower() or "429" in err:
                    # Extrai tempo de espera sugerido pelo rate limit do Groq
                    wait_s = 20
                    m = _re.search(r"please try again in (\d+\.?\d*)s", err.lower())
                    if m:
                        wait_s = int(float(m.group(1))) + 5
                    elif "retry-after" in err.lower():
                        # Tentativa de extração genérica de tempo
                        m2 = _re.search(r"retry\-after[^\d]*(\d+)", err.lower())
                        if m2:
                            wait_s = int(m2.group(1)) + 5
                    
                    print(f"[Distiller]   [Groq] Rate limit atingido. Aguardando {wait_s}s para tentar novamente (Tentativa {attempt+1}/{max_retries})...")
                    time.sleep(wait_s)
                else:
                    print(f"[Distiller]   [Groq] Erro inesperado: {err[:150]}")
                    raise e
        raise RuntimeError("Groq falhou após todas as tentativas de retry")

    def _call_gemini_direct(self, prompt: str) -> str:
        """Chama Gemini diretamente (sem fallback interno)."""
        response = self.gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text.strip()

    def _call_llm(self, prompt: str, max_retries: int = 5, ollama_model: str = None) -> str:
        """
        Chamadas resilientes ao LLM. Ordem de prioridade:
          1. Ollama LOCAL (sem rate-limit, sem custo) — motor principal.
          2. Gemini 2.0 Flash — fallback.
          3. Groq llama-3.3-70b — último fallback.
        Cloud mantém backoff em 429; local não dorme.

        ollama_model: força um modelo local específico (ex: 14b na consolidação).
        """
        import time
        import config

        # ─── Motor principal: Ollama local ──────────────────────────────
        if self._active_llm == "ollama":
            if self._ollama_available():
                try:
                    return self._call_ollama(prompt, model=ollama_model)
                except Exception as e:
                    print(f"[Distiller]   [Ollama] erro na geracao: {str(e)[:150]}. Tentando cloud...")
            else:
                print("[Distiller]   [Ollama] servidor offline. Caindo para cloud (Groq/Gemini)...")
            # Fallback: escolhe cloud disponível
            self._active_llm = "gemini" if config.GEMINI_API_KEY and not getattr(type(self), "_gemini_exhausted", False) else "groq"

        # ─── Cloud (fallback) ───────────────────────────────────────────
        # Delay preventivo só no caminho cloud
        time.sleep(1.0 if getattr(type(self), "_gemini_exhausted", False) else 6.0)

        # Se Gemini já está marcado como exaurido de quota, força Groq imediatamente
        if getattr(type(self), "_gemini_exhausted", False) and self._active_llm == "gemini":
            self._active_llm = "groq"

        for attempt in range(max_retries):
            try:
                if self._active_llm == "gemini":
                    # Tenta Gemini
                    response = self.gemini_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt,
                    )
                    text = response.text.strip()
                    if text:
                        return text
                else:
                    # Tenta Groq
                    # Delay menor para openai/gpt-oss-120b de alta taxa (1s vs 15s)
                    time.sleep(1.0 if self.GROQ_MODEL == "openai/gpt-oss-120b" else 15.0)
                    return self._call_groq(prompt)

            except Exception as e:
                err_str = str(e)
                is_429 = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate_limit" in err_str.lower()
                is_quota = "quota" in err_str.lower() or "exhausted" in err_str.lower() or "billing" in err_str.lower()
                
                print(f"[Distiller]   [Erro LLM - Tentativa {attempt+1}/{max_retries}] Modelo: {self._active_llm} | Erro: {err_str[:150]}")
                
                if is_429:
                    if self._active_llm == "gemini":
                        if config.GROQ_API_KEY:
                            if is_quota:
                                print(f"[Distiller]   Gemini sem quota / limite excedido. Alternando PERMANENTEMENTE para Groq...")
                                # Desativa gemini para esta instância
                                self._active_llm = "groq"
                                # Sobrescreve a propriedade para que futuras chamadas usem apenas Groq
                                type(self)._gemini_exhausted = True
                            else:
                                print(f"[Distiller]   Alternando temporariamente para Groq devido a 429 no Gemini...")
                                self._active_llm = "groq"
                        else:
                            print(f"[Distiller]   Aguardando 45s de cooldown para liberar limite do Gemini...")
                            time.sleep(45)
                    else:
                        print(f"[Distiller]   Aguardando 60s de cooldown para liberar limite do Groq...")
                        time.sleep(60)
                        # Só retorna ao Gemini se ele não estiver com a quota esgotada
                        if not getattr(self, "_gemini_exhausted", False):
                            self._active_llm = "gemini"
                else:
                    # Erro genérico (ex: rede) - aguarda e retenta
                    time.sleep(10)
        
        # Se chegou aqui, falhou. Tenta um último fallback forçado no Groq se tiver chave
        if config.GROQ_API_KEY and self._active_llm == "gemini":
            try:
                print(f"[Distiller]   [Ultimo Recurso] Chamando Groq...")
                self._active_llm = "groq"
                return self._call_groq(prompt)
            except Exception:
                pass

        return ""

        print(f"[Distiller]   Falha apos {max_retries} tentativas. Pulando lote.")
        return ""

    # ─── Leitura de chunks das transcrições ──────────────────────────────

    def load_chunks_for_category(self, cat_id: str) -> list[dict]:
        """
        Carrega todos os chunks relevantes para uma categoria,
        lendo diretamente dos JSONs de transcrição (sem precisar do ChromaDB).
        """
        from core.ict_brain.indexer import ICTIndexer

        cat = CATEGORIES[cat_id]
        cat_keywords = cat["keywords"]
        relevant_chunks = []

        transcript_files = list(TRANSCRIPTS_DIR.glob("*.json"))
        if not transcript_files:
            return []

        indexer = ICTIndexer()

        for path in transcript_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                chunks = indexer.chunk_transcript(data)
                for chunk in chunks:
                    text = chunk["text"].lower()
                    score = score_chunk(chunk["text"])

                    # Verifica se pertence à categoria e tem score mínimo
                    is_category = any(kw in text for kw in cat_keywords)
                    if is_category and score >= MIN_SCORE_PROFITABLE:
                        relevant_chunks.append({
                            "text":        chunk["text"],
                            "score":       score,
                            "video_title": chunk["video_title"],
                            "timestamp":   chunk["timestamp"],
                            "video_url":   chunk["video_url"],
                        })
            except Exception as e:
                print(f"[Distiller] Erro ao ler {path.name}: {e}")

        # Ordena por score descendente e limita
        relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
        return relevant_chunks[:MAX_CHUNKS_PER_CATEGORY]

    def load_all_chunks_by_category(self) -> dict[str, list[dict]]:
        """
        SINGLE-PASS: lê e chunka os 582 transcripts UMA vez, classificando
        cada chunk em todas as categorias a que pertence.

        Substitui N chamadas a load_chunks_for_category (que reliam todos os
        arquivos por categoria → ~5.238 releituras). Aqui: 1 leitura por arquivo.

        Retorna: {cat_id: [chunk, ...]} já ordenado por score e limitado.
        """
        from core.ict_brain.indexer import ICTIndexer

        buckets: dict[str, list[dict]] = {cid: [] for cid in CATEGORIES}
        transcript_files = list(TRANSCRIPTS_DIR.glob("*.json"))
        if not transcript_files:
            return buckets

        indexer = ICTIndexer()
        print(f"[Distiller] Single-pass: lendo {len(transcript_files)} transcripts UMA vez...")

        for path in transcript_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for chunk in indexer.chunk_transcript(data):
                    score = score_chunk(chunk["text"])
                    if score < MIN_SCORE_PROFITABLE:
                        continue
                    cats = classify_categories(chunk["text"])
                    if not cats:
                        continue
                    entry = {
                        "text":        chunk["text"],
                        "score":       score,
                        "video_title": chunk["video_title"],
                        "timestamp":   chunk["timestamp"],
                        "video_url":   chunk["video_url"],
                    }
                    for cid in cats:
                        if cid in buckets:
                            buckets[cid].append(entry)
            except Exception as e:
                print(f"[Distiller] Erro ao ler {path.name}: {e}")

        # Ordena por score e limita cada categoria
        for cid in buckets:
            buckets[cid].sort(key=lambda x: x["score"], reverse=True)
            buckets[cid] = buckets[cid][:MAX_CHUNKS_PER_CATEGORY]
            print(f"[Distiller]   {cid}: {len(buckets[cid])} chunks")

        return buckets

    # ─── Prompt de destilação ─────────────────────────────────────────────

    def _build_distill_prompt(self, category: dict, chunks: list[dict], batch_num: int, total_batches: int) -> str:
        """Builds the distillation prompt for a batch of chunks in native English."""
        trechos_text = ""
        for i, chunk in enumerate(chunks, 1):
            trechos_text += (
                f"\n[Excerpt {i} — {chunk['video_title']} @ {chunk['timestamp']}]\n"
                f"{chunk['text']}\n"
            )

        return f"""You are an expert in the ICT (Inner Circle Trader) method by Michael J. Huddleston.

Below are {len(chunks)} LITERAL transcript excerpts from ICT's YouTube videos on the topic: **{category['nome']}**.

GOAL: Extract ONLY operational trading rules that are SPECIFICALLY about **{category['nome']}**.

STRICT RULES — follow exactly:
1. STAY ON TOPIC. If an excerpt talks about a DIFFERENT concept (not {category['nome']}), IGNORE it. Do not create sections for other concepts.
2. Base every rule EXCLUSIVELY on what the excerpts literally say. NEVER invent, assume, or add outside knowledge.
3. If the excerpts are too vague to yield a concrete rule, output fewer rules — do NOT pad.
4. Use the correct meaning of each label:
   - "Entry conditions" = what must be true to ENTER a trade.
   - "Invalidation" = the price condition that proves the setup WRONG (where the idea fails / stop-loss logic). NOT the profit target.
   - "Targets / objectives" = where price is expected to go (draw on liquidity). Keep these separate from invalidation.
5. Use standard ICT terminology exactly (FVG, OB, MSS, BOS, CHoCH, BSL/SSL, OTE, PD array).

OUTPUT — raw GitHub Markdown ONLY:
- Do NOT wrap the answer in code fences (no ``` of any kind).
- Do NOT invent a "Sources" section, citations, anchor links, or excerpt numbers — sources are added later automatically.
- No preamble, no closing remarks, no "this document..." commentary. Output ONLY the rules.
- Use ### subheadings and bullet lists.

---
ICT EXCERPTS:
{trechos_text}
---

Distilled rules for **{category['nome']}** (batch {batch_num}/{total_batches}):"""

    @staticmethod
    def _sanitize_markdown(text: str) -> str:
        """Defesa pós-LLM: remove code fences que envolvem o doc inteiro e
        remarks finais do tipo 'This document...'."""
        import re
        # Prompt proíbe fences → qualquer linha que seja só ```/```lang é lixo de wrap.
        lines = [ln for ln in text.strip().splitlines()
                 if not re.match(r"^\s*```[a-zA-Z]*\s*$", ln)]
        # Remove comentário-meta final ("This consolidated document ...", "Note: ...")
        while lines and re.match(r"^\s*(this (consolidated |merged )?document|the above|note:)\b",
                                 lines[-1].strip(), re.IGNORECASE):
            lines.pop()
        return "\n".join(lines).strip()

    # ─── Destilação por categoria ─────────────────────────────────────────

    def distill_category(self, cat_id: str, rebuild: bool = False, chunks: list[dict] = None) -> str | None:
        """
        Destila todos os chunks de uma categoria em um arquivo MD.
        Retorna o path do arquivo gerado, ou None se falhou.

        chunks: se fornecido (single-pass), evita reler todos os transcripts.
        """
        cat = CATEGORIES[cat_id]
        output_file = OBSIDIAN_ICT / cat["arquivo"]

        if output_file.exists() and not rebuild:
            print(f"[Distiller] Ja existe: {cat['arquivo']} (use --rebuild para sobrescrever)")
            return str(output_file)

        print(f"\n[Distiller] Destilando: {cat['nome']}")

        # 1. Carregar chunks relevantes (usa pré-carregados se disponíveis)
        if chunks is None:
            chunks = self.load_chunks_for_category(cat_id)
        if not chunks:
            print(f"[Distiller]   ! Nenhum chunk relevante encontrado para {cat_id}")
            return None

        print(f"[Distiller]   Chunks relevantes: {len(chunks)}")

        # 2. Processar em lotes
        batches = [chunks[i:i + CHUNKS_PER_BATCH] for i in range(0, len(chunks), CHUNKS_PER_BATCH)]
        all_sections = []

        for batch_num, batch in enumerate(batches, 1):
            print(f"[Distiller]   Lote {batch_num}/{len(batches)} ({len(batch)} chunks)...")
            prompt = self._build_distill_prompt(cat, batch, batch_num, len(batches))
            result = self._call_llm(prompt)
            if result:
                all_sections.append(result)
            time.sleep(DELAY_API)

        if not all_sections:
            print(f"[Distiller]   ! LLM nao retornou conteudo para {cat_id}")
            return None

        # 3. Se houver múltiplos lotes, consolida com um prompt final
        final_content = ""
        if len(all_sections) > 1:
            print(f"[Distiller]   Consolidando {len(all_sections)} lotes...")
            consolidation_prompt = f"""You are an expert in the ICT (Inner Circle Trader) method.

Below are {len(all_sections)} draft sections of operational rules about **{cat['nome']}**, distilled from ICT's YouTube transcripts.

Merge them into ONE clean, well-organized Markdown document about **{cat['nome']}**.

STRICT RULES:
1. STAY ON TOPIC ({cat['nome']}). DELETE any rule that is actually about a different concept.
2. Eliminate duplicates and merge overlapping rules. Keep only concrete, actionable content.
3. Keep these as DISTINCT sections (do not mix them up):
   - ## Entry Conditions  (what must be true to enter)
   - ## Invalidation  (the price condition that proves the setup wrong / stop logic — NOT the target)
   - ## Targets & Objectives  (draw on liquidity / where price is expected to go)
   - ## Key Concepts  (definitions and mechanics)
4. Use standard ICT terminology exactly.

OUTPUT — raw GitHub Markdown ONLY:
- Do NOT wrap the answer in code fences (no ``` of any kind).
- Do NOT add a "Sources" / citations / anchor-link section — sources are appended automatically later.
- No preamble and no closing commentary (no "this document..." line). Output ONLY the merged rules, starting with a `## ` heading.

---
DRAFT SECTIONS TO MERGE:

{''.join([f"--- DRAFT {i+1} ---\n{s}\n\n" for i, s in enumerate(all_sections)])}
---

Merged document for **{cat['nome']}**:"""

            import config
            final_content = self._call_llm(
                consolidation_prompt,
                ollama_model=getattr(config, "OLLAMA_CONSOLIDATION_MODEL", None),
            )
        else:
            final_content = all_sections[0]

        if not final_content:
            return None

        final_content = self._sanitize_markdown(final_content)

        # 4. Constrói o arquivo MD completo com frontmatter Obsidian
        sources = []
        seen_videos = set()
        for chunk in chunks:
            vid_title = chunk["video_title"]
            if vid_title not in seen_videos:
                seen_videos.add(vid_title)
                ts_seconds = 0
                try:
                    m, s = chunk["timestamp"].split(":")
                    ts_seconds = int(m) * 60 + int(s)
                except Exception:
                    pass
                url = f"{chunk['video_url']}&t={ts_seconds}s" if ts_seconds else chunk["video_url"]
                sources.append(f"- [{vid_title}]({url})")

        sources_section = "\n".join(sources[:20])  # máx 20 fontes
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        markdown = f"""---
tags: [ICT, youtube-distilled, {cat_id}]
distillation_date: {now}
category: {cat['nome']}
total_chunks_analyzed: {len(chunks)}
---

# {cat['nome']}
> Automatically distilled from ICT (Michael J. Huddleston) YouTube transcripts
> Generated on: {now} | Chunks analyzed: {len(chunks)}

## Description
{cat['descricao']}

---

{final_content}

---

## Sources (YouTube Videos)
{sources_section}

---
*Generated by ICT Brain Distiller — Super Agent ICT AI*
*Based on literal transcripts of Michael J. Huddleston*
"""

        # 5. Salva no Obsidian
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

        # Também salva cópia em data/ict_brain/distilled/
        distilled_copy = DISTILLED_DIR / cat["arquivo"]
        with open(distilled_copy, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"[Distiller]   Salvo: {output_file}")
        return str(output_file)

    # ─── Pipeline completo ────────────────────────────────────────────────

    def run(self, cat_ids: list[str] = None, rebuild: bool = False) -> dict:
        """
        Destila todas as categorias (ou as especificadas).

        Args:
            cat_ids:  Lista de IDs de categorias a destilar (None = todas)
            rebuild:  Se True, sobrescreve arquivos existentes

        Returns:
            Dict com resumo por categoria
        """
        print("=" * 60)
        print("ICT BRAIN DISTILLER -- CEREBRO LUCRATIVO")
        print("Destilando ensinamentos do ICT em Ingles")
        print("=" * 60)

        target_cats = cat_ids or list(CATEGORIES.keys())
        results = {}

        # SINGLE-PASS: carrega chunks de todas as categorias lendo cada arquivo 1x.
        # Só vale a pena quando há mais de 1 categoria alvo.
        all_buckets = None
        if len(target_cats) > 1:
            all_buckets = self.load_all_chunks_by_category()

        for cat_id in target_cats:
            if cat_id not in CATEGORIES:
                print(f"[Distiller] Categoria desconhecida: {cat_id}")
                continue

            preloaded = all_buckets.get(cat_id) if all_buckets is not None else None
            result_path = self.distill_category(cat_id, rebuild=rebuild, chunks=preloaded)
            results[cat_id] = {
                "success": result_path is not None,
                "path":    result_path,
                "nome":    CATEGORIES[cat_id]["nome"],
            }

        # Cria o MOC (Map of Content) das regras destiladas no Obsidian
        self._create_moc(results)

        print("\n" + "=" * 60)
        print("DESTILACAO CONCLUIDA")
        success_count = sum(1 for r in results.values() if r["success"])
        print(f"  Categorias destiladas: {success_count}/{len(target_cats)}")
        print(f"  Arquivos em: {OBSIDIAN_ICT}")
        print("=" * 60)

        return results

    def _create_moc(self, results: dict):
        """Creates/updates the Map of Content of distilled rules in Obsidian."""
        moc_path = OBSIDIAN_ICT / "MOC_YouTube_Distilled.md"
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        links = []
        for cat_id, r in results.items():
            if r["success"]:
                arquivo_sem_ext = CATEGORIES[cat_id]["arquivo"].replace(".md", "")
                nome = r["nome"]
                links.append(f"- [[B03 Regras ICT/{arquivo_sem_ext}|{nome}]]")

        moc_content = f"""---
tags: [ICT, moc, youtube-distilled]
updated: {now}
---

# Map — ICT Rules Distilled from YouTube

> Knowledge of Michael J. Huddleston distilled from YouTube transcripts
> Updated on: {now}

## Available Categories

{chr(10).join(links)}

---

## How to use
Each file below contains operational rules automatically extracted
from ICT videos, filtered to contain ONLY technical trading content.

The ICT AI agent uses these files automatically via `core/rag.py`.

---
*Generated by ICT Brain Distiller*
"""
        with open(moc_path, "w", encoding="utf-8") as f:
            f.write(moc_content)
        print(f"\n[Distiller] MOC criado: {moc_path.name}")


# ─── Execução standalone ────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ICT Brain Distiller")
    parser.add_argument("--cat",     type=str, default=None,
                        help=f"Categoria especifica. Opcoes: {', '.join(CATEGORIES.keys())}")
    parser.add_argument("--rebuild", action="store_true", help="Sobrescreve arquivos existentes")
    parser.add_argument("--list",    action="store_true", help="Lista categorias disponíveis")
    args = parser.parse_args()

    if args.list:
        print("\nCategorias disponíveis:")
        for cat_id, cat in CATEGORIES.items():
            print(f"  {cat_id:<25} → {cat['nome']}")
        exit(0)

    distiller = ICTDistiller()
    cat_ids = [args.cat] if args.cat else None
    distiller.run(cat_ids=cat_ids, rebuild=args.rebuild)
