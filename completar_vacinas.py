"""
VacinaFácil AI — Completa todos os campos restantes das 12 vacinas novas
Preenche: efeitos_raros, precauções, mitos, imunossuprimidos, duração, obrigatória, etc.
Uso: python completar_vacinas.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

COMPLEMENTOS = {
    "VAC023": {  # VOP
        "efeitos_colaterais_raros_graves": "VAPP (Paralisia Associada à Vacina Oral de Pólio): 1 caso por ~2,4 milhões de doses — risco extremamente baixo; ocorre principalmente na 1ª dose",
        "precaucoes": "Adiar em diarreia intensa com desidratação ou vômitos frequentes; verificar se há imunodeprimido no domicílio (nesse caso usar VIP); confirmar que criança completou as 3 doses de VIP previamente",
        "doses_totais_imunossuprimido": "Contraindicada para imunodeprimidos — substituir por VIP injetável em todas as doses",
        "restricoes_para_imunossuprimidos": "Contraindicada. Crianças imunodeprimidas devem receber apenas VIP. Também contraindicada em crianças que convivem com imunodeprimidos graves no domicílio.",
        "duracao_da_protecao": "Proteção vitalícia com esquema completo VIP (3 doses) + VOP (2 reforços)",
        "mitos_comuns": "A gotinha causa paralisia infantil; a gotinha foi proibida e não existe mais; a injetável (VIP) é mais segura e substitui totalmente a gotinha",
        "resposta_a_mitos": "A paralisia por VOP (VAPP) é extraordinariamente rara — 1 caso em 2,4 milhões de doses. O Brasil ainda usa a VOP como reforço porque ela gera imunidade intestinal que reduz a transmissão comunitária, complementando a VIP. Os dois tipos de vacina têm funções diferentes e são igualmente seguros.",
        "obrigatoria": "Sim — Calendário Nacional de Vacinação (PNI)",
        "eficacia_numerica": 99,
        "idade_da_1a_dose": "15 meses (1º reforço oral — doses primárias são VIP aos 2, 4 e 6 meses)",
        "local_de_aplicacao_no_corpo": "Boca — 2 gotas orais",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC024": {  # PCV13
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara, < 1:1.000.000 doses); convulsão febril (rara em lactentes)",
        "precaucoes": "Adiar em doença aguda grave com febre alta; verificar histórico de vacinação pneumocócica anterior — respeitar intervalo mínimo de 8 semanas se já recebeu PPV23",
        "doses_totais_imunossuprimido": "Imunodeprimidos adultos: 1 dose PCV13 + PPV23 após ≥ 8 semanas | Crianças imunodeprimidas: série completa de 4 doses",
        "restricoes_para_imunossuprimidos": "Pode e deve ser usada (vacina inativada — segura para imunodeprimidos). Sequência recomendada: PCV13 → aguardar ≥ 8 semanas → PPV23. Imunodeprimidos graves podem precisar de doses adicionais.",
        "duracao_da_protecao": "Proteção duradoura após série completa; adultos de risco beneficiam-se de sequenciamento com PPV23",
        "mitos_comuns": "A vacina pneumo 10 do SUS já é suficiente para todos; PCV13 e PCV10 são a mesma coisa",
        "resposta_a_mitos": "A PCV10 (SUS) cobre 10 sorotipos pneumocócicos; a PCV13 cobre 13, adicionando os sorotipos 19A, 3 e 6A — responsáveis por pneumonias graves e resistentes. Para grupos de risco, a PCV13 via CRIE oferece proteção adicional importante.",
        "obrigatoria": "Não na rotina — indicação especial via CRIE para grupos de risco",
        "eficacia_numerica": 75,
        "idade_da_1a_dose": "2 meses (crianças em esquema completo); qualquer idade para adultos de risco",
        "local_de_aplicacao_no_corpo": "Coxa (lactentes); deltóide (crianças maiores e adultos)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC025": {  # Shingrix
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara); síndrome de Guillain-Barré (sinal de alerta pós-comercialização — investigado, risco extremamente baixo); reação cutânea extensa no local",
        "precaucoes": "Avisar o paciente sobre os efeitos colaterais intensos esperados pelo adjuvante AS01B — são sinais de resposta imune, não de reação adversa grave; adiar em imunossupressão intensa ativa (quimioterapia); esperar ≥ 3 meses após transplante",
        "doses_totais_imunossuprimido": "Mesmas 2 doses — Shingrix é especialmente recomendada para imunodeprimidos ≥ 18 anos por ser inativada e apresentar alta eficácia",
        "restricoes_para_imunossuprimidos": "Pode ser usada (inativada). Timing ideal: discutir com oncologista/infectologista. Evitar durante imunossupressão muito intensa. HIV positivos estáveis: indicada. Transplantados: aguardar ≥ 3 meses.",
        "duracao_da_protecao": "≥ 10 anos; estudos mostram proteção > 85% até 7 anos após a série completa",
        "mitos_comuns": "Quem já teve cobreiro não precisa vacinar; Shingrix contém vírus vivo e pode causar cobreiro; a vacina de catapora já protege contra o cobreiro",
        "resposta_a_mitos": "Quem já teve cobreiro PODE ter recorrência — a vacina reduz esse risco em > 90%. Shingrix usa subunidade recombinante (sem vírus vivo) — impossível causar cobreiro. A vacina de varicela previne primo-infecção, mas o vírus latente nos nervos pode se reativar décadas depois; a Shingrix previne essa reativação.",
        "obrigatoria": "Não — recomendação SBIm para ≥ 50 anos, disponível na rede privada",
        "eficacia_numerica": 97,
        "idade_da_1a_dose": "50 anos (população geral); 18 anos (imunodeprimidos)",
        "local_de_aplicacao_no_corpo": "Deltóide (músculo do braço)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC026": {  # MenB
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara); síncope vasovagal (principalmente em adolescentes); convulsão febril (rara em lactentes com febre alta pós-vacina)",
        "precaucoes": "Coadministração com outras vacinas pode aumentar o risco de febre em lactentes — pode ser orientado paracetamol profilático (consultar médico); deitar adolescentes por 15 min após a vacina para evitar síncope; adiar em doença aguda com febre",
        "doses_totais_imunossuprimido": "3 doses independentemente da idade + reforços periódicos (definir com CRIE). Asplênicos e com deficiência de complemento: encaminhar ao CRIE.",
        "restricoes_para_imunossuprimidos": "Pode e deve ser usada (vacina inativada). Asplênicos, com deficiência de complemento e usuários de eculizumabe têm indicação especial — encaminhar ao CRIE para esquema personalizado.",
        "duracao_da_protecao": "Proteção comprovada por ≥ 4 anos após série primária; recomendações de reforço ainda em evolução",
        "mitos_comuns": "A vacina de meningite C já me protege contra todas as meningites; meningite B é muito rara no Brasil, não precisa vacinar",
        "resposta_a_mitos": "A MenC e MenACWY NÃO cobrem o sorogrupo B, responsável por 30-40% das meningites meningocócicas no Brasil. Meningite meningocócica tem mortalidade de 10-15% mesmo com tratamento — a cobertura contra todos os sorogrupos é fundamental.",
        "obrigatoria": "Não — recomendação SBIm (calendário privado); não faz parte do PNI universal",
        "eficacia_numerica": 79,
        "idade_da_1a_dose": "3 meses (recomendação SBIm)",
        "local_de_aplicacao_no_corpo": "Coxa (lactentes e crianças < 1 ano); deltóide (crianças maiores e adultos)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC027": {  # Gardasil 9
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara); síncope vasovagal (frequente em adolescentes — deitar por 15 min após a aplicação); tromboembolismo venoso (raro, sob investigação)",
        "precaucoes": "Deitar o adolescente por 15 minutos após vacinação para evitar síncope e queda; adiar durante gravidez (concluir série após o parto); não é necessário interromper a amamentação",
        "doses_totais_imunossuprimido": "3 doses (0, 2 e 6 meses) independentemente da idade para imunodeprimidos — incluindo HIV positivos",
        "restricoes_para_imunossuprimidos": "Pode ser usada (inativada). HIV positivos: 3 doses sempre, independentemente da contagem de CD4. Monitorar resposta imune quando possível.",
        "duracao_da_protecao": "≥ 12 anos de proteção comprovada em estudos de longa duração; provavelmente vitalícia após série completa",
        "mitos_comuns": "HPV 9 do SUS e da clínica são a mesma vacina; quem já é sexualmente ativo não se beneficia; HPV só causa doença em mulheres; vacina HPV incentiva a promiscuidade",
        "resposta_a_mitos": "A do SUS é quadrivalente (4 tipos); Gardasil 9 cobre 9 tipos — maior proteção. Quem já teve relações ainda se beneficia pois provavelmente não teve todos os 9 tipos. HPV causa câncer de pênis, ânus e orofaringe em homens. Estudos não mostram mudança de comportamento sexual após vacinação.",
        "obrigatoria": "Não (Gardasil 9 — rede privada); SUS oferece HPV quadrivalente obrigatória para 9-14 anos",
        "eficacia_numerica": 97,
        "idade_da_1a_dose": "9 anos",
        "local_de_aplicacao_no_corpo": "Deltóide (músculo do braço)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC028": {  # Mpox
        "efeitos_colaterais_raros_graves": "Miocardite/pericardite (rara, principalmente em jovens do sexo masculino — risco muito menor que com vacinas replicativas antigas); linfadenopatia regional; reação cutânea no local de injeção",
        "precaucoes": "Comunicar ao médico histórico de doença cardíaca antes de vacinar; observar o paciente por 30 minutos após a dose; adiar em doença aguda com febre; verificar se já recebeu vacina de varíola antiga (pode alterar esquema)",
        "doses_totais_imunossuprimido": "Mesmas 2 doses; HIV com CD4 < 200: avaliação caso a caso pelo CRIE; imunossupressão grave: discutir timing com especialista",
        "restricoes_para_imunossuprimidos": "Avaliação individual obrigatória. HIV bem controlado (CD4 > 200 e CV indetectável): pode receber. Imunossupressão grave ativa: avaliar com infectologista. Jynneos é mais segura que vacinas replicativas antigas.",
        "duracao_da_protecao": "Estimativa de 2 anos de proteção robusta; reforço a cada 2 anos para risco contínuo",
        "mitos_comuns": "Mpox é doença exclusiva de homossexuais; a vacina causa mpox ou varíola; Jynneos é a mesma vacina antiga de varíola",
        "resposta_a_mitos": "Mpox afeta qualquer pessoa com contato físico próximo — embora MSH com múltiplos parceiros tenham maior risco no surto atual. Jynneos usa vírus MVA NÃO replicativo — impossível causar mpox ou varíola. É uma vacina de nova geração, muito mais segura que a antiga Vaccinia replicativa.",
        "obrigatoria": "Não — indicação por grupos de risco via CRIE",
        "eficacia_numerica": 85,
        "idade_da_1a_dose": "18 anos",
        "local_de_aplicacao_no_corpo": "Braço (subcutânea, região deltóide) ou antebraço interno (intradérmica — dose menor)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC029": {  # Nirsevimabe
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara); reações cutâneas graves (raras)",
        "precaucoes": "Dose depende do peso ao nascimento: 50 mg para bebês < 5 kg; 100 mg para ≥ 5 kg. Administrar idealmente antes ou no início da temporada de VSR (outono/inverno). Não substitui vacinação materna contra VSR.",
        "doses_totais_imunossuprimido": "1 dose por temporada (mesma para todos); prematuros e crianças com cardiopatia congênita ou displasia broncopulmonar podem necessitar dose anual na 2ª temporada de VSR",
        "restricoes_para_imunossuprimidos": "Pode ser usado em imunodeprimidos — especialmente benéfico; monitorar sinais de infecção respiratória mesmo após o anticorpo, pois proteção é parcial",
        "duracao_da_protecao": "Aproximadamente 5-6 meses (1 temporada de VSR)",
        "mitos_comuns": "Beyfortus é uma vacina e protege permanentemente; se tomou Synagis (palivizumabe) não precisa de Beyfortus",
        "resposta_a_mitos": "Nirsevimabe é um anticorpo pronto (imunização passiva) — não estimula o sistema imune e protege por apenas uma temporada (~5 meses). Palivizumabe (Synagis) e nirsevimabe são diferentes: nirsevimabe tem meia-vida maior, cobre mais cepas e é mais conveniente (1 dose vs mensal).",
        "obrigatoria": "Não ainda — em processo de incorporação ao PNI (CONITEC 2024)",
        "eficacia_numerica": 75,
        "idade_da_1a_dose": "Recém-nascido — pode ser administrado ainda na maternidade",
        "local_de_aplicacao_no_corpo": "Coxa (músculo vasto lateral)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC030": {  # Febre Tifóide
        "efeitos_colaterais_raros_graves": "Anafilaxia (rara); reação local intensa com inchaço > 5 cm (rara, mais comum em quem já teve a doença ou vacinação prévia)",
        "precaucoes": "Oral (Vivotif): não tomar com antibióticos que atuam contra Salmonella; adiar em diarreia ativa; proguanil e mefloquina (antimaláricos) podem reduzir imunidade oral — espaçar por 3 dias. Injetável: nenhuma precaução especial além das gerais.",
        "doses_totais_imunossuprimido": "Injetável Vi-CPS: 1 dose (inativada — segura). Oral Vivotif: CONTRAINDICADA em imunodeprimidos — usar apenas a injetável.",
        "restricoes_para_imunossuprimidos": "Usar EXCLUSIVAMENTE a injetável Vi-CPS — a oral contém bactérias atenuadas vivas e é contraindicada em imunodeprimidos. 1 dose com reforço a cada 3 anos para exposição contínua.",
        "duracao_da_protecao": "Injetável: 2-3 anos; oral: 5 anos. Reforço necessário para viajantes com risco contínuo.",
        "mitos_comuns": "A vacina protege contra qualquer diarreia do viajante; tomei anos atrás e ainda estou protegido; não preciso me preocupar com água e comida se estou vacinado",
        "resposta_a_mitos": "A vacina protege apenas contra Salmonella Typhi — não cobre ETEC, cólera, norovírus e outras causas de diarreia do viajante. A proteção dura 2-3 anos (injetável) — reforço é necessário. Cuidados com higiene alimentar são ESSENCIAIS mesmo com a vacina.",
        "obrigatoria": "Não — indicada para viajantes e trabalhadores em risco",
        "eficacia_numerica": 70,
        "idade_da_1a_dose": "2 anos (injetável); 6 anos (oral)",
        "local_de_aplicacao_no_corpo": "Deltóide (injetável); oral em cápsulas",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC031": {  # Cólera
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara); diarreia intensa (rara)",
        "precaucoes": "Não ingerir alimentos ou medicamentos (exceto água fria/temperatura ambiente) 1 hora antes e depois da dose oral; adiar em diarreia ativa ou gastroenterite aguda; não usar concomitantemente com antibióticos",
        "doses_totais_imunossuprimido": "Mesmas 2-3 doses (inativada — segura para imunodeprimidos); resposta imune pode ser reduzida em imunossupressão grave",
        "restricoes_para_imunossuprimidos": "Pode ser usada (inativada); resposta imune pode ser subótima em imunossupressão grave; discutir com médico. Não há vacina viva de cólera com registro no Brasil.",
        "duracao_da_protecao": "Adultos: 2 anos; crianças 2-6 anos: 6 meses. Reforço necessário para viajantes em risco contínuo.",
        "mitos_comuns": "Vacina de cólera elimina totalmente o risco — não preciso de cuidados com água e comida; cólera foi erradicada do mundo",
        "resposta_a_mitos": "Eficácia de 85% não é 100% — cuidados com água tratada, lavagem das mãos e alimentos cozidos são INDISPENSÁVEIS. Cólera ainda causa surtos globais — Haiti, África subsaariana e partes da Ásia registraram casos recentes.",
        "obrigatoria": "Não — indicada para viajantes e situações especiais",
        "eficacia_numerica": 85,
        "idade_da_1a_dose": "2 anos",
        "local_de_aplicacao_no_corpo": "Oral (solução efervescente — diluir em copo de água fria)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC032": {  # Encefalite Japonesa
        "efeitos_colaterais_raros_graves": "Anafilaxia (rara — pode ocorrer até 10 dias após a dose, diferente de outras vacinas); urticária tardia; angioedema; dor de cabeça intensa",
        "precaucoes": "Observar o paciente por 30 minutos após cada dose; orientar sobre possibilidade de reação tardia (urticária/angioedema) em até 10 dias — procurar atendimento se ocorrer; vacinar com antecedência mínima de 1 semana antes da viagem para completar o esquema",
        "doses_totais_imunossuprimido": "Mesmas 2 doses; imunodeprimidos podem ter resposta imune reduzida — considerar sorologia pós-vacinação em casos de alto risco",
        "restricoes_para_imunossuprimidos": "Pode ser usada (inativada); resposta imune pode ser subótima; avaliar com infectologista para indicação de dose adicional em imunossupressão grave",
        "duracao_da_protecao": "1-2 anos após série primária; reforço único recomendado após 1-2 anos para viajantes com risco contínuo",
        "mitos_comuns": "Vou a Tóquio ou Bangkok — preciso da vacina; qualquer viagem à Ásia requer a vacina de encefalite japonesa",
        "resposta_a_mitos": "Encefalite japonesa tem risco MUITO BAIXO em áreas urbanas e turísticas da Ásia. A vacina é indicada para estadias > 1 mês em áreas rurais (especialmente durante e após monção), trabalho agrícola, e atividades ao ar livre noturnas perto de arrozais ou criação de porcos — não para turismo em capitais asiáticas.",
        "obrigatoria": "Não — indicada para viajantes com risco específico",
        "eficacia_numerica": 96,
        "idade_da_1a_dose": "2 meses (Ixiaro)",
        "local_de_aplicacao_no_corpo": "Deltóide (adultos e crianças > 3 anos); coxa (crianças < 3 anos)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC033": {  # Twinrix
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara); síndrome de Guillain-Barré (associada historicamente à componente Hep B — risco extremamente baixo, < 1:1.000.000)",
        "precaucoes": "Adiar em doença aguda grave com febre; hemodialisados podem necessitar de doses maiores (40 mcg) ou verificação sorológica após a série; verificar sorologia prévia para Hep A e Hep B antes de vacinar em adultos (pode ser desnecessário se já imune)",
        "doses_totais_imunossuprimido": "3 doses padrão; hemodialisados: doses dobradas (ou Twinrix HD) e verificação de anti-HBs após a série — meta: > 10 UI/L",
        "restricoes_para_imunossuprimidos": "Pode ser usada (inativada). Monitorar títulos de anti-HBs após vacinação — resposta pode ser insuficiente. Pode necessitar dose adicional ou revacinação. HIV positivos: geralmente respondem bem se CD4 > 200.",
        "duracao_da_protecao": "Hepatite A: possivelmente vitalícia após série completa; Hepatite B: ≥ 20 anos (anti-HBs > 10 UI/L no pós-vacinação)",
        "mitos_comuns": "Se tomei hepatite B na infância não preciso de Twinrix; Twinrix dá proteção mais fraca que as vacinas separadas; adulto vacinado de Hep B não precisa checar se ainda está protegido",
        "resposta_a_mitos": "Se você já tem imunidade para Hep B (sorologia positiva), basta a vacina isolada de Hep A (e vice-versa). A eficácia do Twinrix é equivalente às vacinas separadas em estudos comparativos. Após 20+ anos, adultos de alto risco (hemodialisados, profissionais de saúde) devem verificar se ainda têm anticorpos suficientes.",
        "obrigatoria": "Não — disponível na rede privada; SUS oferece Hep A e Hep B separadamente de forma gratuita",
        "eficacia_numerica": 95,
        "idade_da_1a_dose": "18 anos (Twinrix Adulto)",
        "local_de_aplicacao_no_corpo": "Deltóide (músculo do braço)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
    "VAC034": {  # PCV15
        "efeitos_colaterais_raros_graves": "Anafilaxia (muito rara); reação local intensa (rara)",
        "precaucoes": "Adiar em doença aguda grave com febre; verificar histórico de vacinação pneumocócica — se já recebeu PCV13: aguardar ≥ 1 ano; se já recebeu PPV23: aguardar ≥ 1 ano antes de dar PCV15",
        "doses_totais_imunossuprimido": "1 dose PCV15 + PPV23 após ≥ 8 semanas (para máxima cobertura). Imunodeprimidos muito graves: avaliar necessidade de 2 doses de PCV15 com médico.",
        "restricoes_para_imunossuprimidos": "Pode e deve ser usada (inativada). Imunodeprimidos têm indicação especial para sequência PCV15 → PPV23. Alguns imunossuprimidos graves (pós-transplante, oncológicos) podem responder menos — verificar com médico.",
        "duracao_da_protecao": "Proteção duradoura; adultos de alto risco podem se beneficiar de PPV23 após 1-5 anos como complemento",
        "mitos_comuns": "Já tomei vacina de pneumonia (PPV23) — não preciso de PCV15; idoso saudável não precisa de vacina contra pneumococo; pneumonia só afeta idosos muito debilitados",
        "resposta_a_mitos": "PPV23 e PCV15 são complementares e não se substituem: PCV15 é conjugada (melhor resposta imune T-dependente, especialmente em idosos); PPV23 cobre mais sorotipos. Para proteção máxima: PCV15 primeiro, depois PPV23. Pneumonia mata mais idosos que gripe — vacinação é essencial.",
        "obrigatoria": "Não — disponível na rede privada; SUS oferece PCV10 (crianças) e PPV23 via CRIE",
        "eficacia_numerica": 75,
        "idade_da_1a_dose": "19 anos (indicação para adultos)",
        "local_de_aplicacao_no_corpo": "Deltóide (músculo do braço)",
        "data_de_validade_da_informacao": "2026-12-31",
    },
}


def main():
    print(f"\n🌿 VacinaFácil AI — Completando {len(COMPLEMENTOS)} vacinas\n")
    ok = 0
    for vid, campos in COMPLEMENTOS.items():
        try:
            supabase.table("vacinas").update(campos).eq("id", vid).execute()
            print(f"   ✅ {vid} — {len(campos)} campos completados")
            ok += 1
        except Exception as e:
            print(f"   ❌ {vid}: {e}")

    print(f"\n{'='*50}")
    print(f"✅ {ok} vacinas 100% completas")
    print("="*50)
    print("\nPróximo passo: python gerar_embeddings.py")


if __name__ == "__main__":
    main()
