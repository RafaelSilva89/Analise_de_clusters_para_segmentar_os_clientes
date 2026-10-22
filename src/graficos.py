"""Funções de gráficos usadas no notebook. Cada gráfico é salvo na pasta Imagens/ do projeto."""
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

PASTA_IMAGENS = Path(__file__).resolve().parents[1] / 'Imagens'

FIRST_FIG = 0
SECOND_FIG = 1
SUBTITLE_COLOR = '#656565'

NOMES_PRODUTOS = {'MntWines': 'Vinhos',
                  'MntFruits': 'Frutas',
                  'MntMeatProducts': 'Carnes',
                  'MntFishProducts': 'Peixes',
                  'MntSweetProducts': 'Doces',
                  'MntGoldProds': 'Ouro'}


def salvar(titulo):
    plt.savefig(PASTA_IMAGENS / f'{titulo}.png', bbox_inches='tight')


# Gráfico boxplot + stripplot para variáveis numéricas
def plot_num(df, feature, titulo):
    fig = plt.figure(figsize=(8, 5))
    # Para que o título não fique cortado na figura.
    plt.subplots_adjust(top=0.9)
    plt.suptitle(titulo, fontsize=20, y=1.00, x=0, horizontalalignment='left')

    gs = GridSpec(1, 2)
    sns.boxplot(y=feature, data=df, palette='RdYlGn', ax=fig.add_subplot(gs[0, 0]))
    plt.ylabel(feature, fontsize=15)

    sns.stripplot(y=df[feature], color='darkcyan', ax=fig.add_subplot(gs[0, 1]))
    plt.ylabel(None)
    plt.gca().set_yticklabels([])  # Remove os valores do eixo y do stripplot

    salvar(titulo)
    plt.show()


# Gráfico de barras para variáveis categóricas
def plot_cat(df, feature, titulo):
    plt.figure(figsize=(10, 5))
    # Para que o título não fique cortado na figura.
    plt.subplots_adjust(top=0.9)
    plt.suptitle(titulo, fontsize=20, y=1.00, x=0, horizontalalignment='left')

    ax = sns.countplot(data=df, x=feature, palette='Set2')
    for p in ax.patches:
        ax.annotate(f'\n{p.get_height()}',
                    (p.get_x() + 0.4, p.get_height() + 10),
                    ha='center',
                    fontsize=10,
                    color='black')

    plt.xlabel('\n' + feature, fontsize=12)
    plt.ylabel('Quantidade de Clientes', fontsize=12)
    plt.yticks([])
    plt.xticks(fontsize=10)
    sns.despine(left=True)

    salvar(titulo)
    plt.show()


# Compara uma variável entre os clusters (boxplot + stripplot)
def plot_final(df, x_feature, y_feature, titulo):
    fig = plt.figure(figsize=(20, 8))
    # Para que o título não fique cortado na figura.
    plt.subplots_adjust(top=0.9)
    plt.suptitle(titulo, fontsize=20, y=1.00, x=0.09, horizontalalignment='left')

    gs = GridSpec(1, 2)
    sns.boxplot(x=x_feature, y=y_feature, data=df, ax=fig.add_subplot(gs[0, 0]))
    plt.ylabel(y_feature)
    plt.xlabel(x_feature)

    sns.stripplot(x=x_feature, y=y_feature, data=df, ax=fig.add_subplot(gs[0, 1]))
    plt.ylabel(None)
    plt.xlabel(x_feature)

    salvar(titulo)
    plt.show()


def titulo_e_subtitulo(fig, titulo, subtitulo):
    """Título à esquerda + subtítulo em itálico, usado nos gráficos da EDA."""
    fig.suptitle(titulo, x=0.1, y=1.1, horizontalalignment='left', verticalalignment='top', fontsize=14)
    fig.text(0.12, 1.03, subtitulo, horizontalalignment='left', verticalalignment='top',
             color=SUBTITLE_COLOR, fontstyle='italic', fontsize=11)


# Gráficos customizados da EDA
def plot_data(df, feature, titulo, subtitulo, cor, plot_type):
    if plot_type == 'histogram2':
        # Idade: barras por faixa etária + histograma com média e mediana
        sns.set_style(rc={'axes.facecolor': '#FFFFFF'})
        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(16, 5), gridspec_kw={'width_ratios': [1, 2]})

        sns.countplot(data=df, x='group_age', ax=ax[FIRST_FIG], palette=cor)
        ax[FIRST_FIG].bar_label(ax[FIRST_FIG].containers[0])
        ax[FIRST_FIG].set_title(label='Clientes por faixa etária', fontsize=11)
        ax[FIRST_FIG].set(xlabel='Faixa etária', ylabel='Quantidade')

        sns.histplot(data=df, x=feature, ax=ax[SECOND_FIG], color='#4BBFCC')
        ax[SECOND_FIG].axvline(df[feature].mean(), color='#4250BC', ls='--', label='Idade média')
        ax[SECOND_FIG].axvline(df[feature].median(), color='#232B64', ls='-', label='Idade mediana')
        ax[SECOND_FIG].set_title(label='Distribuição', fontsize=11)
        ax[SECOND_FIG].set(xlabel='Idade', ylabel='Quantidade')
        ax[SECOND_FIG].legend()

        sns.despine(left=True)
        titulo_e_subtitulo(fig, titulo, subtitulo)
        salvar(titulo)

    elif plot_type == 'histogram1':
        # Escolaridade
        plt.figure(figsize=(12, 5))
        label_order = ['Graduation', 'PhD', 'Master', '2n Cycle', 'Basic']

        fig = sns.countplot(data=df, x=feature, palette=cor, order=label_order)
        fig.set(xlabel='Escolaridade', ylabel='Quantidade')
        fig.bar_label(fig.containers[0])

        plt.title(titulo, x=0.20, y=1.1, fontsize=14)
        plt.suptitle(subtitulo, color=SUBTITLE_COLOR, x=0.5, y=0.94, fontstyle='italic', fontsize=11)
        sns.despine(left=True)
        salvar(titulo)

    elif plot_type == 'boxhist':
        # Renda: boxplot + histograma com média e mediana
        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(15, 5), gridspec_kw={'width_ratios': [1, 2]})

        sns.boxplot(data=df, y=feature, ax=ax[0], color='#EB7383')
        ax[0].set(ylabel='Renda anual')

        ax1 = sns.histplot(data=df, x=feature, color='#4BBFCC', ax=ax[1])
        ax1.axvline(df[feature].mean(), color='#9E6B0E', ls='--', label='Renda média')
        ax1.axvline(df[feature].median(), ls='--', label='Renda mediana')
        ax1.set(xlabel='Renda anual', ylabel='Quantidade')
        ax1.legend()

        sns.despine(left=True)
        titulo_e_subtitulo(fig, titulo, subtitulo)
        salvar(titulo)

    elif plot_type == 'histogram':
        # Número de filhos
        plt.figure(figsize=(15, 5))

        fig = sns.countplot(data=df, x=feature, palette=cor)
        fig.bar_label(fig.containers[0])
        fig.set(xlabel='Número de filhos', ylabel='Quantidade')

        plt.title(label=titulo, x=0.15, y=1.14, fontsize=14)
        plt.suptitle(subtitulo, color=SUBTITLE_COLOR, x=0.32, y=0.98, fontstyle='italic', fontsize=11)
        sns.despine(left=True)
        salvar(titulo)

    elif plot_type == 'histogram3':
        # Total vendido por categoria de produto
        produtos = df[list(NOMES_PRODUTOS)].sum().sort_values(ascending=False)
        produtos.index = produtos.index.map(NOMES_PRODUTOS)

        plt.figure(figsize=(15, 5))
        fig = sns.barplot(x=produtos.index, y=produtos.values, palette=cor)
        fig.set(xlabel='Produto', ylabel='Total vendido')
        fig.bar_label(fig.containers[0])

        plt.title(label=titulo, x=0.10, y=1.14, fontsize=14)
        plt.suptitle(subtitulo, color=SUBTITLE_COLOR, x=0.35, y=0.98, fontstyle='italic', fontsize=11)
        sns.despine(left=True)
        salvar(titulo)

    elif plot_type == 'histogram4':
        # Aceitação de cada campanha
        promocoes = df[feature].sum()

        plt.figure(figsize=(15, 5))
        fig = sns.barplot(x=promocoes.index, y=promocoes.values, palette=cor)
        fig.bar_label(fig.containers[0])
        fig.set(xlabel='Campanha', ylabel='Clientes que aceitaram')

        plt.title(label=titulo, x=0.10, y=1.12, fontsize=14)
        plt.suptitle(subtitulo, color=SUBTITLE_COLOR, x=0.45, y=0.96, fontstyle='italic', fontsize=11)
        sns.despine(left=True)
        salvar(titulo)

    elif plot_type == 'histogram5':
        # Distribuição do gasto total
        plt.figure(figsize=(15, 5))

        fig = sns.histplot(data=df, x=feature, color='#4BBFCC')
        fig.axvline(df[feature].mean(), color='#9E6B0E', ls='-', label='Gasto médio')
        fig.axvline(df[feature].median(), ls='--', label='Gasto mediano')
        fig.bar_label(fig.containers[0])
        fig.set(xlabel='Total gasto', ylabel='Número de clientes')
        fig.legend()

        plt.title(label=titulo, x=0.12, y=1.1, fontsize=14)
        plt.suptitle(subtitulo, color=SUBTITLE_COLOR, x=0.35, y=0.95, fontstyle='italic', fontsize=11)
        sns.despine(left=True)
        salvar(titulo)

    elif plot_type == 'correlacao':
        # Renda x gasto total
        plt.figure(figsize=(15, 5))

        fig = sns.scatterplot(data=df, x=feature, y='TotalSpent', color='#4BBFCC')
        fig.set(xlabel='Renda anual', ylabel='Total gasto')

        plt.title(label=titulo, x=0.09, y=1.12, fontsize=14)
        plt.suptitle(subtitulo, color=SUBTITLE_COLOR, x=0.30, y=0.96, fontstyle='italic', fontsize=11)
        sns.despine()
        salvar(titulo)

    else:
        print('Erro: tipo de gráfico inválido.')
