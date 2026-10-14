# Medidas DAX: invoices e embarques

Tabela principal: `fInvoices` (uma linha por invoice/contêiner). Relacione `dCalendario[data]` com `fInvoices[data_indicacao]` (ativo) e use `USERELATIONSHIP` para as demais datas, se precisar.

## Indicadores

**Invoices indicadas**

Contagem de invoices por data de indicação.

```dax
[Invoices indicadas] = COUNTROWS(fInvoices)
```

**% cancelamentos**

Invoices canceladas ÷ total indicado.

```dax
[% cancelamentos] = DIVIDE(CALCULATE(COUNTROWS(fInvoices), fInvoices[status_carregamento] = "Cancelado"), COUNTROWS(fInvoices))
```

**Lead time indicação → carregamento (dias)**

Média de (data_carregamento − data_indicacao) das invoices liberadas, sem canceladas.

```dax
[Lead time indicação → carregamento (dias)] = AVERAGEX(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado"), DATEDIFF(fInvoices[data_indicacao], fInvoices[data_carregamento], DAY))
```

**Carregamento → faturamento (dias)**

Média de (data_faturamento − data_carregamento). Reflete cargas aguardando laudo.

```dax
[Carregamento → faturamento (dias)] = AVERAGEX(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado"), DATEDIFF(fInvoices[data_carregamento], fInvoices[data_faturamento], DAY))
```

**Faturamento → documentação (dias)**

Média de (data_documentacao − data_faturamento).

```dax
[Faturamento → documentação (dias)] = AVERAGEX(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado"), DATEDIFF(fInvoices[data_faturamento], fInvoices[data_documentacao], DAY))
```

**Documentação → liberação (dias)**

Média de (data_liberacao − data_documentacao).

```dax
[Documentação → liberação (dias)] = AVERAGEX(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado"), DATEDIFF(fInvoices[data_documentacao], fInvoices[data_liberacao], DAY))
```

**Lead time total indicação → liberação (dias)**

Média de (data_liberacao − data_indicacao).

```dax
[Lead time total indicação → liberação (dias)] = AVERAGEX(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado"), DATEDIFF(fInvoices[data_indicacao], fInvoices[data_liberacao], DAY))
```

**% liberadas dentro do deadline_carga**

Invoices com data_liberacao ≤ deadline_carga ÷ invoices liberadas.

```dax
[% liberadas dentro do deadline_carga] = DIVIDE(COUNTROWS(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado" && fInvoices[data_liberacao] <= fInvoices[deadline_carga])), COUNTROWS(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado")))
```

**% chegada ao porto dentro do deadline_porto**

Invoices com data_chegada_porto ≤ deadline_porto ÷ invoices com chegada registrada (as ainda em trânsito saem do cálculo).

```dax
[% chegada ao porto dentro do deadline_porto] = DIVIDE(COUNTROWS(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_chegada_porto]) && fInvoices[data_chegada_porto] <= fInvoices[deadline_porto])), COUNTROWS(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_chegada_porto]))))
```

**% draft enviado dentro do deadline_draft**

Invoices com data_envio_draft ≤ deadline_draft ÷ invoices com draft enviado.

```dax
[% draft enviado dentro do deadline_draft] = DIVIDE(COUNTROWS(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_envio_draft]) && fInvoices[data_envio_draft] <= fInvoices[deadline_draft])), COUNTROWS(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_envio_draft]))))
```

**Valor total de estadia (R$)**

Soma de valor_estadia.

```dax
[Valor total de estadia (R$)] = SUM(fInvoices[valor_estadia])
```

**% invoices com estadia**

Invoices liberadas com dias_estadia > 0 ÷ invoices liberadas.

```dax
[% invoices com estadia] = DIVIDE(COUNTROWS(FILTER(fInvoices, fInvoices[dias_estadia] > 0 && NOT ISBLANK(fInvoices[data_liberacao]))), COUNTROWS(FILTER(fInvoices, NOT ISBLANK(fInvoices[data_liberacao]) && fInvoices[status_carregamento] <> "Cancelado")))
```

**Estadia média por invoice com estadia (R$)**

Valor de estadia ÷ invoices com estadia.

```dax
[Estadia média por invoice com estadia (R$)] = DIVIDE(SUM(fInvoices[valor_estadia]), COUNTROWS(FILTER(fInvoices, fInvoices[dias_estadia] > 0)))
```

**Dias médios de estadia (invoices com estadia)**

Média de dias_estadia nas invoices com estadia.

```dax
[Dias médios de estadia (invoices com estadia)] = AVERAGEX(FILTER(fInvoices, fInvoices[dias_estadia] > 0), fInvoices[dias_estadia])
```

**% trocas de contêiner (mesmo veículo traz e leva)**

Invoices em que placa_veiculo_1 = placa_veiculo_2 ÷ invoices não canceladas.

```dax
[% trocas de contêiner (mesmo veículo traz e leva)] = DIVIDE(COUNTROWS(FILTER(fInvoices, fInvoices[placa_veiculo_1] = fInvoices[placa_veiculo_2] && fInvoices[status_carregamento] <> "Cancelado")), COUNTROWS(FILTER(fInvoices, fInvoices[status_carregamento] <> "Cancelado")))
```
