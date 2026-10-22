# Registro de decisões analíticas

Este documento registra as principais decisões do projeto, no formato
**Contexto → Decisão → Alternativas consideradas → Consequência → Onde está**.
Cada decisão tem um código (DA-XX) para ser citada em commits e pull requests.

Os números vêm das saídas do notebook [`Notebooks/Análise de Segmentação de Clientes - v2.ipynb`](../Notebooks/).

| Código | Decisão |
|---|---|
| [DA-01](#da-01--remoção-só-dos-erros-óbvios) | Remoção só dos erros óbvios |
| [DA-02](#da-02--variáveis-em-proporção-do-total) | Variáveis em proporção do total |
| [DA-03](#da-03--normalização-min-max-e-pesos-de-negócio) | Normalização Min-Max e pesos de negócio |
| [DA-04](#da-04--k--4-grupos) | k = 4 grupos |
| [DA-05](#da-05--k-means-em-vez-de-clusterização-hierárquica) | K-Means em vez de clusterização hierárquica |
| [DA-06](#da-06--pipeline-de-produção) | Pipeline de produção |

---

## DA-01 — Remoção só dos erros óbvios

- **Contexto:** pela regra do IQR, de 8% a 11% dos clientes são outliers de gasto em algumas categorias; há também uma renda de US$ 666 mil e clientes com mais de 90 anos.
- **Decisão:** remover apenas os erros óbvios (idade acima de 90 anos e renda acima de US$ 300 mil) e manter os gastos altos.
- **Alternativas consideradas:** remover todos os outliers do IQR, o que apagaria justamente os clientes de maior valor.
- **Consequência:** a segmentação consegue isolar o grupo Premium (19% dos clientes, 50% do gasto).
- **Onde está:** item 2.6 da Fase 02.

## DA-02 — Variáveis em proporção do total

- **Contexto:** os gastos por categoria e as compras por canal crescem junto com o gasto total.
- **Decisão:** transformar categorias e canais em **% do total** e criar `TotalAmountSpent` e `TotalPurchases`.
- **Alternativas consideradas:** usar os valores absolutos, que repetiriam a informação do gasto total em várias colunas.
- **Consequência:** os grupos se diferenciam também pelo **mix** de produtos e canais (ex.: Premium compra mais por catálogo).
- **Onde está:** item 4 da Fase 02.

## DA-03 — Normalização Min-Max e pesos de negócio

- **Contexto:** o K-Means usa distâncias, e as colunas têm escalas muito diferentes; o marketing quer priorizar valor do cliente.
- **Decisão:** normalizar de 0 a 1 e aplicar pesos (gasto total 8, total de compras 6, recência/visitas/renda/tempo de cadastro 4, perfil demográfico 2).
- **Alternativas consideradas:** sem pesos, os grupos passam a refletir mais "o que e onde compra" do que "quanto vale" (ARI de 0,20 entre as duas versões).
- **Consequência:** segmentação orientada a valor; a Random Forest e a Informação Mútua confirmam que gasto total, compras e renda são as variáveis que mais definem os grupos.
- **Onde está:** item 4.3 da Fase 03 e item 3 da Fase 04; `PESOS` em `src/utils.py`.

## DA-04 — k = 4 grupos

- **Contexto:** com pesos, não há cotovelo nítido; o melhor silhouette é com k = 2 (0,37), que só separa gasto alto x baixo.
- **Decisão:** k = 4, onde o silhouette se estabiliza (~0,18) e os grupos são acionáveis pelo marketing.
- **Alternativas consideradas:** k = 2 (óbvio demais) e k acima de 5 (grupos pequenos e difíceis de explicar).
- **Consequência:** 4 perfis (Premium, Fiéis de alto volume, Novos e ativos, Em risco de churn) com tamanhos equilibrados (419 a 629 clientes).
- **Onde está:** itens 6.1 e 6.2 da Fase 03.

## DA-05 — K-Means em vez de clusterização hierárquica

- **Contexto:** a clusterização hierárquica (Ward) foi testada como comparação.
- **Decisão:** manter o K-Means.
- **Alternativas consideradas:** hierárquico, com silhouette menor (0,14 contra 0,18) e concordância moderada (ARI de 0,36).
- **Consequência:** modelo mais simples de explicar e capaz de classificar clientes novos com `predict`.
- **Onde está:** item 6.4 da Fase 03.

## DA-06 — Pipeline de produção

- **Contexto:** o cliente novo precisa passar pela mesma normalização e pelos mesmos pesos da base de treino.
- **Decisão:** juntar `MinMaxScaler` + pesos + K-Means em um `Pipeline`, salvo com a ficha do modelo em JSON.
- **Alternativas consideradas:** salvar só o K-Means (versão original), o que exigiria repetir a preparação à mão.
- **Consequência:** o app classifica um cliente a partir dos dados brutos, via `preparar_cliente`.
- **Onde está:** Fase 05; `Model/pipeline_segmentacao.pkl` e `Model/pipeline_segmentacao.json`.
