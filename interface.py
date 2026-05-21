"""
VacinaFácil AI — Interface Web
Uso: python interface.py
Acesse: http://localhost:8000
"""

import os
import re
import json
from typing import List, Dict
from datetime import datetime, timedelta, timezone
from collections import Counter
from dotenv import load_dotenv
from supabase import create_client, Client
import anthropic
from openai import OpenAI
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse, Response
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
def index(request: Request):
    base = str(request.base_url).rstrip("/")
    content = open(os.path.join(STATIC, "index.html"), encoding="utf-8").read()
    # Substitui placeholder pela URL real do servidor (OG tags, WhatsApp share, etc.)
    content = content.replace("https://vacinafacil-ai.onrender.com", base)
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


@app.get("/og.svg")
def og_image():
    """Imagem Open Graph para preview no WhatsApp, LinkedIn e redes sociais."""
    svg = """\
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#085C3C"/>
      <stop offset="60%"  stop-color="#0f9960"/>
      <stop offset="100%" stop-color="#1aaa6e"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <!-- círculos decorativos -->
  <circle cx="1130" cy="70"  r="200" fill="rgba(255,255,255,0.04)"/>
  <circle cx="40"   cy="590" r="150" fill="rgba(255,255,255,0.04)"/>
  <!-- ícone -->
  <rect x="80" y="195" width="130" height="130" rx="32" fill="rgba(255,255,255,0.15)"/>
  <text x="145" y="285" font-size="76" text-anchor="middle"
        font-family="Apple Color Emoji,Segoe UI Emoji,Noto Color Emoji,sans-serif">&#x1F489;</text>
  <!-- título -->
  <text x="240" y="268"
        font-family="Arial,Helvetica,sans-serif" font-size="68" font-weight="800"
        fill="#ffffff" letter-spacing="-1">VacinaF&#xe1;cil</text>
  <text x="240" y="340"
        font-family="Arial,Helvetica,sans-serif" font-size="68" font-weight="800"
        fill="#a7f3d0" letter-spacing="-1">AI</text>
  <!-- tagline -->
  <text x="80" y="418"
        font-family="Arial,Helvetica,sans-serif" font-size="26"
        fill="rgba(255,255,255,0.85)">Tire d&#xfa;vidas sobre vacinas &#x2014; gratuito e baseado no SUS</text>
  <!-- selos -->
  <rect x="80"  y="450" width="210" height="42" rx="21" fill="rgba(255,255,255,0.15)"/>
  <text x="185" y="476" text-anchor="middle"
        font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="600" fill="#ffffff">&#x1F1E7;&#x1F1F7; Dados do SUS</text>
  <rect x="304" y="450" width="200" height="42" rx="21" fill="rgba(255,255,255,0.15)"/>
  <text x="404" y="476" text-anchor="middle"
        font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="600" fill="#ffffff">&#x2705; 100% gratuito</text>
  <rect x="518" y="450" width="200" height="42" rx="21" fill="rgba(255,255,255,0.15)"/>
  <text x="618" y="476" text-anchor="middle"
        font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="600" fill="#ffffff">&#x1F512; Sem cadastro</text>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.post("/push/subscribe")
def push_subscribe():
    """Endpoint de subscrição push — será ativado com pywebpush + VAPID na próxima sprint."""
    raise HTTPException(status_code=501, detail="Push notifications em desenvolvimento — disponível em breve.")


@app.post("/chat")
def chat(req: ChatRequest):
    if len(req.message) > 2000:
        raise HTTPException(status_code=400, detail="Mensagem muito longa (máx. 2000 caracteres).")

    # Log anônimo para analytics (LGPD: sem IP, sem dados pessoais, máx. 200 chars)
    try:
        supabase_admin.table("queries_log").insert({
            "pergunta": req.message[:200]
        }).execute()
    except Exception:
        pass  # Analytics nunca bloqueia o chat

    def generate():
        try:
            contexto = buscar_contexto(req.message)

            # Campanhas ativas — injeta no contexto para o AI mencionar proativamente
            campanhas_ctx = ""
            try:
                hoje = datetime.now(timezone.utc).date().isoformat()
                cr = supabase.table("campanhas").select(
                    "titulo,descricao,publico_alvo,periodo"
                ).eq("ativo", True).lte("data_inicio", hoje).gte("data_fim", hoje).execute()
                if cr.data:
                    linhas = "\n".join(
                        f"- {c['titulo']}: {c.get('descricao','')} | "
                        f"Público: {c.get('publico_alvo','')} | {c.get('periodo','')}"
                        for c in cr.data
                    )
                    campanhas_ctx = (
                        "### CAMPANHAS DE VACINAÇÃO ATIVAS AGORA\n"
                        f"{linhas}\n\n"
                    )
            except Exception:
                pass

            base = f"{campanhas_ctx}{contexto}" if contexto else campanhas_ctx
            user_content = (
                f"{base}\n\n---\n\nPergunta: {req.message}" if base else req.message
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


@app.get("/campanhas")
def listar_campanhas():
    """Retorna campanhas de vacinação ativas hoje (usada pelo frontend)."""
    try:
        hoje = datetime.now(timezone.utc).date().isoformat()
        res = supabase.table("campanhas").select(
            "id,titulo,descricao,publico_alvo,periodo,urgente,fonte_url"
        ).eq("ativo", True).lte("data_inicio", hoje).gte("data_fim", hoje).execute()
        return {"campanhas": res.data or []}
    except Exception:
        return {"campanhas": []}


@app.get("/privacidade", response_class=HTMLResponse)
def privacidade():
    ano = datetime.now(timezone.utc).year
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Política de Privacidade — VacinaFácil AI</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0fdf4;color:#1a1a1a;padding:0}}
  .header{{background:linear-gradient(135deg,#085C3C,#0B7A50);color:#fff;padding:32px 24px 28px;text-align:center}}
  .header h1{{font-size:22px;margin-bottom:6px}}
  .header p{{font-size:14px;opacity:.85}}
  .content{{max-width:760px;margin:0 auto;padding:32px 24px}}
  h2{{color:#085C3C;font-size:17px;margin:28px 0 10px;padding-bottom:6px;border-bottom:2px solid #d1fae5}}
  p,li{{font-size:14px;line-height:1.7;color:#374151;margin-bottom:10px}}
  ul{{padding-left:20px;margin-bottom:10px}}
  .badge{{display:inline-block;background:#d1fae5;color:#065f46;font-size:12px;font-weight:600;padding:4px 10px;border-radius:20px;margin-bottom:8px}}
  .highlight{{background:#fff;border-left:4px solid #0B7A50;padding:14px 18px;border-radius:0 10px 10px 0;margin:14px 0}}
  .footer{{text-align:center;padding:24px;font-size:12px;color:#9ca3af;border-top:1px solid #e5e7eb;margin-top:32px}}
  a{{color:#0B7A50;text-decoration:none}}
  a:hover{{text-decoration:underline}}
</style>
</head>
<body>
<div class="header">
  <h1>🔒 Política de Privacidade</h1>
  <p>VacinaFácil AI — Última atualização: maio/{ano}</p>
</div>
<div class="content">

  <div class="highlight">
    <strong>Resumo:</strong> O VacinaFácil AI <strong>não coleta dados pessoais identificáveis</strong>.
    Não exigimos cadastro, não registramos nome, CPF, e-mail ou endereço IP.
    Perguntas podem ser armazenadas de forma anônima exclusivamente para melhorar o serviço.
  </div>

  <h2>1. Quem somos</h2>
  <p>O <strong>VacinaFácil AI</strong> é um assistente virtual de orientação vacinal desenvolvido como
  projeto de pesquisa e inovação em saúde pública, com foco no apoio ao
  Programa Nacional de Imunizações (PNI) do Ministério da Saúde do Brasil.</p>
  <p>Controlador dos dados: Equipe VacinaFácil AI &mdash; contato: <a href="mailto:vacinafacil@proton.me">vacinafacil@proton.me</a></p>

  <h2>2. Dados coletados</h2>
  <span class="badge">Mínimo necessário</span>
  <ul>
    <li><strong>Texto das perguntas (anônimo):</strong> Os primeiros 200 caracteres de cada pergunta
    são armazenados sem qualquer identificador de usuário, sem IP e sem dados de navegação.
    Finalidade: analisar tópicos mais consultados e melhorar as respostas.</li>
    <li><strong>Avaliações voluntárias (👍/👎):</strong> Quando o usuário avalia uma resposta,
    armazenamos a pergunta, a resposta gerada e a nota. Não há identificação do avaliador.</li>
    <li><strong>Histórico local:</strong> As últimas perguntas são salvas <em>apenas no seu dispositivo</em>
    (localStorage), nunca em nossos servidores.</li>
  </ul>
  <p><strong>Não coletamos:</strong> nome, CPF, RG, e-mail, telefone, endereço IP, localização,
  cookies de rastreamento, dados de saúde pessoais.</p>

  <h2>3. Finalidade do tratamento</h2>
  <ul>
    <li>Melhoria contínua das respostas e da base de conhecimento vacinal</li>
    <li>Identificação de lacunas de informação mais demandadas pela população</li>
    <li>Pesquisa e desenvolvimento em saúde pública (anonimizado e agregado)</li>
  </ul>

  <h2>4. Base legal (LGPD — Lei 13.709/2018)</h2>
  <p>O tratamento de dados se apoia nos seguintes fundamentos:</p>
  <ul>
    <li><strong>Art. 7º, II</strong> — Cumprimento de obrigação legal (dados mínimos para operação)</li>
    <li><strong>Art. 7º, IV</strong> — Execução de políticas públicas de saúde</li>
    <li><strong>Art. 7º, IX</strong> — Legítimo interesse do controlador (melhoria do serviço público)</li>
  </ul>

  <h2>5. Compartilhamento de dados</h2>
  <p>Os dados anônimos <strong>não são vendidos, alugados ou compartilhados</strong> com terceiros
  para fins comerciais. Podem ser utilizados em publicações acadêmicas em formato agregado e
  sem identificação individual.</p>
  <p>Infraestrutura: <a href="https://supabase.com/privacy" target="_blank">Supabase</a> (banco de dados, GDPR-compliant) e
  <a href="https://openai.com/policies/privacy-policy" target="_blank">OpenAI</a> (embeddings semânticos).</p>

  <h2>6. Retenção de dados</h2>
  <p>Os registros de perguntas anônimas são mantidos por no máximo <strong>90 dias</strong>,
  após os quais são deletados automaticamente. Avaliações de feedback são retidas por
  <strong>12 meses</strong> para fins de pesquisa.</p>

  <h2>7. Seus direitos (Art. 18 LGPD)</h2>
  <p>Como os dados coletados são <strong>anonimizados</strong> (não é possível identificar o titular),
  a maioria dos direitos de acesso, correção e exclusão não se aplica diretamente.
  No entanto, você pode:</p>
  <ul>
    <li>Solicitar informações sobre quais dados são coletados</li>
    <li>Solicitar a eliminação de eventuais dados associáveis a você</li>
    <li>Revogar consentimento a qualquer momento (basta não utilizar o serviço)</li>
  </ul>
  <p>Para exercer seus direitos: <a href="mailto:vacinafacil@proton.me">vacinafacil@proton.me</a></p>

  <h2>8. Segurança</h2>
  <p>Adotamos medidas técnicas e organizacionais compatíveis com o estado da arte:</p>
  <ul>
    <li>Conexões criptografadas (HTTPS/TLS)</li>
    <li>Controle de acesso por chaves de API com separação de privilégios (anon key vs. service key)</li>
    <li>Row Level Security (RLS) no banco de dados</li>
    <li>Ausência de dados sensíveis de saúde nos registros</li>
  </ul>

  <h2>9. Cookies e rastreamento</h2>
  <p>O VacinaFácil AI <strong>não usa cookies de rastreamento</strong>. Utilizamos apenas
  <code>localStorage</code> do navegador para funcionalidades locais (histórico de perguntas,
  preferências de acessibilidade e consentimento LGPD) que <strong>nunca saem do seu dispositivo</strong>.</p>

  <h2>10. Alterações nesta política</h2>
  <p>Eventuais alterações serão publicadas nesta página. O uso continuado do serviço após
  a publicação implica aceitação da política atualizada.</p>

  <h2>11. Contato e Encarregado (DPO)</h2>
  <p>Para dúvidas, solicitações ou reclamações relacionadas a privacidade e proteção de dados:</p>
  <ul>
    <li>E-mail: <a href="mailto:vacinafacil@proton.me">vacinafacil@proton.me</a></li>
    <li>Autoridade supervisora: <a href="https://www.gov.br/anpd" target="_blank">ANPD — Autoridade Nacional de Proteção de Dados</a></li>
  </ul>

</div>
<div class="footer">
  &copy; {ano} VacinaFácil AI &mdash; Projeto de pesquisa em saúde pública &mdash;
  <a href="/">Voltar ao assistente</a>
</div>
</body>
</html>""")


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

    today = datetime.now(timezone.utc).date()

    # ── Feedback ──────────────────────────────────────────────────
    try:
        fb_res  = supabase_admin.table("feedback").select("*").order("created_at", desc=True).limit(500).execute()
        rows_fb = fb_res.data or []
    except Exception:
        rows_fb = []

    total_fb  = len(rows_fb)
    positivos = sum(1 for r in rows_fb if r.get("avaliacao"))
    negativos = total_fb - positivos
    pct_sat   = round(positivos / total_fb * 100) if total_fb else 0

    # ── Queries analytics ─────────────────────────────────────────
    total_queries = queries_hoje = 0
    day_data      = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    day_data      = [(d, 0) for d in reversed(day_data)]
    top_topics    : list = []
    recent_q_rows : list = []
    analytics_ok  = False
    max_day = max_topic = 1

    try:
        week_start = (today - timedelta(days=6)).isoformat()

        # Total de consultas
        tq = supabase_admin.table("queries_log").select("id", count="exact").execute()
        total_queries = tq.count or 0

        # Consultas hoje
        thq = supabase_admin.table("queries_log").select("id", count="exact").gte("created_at", today.isoformat()).execute()
        queries_hoje = thq.count or 0

        # Consultas por dia (últimos 7 dias)
        wq = supabase_admin.table("queries_log").select("created_at").gte("created_at", week_start).execute()
        dcounts = Counter(r["created_at"][:10] for r in (wq.data or []))
        days_list = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        day_data  = [(d, dcounts.get(d, 0)) for d in days_list]
        max_day   = max((c for _, c in day_data), default=1) or 1

        # Tópicos mais pesquisados (últimas 500 queries)
        TOPICOS = [
            "gripe", "influenza", "covid", "hepatite", "febre amarela",
            "tétano", "sarampo", "HPV", "dengue", "pólio", "poliomielite",
            "varicela", "catapora", "pneumo", "meningite", "raiva", "BCG",
            "rotavírus", "herpes zóster", "mpox", "tuberculose",
        ]
        tqq = supabase_admin.table("queries_log").select("pergunta").order("created_at", desc=True).limit(500).execute()
        tcounts: Counter = Counter()
        for row in (tqq.data or []):
            q = (row.get("pergunta") or "").lower()
            for t in TOPICOS:
                if t.lower() in q:
                    tcounts[t] += 1
        top_topics = tcounts.most_common(8)
        max_topic  = max((c for _, c in top_topics), default=1) or 1

        # Consultas recentes
        rq = supabase_admin.table("queries_log").select("*").order("created_at", desc=True).limit(15).execute()
        recent_q_rows = rq.data or []

        analytics_ok = True
    except Exception:
        pass  # tabela queries_log ainda não foi criada

    # ── HTML fragments ────────────────────────────────────────────

    # Barras de dias
    bar_days = ""
    for date_str, count in day_data:
        try:
            dt    = datetime.fromisoformat(date_str)
            label = f"{dt.day:02d}/{dt.month:02d}"
        except Exception:
            label = date_str[-5:]
        pct = round(count / max_day * 100) if max_day else 0
        bar_days += (
            f"<div class='brow'><span class='blbl'>{label}</span>"
            f"<div class='btrk'><div class='bfil' style='width:{pct}%'></div></div>"
            f"<span class='bval'>{count}</span></div>"
        )

    # Barras de tópicos
    bar_topics = ""
    for topic, count in top_topics:
        pct = round(count / max_topic * 100) if max_topic else 0
        bar_topics += (
            f"<div class='brow'><span class='blbl' style='text-transform:capitalize;width:100px'>{topic}</span>"
            f"<div class='btrk'><div class='bfil2' style='width:{pct}%'></div></div>"
            f"<span class='bval'>{count}</span></div>"
        )
    if not bar_topics:
        bar_topics = "<p style='color:#9ca3af;font-size:13px;padding:8px 0'>Dados insuficientes ainda</p>"

    # Linhas de consultas recentes
    rq_linhas = ""
    for r in recent_q_rows:
        dt = (r.get("created_at") or "")[:16].replace("T", " ")
        q  = (r.get("pergunta") or "")[:90]
        rq_linhas += f"<tr><td>{dt}</td><td title='{q}'>{q}</td></tr>"
    if not rq_linhas:
        rq_linhas = "<tr><td colspan='2' style='text-align:center;color:#9ca3af;padding:24px'>Nenhuma consulta registrada ainda.</td></tr>"

    # Linhas de feedback
    fb_linhas = ""
    for r in rows_fb[:20]:
        emoji = "👍" if r.get("avaliacao") else "👎"
        dt    = (r.get("created_at") or "")[:16].replace("T", " ")
        perg  = (r.get("pergunta") or "")[:90]
        fb_linhas += f"<tr><td>{emoji}</td><td>{dt}</td><td title='{perg}'>{perg}</td></tr>"
    if not fb_linhas:
        fb_linhas = "<tr><td colspan='3' style='text-align:center;color:#9ca3af;padding:24px'>Nenhuma avaliação ainda.</td></tr>"

    sat_color        = '#15803d' if pct_sat >= 70 else '#d97706' if pct_sat >= 40 else '#dc2626'
    analytics_notice = (
        "<div class='notice'>⚠️ Tabela <code>queries_log</code> não encontrada. "
        "Execute <strong>schema_analytics.sql</strong> no Supabase para ativar o analytics de consultas.</div>"
        if not analytics_ok else ""
    )
    agora = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin — VacinaFácil AI</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;background:#f0fdf4;padding:24px;color:#1a1a1a;min-height:100vh}}
  .wrap{{max-width:1100px;margin:0 auto}}
  h1{{color:#085C3C;font-size:22px;margin-bottom:2px}}
  .sub{{color:#6b7280;font-size:13px;margin-bottom:20px}}
  .sub a{{color:#0B7A50;text-decoration:none;font-weight:600}}
  .notice{{background:#fef9c3;border:1px solid #fde68a;border-radius:10px;padding:12px 16px;font-size:13px;margin-bottom:20px;color:#92400e}}
  .cards{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px}}
  .card{{background:#fff;border-radius:14px;padding:16px 20px;box-shadow:0 1px 6px rgba(0,0,0,.08);min-width:120px;text-align:center;flex:1}}
  .card h2{{font-size:30px;margin:0 0 4px;color:#0B7A50;font-weight:700}}
  .card p{{margin:0;font-size:12px;color:#6b7280}}
  .sat{{font-size:30px;margin:0 0 4px;color:{sat_color};font-weight:700}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}}
  @media(max-width:680px){{.grid2{{grid-template-columns:1fr}}}}
  .panel{{background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 1px 6px rgba(0,0,0,.07)}}
  .panel h3{{font-size:13px;font-weight:600;color:#374151;margin-bottom:14px;text-transform:uppercase;letter-spacing:.5px}}
  .brow{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
  .blbl{{font-size:12px;color:#6b7280;width:44px;flex-shrink:0;text-align:right}}
  .btrk{{flex:1;background:#f3f4f6;border-radius:6px;height:16px;overflow:hidden}}
  .bfil{{height:100%;background:linear-gradient(90deg,#0B7A50,#34d399);border-radius:6px}}
  .bfil2{{height:100%;background:linear-gradient(90deg,#2563eb,#60a5fa);border-radius:6px}}
  .bval{{font-size:12px;color:#374151;font-weight:700;width:24px;text-align:right;flex-shrink:0}}
  .stitle{{font-size:14px;font-weight:600;color:#085C3C;margin:20px 0 10px}}
  table{{width:100%;border-collapse:collapse}}
  th{{background:#0B7A50;color:#fff;padding:9px 12px;text-align:left;font-size:12px;font-weight:600}}
  td{{padding:9px 12px;font-size:12px;border-bottom:1px solid #f3f4f6;color:#374151}}
  tr:last-child td{{border:none}}
  tr:hover td{{background:#f0fdf4}}
</style>
</head>
<body>
<div class="wrap">
<h1>📊 VacinaFácil AI — Dashboard</h1>
<p class="sub">Atualizado em {agora} UTC &nbsp;·&nbsp; <a href="?senha={senha}">↻ Atualizar</a></p>
{analytics_notice}

<div class="cards">
  <div class="card"><h2>{total_queries}</h2><p>Total de consultas</p></div>
  <div class="card"><h2>{queries_hoje}</h2><p>Consultas hoje</p></div>
  <div class="card"><h2>{total_fb}</h2><p>Avaliações</p></div>
  <div class="card"><h2>{positivos} 👍</h2><p>Úteis</p></div>
  <div class="card"><h2>{negativos} 👎</h2><p>Melhoráveis</p></div>
  <div class="card"><p class="sat">{pct_sat}%</p><p>Satisfação</p></div>
</div>

<div class="grid2">
  <div class="panel">
    <h3>📅 Consultas por dia — últimos 7 dias</h3>
    {bar_days if bar_days else "<p style='color:#9ca3af;font-size:13px'>Sem dados</p>"}
  </div>
  <div class="panel">
    <h3>💉 Tópicos mais pesquisados</h3>
    {bar_topics}
  </div>
</div>

<p class="stitle">🕐 Consultas recentes (anonimizadas)</p>
<div class="panel" style="margin-bottom:20px">
  <table>
    <thead><tr><th style="width:140px">Data / Hora</th><th>Pergunta</th></tr></thead>
    <tbody>{rq_linhas}</tbody>
  </table>
</div>

<p class="stitle">💬 Feedback recente</p>
<div class="panel">
  <table>
    <thead><tr><th style="width:40px">Nota</th><th style="width:130px">Data / Hora</th><th>Pergunta</th></tr></thead>
    <tbody>{fb_linhas}</tbody>
  </table>
</div>
</div>
</body>
</html>"""


# ── Curadoria ─────────────────────────────────────────────────

def _esc(s) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def _tf(name: str, label: str, val, rows: int = 3) -> str:
    return (
        f"<div class='cf'><label class='cl'>{label}</label>"
        f"<textarea name='{name}' rows='{rows}' class='ca'>{_esc(val)}</textarea></div>"
    )


@app.get("/curadoria", response_class=HTMLResponse)
def curadoria(senha: str = Query(""), msg: str = Query("")):
    if senha != ADMIN_PASSWORD:
        return HTMLResponse(
            "<!DOCTYPE html><html><body style='font-family:system-ui;padding:40px;text-align:center'>"
            "<h2>🔒 Acesso negado</h2><p>Use <code>?senha=suasenha</code> na URL.</p></body></html>",
            status_code=403,
        )

    vacinas: list = []
    faqs:    list = []
    mitos:   list = []

    try:
        r = supabase_admin.table("vacinas").select(
            "id,nome_da_vacina,disponivel_no_sus,"
            "resposta_padrao_sugerida,esquema_de_vacinacao,"
            "contraindicacoes_absolutas,efeitos_colaterais_comuns,"
            "precaucoes,duracao_da_protecao,eficacia_numerica,observacoes_internas"
        ).order("id").execute()
        vacinas = r.data or []
    except Exception:
        pass

    try:
        r = supabase_admin.table("faq").select("id,pergunta,resposta").order("pergunta").execute()
        faqs = r.data or []
    except Exception:
        pass

    try:
        r = supabase_admin.table("mitos").select(
            "id,mito_como_circula,resposta_baseada_em_evidencia"
        ).order("mito_como_circula").execute()
        mitos = r.data or []
    except Exception:
        pass

    # ── HTML fragments ──────────────────────────────────────────
    def vac_rows() -> str:
        html = ""
        for v in vacinas:
            vid  = _esc(v.get("id", ""))
            nome = _esc(v.get("nome_da_vacina", ""))
            sus  = v.get("disponivel_no_sus") or ""
            sus_badge = (
                f"<span style='color:#059669;font-weight:600'>{_esc(sus)}</span>"
                if sus else "<span style='color:#9ca3af'>—</span>"
            )
            fields_html = (
                _tf("resposta_padrao_sugerida", "Resposta padrão sugerida", v.get("resposta_padrao_sugerida"), 5) +
                _tf("esquema_de_vacinacao",     "Esquema de vacinação",     v.get("esquema_de_vacinacao"),     3) +
                _tf("contraindicacoes_absolutas","Contraindicações absolutas",v.get("contraindicacoes_absolutas"),3) +
                _tf("efeitos_colaterais_comuns", "Efeitos colaterais comuns", v.get("efeitos_colaterais_comuns"), 3) +
                _tf("precaucoes",               "Precauções",               v.get("precaucoes"),               2) +
                _tf("duracao_da_protecao",      "Duração da proteção",      v.get("duracao_da_protecao"),      1) +
                _tf("eficacia_numerica",        "Eficácia (%)",             v.get("eficacia_numerica"),        1) +
                _tf("observacoes_internas",     "Observações internas",     v.get("observacoes_internas"),     2)
            )
            html += (
                f"<tr>"
                f"<td><strong>{nome}</strong></td>"
                f"<td>{sus_badge}</td>"
                f"<td><button type='button' class='ebtn' data-id='{vid}'>✏️ Editar</button></td>"
                f"</tr>"
                f"<tr class='erow' data-id='{vid}'>"
                f"<td colspan='3' style='padding:0;background:#f8fffe'>"
                f"<form method='POST' action='/curadoria/salvar-vacina'>"
                f"<input type='hidden' name='senha' value='{senha}'>"
                f"<input type='hidden' name='vid' value='{vid}'>"
                f"<div class='efhdr'><strong>✏️ {nome}</strong>"
                f"<button type='submit' class='sbtn'>💾 Salvar alterações</button></div>"
                f"<div class='efields'>{fields_html}</div>"
                f"</form></td></tr>"
            )
        return html

    def faq_rows() -> str:
        html = ""
        for f in faqs:
            fid  = _esc(f.get("id", ""))
            perg = _esc(f.get("pergunta", ""))
            html += (
                f"<tr>"
                f"<td style='max-width:500px'>{perg}</td>"
                f"<td style='white-space:nowrap'>"
                f"<button type='button' class='ebtn' data-faq='{fid}'>✏️</button> "
                f"<a href='/curadoria/del-faq?id={fid}&senha={senha}'"
                f"   onclick=\"return confirm('Deletar esta FAQ?')\" class='del-lnk'>🗑️</a>"
                f"</td></tr>"
                f"<tr class='efrow' data-faq='{fid}'>"
                f"<td colspan='2' style='padding:0;background:#f8fffe'>"
                f"<form method='POST' action='/curadoria/salvar-faq'>"
                f"<input type='hidden' name='senha' value='{senha}'>"
                f"<input type='hidden' name='fid' value='{fid}'>"
                f"<div class='efields'>"
                f"{_tf('pergunta','Pergunta',f.get('pergunta'),2)}"
                f"{_tf('resposta','Resposta',f.get('resposta'),5)}"
                f"</div>"
                f"<div style='padding:10px 16px;text-align:right'>"
                f"<button type='submit' class='sbtn'>💾 Salvar</button></div>"
                f"</form></td></tr>"
            )
        return html

    def mito_rows() -> str:
        html = ""
        for m in mitos:
            mid  = _esc(m.get("id", ""))
            mito = _esc(m.get("mito_como_circula", ""))
            html += (
                f"<tr>"
                f"<td style='max-width:500px'>{mito}</td>"
                f"<td><button type='button' class='ebtn' data-mito='{mid}'>✏️</button></td>"
                f"</tr>"
                f"<tr class='emrow' data-mito='{mid}'>"
                f"<td colspan='2' style='padding:0;background:#f8fffe'>"
                f"<form method='POST' action='/curadoria/salvar-mito'>"
                f"<input type='hidden' name='senha' value='{senha}'>"
                f"<input type='hidden' name='mid' value='{mid}'>"
                f"<div class='efields'>"
                f"{_tf('mito_como_circula','Mito (como circula)',m.get('mito_como_circula'),2)}"
                f"{_tf('resposta_baseada_em_evidencia','Resposta baseada em evidência',m.get('resposta_baseada_em_evidencia'),5)}"
                f"</div>"
                f"<div style='padding:10px 16px;text-align:right'>"
                f"<button type='submit' class='sbtn'>💾 Salvar</button></div>"
                f"</form></td></tr>"
            )
        return html

    vrows  = vac_rows()
    frows  = faq_rows()
    mrows  = mito_rows()
    msg_html = f"<div class='msg-ok'>✅ {_esc(msg)}</div>" if msg else ""

    css = """<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f0fdf4;color:#1a1a1a;min-height:100vh}
.wrap{max-width:1000px;margin:0 auto;padding:24px}
h1{color:#085C3C;font-size:21px;margin-bottom:2px}
.sub{color:#6b7280;font-size:13px;margin-bottom:18px}
.sub a{color:#0B7A50;text-decoration:none;font-weight:600}
.warn{background:#fef9c3;border:1px solid #fde68a;border-radius:10px;padding:11px 16px;font-size:13px;color:#92400e;margin-bottom:18px}
.warn code{background:#fde68a;padding:2px 6px;border-radius:4px}
.msg-ok{background:#d1fae5;border:1px solid #6ee7b7;border-radius:10px;padding:11px 16px;font-size:13px;color:#065f46;margin-bottom:18px;font-weight:600}
.tabs{display:flex;gap:6px;margin-bottom:18px;flex-wrap:wrap}
.tab{background:#fff;border:2px solid #e5e7eb;border-radius:20px;padding:8px 18px;font-size:13px;font-weight:600;cursor:pointer;color:#374151;font-family:inherit}
.tab.active{background:#0B7A50;color:#fff;border-color:#0B7A50}
.section{display:none}.section.show{display:block}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.07)}
th{background:#0B7A50;color:#fff;padding:10px 14px;text-align:left;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.4px}
td{padding:10px 14px;font-size:13px;border-bottom:1px solid #f3f4f6;vertical-align:top}
tr:last-child td{border:none}
tr:hover td{background:#f9fafb}
.ebtn{background:#f3f4f6;border:1px solid #e5e7eb;border-radius:8px;padding:5px 10px;font-size:12px;cursor:pointer;font-family:inherit}
.ebtn:hover{background:#e5e7eb}
.del-lnk{font-size:14px;text-decoration:none;opacity:.6}
.del-lnk:hover{opacity:1}
.erow,.efrow,.emrow{display:none}
.efhdr{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:#e6f4ee;border-bottom:1px solid #bbf7d0;flex-wrap:wrap;gap:8px}
.efhdr strong{font-size:14px;color:#085C3C}
.sbtn{background:#0B7A50;color:#fff;border:none;border-radius:20px;padding:8px 18px;font-size:13px;font-weight:700;cursor:pointer;font-family:inherit}
.sbtn:hover{background:#085C3C}
.efields{padding:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:600px){.efields{grid-template-columns:1fr}}
.cf{display:flex;flex-direction:column;gap:4px}
.cl{font-size:12px;font-weight:600;color:#374151;text-transform:uppercase;letter-spacing:.3px}
.ca{border:1px solid #d1d5db;border-radius:8px;padding:8px 10px;font-size:13px;font-family:inherit;resize:vertical;background:#fff}
.ca:focus{outline:none;border-color:#0B7A50;box-shadow:0 0 0 3px rgba(11,122,80,.15)}
.new-section{background:#fff;border-radius:14px;padding:20px;margin-top:20px;box-shadow:0 1px 6px rgba(0,0,0,.07)}
.new-section h3{font-size:14px;color:#085C3C;margin-bottom:14px;font-weight:700}
.new-fields{display:grid;grid-template-columns:1fr;gap:12px}
</style>"""

    script = """<script>
function switchTab(id) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.section').forEach(s => s.classList.remove('show'));
  document.querySelector('.tab[data-section="' + id + '"]').classList.add('active');
  document.getElementById(id).classList.add('show');
}
document.addEventListener('DOMContentLoaded', () => {
  // Vacinas
  document.querySelectorAll('.ebtn[data-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.id;
      const row = document.querySelector('.erow[data-id="' + id + '"]');
      const open = row.style.display === 'table-row';
      document.querySelectorAll('.erow').forEach(r => r.style.display = 'none');
      document.querySelectorAll('.ebtn[data-id]').forEach(b => b.textContent = '✏️ Editar');
      if (!open) {
        row.style.display = 'table-row';
        btn.textContent = '✖ Fechar';
        row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  });
  // FAQ
  document.querySelectorAll('.ebtn[data-faq]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.faq;
      const row = document.querySelector('.efrow[data-faq="' + id + '"]');
      const open = row.style.display === 'table-row';
      document.querySelectorAll('.efrow').forEach(r => r.style.display = 'none');
      document.querySelectorAll('.ebtn[data-faq]').forEach(b => b.textContent = '✏️');
      if (!open) { row.style.display = 'table-row'; btn.textContent = '✖'; row.scrollIntoView({behavior:'smooth',block:'nearest'}); }
    });
  });
  // Mitos
  document.querySelectorAll('.ebtn[data-mito]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.mito;
      const row = document.querySelector('.emrow[data-mito="' + id + '"]');
      const open = row.style.display === 'table-row';
      document.querySelectorAll('.emrow').forEach(r => r.style.display = 'none');
      document.querySelectorAll('.ebtn[data-mito]').forEach(b => b.textContent = '✏️');
      if (!open) { row.style.display = 'table-row'; btn.textContent = '✖'; row.scrollIntoView({behavior:'smooth',block:'nearest'}); }
    });
  });
  // Tabs
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.section));
  });
  // URL hash para abrir aba correta
  const hash = location.hash.replace('#','');
  if (['sec-faq','sec-mitos'].includes(hash)) switchTab(hash);
  else document.getElementById('sec-vac').classList.add('show');
});
</script>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Curadoria — VacinaFácil AI</title>{css}</head>
<body><div class="wrap">
<h1>✏️ VacinaFácil AI — Curadoria de Conteúdo</h1>
<p class="sub">
  {len(vacinas)} vacinas &nbsp;·&nbsp; {len(faqs)} FAQs &nbsp;·&nbsp; {len(mitos)} mitos &nbsp;·&nbsp;
  <a href="/admin?senha={senha}">📊 Dashboard</a> &nbsp;·&nbsp;
  <a href="/">💬 Chat</a>
</p>
{msg_html}
<div class="warn">⚠️ Após editar qualquer conteúdo, rode <code>python3 gerar_embeddings.py</code>
no servidor para atualizar a busca semântica.</div>

<div class="tabs">
  <button class="tab" data-section="sec-vac">💉 Vacinas ({len(vacinas)})</button>
  <button class="tab" data-section="sec-faq">💬 FAQ ({len(faqs)})</button>
  <button class="tab" data-section="sec-mitos">🚫 Mitos ({len(mitos)})</button>
</div>

<div id="sec-vac" class="section">
  <table>
    <thead><tr><th>Vacina</th><th>Disponível SUS</th><th style="width:100px"></th></tr></thead>
    <tbody>{vrows if vrows else "<tr><td colspan='3' style='text-align:center;color:#9ca3af;padding:20px'>Sem vacinas cadastradas.</td></tr>"}</tbody>
  </table>
</div>

<div id="sec-faq" class="section">
  <table>
    <thead><tr><th>Pergunta</th><th style="width:80px"></th></tr></thead>
    <tbody>{frows if frows else "<tr><td colspan='2' style='text-align:center;color:#9ca3af;padding:20px'>Sem FAQs cadastradas.</td></tr>"}</tbody>
  </table>
  <div class="new-section">
    <h3>➕ Nova pergunta frequente</h3>
    <form method="POST" action="/curadoria/salvar-faq">
      <input type="hidden" name="senha" value="{senha}">
      <input type="hidden" name="fid" value="">
      <div class="new-fields">
        {_tf("pergunta","Pergunta",None,2)}
        {_tf("resposta","Resposta",None,5)}
      </div>
      <div style="margin-top:12px"><button type="submit" class="sbtn">💾 Adicionar FAQ</button></div>
    </form>
  </div>
</div>

<div id="sec-mitos" class="section">
  <table>
    <thead><tr><th>Mito</th><th style="width:60px"></th></tr></thead>
    <tbody>{mrows if mrows else "<tr><td colspan='2' style='text-align:center;color:#9ca3af;padding:20px'>Sem mitos cadastrados.</td></tr>"}</tbody>
  </table>
</div>
</div>
{script}
</body></html>"""


@app.post("/curadoria/salvar-vacina")
def curadoria_salvar_vacina(
    senha:                      str = Form(...),
    vid:                        str = Form(...),
    resposta_padrao_sugerida:   str = Form(""),
    esquema_de_vacinacao:       str = Form(""),
    contraindicacoes_absolutas: str = Form(""),
    efeitos_colaterais_comuns:  str = Form(""),
    precaucoes:                 str = Form(""),
    duracao_da_protecao:        str = Form(""),
    eficacia_numerica:          str = Form(""),
    observacoes_internas:       str = Form(""),
):
    if senha != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Acesso negado")
    try:
        supabase_admin.table("vacinas").update({
            "resposta_padrao_sugerida":   resposta_padrao_sugerida   or None,
            "esquema_de_vacinacao":       esquema_de_vacinacao       or None,
            "contraindicacoes_absolutas": contraindicacoes_absolutas or None,
            "efeitos_colaterais_comuns":  efeitos_colaterais_comuns  or None,
            "precaucoes":                 precaucoes                 or None,
            "duracao_da_protecao":        duracao_da_protecao        or None,
            "eficacia_numerica":          eficacia_numerica          or None,
            "observacoes_internas":       observacoes_internas       or None,
        }).eq("id", vid).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(
        f"/curadoria?senha={senha}&msg=Vacina+{vid}+atualizada+com+sucesso",
        status_code=303,
    )


@app.post("/curadoria/salvar-faq")
def curadoria_salvar_faq(
    senha:    str = Form(...),
    fid:      str = Form(""),
    pergunta: str = Form(""),
    resposta: str = Form(""),
):
    if senha != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Acesso negado")
    if not pergunta.strip() or not resposta.strip():
        raise HTTPException(status_code=400, detail="Pergunta e resposta são obrigatórias")
    try:
        if fid:
            supabase_admin.table("faq").update(
                {"pergunta": pergunta.strip(), "resposta": resposta.strip()}
            ).eq("id", fid).execute()
            msg = "FAQ+atualizada+com+sucesso"
        else:
            supabase_admin.table("faq").insert(
                {"pergunta": pergunta.strip(), "resposta": resposta.strip()}
            ).execute()
            msg = "Nova+FAQ+adicionada+com+sucesso"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(f"/curadoria?senha={senha}&msg={msg}#sec-faq", status_code=303)


@app.post("/curadoria/salvar-mito")
def curadoria_salvar_mito(
    senha:                        str = Form(...),
    mid:                          str = Form(""),
    mito_como_circula:            str = Form(""),
    resposta_baseada_em_evidencia: str = Form(""),
):
    if senha != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Acesso negado")
    try:
        supabase_admin.table("mitos").update({
            "mito_como_circula":             mito_como_circula.strip()             or None,
            "resposta_baseada_em_evidencia": resposta_baseada_em_evidencia.strip() or None,
        }).eq("id", mid).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(
        f"/curadoria?senha={senha}&msg=Mito+atualizado+com+sucesso#sec-mitos",
        status_code=303,
    )


@app.get("/curadoria/del-faq")
def curadoria_del_faq(id: str = Query(""), senha: str = Query("")):
    if senha != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Acesso negado")
    try:
        supabase_admin.table("faq").delete().eq("id", id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RedirectResponse(
        f"/curadoria?senha={senha}&msg=FAQ+removida#sec-faq", status_code=303
    )


if __name__ == "__main__":
    import uvicorn
    print("\n🌿 VacinaFácil AI — Interface Web")
    print("   Acesse: http://localhost:8000")
    print("   Admin:  http://localhost:8000/admin?senha=vacinafacil2025\n")
    # access_log=False: não persiste perguntas dos usuários nos logs (LGPD)
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False, log_level="warning")
