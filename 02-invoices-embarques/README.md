# Projeto 2: Invoices e embarques de exportação

Base fictícia de **1,478 invoices** (1 contêiner por invoice) indicadas entre 01/10/2025 e 30/09/2026, com o ciclo completo do embarque e o custo de estadia. Serve para montar um painel de acompanhamento logístico.

> Dados 100% fictícios. Projeto pessoal de portfólio.

## Colunas principais (`fInvoices`)

Número da invoice, data de indicação, porto de origem (Paranaguá, Itajaí, Santos), número do contêiner (padrão ISO 6346), data de coleta do contêiner, armador, porto e país de destino, deadlines de draft, carga e porto, status do carregamento, datas de carregamento, faturamento, documentação e liberação, placa e transportador dos dois veículos (placas no padrão Mercosul, 681 distintas), data de chegada do veículo e valor de estadia.

Colunas extras para permitir os indicadores de prazo: produto, peso, valor em USD, data de envio do draft, data de chegada ao porto, dias de estadia e causa da estadia.

## Premissas

- **Veículo 1** traz o contêiner vazio à planta; **veículo 2** leva o contêiner carregado ao porto. Em cerca de metade dos casos é o mesmo veículo (troca de contêiner).
- **Deadlines:** o do porto é o limite de entrada no terminal; o da carga é o do porto menos o trânsito planta→porto; o do draft é 3 dias antes do porto.
- **Estadia:** dias entre a chegada do veículo e a liberação, menos 1 dia de franquia, vezes a diária do transportador.
- **Causas de estadia:** documento liberativo, alteração de PCP/saldo, laudo laboratorial, programação incorreta, problema com veículo. Parte das estadias fica "Sem causa registrada", de propósito, para praticar tratamento de dados.
- **Cenário simulado:** a partir de 01/03/2026 os atrasos por documento diminuem, como se uma automação documental tivesse sido implantada, para o painel mostrar o antes e depois.

## Indicadores sugeridos (15)

Lead time por etapa (indicação → carregamento → faturamento → documentação → liberação), cumprimento dos deadlines de draft, carga e porto, valor total de estadia, % de invoices com estadia, estadia média, dias de estadia, estadia por causa e por transportador, % de trocas de contêiner e cancelamentos. Definições e DAX em [dax/medidas.md](dax/medidas.md); valores esperados em [docs/gabarito_mensal.csv](docs/gabarito_mensal.csv).

## Como usar no Power BI

1. Importe os CSVs de `dados/`.
2. Relacione `dCalendario[data]` com `fInvoices[data_indicacao]` (ativo). Para as outras datas, crie relacionamentos inativos e use `USERELATIONSHIP`.
3. Relacione as dimensões: `transportador_1` com `dTransportador`, `armador` com `dArmador`, `porto_destino` com `dDestino` e `porto_origem` com `dPorto`.
4. Cole as medidas de `dax/medidas.md` e compare com o gabarito.

## Reproduzir os dados

```bash
cd simulacao
pip install -r requirements.txt
python gerar_base_invoices.py saida/Base_Invoices.xlsx saida/fInvoices.csv
```

<!-- Adicione aqui prints do painel quando ele estiver pronto: ![Painel de embarques](docs/imagens/painel.png) -->
