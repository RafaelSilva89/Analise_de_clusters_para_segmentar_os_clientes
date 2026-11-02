"""Funções do notebook "Teste A-B da campanha": os 4 ciclos (A/B, A/B/n, Bayesiano e Multi-Armed Bandit).

A última campanha foi enviada a TODOS os clientes, então a base tem a resposta real de cada um (`Response`).
Os experimentos são reconstruídos com essas respostas (replay): sorteamos os grupos, aplicamos a regra de
contato de cada grupo e lemos a resposta verdadeira de quem foi contatado.
"""
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats import api as sms
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest

from src.utils import COLUNAS_MODELO, preparar_cliente

CUSTO_CONTATO = 3        # Z_CostContact: custo de cada contato da campanha
RECEITA_RESPOSTA = 11    # Z_Revenue: receita de cada cliente que aceita a oferta
PONTO_EQUILIBRIO = CUSTO_CONTATO / RECEITA_RESPOSTA  # taxa de resposta a partir da qual o contato dá lucro

CAMPANHAS_ANTERIORES = ['AcceptedCmp1', 'AcceptedCmp2', 'AcceptedCmp3', 'AcceptedCmp4', 'AcceptedCmp5']
COLUNAS_BRUTAS = ['Year_Birth', 'Education', 'Marital_Status', 'Income', 'Kidhome', 'Teenhome', 'LifeTime',
                  'Recency', 'MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts',
                  'MntGoldProds', 'NumWebPurchases', 'NumCatalogPurchases', 'NumStorePurchases',
                  'NumDealsPurchases', 'NumWebVisitsMonth']

# Uma cor fixa por entidade (paleta categórica validada, sempre na mesma ordem)
CORES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']


def limpar_base(df):
    """Os mesmos filtros de limpeza do notebook v2 (Fase 02 e Feature Engineering)."""
    df = df.dropna(subset=['Income'])
    df = df[(df.Income < 200000) & (df.Year_Birth > 1930) & (df.Marital_Status != 'Absurd')]
    compras = df.NumWebPurchases + df.NumCatalogPurchases + df.NumStorePurchases
    df = df[(compras > 0) & (df.NumDealsPurchases <= compras)].copy()
    df['LifeTime'] = (pd.to_datetime('2014-10-05') - pd.to_datetime(df.Dt_Customer, dayfirst=True)).dt.days / 30
    return df


def segmentar(df, modelo, com_resposta):
    """Segmento de cada cliente pelo pipeline salvo na Fase 05.

    `com_resposta=False` monta `AcceptedCmp` só com as campanhas 1 a 5 (o histórico de ANTES da campanha),
    para que a resposta que vamos medir não ajude a escolher quem recebe a campanha (vazamento).
    """
    clientes = []
    for _, linha in df.iterrows():
        dados = {coluna: linha[coluna] for coluna in COLUNAS_BRUTAS}
        dados['AcceptedCmp'] = linha[CAMPANHAS_ANTERIORES].sum() + (linha['Response'] if com_resposta else 0)
        clientes.append(preparar_cliente(dados))
    X = pd.concat(clientes)[COLUNAS_MODELO]
    clusters = modelo['pipeline'].predict(X)
    return pd.Series(clusters, index=df.index).map(modelo['segmentos'])


def lucro(resposta, contatado):
    """Lucro de cada cliente: receita se respondeu, menos o custo se foi contatado (0 se não foi contatado)."""
    return contatado * (RECEITA_RESPOSTA * resposta - CUSTO_CONTATO)


def sortear_grupos(n, grupos, semente):
    """Sorteia cada cliente em um dos grupos, em partes iguais (a divisão aleatória do experimento)."""
    rng = np.random.default_rng(semente)
    rotulos = np.resize(np.array(grupos), n)
    return rng.permutation(rotulos)


def teste_srm(contagens):
    """Sample Ratio Mismatch: a divisão saiu do jeito planejado (partes iguais)? p baixo = sorteio com problema."""
    return stats.chisquare(contagens).pvalue


def tamanho_amostra_proporcoes(p_controle, p_tratamento, alpha=0.05, poder=0.80):
    """Quantos contatos cada grupo precisa para enxergar a diferença entre duas taxas (Cohen's h)."""
    efeito = sms.proportion_effectsize(p_tratamento, p_controle)
    n = sms.NormalIndPower().solve_power(effect_size=efeito, alpha=alpha, power=poder)
    return int(np.ceil(n)), efeito


def tamanho_amostra_qui_quadrado(taxas, alpha=0.05, poder=0.80):
    """Contatos por grupo para o qui-quadrado com k grupos enxergar taxas tão diferentes quanto `taxas`."""
    taxas = np.asarray(taxas, dtype=float)
    k = len(taxas)
    # tabela k x 2 (respondeu / não respondeu) com o mesmo número de contatos por grupo
    observado = np.column_stack([taxas, 1 - taxas]) / k
    esperado = np.outer(observado.sum(axis=1), observado.sum(axis=0))
    w = np.sqrt(((observado - esperado) ** 2 / esperado).sum())  # tamanho do efeito w de Cohen
    n_total = sms.GofChisquarePower().solve_power(effect_size=w, alpha=alpha, power=poder, n_bins=k)
    return int(np.ceil(n_total / k)), w


def poder_simulado_qui_quadrado(taxas, n_por_grupo, alpha=0.05, n_simulacoes=4000, semente=42):
    """Confere o tamanho de amostra na prática: simula muitos experimentos com essas taxas e conta em quantos
    o qui-quadrado encontra a diferença (p < alpha). Essa fração é o poder real do teste."""
    rng = np.random.default_rng(semente)
    taxas = np.asarray(taxas, dtype=float)
    acertos = 0
    for _ in range(n_simulacoes):
        respostas = rng.binomial(n_por_grupo, taxas)
        tabela = np.column_stack([respostas, n_por_grupo - respostas])
        acertos += stats.chi2_contingency(tabela)[1] < alpha
    return acertos / n_simulacoes


def teste_z_proporcoes(sucessos, contatos):
    """Teste z de duas proporções (B contra A) + intervalo de 95% da diferença B - A."""
    sucessos, contatos = np.asarray(sucessos), np.asarray(contatos)
    z, p = proportions_ztest(sucessos[::-1], contatos[::-1])  # ordem B, A: z positivo quando B é maior
    inferior, superior = confint_proportions_2indep(sucessos[1], contatos[1], sucessos[0], contatos[0])
    taxa_a, taxa_b = sucessos / contatos
    return {'taxa A': taxa_a, 'taxa B': taxa_b, 'diferença (B - A)': taxa_b - taxa_a,
            'IC 95% inferior': inferior, 'IC 95% superior': superior, 'z': z, 'p-valor': p}


def post_hoc_bonferroni(tabela, alpha=0.05):
    """Qui-quadrado de cada par de grupos, com o p-valor corrigido por Bonferroni (p × número de pares)."""
    pares = list(combinations(tabela.index, 2))
    linhas = []
    for a, b in pares:
        p = stats.chi2_contingency(tabela.loc[[a, b]])[1]
        p_corrigido = min(p * len(pares), 1.0)
        linhas.append({'par': f'{a} × {b}', 'p-valor': p, 'p-valor corrigido': p_corrigido,
                       'diferença real?': 'sim' if p_corrigido < alpha else 'não'})
    return pd.DataFrame(linhas)


def comparar_bayesiano(sucessos, contatos, n_amostras=200_000, semente=42):
    """Teste A/B Bayesiano com a Beta(1 + respostas, 1 + não respostas) de cada grupo.

    Retorna P(B > A), a perda esperada de cada escolha (quanto de taxa perdemos, em média, se escolhermos
    o grupo errado) e a chance de cada grupo passar do ponto de equilíbrio (dar lucro).
    """
    rng = np.random.default_rng(semente)
    (s_a, s_b), (n_a, n_b) = sucessos, contatos
    taxa_a = rng.beta(1 + s_a, 1 + n_a - s_a, n_amostras)
    taxa_b = rng.beta(1 + s_b, 1 + n_b - s_b, n_amostras)
    return {'P(B > A)': np.mean(taxa_b > taxa_a),
            'perda ao escolher A': np.mean(np.maximum(taxa_b - taxa_a, 0)),
            'perda ao escolher B': np.mean(np.maximum(taxa_a - taxa_b, 0)),
            'P(A dá lucro)': np.mean(taxa_a > PONTO_EQUILIBRIO),
            'P(B dá lucro)': np.mean(taxa_b > PONTO_EQUILIBRIO)}


# ---------------------------------------------------------------- Multi-Armed Bandit (Ciclo 04)
# Cada "braço" é um segmento. A cada contato o agente escolhe um segmento, um cliente desse segmento é
# sorteado e a resposta REAL dele vira a recompensa (1 = aceitou a oferta, 0 = não aceitou).

class AgenteAleatorio:
    """Escolhe o segmento ao acaso, em partes iguais: é o que um teste A/B/n faz durante todo o teste."""
    nome = 'Aleatório (A/B/n)'

    def __init__(self, k, rng):
        self.k, self.rng = k, rng
        self.respostas, self.contatos = np.zeros(k), np.zeros(k)

    def escolher(self):
        return int(self.rng.integers(self.k))

    def atualizar(self, braco, recompensa):
        self.respostas[braco] += recompensa
        self.contatos[braco] += 1


class AgenteOnisciente(AgenteAleatorio):
    """Já sabe qual segmento responde mais e só contata ele. Não existe na prática: é a referência do máximo."""
    nome = 'Onisciente'

    def __init__(self, k, rng, taxas_reais):
        super().__init__(k, rng)
        self.melhor = int(np.argmax(taxas_reais))

    def escolher(self):
        return self.melhor


class AgenteGuloso(AgenteAleatorio):
    """Testa cada segmento uma vez e depois fica sempre com o de maior taxa observada (decide rápido demais)."""
    nome = 'Guloso'

    def escolher(self):
        if self.contatos.min() == 0:
            return int(np.argmin(self.contatos))
        return int(np.argmax(self.respostas / self.contatos))


class AgenteEpsilonGuloso(AgenteGuloso):
    """Guloso "controlado" com ε decrescente (Aula 41 do curso): explora ao acaso com probabilidade ε,
    e o ε cai a cada contato (ε = (1 - decaimento) ^ contato). Explora muito no começo e quase nada no fim."""

    def __init__(self, k, rng, decaimento=0.01):
        super().__init__(k, rng)
        self.decaimento, self.t = decaimento, 0
        self.nome = f'ε-Guloso (decaimento {decaimento:.0%})'

    def escolher(self):
        epsilon = (1 - self.decaimento) ** self.t
        self.t += 1
        if self.rng.random() < epsilon:
            return int(self.rng.integers(self.k))
        return super().escolher()


class AgenteThompson(AgenteAleatorio):
    """Sorteia uma taxa possível de cada segmento da sua Beta e contata o segmento com o maior sorteio."""
    nome = 'Thompson'

    def escolher(self):
        sorteio = self.rng.beta(1 + self.respostas, 1 + self.contatos - self.respostas)
        return int(np.argmax(sorteio))


def simular_bandit(criar_agente, respostas_por_braco, n_contatos, n_episodios, semente=42):
    """Roda o agente `n_episodios` vezes, cada uma com `n_contatos` contatos.

    Retorna a média, por contato, das respostas acumuladas e a fração dos contatos que foi para cada braço.
    """
    rng = np.random.default_rng(semente)
    k = len(respostas_por_braco)
    acumulado = np.zeros(n_contatos)
    contatos_por_braco = np.zeros(k)
    for _ in range(n_episodios):
        agente = criar_agente(k, rng)
        respostas = np.zeros(n_contatos)
        for t in range(n_contatos):
            braco = agente.escolher()
            recompensa = rng.choice(respostas_por_braco[braco])
            agente.atualizar(braco, recompensa)
            respostas[t] = recompensa
        acumulado += np.cumsum(respostas)
        contatos_por_braco += agente.contatos
    return {'agente': agente.nome, 'respostas acumuladas': acumulado / n_episodios,
            'fração por braço': contatos_por_braco / contatos_por_braco.sum()}
