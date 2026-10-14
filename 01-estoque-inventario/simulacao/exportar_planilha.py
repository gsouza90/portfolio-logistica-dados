"""
Gera a planilha final (tabelas nomeadas, dicionário de indicadores com DAX e gabarito) e os CSVs.
Uso: python exportar_planilha.py saida/tabelas.pkl saida/Base_Estoque.xlsx saida/csv

Projeto de portfólio com dados 100% fictícios.
"""
import pickle, sys, os, zipfile
import numpy as np, pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter
import gabarito as gab

X = pickle.load(open(sys.argv[1], 'rb')); T = X['T']
OUT = sys.argv[2]; CSVDIR = sys.argv[3]
G = gab.compute(X)

# ------------------------------------------------------------ indicadores (n, nome, grupo, fmt, definição, DAX)
IND = [
(1,'Inventory Accuracy','Acuracidade e inventário','pct','Contagens sem divergência após recontagem ÷ contagens realizadas.','DIVIDE(SUM(fContagem[sem_div_final]), SUM(fContagem[realizada]))'),
(2,'Count Accuracy','Acuracidade e inventário','pct','Contagens sem divergência já na 1ª contagem ÷ contagens realizadas.','DIVIDE(SUM(fContagem[sem_div_1a]), SUM(fContagem[realizada]))'),
(3,'Cycle Count Compliance','Acuracidade e inventário','pct','Contagens cíclicas realizadas no prazo (tolerância de 1 dia) ÷ planejadas. Usa a data planejada.','CALCULATE(DIVIDE(SUM(fContagem[no_prazo]), SUM(fContagem[planejada])), fContagem[tipo_contagem] = "Cíclica", USERELATIONSHIP(fContagem[data_planejada], dCalendario[data]))'),
(4,'Inventory Adjustment Rate','Acuracidade e inventário','pct','Valor absoluto dos ajustes de inventário ÷ valor médio do estoque.','DIVIDE(CALCULATE(SUMX(fMov, ABS(fMov[valor])), fMov[tipo_mov] = "AJUSTE_INVENTARIO"), [Valor Estoque Médio])'),
(5,'Acuracidade de endereço','Acuracidade e inventário','pct','Contagens em que o item estava no endereço correto ÷ contagens realizadas.','DIVIDE(SUM(fContagem[endereco_correto]), SUM(fContagem[realizada]))'),
(6,'Divergência de inventário (%)','Acuracidade e inventário','pct','Soma das divergências finais em módulo (un) ÷ quantidade do sistema nas contagens.','DIVIDE(SUMX(fContagem, ABS(fContagem[divergencia_final])), SUM(fContagem[qtd_sistema]))'),
(7,'Valor da divergência (R$)','Acuracidade e inventário','brl','Divergência final em módulo × custo unitário. Para o líquido (sobra − falta) use valor_divergencia_liq.','SUM(fContagem[valor_divergencia_abs])'),
(8,'Taxa de recontagem','Acuracidade e inventário','pct','Contagens que precisaram de recontagem ÷ contagens realizadas.','DIVIDE(SUM(fContagem[recontada]), SUM(fContagem[realizada]))'),
(9,'Cobertura do plano de inventário','Acuracidade e inventário','pct','SKUs distintos contados desde o início do ano de análise (out/25) ÷ total de SKUs (40). Acumulado.','DIVIDE(CALCULATE(DISTINCTCOUNT(fContagem[sku]), fContagem[realizada] = 1, DATESYTD(dCalendario[data], "9/30")), COUNTROWS(dProduto))'),
(10,'Produtividade de inventário','Acuracidade e inventário','dec1','Itens (SKUs) contados por hora de contagem.','DIVIDE(SUM(fContagem[realizada]), DIVIDE(SUM(fContagem[tempo_min]), 60))'),
(11,'Giro de estoque (anualizado)','Giro, cobertura e níveis','dec1','Custo das vendas do mês ÷ valor médio do estoque × 12. Para vários meses: divida por [Meses] em vez de multiplicar por 12.','DIVIDE([COGS], [Valor Estoque Médio]) * 12'),
(12,'Days of Inventory (DOI)','Giro, cobertura e níveis','dec1','Valor médio do estoque ÷ custo diário das vendas (dias de cobertura).','DIVIDE([Valor Estoque Médio], DIVIDE([COGS], [Dias no Período]))'),
(13,'Estoque médio (un)','Giro, cobertura e níveis','int','Média diária da quantidade em estoque (sistema).','[Estoque Médio (un)]'),
(14,'Valor do estoque (fim do período, R$)','Giro, cobertura e níveis','brl','Σ quantidade × custo no último dia do período.','[Valor Estoque Fim]'),
(15,'Estoque de segurança: % SKU-dias abaixo','Giro, cobertura e níveis','pct','SKU-dias ativos com estoque disponível menor que o estoque de segurança ÷ SKU-dias ativos. O parâmetro está em dProduto[estoque_seguranca].','DIVIDE(SUM(fEstoque[flag_abaixo_ss]), [SKU-dias Ativos])'),
(16,'Estoque mínimo: % SKU-dias abaixo','Giro, cobertura e níveis','pct','SKU-dias ativos com disponível abaixo do mínimo (50% do estoque de segurança) ÷ SKU-dias ativos.','DIVIDE(SUM(fEstoque[flag_abaixo_min]), [SKU-dias Ativos])'),
(17,'Ponto de pedido: % SKU-dias no ou abaixo','Giro, cobertura e níveis','pct','SKU-dias ativos com disponível ≤ ponto de pedido ÷ SKU-dias ativos (mede quanto do tempo o SKU está em fase de reposição).','DIVIDE(SUM(fEstoque[flag_abaixo_rop]), [SKU-dias Ativos])'),
(18,'Estoque máximo: % SKU-dias acima','Giro, cobertura e níveis','pct','SKU-dias ativos com estoque (sistema) acima do máximo ÷ SKU-dias ativos.','DIVIDE(SUM(fEstoque[flag_acima_max]), [SKU-dias Ativos])'),
(19,'Lead time de reposição real (dias)','Giro, cobertura e níveis','dec1','Média de (data de recebimento − data do pedido) das compras recebidas. Compare com dProduto[lead_time_planejado].','AVERAGE(fCompras[lead_time_real])'),
(20,'Acuracidade de reposição','Disponibilidade e nível de serviço','pct','Compras recebidas no prazo e com quantidade ≥ 95% do pedido ÷ compras recebidas.','DIVIDE(SUM(fCompras[reposicao_ok]), SUM(fCompras[recebido]))'),
(21,'Stockout Rate','Disponibilidade e nível de serviço','pct','SKU-dias ativos com disponível = 0 ÷ SKU-dias ativos.','DIVIDE(SUM(fEstoque[flag_ruptura]), [SKU-dias Ativos])'),
(22,'Inventory Availability (valor)','Disponibilidade e nível de serviço','pct','Valor do estoque disponível (sem bloqueado, quarentena e avariado) ÷ valor do estoque no sistema.','DIVIDE(SUM(fEstoque[valor_disponivel]), SUM(fEstoque[valor_estoque]))'),
(23,'Backorder Rate','Disponibilidade e nível de serviço','pct','Quantidade pendente por falta ÷ quantidade pedida.','DIVIDE(SUM(fPedidos[qtd_backorder]), SUM(fPedidos[qtd_pedida]))'),
(24,'Fill Rate (linhas)','Disponibilidade e nível de serviço','pct','Linhas de pedido atendidas integralmente ÷ total de linhas. Para fill rate em unidades: SUM(qtd_atendida) ÷ SUM(qtd_pedida).','DIVIDE(SUM(fPedidos[linha_completa]), COUNTROWS(fPedidos))'),
(25,'Excess Inventory (% do valor)','Excesso, obsolescência e perdas','pct','Valor do estoque acima do máximo (SKUs ativos) ÷ valor total do estoque.','DIVIDE(SUM(fEstoque[valor_excesso]), SUM(fEstoque[valor_estoque]))'),
(26,'Dead Stock (% do valor)','Excesso, obsolescência e perdas','pct','Valor de SKUs com estoque e sem saída há 90 dias ou mais ÷ valor total do estoque.','DIVIDE(CALCULATE(SUM(fEstoque[valor_estoque]), fEstoque[flag_dead_stock] = 1), SUM(fEstoque[valor_estoque]))'),
(27,'Slow Moving (% do valor)','Excesso, obsolescência e perdas','pct','Valor de SKUs com cobertura > 60 dias e saída nos últimos 90 dias ÷ valor total do estoque.','DIVIDE(CALCULATE(SUM(fEstoque[valor_estoque]), fEstoque[flag_slow_moving] = 1), SUM(fEstoque[valor_estoque]))'),
(28,'Aging de estoque (idade média, dias)','Excesso, obsolescência e perdas','dec1','Idade média do estoque (FIFO) ponderada pelo valor. Para % acima de 90 dias use SUM(valor_acima_90d) ÷ SUM(valor_estoque).','DIVIDE(SUMX(fEstoque, fEstoque[idade_media_dias] * fEstoque[valor_estoque]), SUM(fEstoque[valor_estoque]))'),
(29,'Obsolescence Rate','Excesso, obsolescência e perdas','pct','Valor de SKUs descontinuados em estoque ÷ valor total do estoque.','DIVIDE(SUM(fEstoque[valor_obsoleto]), SUM(fEstoque[valor_estoque]))'),
(30,'Obsolete Inventory Value (fim, R$)','Excesso, obsolescência e perdas','brl','Valor em R$ do estoque obsoleto no último dia do período.','CALCULATE(SUM(fEstoque[valor_obsoleto]), LASTDATE(fEstoque[data]))'),
(31,'Shrinkage Rate','Excesso, obsolescência e perdas','pct','Ajustes negativos por perda não explicada (perda não identificada, furto/extravio, quebra não registrada) ÷ valor médio do estoque.','DIVIDE(-CALCULATE(SUM(fMov[valor]), fMov[tipo_mov] = "AJUSTE_INVENTARIO", fMov[perda_nao_explicada] = 1), [Valor Estoque Médio])'),
(32,'Taxa de avaria','Excesso, obsolescência e perdas','pct','Unidades avariadas ÷ unidades movimentadas (entradas + saídas).','DIVIDE(-CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "AVARIA"), CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "ENTRADA_COMPRA") - CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "SAIDA_VENDA"))'),
(33,'Carrying Cost (% ao ano)','Custos e retorno','pct','Custo total de manter estoque no mês ÷ valor médio do estoque × 12 (capital, armazenagem, seguro, mão de obra e perdas).','DIVIDE(SUM(fCustos[custo_total]), [Valor Estoque Médio]) * 12'),
(34,'Custo por unidade estocada (R$/un/mês)','Custos e retorno','dec2','Custo total de manter estoque no mês ÷ estoque médio em unidades.','DIVIDE(SUM(fCustos[custo_total]), [Estoque Médio (un)])'),
(35,'GMROI (anualizado)','Custos e retorno','dec1','Margem bruta do mês ÷ valor médio do estoque a custo × 12.','DIVIDE(SUM(fPedidos[margem_bruta]), [Valor Estoque Médio]) * 12'),
(36,'Inventory-to-Sales Ratio','Custos e retorno','dec2','Valor do estoque no fim do mês ÷ vendas do mês (R$).','DIVIDE([Valor Estoque Fim], [Vendas R$])'),
(37,'Inventory Investment (R$ médio)','Custos e retorno','brl','Capital médio imobilizado em estoque no período.','[Valor Estoque Médio]'),
(38,'Stock Utilization Rate','Custos e retorno','pct','Definição adotada: unidades expedidas no mês ÷ (estoque no 1º dia + entradas do mês), isto é, o quanto do disponível foi efetivamente consumido (sell-through).','DIVIDE(-CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "SAIDA_VENDA"), CALCULATE(SUM(fEstoque[qtd_sistema]), FIRSTDATE(fEstoque[data])) + CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "ENTRADA_COMPRA"))'),
(39,'Acuracidade do status do estoque','Custos e retorno','pct','Contagens em que o status do sistema (disponível, bloqueado, quarentena) bate com o status real ÷ contagens realizadas.','DIVIDE(SUM(fContagem[status_correto]), SUM(fContagem[realizada]))'),
(40,'Disponibilidade real vs sistêmica (R$ no fim)','Custos e retorno','brl','Valor no sistema − valor realmente utilizável (bloqueado + quarentena + avariado) no último dia do período.','CALCULATE(SUM(fEstoque[valor_estoque]) - SUM(fEstoque[valor_disponivel]), LASTDATE(fEstoque[data]))'),
]
BASE = [
('Dias no Período','DISTINCTCOUNT(fEstoque[data])'),
('Meses','DISTINCTCOUNT(dCalendario[ano_mes])'),
('Valor Estoque Médio','DIVIDE(SUM(fEstoque[valor_estoque]), [Dias no Período])'),
('Estoque Médio (un)','DIVIDE(SUM(fEstoque[qtd_sistema]), [Dias no Período])'),
('Valor Estoque Fim','CALCULATE(SUM(fEstoque[valor_estoque]), LASTDATE(fEstoque[data]))'),
('COGS','SUM(fPedidos[custo_atendido])'),
('Vendas R$','SUM(fPedidos[valor_atendido])'),
('SKU-dias Ativos','SUM(fEstoque[estoque_ativo])'),
]
FMT = {'pct':'0.0%','int':'#,##0','brl':'"R$" #,##0','dec1':'0.0','dec2':'0.00'}

HF = PatternFill('solid', fgColor='1F3864'); HFont = Font(bold=True, color='FFFFFF', name='Arial', size=10)
BF = Font(name='Arial', size=10); thin = Side(style='thin', color='D9D9D9')

def style_header(ws, row=1):
    for c in ws[row]:
        if c.value is not None:
            c.fill = HF; c.font = HFont; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

def add_table(ws, name, df):
    ref = f"A1:{get_column_letter(df.shape[1])}{df.shape[0]+1}"
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name='TableStyleMedium2', showRowStripes=True)
    ws.add_table(t)

writer = pd.ExcelWriter(OUT, engine='openpyxl', datetime_format='dd/mm/yyyy', date_format='dd/mm/yyyy')
wb = None

# ---------------- LeiaMe
leia = [
('BASE FICTÍCIA DE ESTOQUE E INVENTÁRIO (40 indicadores)',''),
('',''),
('O que é','Base 100% fictícia, gerada por simulação dia a dia de um centro de distribuição de bens de consumo (40 SKUs, 12 meses: 01/10/2025 a 30/09/2026). Nenhum dado é real; nenhuma empresa, fornecedor ou pessoa citada existe.'),
('Para que serve','Alimentar um dashboard (Power BI ou Excel) com os 40 indicadores de gestão de estoque e inventário. Pode ser apresentada como projeto pessoal com dados fictícios.'),
('Como foi feita','Simulação de demanda com sazonalidade, política de reposição por ponto de pedido, atrasos de fornecedor, avarias, bloqueios/quarentena, contagens cíclicas e geral (com divergências e recontagens), descontinuação de 5 SKUs, choques de demanda e compras antecipadas.'),
('',''),
('COMO USAR NO POWER BI',''),
('1','Obter dados > Pasta de trabalho do Excel > selecione todas as tabelas (dCalendario, dProduto, dFornecedor, dEndereco, fEstoque, fPedidos, fCompras, fContagem, fMov, fCustos). Cada aba é uma tabela nomeada.'),
('2','Marque dCalendario como tabela de datas (coluna data).'),
('3','Crie os relacionamentos (1 → muitos) listados na aba Relacionamentos abaixo.'),
('4','Cole as medidas da aba Indicadores_DAX (comece pelas "Medidas base").'),
('5','Compare os resultados com a aba Gabarito_Mensal. Se bater, seu modelo está correto.'),
('Alternativa CSV','O arquivo .zip traz os mesmos dados em CSV (separador vírgula, ponto decimal, UTF-8). Importe com localidade "Inglês (EUA)" para não trocar vírgula por ponto.'),
('',''),
('RELACIONAMENTOS SUGERIDOS',''),
('dCalendario[data]  →  fEstoque[data]','ativo'),
('dCalendario[data]  →  fPedidos[data_pedido]','ativo'),
('dCalendario[data]  →  fCompras[data_recebimento]','ativo (data_pedido e data_prevista: inativos)'),
('dCalendario[data]  →  fContagem[data_realizada]','ativo (data_planejada: inativo, usado por USERELATIONSHIP no indicador 3)'),
('dCalendario[data]  →  fMov[data]','ativo'),
('dCalendario[data]  →  fCustos[mes_ref]','ativo; funciona no nível mês (fCustos tem uma linha por mês, no dia 1)'),
('dProduto[sku]  →  fEstoque, fPedidos, fCompras, fContagem, fMov','ativo'),
('dFornecedor[fornecedor_id]  →  dProduto[fornecedor_id]','ativo'),
('dEndereco[endereco_id]  →  dProduto[endereco_id]','ativo'),
('',''),
('DEFINIÇÕES IMPORTANTES',''),
('Estoque do sistema','qtd_sistema: o que o ERP/WMS mostra. Inclui bloqueado, quarentena e avariado.'),
('Estoque disponível','qtd_disponivel = sistema − bloqueado − quarentena − avariado.'),
('Ruptura','SKU ativo com qtd_disponivel = 0 no fim do dia.'),
('SKU ativo','estoque_ativo = 1 (não descontinuado). SKUs descontinuados entram só nos indicadores de obsolescência, dead stock e aging.'),
('Fill rate / backorder','Calculados por linha de pedido (fPedidos). A quantidade não atendida vira backorder e não é reatendida depois.'),
('Contagens','fContagem tem contagens cíclicas (A a cada 14 dias, B a cada 30, C a cada 60) e 1 inventário geral em 31/03/2026. Contagens não realizadas têm realizada = 0.'),
('Indicador 38','"Stock Utilization Rate" admite mais de uma definição; foi adotado o sell-through (ver aba Indicadores_DAX).'),
('Indicadores 33 e 34','Custos de capital, armazenagem, seguro e mão de obra seguem parâmetros fictícios simples (aba fCustos). Valores absolutos não têm referência de mercado.'),
('Gabarito','Valores calculados em Python com as mesmas regras do DAX. Pequenas diferenças de arredondamento são normais.'),
]
pd.DataFrame(leia, columns=['Tópico','Descrição']).to_excel(writer, sheet_name='LeiaMe', index=False, header=False)
ind_rows = []
for n,nome,grp,fmt,defi,dax in IND:
    ind_rows.append(dict(n=n, indicador=nome, grupo=grp, definicao_adotada=defi, medida_DAX=f"[{nome}] = " + dax))
pd.DataFrame(ind_rows).to_excel(writer, sheet_name='Indicadores_DAX', index=False, startrow=len(BASE)+3)
wb = writer.book
ws = writer.sheets['Indicadores_DAX']
ws['A1'] = 'Medidas base (crie primeiro)'; ws['A1'].font = Font(bold=True, name='Arial', size=11)
for i,(nm,dx) in enumerate(BASE):
    ws.cell(row=2+i, column=1, value=nm).font = BF
    c = ws.cell(row=2+i, column=2, value=f"[{nm}] = {dx}"); c.font = Font(name='Consolas', size=9)
    ws.merge_cells(start_row=2+i, start_column=2, end_row=2+i, end_column=5)
hdr_row = len(BASE)+4
for c in ws[hdr_row]:
    if c.value is not None: c.fill = HF; c.font = HFont; c.alignment = Alignment(horizontal='center')
for r in range(hdr_row+1, hdr_row+1+len(IND)):
    for ci in range(1,6):
        c = ws.cell(row=r, column=ci); c.alignment = Alignment(wrap_text=True, vertical='top')
        c.font = Font(name='Consolas', size=9) if ci==5 else BF
for col,w in zip('ABCDE',[8,34,30,60,95]): ws.column_dimensions[col].width = w
ws.column_dimensions['A'].width = 22
ws.freeze_panes = ws.cell(row=hdr_row+1, column=1)

# ---------------- Gabarito
gm = G.copy(); gm.insert(0,'indicador',[IND[i-1][1] for i in gm.index]); gm.insert(0,'#',gm.index)
gm.to_excel(writer, sheet_name='Gabarito_Mensal', index=False)
wg = writer.sheets['Gabarito_Mensal']; style_header(wg)
for r in range(2, len(gm)+2):
    f = FMT[IND[r-2][3]]
    wg.cell(row=r, column=2).font = BF
    for c in range(3, 3+G.shape[1]):
        wg.cell(row=r, column=c).number_format = f; wg.cell(row=r, column=c).font = BF
wg.column_dimensions['A'].width = 5; wg.column_dimensions['B'].width = 44
for c in range(3, 3+G.shape[1]): wg.column_dimensions[get_column_letter(c)].width = 13
wg.freeze_panes = 'C2'

# ---------------- tabelas
ORDER = ['Parametros','dCalendario','dProduto','dFornecedor','dEndereco','fEstoque','fPedidos','fCompras','fContagem','fMov','fCustos']
param = pd.DataFrame([
 ('Período simulado','01/10/2025 a 30/09/2026 (365 dias)'),('SKUs','40 (5 categorias)'),('Fornecedores','8'),
 ('Política de reposição','Ponto de pedido: pede quando (estoque + em trânsito) ≤ ponto_pedido; leva até estoque_maximo (múltiplos de 12; 6% das compras são antecipadas, em dobro)'),
 ('Estoque de segurança','1,65 × desvio diário × √lead time (z de 95%)'),('Ponto de pedido','demanda média × lead time + estoque de segurança'),
 ('Estoque máximo','ponto de pedido + 28 dias de demanda'),('Estoque mínimo','50% do estoque de segurança'),
 ('SKUs descontinuados','5 (datas em dProduto[data_descontinuacao]); descartes parciais 45 e 120 dias depois'),
 ('Contagens','A: 14 dias, B: 30 dias, C: 60 dias; geral em 31/03/2026'),
 ('Custo de capital','0,9% ao mês sobre o valor médio do estoque'),('Armazenagem','R$ 2.000 fixos + 0,15% do valor médio ao mês'),
 ('Seguro','0,12% do valor médio ao mês'),('Mão de obra de estoque','R$ 2.000 ao mês (+10% em nov e dez)'),
 ('Perdas','Avarias + descartes de obsoletos + ajustes por perda não explicada (valor a custo)'),
], columns=['parametro','valor'])
frames = dict(T); frames['Parametros'] = param
for name in ORDER:
    df = frames[name]
    df.to_excel(writer, sheet_name=name, index=False)
    ws = writer.sheets[name]; style_header(ws)
    ws.freeze_panes = 'A2'
    for i,c in enumerate(df.columns, start=1):
        L = get_column_letter(i)
        w = max(len(str(c)), 10)
        if name == 'Parametros': w = 28 if i==1 else 120
        elif str(df[c].dtype).startswith('datetime'): w = 12
        elif df[c].dtype == object: w = min(max(w, int(df[c].astype(str).str.len().max())+2), 34)
        ws.column_dimensions[L].width = min(w+2, 36) if name!='Parametros' else w
    if name != 'Parametros': add_table(ws, name, df)
    if name == 'fCustos':
        for col in ws.iter_cols(min_row=2, min_col=2, max_col=7, max_row=len(df)+1):
            for c in col: c.number_format = '#,##0.00'
    if name == 'fCustos':
        for r in range(2, len(df)+2): ws.cell(row=r, column=1).number_format = 'mm/yyyy'
# LeiaMe formatting
wl = writer.sheets['LeiaMe']
wl.column_dimensions['A'].width = 52; wl.column_dimensions['B'].width = 130
for row in wl.iter_rows():
    for c in row:
        c.font = BF; c.alignment = Alignment(wrap_text=True, vertical='top')
wl['A1'].font = Font(bold=True, size=14, name='Arial')
for r in range(1, wl.max_row+1):
    v = wl.cell(row=r, column=1).value
    if v in ('COMO USAR NO POWER BI','RELACIONAMENTOS SUGERIDOS','DEFINIÇÕES IMPORTANTES'):
        wl.cell(row=r, column=1).font = Font(bold=True, name='Arial', size=11, color='1F3864')
    elif v and wl.cell(row=r, column=2).value not in (None,''):
        wl.cell(row=r, column=1).font = Font(bold=True, name='Arial', size=10)
# ordem das abas
order = ['LeiaMe','Indicadores_DAX','Gabarito_Mensal'] + ORDER
writer.book._sheets = [writer.book[n] for n in order]
writer.book.active = 0
writer.close()

# ---------------- CSVs
os.makedirs(CSVDIR, exist_ok=True)
for name in ORDER:
    if name == 'Parametros': continue
    df = frames[name].copy()
    for c in df.columns:
        if str(df[c].dtype).startswith('datetime'): df[c] = df[c].dt.strftime('%Y-%m-%d')
    df.to_csv(os.path.join(CSVDIR, name + '.csv'), index=False, encoding='utf-8')
print('done')
