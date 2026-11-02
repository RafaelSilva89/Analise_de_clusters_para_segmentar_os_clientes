# Registro de decisões analíticas

Este documento registra as principais decisões do projeto, no formato
**Contexto → Decisão → Alternativas consideradas → Consequência → Onde está**.
Cada decisão tem um código (DA-XX) para ser citada em commits e pull requests.

Os números vêm das saídas do notebook [`Notebooks/Análise de Segmentação de Clientes - v2.ipynb`](../Notebooks/); os das decisões DA-07 a DA-12, do notebook `Notebooks/Teste A-B da campanha.ipynb`.

| Código | Decisão |
|---|---|
| [DA-01](#da-01--remoção-só-dos-erros-óbvios) | Remoção só dos erros óbvios |
| [DA-02](#da-02--variáveis-em-proporção-do-total) | Variáveis em proporção do total |
| [DA-03](#da-03--normalização-min-max-e-pesos-de-negócio) | Normalização Min-Max e pesos de negócio |
| [DA-04](#da-04--k--4-grupos) | k = 4 grupos |
| [DA-05](#da-05--k-means-em-vez-de-clusterização-hierárquica) | K-Means em vez de clusterização hierárquica |
| [DA-06](#da-06--pipeline-de-produção) | Pipeline de produção |
| [DA-07](#da-07--segmento-sem-a-resposta-da-campanha-no-teste-ab) | Segmento sem a resposta da campanha no Teste A/B |
| [DA-08](#da-08--experimentos-reconstruídos-com-as-respostas-reais-replay) | Experimentos reconstruídos com as respostas reais (replay) |
| [DA-09](#da-09--lucro-e-ponto-de-equilíbrio-como-métrica-de-decisão) | Lucro e ponto de equilíbrio como métrica de decisão |
| [DA-10](#da-10--teste-ideal-abn-para-validar-e-thompson-sampling-em-produção) | Teste ideal: A/B/n para validar e Thompson Sampling em produção |
| [DA-11](#da-11--tamanho-da-amostra-do-qui-quadrado-com-gofchisquarepower) | Tamanho da amostra do qui-quadrado com `GofChisquarePower` |
| [DA-12](#da-12--o-v2-aponta-para-o-teste-ab-sem-duplicá-lo) | O v2 aponta para o Teste A/B, sem duplicá-lo |

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

## DA-07 — Segmento sem a resposta da campanha no Teste A/B

- **Contexto:** `AcceptedCmp` soma as 6 campanhas, incluindo a última (`Response`), que é o resultado medido no Teste A/B.
- **Decisão:** no notebook do Teste A/B, recalcular o segmento com o pipeline salvo usando só as campanhas 1 a 5 (o histórico de antes da campanha).
- **Alternativas consideradas:** usar o segmento do notebook v2, que deixaria a resposta medida influenciar quem é contatado (vazamento).
- **Consequência:** só 2 clientes mudam de segmento (Premium 419 → 417, Fiéis 629 → 631); o teste fica livre de vazamento.
- **Onde está:** item 3 do notebook `Teste A-B da campanha.ipynb`; `segmentar` em `src/teste_ab.py`.

## DA-08 — Experimentos reconstruídos com as respostas reais (replay)

- **Contexto:** a base não vem de um experimento com sorteio, mas a última campanha foi enviada a todos os clientes.
- **Decisão:** sortear os grupos, aplicar a regra de contato de cada grupo e ler a resposta real de quem foi contatado, com sementes fixas.
- **Alternativas consideradas:** simular taxas inventadas, o que tiraria a ligação com os dados do projeto.
- **Consequência:** nenhuma taxa é inventada; as premissas (mesma oferta, um cliente não influencia o outro) ficam escritas no notebook. No MAB, o cliente é sorteado com reposição, imaginando um fluxo contínuo de clientes novos.
- **Onde está:** abertura e Ciclos 01 a 04 do notebook `Teste A-B da campanha.ipynb`.

## DA-09 — Lucro e ponto de equilíbrio como métrica de decisão

- **Contexto:** a base traz o custo por contato (3) e a receita por resposta (11).
- **Decisão:** decidir pelo lucro e comparar cada taxa com o ponto de equilíbrio (3 / 11 = 27,3%), além da taxa de resposta.
- **Alternativas consideradas:** decidir só pela taxa de resposta, que no Ciclo 01 não mostrou diferença (p = 0,145) enquanto o lucro mostrou (p < 0,001).
- **Consequência:** a recomendação muda de "Premium + Fiéis" para **só Premium**, a única regra com taxa acima do equilíbrio (34,2%) e lucro positivo.
- **Onde está:** item 2 e Ciclos 01 e 02 do notebook `Teste A-B da campanha.ipynb`.

## DA-10 — Teste ideal: A/B/n para validar e Thompson Sampling em produção

- **Contexto:** a campanha se repete e a decisão é sempre "para quem mandar".
- **Decisão:** validar a regra uma vez com um A/B/n (lido também pelo lado Bayesiano) e alocar os contatos no dia a dia com um Multi-Armed Bandit de Thompson, com um grupo de controle fixo de ~10%.
- **Alternativas consideradas:** repetir A/B/n a cada campanha (lucro de −1.200 em 1.000 contatos, contra +480 do Thompson) ou usar o Guloso e o ε-Guloso, que ficaram atrás do Thompson.
- **Consequência:** a campanha fica no lucro enquanto continua aprendendo; o controle fixo mede o ganho real.
- **Onde está:** Ciclo 04 e Conclusão do notebook `Teste A-B da campanha.ipynb`.

## DA-11 — Tamanho da amostra do qui-quadrado com `GofChisquarePower`

- **Contexto:** no notebook PA James ABN do curso, a amostra do qui-quadrado foi calculada com `TTestIndPower` (fórmula do teste t), e o `GofChisquarePower` ficou comentado como "aplicação errada".
- **Decisão:** usar o `GofChisquarePower` (feito para o qui-quadrado e o w de Cohen), com df = número de grupos − 1.
- **Alternativas consideradas:** a fórmula do curso, que pediria 771 contatos por regra em vez de 134.
- **Consequência:** a simulação de 4.000 experimentos deu 79,6% de poder com 134 contatos (os 80% planejados) e 100,0% com 771: a fórmula do teste t superestima a amostra.
- **Onde está:** Ciclo 02 do notebook `Teste A-B da campanha.ipynb`; `tamanho_amostra_qui_quadrado` e `poder_simulado_qui_quadrado` em `src/teste_ab.py`.

## DA-12 — O v2 aponta para o Teste A/B, sem duplicá-lo

- **Contexto:** o v2 recomendava lançar para Premium e, em seguida, para os Fiéis (89% do gasto). O Teste A/B mostrou que, com custo de 3 e receita de 11, só o Premium passa do ponto de equilíbrio de 27,3% (34,2% de resposta).
- **Decisão:** manter a análise do v2 e acrescentar uma nota de validação, uma linha na tabela da resposta de negócio, o limite e o próximo passo atualizados, com link para o notebook do Teste A/B. No app, os Fiéis deixam de ser o "segundo público do lançamento".
- **Alternativas consideradas:** copiar os 4 ciclos para o v2, o que duplicaria o código e deixaria o notebook longo demais; ou não mexer no v2, que ficaria com uma recomendação desatualizada.
- **Consequência:** o v2 continua respondendo **quem são** os segmentos, e o Teste A/B responde **para quem o contato pago compensa**. O v1 não muda.
- **Onde está:** Insights, Limites e Próximos passos do v2; dicionário `SEGMENTOS` do `app.py` (gerado pela célula `%%writefile` do v2).
