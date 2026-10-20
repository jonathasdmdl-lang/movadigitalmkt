"""Estúdio MOVA: planejamento, peças e revisão por link sem login.
Demo: usa SQLite efêmero até DATABASE_URL ser configurado para Postgres persistente.
"""
import os, secrets, hashlib, hmac, mimetypes
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, redirect, url_for, session, abort, flash, render_template_string, Response, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from werkzeug.exceptions import RequestEntityTooLarge

studio_db = SQLAlchemy()
studio = Blueprint("studio", __name__)
MAX_BYTES = 12 * 1024 * 1024
VALID = {"image/png":"png","image/jpeg":"jpg","image/webp":"webp","application/pdf":"pdf","video/mp4":"mp4"}
def utcnow(): return datetime.now(timezone.utc)
def digest(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
class Plan(studio_db.Model):
    __tablename__="mova_studio_plans"
    id=studio_db.Column(studio_db.Integer,primary_key=True)
    client_id=studio_db.Column(studio_db.Integer,nullable=False,index=True)
    period=studio_db.Column(studio_db.String(7),nullable=False)
    campaign=studio_db.Column(studio_db.String(180),nullable=False)
    objective=studio_db.Column(studio_db.Text,default="")
    audience=studio_db.Column(studio_db.Text,default="")
    channels=studio_db.Column(studio_db.String(180),default="")
    pillars=studio_db.Column(studio_db.Text,default="")
    strategy=studio_db.Column(studio_db.Text,default="")
    kpis=studio_db.Column(studio_db.Text,default="")
    owner=studio_db.Column(studio_db.String(130),default="")
class Creative(studio_db.Model):
    __tablename__="mova_studio_creatives"
    id=studio_db.Column(studio_db.Integer,primary_key=True)
    plan_id=studio_db.Column(studio_db.Integer,nullable=False,index=True)
    client_id=studio_db.Column(studio_db.Integer,nullable=False,index=True)
    title=studio_db.Column(studio_db.String(180),nullable=False)
    format=studio_db.Column(studio_db.String(35),default="Post estático")
    channel=studio_db.Column(studio_db.String(90),default="Instagram")
    publish_date=studio_db.Column(studio_db.String(10),default="")
    briefing=studio_db.Column(studio_db.Text,default="")
    caption=studio_db.Column(studio_db.Text,default="")
    owner=studio_db.Column(studio_db.String(130),default="")
    status=studio_db.Column(studio_db.String(30),default="Em produção")
    version=studio_db.Column(studio_db.Integer,default=1)
    filename=studio_db.Column(studio_db.String(220),default="")
    mimetype=studio_db.Column(studio_db.String(80),default="")
    file_bytes=studio_db.Column(studio_db.LargeBinary)
    token_hash=studio_db.Column(studio_db.String(64),index=True)
    token_expires=studio_db.Column(studio_db.DateTime(timezone=True))
    reviewer=studio_db.Column(studio_db.String(130),default="")
    feedback=studio_db.Column(studio_db.Text,default="")
    reviewed_at=studio_db.Column(studio_db.DateTime(timezone=True))
class Review(studio_db.Model):
    __tablename__="mova_studio_reviews"
    id=studio_db.Column(studio_db.Integer,primary_key=True)
    creative_id=studio_db.Column(studio_db.Integer,nullable=False,index=True)
    version=studio_db.Column(studio_db.Integer,nullable=False)
    action=studio_db.Column(studio_db.String(35),nullable=False)
    reviewer=studio_db.Column(studio_db.String(130),default="")
    note=studio_db.Column(studio_db.Text,default="")
    timestamp=studio_db.Column(studio_db.DateTime(timezone=True),default=utcnow)
def clean(key,length=1000):return (request.form.get(key) or "").strip()[:length]
def get_client(conn, id):
    with conn() as c:return c.execute("SELECT id,nome,email,telefone FROM crm_clientes WHERE id=?",(id,)).fetchone()
def protected():
    if not session.get("user"):abort(403)
def persist():studio_db.session.commit()
def file_type(data, mime):
    if mime=="image/png":return data.startswith(b"\x89PNG\r\n\x1a\n")
    if mime=="image/jpeg":return data.startswith(b"\xff\xd8\xff")
    if mime=="image/webp":return data.startswith(b"RIFF") and data[8:12]==b"WEBP"
    if mime=="application/pdf":return data.startswith(b"%PDF-")
    if mime=="video/mp4":return len(data)>12 and data[4:8]==b"ftyp"
    return False
def review_by_token(token):
    if len(token)<32 or len(token)>128:abort(404)
    item=studio_db.session.execute(select(Creative).where(Creative.token_hash==digest(token))).scalar_one_or_none()
    if not item:abort(404)
    if not item.token_expires or item.token_expires.replace(tzinfo=timezone.utc)<utcnow():abort(410)
    return item
def render_public(body,**kw):
    html="""<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow,noarchive"><title>Aprovação | MOVA Marketing Digital</title><style>body{background:#0c111c;color:#eef1f8;font:16px system-ui,Arial;margin:0}.wrap{max-width:840px;margin:36px auto;padding:0 20px}.brand{font-weight:900;letter-spacing:2px;font-size:30px}.brand b{color:#91a6fa}h1{font-size:clamp(23px,4vw,36px)}.card{background:#1c2638;border:1px solid #34425c;padding:25px;border-radius:17px;margin:20px 0}.art{background:#0a0e16;border-radius:10px;min-height:100px;display:flex;align-items:center;justify-content:center;overflow:hidden}.art img,.art video{max-width:100%;max-height:590px;object-fit:contain}a{color:#bbcdff}textarea,input{box-sizing:border-box;width:100%;padding:12px;border-radius:8px;border:1px solid #657391;background:#101827;color:white;margin:7px 0 15px}button{padding:13px 17px;border:0;border-radius:9px;font-weight:bold;cursor:pointer}.yes{background:#9af0c5}.no{background:#ffc9b5}p{line-height:1.6;color:#d0d9e9}.muted{font-size:13px;color:#aab5c8}.buttons{display:flex;gap:12px;flex-wrap:wrap}</style></head><body><div class="wrap"><div class="brand">MO<b>V</b>A</div><div class="muted">Estratégia que gera movimento.</div>"""+body+"</div></body></html>"
    resp=make_response(render_template_string(html,**kw))
    resp.headers["Cache-Control"]="private, no-store"
    resp.headers["Referrer-Policy"]="no-referrer"
    resp.headers["X-Content-Type-Options"]="nosniff"
    resp.headers["Content-Security-Policy"]="default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    return resp

def init_studio(app, conn, render):
    app.config["SQLALCHEMY_DATABASE_URI"]=os.environ.get("DATABASE_URL","sqlite:////tmp/mova_studio_demo.sqlite3").replace("postgres://","postgresql://",1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
    studio_db.init_app(app)
    with app.app_context():studio_db.create_all()
    app.register_blueprint(studio)
    studio._client_conn=conn
    studio._inner_render=render

@studio.route("/studio")
def index():
    protected()
    with studio._client_conn() as db:clients=db.execute("SELECT id,nome FROM crm_clientes ORDER BY nome").fetchall()
    plans=studio_db.session.execute(select(Plan).order_by(Plan.id.desc())).scalars().all()
    creatives=studio_db.session.execute(select(Creative).order_by(Creative.id.desc()).limit(40)).scalars().all()
    name={c["id"]:c["nome"] for c in clients}
    return studio._inner_render("""<h1>Estúdio MOVA · Planejamento & Aprovação</h1><p>Da estratégia ao conteúdo aprovado, sempre ligado ao cliente.</p><div class="quick"><a href="/gestao/clientes">+ Novo cliente</a><a href="/studio/plano/novo">+ Planejamento editorial</a></div><div class="grid"><div class="box"><h3>Planejamentos</h3><div class="metric">{{plans|length}}</div></div><div class="box"><h3>Peças</h3><div class="metric">{{items|length}}</div></div><div class="box"><h3>Aguardando cliente</h3><div class="metric">{{waiting}}</div></div></div><div class="box"><h3>Planejamentos por conta</h3><table><tr><th>Cliente</th><th>Campanha</th><th>Competência</th><th>Ação</th></tr>{% for p in plans %}<tr><td>{{names.get(p.client_id,'Cliente não encontrado')}}</td><td>{{p.campaign}}</td><td>{{p.period}}</td><td><a href="/studio/plano/{{p.id}}">Abrir →</a></td></tr>{% endfor %}</table></div><div class="box"><h3>Produção e aprovações recentes</h3><table><tr><th>Cliente</th><th>Peça</th><th>Status</th></tr>{% for c in items %}<tr><td>{{names.get(c.client_id,'Cliente não encontrado')}}</td><td><a href="/studio/peca/{{c.id}}">{{c.title}}</a></td><td>{{c.status}}</td></tr>{% endfor %}</table></div>""",plans=plans,items=creatives,names=name,waiting=sum(x.status=="Aguardando aprovação" for x in creatives))

@studio.route("/studio/plano/novo",methods=["GET","POST"])
def plan_create():
    protected()
    with studio._client_conn() as c:clients=c.execute("SELECT id,nome FROM crm_clientes ORDER BY nome").fetchall()
    if request.method=="POST":
        cid=request.form.get("client_id",type=int)
        if not cid or not get_client(studio._client_conn,cid) or not clean("campaign",180):
            flash("Escolha um cliente e informe a campanha.");return redirect("/studio/plano/novo")
        p=Plan(client_id=cid,period=clean("period",7),campaign=clean("campaign",180),objective=clean("objective"),audience=clean("audience"),channels=clean("channels",180),pillars=clean("pillars"),strategy=clean("strategy"),kpis=clean("kpis"),owner=clean("owner",130))
        studio_db.session.add(p);persist()
        return redirect(url_for("studio.plan_detail",pid=p.id))
    return studio._inner_render("""<h1>Novo planejamento editorial</h1><p>Briefing de campanha conectado ao cliente.</p><div class="box"><form method="post"><label>Cliente</label><select name="client_id" required><option value="">Selecione</option>{% for c in clients %}<option value="{{c['id']}}">{{c['nome']}}</option>{% endfor %}</select><label>Mês/competência</label><input type="month" name="period" required><input name="campaign" placeholder="Campanha / nome do planejamento" required><textarea name="objective" placeholder="Objetivos comerciais e de comunicação"></textarea><textarea name="audience" placeholder="Persona, público-alvo e dores"></textarea><input name="channels" placeholder="Instagram, TikTok, LinkedIn, Google..."><textarea name="pillars" placeholder="Pilares editoriais: institucional, educativo, comercial..."></textarea><textarea name="strategy" placeholder="Estratégia, tom de voz e diferenciais"></textarea><textarea name="kpis" placeholder="Indicadores, metas e frequência"></textarea><input name="owner" placeholder="Gestor responsável"><button>Salvar planejamento</button></form></div>""",clients=clients)

@studio.get("/studio/plano/<int:pid>")
def plan_detail(pid):
    protected()
    p=studio_db.session.get(Plan,pid)
    if not p:abort(404)
    client=get_client(studio._client_conn,p.client_id)
    items=studio_db.session.execute(select(Creative).where(Creative.plan_id==pid).order_by(Creative.publish_date,Creative.id)).scalars().all()
    return studio._inner_render("""<a href="/studio">← Estúdio</a><h1>{{p.campaign}} · {{p.period}}</h1><p><strong>Cliente:</strong> {{client['nome'] if client else 'não encontrado'}} | {{p.channels}} | Gestor: {{p.owner}}</p><div class="quick"><a href="/studio/plano/{{p.id}}/peca">+ Nova peça / vídeo</a><a href="/agencia/cliente/{{p.client_id}}">Ficha 360°</a></div><div class="grid"><div class="box"><h3>Objetivos</h3><p>{{p.objective}}</p><h3>Público</h3><p>{{p.audience}}</p></div><div class="box"><h3>Pilares</h3><p>{{p.pillars}}</p><h3>Estratégia</h3><p>{{p.strategy}}</p><h3>KPIs / frequência</h3><p>{{p.kpis}}</p></div></div><div class="box"><h3>Guia de conteúdo / calendário editorial</h3><table><tr><th>Data</th><th>Formato</th><th>Tema</th><th>Canal</th><th>Responsável</th><th>Status</th></tr>{% for c in items %}<tr><td>{{c.publish_date}}</td><td>{{c.format}}</td><td><a href="/studio/peca/{{c.id}}">{{c.title}}</a></td><td>{{c.channel}}</td><td>{{c.owner}}</td><td>{{c.status}}</td></tr>{% endfor %}</table></div>""",p=p,client=client,items=items)

@studio.route("/studio/plano/<int:pid>/peca",methods=["GET","POST"])
def creative_create(pid):
    protected()
    p=studio_db.session.get(Plan,pid)
    if not p:abort(404)
    if request.method=="POST":
        if not clean("title",180):flash("Informe o título da peça.");return redirect(request.path)
        item=Creative(plan_id=pid,client_id=p.client_id,title=clean("title",180),format=clean("format",35),channel=clean("channel",90),publish_date=clean("publish_date",10),briefing=clean("briefing"),caption=clean("caption"),owner=clean("owner",130))
        studio_db.session.add(item);persist()
        return redirect(url_for("studio.creative_detail",cid=item.id))
    return studio._inner_render("""<a href="/studio/plano/{{p.id}}">← Planejamento</a><h1>Nova peça do planejamento</h1><div class="box"><form method="post"><input name="title" required placeholder="Tema / título da peça"><div class="grid"><select name="format"><option>Post estático</option><option>Carrossel</option><option>Reels</option><option>Stories</option><option>Vídeo</option><option>Outro</option></select><select name="channel"><option>Instagram</option><option>Facebook</option><option>TikTok</option><option>LinkedIn</option><option>YouTube</option><option>Google Ads</option></select><input type="date" name="publish_date"><input name="owner" placeholder="Responsável"></div><textarea name="briefing" placeholder="Objetivo, referência visual e briefing criativo"></textarea><textarea name="caption" placeholder="Legenda, roteiro e CTA"></textarea><button>Criar peça</button></form></div>""",p=p)

@studio.route("/studio/peca/<int:cid>",methods=["GET","POST"])
def creative_detail(cid):
    protected()
    c=studio_db.session.get(Creative,cid)
    if not c:abort(404)
    if request.method=="POST":
        file=request.files.get("arte")
        if not file or not file.filename:flash("Selecione o arquivo.");return redirect(request.path)
        mime=(file.mimetype or "").split(";")[0]
        if mime not in VALID:flash("Formatos aceitos: JPG, PNG, WEBP, PDF ou MP4.");return redirect(request.path)
        data=file.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES or not file_type(data,mime):
            flash("Arquivo inválido ou maior que 12 MB.");return redirect(request.path)
        c.version += 1 if c.file_bytes else 0
        c.file_bytes=data;c.mimetype=mime;c.filename=("arte-v"+str(c.version)+"."+VALID[mime])
        c.token_hash=None;c.token_expires=None;c.status="Pronto para revisão"
        c.reviewer="";c.feedback="";c.reviewed_at=None
        studio_db.session.add(Review(creative_id=c.id,version=c.version,action="Nova versão enviada",reviewer=session.get("user","Equipe")))
        persist();flash("Arquivo salvo; links antigos foram revogados.")
        return redirect(request.path)
    events=studio_db.session.execute(select(Review).where(Review.creative_id==c.id).order_by(Review.id.desc())).scalars().all()
    return studio._inner_render("""<a href="/studio/plano/{{c.plan_id}}">← Calendário editorial</a><h1>{{c.title}}</h1><p>{{c.format}} · {{c.channel}} · {{c.publish_date}} · Responsável: {{c.owner}}</p><div class="grid"><div class="box"><h3>Briefing</h3><p>{{c.briefing}}</p><h3>Legenda / CTA</h3><p>{{c.caption}}</p></div><div class="box"><h3>Aprovação</h3><p>Status: <b>{{c.status}}</b></p><p>Versão: {{c.version}}</p>{% if c.file_bytes %}<a href="/studio/peca/{{c.id}}/arquivo" target="_blank">Visualizar arquivo anexado</a>{% endif %}<p>{{c.reviewer}} · {{c.feedback}}</p></div></div><div class="box"><h3>Anexar ou substituir arte / vídeo</h3><p>Tipos: JPG, PNG, WEBP, PDF ou MP4 até 12 MB. Enviar nova versão invalida link anterior e reinicia a aprovação.</p><form method="post" enctype="multipart/form-data"><input type="file" name="arte" accept=".jpg,.jpeg,.png,.webp,.pdf,.mp4" required><button>Salvar arquivo</button></form></div>{% if c.file_bytes %}<div class="box"><h3>Compartilhar com cliente</h3><p>Gere um link temporário exclusivo. O cliente não precisa criar conta.</p><form method="post" action="/studio/peca/{{c.id}}/link"><button>Gerar novo link de aprovação</button></form><small>Gerar novo link revoga o anterior. Compartilhe apenas com o cliente autorizado.</small></div>{% endif %}<div class="box"><h3>Histórico de revisão</h3><table><tr><th>Versão</th><th>Ação</th><th>Quem</th><th>Observações</th></tr>{% for e in events %}<tr><td>{{e.version}}</td><td>{{e.action}}</td><td>{{e.reviewer}}</td><td>{{e.note}}</td></tr>{% endfor %}</table></div>""",c=c,events=events)

@studio.get("/studio/peca/<int:cid>/arquivo")
def staff_asset(cid):
    protected()
    c=studio_db.session.get(Creative,cid)
    if not c or not c.file_bytes:abort(404)
    return serve(c)

def serve(c):
    r=Response(c.file_bytes,mimetype=c.mimetype)
    r.headers["Cache-Control"]="private, no-store"
    r.headers["X-Content-Type-Options"]="nosniff"
    r.headers["Content-Security-Policy"]="default-src 'none'; sandbox"
    r.headers["Content-Disposition"]=("inline" if c.mimetype.startswith(("image/","video/")) else "attachment")+'; filename="'+c.filename+'"'
    return r

@studio.post("/studio/peca/<int:cid>/link")
def send_review(cid):
    protected()
    c=studio_db.session.get(Creative,cid)
    if not c or not c.file_bytes:abort(404)
    raw=secrets.token_urlsafe(36)
    c.token_hash=digest(raw);c.token_expires=utcnow()+timedelta(days=14)
    c.status="Aguardando aprovação"
    studio_db.session.add(Review(creative_id=c.id,version=c.version,action="Link de revisão criado",reviewer=session.get("user","Equipe")))
    persist()
    url=url_for("studio.public_review",token=raw,_external=True)
    return studio._inner_render("""<h1>Link de aprovação criado</h1><p>Copie e envie via WhatsApp ou e-mail. Este link só será mostrado agora; para emitir outro, volte à peça.</p><div class="box"><input readonly value="{{url}}" onclick="this.select()"><p><a href="{{url}}" target="_blank" rel="noopener noreferrer">Visualizar como cliente</a></p><a href="{{wa}}" target="_blank" rel="noopener noreferrer">Compartilhar no WhatsApp</a><p><small>Válido por 14 dias ou até receber uma decisão. Qualquer pessoa com o link pode responder. Não equivale a assinatura eletrônica autenticada.</small></p></div><a href="/studio/peca/{{c.id}}">Voltar à peça</a>""",url=url,wa="https://wa.me/?text="+__import__("urllib.parse",fromlist=["quote"]).quote("Olá! Segue a arte para sua revisão na MOVA: "+url),c=c)

@studio.route("/revisao/<token>",methods=["GET","POST"])
def public_review(token):
    c=review_by_token(token)
    if request.method=="POST":
        check=clean("csrf",100)
        if not hmac.compare_digest(check,session.get("studio_csrf","")):abort(400)
        if c.status!="Aguardando aprovação":abort(409)
        action=clean("acao",30)
        if action not in ("Aprovado","Revisão solicitada"):abort(400)
        note=clean("observacao",2000)
        if action=="Revisão solicitada" and not note:abort(400)
        person=clean("nome",130)
        if not person:abort(400)
        c.status=action;c.reviewer=person;c.feedback=note;c.reviewed_at=utcnow()
        c.token_hash=None;c.token_expires=None
        studio_db.session.add(Review(creative_id=c.id,version=c.version,action=action,reviewer=person,note=note))
        persist()
        return render_public("""<div class="card"><h1>Resposta registrada</h1><p>Obrigado! A MOVA recebeu sua decisão: <b>{{status}}</b>.</p><p>Você pode fechar esta página.</p></div>""",status=action)
    session["studio_csrf"]=secrets.token_urlsafe(24)
    return render_public("""<h1>Revisão de arte</h1><div class="card"><h2>{{c.title}}</h2><p>{{c.format}} · {{c.channel}}</p><div class="art">{% if c.mimetype.startswith('image/') %}<img src="/revisao/{{token}}/arquivo" alt="Arte enviada para aprovação">{% elif c.mimetype.startswith('video/') %}<video src="/revisao/{{token}}/arquivo" controls preload="metadata"></video>{% else %}<a href="/revisao/{{token}}/arquivo" target="_blank" rel="noopener noreferrer">Abrir PDF</a>{% endif %}</div><h3>Legenda / texto</h3><p style="white-space:pre-wrap">{{c.caption}}</p><small>Versão {{c.version}}</small></div>{% if c.status=="Aguardando aprovação" %}<div class="card"><h2>Sua avaliação</h2><form method="post"><input type="hidden" name="csrf" value="{{csrf}}"><label>Seu nome</label><input name="nome" required maxlength="130" placeholder="Nome de quem está avaliando"><label>Observações ou alterações solicitadas</label><textarea name="observacao" rows="4" maxlength="2000" placeholder="Caso queira ajustes, descreva o que deve ser alterado"></textarea><div class="buttons"><button class="yes" type="submit" name="acao" value="Aprovado">✓ Aprovar arte</button><button class="no" type="submit" name="acao" value="Revisão solicitada">Solicitar alterações</button></div></form><p class="muted">Ao responder você registra uma decisão relativa a esta versão da peça. O link não verifica sua identidade.</p></div>{% else %}<div class="card"><h2>Revisão encerrada</h2><p>Esta peça já recebeu uma resposta.</p></div>{% endif %}""",c=c,token=token,csrf=session["studio_csrf"])

@studio.get("/revisao/<token>/arquivo")
def client_asset(token):
    c=review_by_token(token)
    if not c.file_bytes:abort(404)
    return serve(c)
