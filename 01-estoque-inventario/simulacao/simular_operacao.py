"""
Simula, dia a dia, 12 meses de um centro de distribuição fictício (40 SKUs).
Gera demanda, reposição por ponto de pedido, atrasos de fornecedor, avarias, bloqueios, contagens e descontinuação de SKUs.
Uso: python simular_operacao.py saida/sim.pkl

Projeto de portfólio com dados 100% fictícios.
"""
import numpy as np, pandas as pd, math, pickle, sys
from datetime import date, timedelta
from collections import deque, defaultdict

rng = np.random.default_rng(2026)
START = date(2025, 10, 1)
NDAYS = 365
DATES = [START + timedelta(days=i) for i in range(NDAYS)]
END = DATES[-1]

PRODUTOS = [
 ("Arroz tipo 1 5kg","Alimentos secos"),("Feijão carioca 1kg","Alimentos secos"),("Macarrão espaguete 500g","Alimentos secos"),
 ("Açúcar refinado 1kg","Alimentos secos"),("Farinha de trigo 1kg","Alimentos secos"),("Óleo de soja 900ml","Alimentos secos"),
 ("Café torrado 500g","Alimentos secos"),("Molho de tomate 340g","Alimentos secos"),("Sal refinado 1kg","Alimentos secos"),
 ("Biscoito cream cracker 400g","Alimentos secos"),
 ("Água mineral 1,5L","Bebidas"),("Refrigerante cola 2L","Bebidas"),("Suco de uva 1L","Bebidas"),("Cerveja lata 350ml","Bebidas"),
 ("Energético 250ml","Bebidas"),("Chá gelado 1,5L","Bebidas"),("Água com gás 500ml","Bebidas"),
 ("Detergente líquido 500ml","Limpeza"),("Sabão em pó 1kg","Limpeza"),("Amaciante 2L","Limpeza"),("Desinfetante 1L","Limpeza"),
 ("Água sanitária 2L","Limpeza"),("Esponja multiuso","Limpeza"),("Limpa vidros 500ml","Limpeza"),("Multiuso 500ml","Limpeza"),
 ("Shampoo 350ml","Higiene"),("Condicionador 350ml","Higiene"),("Sabonete 90g","Higiene"),("Creme dental 90g","Higiene"),
 ("Papel higiênico 12un","Higiene"),("Desodorante aerosol","Higiene"),("Absorvente 8un","Higiene"),("Fralda G 30un","Higiene"),
 ("Sacola plástica 50un","Embalagens"),("Filme PVC rolo","Embalagens"),("Papel alumínio rolo","Embalagens"),("Saco de lixo 50L","Embalagens"),
 ("Copo descartável 200ml","Embalagens"),("Marmitex alumínio","Embalagens"),("Caixa de papelão M","Embalagens"),
]
BASE_COST = {"Alimentos secos":9,"Bebidas":7,"Limpeza":8,"Higiene":14,"Embalagens":6}
QC_DIAS = {"Alimentos secos":2,"Bebidas":0,"Limpeza":0,"Higiene":1,"Embalagens":0}

FORNECEDORES = [
 ("FOR01","Fornecedor Alfa",5,0.08),("FOR02","Fornecedor Beta",7,0.15),("FOR03","Fornecedor Gama",8,0.10),
 ("FOR04","Fornecedor Delta",10,0.20),("FOR05","Fornecedor Épsilon",12,0.12),("FOR06","Fornecedor Zeta",14,0.30),
 ("FOR07","Fornecedor Eta",6,0.06),("FOR08","Fornecedor Teta",9,0.18),
]
FOR_BY_CAT = {"Alimentos secos":["FOR01","FOR02","FOR03"],"Bebidas":["FOR04","FOR05"],"Limpeza":["FOR06","FOR07"],
              "Higiene":["FOR07","FOR08"],"Embalagens":["FOR06","FOR08"]}
FOR_D = {f[0]:f for f in FORNECEDORES}

SLOW_IDX = [8, 19, 33]
DISC_IDX = {4: date(2026,2,15), 13: date(2026,3,20), 22: date(2026,5,10), 29: date(2026,6,15), 36: date(2026,8,1)}

# ---------- produtos
prods = []
for i,(desc,cat) in enumerate(PRODUTOS):
    mean_d = float(np.clip(rng.lognormal(math.log(45),0.8),8,300))
    cost = float(np.clip(BASE_COST[cat]*rng.lognormal(0,0.5),2.5,60))
    if i in SLOW_IDX:
        mean_d = float(rng.uniform(5,9)); cost *= 2
    margin = float(rng.uniform(0.18,0.45))
    f = str(rng.choice(FOR_BY_CAT[cat]))
    lt = FOR_D[f][2]
    cv = float(rng.uniform(0.30,0.55))
    prods.append(dict(sku=f"SKU{i+1:03d}", desc=desc, cat=cat, mean_d=mean_d, cost=round(cost,2),
                      preco=round(cost*(1+margin),2), forn=f, lt=lt, cv=cv,
                      disc=DISC_IDX.get(i), slow=(i in SLOW_IDX), trend=float(rng.uniform(-0.004,0.008))))
# classe ABC por valor anual
vals = sorted([(p['mean_d']*p['cost'],k) for k,p in enumerate(prods)], reverse=True)
for rank,(v,k) in enumerate(vals):
    prods[k]['cls'] = 'A' if rank<8 else ('B' if rank<20 else 'C')
for k,p in enumerate(prods):
    sd = p['mean_d']*p['cv']
    p['ss'] = int(math.ceil(1.65*sd*math.sqrt(p['lt'])))
    p['min'] = int(math.ceil(0.5*p['ss']))
    p['rop'] = int(math.ceil(p['mean_d']*p['lt']+p['ss']))
    p['max'] = int(math.ceil(p['rop']+p['mean_d']*28))
    # endereço
    rua = 1 + k//8
    p['end'] = f"R{rua:02d}-P{(k%8)+1:02d}-N{1+(k*3)%4:02d}"
    # cobertura inicial
    if p['slow']: p['cov0'] = float(rng.uniform(110,160))
    else:
        r = rng.random()
        p['cov0'] = float(rng.uniform(3,8)) if r<0.15 else (float(rng.uniform(45,75)) if r<0.35 else float(rng.uniform(12,30)))


for k,p in enumerate(prods):
    p['shock']=None
    if (not p['disc']) and (not p['slow']) and rng.random()<0.3:
        st=START+timedelta(days=int(rng.integers(90,240)))
        p['shock']=(st,st+timedelta(days=int(rng.integers(60,91))),float(rng.uniform(0.4,0.6)))

SEAS={10:1.0,11:1.08,12:1.2,1:0.92,2:0.9,3:0.98,4:1.0,5:1.02,6:0.97,7:1.0,8:1.03,9:1.05}
def season(m,cat):
    s=SEAS[m]
    if cat=='Bebidas' and m in (12,1,2): s*=1.18
    return s
WD_RAW=[1.2,1.15,1.1,1.1,1.15,0.9,0.0]
WF=[w/(sum(WD_RAW)/7) for w in WD_RAW]
CANAIS=['Varejo','Atacado','E-commerce']; CANAL_P=[0.5,0.3,0.2]
P_TRUE={'A':0.03,'B':0.045,'C':0.07}; P_END={'A':0.02,'B':0.03,'C':0.05}
CONTADORES=['Ana','Bruno','Carla','Diego','Elisa','Fábio']
INTERVAL={'A':14,'B':30,'C':60}

def consume(layers,q):
    while q>0 and layers:
        if layers[0][1]<=q:
            q-=layers[0][1]; layers.popleft()
        else:
            layers[0][1]-=q; q=0
def total(layers): return sum(l[1] for l in layers)
def split_lines(q):
    if q<=0: return []
    n=min(1+(q>30)+(q>100),q)
    if n==1: return [int(q)]
    cuts=np.sort(rng.choice(np.arange(1,q),size=n-1,replace=False))
    parts=np.diff(np.concatenate([[0],cuts,[q]]))
    return [int(x) for x in parts if x>0]

mov_rows=[]; ped_rows=[]; po_rows=[]; cnt_rows=[]; snap_rows=[]

for p in prods:
    sku=p['sku']; cost=p['cost']; cls=p['cls']; cat=p['cat']; disc=p['disc']
    layers=deque()
    q0=int(p['mean_d']*p['cov0'])
    amax = 150 if p['slow'] else 40
    ages=sorted(rng.integers(2,amax,size=3),reverse=True)
    parts=(rng.dirichlet(np.ones(3))*q0).astype(int)
    for a,pq in zip(ages,parts): layers.append([START-timedelta(days=int(a)),int(pq)])
    bloq=None; quar=[]; avar=[]; pos=[]
    gap=0
    dm=deque([p['mean_d']]*30,maxlen=30)
    # plano de contagem
    exec_map=defaultdict(list)
    interval=INTERVAL[cls]
    pd_=START+timedelta(days=int(rng.integers(3,interval+3)))
    while pd_<=END:
        pdt=pd_ if pd_.weekday()!=6 else pd_+timedelta(1)
        if pdt>END: break
        r=rng.random()
        if r<0.75: delay=0
        elif r<0.83: delay=1
        elif r<0.90: delay=int(rng.integers(2,6))
        else: delay=None
        ex=None
        if delay is not None:
            ex=pdt+timedelta(delay)
            if ex.weekday()==6: ex+=timedelta(1)
            if ex>END: ex=None
        c=dict(sku=sku,plan=pdt,exec=ex,tipo='Cíclica',delay=(None if ex is None else (ex-pdt).days))
        if ex is not None: exec_map[ex].append(c)
        else: cnt_rows.append(dict(c,realizada=0))
        pd_+=timedelta(interval)
    gdate=date(2026,3,31)
    exec_map[gdate].append(dict(sku=sku,plan=gdate,exec=gdate,tipo='Geral',delay=0))

    for di,d in enumerate(DATES):
        # 1. recebimentos
        for po in [x for x in pos if x['rec'] is not None and x['rec']==d]:
            q=po['qtd_rec']
            layers.append([d,q])
            if QC_DIAS[cat]>0: quar.append([q,d+timedelta(QC_DIAS[cat])])
            mov_rows.append(dict(data=d,sku=sku,tipo_mov='ENTRADA_COMPRA',qtd=q,valor=round(q*cost,2),motivo='Recebimento de compra',documento=po['id_tmp'],perda_nao_explicada=0))
            po['recebido']=1; po['done']=True
        pos=[x for x in pos if not x.get('done')]
        quar=[x for x in quar if x[1]>d]
        # avarias liberadas -> baixa
        keep=[]
        for a in avar:
            if a[1]<=d:
                q=min(a[0],total(layers))
                if q>0:
                    consume(layers,q)
                    mov_rows.append(dict(data=d,sku=sku,tipo_mov='AVARIA',qtd=-q,valor=round(-q*cost,2),motivo='Avaria (armazenagem/movimentação)',documento='AV-'+d.strftime('%Y%m%d'),perda_nao_explicada=0))
            else: keep.append(a)
        avar=keep
        if bloq and bloq[1]<=d: bloq=None
        # descarte obsoleto
        if disc:
            for off,frac in ((45,0.20),(120,0.15)):
                if d==disc+timedelta(off):
                    q=int(total(layers)*frac)
                    if q>0:
                        consume(layers,q)
                        mov_rows.append(dict(data=d,sku=sku,tipo_mov='DESCARTE_OBSOLETO',qtd=-q,valor=round(-q*cost,2),motivo='Descarte de item descontinuado',documento='DESC-'+d.strftime('%Y%m%d'),perda_nao_explicada=0))
        # 2. contagens
        for c in exec_map.get(d,[]):
            sist=total(layers)
            true_div=0
            if sist>0 and rng.random()<P_TRUE[cls]:
                mag=max(1,int(round(abs(rng.normal(0,0.06))*sist)))
                true_div=-mag if rng.random()<0.55 else mag
                if true_div<0: true_div=max(true_div,-sist)
            ferr=0
            if sist>0 and rng.random()<0.04:
                mag=max(1,int(round(abs(rng.normal(0,0.03))*sist)))
                ferr=mag if rng.random()<0.5 else -mag
            q1=max(0,sist+true_div+ferr); div1=q1-sist
            rec=1 if div1!=0 else 0
            q2=(sist+true_div) if rec else None
            fdiv=true_div if rec else div1
            tmin=round(max(3,rng.normal(8,2.5))+(7 if rec else 0),1)
            end_ok=int(rng.random()>P_END[cls])
            st_sis='Bloqueado' if bloq else ('Quarentena' if quar else 'Disponível')
            if rng.random()<0.02:
                st_real=str(rng.choice([s for s in ['Disponível','Bloqueado','Quarentena'] if s!=st_sis]))
            else: st_real=st_sis
            cnt_rows.append(dict(sku=sku,plan=c['plan'],exec=d,tipo=c['tipo'],delay=c['delay'],realizada=1,
                                 contador=str(rng.choice(CONTADORES)),qtd_sistema=sist,q1=q1,div1=div1,recontada=rec,q2=q2,fdiv=fdiv,
                                 tmin=tmin,end_ok=end_ok,st_sis=st_sis,st_real=st_real))
            if fdiv!=0:
                if fdiv<0:
                    motivo=str(rng.choice(['Erro de apontamento','Perda não identificada','Furto/extravio','Quebra não registrada'],p=[0.40,0.35,0.10,0.15]))
                    perda=0 if motivo=='Erro de apontamento' else 1
                    consume(layers,-fdiv)
                else:
                    motivo=str(rng.choice(['Erro de apontamento','Devolução não lançada'],p=[0.7,0.3])); perda=0
                    layers.append([d,fdiv])
                mov_rows.append(dict(data=d,sku=sku,tipo_mov='AJUSTE_INVENTARIO',qtd=fdiv,valor=round(fdiv*cost,2),motivo=motivo,documento='INV-'+d.strftime('%Y%m%d'),perda_nao_explicada=perda))
        # 3. demanda
        if disc and d>=disc: dem=0
        else:
            base=p['mean_d']*WF[d.weekday()]*season(d.month,cat)*(1+p['trend']*di/30)
            if p['shock'] and p['shock'][0]<=d<=p['shock'][1]: base*=p['shock'][2]
            k=1/(p['cv']**2)
            dem=int(round(base*rng.gamma(k,1/k)))
        dm.append(dem)
        sist=total(layers)
        if bloq: bloq[0]=min(bloq[0],sist)
        disp=max(0,sist-(bloq[0] if bloq else 0)-sum(x[0] for x in quar)-sum(x[0] for x in avar))
        sold=0
        for q in split_lines(dem):
            att=min(q,disp); disp-=att; sold+=att
            ped_rows.append(dict(data_pedido=d,sku=sku,canal=str(rng.choice(CANAIS,p=CANAL_P)),qtd_pedida=q,qtd_atendida=att,
                                 preco_unit=p['preco'],custo_unit=cost))
        if sold>0:
            consume(layers,sold); gap=0
            mov_rows.append(dict(data=d,sku=sku,tipo_mov='SAIDA_VENDA',qtd=-sold,valor=round(-sold*cost,2),motivo='Expedição de vendas',documento='VENDAS-'+d.strftime('%Y%m%d'),perda_nao_explicada=0))
        else: gap+=1
        # 4. eventos
        sist=total(layers)
        if not (disc and d>=disc) and sist>0 and rng.random()<0.10:
            q=max(1,int(p['mean_d']*0.06*rng.lognormal(0,0.6)))
            q=min(q,max(0,disp))
            if q>0: avar.append([q,d+timedelta(3)])
        if bloq is None and sist>0 and rng.random()<0.005:
            bloq=[max(1,int(sist*rng.uniform(0.1,0.25))),d+timedelta(int(rng.integers(5,11)))]
        # 5. reposição
        if not (disc and d>=disc) and d<END-timedelta(1):
            onorder=sum(x['qtd_ped'] for x in pos)
            position=sist+onorder
            if position<=p['rop']:
                qty=int(math.ceil(max(24,p['max']-position)/12)*12)
                if rng.random()<0.06: qty=int(math.ceil(qty*2.0/12)*12)
                _,_,lt,pdly=FOR_D[p['forn']]
                lt_real=lt+(int(rng.integers(1,6)) if rng.random()<pdly else 0)-(1 if (lt>5 and rng.random()<0.1) else 0)
                lt_real=max(1,lt_real)
                prev=d+timedelta(lt)
                rec=d+timedelta(lt_real)
                if rec.weekday()==6: rec+=timedelta(1)
                if prev.weekday()==6: prev+=timedelta(1)
                qrec=qty if rng.random()<0.85 else int(qty*rng.uniform(0.85,0.99))
                tmp=f"PCTMP-{sku}-{d.isoformat()}"
                po=dict(id_tmp=tmp,sku=sku,forn=p['forn'],dped=d,dprev=prev,rec=(rec if rec<=END else None),qtd_ped=qty,qtd_rec=qrec,lt_plan=lt,recebido=0)
                pos.append(po); po_rows.append(po)
        # 6. snapshot
        sist=total(layers)
        if bloq: bloq[0]=min(bloq[0],sist)
        qb=bloq[0] if bloq else 0; qq=sum(x[0] for x in quar); qa=sum(x[0] for x in avar)
        disp=max(0,sist-qb-qq-qa)
        ages=[((d-l[0]).days,l[1]) for l in layers]
        b=[0]*5
        for a,q in ages:
            if a<=30: b[0]+=q
            elif a<=60: b[1]+=q
            elif a<=90: b[2]+=q
            elif a<=180: b[3]+=q
            else: b[4]+=q
        idade=(sum(a*q for a,q in ages)/sist) if sist>0 else 0
        snap_rows.append(dict(data=d,sku=sku,qtd_sistema=sist,qtd_bloqueada=qb,qtd_quarentena=qq,qtd_avariada=qa,qtd_disponivel=disp,
                              demanda_media_30d=round(sum(dm)/30,2),dias_sem_saida=gap,idade_media_dias=round(idade,1),
                              qtd_0_30d=b[0],qtd_31_60d=b[1],qtd_61_90d=b[2],qtd_91_180d=b[3],qtd_acima_180d=b[4]))

pickle.dump(dict(prods=prods,mov=mov_rows,ped=ped_rows,po=po_rows,cnt=cnt_rows,snap=snap_rows,fornec=FORNECEDORES,
                 start=START,end=END), open(sys.argv[1],'wb'))
print('ok', len(mov_rows),len(ped_rows),len(po_rows),len(cnt_rows),len(snap_rows))
