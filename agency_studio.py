import secrets,hashlib,sqlite3,datetime,html
from flask import request,redirect,flash,session,render_template_string,abort,Response,url_for
from functools import wraps
from urllib.parse import quote
def init_studio(app, connection, render, require):
 with connection() as db:
  db.execute("""CREATE TABLE IF NOT EXISTS studio_pecas(id INTEGER PRIMARY KEY,cliente_id INTEGER NOT NULL,planejamento_id INTEGER,tema TEXT NOT NULL,formato TEXT NOT NULL,canal TEXT NOT NULL,data_prevista TEXT,briefing TEXT,legenda TEXT,cta TEXT,responsavel TEXT,status TEXT NOT NULL DEFAULT 'Rascunho',versao INTEGER NOT NULL DEFAULT 0,criado TEXT DEFAULT CURRENT_TIMESTAMP)""")
  db.execute("""CREATE TABLE IF NOT EXISTS studio_arquivos(id INTEGER PRIMARY KEY,peca_id INTEGER NOT NULL,versao INTEGER NOT NULL,nome TEXT,mime TEXT,bytes BLOB,criado TEXT DEFAULT CURRENT_TIMESTAMP)""")
  db.execute("""CREATE TABLE IF NOT EXISTS studio_links(id INTEGER PRIMARY KEY,peca_id INTEGER NOT NULL,versao INTEGER NOT NULL,token_hash TEXT UNIQUE NOT NULL,expira TEXT NOT NULL,revogado INTEGER DEFAULT 0,criado TEXT DEFAULT CURRENT_TIMESTAMP)""")
  db.execute("""CREATE TABLE IF NOT EXISTS studio_pareceres(id INTEGER PRIMARY KEY,peca_id INTEGER NOT NULL,versao INTEGER NOT NULL,decisao TEXT NOT NULL,observacao TEXT NOT NULL DEFAULT '',criado TEXT DEFAULT CURRENT_TIMESTAMP)""")
 def row(db,sql,args=()):return db.execute(sql,args).fetchone()
 def piece(pid):
  with connection() as db:return row(db,"SELECT p.*,c.nome FROM studio_pecas p JOIN crm_clientes c ON c.id=p.cliente_id WHERE p.id=?",(pid,))
 def auth_token(token):
  digest=hashlib.sha256(token.encode()).hexdigest()
  with connection() as db:
   return row(db,"SELECT l.*,p.tema,p.formato,p.canal,p.legenda,p.cliente_id,c.nome FROM studio_links l JOIN studio_pecas p ON p.id=l.peca_id JOIN crm_clientes c ON c.id=p.cliente_id WHERE l.token_hash=? AND l.revogado=0 AND l.expira>? AND l.versao=p.versao",(digest,datetime.datetime.now(datetime.timezone.utc).isoformat()))
 @app.route("/studio",methods=["GET","POST"])
 @require
 def studio_index():
  if request.method=="POST":
   cid=request.form.get("cliente_id",type=int)
   with connection() as db:
    client=row(db,"SELECT id FROM crm_clientes WHERE id=?",(cid,))
    if not client:flash("Selecione um cliente.");return redirect("/studio")
    tema=request.form.get("tema","").strip()[:180]
    if not tema:flash("Informe o tema.");return redirect("/studio")
    plan=request.form.get("planejamento_id",type=int)
    if plan and not row(db,"SELECT id FROM planejamento WHERE id=? AND cliente_id=?",(plan,cid)):plan=None
    db.execute("INSERT INTO studio_pecas(cliente_id,planejamento_id,tema,formato,canal,data_prevista,briefing,legenda,cta,responsavel) VALUES(?,?,?,?,?,?,?,?,?,?)",(cid,plan,tema,request.form.get("formato","Post")[:40],request.form.get("canal","Instagram")[:70],request.form.get("data_prevista","")[:10],request.form.get("briefing","")[:2000],request.form.get("legenda","")[:3000],request.form.get("cta","")[:400],request.form.get("responsavel","")[:120]))
   flash("Peça criada no planejamento.");return redirect("/studio")
  with connection() as db:
   clients=db.execute("SELECT id,nome FROM crm_clientes ORDER BY nome").fetchall()
   plans=db.execute("SELECT id,cliente_id,mes,objetivo FROM planejamento ORDER BY id DESC").fetchall()
   pieces=db.execute("SELECT p.*,c.nome FROM studio_pecas p JOIN crm_clientes c ON c.id=p.cliente_id ORDER BY p.id DESC").fetchall()
  return render("""<h1>Estúdio MOVA · Planejamento e aprovação</h1><p>Planeje posts, reels, vídeos e campanhas, envie versões e compartilhe uma revisão sem login.</p><div class="box"><h3>Nova peça / pauta</h3><form method="post"><select name="cliente_id" required><option value="">Cliente</option>{% for c in clients %}<option value="{{c['id']}}">{{c['nome']}}</option>{% endfor %}</select><select name="planejamento_id"><option value="">Sem planejamento vinculado</option>{% for p in plans %}<option value="{{p['id']}}">{{p['mes']}} · {{p['objetivo']}}</option>{% endfor %}</select><input name="tema" required placeholder="Tema / título da peça"><div class="grid"><select name="formato"><option>Post estático</option><option>Carrossel</option><option>Reels</option><option>Stories</option><option>Vídeo</option><option>Banner</option></select><select name="canal"><option>Instagram</option><option>Facebook</option><option>TikTok</option><option>LinkedIn</option><option>Google</option><option>Multicanal</option></select><input type="date" name="data_prevista"><input name="responsavel" placeholder="Responsável"></div><textarea name="briefing" placeholder="Objetivo, público, referências, direção visual"></textarea><textarea name="legenda" placeholder="Legenda / roteiro"></textarea><input name="cta" placeholder="Chamada para ação (CTA)"><button>Criar peça</button></form></div><div class="box"><h3>Pipeline editorial</h3><table><tr><th>Cliente</th><th>Conteúdo</th><th>Formato</th><th>Prazo</th><th>Situação</th></tr>{% for p in pieces %}<tr><td>{{p['nome']}}</td><td><a href="/studio/peca/{{p['id']}}">{{p['tema']}}</a></td><td>{{p['formato']}}</td><td>{{p['data_prevista']}}</td><td>{{p['status']}}</td></tr>{% endfor %}</table></div>""",clients=clients,plans=plans,pieces=pieces)
 @app.route("/studio/peca/<int:pid>",methods=["GET","POST"])
 @require
 def studio_detail(pid):
  p=piece(pid)
  if not p:abort(404)
  if request.method=="POST":
   action=request.form.get("action")
   if action=="upload":
    file=request.files.get("arquivo")
    if not file or not file.filename:flash("Escolha uma imagem ou vídeo.")
    else:
     content=file.read(12*1024*1024+1)
     mime=file.mimetype
     if len(content)>12*1024*1024:flash("Limite de 12 MB. Envie vídeos maiores por link externo seguro.")
     elif mime not in ("image/jpeg","image/png","image/webp","image/gif","video/mp4","video/webm","application/pdf"):flash("Formato de arquivo não permitido.")
     else:
      with connection() as db:
       vers=p["versao"]+1
       db.execute("UPDATE studio_pecas SET versao=?,status='Em revisão' WHERE id=?",(vers,pid))
       db.execute("UPDATE studio_links SET revogado=1 WHERE peca_id=?",(pid,))
       db.execute("INSERT INTO studio_arquivos(peca_id,versao,nome,mime,bytes) VALUES(?,?,?,?,?)",(pid,vers,file.filename[:180],mime,content))
      flash("Nova versão anexada. Links anteriores revogados.")
   elif action=="link":
    if p["versao"]<=0:flash("Envie um arquivo antes de gerar o link.")
    else:
     token=secrets.token_urlsafe(32)
     expires=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=7)).isoformat()
     with connection() as db:db.execute("INSERT INTO studio_links(peca_id,versao,token_hash,expira) VALUES(?,?,?,?)",(pid,p["versao"],hashlib.sha256(token.encode()).hexdigest(),expires))
     session["studio_last_link"]=request.host_url.rstrip("/")+"/revisao/"+token
     flash("Link individual criado. Copie e envie pelo WhatsApp ou e-mail.")
   elif action=="revogar":
    with connection() as db:db.execute("UPDATE studio_links SET revogado=1 WHERE peca_id=?",(pid,))
    flash("Links de revisão revogados.")
   return redirect("/studio/peca/"+str(pid))
  with connection() as db:
   arquivo=row(db,"SELECT id,nome,mime,versao FROM studio_arquivos WHERE peca_id=? ORDER BY id DESC LIMIT 1",(pid,))
   pareceres=db.execute("SELECT * FROM studio_pareceres WHERE peca_id=? ORDER BY id DESC",(pid,)).fetchall()
  last=session.pop("studio_last_link",None)
  return render("""<p><a href="/studio">← Estúdio</a></p><h1>{{p['tema']}}</h1><p><a href="/agencia/cliente/{{p['cliente_id']}}">{{p['nome']}}</a> · {{p['canal']}} · {{p['formato']}} · Prazo {{p['data_prevista']}}</p><div class="grid"><div class="box"><h3>Briefing e legenda</h3><p style="white-space:pre-wrap">{{p['briefing']}}</p><h4>Legenda</h4><p style="white-space:pre-wrap">{{p['legenda']}}</p><b>CTA:</b> {{p['cta']}}</div><div class="box"><h3>Enviar arte ou vídeo</h3><p>Versão atual: {{p['versao']}} · {{p['status']}}</p><form method="post" enctype="multipart/form-data"><input type="hidden" name="action" value="upload"><input type="file" name="arquivo" accept="image/png,image/jpeg,image/webp,image/gif,video/mp4,video/webm,application/pdf" required><button>Enviar nova versão</button></form>{% if arquivo %}<p>Arquivo: {{arquivo['nome']}}</p><a href="/studio/arquivo/{{arquivo['id']}}">Visualizar arquivo</a>{% endif %}</div></div><div class="box"><h3>Aprovação por link externo</h3><p>Link individual por 7 dias. O cliente não precisa de login e só visualiza esta peça. Qualquer pessoa com o link poderá responder: envie apenas ao destinatário.</p><form method="post"><input type="hidden" name="action" value="link"><button>Gerar link de aprovação</button></form>{% if last %}<input readonly value="{{last}}"><a href="{{last}}" target="_blank">Testar link</a><p><a href="https://wa.me/?text={{('Veja e aprove a arte da MOVA: '+last)|urlencode}}" target="_blank">Compartilhar no WhatsApp ↗</a></p>{% endif %}<form method="post"><input type="hidden" name="action" value="revogar"><button>Revogar links ativos</button></form></div><div class="box"><h3>Histórico de decisões</h3><table><tr><th>Versão</th><th>Decisão</th><th>Observações</th><th>Data</th></tr>{% for x in pareceres %}<tr><td>{{x['versao']}}</td><td>{{x['decisao']}}</td><td>{{x['observacao']}}</td><td>{{x['criado']}}</td></tr>{% endfor %}</table></div>""",p=p,arquivo=arquivo,pareceres=pareceres,last=last)
 @app.get("/studio/arquivo/<int:fid>")
 @require
 def private_file(fid):
  with connection() as db:f=row(db,"SELECT nome,mime,bytes FROM studio_arquivos WHERE id=?",(fid,))
  if not f:abort(404)
  return Response(f["bytes"],mimetype=f["mime"],headers={"Cache-Control":"no-store","Content-Disposition":"inline"})
 @app.route("/revisao/<token>",methods=["GET","POST"])
 def public_review(token):
  link=auth_token(token)
  if not link:return render_template_string("<h2>Este link expirou ou foi revogado.</h2>"),410
  if request.method=="POST":
   decision=request.form.get("decisao")
   notes=request.form.get("observacao","").strip()[:1500]
   if decision not in ("Aprovado","Alterações solicitadas"):abort(400)
   if decision=="Alterações solicitadas" and not notes:return "Descreva os ajustes solicitados.",400
   with connection() as db:
    db.execute("INSERT INTO studio_pareceres(peca_id,versao,decisao,observacao) VALUES(?,?,?,?)",(link["peca_id"],link["versao"],decision,notes))
    db.execute("UPDATE studio_pecas SET status=? WHERE id=?",(decision,link["peca_id"]))
    db.execute("UPDATE studio_links SET revogado=1 WHERE id=?",(link["id"],))
   return render_template_string("<html lang='pt-br'><meta charset='utf-8'><body style='background:#11182a;color:white;font:18px Arial;text-align:center;padding:80px'><h1>Resposta registrada!</h1><p>A MOVA recebeu sua decisão. Obrigado.</p></body></html>")
  with connection() as db:f=row(db,"SELECT id,mime FROM studio_arquivos WHERE peca_id=? AND versao=? ORDER BY id DESC",(link["peca_id"],link["versao"]))
  if not f:return "Arquivo indisponível",404
  return render_template_string("""<html lang="pt-br"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MOVA · Aprovação</title><style>body{background:#0e1425;color:#f1f4fb;font:16px Arial;margin:0}main{max-width:850px;margin:40px auto;padding:24px;background:#202b43;border-radius:20px}img,video,iframe{max-width:100%;width:100%;max-height:65vh;object-fit:contain;border-radius:12px;background:#0b1120}textarea{box-sizing:border-box;width:100%;min-height:110px;margin:15px 0;padding:12px}button{border:0;border-radius:9px;padding:14px;margin:5px;font-weight:bold;cursor:pointer}.yes{background:#98e4b9}.no{background:#f7c2be}</style><main><h1>MOVA <small>· Revisão de conteúdo</small></h1><p>Cliente: {{link['nome']}}</p><h2>{{link['tema']}}</h2><p>{{link['canal']}} · {{link['formato']}} · Versão {{link['versao']}}</p>{% if mime.startswith('image/') %}<img src="/revisao/{{token}}/arquivo">{% elif mime.startswith('video/') %}<video src="/revisao/{{token}}/arquivo" controls></video>{% else %}<iframe src="/revisao/{{token}}/arquivo" height="500"></iframe>{% endif %}<h3>Legenda / texto</h3><p style="white-space:pre-wrap">{{link['legenda']}}</p><form method="post"><label>Observações ou ajustes</label><textarea name="observacao" placeholder="Escreva aqui ajustes, correções ou comentários"></textarea><button class="yes" name="decisao" value="Aprovado">Aprovar esta versão</button><button class="no" name="decisao" value="Alterações solicitadas">Solicitar alterações</button></form><small>Link exclusivo e temporário. Não encaminhe a terceiros.</small></main></html>""",link=link,token=token,mime=f["mime"])
 @app.get("/revisao/<token>/arquivo")
 def public_file(token):
  l=auth_token(token)
  if not l:abort(404)
  with connection() as db:f=row(db,"SELECT bytes,mime FROM studio_arquivos WHERE peca_id=? AND versao=? ORDER BY id DESC",(l["peca_id"],l["versao"]))
  if not f:abort(404)
  return Response(f["bytes"],mimetype=f["mime"],headers={"Cache-Control":"private, no-store","Content-Disposition":"inline","X-Content-Type-Options":"nosniff"})
