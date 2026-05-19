"""
VacinaFácil AI — Gerador de Embeddings Semânticos
Gera embeddings para todos os registros da base e armazena no Supabase.

Pré-requisito: execute schema_embeddings.sql no Supabase antes.
Uso: python gerar_embeddings.py
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv(override=True)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Mapeamento: tabela → campos de título e conteúdo
TABELAS = {
    "vacinas":       ("nome",    "conteudo"),
    "faq":           ("pergunta","resposta"),
    "mitos":         ("mito",    "esclarecimento"),
    "doencas":       ("nome",    "conteudo"),
    "pos_exposicao": ("situacao","protocolo"),
}


def gerar_embedding(texto: str) -> list[float]:
    res = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texto[:8000]
    )
    return res.data[0].embedding


def main():
    print("🌿 VacinaFácil AI — Gerador de Embeddings")
    print("Limpando embeddings antigos...")
    supabase.table("base_embeddings").delete().neq(
        "id", "00000000-0000-0000-0000-000000000000"
    ).execute()

    total = 0
    erros = 0

    for tabela, (campo_titulo, campo_conteudo) in TABELAS.items():
        print(f"\n📋 Processando: {tabela}")
        try:
            res = supabase.table(tabela).select("*").execute()
            if not res.data:
                print(f"   (vazia)")
                continue
            for row in res.data:
                titulo   = str(row.get(campo_titulo)   or "").strip()
                conteudo = str(row.get(campo_conteudo) or "").strip()
                if not conteudo:
                    continue
                texto_completo = f"{titulo}\n{conteudo}".strip()
                try:
                    embedding = gerar_embedding(texto_completo)
                    supabase.table("base_embeddings").insert({
                        "fonte":     tabela,
                        "titulo":    titulo[:500]  if titulo   else None,
                        "conteudo":  conteudo[:4000],
                        "embedding": embedding,
                    }).execute()
                    total += 1
                    print(f"   ✓ {titulo[:60] or '(sem título)'}")
                    time.sleep(0.05)  # evita rate limit
                except Exception as e:
                    erros += 1
                    print(f"   ✗ Erro em '{titulo[:40]}': {e}")
        except Exception as e:
            print(f"   ✗ Erro ao ler tabela {tabela}: {e}")

    print(f"\n{'─'*40}")
    print(f"✅ {total} embeddings gerados com sucesso.")
    if erros:
        print(f"⚠️  {erros} erros (verifique acima).")
    print("\nBusca semântica pronta! Reinicie o interface.py.")


if __name__ == "__main__":
    main()
