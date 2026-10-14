# Portfólio de Logística e Dados

Três projetos pessoais de logística e análise de dados, feitos com **dados 100% fictícios**. Nenhum número, empresa, fornecedor, armador, transportador ou placa é real, e nada aqui vem de algum empregador.

Autor: Gilberto Souza | [LinkedIn](https://www.linkedin.com/in/gilberto-souza-82231182/)

## Projetos

| Pasta | O que é | Ferramentas |
|---|---|---|
| [01-estoque-inventario](01-estoque-inventario) | Base e modelo para um painel com **40 indicadores de estoque e inventário** (acuracidade, giro, cobertura, ruptura, obsolescência, custos). Dados simulados dia a dia, 40 SKUs, 12 meses. | Python, Excel, Power BI (DAX) |
| [02-invoices-embarques](02-invoices-embarques) | Base de **invoices e embarques de exportação**: ciclo completo, deadlines de draft, carga e porto, e custo de estadia por causa e transportador. | Python, Excel, Power BI (DAX) |
| [03-abastecimento-excel](03-abastecimento-excel) | Planilha de **reposição e abastecimento**: curva ABC, estoque de segurança, ponto de reposição, status e alocação por loja. | Excel (fórmulas), Power Query |

## Como cada projeto está organizado

- `dados/`: tabelas em CSV, prontas para importar no Power BI.
- `dax/medidas.md`: definição e medida DAX de cada indicador.
- `docs/gabarito_mensal.csv`: valor esperado de cada indicador por mês, para conferir o seu modelo.
- `simulacao/`: scripts em Python que geram os dados (reprodutíveis).

## Aviso

Os cenários (por exemplo, a melhora de prazos de documentação a partir de março/2026) são narrativas simuladas para tornar o painel interessante. Não representam resultados reais de nenhuma empresa.
