-- ──────────────────────────────────────────────────────────────
-- VacinaFácil AI — Busca semântica com pgvector
-- Execute no Supabase: SQL Editor → New Query → Run
-- Requer: extensão vector habilitada (Database > Extensions > vector)
-- ──────────────────────────────────────────────────────────────

-- 1. Habilita pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabela de embeddings
CREATE TABLE IF NOT EXISTS base_embeddings (
  id         UUID    DEFAULT gen_random_uuid() PRIMARY KEY,
  fonte      TEXT    NOT NULL,          -- vacinas | faq | mitos | doencas | pos_exposicao
  titulo     TEXT,
  conteudo   TEXT    NOT NULL,
  embedding  vector(1536),              -- text-embedding-3-small
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Índice IVFFlat para busca por similaridade coseno
CREATE INDEX IF NOT EXISTS idx_base_embeddings_ivfflat
  ON base_embeddings USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- 4. RLS: anon pode ler, service role pode escrever
ALTER TABLE base_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read_embeddings"
  ON base_embeddings FOR SELECT
  TO anon
  USING (true);

-- 5. Função de busca semântica
CREATE OR REPLACE FUNCTION buscar_semantico(
  query_embedding vector(1536),
  limite          INT DEFAULT 6
)
RETURNS TABLE (
  fonte        TEXT,
  titulo       TEXT,
  conteudo     TEXT,
  similaridade FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    fonte,
    titulo,
    conteudo,
    1 - (embedding <=> query_embedding) AS similaridade
  FROM base_embeddings
  WHERE embedding IS NOT NULL
  ORDER BY embedding <=> query_embedding
  LIMIT limite;
$$;
