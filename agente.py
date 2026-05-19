"""
VacinaFácil AI — Agente de Orientação Vacinal
Uso: python agente.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import anthropic

load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not ANTHROPIC_KEY:
    raise SystemExit("❌ Configure SUPABASE_URL, SUPABASE_ANON_KEY e ANTHROPIC_API_KEY no .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SYSTEM_PROMPT = """\
Você é o VacinaFácil AI, um assistente virtual especializado em orientações sobre vacinação no Brasil.
Você foi desenvolvido como projeto acadêmico para ajudar cidadãos brasileiros a entender o Programa
Nacional de Imunizações (PNI) do Ministério da Saúde.

DIRETRIZES:
- Responda sempre em português brasileiro, de forma clara, amigável e acessível a qualquer público
- Baseie suas respostas nas informações do contexto fornecido (quando disponível)
- Quando a base de conhecimento não tiver a informação, diga isso claramente e oriente a buscar
  uma Unidade Básica de Saúde (UBS) ou profissional de saúde
- NUNCA diagnostique doenças nem substitua o aconselhamento médico profissional
- Para situações de urgência (suspeita de raiva, tétano pós-ferimento, etc.), sempre enfatize
  a necessidade de atendimento médico imediato
- Promova a vacinação com empatia, sem julgamentos a quem tem dúvidas ou hesitação
- Responda de forma objetiva; use listas quando facilitar a leitura

Você tem acesso a informações sobre: vacinas do SUS e rede privada, calendário PNI, perguntas
frequentes, mitos e verdades, atrasos no esquema vacinal, viagem internacional, doenças
preveníveis por vacinas, profilaxia pós-exposição e protocolos históricos.\
"""


def buscar_contexto(pergunta: str, limite: int = 6) -> str:
    """Busca no Supabase os trechos mais relevantes para a pergunta."""
    try:
        res = supabase.rpc("buscar_conhecimento", {
            "query_text": pergunta,
            "limite": limite,
        }).execute()

        if not res.data:
            return ""

        blocos = []
        for item in res.data:
            fonte = item["fonte"].upper()
            titulo = item["titulo"] or ""
            conteudo = item["conteudo"] or ""
            blocos.append(f"[{fonte}] {titulo}\n{conteudo}")

        return "### BASE DE CONHECIMENTO\n\n" + "\n\n---\n\n".join(blocos)

    except Exception as e:
        print(f"\n⚠  Aviso: não foi possível buscar contexto ({e})")
        return ""


def chat():
    historico: list[dict] = []

    print()
    print("=" * 56)
    print("  VacinaFácil AI — Assistente de Orientação Vacinal  ")
    print("=" * 56)
    print("  Tire suas dúvidas sobre vacinas. Digite 'sair' para encerrar.")
    print()

    while True:
        try:
            pergunta = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nAté logo! Mantenha sua vacinação em dia.")
            break

        if not pergunta:
            continue
        if pergunta.lower() in ("sair", "exit", "quit"):
            print("\nAté logo! Mantenha sua vacinação em dia.")
            break

        # RAG: recupera contexto relevante da base de dados
        contexto = buscar_contexto(pergunta)

        # Injeta contexto na mensagem do usuário (invisível ao histórico exibido)
        if contexto:
            mensagem_com_contexto = f"{contexto}\n\n---\n\nPergunta: {pergunta}"
        else:
            mensagem_com_contexto = pergunta

        historico.append({"role": "user", "content": mensagem_com_contexto})

        print("\nVacinaFácil AI: ", end="", flush=True)

        resposta = ""
        try:
            with claude.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=historico,
            ) as stream:
                for trecho in stream.text_stream:
                    print(trecho, end="", flush=True)
                    resposta += trecho
        except Exception as e:
            print(f"\n❌ Erro ao chamar Claude: {e}")
            historico.pop()
            continue

        print("\n")

        # Guarda no histórico a pergunta original (sem contexto injetado)
        historico[-1] = {"role": "user", "content": pergunta}
        historico.append({"role": "assistant", "content": resposta})


if __name__ == "__main__":
    chat()
