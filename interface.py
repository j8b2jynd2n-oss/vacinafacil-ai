"""
VacinaFácil AI — Interface Web
Uso: python interface.py
Acesse: http://localhost:8000
"""

import os
import re
import json
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client, Client
import anthropic
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from pydantic import BaseModel

load_dotenv(override=True)

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_KEY         = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ANTHROPIC_KEY        = os.getenv("ANTHROPIC_API_KEY")
OPENAI_KEY           = os.getenv("OPENAI_API_KEY")
ADMIN_PASSWORD       = os.getenv("ADMIN_PASSWORD", "vacinafacil2025")

if not SUPABASE_URL or not SUPABASE_KEY or not ANTHROPIC_KEY:
    raise SystemExit("❌ Configure SUPABASE_URL, SUPABASE_ANON_KEY e ANTHROPIC_API_KEY no .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Cliente privilegiado — usado APENAS no endpoint /admin (leitura de feedback)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY or SUPABASE_KEY)
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

SYSTEM_PROMPT = """\
Você é o VacinaFácil AI, um assistente virtual especializado em orientações sobre vacinação no Brasil.
Você foi desenvolvido como projeto acadêmico para ajudar cidadãos brasileiros a entender o Programa
Nacional de Imunizações (PNI) do Ministério da Saúde.

REGRAS ANTI-HALLUCINATION:
- Para dados específicos (intervalos entre doses, idades, esquemas exatos): use APENAS o contexto
  da BASE DE CONHECIMENTO. Se não estiver no contexto, diga "não tenho esse dado preciso" e
  oriente a UBS.
- Para orientações gerais do calendário PNI (ex: quais vacinas são recomendadas na gravidez):
  você pode usar seu conhecimento sobre o Programa Nacional de Imunizações do Brasil, deixando
  claro que é orientação geral e recomendando confirmar na UBS.
- NUNCA invente doses, datas, intervalos ou contraindicações específicas sem base no contexto.
- NUNCA diagnostique doenças nem substitua o aconselhamento médico profissional.

DIRETRIZES:
- Responda sempre em português brasileiro, de forma clara, amigável e acessível a qualquer público
- Use linguagem simples, evite termos técnicos sem explicação
- Priorize sempre as informações do contexto da BASE DE CONHECIMENTO quando disponível
- Para situações de urgência (reação alérgica grave, suspeita de raiva, tétano pós-ferimento,
  febre alta após vacina, convulsão), instrua IMEDIATAMENTE a ligar para o SAMU (192) ou
  Bombeiros (193), e mencione o Disque Saúde SUS (136) para dúvidas não urgentes
- Em respostas sobre contraindicações ou efeitos adversos, sempre finalize com orientação à UBS
- Promova a vacinação com empatia, sem julgamentos
- Respostas curtas e objetivas; use listas quando facilitar a leitura\
"""

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def strip_markdown(text: str) -> str:
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'^[-•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'---+', '.', text)
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', ' ', text)
    return text.strip()[:4000]

app = FastAPI(title="VacinaFácil AI")


# ── Models ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: List[Dict] = []

class TTSRequest(BaseModel):
    text: str

class FeedbackRequest(BaseModel):
    pergunta: str
    resposta: str
    avaliacao: bool  # True = 👍  False = 👎


# ── RAG: busca contexto ───────────────────────────────────────

def buscar_contexto(pergunta: str, limite: int = 6) -> str:
    resultados = []

    # 1. Busca semântica (pgvector) — entende sinônimos e intenção
    if openai_client:
        try:
            emb_res = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=pergunta[:8000]
            )
            embedding = emb_res.data[0].embedding
            res = supabase.rpc("buscar_semantico", {
                "query_embedding": embedding,
                "limite": limite,
            }).execute()
            if res.data:
                resultados = res.data
        except Exception:
            pass

    # 2. FTS como complemento (ou fallback se semântica falhou)
    if len(resultados) < 3:
        try:
            res = supabase.rpc("buscar_conhecimento", {
                "query_text": pergunta,
                "limite": limite,
            }).execute()
            if res.data:
                # Adiciona resultados do FTS que não estão nos semânticos
                titulos_ja = {r.get("titulo") for r in resultados}
                for item in res.data:
                    if item.get("titulo") not in titulos_ja:
                        resultados.append(item)
                        if len(resultados) >= limite:
                            break
        except Exception:
            pass

    if not resultados:
        return ""

    blocos = [
        f"[{item['fonte'].upper()}] {item['titulo'] or ''}\n{item['conteudo'] or ''}"
        for item in resultados[:limite]
    ]
    return "### BASE DE CONHECIMENTO\n\n" + "\n\n---\n\n".join(blocos)


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    content = open(os.path.join(STATIC, "index.html"), encoding="utf-8").read()
    return HTMLResponse(content=content, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    })


@app.get("/manifest.json")
def manifest():
    return FileResponse(os.path.join(STATIC, "manifest.json"), media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(os.path.join(STATIC, "sw.js"), media_type="application/javascript")


@app.get("/icon.svg")
def icon():
    return FileResponse(os.path.join(STATIC, "icon.svg"), media_type="image/svg+xml")


@app.post("/chat")
def chat(req: ChatRequest):
    if len(req.message) > 2000:
        raise HTTPException(status_code=400, detail="Mensagem muito longa (máx. 2000 caracteres).")
    def generate():
        try:
            contexto = buscar_contexto(req.message)
            user_content = (
                f"{contexto}\n\n---\n\nPergunta: {req.message}" if contexto else req.message
            )
            messages = list(req.history)
            messages.append({"role": "user", "content": user_content})

            with claude.messages.stream(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/tts")
def tts(req: TTSRequest):
    if not openai_client:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY não configurada no .env")
    audio = openai_client.audio.speech.create(
        model="tts-1-hd",
        voice="nova",
        input=strip_markdown(req.text),
    )
    return StreamingResponse(audio.iter_bytes(1024), media_type="audio/mpeg")


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    try:
        supabase_admin.table("feedback").insert({
            "pergunta":  req.pergunta[:2000],
            "resposta":  req.resposta[:4000],
            "avaliacao": req.avaliacao,
        }).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin", response_class=HTMLResponse)
def admin(senha: str = Query("")):
    if senha != ADMIN_PASSWORD:
        return HTMLResponse(
            "<!DOCTYPE html><html><body style='font-family:system-ui;padding:40px;text-align:center'>"
            "<h2>🔒 Acesso negado</h2><p>Use <code>?senha=suasenha</code> na URL.</p></body></html>",
            status_code=403,
        )
    try:
        # Usa service key indiretamente via anon key com RLS — apenas leitura admin
        # Para produção real, use SUPABASE_SERVICE_KEY aqui
        res = supabase_admin.table("feedback").select("*").order("created_at", desc=True).limit(500).execute()
        rows = res.data or []
        total     = len(rows)
        positivos = sum(1 for r in rows if r.get("avaliacao"))
        negativos = total - positivos
        pct       = round(positivos / total * 100) if total else 0

        linhas = ""
        for r in rows[:100]:
            emoji = "👍" if r.get("avaliacao") else "👎"
            dt    = (r.get("created_at") or "")[:16].replace("T", " ")
            perg  = (r.get("pergunta") or "")[:90]
            linhas += f"<tr><td>{emoji}</td><td>{dt}</td><td title='{perg}'>{perg}</td></tr>\n"

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin — VacinaFácil AI</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#f0fdf4;padding:24px;max-width:960px;margin:auto;color:#1a1a1a}}
  h1{{color:#085C3C;font-size:24px;margin-bottom:4px}}
  p.sub{{color:#6b7280;font-size:14px;margin-bottom:24px}}
  .cards{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:28px}}
  .card{{background:#fff;border-radius:14px;padding:20px 26px;box-shadow:0 1px 6px rgba(0,0,0,.08);min-width:140px;text-align:center}}
  .card h2{{font-size:38px;margin:0 0 4px;color:#0B7A50}}
  .card p{{margin:0;font-size:13px;color:#6b7280}}
  .pct{{font-size:38px;margin:0 0 4px;color:{('#15803d' if pct>=70 else '#d97706' if pct>=40 else '#dc2626')}}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.07)}}
  th{{background:#0B7A50;color:#fff;padding:11px 14px;text-align:left;font-size:13px}}
  td{{padding:10px 14px;font-size:13px;border-bottom:1px solid #f3f4f6}}
  tr:last-child td{{border:none}}
  tr:hover td{{background:#f0fdf4}}
</style>
</head>
<body>
<h1>📊 VacinaFácil AI — Dashboard</h1>
<p class="sub">Dados de feedback dos usuários (últimas 100 avaliações exibidas)</p>
<div class="cards">
  <div class="card"><h2>{total}</h2><p>Avaliações totais</p></div>
  <div class="card"><h2>{positivos} 👍</h2><p>Respostas úteis</p></div>
  <div class="card"><h2>{negativos} 👎</h2><p>Melhoráveis</p></div>
  <div class="card"><p class="pct">{pct}%</p><p>Satisfação</p></div>
</div>
<table>
  <thead><tr><th>Avaliação</th><th>Data / Hora</th><th>Pergunta</th></tr></thead>
  <tbody>{linhas if linhas else '<tr><td colspan="3" style="text-align:center;color:#9ca3af;padding:24px">Nenhuma avaliação ainda.</td></tr>'}</tbody>
</table>
</body>
</html>"""
    except Exception as e:
        return HTMLResponse(f"<pre style='padding:24px'>Erro: {e}</pre>", status_code=500)


if __name__ == "__main__":
    import uvicorn
    print("\n🌿 VacinaFácil AI — Interface Web")
    print("   Acesse: http://localhost:8000")
    print("   Admin:  http://localhost:8000/admin?senha=vacinafacil2025\n")
    # access_log=False: não persiste perguntas dos usuários nos logs (LGPD)
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False, log_level="warning")
