"""
VacinaFácil AI — Script de Importação do Excel para o Supabase
Uso: python import_excel.py
"""

import os
import re
import unicodedata
import pandas as pd
from datetime import date, datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(override=True)

EXCEL_PATH = os.getenv("EXCEL_PATH", "../Downloads/VacinaFacil_AI_Base_Vacinas_v2.xlsx")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # service_role key para importação

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("❌ Configure SUPABASE_URL e SUPABASE_SERVICE_KEY no arquivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─────────────────────────────────────────────
# Utilitários
# ─────────────────────────────────────────────

def to_snake(name: str) -> str:
    name = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    name = re.sub(r"\s+", "_", name.strip()).lower()
    return re.sub(r"_+", "_", name).strip("_")


def clean_value(val):
    """Converte NaN, datas e tipos pandas para tipos Python nativos."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, datetime)):
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return None
        return val
    return str(val).strip() if str(val).strip() not in ("nan", "NaT", "None", "") else None


def df_to_records(df: pd.DataFrame, col_map: dict) -> list[dict]:
    """Converte um DataFrame para lista de dicts com nomes de coluna mapeados."""
    records = []
    for _, row in df.iterrows():
        record = {}
        for excel_col, sql_col in col_map.items():
            if excel_col in df.columns:
                record[sql_col] = clean_value(row[excel_col])
        records.append(record)
    return records


def inserir(tabela: str, records: list[dict], id_col: str = None):
    """Insere registros no Supabase com upsert para evitar duplicatas."""
    if not records:
        print(f"  ⚠  {tabela}: nenhum registro para inserir")
        return

    # Remove registros onde o ID é None (linhas vazias)
    if id_col:
        records = [r for r in records if r.get(id_col)]

    try:
        res = supabase.table(tabela).upsert(records).execute()
        print(f"  ✅ {tabela}: {len(records)} registros inseridos")
    except Exception as e:
        print(f"  ❌ {tabela}: erro — {e}")
        raise


# ─────────────────────────────────────────────
# Carregar Excel
# ─────────────────────────────────────────────

print(f"\n📂 Carregando Excel: {EXCEL_PATH}")
xl = pd.read_excel(EXCEL_PATH, sheet_name=None)
print(f"   {len(xl)} abas encontradas\n")

print("🚀 Iniciando importação...\n")

# ─────────────────────────────────────────────
# 1. VACINAS (Aba 1)
# ─────────────────────────────────────────────
df = xl["1. Base de Vacinas"]
col_map = {
    "ID":                                    "id",
    "Nome da Vacina":                        "nome_da_vacina",
    "Nome Popular / Apelido":               "nome_popular_apelido",
    "Sinônimos / Variações":                "sinonimos_variacoes",
    "Doença(s) Prevenida(s)":              "doencas_prevenidas",
    "Tipo de Vacina":                        "tipo_de_vacina",
    "Fabricante / Laboratório":             "fabricante_laboratorio",
    "Composição Principal":                 "composicao_principal",
    "Público-Alvo":                         "publico_alvo",
    "Faixa Etária Recomendada":            "faixa_etaria_recomendada",
    "Idade da 1ª Dose":                    "idade_da_1a_dose",
    "Doses Totais (Padrão)":               "doses_totais_padrao",
    "Doses Totais (Imunossuprimido)":       "doses_totais_imunossuprimido",
    "Esquema Resumido":                      "esquema_resumido",
    "Tipo de Esquema":                       "tipo_de_esquema",
    "Intervalo Entre Doses":                "intervalo_entre_doses",
    "Reforços":                             "reforcos",
    "Substitui / É Substituída Por":       "substitui_e_substituida_por",
    "Via de Administração":                 "via_de_administracao",
    "Local de Aplicação no Corpo":         "local_de_aplicacao_no_corpo",
    "Disponível no SUS?":                  "disponivel_no_sus",
    "Disponível na Rede Privada?":         "disponivel_na_rede_privada",
    "Onde se Vacinar":                      "onde_se_vacinar",
    "Documentos Necessários":              "documentos_necessarios",
    "Precisa de Receita Médica?":          "precisa_de_receita_medica",
    "Obrigatória?":                         "obrigatoria",
    "Calendário (PNI)":                    "calendario_pni",
    "Contraindicações":                     "contraindicacoes",
    "Precauções":                           "precaucoes",
    "Efeitos Colaterais Comuns":           "efeitos_colaterais_comuns",
    "Efeitos Colaterais Raros / Graves":   "efeitos_colaterais_raros_graves",
    "O Que Fazer em Caso de Reação":       "o_que_fazer_em_caso_de_reacao",
    "Quando Procurar Atendimento Urgente": "quando_procurar_atendimento_urgente",
    "Pode Tomar Junto com Outras Vacinas?": "pode_tomar_junto_com_outras_vacinas",
    "Restrições para Gestantes":           "restricoes_para_gestantes",
    "Restrições para Lactantes":           "restricoes_para_lactantes",
    "Restrições para Imunossuprimidos":    "restricoes_para_imunossuprimidos",
    "Restrições para Alérgicos":           "restricoes_para_alergicos",
    "Eficácia Numérica (%)":               "eficacia_numerica",
    "Eficácia Descritiva":                 "eficacia_descritiva",
    "Duração da Proteção":                 "duracao_da_protecao",
    "Registro no Cartão de Vacinação":     "registro_no_cartao_de_vacinacao",
    "Mitos Comuns":                         "mitos_comuns",
    "Resposta a Mitos":                     "resposta_a_mitos",
    "Palavras-Chave (IA)":                 "palavras_chave_ia",
    "Perguntas-Gatilho (IA)":              "perguntas_gatilho_ia",
    "Resposta Padrão Sugerida":            "resposta_padrao_sugerida",
    "Pergunta de Follow-up Sugerida":      "pergunta_de_followup_sugerida",
    "Quando Encaminhar a Profissional":    "quando_encaminhar_a_profissional",
    "Nível de Confiança da Info":          "nivel_de_confianca_da_info",
    "Fonte Oficial (ID)":                  "fonte_oficial_id",
    "Última Atualização":                  "ultima_atualizacao",
    "Data de Validade da Informação":      "data_de_validade_da_informacao",
    "Responsável pela Curadoria":          "responsavel_pela_curadoria",
    "Status de Revisão":                   "status_de_revisao",
    "Observações Internas":               "observacoes_internas",
}
inserir("vacinas", df_to_records(df, col_map), id_col="id")

# ─────────────────────────────────────────────
# 2. CALENDÁRIOS PNI (Aba 2)
# ─────────────────────────────────────────────
df = xl["2. Calendários PNI"]
col_map = {
    "ID Calendário":     "id_calendario",
    "Público":           "publico",
    "Idade ou Momento":  "idade_ou_momento",
    "ID Vacina":         "id_vacina",
    "Nome da Vacina":    "nome_da_vacina",
    "Dose":              "dose",
    "Observações":       "observacoes",
    "Fonte (ID)":        "fonte_id",
}
inserir("calendarios_pni", df_to_records(df, col_map), id_col="id_calendario")

# ─────────────────────────────────────────────
# 3. FAQ (Aba 3)
# ─────────────────────────────────────────────
df = xl["3. FAQ Transversal"]
col_map = {
    "ID FAQ":                            "id_faq",
    "Categoria":                         "categoria",
    "Pergunta":                          "pergunta",
    "Variações da Pergunta":            "variacoes_da_pergunta",
    "Resposta":                          "resposta",
    "Pergunta de Follow-up Sugerida":   "pergunta_de_followup_sugerida",
    "Vacinas Relacionadas (IDs)":        "vacinas_relacionadas_ids",
    "Palavras-Chave (IA)":              "palavras_chave_ia",
    "Quando Encaminhar a Profissional": "quando_encaminhar_a_profissional",
    "Fonte (ID)":                        "fonte_id",
    "Status de Revisão":                "status_de_revisao",
    "Última Atualização":               "ultima_atualizacao",
}
inserir("faq", df_to_records(df, col_map), id_col="id_faq")

# ─────────────────────────────────────────────
# 4. GLOSSÁRIO (Aba 4)
# ─────────────────────────────────────────────
df = xl["4. Glossário"]
col_map = {
    "Termo Técnico":                    "termo_tecnico",
    "Tradução para Linguagem Simples": "traducao_para_linguagem_simples",
    "Exemplo de Uso":                   "exemplo_de_uso",
    "Categoria":                        "categoria",
    "Sinônimos":                        "sinonimos",
}
inserir("glossario", df_to_records(df, col_map), id_col="termo_tecnico")

# ─────────────────────────────────────────────
# 5. LIMITES DE ATUAÇÃO (Aba 5)
# ─────────────────────────────────────────────
df = xl["5. Limites de Atuação"]
col_map = {
    "ID Regra":                          "id_regra",
    "Tipo de Limite":                    "tipo_de_limite",
    "Descrição da Situação":            "descricao_da_situacao",
    "Comportamento Esperado da IA":      "comportamento_esperado_da_ia",
    "Exemplo de Pergunta do Usuário":   "exemplo_de_pergunta_do_usuario",
    "Resposta Padrão Sugerida":         "resposta_padrao_sugerida",
    "Encaminhamento":                    "encaminhamento",
    "Severidade":                        "severidade",
    "Responsável":                       "responsavel",
    "Status":                            "status",
}
inserir("limites_atuacao", df_to_records(df, col_map), id_col="id_regra")

# ─────────────────────────────────────────────
# 6. FONTES OFICIAIS (Aba 6)
# ─────────────────────────────────────────────
df = xl["6. Fontes Oficiais"]
col_map = {
    "ID Fonte":           "id_fonte",
    "Nome da Fonte":      "nome_da_fonte",
    "Instituição":        "instituicao",
    "Tipo":               "tipo",
    "Link / URL":         "link_url",
    "Data de Publicação": "data_publicacao",
    "Data de Acesso":     "data_acesso",
    "Confiabilidade":     "confiabilidade",
    "Observações":        "observacoes",
}
inserir("fontes_oficiais", df_to_records(df, col_map), id_col="id_fonte")

# ─────────────────────────────────────────────
# 7. CAMPANHAS (Aba 7)
# ─────────────────────────────────────────────
df = xl["7. Campanhas"]
col_map = {
    "ID Campanha":          "id_campanha",
    "Nome da Campanha":     "nome_da_campanha",
    "Vacina(s) - IDs":      "vacinas_ids",
    "Tipo de Campanha":     "tipo_de_campanha",
    "Período do Ano":      "periodo_do_ano",
    "Público da Campanha": "publico_da_campanha",
    "Meta de Cobertura (%)": "meta_de_cobertura",
    "Locais de Mobilização": "locais_de_mobilizacao",
    "Mensagem-Chave":       "mensagem_chave",
    "Observações":          "observacoes",
}
inserir("campanhas", df_to_records(df, col_map), id_col="id_campanha")

# ─────────────────────────────────────────────
# 8. MITOS (Aba 8)
# ─────────────────────────────────────────────
df = xl["8. Mitos Brasileiros"]
col_map = {
    "ID Mito":                        "id_mito",
    "Categoria":                      "categoria",
    "Mito (como circula)":           "mito_como_circula",
    "Variações do Mito":             "variacoes_do_mito",
    "Resposta Baseada em Evidência": "resposta_baseada_em_evidencia",
    "Tom da Resposta":               "tom_da_resposta",
    "Vacinas Relacionadas (IDs)":    "vacinas_relacionadas_ids",
    "Origem do Mito":                "origem_do_mito",
    "Palavras-Chave (IA)":           "palavras_chave_ia",
    "Fonte (ID)":                    "fonte_id",
    "Status de Revisão":             "status_de_revisao",
    "Última Atualização":            "ultima_atualizacao",
}
inserir("mitos", df_to_records(df, col_map), id_col="id_mito")

# ─────────────────────────────────────────────
# 9. CENÁRIOS (Aba 9)
# ─────────────────────────────────────────────
df = xl["9. Cenários de Conversa"]
col_map = {
    "ID Cenário":                         "id_cenario",
    "Nome do Cenário":                    "nome_do_cenario",
    "Persona / Contexto":                "persona_contexto",
    "Intenção Principal":                "intencao_principal",
    "Pergunta Inicial Típica":           "pergunta_inicial_tipica",
    "Sequência de Perguntas Esperadas":  "sequencia_de_perguntas_esperadas",
    "Respostas Sugeridas (em ordem)":    "respostas_sugeridas_em_ordem",
    "Pontos de Atenção":                 "pontos_de_atencao",
    "Quando Encerrar":                   "quando_encerrar",
    "Tom Recomendado":                   "tom_recomendado",
    "Vacinas Relacionadas (IDs)":        "vacinas_relacionadas_ids",
    "Status de Revisão":                 "status_de_revisao",
}
inserir("cenarios", df_to_records(df, col_map), id_col="id_cenario")

# ─────────────────────────────────────────────
# 10. ATRASOS E ESQUEMAS (Aba 10)
# ─────────────────────────────────────────────
df = xl["10. Atrasos e Esquemas"]
col_map = {
    "ID Caso":                  "id_caso",
    "ID Vacina":                "id_vacina",
    "Situação":                 "situacao",
    "Faixa Etária":            "faixa_etaria",
    "Tempo de Atraso":          "tempo_de_atraso",
    "Recomendação":             "recomendacao",
    "Justificativa":            "justificativa",
    "Tipo de Caso":             "tipo_de_caso",
    "Encaminhar a Profissional?": "encaminhar_a_profissional",
    "Fonte (ID)":               "fonte_id",
    "Status de Revisão":        "status_de_revisao",
}
inserir("atrasos_esquemas", df_to_records(df, col_map), id_col="id_caso")

# ─────────────────────────────────────────────
# 11. HISTÓRICO DE PROTOCOLOS (Aba 11)
# ─────────────────────────────────────────────
df = xl["11. Histórico de Protocolos"]
col_map = {
    "ID Mudança":                           "id_mudanca",
    "ID Vacina":                            "id_vacina",
    "Ano da Mudança":                      "ano_da_mudanca",
    "Protocolo Anterior":                  "protocolo_anterior",
    "Protocolo Atual":                     "protocolo_atual",
    "Motivo da Mudança":                   "motivo_da_mudanca",
    "Impacto para Quem Iniciou no Antigo": "impacto_para_quem_iniciou_no_antigo",
    "Fonte (ID)":                          "fonte_id",
    "Status de Revisão":                   "status_de_revisao",
}
inserir("historico_protocolos", df_to_records(df, col_map), id_col="id_mudanca")

# ─────────────────────────────────────────────
# 12. VIAGEM INTERNACIONAL (Aba 12)
# ─────────────────────────────────────────────
df = xl["12. Viagem Internacional"]
col_map = {
    "ID Viagem":                   "id_viagem",
    "Destino / Região":           "destino_regiao",
    "Vacina(s) Recomendada(s)":   "vacinas_recomendadas",
    "Vacina(s) Obrigatória(s)":   "vacinas_obrigatorias",
    "Antecedência Necessária":    "antecedencia_necessaria",
    "Onde se Vacinar":             "onde_se_vacinar",
    "Certificado Internacional?":  "certificado_internacional",
    "Documentos Necessários":     "documentos_necessarios",
    "Observações":                 "observacoes",
    "Fonte (ID)":                  "fonte_id",
    "Status de Revisão":          "status_de_revisao",
}
inserir("viagem_internacional", df_to_records(df, col_map), id_col="id_viagem")

# ─────────────────────────────────────────────
# 13. DOENÇAS (Aba 13)
# ─────────────────────────────────────────────
df = xl["13. Doenças"]
col_map = {
    "ID Doença":                            "id_doenca",
    "Nome da Doença":                      "nome_da_doenca",
    "Sinônimos / Como o cidadão chama":   "sinonimos_como_o_cidadao_chama",
    "Categoria":                            "categoria",
    "Resumo (linguagem simples)":          "resumo_linguagem_simples",
    "Sintomas Principais":                 "sintomas_principais",
    "Forma de Transmissão":               "forma_de_transmissao",
    "Gravidade":                           "gravidade",
    "Vacina(s) que Previne(m) - IDs":     "vacinas_que_previnem_ids",
    "Quando Procurar Atendimento":         "quando_procurar_atendimento",
    "Há tratamento específico?":          "ha_tratamento_especifico",
    "Profilaxia Pós-Exposição (ID)":      "profilaxia_pos_exposicao_id",
    "Está controlada/erradicada no Brasil?": "esta_controlada_no_brasil",
    "Palavras-Chave (IA)":                "palavras_chave_ia",
    "Pergunta-Gatilho Típica":            "pergunta_gatilho_tipica",
    "Resposta Padrão Sugerida":           "resposta_padrao_sugerida",
    "Quando Encaminhar a Profissional":   "quando_encaminhar_a_profissional",
    "Fonte (ID)":                          "fonte_id",
    "Status":                              "status",
    "Última Atualização":                 "ultima_atualizacao",
}
inserir("doencas", df_to_records(df, col_map), id_col="id_doenca")

# ─────────────────────────────────────────────
# 14. PÓS-EXPOSIÇÃO (Aba 14)
# ─────────────────────────────────────────────
df = xl["14. Pós-Exposição"]
col_map = {
    "ID Profilaxia":                  "id_profilaxia",
    "Tipo de Exposição":             "tipo_de_exposicao",
    "Cenário Específico":            "cenario_especifico",
    "Doença Prevenida":              "doenca_prevenida",
    "URGÊNCIA":                       "urgencia",
    "Primeiro Passo (Cidadão)":      "primeiro_passo_cidadao",
    "Aonde Procurar":                "aonde_procurar",
    "Conduta Profissional Esperada": "conduta_profissional_esperada",
    "Esquema de Profilaxia":         "esquema_de_profilaxia",
    "Vacina(s) Envolvida(s) - IDs": "vacinas_envolvidas_ids",
    "Janela de Oportunidade":        "janela_de_oportunidade",
    "Para Não Vacinados Anteriormente": "para_nao_vacinados",
    "Para Já Vacinados":             "para_ja_vacinados",
    "Sinais de Alarme":              "sinais_de_alarme",
    "Mensagem Empática Sugerida":    "mensagem_empatica_sugerida",
    "Encaminhar para Atendimento?":  "encaminhar_para_atendimento",
    "Fonte (ID)":                    "fonte_id",
    "Status":                        "status",
    "Última Atualização":            "ultima_atualizacao",
    "Observações Internas":         "observacoes_internas",
}
inserir("pos_exposicao", df_to_records(df, col_map), id_col="id_profilaxia")

# ─────────────────────────────────────────────
# 15. REDE PRIVADA (Aba 15)
# ─────────────────────────────────────────────
df = xl["15. Rede Privada"]
col_map = {
    "ID Vacina Privada":                    "id_vacina_privada",
    "Nome da Vacina":                       "nome_da_vacina",
    "Nome Popular":                         "nome_popular",
    "Doença Prevenida":                    "doenca_prevenida",
    "Tipo":                                 "tipo",
    "Fabricante":                           "fabricante",
    "Indicação Principal":                 "indicacao_principal",
    "Faixa Etária":                        "faixa_etaria",
    "Esquema de Doses":                    "esquema_de_doses",
    "Existe Equivalente no SUS?":          "existe_equivalente_no_sus",
    "Quando Considerar (vs SUS)":          "quando_considerar_vs_sus",
    "Disponível no SUS para grupos específicos?": "disponivel_no_sus_grupos",
    "Faixa de Preço Aproximada (BRL)":     "faixa_de_preco_brl",
    "Onde Encontrar":                      "onde_encontrar",
    "Contraindicações Principais":         "contraindicacoes_principais",
    "Eficácia":                            "eficacia",
    "Recomendação SBIm":                   "recomendacao_sbim",
    "Palavras-Chave (IA)":                "palavras_chave_ia",
    "Pergunta-Gatilho Típica":            "pergunta_gatilho_tipica",
    "Resposta Padrão Sugerida":           "resposta_padrao_sugerida",
    "Encaminhar a Profissional?":         "encaminhar_a_profissional",
    "Fonte (ID)":                          "fonte_id",
    "Status":                              "status",
    "Última Atualização":                 "ultima_atualizacao",
    "Observações":                         "observacoes",
}
records = df_to_records(df, col_map)
for r in records:
    if r.get("ultima_atualizacao"):
        try:
            date.fromisoformat(r["ultima_atualizacao"])
        except (ValueError, TypeError):
            r["ultima_atualizacao"] = None
inserir("rede_privada", records, id_col="id_vacina_privada")

# ─────────────────────────────────────────────
# Relatório final
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("✅ IMPORTAÇÃO CONCLUÍDA")
print("=" * 50)
print("\nPróximos passos:")
print("  1. Acesse o painel do Supabase e confira as tabelas")
print("  2. Teste a busca: SELECT * FROM buscar_conhecimento('febre amarela');")
print("  3. Rode o agente: python agente.py")
