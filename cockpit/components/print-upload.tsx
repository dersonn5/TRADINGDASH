"use client";

import React, { useState, useEffect, useRef } from "react";
import { subirPrint, urlDoPrint } from "@/lib/storage";
import { InstBadge } from "@/components/inst";
import { Image as ImageIcon, Loader2, Trash2, X, ExternalLink } from "lucide-react";

export interface PrintUploadProps {
  path: string | null;
  data: string;
  nome: string;
  onChange: (path: string | null) => void;
  obrigatorio?: boolean;
  label?: string;
  disabled?: boolean;
}

export function PrintUpload({
  path,
  data,
  nome,
  onChange,
  obrigatorio = false,
  label,
  disabled = false,
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

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      {label && (
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span className="mono" style={{ fontSize: "11px", letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--inst-faint)" }}>
            {label}
          </span>
          {obrigatorio && (
            <span style={{ fontSize: "11px", color: "var(--inst-block)", fontWeight: 700 }}>*</span>
          )}
        </div>
      )}

      <input
        type="file"
        ref={inputRef}
        onChange={handleFileChange}
        accept="image/png,image/jpeg,image/webp"
        style={{ display: "none" }}
        disabled={disabled || uploading}
      />

      {!path ? (
        <div
          tabIndex={disabled ? -1 : 0}
          onClick={() => {
            if (!disabled && !uploading) {
              inputRef.current?.click();
            }
          }}
          onPaste={handlePaste}
          onKeyDown={(e) => {
            if (!disabled && !uploading && (e.key === "Enter" || e.key === " ")) {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          className="mono"
          style={{
            border: "1px dashed var(--inst-line-2)",
            borderRadius: "10px",
            padding: "20px 16px",
            textAlign: "center",
            cursor: disabled ? "not-allowed" : "pointer",
            background: "var(--inst-panel)",
            color: "var(--inst-dim)",
            outline: "none",
            opacity: disabled ? 0.6 : 1,
            transition: "border-color 0.15s ease",
          }}
        >
          {uploading ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", color: "var(--inst-now)" }}>
              <Loader2 className="animate-spin" style={{ width: "16px", height: "16px" }} />
              <span style={{ fontSize: "12px" }}>Enviando print...</span>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <ImageIcon style={{ width: "16px", height: "16px", color: "var(--inst-dim)" }} />
                <span style={{ fontSize: "12px", color: "var(--inst-text)", fontWeight: 600 }}>
                  Ctrl+V em qualquer lugar da página, ou clique para escolher
                </span>
              </div>
              <span style={{ fontSize: "11px", color: "var(--inst-faint)" }}>
                Win+Shift+S recorta a tela · PNG, JPEG ou WebP até 10 MB
              </span>
            </div>
          )}
        </div>
      ) : (
        <div
          tabIndex={disabled ? -1 : 0}
          onPaste={handlePaste}
          style={{
            border: "1px solid var(--inst-ok-line)",
            borderRadius: "10px",
            padding: "10px 14px",
            background: "var(--inst-ok-bg)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
            outline: "none",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px", overflow: "hidden" }}>
            {signedUrl ? (
              <img
                src={signedUrl}
                alt="Miniatura do print"
                onClick={() => setModalOpen(true)}
                style={{
                  width: "56px",
                  height: "40px",
                  objectFit: "cover",
                  borderRadius: "8px",
                  border: "1px solid var(--inst-ok-line)",
                  cursor: "pointer",
                  flexShrink: 0,
                }}
                title="Clique para ampliar em tela cheia"
              />
            ) : (
              <div
                style={{
                  width: "56px",
                  height: "40px",
                  background: "var(--inst-panel)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "11px",
                  color: "var(--inst-dim)",
                  borderRadius: "8px",
                  flexShrink: 0,
                }}
              >
                Imagem
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "2px", minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <InstBadge tom="ok">PRINT ANEXADO</InstBadge>
                <span className="mono tabular truncate" style={{ fontSize: "11px", color: "var(--inst-dim)", maxWidth: "220px" }}>
                  {path.split("/").pop()}
                </span>
              </div>
              {signedUrl && (
                <button
                  type="button"
                  onClick={() => setModalOpen(true)}
                  className="mono"
                  style={{
                    background: "none",
                    border: "none",
                    padding: 0,
                    fontSize: "11px",
                    color: "var(--inst-ok)",
                    textAlign: "left",
                    cursor: "pointer",
                    textDecoration: "underline",
                  }}
                >
                  Ver em tamanho cheio
                </button>
              )}
            </div>
          </div>

          {!disabled && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                disabled={uploading}
                className="mono tabular"
                style={{
                  background: "var(--inst-panel-2)",
                  border: "1px solid var(--inst-line)",
                  color: "var(--inst-text)",
                  borderRadius: "8px",
                  padding: "4px 8px",
                  fontSize: "11px",
                  cursor: "pointer",
                }}
              >
                {uploading ? "Subindo..." : "Substituir"}
              </button>
              <button
                type="button"
                onClick={() => onChange(null)}
                disabled={uploading}
                className="mono tabular"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--inst-block)",
                  cursor: "pointer",
                  padding: "4px",
                  display: "flex",
                  alignItems: "center",
                }}
                title="Remover print"
              >
                <Trash2 style={{ width: "14px", height: "14px" }} />
              </button>
            </div>
          )}
        </div>
      )}

      {errorMsg && (
        <div className="mono" style={{ fontSize: "11px", color: "var(--inst-block)", marginTop: "2px" }}>
          {errorMsg}
        </div>
      )}

      {/* Modal de imagem em tamanho cheio */}
      {modalOpen && signedUrl && (
        <div
          onClick={() => setModalOpen(false)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.88)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: "relative",
              maxWidth: "95vw",
              maxHeight: "95vh",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="mono" style={{ fontSize: "11px", color: "var(--inst-dim)" }}>
                {path}
              </span>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="mono"
                style={{
                  background: "var(--inst-panel-2)",
                  border: "1px solid var(--inst-line)",
                  color: "var(--inst-text)",
                  borderRadius: "10px",
                  padding: "4px 10px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  fontSize: "11px",
                }}
              >
                <X style={{ width: "13px", height: "13px" }} /> Fechar
              </button>
            </div>
            <img
              src={signedUrl}
              alt="Print ampliado"
              style={{
                maxWidth: "100%",
                maxHeight: "85vh",
                objectFit: "contain",
                borderRadius: "10px",
                border: "1px solid var(--inst-line)",
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
