-- VacinaFácil AI — Campanhas de Vacinação
-- Execute no Supabase SQL Editor

CREATE TABLE IF NOT EXISTS campanhas (
  id           uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  titulo       text        NOT NULL,
  descricao    text,
  publico_alvo text,
  periodo      text,
  data_inicio  date        DEFAULT CURRENT_DATE,
  data_fim     date        NOT NULL,
  urgente      boolean     DEFAULT false,
  ativo        boolean     DEFAULT true,
  fonte_url    text,
  created_at   timestamptz DEFAULT now()
);

-- RLS: leitura pública, escrita apenas via service key
ALTER TABLE campanhas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "campanhas_public_read" ON campanhas
  FOR SELECT TO anon USING (ativo = true);

CREATE POLICY "campanhas_service_write" ON campanhas
  FOR ALL TO authenticated USING (true);

-- Índice para filtro por datas
CREATE INDEX IF NOT EXISTS campanhas_datas_idx ON campanhas (data_inicio, data_fim, ativo);

-- ─── Campanhas exemplo para 2026 ────────────────────────────────
INSERT INTO campanhas (titulo, descricao, publico_alvo, periodo, data_inicio, data_fim, urgente, fonte_url)
VALUES
  (
    'Campanha Nacional contra a Dengue',
    'Vacina Qdenga disponível gratuitamente nas UBS. São 2 doses com intervalo de 3 meses.',
    'Crianças e adolescentes de 10 a 14 anos',
    'Janeiro a Junho de 2026',
    '2026-01-01', '2026-06-30',
    true,
    'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/dengue'
  ),
  (
    'Campanha de Vacinação contra a Gripe 2026',
    'Vacina Influenza gratuita para grupos prioritários. Proteção dura um ano.',
    'Idosos +60 anos, gestantes, crianças 6m–5 anos, profissionais de saúde e educação',
    'Abril a Junho de 2026',
    '2026-04-01', '2026-06-30',
    false,
    'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/i/influenza-gripe'
  );
