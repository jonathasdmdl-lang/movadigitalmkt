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
HTML="""<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MOVA Gestão</title><style>body{margin:0;background:#0e1119;color:#f0f2f8;font:15px Arial,sans-serif}header{padding:24px;background:#171b29;border-bottom:1px solid #30384d}.brand{font-size:27px;font-weight:900;letter-spacing:1px}.brand span{color:#9baeff}main{max-width:1050px;margin:28px auto;padding:0 18px}a{color:#aabcff;text-decoration:none}nav a{display:inline-block;margin:16px 15px 0 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:15px}.box{background:#1b2232;border:1px solid #343e52;border-radius:14px;padding:22px;margin:12px 0}.warning{background:#30271a;border:1px solid #806435;padding:15px;border-radius:10px;margin:16px 0}input,textarea,select{display:block;width:100%;box-sizing:border-box;padding:12px;margin:10px 0;background:#111726;color:white;border:1px solid #515c78;border-radius:9px}button{background:#94abff;color:#121625;border:0;border-radius:8px;padding:12px 22px;font-weight:700;cursor:pointer}table{width:100%;border-collapse:collapse}th,td{padding:13px;border-bottom:1px solid #394154;text-align:left}</style></head><body><header><div class="brand">MOVA <span>GESTÃO</span></div><small>Estratégia que gera movimento.</small>{% if session.get("user") %}<nav><a href="/">Painel</a><a href="/gestao/clientes">Gestão de clientes</a><a href="/gestao/cobrancas">Cobranças</a>{% for key,label in modules.items() %}<a href="/modulo/{{key}}">{{label}}</a>{% endfor %}<a href="/sair">Sair</a></nav>{% endif %}</header><main><div class="warning">VERSÃO DE DEMONSTRAÇÃO — não cadastre dados pessoais, contratos ou valores reais. Dados temporários, sujeitos a exclusão.</div>{% for msg in get_flashed_messages() %}<p>{{msg}}</p>{% endfor %}{% block main %}{% endblock %}</main></body></html>"""
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
 return render("""<h1>Gestão de clientes</h1><div class="box"><h3>Novo cliente</h3><form method="post"><input name="nome" required placeholder="Nome da empresa ou cliente"><div class="grid"><input name="documento" placeholder="CPF/CNPJ"><input name="email" type="email" placeholder="E-mail"><input name="telefone" placeholder="Telefone / WhatsApp"><input name="contato" placeholder="Pessoa responsável"></div><input name="endereco" placeholder="Endereço"><textarea name="observacoes" placeholder="Observações e necessidades"></textarea><button>Salvar cliente</button></form></div><div class="box"><h3>Clientes cadastrados</h3><table><tr><th>Cliente</th><th>Contato</th><th>Gestão</th></tr>{% for c in clients %}<tr><td>{{c['nome']}}</td><td>{{c['telefone'] or c['email']}}</td><td><a href="/gestao/cliente/{{c['id']}}">Abrir ficha →</a></td></tr>{% endfor %}</table></div>""",clients=clients)
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
