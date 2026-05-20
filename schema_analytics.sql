-- VacinaFácil AI — Analytics de Consultas (LGPD-compliant)
-- Execute no Supabase SQL Editor antes de iniciar o servidor.
--
-- Conformidade LGPD (Lei 13.709/2018):
--   ✔ Sem dados pessoais identificáveis
--   ✔ Sem endereço IP
--   ✔ Sem identificadores de sessão ou usuário
--   ✔ Apenas texto da pergunta (limitado a 200 chars) + timestamp

CREATE TABLE IF NOT EXISTS queries_log (
  id         uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  pergunta   text        NOT NULL CHECK (char_length(pergunta) <= 200),
  created_at timestamptz DEFAULT now()
);

-- Row Level Security
ALTER TABLE queries_log ENABLE ROW LEVEL SECURITY;

-- Qualquer cliente (anônimo) pode inserir — backend usa service key
CREATE POLICY "queries_insert_anon" ON queries_log
  FOR INSERT TO anon WITH CHECK (true);

-- Leitura apenas para usuários autenticados / service key
-- A service key bypassa RLS automaticamente
CREATE POLICY "queries_select_authenticated" ON queries_log
  FOR SELECT TO authenticated USING (true);

-- Índice para consultas por data (dashboard)
CREATE INDEX IF NOT EXISTS queries_log_created_at_idx ON queries_log (created_at DESC);

-- Limpeza automática: mantém apenas 90 dias de dados
-- (opcional — descomente para ativar retenção automática)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('limpar-queries-log', '0 3 * * *',
--   $$DELETE FROM queries_log WHERE created_at < now() - interval '90 days'$$);
