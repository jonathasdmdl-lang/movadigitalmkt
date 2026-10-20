import os, sqlite3, hmac, hashlib, secrets
from functools import wraps
from flask import Flask, request, redirect, session, render_template_string, flash
app=Flask(__name__)
app.secret_key=os.environ["SECRET_KEY"]
DB="/tmp/mova_demo.db"
MODULES={"clientes":"Clientes","projetos":"Projetos","tarefas":"Tarefas","financeiro":"Financeiro","contratos":"Contratos","aprovacoes":"Aprovações"}
def connection():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 return c
with connection() as c:
 for k in MODULES: c.execute("CREATE TABLE IF NOT EXISTS "+k+"(id INTEGER PRIMARY KEY, titulo TEXT NOT NULL, descricao TEXT DEFAULT '', status TEXT DEFAULT 'Pendente', criado TEXT DEFAULT CURRENT_TIMESTAMP)")
HTML="""<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MOVA Gestão</title><style>body{margin:0;background:#0e1119;color:#f0f2f8;font:15px Arial,sans-serif}header{padding:24px;background:#171b29;border-bottom:1px solid #30384d}.brand{font-size:27px;font-weight:900;letter-spacing:1px}.brand span{color:#9baeff}main{max-width:1050px;margin:28px auto;padding:0 18px}a{color:#aabcff;text-decoration:none}nav a{display:inline-block;margin:16px 15px 0 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:15px}.box{background:#1b2232;border:1px solid #343e52;border-radius:14px;padding:22px;margin:12px 0}.warning{background:#30271a;border:1px solid #806435;padding:15px;border-radius:10px;margin:16px 0}input,textarea,select{display:block;width:100%;box-sizing:border-box;padding:12px;margin:10px 0;background:#111726;color:white;border:1px solid #515c78;border-radius:9px}button{background:#94abff;color:#121625;border:0;border-radius:8px;padding:12px 22px;font-weight:700;cursor:pointer}table{width:100%;border-collapse:collapse}th,td{padding:13px;border-bottom:1px solid #394154;text-align:left}</style></head><body><header><div class="brand">MOVA <span>GESTÃO</span></div><small>Estratégia que gera movimento.</small>{% if session.get("user") %}<nav><a href="/">Painel</a>{% for key,label in modules.items() %}<a href="/modulo/{{key}}">{{label}}</a>{% endfor %}<a href="/sair">Sair</a></nav>{% endif %}</header><main><div class="warning">VERSÃO DE DEMONSTRAÇÃO — não cadastre dados pessoais, contratos ou valores reais. Dados temporários, sujeitos a exclusão.</div>{% for msg in get_flashed_messages() %}<p>{{msg}}</p>{% endfor %}{% block main %}{% endblock %}</main></body></html>"""
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
