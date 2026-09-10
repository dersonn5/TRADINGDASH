import { createClient } from "@supabase/supabase-js";

/**
 * Cliente service_role — ignora RLS, acesso total no backend.
 * SERVER-ONLY. Nunca importar em client components.
 */

const supabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL ||
  process.env.SUPABASE_URL ||
  "https://jirgsqhhnfqglxadqeap.supabase.co";

const serviceKey =
  process.env.SUPABASE_SERVICE_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImppcmdzcWhobmZxZ2x4YWRxZWFwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTYyNTMwNSwiZXhwIjoyMDg1MjAxMzA1fQ.JF7k5qAbpVO9ktx6zKa1YFWWweBKfwu6PODaTpwY0FA";

export const supabaseAdmin = createClient(supabaseUrl, serviceKey, {
  auth: { persistSession: false },
});
