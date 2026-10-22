"""Funções de apoio usadas no notebook e no app Streamlit."""
import pandas as pd

# Pesos de negócio aplicados após a normalização (quanto maior, mais a variável influencia os grupos)
PESOS = {
    'TotalAmountSpent': 8,   # dinheiro gasto pelo cliente: a variável mais importante
    'TotalPurchases': 6,     # número total de compras
    'Recency': 4,            # dias desde a última compra
    'NumWebVisitsMonth': 4,  # visitas ao site no último mês
    'Income': 4,             # renda anual
    'LifeTime': 4,           # tempo de cadastro na plataforma (meses)
    'Year_Birth': 2,         # idade do cliente
    'ChildrenHome': 2,       # filhos em casa
    'Education': 2,          # escolaridade
}

# Colunas (e ordem) usadas no treinamento do modelo
COLUNAS_MODELO = [
    'Year_Birth', 'Education', 'Income', 'Recency', 'ChildrenHome', 'LifeTime',
    'MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts', 'MntGoldProds',
    'TotalAmountSpent', 'AcceptedCmp',
    'NumWebPurchases', 'NumCatalogPurchases', 'NumStorePurchases', 'NumDealsPurchases',
    'NumWebVisitsMonth', 'TotalPurchases',
    'Marital_Status_Divorced', 'Marital_Status_Single', 'Marital_Status_Together', 'Marital_Status_Widow',
]

# Escolaridade é ordinal: o número respeita a hierarquia
EDUCACAO = {'Basic': 0, '2n Cycle': 1, 'Graduation': 2, 'Master': 3, 'PhD': 4}

# Agrupamento do estado civil feito no Feature Engineering
ESTADO_CIVIL = {'Married': 'Together', 'Alone': 'Single', 'YOLO': 'Single'}

PRODUTOS = ['MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']
CANAIS = ['NumWebPurchases', 'NumCatalogPurchases', 'NumStorePurchases']


def show_null(df):
    """Quantidade e % de nulos + tipo de cada coluna."""
    null_data = pd.concat([df.isnull().sum(axis=0),
                           df.isnull().sum(axis=0) / len(df),
                           df.dtypes],
                          axis=1)
    null_data.columns = ['QTD', '% null', 'Type']
    return null_data.sort_values(by='% null', ascending=False)


def scaler(df):
    """Normalização Min-Max: deixa todas as colunas entre 0 e 1."""
    df2 = df.copy()
    for column in df2:
        minimo = df2[column].min()
        maximo = df2[column].max()
        df2[column] = (df[column] - minimo) / (maximo - minimo)
    return df2


def aplicar_pesos(X, pesos=PESOS):
    """Multiplica as colunas normalizadas pelos pesos de negócio."""
    X = X.copy()
    for coluna, peso in pesos.items():
        X[coluna] = peso * X[coluna]
    return X


def preparar_cliente(dados):
    """Aplica o mesmo Feature Engineering do notebook a um cliente com valores brutos.

    `dados` é um dicionário com as colunas originais da base (Year_Birth, Education, Marital_Status,
    Income, Kidhome, Teenhome, LifeTime, Recency, Mnt*, Num*, AcceptedCmp).
    """
    cliente = dict(dados)

    cliente['Education'] = EDUCACAO[cliente['Education']]
    cliente['ChildrenHome'] = cliente.pop('Kidhome') + cliente.pop('Teenhome')

    # Quanto gasta e no que gasta (% do gasto total)
    cliente['TotalAmountSpent'] = sum(cliente[p] for p in PRODUTOS)
    if cliente['TotalAmountSpent'] <= 0:
        raise ValueError('O gasto total precisa ser maior que zero.')
    for p in PRODUTOS:
        cliente[p] = cliente[p] / cliente['TotalAmountSpent']

    # Quanto compra e onde compra (% do total de compras)
    cliente['TotalPurchases'] = sum(cliente[c] for c in CANAIS)
    if cliente['TotalPurchases'] <= 0:
        raise ValueError('O total de compras precisa ser maior que zero.')
    for c in CANAIS + ['NumDealsPurchases']:
        cliente[c] = cliente[c] / cliente['TotalPurchases']

    # Estado civil vira colunas 0/1 (One-Hot Encoding)
    estado_civil = cliente.pop('Marital_Status')
    estado_civil = ESTADO_CIVIL.get(estado_civil, estado_civil)
    for categoria in ['Divorced', 'Single', 'Together', 'Widow']:
        cliente[f'Marital_Status_{categoria}'] = int(estado_civil == categoria)

    return pd.DataFrame([cliente])[COLUNAS_MODELO]
