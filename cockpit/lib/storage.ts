import { supabase } from "./supabase";

const BUCKET = "copa-prints";
const MIME_PERMITIDOS = ["image/png", "image/jpeg", "image/webp"];
const MAX_BYTES = 10 * 1024 * 1024; // 10 MB

/** Sobe um print. Caminho: <uid>/<YYYY-MM-DD>/<nome>. Devolve o path. */
export async function subirPrint(file: File, data: string, nome: string): Promise<string> {
  const { data: authData, error: authError } = await supabase.auth.getUser();
  if (authError || !authData?.user?.id) {
    throw new Error("Usuário não autenticado");
  }

  if (!MIME_PERMITIDOS.includes(file.type)) {
    throw new Error(`Tipo de imagem não suportado: ${file.type}. Aceito apenas PNG, JPEG ou WebP.`);
  }

  if (file.size > MAX_BYTES) {
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    throw new Error(`Arquivo muito grande (${sizeMb} MB). Máximo permitido é 10 MB.`);
  }

  const uid = authData.user.id;
  const sanitizedNome = nome.replace(/[^a-zA-Z0-9_.-]/g, "_");
  const path = `${uid}/${data}/${sanitizedNome}`;

  const { error: uploadError } = await supabase.storage
    .from(BUCKET)
    .upload(path, file, {
      upsert: true,
      contentType: file.type,
    });

  if (uploadError) {
    throw new Error(`Erro ao enviar print: ${uploadError.message}`);
  }

  return path;
}

/** URL assinada para exibir. O bucket é privado; URL pública não funciona. */
export async function urlDoPrint(path: string, segundos: number = 3600): Promise<string | null> {
  if (!path) return null;
  try {
    const { data, error } = await supabase.storage
      .from(BUCKET)
      .createSignedUrl(path, segundos);

    if (error || !data?.signedUrl) {
      return null;
    }

    return data.signedUrl;
  } catch {
    return null;
  }
}
