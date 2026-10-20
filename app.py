import os, sqlite3, hmac, hashlib, secrets
from functools import wraps
from flask import Flask, request, redirect, session, render_template_string, flash
app=Flask(__name__)
app.secret_key=os.environ["SECRET_KEY"]
DB=os.environ.get("DB_PATH","/tmp/mova_demo.db")
MODULES={"clientes":"Clientes","projetos":"Projetos","tarefas":"Tarefas","financeiro":"Financeiro","contratos":"Contratos","aprovacoes":"Aprovações"}
def connection():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 return c
with connection() as c:
 for k in MODULES: c.execute("CREATE TABLE IF NOT EXISTS "+k+"(id INTEGER PRIMARY KEY, titulo TEXT NOT NULL, descricao TEXT DEFAULT '', status TEXT DEFAULT 'Pendente', criado TEXT DEFAULT CURRENT_TIMESTAMP)")
HTML="""<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MOVA Gestão</title><style>body{margin:0;background:#0b1020;color:#f0f2f8;font:15px Inter,system-ui,-apple-system,Arial,sans-serif;line-height:1.55;background-image:radial-gradient(circle at top right,#283352 0,transparent 35%)}header{padding:22px max(24px,calc((100vw - 1200px)/2));background:#101829ed;border-bottom:1px solid #30384d;position:sticky;top:0;z-index:4;backdrop-filter:blur(16px)}.brand{font-size:27px;font-weight:900;letter-spacing:1px}.brand span{color:#9baeff}main{max-width:1200px;margin:35px auto;padding:0 22px}a{color:#aabcff;text-decoration:none}nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:17px}nav a{display:inline-block;margin:0;padding:9px 12px;border:1px solid #34405b;border-radius:9px;background:#192239;color:#cfdaff;font-size:13px;font-weight:650}nav a:hover{background:#33466e}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:15px}.box{background:#1c263b;border:1px solid #384763;border-radius:17px;padding:25px;margin:14px 0;box-shadow:0 8px 30px #080d1929}.warning{background:#30271a;border:1px solid #806435;padding:15px;border-radius:10px;margin:16px 0}input,textarea,select{display:block;width:100%;box-sizing:border-box;padding:12px;margin:10px 0;background:#111726;color:white;border:1px solid #515c78;border-radius:9px}button{background:linear-gradient(135deg,#aec0ff,#859cff);color:#121625;border:0;border-radius:9px;padding:12px 22px;font-weight:800;cursor:pointer}button:hover{filter:brightness(1.09)}h1{font-size:30px;letter-spacing:-.8px}h3{color:#e8eeff}input:focus,textarea:focus,select:focus{outline:2px solid #9fb0ff}a:hover{text-decoration:underline}@media(max-width:600px){header{padding:16px}main{margin:15px auto;padding:0 12px}.box{padding:15px}table{font-size:12px}th,td{padding:8px}}table{width:100%;border-collapse:collapse}th,td{padding:13px;border-bottom:1px solid #394154;text-align:left}@media(min-width:1050px){body{padding-left:235px}header{position:fixed;top:0;bottom:0;left:0;width:195px;padding:28px 20px;overflow:auto}nav{display:flex;flex-direction:column;align-items:stretch}nav a{margin:0 0 7px!important;padding:12px;border:1px solid #344262;border-radius:10px;background:#24304b}main{margin:30px auto}}.quick{display:flex;flex-wrap:wrap;gap:9px;margin:16px 0}.quick a{padding:10px 14px;border-radius:9px;color:white;background:#34466b;font-weight:700}.metric{font-size:28px;font-weight:800;color:#b6c7ff}</style></head><body><header><div class="brand">MO<span style="color:#aebfff;display:inline-block;transform:skew(-12deg)">V</span>A <span>GESTÃO</span></div><small>Estratégia que gera movimento.</small>{% if session.get("user") %}<nav><a href="/">Dashboard</a><a href="/gestao/clientes">Clientes 360°</a><a href="/agencia/planejamento">Planejamento</a><a href="/agencia/servicos">Ordens de serviço</a><a href="/agencia/producao">Produção</a><a href="/studio">Estúdio & Aprovações</a><a href="/agencia/aprovacoes">Painel de Aprovações</a><a href="/gestao/cobrancas">Financeiro</a><a href="/agencia/relatorios">Relatórios</a><a href="/agencia/alertas">Alertas</a><a href="/sair">Sair</a></nav>{% endif %}</header><main><div class="warning">VERSÃO DE DEMONSTRAÇÃO — não cadastre dados pessoais, contratos ou valores reais. Dados temporários, sujeitos a exclusão.</div>{% for msg in get_flashed_messages() %}<p>{{msg}}</p>{% endfor %}{% block main %}{% endblock %}</main></body></html>"""
def render(inner,**kwargs):return render_template_string(HTML.replace("{% block main %}{% endblock %}",inner),modules=MODULES,**kwargs)
def require(f):
 @wraps(f)
 def wrap(*args,**kwargs):
  if not session.get("user"):return redirect("/login")
  return f(*args,**kwargs)
 return wrap
@app.get("/health")
def health():return {"status":"ok","app":"MOVA Gestão Demonstração"}
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  a=request.form.get("email","");b=request.form.get("senha","")
  valid=hmac.compare_digest(a,os.environ["ADMIN_EMAIL"]) and hmac.compare_digest(hashlib.sha256(b.encode()).hexdigest(),os.environ["ADMIN_PASSWORD_SHA256"])
  if valid:session["user"]=a;return redirect("/")
  flash("Login ou senha inválidos.")
 return render("""<div class="box" style="max-width:430px"><h2>Acessar MOVA Gestão</h2><form method="post"><label>E-mail</label><input type="email" name="email" required><label>Senha</label><input type="password" name="senha" required><button>Entrar</button></form></div>""")
@app.get("/sair")
def logout():session.clear();return redirect("/login")
@app.get("/")
@require
def home():
 with connection() as c:counts={k:c.execute("SELECT COUNT(*) FROM "+k).fetchone()[0] for k in MODULES}
 return render("""<h1>Painel administrativo</h1><p>Bem-vindo à demonstração da MOVA Gestão.</p><div class="grid">{% for key,label in modules.items() %}<a class="box" href="/modulo/{{key}}"><h3>{{label}}</h3><h1>{{counts[key]}}</h1><small>Abrir módulo →</small></a>{% endfor %}</div>""",counts=counts)
@app.route("/modulo/<key>",methods=["GET","POST"])
@require
def module(key):
 if key not in MODULES:return "Não encontrado",404
 if request.method=="POST":
  title=request.form.get("titulo","").strip()[:160];desc=request.form.get("descricao","").strip()[:1000];status=request.form.get("status","Pendente")
  if title:
   with connection() as c:c.execute("INSERT INTO "+key+"(titulo,descricao,status) VALUES(?,?,?)",(title,desc,status))
   flash("Registro de demonstração cadastrado.")
  return redirect("/modulo/"+key)
 with connection() as c:items=c.execute("SELECT id,titulo,descricao,status,criado FROM "+key+" ORDER BY id DESC").fetchall()
 return render("""<h1>{{label}}</h1><div class="box"><h3>Adicionar registro</h3><form method="post"><input name="titulo" required maxlength="160" placeholder="Nome ou título"><textarea name="descricao" maxlength="1000" placeholder="Descrição"></textarea><select name="status"><option>Pendente</option><option>Em andamento</option><option>Concluído</option><option>Aprovado</option><option>Revisão solicitada</option></select><button>Cadastrar</button></form></div><div class="box"><h3>Registros ({{items|length}})</h3><table><tr><th>Título</th><th>Status</th><th>Descrição</th></tr>{% for item in items %}<tr><td>{{item["titulo"]}}</td><td>{{item["status"]}}</td><td>{{item["descricao"]}}</td></tr>{% endfor %}</table></div>""",label=MODULES[key],items=items)

# Gestao comercial demonstrativa (os registros do plano gratuito sao temporarios)
from decimal import Decimal, InvalidOperation
from datetime import date
with connection() as c:
 c.execute("""CREATE TABLE IF NOT EXISTS crm_clientes(id INTEGER PRIMARY KEY, nome TEXT NOT NULL, documento TEXT, email TEXT, telefone TEXT, endereco TEXT, contato TEXT, observacoes TEXT, ativo INTEGER DEFAULT 1)""")
 c.execute("""CREATE TABLE IF NOT EXISTS crm_contratos(id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL, servico TEXT NOT NULL, valor_centavos INTEGER NOT NULL, parcelas INTEGER NOT NULL DEFAULT 1, inicio TEXT, observacoes TEXT, FOREIGN KEY(cliente_id) REFERENCES crm_clientes(id))""")
 c.execute("""CREATE TABLE IF NOT EXISTS crm_cobrancas(id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL, contrato_id INTEGER, descricao TEXT NOT NULL, vencimento TEXT NOT NULL, valor_centavos INTEGER NOT NULL, situacao TEXT NOT NULL DEFAULT 'Pendente', pago_em TEXT, referencia TEXT, FOREIGN KEY(cliente_id) REFERENCES crm_clientes(id))""")
def real(v):
 try:
  d=Decimal(str(v).strip().replace(".","").replace(",","."))
  if d <= 0 or d>999999999:return None
  return int(d*100)
 except (InvalidOperation,ValueError):return None
def money(v):return "R$ {:,.2f}".format(v/100).replace(",","X").replace(".",",").replace("X",".")
app.jinja_env.globals["money"]=money
def client_exists(cid):
 with connection() as c:return c.execute("SELECT id FROM crm_clientes WHERE id=?",(cid,)).fetchone() is not None
@app.route("/gestao/clientes",methods=["GET","POST"])
@require
def crm_clients():
 if request.method=="POST":
  name=request.form.get("nome","").strip()[:180]
  if not name:flash("Informe o nome do cliente.")
  else:
   values=[request.form.get(k,"").strip()[:800] for k in ("documento","email","telefone","endereco","contato","observacoes")]
   with connection() as c:c.execute("INSERT INTO crm_clientes(nome,documento,email,telefone,endereco,contato,observacoes) VALUES(?,?,?,?,?,?,?)",[name]+values)
   flash("Cliente cadastrado.")
  return redirect("/gestao/clientes")
 with connection() as c:clients=c.execute("SELECT * FROM crm_clientes ORDER BY nome").fetchall()
 return render("""<h1>Gestão de clientes</h1><div class="box"><h3>Novo cliente</h3><form method="post"><input name="nome" required placeholder="Nome da empresa ou cliente"><div class="grid"><input name="documento" placeholder="CPF/CNPJ"><input name="email" type="email" placeholder="E-mail"><input name="telefone" placeholder="Telefone / WhatsApp"><input name="contato" placeholder="Pessoa responsável"></div><input name="endereco" placeholder="Endereço"><textarea name="observacoes" placeholder="Observações e necessidades"></textarea><button>Salvar cliente</button></form></div><div class="box"><h3>Clientes cadastrados</h3><table><tr><th>Cliente</th><th>Contato</th><th>Gestão</th></tr>{% for c in clients %}<tr><td>{{c['nome']}}</td><td>{{c['telefone'] or c['email']}}</td><td><a href="/agencia/cliente/{{c['id']}}">Abrir conta 360° →</a></td></tr>{% endfor %}</table></div>""",clients=clients)
@app.route("/gestao/cliente/<int:cid>",methods=["GET","POST"])
@require
def crm_client(cid):
 with connection() as c:client=c.execute("SELECT * FROM crm_clientes WHERE id=?",(cid,)).fetchone()
 if not client:return "Cliente não encontrado",404
 if request.method=="POST":
  action=request.form.get("action")
  with connection() as c:
   if action=="editar":
    vals=[request.form.get(k,"").strip()[:800] for k in ("nome","documento","email","telefone","endereco","contato","observacoes")]
    if vals[0]:c.execute("UPDATE crm_clientes SET nome=?,documento=?,email=?,telefone=?,endereco=?,contato=?,observacoes=? WHERE id=?",vals+[cid]);flash("Dados do cliente atualizados.")
   elif action=="contrato":
    amount=real(request.form.get("valor",""))
    try:parc=int(request.form.get("parcelas","1"))
    except ValueError:parc=0
    serv=request.form.get("servico","").strip()[:180]
    if amount and 1<=parc<=120 and serv:
     cur=c.execute("INSERT INTO crm_contratos(cliente_id,servico,valor_centavos,parcelas,inicio,observacoes) VALUES(?,?,?,?,?,?)",(cid,serv,amount,parc,request.form.get("inicio",""),request.form.get("obs","")[:1000]))
     flash("Contrato registrado. Adicione as cobranças com seus vencimentos.")
    else:flash("Verifique serviço, valor e número de parcelas.")
   elif action=="cobranca":
    amount=real(request.form.get("valor",""))
    venc=request.form.get("vencimento","")
    if amount and len(venc)==10:
     c.execute("INSERT INTO crm_cobrancas(cliente_id,descricao,vencimento,valor_centavos,referencia) VALUES(?,?,?,?,?)",(cid,request.form.get("descricao","Cobrança")[:180],venc,amount,request.form.get("referencia","")[:80]))
     flash("Cobrança lançada.")
    else:flash("Informe um valor e vencimento válidos.")
  return redirect("/gestao/cliente/"+str(cid))
 with connection() as c:
  client=c.execute("SELECT * FROM crm_clientes WHERE id=?",(cid,)).fetchone()
  contracts=c.execute("SELECT * FROM crm_contratos WHERE cliente_id=? ORDER BY id DESC",(cid,)).fetchall()
  bills=c.execute("SELECT * FROM crm_cobrancas WHERE cliente_id=? ORDER BY vencimento DESC",(cid,)).fetchall()
 return render("""<p><a href="/gestao/clientes">← Todos os clientes</a></p><h1>{{c['nome']}}</h1><div class="box"><h3>Editar ficha</h3><form method="post"><input type="hidden" name="action" value="editar"><input name="nome" value="{{c['nome']}}" required><div class="grid"><input name="documento" placeholder="CPF/CNPJ" value="{{c['documento'] or ''}}"><input name="email" placeholder="E-mail" value="{{c['email'] or ''}}"><input name="telefone" placeholder="Telefone" value="{{c['telefone'] or ''}}"><input name="contato" placeholder="Contato principal" value="{{c['contato'] or ''}}"></div><input name="endereco" placeholder="Endereço" value="{{c['endereco'] or ''}}"><textarea name="observacoes" placeholder="Observações">{{c['observacoes'] or ''}}</textarea><button>Salvar alterações</button></form></div><div class="grid"><div class="box"><h3>Novo contrato / prestação</h3><form method="post"><input type="hidden" name="action" value="contrato"><input name="servico" required placeholder="Serviço ou pacote contratado"><input name="valor" required placeholder="Valor total (ex.: 1500,00)"><input name="parcelas" type="number" min="1" max="120" value="1" required><input type="date" name="inicio"><textarea name="obs" placeholder="Observações"></textarea><button>Registrar contrato</button></form></div><div class="box"><h3>Lançar cobrança</h3><form method="post"><input type="hidden" name="action" value="cobranca"><input name="descricao" required placeholder="Mensalidade / parcela / serviço"><input name="valor" required placeholder="Valor (ex.: 500,00)"><input type="date" name="vencimento" required><input name="referencia" placeholder="Número / referência da cobrança"><button>Lançar cobrança</button></form></div></div><div class="box"><h3>Contratos</h3><table><tr><th>Serviço</th><th>Total</th><th>Parcelas</th></tr>{% for x in contracts %}<tr><td>{{x['servico']}}</td><td>{{money(x['valor_centavos'])}}</td><td>{{x['parcelas']}}</td></tr>{% endfor %}</table></div><div class="box"><h3>Cobranças</h3><table><tr><th>Descrição</th><th>Vencimento</th><th>Valor</th><th>Status</th><th>Ação</th></tr>{% for x in bills %}<tr><td>{{x['descricao']}} <small>{{x['referencia'] or ''}}</small></td><td>{{x['vencimento']}}</td><td>{{money(x['valor_centavos'])}}</td><td>{{x['situacao']}}</td><td>{% if x['situacao'] != 'Pago' %}<form action="/gestao/cobranca/{{x['id']}}/pagar" method="post"><button>Marcar pago</button></form>{% endif %}</td></tr>{% endfor %}</table></div>""",c=client,contracts=contracts,bills=bills)
@app.post("/gestao/cobranca/<int:bid>/pagar")
@require
def bill_paid(bid):
 with connection() as c:
  bill=c.execute("SELECT cliente_id FROM crm_cobrancas WHERE id=?",(bid,)).fetchone()
  if not bill:return "Não encontrado",404
  c.execute("UPDATE crm_cobrancas SET situacao='Pago',pago_em=? WHERE id=?",(date.today().isoformat(),bid))
 return redirect("/gestao/cliente/"+str(bill["cliente_id"]))
@app.get("/gestao/cobrancas")
@require
def bills():
 with connection() as c:
  rows=c.execute("SELECT b.*,c.nome FROM crm_cobrancas b JOIN crm_clientes c ON c.id=b.cliente_id ORDER BY b.vencimento DESC").fetchall()
 total=sum(x["valor_centavos"] for x in rows if x["situacao"]!="Pago")
 return render("""<h1>Contas a receber</h1><div class="box"><h2>Em aberto: {{money(total)}}</h2><p>Cadastre cobranças pela ficha de cada cliente.</p><table><tr><th>Cliente</th><th>Cobrança</th><th>Vencimento</th><th>Valor</th><th>Situação</th></tr>{% for x in rows %}<tr><td><a href="/gestao/cliente/{{x['cliente_id']}}">{{x['nome']}}</a></td><td>{{x['descricao']}}</td><td>{{x['vencimento']}}</td><td>{{money(x['valor_centavos'])}}</td><td>{{x['situacao']}}</td></tr>{% endfor %}</table></div>""",rows=rows,total=total)

# MODULOS AGENCIA: planejamento editorial e ordens de servico
with connection() as c:
 c.execute("""CREATE TABLE IF NOT EXISTS planejamento(id INTEGER PRIMARY KEY,cliente_id INTEGER NOT NULL,mes TEXT NOT NULL,objetivo TEXT NOT NULL,publico TEXT DEFAULT '',canais TEXT DEFAULT '',estrategia TEXT DEFAULT '',metas TEXT DEFAULT '',orcamento TEXT DEFAULT '',responsavel TEXT DEFAULT '',status TEXT DEFAULT 'Planejamento',criado TEXT DEFAULT CURRENT_TIMESTAMP)""")
 c.execute("""CREATE TABLE IF NOT EXISTS pauta(id INTEGER PRIMARY KEY,planejamento_id INTEGER NOT NULL,data TEXT,canal TEXT,formato TEXT,tema TEXT NOT NULL,legenda TEXT DEFAULT '',responsavel TEXT DEFAULT '',status TEXT DEFAULT 'Ideia',observacoes TEXT DEFAULT '')""")
 c.execute("""CREATE TABLE IF NOT EXISTS ordem_servico(id INTEGER PRIMARY KEY,cliente_id INTEGER NOT NULL,numero TEXT UNIQUE,servico TEXT NOT NULL,escopo TEXT NOT NULL,entregaveis TEXT DEFAULT '',inicio TEXT,termino TEXT,valor_centavos INTEGER DEFAULT 0,responsavel TEXT DEFAULT '',status TEXT DEFAULT 'Rascunho',observacoes TEXT DEFAULT '',criado TEXT DEFAULT CURRENT_TIMESTAMP)""")
@app.route("/agencia/planejamento",methods=["GET","POST"])
@require
def plano_lista():
 if request.method=="POST":
  cid=request.form.get("cliente_id",type=int);objective=request.form.get("objetivo","").strip()[:500]
  if cid and client_exists(cid) and objective:
   values=[request.form.get(k,"").strip()[:1400] for k in ("mes","publico","canais","estrategia","metas","orcamento","responsavel")]
   with connection() as c:c.execute("INSERT INTO planejamento(cliente_id,objetivo,mes,publico,canais,estrategia,metas,orcamento,responsavel) VALUES(?,?,?,?,?,?,?,?,?)",[cid,objective]+values)
   flash("Planejamento criado.")
  else:flash("Selecione um cliente e defina o objetivo.")
  return redirect("/agencia/planejamento")
 with connection() as c:
  clients=c.execute("SELECT id,nome FROM crm_clientes ORDER BY nome").fetchall()
  plans=c.execute("SELECT p.*,c.nome FROM planejamento p JOIN crm_clientes c ON c.id=p.cliente_id ORDER BY p.id DESC").fetchall()
 return render("""<h1>Planejamento estratégico e editorial</h1><p>Organize objetivos, canais, metas e conteúdos de cada cliente.</p><div class="box"><h3>Novo planejamento</h3><form method="post"><select name="cliente_id" required><option value="">Escolher cliente</option>{% for c in clients %}<option value="{{c['id']}}">{{c['nome']}}</option>{% endfor %}</select><label>Mês de referência</label><input name="mes" type="month" required><input name="objetivo" placeholder="Objetivo da campanha" required><input name="publico" placeholder="Público-alvo"><input name="canais" placeholder="Canais (Instagram, Facebook, Google Ads...)"><textarea name="estrategia" placeholder="Estratégia, tom de voz, mensagens principais"></textarea><textarea name="metas" placeholder="Metas e indicadores (KPIs)"></textarea><input name="orcamento" placeholder="Orçamento previsto"><input name="responsavel" placeholder="Gestor responsável"><button>Criar planejamento</button></form></div><div class="box"><h3>Planejamentos por cliente</h3><table><tr><th>Cliente</th><th>Mês</th><th>Objetivo</th><th>Etapa</th></tr>{% for p in plans %}<tr><td><a href="/agencia/plano/{{p['id']}}">{{p['nome']}}</a></td><td>{{p['mes']}}</td><td>{{p['objetivo']}}</td><td>{{p['status']}}</td></tr>{% endfor %}</table></div>""",clients=clients,plans=plans)
@app.route("/agencia/plano/<int:pid>",methods=["GET","POST"])
@require
def plan_detail(pid):
 with connection() as c: p=c.execute("SELECT p.*,c.nome FROM planejamento p JOIN crm_clientes c ON c.id=p.cliente_id WHERE p.id=?",(pid,)).fetchone()
 if not p:return "Planejamento não encontrado",404
 if request.method=="POST":
  action=request.form.get("action")
  with connection() as c:
   if action=="pauta":
    tema=request.form.get("tema","").strip()[:300]
    if tema:
     vals=[request.form.get(k,"").strip()[:1200] for k in ("data","canal","formato","legenda","responsavel","observacoes")]
     c.execute("INSERT INTO pauta(planejamento_id,tema,data,canal,formato,legenda,responsavel,observacoes) VALUES(?,?,?,?,?,?,?,?)",[pid,tema]+vals)
     flash("Conteúdo adicionado ao calendário.")
   elif action=="status":
    status=request.form.get("status","")
    if status in ("Planejamento","Produção","Aprovação","Publicado","Concluído"):c.execute("UPDATE planejamento SET status=? WHERE id=?",(status,pid))
  return redirect("/agencia/plano/"+str(pid))
 with connection() as c:it=c.execute("SELECT * FROM pauta WHERE planejamento_id=? ORDER BY data,id",(pid,)).fetchall()
 return render("""<p><a href="/agencia/planejamento">← Planejamentos</a></p><h1>{{p['nome']}} · {{p['mes']}}</h1><div class="grid"><div class="box"><h3>Objetivos</h3><p>{{p['objetivo']}}</p><h3>Público</h3><p>{{p['publico']}}</p><h3>Canais</h3><p>{{p['canais']}}</p></div><div class="box"><h3>Estratégia</h3><p style="white-space:pre-wrap">{{p['estrategia']}}</p><h3>KPIs</h3><p>{{p['metas']}}</p><p>Orçamento: {{p['orcamento']}}</p><p>Gestor: {{p['responsavel']}}</p><form method="post"><input type="hidden" name="action" value="status"><select name="status">{% for x in ['Planejamento','Produção','Aprovação','Publicado','Concluído'] %}<option {% if x==p['status'] %}selected{% endif %}>{{x}}</option>{% endfor %}</select><button>Atualizar etapa</button></form></div></div><div class="box"><h3>Calendário editorial · Novo conteúdo</h3><form method="post"><input type="hidden" name="action" value="pauta"><div class="grid"><input name="data" type="date"><input name="canal" placeholder="Instagram, TikTok..."><select name="formato"><option>Reels</option><option>Carrossel</option><option>Stories</option><option>Post estático</option><option>Vídeo</option><option>Outro</option></select><input name="responsavel" placeholder="Responsável"></div><input name="tema" required placeholder="Tema da publicação"><textarea name="legenda" placeholder="Texto / legenda planejada"></textarea><textarea name="observacoes" placeholder="Briefing visual e orientações"></textarea><button>Adicionar conteúdo</button></form></div><div class="box"><h3>Pautas planejadas</h3><table><tr><th>Data</th><th>Canal</th><th>Formato</th><th>Tema</th><th>Responsável</th><th>Status</th></tr>{% for i in it %}<tr><td>{{i['data']}}</td><td>{{i['canal']}}</td><td>{{i['formato']}}</td><td>{{i['tema']}}</td><td>{{i['responsavel']}}</td><td>{{i['status']}}</td></tr>{% endfor %}</table></div>""",p=p,it=it)
@app.route("/agencia/servicos",methods=["GET","POST"])
@require
def os_list():
 if request.method=="POST":
  cid=request.form.get("cliente_id",type=int);service=request.form.get("servico","").strip()[:180];scope=request.form.get("escopo","").strip()[:2000];amount=real(request.form.get("valor",""))
  if cid and client_exists(cid) and service and scope:
   import uuid
   numero="MOVA-"+date.today().strftime("%Y%m")+"-"+uuid.uuid4().hex[:6].upper()
   vals=[request.form.get(k,"").strip()[:1500] for k in ("entregaveis","inicio","termino","responsavel","observacoes")]
   with connection() as c:c.execute("INSERT INTO ordem_servico(cliente_id,numero,servico,escopo,valor_centavos,entregaveis,inicio,termino,responsavel,observacoes) VALUES(?,?,?,?,?,?,?,?,?,?)",[cid,numero,service,scope,amount or 0]+vals)
   flash("Ordem de serviço "+numero+" gerada.")
  else:flash("Informe cliente, serviço e escopo.")
  return redirect("/agencia/servicos")
 with connection() as c:
  clients=c.execute("SELECT id,nome FROM crm_clientes ORDER BY nome").fetchall()
  orders=c.execute("SELECT o.*,c.nome FROM ordem_servico o JOIN crm_clientes c ON c.id=o.cliente_id ORDER BY o.id DESC").fetchall()
 return render("""<h1>Prestação de serviços</h1><p>Gere ordens de serviço vinculadas aos clientes, com numeração automática.</p><div class="box"><h3>Nova ordem de serviço</h3><form method="post"><select name="cliente_id" required><option value="">Selecionar cliente</option>{% for c in clients %}<option value="{{c['id']}}">{{c['nome']}}</option>{% endfor %}</select><input name="servico" required placeholder="Serviço contratado"><textarea name="escopo" required placeholder="Escopo detalhado da prestação do serviço"></textarea><textarea name="entregaveis" placeholder="Entregáveis e quantidades (ex.: 12 posts, 4 reels...)"></textarea><div class="grid"><input type="date" name="inicio"><input type="date" name="termino"><input name="valor" placeholder="Valor, ex.: 2500,00"><input name="responsavel" placeholder="Gestor da conta"></div><textarea name="observacoes" placeholder="Condições adicionais"></textarea><button>Gerar ordem de serviço</button></form></div><div class="box"><h3>Ordens emitidas</h3><table><tr><th>Número</th><th>Cliente</th><th>Serviço</th><th>Valor</th><th>Status</th><th>Documento</th></tr>{% for o in orders %}<tr><td>{{o['numero']}}</td><td>{{o['nome']}}</td><td>{{o['servico']}}</td><td>{{money(o['valor_centavos'])}}</td><td>{{o['status']}}</td><td><a href="/agencia/os/{{o['id']}}">Visualizar</a></td></tr>{% endfor %}</table></div>""",clients=clients,orders=orders)
@app.get("/agencia/os/<int:oid>")
@require
def os_document(oid):
 with connection() as c:o=c.execute("SELECT o.*,c.nome,c.documento,c.email,c.telefone FROM ordem_servico o JOIN crm_clientes c ON c.id=o.cliente_id WHERE o.id=?",(oid,)).fetchone()
 if not o:return "Não encontrado",404
 return render("""<div class="box"><h1>ORDEM DE SERVIÇO · {{o['numero']}}</h1><p><b>Prestadora:</b> MOVA Marketing Digital</p><p><b>Contratante:</b> {{o['nome']}} · {{o['documento'] or ''}}</p><p><b>Contato:</b> {{o['email'] or ''}} · {{o['telefone'] or ''}}</p><h3>Serviço: {{o['servico']}}</h3><p style="white-space:pre-wrap">{{o['escopo']}}</p><h3>Entregáveis</h3><p style="white-space:pre-wrap">{{o['entregaveis']}}</p><p><b>Período:</b> {{o['inicio']}} a {{o['termino']}}</p><p><b>Investimento:</b> {{money(o['valor_centavos'])}}</p><p><b>Responsável:</b> {{o['responsavel']}}</p><p><b>Observações:</b> {{o['observacoes']}}</p><p><b>Status:</b> {{o['status']}}</p><p><small>Documento operacional. Não constitui contrato assinado, nota fiscal ou comprovante de pagamento.</small></p><button onclick="window.print()">Imprimir / salvar PDF</button></div>""",o=o)

@app.get("/agencia/cliente/<int:cid>")
@require
def agency_client(cid):
 with connection() as db:
  client=db.execute("SELECT * FROM crm_clientes WHERE id=?",(cid,)).fetchone()
  if not client:return "Cliente não encontrado",404
  plans=db.execute("SELECT * FROM planejamento WHERE cliente_id=? ORDER BY id DESC",(cid,)).fetchall()
  orders=db.execute("SELECT * FROM ordem_servico WHERE cliente_id=? ORDER BY id DESC",(cid,)).fetchall()
  bills=db.execute("SELECT * FROM crm_cobrancas WHERE cliente_id=? ORDER BY vencimento DESC",(cid,)).fetchall()
  due=sum(x["valor_centavos"] for x in bills if x["situacao"]!="Pago")
 return render("""<a href="/gestao/clientes">← Clientes</a><h1>{{client['nome']}} · Conta 360°</h1><p>{{client['contato'] or ''}} · {{client['email'] or ''}} · {{client['telefone'] or ''}}</p><div class="quick"><a href="/gestao/cliente/{{client['id']}}">Editar e cobrar</a><a href="/agencia/servicos">Nova ordem de serviço</a><a href="/agencia/planejamento">Novo planejamento</a><a href="/studio">Criar artes e aprovações</a></div><div class="grid"><div class="box">Planejamentos <div class="metric">{{plans|length}}</div></div><div class="box">Ordens de serviço <div class="metric">{{orders|length}}</div></div><div class="box">A receber <div class="metric">{{money(due)}}</div></div></div><div class="box"><h3>Planejamentos</h3><table>{% for p in plans %}<tr><td>{{p['mes']}}</td><td>{{p['objetivo']}}</td><td><a href="/agencia/plano/{{p['id']}}">Abrir →</a></td></tr>{% endfor %}</table></div><div class="box"><h3>Ordens de serviço</h3><table>{% for o in orders %}<tr><td>{{o['numero']}}</td><td>{{o['servico']}}</td><td><a href="/agencia/os/{{o['id']}}">Visualizar →</a></td></tr>{% endfor %}</table></div><div class="box"><h3>Cobranças</h3><table>{% for x in bills %}<tr><td>{{x['descricao']}}</td><td>{{x['vencimento']}}</td><td>{{money(x['valor_centavos'])}}</td><td>{{x['situacao']}}</td></tr>{% endfor %}</table></div>""",client=client,plans=plans,orders=orders,bills=bills,due=due)

from datetime import timedelta
with connection() as db:
 db.execute("""CREATE TABLE IF NOT EXISTS alertas(id INTEGER PRIMARY KEY, cliente_id INTEGER, titulo TEXT NOT NULL, tipo TEXT NOT NULL DEFAULT 'Tarefa', prazo TEXT NOT NULL, detalhe TEXT DEFAULT '', concluido INTEGER DEFAULT 0, criado TEXT DEFAULT CURRENT_TIMESTAMP)""")
@app.route("/agencia/producao",methods=["GET","POST"])
@require
def board_production():
 if request.method=="POST":
  pid=request.form.get("id",type=int)
  st=request.form.get("status","")
  if st in ("Ideia","Em produção","Em aprovação","Revisão solicitada","Aprovado","Publicado") and pid:
   with connection() as db:db.execute("UPDATE pauta SET status=? WHERE id=?",(st,pid))
   flash("Status atualizado.")
  return redirect("/agencia/producao")
 with connection() as db:
  rows=db.execute("SELECT p.*,c.nome FROM pauta p JOIN planejamento pl ON pl.id=p.planejamento_id JOIN crm_clientes c ON c.id=pl.cliente_id ORDER BY p.data DESC,p.id DESC").fetchall()
 return render("""<h1>Produção e entregas</h1><p>Itens relacionados aos planejamentos dos clientes; acompanhe cada entrega e seu status.</p><div class="quick"><a href="/agencia/planejamento">+ Criar pauta em planejamento</a><a href="/studio">Estúdio de artes</a></div><div class="box"><table><tr><th>Cliente</th><th>Entrega</th><th>Data</th><th>Responsável</th><th>Atualizar etapa</th></tr>{% for x in rows %}<tr><td>{{x['nome']}}</td><td><a href="/agencia/plano/{{x['planejamento_id']}}">{{x['tema']}}</a><div><small>{{x['canal']}} · {{x['formato']}}</small></div></td><td>{{x['data']}}</td><td>{{x['responsavel']}}</td><td><form method="post"><input type="hidden" name="id" value="{{x['id']}}"><select name="status">{% for st in ['Ideia','Em produção','Em aprovação','Revisão solicitada','Aprovado','Publicado'] %}<option {% if st==x['status'] %}selected{% endif %}>{{st}}</option>{% endfor %}</select><button>Salvar</button></form></td></tr>{% endfor %}</table></div>""",rows=rows)
@app.get("/agencia/aprovacoes")
@require
def board_approvals():
 with connection() as db:
  rows=db.execute("SELECT p.*,c.nome FROM pauta p JOIN planejamento pl ON pl.id=p.planejamento_id JOIN crm_clientes c ON c.id=pl.cliente_id WHERE p.status IN ('Em aprovação','Revisão solicitada','Aprovado') ORDER BY p.data,p.id").fetchall()
 return render("""<h1>Aprovações</h1><p>Itens em aprovação e revisões solicitadas. Altere o status na aba Produção.</p><div class="quick"><a href="/agencia/producao">Abrir Produção</a></div><div class="box"><table><tr><th>Cliente</th><th>Peça</th><th>Prazo</th><th>Status</th></tr>{% for x in rows %}<tr><td>{{x['nome']}}</td><td><a href="/agencia/plano/{{x['planejamento_id']}}">{{x['tema']}}</a></td><td>{{x['data']}}</td><td>{{x['status']}}</td></tr>{% endfor %}</table></div><small>Aprovação externa por login do cliente e anexos ainda não disponível nesta demonstração.</small>""",rows=rows)
@app.get("/agencia/relatorios")
@require
def board_reports():
 with connection() as db:
  rows=db.execute("SELECT c.id,c.nome,(SELECT COUNT(*) FROM planejamento p WHERE p.cliente_id=c.id) planos,(SELECT COUNT(*) FROM ordem_servico o WHERE o.cliente_id=c.id) ordens,(SELECT COALESCE(SUM(valor_centavos),0) FROM crm_cobrancas b WHERE b.cliente_id=c.id AND b.situacao!='Pago') devido FROM crm_clientes c ORDER BY c.nome").fetchall()
 return render("""<h1>Relatórios da agência</h1><p>Consolidado de gestão por cliente.</p><div class="box"><table><tr><th>Cliente</th><th>Planejamentos</th><th>Ordens de serviço</th><th>A receber</th></tr>{% for x in rows %}<tr><td><a href="/agencia/cliente/{{x['id']}}">{{x['nome']}}</a></td><td>{{x['planos']}}</td><td>{{x['ordens']}}</td><td>{{money(x['devido'])}}</td></tr>{% endfor %}</table></div>""",rows=rows)
@app.route("/agencia/alertas",methods=["GET","POST"])
@require
def alarms():
 if request.method=="POST":
  action=request.form.get("action","novo")
  if action=="concluir":
   ident=request.form.get("id",type=int)
   if ident:
    with connection() as db:db.execute("UPDATE alertas SET concluido=1 WHERE id=?",(ident,))
  else:
   title=request.form.get("titulo","").strip()[:180];due=request.form.get("prazo","").strip()
   kind=request.form.get("tipo","Tarefa")
   if kind not in ("Tarefa","Cliente","Cobrança","Aprovação","Reunião"):kind="Tarefa"
   cid=request.form.get("cliente_id",type=int)
   if title and len(due)>=10:
    if cid and not client_exists(cid):cid=None
    with connection() as db:db.execute("INSERT INTO alertas(cliente_id,titulo,tipo,prazo,detalhe) VALUES(?,?,?,?,?)",(cid,title,kind,due[:10],request.form.get("detalhe","")[:1000]))
    flash("Alerta cadastrado.")
   else:flash("Informe título e prazo.")
  return redirect("/agencia/alertas")
 now=date.today().isoformat();soon=(date.today()+timedelta(days=7)).isoformat()
 with connection() as db:
  cs=db.execute("SELECT id,nome FROM crm_clientes ORDER BY nome").fetchall()
  alerts=db.execute("SELECT a.*,c.nome FROM alertas a LEFT JOIN crm_clientes c ON c.id=a.cliente_id WHERE a.concluido=0 ORDER BY a.prazo").fetchall()
  bills=db.execute("SELECT b.*,c.nome FROM crm_cobrancas b JOIN crm_clientes c ON c.id=b.cliente_id WHERE b.situacao!='Pago' AND b.vencimento<=? ORDER BY b.vencimento",(soon,)).fetchall()
  tasks=db.execute("SELECT p.*,c.nome FROM pauta p JOIN planejamento pl ON pl.id=p.planejamento_id JOIN crm_clientes c ON c.id=pl.cliente_id WHERE p.status NOT IN ('Publicado','Aprovado') AND p.data!='' AND p.data<=? ORDER BY p.data",(soon,)).fetchall()
 return render("""<h1>Central de Alertas <span class="pill">{{alerts|length + bills|length + tasks|length}} pendências</span></h1><p>Monitoramento interno de vencimentos, conteúdo e tarefas. Alertas aparecem quando você abre esta página; notificações externas automáticas ainda não estão ativadas.</p><div class="box"><h3>Novo lembrete</h3><form method="post"><input name="titulo" required placeholder="O que precisa ser lembrado?"><div class="grid"><select name="cliente_id"><option value="">Sem cliente</option>{% for c in cs %}<option value="{{c['id']}}">{{c['nome']}}</option>{% endfor %}</select><select name="tipo">{% for x in ['Tarefa','Cliente','Cobrança','Aprovação','Reunião'] %}<option>{{x}}</option>{% endfor %}</select><input type="date" name="prazo" required></div><textarea name="detalhe" placeholder="Detalhes do lembrete"></textarea><button>Criar lembrete</button></form></div><div class="box"><h3>Lembretes manuais</h3><table><tr><th>Prazo</th><th>Tipo</th><th>Cliente</th><th>Descrição</th><th>Ação</th></tr>{% for x in alerts %}<tr><td>{{x['prazo']}} {% if x['prazo'] < today %}⚠ Atrasado{% endif %}</td><td>{{x['tipo']}}</td><td>{{x['nome'] or 'Geral'}}</td><td>{{x['titulo']}}</td><td><form method="post"><input type="hidden" name="action" value="concluir"><input type="hidden" name="id" value="{{x['id']}}"><button>Concluir</button></form></td></tr>{% endfor %}</table></div><div class="box"><h3>Vencimentos financeiros · próximos 7 dias e atrasados</h3><table><tr><th>Cliente</th><th>Vencimento</th><th>Descrição</th><th>Valor</th></tr>{% for x in bills %}<tr><td><a href="/agencia/cliente/{{x['cliente_id']}}">{{x['nome']}}</a></td><td>{{x['vencimento']}}</td><td>{{x['descricao']}}</td><td>{{money(x['valor_centavos'])}}</td></tr>{% endfor %}</table></div><div class="box"><h3>Entregas próximas e atrasadas</h3><table><tr><th>Cliente</th><th>Prazo</th><th>Peça</th><th>Status</th></tr>{% for x in tasks %}<tr><td>{{x['nome']}}</td><td>{{x['data']}}</td><td><a href="/agencia/plano/{{x['planejamento_id']}}">{{x['tema']}}</a></td><td>{{x['status']}}</td></tr>{% endfor %}</table></div>""",alerts=alerts,bills=bills,tasks=tasks,cs=cs,today=now)

from agency_studio import init_studio
init_studio(app, connection, render, require)
