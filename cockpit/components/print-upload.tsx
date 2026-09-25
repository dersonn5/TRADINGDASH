"use client";

import React, { useState, useEffect, useRef } from "react";
import { subirPrint, urlDoPrint } from "@/lib/storage";

export interface PrintUploadProps {
  path: string | null;
  data: string;
  nome: string;
  onChange: (path: string | null) => void;
  obrigatorio?: boolean;
  label?: string;
  disabled?: boolean;
  /** linha compacta (checklist) em vez da area grande com miniatura (pre-sessao) */
  compacto?: boolean;
}

export function PrintUpload({
  path,
  data,
  nome,
  onChange,
  obrigatorio = false,
  label,
  disabled = false,
  compacto = false,
}: PrintUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [signedUrl, setSignedUrl] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Carrega URL assinada quando o path mudar
  useEffect(() => {
    let active = true;
    if (!path) {
      setSignedUrl(null);
      return;
    }

    urlDoPrint(path).then((url) => {
      if (active) {
        setSignedUrl(url);
      }
    });

    return () => {
      active = false;
    };
  }, [path]);

  const processUpload = async (file: File) => {
    if (disabled) return;
    setErrorMsg(null);
    setUploading(true);
    try {
      const ext = file.name.split(".").pop() || "png";
      const fileNome = nome.includes(".") ? nome : `${nome}.${ext}`;
      const newPath = await subirPrint(file, data, fileNome);
      onChange(newPath);
    } catch (err: any) {
      setErrorMsg(err.message || "Erro no upload da imagem");
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processUpload(file);
    }
    // Reseta input para permitir selecionar o mesmo arquivo novamente se quiser
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    if (disabled || uploading) return;
    const files = e.clipboardData?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith("image/")) {
        e.preventDefault();
        processUpload(file);
      }
    }
  };

  // Colar em QUALQUER lugar da pagina, nao so com a area focada.
  //
  // onPaste na div so dispara se a div tiver foco. Mas para focar a area o
  // usuario precisa clicar nela, e o clique abre o seletor de arquivo — nao
  // existe caminho para focar sem abrir o dialogo. Resultado: Ctrl+V nascia no
  // body, nunca passava pela div, e nao acontecia nada nem aparecia erro.
  //
  // O listener na janela resolve. So fica ativo enquanto nao ha print, para uma
  // area ja preenchida nao roubar o Ctrl+V de outra vazia na mesma tela.
  useEffect(() => {
    if (disabled || path) return;

    const aoColarNaJanela = (e: ClipboardEvent) => {
      if (uploading) return;
      const files = e.clipboardData?.files;
      if (!files || files.length === 0) return;
      const file = files[0];
      // Texto colado num campo nao traz files, entao digitar segue normal.
      if (!file.type.startsWith("image/")) return;
      e.preventDefault();
      processUpload(file);
    };

    window.addEventListener("paste", aoColarNaJanela);
    return () => window.removeEventListener("paste", aoColarNaJanela);
  }, [disabled, path, uploading, data, nome]);

  // Botao "Colar da area de transferencia": le a imagem copiada sem precisar do Ctrl+V.
  const colarDaAreaDeTransferencia = async () => {
    if (disabled || uploading) return;
    setErrorMsg(null);
    try {
      const itens = await navigator.clipboard.read();
      for (const item of itens) {
        const tipo = item.types.find((t) => t.startsWith("image/"));
        if (tipo) {
          const blob = await item.getType(tipo);
          await processUpload(new File([blob], `print.${tipo.split("/")[1] || "png"}`, { type: tipo }));
          return;
        }
      }
      setErrorMsg("Não há imagem na área de transferência.");
    } catch {
      setErrorMsg("O navegador não liberou a área de transferência. Use Ctrl+V.");
    }
  };

  const nomeArquivo = path ? path.split("/").pop() : "";
  const icone = (tam: number) => (
    <svg width={tam} height={tam} viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0, fill: "none", stroke: "var(--tx3)", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round" }}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 15l5-5 4 4 3-3 6 6" />
    </svg>
  );
  const botao: React.CSSProperties = {
    height: "40px",
    padding: "0 16px",
    borderRadius: "10px",
    border: "1px solid var(--bd)",
    background: "transparent",
    color: "var(--tx)",
    fontFamily: "inherit",
    fontSize: "13px",
    cursor: uploading ? "wait" : "pointer",
  };
  const escolher = () => {
    if (!disabled && !uploading) inputRef.current?.click();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      <input
        type="file"
        ref={inputRef}
        onChange={handleFileChange}
        accept="image/png,image/jpeg,image/webp"
        style={{ display: "none" }}
        disabled={disabled || uploading}
      />

      {compacto ? (
        <div
          role="button"
          tabIndex={disabled || path ? -1 : 0}
          onClick={path ? undefined : escolher}
          onPaste={handlePaste}
          onKeyDown={(e) => {
            if (!path && (e.key === "Enter" || e.key === " ")) {
              e.preventDefault();
              escolher();
            }
          }}
          style={{
            display: "flex", alignItems: "center", gap: "12px", padding: "12px 14px", borderRadius: "12px",
            border: `1px ${path ? "solid" : "dashed"} ${path ? "var(--ac)" : "var(--bd)"}`, background: path ? "var(--acs)" : "var(--bg)",
            cursor: path || disabled ? "default" : "pointer", outline: "none",
          }}
        >
          {path && signedUrl ? (
            <img src={signedUrl} alt="Miniatura do print" onClick={() => setModalOpen(true)} style={{ width: "48px", height: "32px", objectFit: "cover", borderRadius: "6px", cursor: "zoom-in", flexShrink: 0 }} />
          ) : (
            icone(20)
          )}
          <span style={{ flexGrow: 1, fontSize: "13px", color: path ? "var(--tx)" : "var(--tx2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {uploading ? "Enviando print…" : path ? nomeArquivo : label || "Print · cole com Ctrl+V"}
          </span>
          {path && !disabled ? (
            <>
              <button type="button" onClick={escolher} style={{ ...botao, height: "32px", padding: "0 12px", fontSize: "12px" }}>Trocar</button>
              <button type="button" onClick={() => onChange(null)} aria-label="Remover print" style={{ ...botao, height: "32px", width: "32px", padding: 0, color: "var(--tx3)" }}>×</button>
            </>
          ) : (
            <span style={{ fontSize: "12px", color: "var(--tx3)" }}>{obrigatorio ? "obrigatório" : "opcional"}</span>
          )}
        </div>
      ) : (
        <>
          <div
            role={path ? undefined : "button"}
            tabIndex={disabled || path ? -1 : 0}
            onClick={path ? () => signedUrl && setModalOpen(true) : escolher}
            onPaste={handlePaste}
            onKeyDown={(e) => {
              if (!path && (e.key === "Enter" || e.key === " ")) {
                e.preventDefault();
                escolher();
              }
            }}
            style={{
              height: "220px", borderRadius: "12px", border: `1px ${path ? "solid" : "dashed"} var(--bd)`, background: "var(--bg)",
              overflow: "hidden", position: "relative", display: "flex", alignItems: "center", justifyContent: "center",
              cursor: path ? (signedUrl ? "zoom-in" : "default") : disabled ? "not-allowed" : "pointer", outline: "none",
            }}
          >
            {path && signedUrl ? (
              <img src={signedUrl} alt="Print do gráfico HTF" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : path ? (
              <span style={{ fontSize: "13px", color: "var(--tx3)" }}>Carregando print…</span>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", padding: "0 24px", textAlign: "center" }}>
                {icone(28)}
                <span style={{ fontSize: "14px", fontWeight: 500 }}>{uploading ? "Enviando print…" : "Cole o print (Ctrl+V) ou clique para escolher"}</span>
                <span style={{ fontSize: "12px", color: "var(--tx3)" }}>Win+Shift+S recorta a tela · PNG, JPEG ou WebP até 10 MB</span>
              </div>
            )}
            {path && (
              <span style={{ position: "absolute", left: "14px", bottom: "12px", fontSize: "12px", padding: "6px 10px", borderRadius: "8px", background: "var(--s1)", border: "1px solid var(--bd)", color: "var(--tx2)" }}>
                {nomeArquivo}
              </span>
            )}
          </div>
          {!disabled && (
            <div style={{ display: "flex", gap: "10px" }}>
              <button type="button" onClick={escolher} disabled={uploading} style={botao}>
                {uploading ? "Enviando…" : path ? "Trocar print" : "Escolher arquivo"}
              </button>
              <button type="button" onClick={colarDaAreaDeTransferencia} disabled={uploading} style={{ ...botao, color: "var(--tx2)" }}>
                Colar da área de transferência
              </button>
              {path && (
                <button type="button" onClick={() => onChange(null)} disabled={uploading} style={{ ...botao, color: "var(--tx3)", marginLeft: "auto" }}>
                  Remover
                </button>
              )}
            </div>
          )}
        </>
      )}

      {errorMsg && <span style={{ fontSize: "12px", color: "var(--negtx)" }}>{errorMsg}</span>}

      {modalOpen && signedUrl && (
        <div onClick={() => setModalOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0, 0, 0, 0.85)", zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
          <div onClick={(e) => e.stopPropagation()} style={{ maxWidth: "95vw", maxHeight: "95vh", display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "12px", color: "var(--tx3)" }}>{nomeArquivo}</span>
              <button type="button" onClick={() => setModalOpen(false)} style={{ ...botao, height: "34px" }}>Fechar</button>
            </div>
            <img src={signedUrl} alt="Print ampliado" style={{ maxWidth: "100%", maxHeight: "85vh", objectFit: "contain", borderRadius: "12px", border: "1px solid var(--bd)" }} />
          </div>
        </div>
      )}
    </div>
  );
}
