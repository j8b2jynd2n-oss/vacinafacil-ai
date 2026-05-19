-- ──────────────────────────────────────────────────────────────
-- VacinaFácil AI — Tabela de feedback dos usuários
-- Execute no Supabase: SQL Editor → New Query → Run
-- ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS feedback (
  id         UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  pergunta   TEXT        NOT NULL,
  resposta   TEXT        NOT NULL,
  avaliacao  BOOLEAN     NOT NULL,   -- true = 👍  false = 👎
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: usuário anônimo pode inserir (chatbot público)
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_insert_feedback"
  ON feedback FOR INSERT
  TO anon
  WITH CHECK (true);

-- Service role (admin) pode ler tudo — sem política extra necessária
