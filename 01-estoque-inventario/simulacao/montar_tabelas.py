"""
Transforma o resultado da simulação nas tabelas do modelo (fEstoque, fPedidos, fCompras, fContagem, fMov, fCustos e dimensões).
Uso: python montar_tabelas.py saida/sim.pkl saida/tabelas.pkl

Projeto de portfólio com dados 100% fictícios.
"""
import pickle, sys, math
import numpy as np, pandas as pd
from datetime import date, timedelta

D = pickle.load(open(sys.argv[1], 'rb'))
prods = D['prods']; START = D['start']; END = D['end']
T = {}

# ---------------- dimensões
T['dProduto'] = pd.DataFrame([dict(
    sku=p['sku'], descricao=p['desc'], categoria=p['cat'], fornecedor_id=p['forn'], classe_abc=p['cls'], unidade='UN',
    custo_unit=p['cost'], preco_unit=p['preco'], lead_time_planejado=p['lt'], estoque_seguranca=p['ss'],
    estoque_minimo=p['min'], ponto_pedido=p['rop'], estoque_maximo=p['max'], endereco_id=p['end'],
    status_produto='Descontinuado' if p['disc'] else 'Ativo',
    data_descontinuacao=pd.Timestamp(p['disc']) if p['disc'] else pd.NaT) for p in prods])
T['dFornecedor'] = pd.DataFrame([dict(fornecedor_id=f[0], fornecedor=f[1], lead_time_planejado=f[2], taxa_atraso_esperada=f[3]) for f in D['fornec']])
ends = sorted(set(p['end'] for p in prods))
T['dEndereco'] = pd.DataFrame([dict(endereco_id=e, rua=e[:3], posicao=e[4:7], nivel=e[8:], armazem='CD Principal') for e in ends])
cal = pd.DataFrame({'data': pd.date_range(START, END)})
MESES = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']
DIAS = ['seg','ter','qua','qui','sex','sáb','dom']
cal['ano'] = cal.data.dt.year; cal['mes_num'] = cal.data.dt.month
cal['mes_nome'] = cal.mes_num.map(lambda m: MESES[m-1])
cal['ano_mes'] = cal.data.dt.strftime('%Y-%m'); cal['mes_ref'] = cal.data.dt.to_period('M').dt.to_timestamp()
cal['trimestre'] = 'T' + cal.data.dt.quarter.astype(str)
cal['dia_semana_num'] = cal.data.dt.weekday + 1; cal['dia_semana'] = cal.data.dt.weekday.map(lambda i: DIAS[i])
cal['dia_util'] = (cal.data.dt.weekday < 6).astype(int)
cal['semana_ano'] = cal.data.dt.isocalendar().week.astype(int)
T['dCalendario'] = cal

dP = T['dProduto']
# ---------------- fEstoque
S = pd.DataFrame(D['snap']); S['data'] = pd.to_datetime(S['data'])
S = S.merge(dP[['sku','custo_unit','estoque_seguranca','estoque_minimo','ponto_pedido','estoque_maximo','data_descontinuacao']], on='sku')
S['valor_estoque'] = (S.qtd_sistema*S.custo_unit).round(2)
S['valor_disponivel'] = (S.qtd_disponivel*S.custo_unit).round(2)
S['flag_obsoleto'] = (S.data_descontinuacao.notna() & (S.data >= S.data_descontinuacao)).astype(int)
S['estoque_ativo'] = 1 - S.flag_obsoleto
S['cobertura_dias'] = np.where(S.demanda_media_30d > 0, S.qtd_sistema/S.demanda_media_30d.replace(0, np.nan), 999).clip(max=999).round(1)
S['flag_ruptura'] = ((S.qtd_disponivel == 0) & (S.estoque_ativo == 1)).astype(int)
S['flag_abaixo_ss'] = ((S.qtd_disponivel < S.estoque_seguranca) & (S.estoque_ativo == 1)).astype(int)
S['flag_abaixo_min'] = ((S.qtd_disponivel < S.estoque_minimo) & (S.estoque_ativo == 1)).astype(int)
S['flag_abaixo_rop'] = ((S.qtd_disponivel <= S.ponto_pedido) & (S.estoque_ativo == 1)).astype(int)
S['flag_acima_max'] = ((S.qtd_sistema > S.estoque_maximo) & (S.estoque_ativo == 1)).astype(int)
S['qtd_excesso'] = ((S.qtd_sistema - S.estoque_maximo).clip(lower=0) * S.estoque_ativo).astype(int)
S['valor_excesso'] = (S.qtd_excesso*S.custo_unit).round(2)
S['flag_dead_stock'] = ((S.dias_sem_saida >= 90) & (S.qtd_sistema > 0)).astype(int)
S['flag_slow_moving'] = ((S.cobertura_dias > 60) & (S.dias_sem_saida < 90) & (S.qtd_sistema > 0)).astype(int)
S['valor_obsoleto'] = (S.valor_estoque*S.flag_obsoleto).round(2)
S['valor_acima_90d'] = ((S.qtd_91_180d + S.qtd_acima_180d)*S.custo_unit).round(2)
S['ym'] = S.data.dt.strftime('%Y-%m')
cols_est = ['data','sku','qtd_sistema','qtd_bloqueada','qtd_quarentena','qtd_avariada','qtd_disponivel','valor_estoque','valor_disponivel',
            'demanda_media_30d','cobertura_dias','dias_sem_saida','idade_media_dias','qtd_0_30d','qtd_31_60d','qtd_61_90d','qtd_91_180d','qtd_acima_180d',
            'valor_acima_90d','estoque_ativo','flag_obsoleto','valor_obsoleto','flag_ruptura','flag_abaixo_ss','flag_abaixo_min','flag_abaixo_rop',
            'flag_acima_max','qtd_excesso','valor_excesso','flag_dead_stock','flag_slow_moving']
T['fEstoque'] = S[cols_est].copy()

# ---------------- fPedidos
P = pd.DataFrame(D['ped']); P['data_pedido'] = pd.to_datetime(P['data_pedido'])
P = P.sort_values(['data_pedido','sku']).reset_index(drop=True)
P.insert(0, 'pedido_id', ['PED-%06d' % (i+1) for i in range(len(P))])
P['qtd_backorder'] = P.qtd_pedida - P.qtd_atendida
P['valor_pedido'] = (P.qtd_pedida*P.preco_unit).round(2)
P['valor_atendido'] = (P.qtd_atendida*P.preco_unit).round(2)
P['custo_atendido'] = (P.qtd_atendida*P.custo_unit).round(2)
P['margem_bruta'] = (P.valor_atendido - P.custo_atendido).round(2)
P['linha_completa'] = (P.qtd_backorder == 0).astype(int)
P['linha_backorder'] = (P.qtd_backorder > 0).astype(int)
P['ym'] = P.data_pedido.dt.strftime('%Y-%m')
T['fPedidos'] = P.drop(columns='ym')

# ---------------- fCompras
B = pd.DataFrame(D['po'])
B = B.sort_values(['dped','sku']).reset_index(drop=True)
B['po_id'] = ['PC-%06d' % (i+1) for i in range(len(B))]
B['data_pedido'] = pd.to_datetime(B.dped); B['data_prevista'] = pd.to_datetime(B.dprev); B['data_recebimento'] = pd.to_datetime(B.rec)
B['recebido'] = B.data_recebimento.notna().astype(int)
B['qtd_recebida'] = np.where(B.recebido == 1, B.qtd_rec, np.nan)
B['lead_time_real'] = (B.data_recebimento - B.data_pedido).dt.days
B['no_prazo'] = np.where(B.recebido == 1, (B.data_recebimento <= B.data_prevista).astype(int), 0)
B['qtd_ok'] = np.where(B.recebido == 1, (B.qtd_rec >= 0.95*B.qtd_ped).astype(int), 0)
B['reposicao_ok'] = B.no_prazo*B.qtd_ok
B = B.rename(columns={'forn':'fornecedor_id','qtd_ped':'qtd_pedida','lt_plan':'lead_time_planejado'})
T['fCompras'] = B[['po_id','sku','fornecedor_id','data_pedido','data_prevista','data_recebimento','qtd_pedida','qtd_recebida','lead_time_planejado',
                   'lead_time_real','recebido','no_prazo','qtd_ok','reposicao_ok']].copy()
T['fCompras']['qtd_recebida'] = T['fCompras']['qtd_recebida'].astype('Int64')
T['fCompras']['lead_time_real'] = T['fCompras']['lead_time_real'].astype('Int64')
# mapear id temporário -> po_id para movimentações
tmp2po = dict(zip(B.id_tmp, B.po_id))

# ---------------- fMov
M = pd.DataFrame(D['mov']); M['data'] = pd.to_datetime(M['data'])
M['documento'] = M['documento'].map(lambda x: tmp2po.get(x, x))
M = M.sort_values(['data','sku','tipo_mov']).reset_index(drop=True)
M.insert(0, 'mov_id', ['MV-%07d' % (i+1) for i in range(len(M))])
M['ym'] = M.data.dt.strftime('%Y-%m')
T['fMov'] = M.drop(columns='ym')

# ---------------- fContagem
C = pd.DataFrame(D['cnt'])
C = C.sort_values(['plan','sku']).reset_index(drop=True)
cost = dict(zip(dP.sku, dP.custo_unit)); endr = dict(zip(dP.sku, dP.endereco_id))
C.insert(0, 'contagem_id', ['CT-%05d' % (i+1) for i in range(len(C))])
C['endereco_id'] = C.sku.map(endr); C['custo_unit'] = C.sku.map(cost)
C['planejada'] = 1
C['status_exec'] = np.where(C.realizada == 0, 'Não realizada', np.where(C.delay.fillna(99) <= 1, 'Realizada no prazo', 'Realizada com atraso'))
C['no_prazo'] = ((C.realizada == 1) & (C.delay.fillna(99) <= 1)).astype(int)
C['sem_div_1a'] = np.where(C.realizada == 1, (C.div1 == 0).astype(int), np.nan)
C['sem_div_final'] = np.where(C.realizada == 1, (C.fdiv == 0).astype(int), np.nan)
C['valor_divergencia_abs'] = (C.fdiv.abs()*C.custo_unit).round(2)
C['valor_divergencia_liq'] = (C.fdiv*C.custo_unit).round(2)
C['status_correto'] = np.where(C.realizada == 1, (C.st_sis == C.st_real).astype(int), np.nan)
C['ajuste_gerado'] = np.where(C.realizada == 1, (C.fdiv != 0).astype(int), np.nan)
C['endereco_correto'] = C.end_ok
C = C.rename(columns={'plan':'data_planejada','exec':'data_realizada','tipo':'tipo_contagem','q1':'qtd_contada_1a','div1':'divergencia_1a',
                      'q2':'qtd_recontagem','fdiv':'divergencia_final','tmin':'tempo_min','st_sis':'status_sistema','st_real':'status_real'})
for c_ in ['data_planejada','data_realizada']: C[c_] = pd.to_datetime(C[c_])
C['ym_r'] = C.data_realizada.dt.strftime('%Y-%m'); C['ym_p'] = C.data_planejada.dt.strftime('%Y-%m')
colsC = ['contagem_id','sku','endereco_id','tipo_contagem','data_planejada','data_realizada','status_exec','contador','planejada','realizada','no_prazo',
         'qtd_sistema','qtd_contada_1a','divergencia_1a','recontada','qtd_recontagem','divergencia_final','sem_div_1a','sem_div_final','ajuste_gerado',
         'custo_unit','valor_divergencia_abs','valor_divergencia_liq','tempo_min','endereco_correto','status_sistema','status_real','status_correto']
for c_ in ['qtd_sistema','qtd_contada_1a','divergencia_1a','recontada','qtd_recontagem','divergencia_final','sem_div_1a','sem_div_final','ajuste_gerado','endereco_correto','status_correto']:
    C[c_] = C[c_].astype('Int64')
C.loc[C.realizada == 0, ['valor_divergencia_abs','valor_divergencia_liq','tempo_min']] = np.nan
T['fContagem'] = C[colsC].copy()

# ---------------- fCustos
S['ym'] = S.data.dt.strftime('%Y-%m')
days = S.groupby('ym').data.nunique()
val_med = S.groupby('ym').valor_estoque.sum()/days
perd = M.assign(v=lambda d: np.where(d.tipo_mov.isin(['AVARIA','DESCARTE_OBSOLETO']) | ((d.tipo_mov == 'AJUSTE_INVENTARIO') & (d.perda_nao_explicada == 1)), -d.valor, 0)).groupby('ym').v.sum()
rows = []
for ym in val_med.index:
    vm = val_med[ym]; mth = int(ym[-2:])
    cap = vm*0.009; arm = 2000 + 0.0015*vm; seg = 0.0012*vm; mdo = 2000*(1.1 if mth in (11,12) else 1.0)
    rows.append(dict(mes_ref=pd.Timestamp(ym+'-01'), custo_capital=round(cap,2), armazenagem=round(arm,2), seguro=round(seg,2),
                     mao_de_obra_estoque=round(mdo,2), perdas=round(float(perd.get(ym,0)),2)))
K = pd.DataFrame(rows)
K['custo_total'] = (K.custo_capital+K.armazenagem+K.seguro+K.mao_de_obra_estoque+K.perdas).round(2)
T['fCustos'] = K

pickle.dump(dict(T=T, S=S, P=P, B=B, M=M, C=C, K=K), open(sys.argv[2], 'wb'))
for k,v in T.items(): print(k, v.shape)
