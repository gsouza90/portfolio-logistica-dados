"""
Calcula o gabarito mensal dos 40 indicadores em pandas, com as mesmas regras das medidas DAX.
É importado por exportar_planilha.py.

Projeto de portfólio com dados 100% fictícios.
"""
import pickle, sys
import numpy as np, pandas as pd

def compute(X):
    S, P, B, M, C, K = X['S'], X['P'], X['B'], X['M'], X['C'], X['K']
    yms = sorted(S.ym.unique())
    days = S.groupby('ym').data.nunique()
    lastd = S.groupby('ym').data.max(); firstd = S.groupby('ym').data.min()
    val_med = S.groupby('ym').valor_estoque.sum()/days
    qtd_med = S.groupby('ym').qtd_sistema.sum()/days
    Sl = S[S.data.isin(lastd.values)].groupby('ym').sum(numeric_only=True)
    Sf = S[S.data.isin(firstd.values)].groupby('ym').sum(numeric_only=True)
    ativo = S.groupby('ym').estoque_ativo.sum()
    g = lambda col: S.groupby('ym')[col].sum()
    cogs = P.groupby('ym').custo_atendido.sum(); vendas = P.groupby('ym').valor_atendido.sum(); marg = P.groupby('ym').margem_bruta.sum()
    R = C[C.realizada == 1]
    rg = R.groupby('ym_r')
    Bm = B[B.recebido == 1].assign(ym=lambda d: d.data_recebimento.dt.strftime('%Y-%m')).groupby('ym')
    mv = lambda t: M[M.tipo_mov == t].groupby('ym')
    K2 = K.assign(ym=K.mes_ref.dt.strftime('%Y-%m')).set_index('ym')
    G = {}
    G[1] = rg.sem_div_final.sum().astype(float)/rg.size()
    G[2] = rg.sem_div_1a.sum().astype(float)/rg.size()
    Cc = C[C.tipo_contagem == 'Cíclica'].groupby('ym_p')
    G[3] = Cc.no_prazo.sum()/Cc.planejada.sum()
    adj = M[M.tipo_mov == 'AJUSTE_INVENTARIO'].assign(a=lambda d: d.valor.abs()).groupby('ym').a.sum()
    G[4] = adj.reindex(yms).fillna(0)/val_med
    G[5] = rg.endereco_correto.sum().astype(float)/rg.size()
    G[6] = R.assign(a=R.divergencia_final.abs().astype(float)).groupby('ym_r').a.sum()/rg.qtd_sistema.sum().astype(float)
    G[7] = rg.valor_divergencia_abs.sum()
    G[8] = rg.recontada.sum().astype(float)/rg.size()
    cum = {}
    for ym in yms:
        cum[ym] = R[R.data_realizada <= lastd[ym]].sku.nunique()/40
    G[9] = pd.Series(cum)
    G[10] = rg.size()/(rg.tempo_min.sum()/60)
    G[11] = cogs/val_med*12
    G[12] = val_med/(cogs/days)
    G[13] = qtd_med
    G[14] = Sl.valor_estoque
    G[15] = g('flag_abaixo_ss')/ativo
    G[16] = g('flag_abaixo_min')/ativo
    G[17] = g('flag_abaixo_rop')/ativo
    G[18] = g('flag_acima_max')/ativo
    G[19] = Bm.lead_time_real.mean()
    G[20] = Bm.reposicao_ok.sum()/Bm.size()
    G[21] = g('flag_ruptura')/ativo
    G[22] = g('valor_disponivel')/g('valor_estoque')
    G[23] = P.groupby('ym').qtd_backorder.sum()/P.groupby('ym').qtd_pedida.sum()
    G[24] = P.groupby('ym').linha_completa.sum()/P.groupby('ym').size()
    G[25] = g('valor_excesso')/g('valor_estoque')
    G[26] = S[S.flag_dead_stock == 1].groupby('ym').valor_estoque.sum().reindex(yms).fillna(0)/g('valor_estoque')
    G[27] = S[S.flag_slow_moving == 1].groupby('ym').valor_estoque.sum().reindex(yms).fillna(0)/g('valor_estoque')
    G[28] = (S.assign(w=S.idade_media_dias*S.valor_estoque).groupby('ym').w.sum())/g('valor_estoque')
    G[29] = g('valor_obsoleto')/g('valor_estoque')
    G[30] = Sl.valor_obsoleto
    shr = -M[(M.tipo_mov == 'AJUSTE_INVENTARIO') & (M.perda_nao_explicada == 1)].groupby('ym').valor.sum()
    G[31] = shr.reindex(yms).fillna(0)/val_med
    avq = -mv('AVARIA').qtd.sum(); ent = mv('ENTRADA_COMPRA').qtd.sum(); sai = -mv('SAIDA_VENDA').qtd.sum()
    G[32] = avq.reindex(yms).fillna(0)/(ent+sai)
    G[33] = K2.custo_total/val_med*12
    G[34] = K2.custo_total/qtd_med
    G[35] = marg/val_med*12
    G[36] = Sl.valor_estoque/vendas
    G[37] = val_med
    G[38] = sai/(Sf.qtd_sistema+ent)
    G[39] = rg.status_correto.sum().astype(float)/rg.size()
    G[40] = Sl.valor_estoque - Sl.valor_disponivel
    out = pd.DataFrame({k: v.reindex(yms) for k, v in G.items()}).T
    out.index.name = 'n'
    return out

if __name__ == '__main__':
    X = pickle.load(open(sys.argv[1], 'rb'))
    out = compute(X)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 20)
    print(out.round(3).to_string())
    print(out.isna().sum(axis=1)[out.isna().sum(axis=1) > 0])
