# Projeto 3: Reposição e abastecimento (Excel)

Planilha fictícia de abastecimento para **40 SKUs e 6 lojas**, com 8 semanas de vendas. Tudo é calculado com fórmulas (sem macros).

> Dados 100% fictícios. Projeto pessoal de portfólio.

## Abas

| Aba | O que tem |
|---|---|
| LeiaMe | Como a planilha funciona |
| Painel | Resumo: estoque, cobertura, rupturas, itens a repor, excesso e atendimento das lojas |
| Parametros | Células amarelas editáveis: lead time, nível de serviço (Z), cobertura-alvo, limite de excesso, limites da curva ABC |
| Produtos | Demanda diária, desvio, estoque de segurança, ponto de reposição, cobertura, curva ABC, status e quantidade sugerida |
| Lojas / Alocacao | Necessidade por loja e rateio quando o estoque não cobre tudo |
| VendasBrutas | Dados brutos em formato longo, para praticar com Power Query |
| RoteiroPowerQuery | Passo a passo para refazer o tratamento no Power Query |

## Lógica principal

- **Estoque de segurança** = Z × desvio diário × raiz do lead time.
- **Ponto de reposição** = demanda diária × lead time + estoque de segurança.
- **Curva ABC** acumulada por valor, com limites de 80% e 95%.
- **Status:** Ruptura, Repor, Excesso ou OK. Só Ruptura e Repor geram sugestão de compra.
- **Alocação:** fator = mínimo entre 1 e (disponível ÷ necessidade).

`vendas_brutas_ficticias.csv` é a mesma base de vendas em formato longo (SKU, Semana, Loja, Qtd).
