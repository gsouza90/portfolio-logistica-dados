# Medidas DAX: estoque e inventário

Cole as medidas no Power BI na ordem abaixo. As tabelas esperadas são `fEstoque`, `fPedidos`, `fCompras`, `fContagem`, `fMov`, `fCustos`, `dProduto` e `dCalendario` (relacionamentos no README do projeto).

## Medidas base

```dax
[Dias no Período] = DISTINCTCOUNT(fEstoque[data])
[Meses] = DISTINCTCOUNT(dCalendario[ano_mes])
[Valor Estoque Médio] = DIVIDE(SUM(fEstoque[valor_estoque]), [Dias no Período])
[Estoque Médio (un)] = DIVIDE(SUM(fEstoque[qtd_sistema]), [Dias no Período])
[Valor Estoque Fim] = CALCULATE(SUM(fEstoque[valor_estoque]), LASTDATE(fEstoque[data]))
[COGS] = SUM(fPedidos[custo_atendido])
[Vendas R$] = SUM(fPedidos[valor_atendido])
[SKU-dias Ativos] = SUM(fEstoque[estoque_ativo])
```

## Os 40 indicadores

### Acuracidade e inventário

**1. Inventory Accuracy**

Contagens sem divergência após recontagem ÷ contagens realizadas.

```dax
[Inventory Accuracy] = DIVIDE(SUM(fContagem[sem_div_final]), SUM(fContagem[realizada]))
```

**2. Count Accuracy**

Contagens sem divergência já na 1ª contagem ÷ contagens realizadas.

```dax
[Count Accuracy] = DIVIDE(SUM(fContagem[sem_div_1a]), SUM(fContagem[realizada]))
```

**3. Cycle Count Compliance**

Contagens cíclicas realizadas no prazo (tolerância de 1 dia) ÷ planejadas. Usa a data planejada.

```dax
[Cycle Count Compliance] = CALCULATE(DIVIDE(SUM(fContagem[no_prazo]), SUM(fContagem[planejada])), fContagem[tipo_contagem] = "Cíclica", USERELATIONSHIP(fContagem[data_planejada], dCalendario[data]))
```

**4. Inventory Adjustment Rate**

Valor absoluto dos ajustes de inventário ÷ valor médio do estoque.

```dax
[Inventory Adjustment Rate] = DIVIDE(CALCULATE(SUMX(fMov, ABS(fMov[valor])), fMov[tipo_mov] = "AJUSTE_INVENTARIO"), [Valor Estoque Médio])
```

**5. Acuracidade de endereço**

Contagens em que o item estava no endereço correto ÷ contagens realizadas.

```dax
[Acuracidade de endereço] = DIVIDE(SUM(fContagem[endereco_correto]), SUM(fContagem[realizada]))
```

**6. Divergência de inventário (%)**

Soma das divergências finais em módulo (un) ÷ quantidade do sistema nas contagens.

```dax
[Divergência de inventário (%)] = DIVIDE(SUMX(fContagem, ABS(fContagem[divergencia_final])), SUM(fContagem[qtd_sistema]))
```

**7. Valor da divergência (R$)**

Divergência final em módulo × custo unitário. Para o líquido (sobra − falta) use valor_divergencia_liq.

```dax
[Valor da divergência (R$)] = SUM(fContagem[valor_divergencia_abs])
```

**8. Taxa de recontagem**

Contagens que precisaram de recontagem ÷ contagens realizadas.

```dax
[Taxa de recontagem] = DIVIDE(SUM(fContagem[recontada]), SUM(fContagem[realizada]))
```

**9. Cobertura do plano de inventário**

SKUs distintos contados desde o início do ano de análise (out/25) ÷ total de SKUs (40). Acumulado.

```dax
[Cobertura do plano de inventário] = DIVIDE(CALCULATE(DISTINCTCOUNT(fContagem[sku]), fContagem[realizada] = 1, DATESYTD(dCalendario[data], "9/30")), COUNTROWS(dProduto))
```

**10. Produtividade de inventário**

Itens (SKUs) contados por hora de contagem.

```dax
[Produtividade de inventário] = DIVIDE(SUM(fContagem[realizada]), DIVIDE(SUM(fContagem[tempo_min]), 60))
```

### Giro, cobertura e níveis

**11. Giro de estoque (anualizado)**

Custo das vendas do mês ÷ valor médio do estoque × 12. Para vários meses: divida por [Meses] em vez de multiplicar por 12.

```dax
[Giro de estoque (anualizado)] = DIVIDE([COGS], [Valor Estoque Médio]) * 12
```

**12. Days of Inventory (DOI)**

Valor médio do estoque ÷ custo diário das vendas (dias de cobertura).

```dax
[Days of Inventory (DOI)] = DIVIDE([Valor Estoque Médio], DIVIDE([COGS], [Dias no Período]))
```

**13. Estoque médio (un)**

Média diária da quantidade em estoque (sistema).

```dax
[Estoque médio (un)] = [Estoque Médio (un)]
```

**14. Valor do estoque (fim do período, R$)**

Σ quantidade × custo no último dia do período.

```dax
[Valor do estoque (fim do período, R$)] = [Valor Estoque Fim]
```

**15. Estoque de segurança: % SKU-dias abaixo**

SKU-dias ativos com estoque disponível menor que o estoque de segurança ÷ SKU-dias ativos. O parâmetro está em dProduto[estoque_seguranca].

```dax
[Estoque de segurança: % SKU-dias abaixo] = DIVIDE(SUM(fEstoque[flag_abaixo_ss]), [SKU-dias Ativos])
```

**16. Estoque mínimo: % SKU-dias abaixo**

SKU-dias ativos com disponível abaixo do mínimo (50% do estoque de segurança) ÷ SKU-dias ativos.

```dax
[Estoque mínimo: % SKU-dias abaixo] = DIVIDE(SUM(fEstoque[flag_abaixo_min]), [SKU-dias Ativos])
```

**17. Ponto de pedido: % SKU-dias no ou abaixo**

SKU-dias ativos com disponível ≤ ponto de pedido ÷ SKU-dias ativos (mede quanto do tempo o SKU está em fase de reposição).

```dax
[Ponto de pedido: % SKU-dias no ou abaixo] = DIVIDE(SUM(fEstoque[flag_abaixo_rop]), [SKU-dias Ativos])
```

**18. Estoque máximo: % SKU-dias acima**

SKU-dias ativos com estoque (sistema) acima do máximo ÷ SKU-dias ativos.

```dax
[Estoque máximo: % SKU-dias acima] = DIVIDE(SUM(fEstoque[flag_acima_max]), [SKU-dias Ativos])
```

**19. Lead time de reposição real (dias)**

Média de (data de recebimento − data do pedido) das compras recebidas. Compare com dProduto[lead_time_planejado].

```dax
[Lead time de reposição real (dias)] = AVERAGE(fCompras[lead_time_real])
```

### Disponibilidade e nível de serviço

**20. Acuracidade de reposição**

Compras recebidas no prazo e com quantidade ≥ 95% do pedido ÷ compras recebidas.

```dax
[Acuracidade de reposição] = DIVIDE(SUM(fCompras[reposicao_ok]), SUM(fCompras[recebido]))
```

**21. Stockout Rate**

SKU-dias ativos com disponível = 0 ÷ SKU-dias ativos.

```dax
[Stockout Rate] = DIVIDE(SUM(fEstoque[flag_ruptura]), [SKU-dias Ativos])
```

**22. Inventory Availability (valor)**

Valor do estoque disponível (sem bloqueado, quarentena e avariado) ÷ valor do estoque no sistema.

```dax
[Inventory Availability (valor)] = DIVIDE(SUM(fEstoque[valor_disponivel]), SUM(fEstoque[valor_estoque]))
```

**23. Backorder Rate**

Quantidade pendente por falta ÷ quantidade pedida.

```dax
[Backorder Rate] = DIVIDE(SUM(fPedidos[qtd_backorder]), SUM(fPedidos[qtd_pedida]))
```

**24. Fill Rate (linhas)**

Linhas de pedido atendidas integralmente ÷ total de linhas. Para fill rate em unidades: SUM(qtd_atendida) ÷ SUM(qtd_pedida).

```dax
[Fill Rate (linhas)] = DIVIDE(SUM(fPedidos[linha_completa]), COUNTROWS(fPedidos))
```

### Excesso, obsolescência e perdas

**25. Excess Inventory (% do valor)**

Valor do estoque acima do máximo (SKUs ativos) ÷ valor total do estoque.

```dax
[Excess Inventory (% do valor)] = DIVIDE(SUM(fEstoque[valor_excesso]), SUM(fEstoque[valor_estoque]))
```

**26. Dead Stock (% do valor)**

Valor de SKUs com estoque e sem saída há 90 dias ou mais ÷ valor total do estoque.

```dax
[Dead Stock (% do valor)] = DIVIDE(CALCULATE(SUM(fEstoque[valor_estoque]), fEstoque[flag_dead_stock] = 1), SUM(fEstoque[valor_estoque]))
```

**27. Slow Moving (% do valor)**

Valor de SKUs com cobertura > 60 dias e saída nos últimos 90 dias ÷ valor total do estoque.

```dax
[Slow Moving (% do valor)] = DIVIDE(CALCULATE(SUM(fEstoque[valor_estoque]), fEstoque[flag_slow_moving] = 1), SUM(fEstoque[valor_estoque]))
```

**28. Aging de estoque (idade média, dias)**

Idade média do estoque (FIFO) ponderada pelo valor. Para % acima de 90 dias use SUM(valor_acima_90d) ÷ SUM(valor_estoque).

```dax
[Aging de estoque (idade média, dias)] = DIVIDE(SUMX(fEstoque, fEstoque[idade_media_dias] * fEstoque[valor_estoque]), SUM(fEstoque[valor_estoque]))
```

**29. Obsolescence Rate**

Valor de SKUs descontinuados em estoque ÷ valor total do estoque.

```dax
[Obsolescence Rate] = DIVIDE(SUM(fEstoque[valor_obsoleto]), SUM(fEstoque[valor_estoque]))
```

**30. Obsolete Inventory Value (fim, R$)**

Valor em R$ do estoque obsoleto no último dia do período.

```dax
[Obsolete Inventory Value (fim, R$)] = CALCULATE(SUM(fEstoque[valor_obsoleto]), LASTDATE(fEstoque[data]))
```

**31. Shrinkage Rate**

Ajustes negativos por perda não explicada (perda não identificada, furto/extravio, quebra não registrada) ÷ valor médio do estoque.

```dax
[Shrinkage Rate] = DIVIDE(-CALCULATE(SUM(fMov[valor]), fMov[tipo_mov] = "AJUSTE_INVENTARIO", fMov[perda_nao_explicada] = 1), [Valor Estoque Médio])
```

**32. Taxa de avaria**

Unidades avariadas ÷ unidades movimentadas (entradas + saídas).

```dax
[Taxa de avaria] = DIVIDE(-CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "AVARIA"), CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "ENTRADA_COMPRA") - CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "SAIDA_VENDA"))
```

### Custos e retorno

**33. Carrying Cost (% ao ano)**

Custo total de manter estoque no mês ÷ valor médio do estoque × 12 (capital, armazenagem, seguro, mão de obra e perdas).

```dax
[Carrying Cost (% ao ano)] = DIVIDE(SUM(fCustos[custo_total]), [Valor Estoque Médio]) * 12
```

**34. Custo por unidade estocada (R$/un/mês)**

Custo total de manter estoque no mês ÷ estoque médio em unidades.

```dax
[Custo por unidade estocada (R$/un/mês)] = DIVIDE(SUM(fCustos[custo_total]), [Estoque Médio (un)])
```

**35. GMROI (anualizado)**

Margem bruta do mês ÷ valor médio do estoque a custo × 12.

```dax
[GMROI (anualizado)] = DIVIDE(SUM(fPedidos[margem_bruta]), [Valor Estoque Médio]) * 12
```

**36. Inventory-to-Sales Ratio**

Valor do estoque no fim do mês ÷ vendas do mês (R$).

```dax
[Inventory-to-Sales Ratio] = DIVIDE([Valor Estoque Fim], [Vendas R$])
```

**37. Inventory Investment (R$ médio)**

Capital médio imobilizado em estoque no período.

```dax
[Inventory Investment (R$ médio)] = [Valor Estoque Médio]
```

**38. Stock Utilization Rate**

Definição adotada: unidades expedidas no mês ÷ (estoque no 1º dia + entradas do mês), isto é, o quanto do disponível foi efetivamente consumido (sell-through).

```dax
[Stock Utilization Rate] = DIVIDE(-CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "SAIDA_VENDA"), CALCULATE(SUM(fEstoque[qtd_sistema]), FIRSTDATE(fEstoque[data])) + CALCULATE(SUM(fMov[qtd]), fMov[tipo_mov] = "ENTRADA_COMPRA"))
```

**39. Acuracidade do status do estoque**

Contagens em que o status do sistema (disponível, bloqueado, quarentena) bate com o status real ÷ contagens realizadas.

```dax
[Acuracidade do status do estoque] = DIVIDE(SUM(fContagem[status_correto]), SUM(fContagem[realizada]))
```

**40. Disponibilidade real vs sistêmica (R$ no fim)**

Valor no sistema − valor realmente utilizável (bloqueado + quarentena + avariado) no último dia do período.

```dax
[Disponibilidade real vs sistêmica (R$ no fim)] = CALCULATE(SUM(fEstoque[valor_estoque]) - SUM(fEstoque[valor_disponivel]), LASTDATE(fEstoque[data]))
```
