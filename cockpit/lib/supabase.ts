import { createClient } from "@supabase/supabase-js";

const supabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL ||
  process.env.SUPABASE_URL ||
  "https://jirgsqhhnfqglxadqeap.supabase.co";

const anonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImppcmdzcWhobmZxZ2x4YWRxZWFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2MjUzMDUsImV4cCI6MjA4NTIwMTMwNX0.SMoPod2HY5eyqXsQCZlHX9-z86aVZoBl062fMP-Uapw";

export const supabase = createClient(supabaseUrl, anonKey, {
  auth: { persistSession: true },
});
