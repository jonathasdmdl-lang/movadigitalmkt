from flask import request, redirect, flash, session, abort
from decimal import Decimal, InvalidOperation
from datetime import date
from calendar import monthrange
import secrets

def init_painel(app, connection, render, require, money):
 @app.get("/mova")
 @require
 def mova_home():
  today=date.today().isoformat()
  with connection() as db:
   clientes=db.execute("SELECT COUNT(*) FROM crm_clientes").fetchone()[0]
   planejamentos=db.execute("SELECT COUNT(*) FROM planejamento").fetchone()[0]
   pecas=db.execute("SELECT COUNT(*) FROM studio_pecas").fetchone()[0]
   aprovacoes=db.execute("SELECT COUNT(*) FROM studio_pecas WHERE status IN ('Em revisão','Alterações solicitadas')").fetchone()[0]
   vencer=db.execute("SELECT COUNT(*) FROM crm_cobrancas WHERE situacao!='Pago' AND vencimento<?",(today,)).fetchone()[0]
   receber=db.execute("SELECT COALESCE(SUM(valor_centavos),0) FROM crm_cobrancas WHERE situacao!='Pago'").fetchone()[0]
   lista=db.execute("SELECT id,nome,telefone FROM crm_clientes ORDER BY id DESC LIMIT 8").fetchall()
   proximas=db.execute("SELECT p.id,p.tema,p.data_prevista,p.status,c.nome FROM studio_pecas p JOIN crm_clientes c ON c.id=p.cliente_id WHERE p.data_prevista!='' AND p.status NOT IN ('Aprovado','Publicado') ORDER BY p.data_prevista LIMIT 8").fetchall()
  return render("""<div class="box hero"><div class="eyebrow">CENTRAL DE OPERAÇÕES</div><h1>MOVA Gestão</h1><p>Estratégia que gera movimento. Clientes, produção, aprovações e financeiro no mesmo fluxo.</p><div class="quick"><a href="/gestao/clientes">+ Cliente</a><a href="/studio">+ Conteúdo</a><a href="/agencia/planejamento">+ Planejamento</a></div></div><div class="grid"><div class="box kpi"><div class="metric-label">Clientes</div><div class="metric">{{clientes}}</div><div class="metric-note">Contas na agência</div></div><div class="box kpi"><div class="metric-label">Produção criativa</div><div class="metric">{{pecas}}</div><div class="metric-note">{{planejamentos}} planejamentos</div></div><div class="box kpi"><div class="metric-label">Em aprovação</div><div class="metric">{{aprovacoes}}</div><div class="metric-note"><a href="/mova/aprovacoes">Revisar peças →</a></div></div><div class="box kpi"><div class="metric-label">A receber</div><div class="metric">{{money(receber)}}</div><div class="metric-note">{{vencer}} cobrança(s) em atraso</div></div></div><div class="layout-2"><div class="box"><div class="section-title">Clientes recentes <a href="/gestao/clientes" class="mini">Todos →</a></div><div class="table-wrap"><table><tr><th>Cliente</th><th>Contato</th><th>Painel</th></tr>{% for x in lista %}<tr><td><strong>{{x['nome']}}</strong></td><td>{{x['telefone'] or '—'}}</td><td><a href="/mova/cliente/{{x['id']}}">Abrir 360° →</a></td></tr>{% endfor %}</table></div>{% if not lista %}<div class="empty">Cadastre seu primeiro cliente para começar.</div>{% endif %}</div><div class="box"><div class="section-title">Próximas entregas <a href="/studio" class="mini">Estúdio →</a></div><table><tr><th>Conteúdo</th><th>Data</th></tr>{% for x in proximas %}<tr><td><a href="/studio/peca/{{x['id']}}">{{x['tema']}}</a><div class="subtle">{{x['nome']}}</div></td><td>{{x['data_prevista']}}</td></tr>{% endfor %}</table>{% if not proximas %}<div class="empty">Nenhuma entrega pendente com prazo.</div>{% endif %}</div></div><div class="box"><h3>Operação integrada</h3><div class="strip"><span class="step">01 Cliente</span><span class="step-arrow">→</span><span class="step">02 Serviços</span><span class="step-arrow">→</span><span class="step">03 Planejamento</span><span class="step-arrow">→</span><span class="step">04 Produção</span><span class="step-arrow">→</span><span class="step">05 Aprovação</span><span class="step-arrow">→</span><span class="step">06 Cobrança</span></div></div>""",clientes=clientes,pecas=pecas,planejamentos=planejamentos,aprovacoes=aprovacoes,vencer=vencer,receber=receber,lista=lista,proximas=proximas)

 @app.get("/mova/cliente/<int:cid>")
 @require
 def mova_account(cid):
  with connection() as db:
   c=db.execute("SELECT * FROM crm_clientes WHERE id=?",(cid,)).fetchone()
   if not c:abort(404)
   contratos=db.execute("SELECT * FROM crm_contratos WHERE cliente_id=? ORDER BY id DESC",(cid,)).fetchall()
   planos=db.execute("SELECT * FROM planejamento WHERE cliente_id=? ORDER BY id DESC",(cid,)).fetchall()
   pecas=db.execute("SELECT * FROM studio_pecas WHERE cliente_id=? ORDER BY id DESC",(cid,)).fetchall()
   ordens=db.execute("SELECT * FROM ordem_servico WHERE cliente_id=? ORDER BY id DESC",(cid,)).fetchall()
   contas=db.execute("SELECT * FROM crm_cobrancas WHERE cliente_id=? ORDER BY vencimento",(cid,)).fetchall()
  pendente=sum(x["valor_centavos"] for x in contas if x["situacao"]!="Pago")
  csrf=session.setdefault("mova_csrf",secrets.token_urlsafe(24))
  return render("""<div class="toprow"><div><div class="eyebrow">CLIENTE / VISÃO 360°</div><h1>{{c['nome']}}</h1><p class="subtle">{{c['contato'] or 'Contato não definido'}} · {{c['email'] or 'Sem e-mail'}} · {{c['telefone'] or 'Sem telefone'}}</p></div><a href="/gestao/clientes">← Todos os clientes</a></div><div class="quick"><a href="/gestao/cliente/{{c['id']}}">Editar cadastro</a><a href="/agencia/planejamento">Novo planejamento</a><a href="/studio">Criar arte e aprovação</a><a href="/agencia/servicos">Gerar OS</a></div><div class="grid"><div class="box kpi"><div class="metric-label">Serviços</div><div class="metric">{{contratos|length}}</div></div><div class="box kpi"><div class="metric-label">Planejamentos</div><div class="metric">{{planos|length}}</div></div><div class="box kpi"><div class="metric-label">Peças</div><div class="metric">{{pecas|length}}</div></div><div class="box kpi"><div class="metric-label">A receber</div><div class="metric">{{money(pendente)}}</div></div></div><div class="box"><h3>Contratar pacote e gerar parcelas automaticamente</h3><p class="subtle">Informe a mensalidade, a quantidade de meses e o primeiro vencimento. As cobranças serão criadas no financeiro e vinculadas ao contrato.</p><form method="post" action="/mova/cliente/{{c['id']}}/pacote"><input type="hidden" name="csrf" value="{{csrf}}"><div class="control-row"><label>Serviço<input name="servico" required placeholder="Gestão de redes sociais"></label><label>Mensalidade (R$)<input name="mensalidade" required placeholder="1500,00"></label><label>Meses<input name="meses" required type="number" min="1" max="36" value="3"></label><label>Primeiro vencimento<input name="vencimento" type="date" required></label></div><button>Gerar contrato e cobranças</button></form></div><div class="layout-2"><div class="box"><div class="section-title">Planejamentos <a href="/agencia/planejamento" class="mini">Novo →</a></div><div class="table-wrap"><table><tr><th>Mês</th><th>Objetivo</th><th>Etapa</th></tr>{% for x in planos %}<tr><td><a href="/agencia/plano/{{x['id']}}">{{x['mes']}}</a></td><td>{{x['objetivo']}}</td><td><span class="tag">{{x['status']}}</span></td></tr>{% endfor %}</table></div></div><div class="box"><div class="section-title">Peças e aprovações <a href="/studio" class="mini">Estúdio →</a></div><table><tr><th>Arte</th><th>Status</th></tr>{% for x in pecas %}<tr><td><a href="/studio/peca/{{x['id']}}">{{x['tema']}}</a></td><td><span class="tag">{{x['status']}}</span></td></tr>{% endfor %}</table></div></div><div class="box"><div class="section-title">Financeiro <a href="/gestao/cliente/{{c['id']}}" class="mini">Gerenciar →</a></div><div class="table-wrap"><table><tr><th>Referência</th><th>Vencimento</th><th>Valor</th><th>Situação</th></tr>{% for x in contas %}<tr><td>{{x['descricao']}}</td><td>{{x['vencimento']}}</td><td>{{money(x['valor_centavos'])}}</td><td><span class="tag">{{x['situacao']}}</span></td></tr>{% endfor %}</table></div></div><div class="box"><div class="section-title">Ordens de serviço <a href="/agencia/servicos" class="mini">Nova OS →</a></div><div class="table-wrap"><table><tr><th>Número</th><th>Serviço</th><th>Valor</th><th>Ação</th></tr>{% for x in ordens %}<tr><td>{{x['numero']}}</td><td>{{x['servico']}}</td><td>{{money(x['valor_centavos'])}}</td><td><a href="/agencia/os/{{x['id']}}">Ver documento</a></td></tr>{% endfor %}</table></div></div>""",c=c,csrf=csrf,contratos=contratos,planos=planos,pecas=pecas,ordens=ordens,contas=contas,pendente=pendente)

 @app.post("/mova/cliente/<int:cid>/pacote")
 @require
 def mova_package(cid):
  if request.form.get("csrf")!=session.get("mova_csrf"):abort(403)
  servico=request.form.get("servico","").strip()[:180]
  try:
   valor=Decimal(request.form.get("mensalidade","").strip().replace(".","").replace(",","."))
   centavos=int(valor*100)
   meses=int(request.form.get("meses","0"))
   first=date.fromisoformat(request.form.get("vencimento",""))
  except (ValueError,InvalidOperation,OverflowError):
   flash("Verifique mensalidade, meses e data.");return redirect(f"/mova/cliente/{cid}")
  if not servico or centavos<=0 or centavos>100000000 or not 1<=meses<=36:
   flash("Preencha valores válidos.");return redirect(f"/mova/cliente/{cid}")
  with connection() as db:
   if not db.execute("SELECT 1 FROM crm_clientes WHERE id=?",(cid,)).fetchone():abort(404)
   cur=db.execute("INSERT INTO crm_contratos(cliente_id,servico,valor_centavos,parcelas,inicio,observacoes) VALUES(?,?,?,?,?,?)",(cid,servico,centavos*meses,meses,first.isoformat(),"Parcelas automáticas geradas no MOVA"))
   contract_id=cur.lastrowid
   for i in range(meses):
    month=first.month-1+i;year=first.year+month//12;month=month%12+1
    due=date(year,month,min(first.day,monthrange(year,month)[1])).isoformat()
    db.execute("INSERT INTO crm_cobrancas(cliente_id,contrato_id,descricao,vencimento,valor_centavos,referencia) VALUES(?,?,?,?,?,?)",(cid,contract_id,f"{servico} · {i+1}/{meses}",due,centavos,f"CTR-{contract_id}-{i+1:02d}"))
  flash(f"Contrato registrado e {meses} cobrança(s) gerada(s).")
  return redirect(f"/mova/cliente/{cid}")
