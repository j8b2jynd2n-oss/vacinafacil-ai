-- =============================================================
-- VacinaFácil AI — Schema do Banco de Dados
-- Executar no SQL Editor do Supabase (em ordem)
-- =============================================================

-- 1. Extensão para busca sem acento (obrigatória)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- =============================================================
-- TABELAS
-- =============================================================

CREATE TABLE IF NOT EXISTS vacinas (
    id                                  TEXT PRIMARY KEY,
    nome_da_vacina                      TEXT NOT NULL,
    nome_popular_apelido                TEXT,
    sinonimos_variacoes                 TEXT,
    doencas_prevenidas                  TEXT,
    tipo_de_vacina                      TEXT,
    fabricante_laboratorio              TEXT,
    composicao_principal                TEXT,
    publico_alvo                        TEXT,
    faixa_etaria_recomendada            TEXT,
    idade_da_1a_dose                    TEXT,
    doses_totais_padrao                 TEXT,
    doses_totais_imunossuprimido        TEXT,
    esquema_resumido                    TEXT,
    tipo_de_esquema                     TEXT,
    intervalo_entre_doses               TEXT,
    reforcos                            TEXT,
    substitui_e_substituida_por         TEXT,
    via_de_administracao                TEXT,
    local_de_aplicacao_no_corpo         TEXT,
    disponivel_no_sus                   TEXT,
    disponivel_na_rede_privada          TEXT,
    onde_se_vacinar                     TEXT,
    documentos_necessarios              TEXT,
    precisa_de_receita_medica           TEXT,
    obrigatoria                         TEXT,
    calendario_pni                      TEXT,
    contraindicacoes                    TEXT,
    precaucoes                          TEXT,
    efeitos_colaterais_comuns           TEXT,
    efeitos_colaterais_raros_graves     TEXT,
    o_que_fazer_em_caso_de_reacao       TEXT,
    quando_procurar_atendimento_urgente TEXT,
    pode_tomar_junto_com_outras_vacinas TEXT,
    restricoes_para_gestantes           TEXT,
    restricoes_para_lactantes           TEXT,
    restricoes_para_imunossuprimidos    TEXT,
    restricoes_para_alergicos           TEXT,
    eficacia_numerica                   NUMERIC,
    eficacia_descritiva                 TEXT,
    duracao_da_protecao                 TEXT,
    registro_no_cartao_de_vacinacao     TEXT,
    mitos_comuns                        TEXT,
    resposta_a_mitos                    TEXT,
    palavras_chave_ia                   TEXT,
    perguntas_gatilho_ia                TEXT,
    resposta_padrao_sugerida            TEXT,
    pergunta_de_followup_sugerida       TEXT,
    quando_encaminhar_a_profissional    TEXT,
    nivel_de_confianca_da_info          TEXT,
    fonte_oficial_id                    TEXT,
    ultima_atualizacao                  DATE,
    data_de_validade_da_informacao      DATE,
    responsavel_pela_curadoria          TEXT,
    status_de_revisao                   TEXT,
    observacoes_internas                TEXT
);

CREATE TABLE IF NOT EXISTS calendarios_pni (
    id_calendario   TEXT PRIMARY KEY,
    publico         TEXT,
    idade_ou_momento TEXT,
    id_vacina       TEXT REFERENCES vacinas(id),
    nome_da_vacina  TEXT,
    dose            TEXT,
    observacoes     TEXT,
    fonte_id        TEXT
);

CREATE TABLE IF NOT EXISTS faq (
    id_faq                           TEXT PRIMARY KEY,
    categoria                        TEXT,
    pergunta                         TEXT NOT NULL,
    variacoes_da_pergunta            TEXT,
    resposta                         TEXT NOT NULL,
    pergunta_de_followup_sugerida    TEXT,
    vacinas_relacionadas_ids         TEXT,
    palavras_chave_ia                TEXT,
    quando_encaminhar_a_profissional TEXT,
    fonte_id                         TEXT,
    status_de_revisao                TEXT,
    ultima_atualizacao               DATE
);

CREATE TABLE IF NOT EXISTS glossario (
    termo_tecnico                    TEXT PRIMARY KEY,
    traducao_para_linguagem_simples  TEXT,
    exemplo_de_uso                   TEXT,
    categoria                        TEXT,
    sinonimos                        TEXT
);

CREATE TABLE IF NOT EXISTS limites_atuacao (
    id_regra                         TEXT PRIMARY KEY,
    tipo_de_limite                   TEXT,
    descricao_da_situacao            TEXT,
    comportamento_esperado_da_ia     TEXT,
    exemplo_de_pergunta_do_usuario   TEXT,
    resposta_padrao_sugerida         TEXT,
    encaminhamento                   TEXT,
    severidade                       TEXT,
    responsavel                      TEXT,
    status                           TEXT
);

CREATE TABLE IF NOT EXISTS fontes_oficiais (
    id_fonte         TEXT PRIMARY KEY,
    nome_da_fonte    TEXT,
    instituicao      TEXT,
    tipo             TEXT,
    link_url         TEXT,
    data_publicacao  TEXT,
    data_acesso      TEXT,
    confiabilidade   TEXT,
    observacoes      TEXT
);

CREATE TABLE IF NOT EXISTS campanhas (
    id_campanha          TEXT PRIMARY KEY,
    nome_da_campanha     TEXT,
    vacinas_ids          TEXT,
    tipo_de_campanha     TEXT,
    periodo_do_ano       TEXT,
    publico_da_campanha  TEXT,
    meta_de_cobertura    TEXT,
    locais_de_mobilizacao TEXT,
    mensagem_chave       TEXT,
    observacoes          TEXT
);

CREATE TABLE IF NOT EXISTS mitos (
    id_mito                       TEXT PRIMARY KEY,
    categoria                     TEXT,
    mito_como_circula             TEXT NOT NULL,
    variacoes_do_mito             TEXT,
    resposta_baseada_em_evidencia TEXT NOT NULL,
    tom_da_resposta               TEXT,
    vacinas_relacionadas_ids      TEXT,
    origem_do_mito                TEXT,
    palavras_chave_ia             TEXT,
    fonte_id                      TEXT,
    status_de_revisao             TEXT,
    ultima_atualizacao            DATE
);

CREATE TABLE IF NOT EXISTS cenarios (
    id_cenario                       TEXT PRIMARY KEY,
    nome_do_cenario                  TEXT,
    persona_contexto                 TEXT,
    intencao_principal               TEXT,
    pergunta_inicial_tipica          TEXT,
    sequencia_de_perguntas_esperadas TEXT,
    respostas_sugeridas_em_ordem     TEXT,
    pontos_de_atencao                TEXT,
    quando_encerrar                  TEXT,
    tom_recomendado                  TEXT,
    vacinas_relacionadas_ids         TEXT,
    status_de_revisao                TEXT
);

CREATE TABLE IF NOT EXISTS atrasos_esquemas (
    id_caso                  TEXT PRIMARY KEY,
    id_vacina                TEXT REFERENCES vacinas(id),
    situacao                 TEXT,
    faixa_etaria             TEXT,
    tempo_de_atraso          TEXT,
    recomendacao             TEXT,
    justificativa            TEXT,
    tipo_de_caso             TEXT,
    encaminhar_a_profissional TEXT,
    fonte_id                 TEXT,
    status_de_revisao        TEXT
);

CREATE TABLE IF NOT EXISTS historico_protocolos (
    id_mudanca                       TEXT PRIMARY KEY,
    id_vacina                        TEXT REFERENCES vacinas(id),
    ano_da_mudanca                   TEXT,
    protocolo_anterior               TEXT,
    protocolo_atual                  TEXT,
    motivo_da_mudanca                TEXT,
    impacto_para_quem_iniciou_no_antigo TEXT,
    fonte_id                         TEXT,
    status_de_revisao                TEXT
);

CREATE TABLE IF NOT EXISTS viagem_internacional (
    id_viagem               TEXT PRIMARY KEY,
    destino_regiao          TEXT,
    vacinas_recomendadas    TEXT,
    vacinas_obrigatorias    TEXT,
    antecedencia_necessaria TEXT,
    onde_se_vacinar         TEXT,
    certificado_internacional TEXT,
    documentos_necessarios  TEXT,
    observacoes             TEXT,
    fonte_id                TEXT,
    status_de_revisao       TEXT
);

CREATE TABLE IF NOT EXISTS doencas (
    id_doenca                       TEXT PRIMARY KEY,
    nome_da_doenca                  TEXT NOT NULL,
    sinonimos_como_o_cidadao_chama  TEXT,
    categoria                       TEXT,
    resumo_linguagem_simples        TEXT,
    sintomas_principais             TEXT,
    forma_de_transmissao            TEXT,
    gravidade                       TEXT,
    vacinas_que_previnem_ids        TEXT,
    quando_procurar_atendimento     TEXT,
    ha_tratamento_especifico        TEXT,
    profilaxia_pos_exposicao_id     TEXT,
    esta_controlada_no_brasil       TEXT,
    palavras_chave_ia               TEXT,
    pergunta_gatilho_tipica         TEXT,
    resposta_padrao_sugerida        TEXT,
    quando_encaminhar_a_profissional TEXT,
    fonte_id                        TEXT,
    status                          TEXT,
    ultima_atualizacao              DATE
);

CREATE TABLE IF NOT EXISTS pos_exposicao (
    id_profilaxia                TEXT PRIMARY KEY,
    tipo_de_exposicao            TEXT,
    cenario_especifico           TEXT,
    doenca_prevenida             TEXT,
    urgencia                     TEXT,
    primeiro_passo_cidadao       TEXT,
    aonde_procurar               TEXT,
    conduta_profissional_esperada TEXT,
    esquema_de_profilaxia        TEXT,
    vacinas_envolvidas_ids       TEXT,
    janela_de_oportunidade       TEXT,
    para_nao_vacinados           TEXT,
    para_ja_vacinados            TEXT,
    sinais_de_alarme             TEXT,
    mensagem_empatica_sugerida   TEXT,
    encaminhar_para_atendimento  TEXT,
    fonte_id                     TEXT,
    status                       TEXT,
    ultima_atualizacao           DATE,
    observacoes_internas         TEXT
);

CREATE TABLE IF NOT EXISTS rede_privada (
    id_vacina_privada            TEXT PRIMARY KEY,
    nome_da_vacina               TEXT,
    nome_popular                 TEXT,
    doenca_prevenida             TEXT,
    tipo                         TEXT,
    fabricante                   TEXT,
    indicacao_principal          TEXT,
    faixa_etaria                 TEXT,
    esquema_de_doses             TEXT,
    existe_equivalente_no_sus    TEXT,
    quando_considerar_vs_sus     TEXT,
    disponivel_no_sus_grupos     TEXT,
    faixa_de_preco_brl           TEXT,
    onde_encontrar               TEXT,
    contraindicacoes_principais  TEXT,
    eficacia                     TEXT,
    recomendacao_sbim            TEXT,
    palavras_chave_ia            TEXT,
    pergunta_gatilho_tipica      TEXT,
    resposta_padrao_sugerida     TEXT,
    encaminhar_a_profissional    TEXT,
    fonte_id                     TEXT,
    status                       TEXT,
    ultima_atualizacao           DATE,
    observacoes                  TEXT
);

-- =============================================================
-- FUNÇÃO AUXILIAR: unaccent imutável (obrigatório para índices)
-- =============================================================

CREATE OR REPLACE FUNCTION f_unaccent(text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT AS
$func$ SELECT unaccent($1) $func$;

-- =============================================================
-- ÍNDICES DE BUSCA (Full-Text Search em Português)
-- =============================================================

CREATE INDEX IF NOT EXISTS idx_vacinas_fts ON vacinas
    USING gin(to_tsvector('portuguese',
        f_unaccent(coalesce(nome_da_vacina,'') || ' ' ||
                   coalesce(sinonimos_variacoes,'') || ' ' ||
                   coalesce(palavras_chave_ia,'') || ' ' ||
                   coalesce(perguntas_gatilho_ia,'') || ' ' ||
                   coalesce(doencas_prevenidas,'') || ' ' ||
                   coalesce(nome_popular_apelido,''))
    ));

CREATE INDEX IF NOT EXISTS idx_faq_fts ON faq
    USING gin(to_tsvector('portuguese',
        f_unaccent(coalesce(pergunta,'') || ' ' ||
                   coalesce(variacoes_da_pergunta,'') || ' ' ||
                   coalesce(palavras_chave_ia,'') || ' ' ||
                   coalesce(resposta,''))
    ));

CREATE INDEX IF NOT EXISTS idx_mitos_fts ON mitos
    USING gin(to_tsvector('portuguese',
        f_unaccent(coalesce(mito_como_circula,'') || ' ' ||
                   coalesce(variacoes_do_mito,'') || ' ' ||
                   coalesce(palavras_chave_ia,''))
    ));

CREATE INDEX IF NOT EXISTS idx_doencas_fts ON doencas
    USING gin(to_tsvector('portuguese',
        f_unaccent(coalesce(nome_da_doenca,'') || ' ' ||
                   coalesce(sinonimos_como_o_cidadao_chama,'') || ' ' ||
                   coalesce(palavras_chave_ia,''))
    ));

-- =============================================================
-- FUNÇÃO DE BUSCA UNIFICADA (usada pelo agente de IA)
-- =============================================================

CREATE OR REPLACE FUNCTION buscar_conhecimento(
    query_text TEXT,
    limite     INTEGER DEFAULT 5
)
RETURNS TABLE(
    fonte      TEXT,
    id         TEXT,
    titulo     TEXT,
    conteudo   TEXT,
    relevancia REAL
)
LANGUAGE plpgsql AS $$
DECLARE
    tsq tsquery;
BEGIN
    -- Converte a pergunta do usuário em tsquery tolerante a erros
    BEGIN
        tsq := plainto_tsquery('portuguese', f_unaccent(query_text));
    EXCEPTION WHEN OTHERS THEN
        tsq := plainto_tsquery('simple', f_unaccent(query_text));
    END;

    RETURN QUERY

    -- Vacinas
    SELECT
        'vacina'::TEXT,
        v.id,
        v.nome_da_vacina,
        concat_ws(' | ',
            v.doencas_prevenidas,
            v.resposta_padrao_sugerida,
            v.efeitos_colaterais_comuns,
            v.contraindicacoes,
            v.restricoes_para_gestantes,
            v.restricoes_para_imunossuprimidos
        ),
        ts_rank(
            to_tsvector('portuguese', f_unaccent(
                coalesce(v.nome_da_vacina,'') || ' ' ||
                coalesce(v.sinonimos_variacoes,'') || ' ' ||
                coalesce(v.palavras_chave_ia,'') || ' ' ||
                coalesce(v.perguntas_gatilho_ia,'') || ' ' ||
                coalesce(v.doencas_prevenidas,'') || ' ' ||
                coalesce(v.nome_popular_apelido,'')
            )), tsq
        )
    FROM vacinas v
    WHERE to_tsvector('portuguese', f_unaccent(
            coalesce(v.nome_da_vacina,'') || ' ' ||
            coalesce(v.sinonimos_variacoes,'') || ' ' ||
            coalesce(v.palavras_chave_ia,'') || ' ' ||
            coalesce(v.perguntas_gatilho_ia,'') || ' ' ||
            coalesce(v.doencas_prevenidas,'') || ' ' ||
            coalesce(v.nome_popular_apelido,'')
          )) @@ tsq

    UNION ALL

    -- FAQ
    SELECT
        'faq'::TEXT,
        f.id_faq,
        f.pergunta,
        concat_ws(' | ', f.resposta, f.pergunta_de_followup_sugerida),
        ts_rank(
            to_tsvector('portuguese', f_unaccent(
                coalesce(f.pergunta,'') || ' ' ||
                coalesce(f.variacoes_da_pergunta,'') || ' ' ||
                coalesce(f.palavras_chave_ia,'') || ' ' ||
                coalesce(f.resposta,'')
            )), tsq
        )
    FROM faq f
    WHERE to_tsvector('portuguese', f_unaccent(
            coalesce(f.pergunta,'') || ' ' ||
            coalesce(f.variacoes_da_pergunta,'') || ' ' ||
            coalesce(f.palavras_chave_ia,'') || ' ' ||
            coalesce(f.resposta,'')
          )) @@ tsq

    UNION ALL

    -- Mitos
    SELECT
        'mito'::TEXT,
        m.id_mito,
        m.mito_como_circula,
        m.resposta_baseada_em_evidencia,
        ts_rank(
            to_tsvector('portuguese', f_unaccent(
                coalesce(m.mito_como_circula,'') || ' ' ||
                coalesce(m.variacoes_do_mito,'') || ' ' ||
                coalesce(m.palavras_chave_ia,'')
            )), tsq
        )
    FROM mitos m
    WHERE to_tsvector('portuguese', f_unaccent(
            coalesce(m.mito_como_circula,'') || ' ' ||
            coalesce(m.variacoes_do_mito,'') || ' ' ||
            coalesce(m.palavras_chave_ia,'')
          )) @@ tsq

    UNION ALL

    -- Doenças
    SELECT
        'doenca'::TEXT,
        d.id_doenca,
        d.nome_da_doenca,
        concat_ws(' | ', d.resumo_linguagem_simples, d.quando_procurar_atendimento),
        ts_rank(
            to_tsvector('portuguese', f_unaccent(
                coalesce(d.nome_da_doenca,'') || ' ' ||
                coalesce(d.sinonimos_como_o_cidadao_chama,'') || ' ' ||
                coalesce(d.palavras_chave_ia,'') || ' ' ||
                coalesce(d.sintomas_principais,'')
            )), tsq
        )
    FROM doencas d
    WHERE to_tsvector('portuguese', f_unaccent(
            coalesce(d.nome_da_doenca,'') || ' ' ||
            coalesce(d.sinonimos_como_o_cidadao_chama,'') || ' ' ||
            coalesce(d.palavras_chave_ia,'') || ' ' ||
            coalesce(d.sintomas_principais,'')
          )) @@ tsq

    UNION ALL

    -- Pós-Exposição
    SELECT
        'pos_exposicao'::TEXT,
        p.id_profilaxia,
        p.tipo_de_exposicao,
        concat_ws(' | ', p.primeiro_passo_cidadao, p.esquema_de_profilaxia, p.sinais_de_alarme),
        ts_rank(
            to_tsvector('portuguese', f_unaccent(
                coalesce(p.tipo_de_exposicao,'') || ' ' ||
                coalesce(p.cenario_especifico,'') || ' ' ||
                coalesce(p.doenca_prevenida,'')
            )), tsq
        )
    FROM pos_exposicao p
    WHERE to_tsvector('portuguese', f_unaccent(
            coalesce(p.tipo_de_exposicao,'') || ' ' ||
            coalesce(p.cenario_especifico,'') || ' ' ||
            coalesce(p.doenca_prevenida,'')
          )) @@ tsq

    ORDER BY relevancia DESC
    LIMIT limite;
END;
$$;

-- =============================================================
-- HABILITAR ROW LEVEL SECURITY (leitura pública, sem escrita)
-- =============================================================

ALTER TABLE vacinas             ENABLE ROW LEVEL SECURITY;
ALTER TABLE faq                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE mitos               ENABLE ROW LEVEL SECURITY;
ALTER TABLE doencas             ENABLE ROW LEVEL SECURITY;
ALTER TABLE pos_exposicao       ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendarios_pni     ENABLE ROW LEVEL SECURITY;
ALTER TABLE glossario           ENABLE ROW LEVEL SECURITY;
ALTER TABLE limites_atuacao     ENABLE ROW LEVEL SECURITY;
ALTER TABLE campanhas           ENABLE ROW LEVEL SECURITY;
ALTER TABLE cenarios            ENABLE ROW LEVEL SECURITY;
ALTER TABLE atrasos_esquemas    ENABLE ROW LEVEL SECURITY;
ALTER TABLE historico_protocolos ENABLE ROW LEVEL SECURITY;
ALTER TABLE viagem_internacional ENABLE ROW LEVEL SECURITY;
ALTER TABLE rede_privada        ENABLE ROW LEVEL SECURITY;
ALTER TABLE fontes_oficiais     ENABLE ROW LEVEL SECURITY;

-- Política: leitura pública para o chatbot (anon key)
CREATE POLICY "leitura_publica" ON vacinas             FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON faq                 FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON mitos               FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON doencas             FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON pos_exposicao       FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON calendarios_pni     FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON glossario           FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON limites_atuacao     FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON campanhas           FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON cenarios            FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON atrasos_esquemas    FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON historico_protocolos FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON viagem_internacional FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON rede_privada        FOR SELECT USING (true);
CREATE POLICY "leitura_publica" ON fontes_oficiais     FOR SELECT USING (true);
