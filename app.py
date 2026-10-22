import pickle
from pathlib import Path

import pandas as pd
import streamlit as st

from src.utils import preparar_cliente

st.set_page_config(page_title="Segmentação de Clientes 🛒", page_icon="🛒", layout="wide")
st.title("🛒 Segmentação de Clientes")
st.markdown("Preencha os dados do cliente na barra lateral e descubra a qual **segmento** ele pertence.")

CAMINHO_MODELO = Path(__file__).parent / "Model" / "pipeline_segmentacao.pkl"

# Descrição e ação de marketing de cada segmento
SEGMENTOS = {
    "Premium": {
        "emoji": "🥇",
        "descricao": "Maior renda e maior gasto. Compram por catálogo e na loja, quase não usam desconto e são os que mais aceitam campanhas.",
        "acao": "Público prioritário do novo produto: ofertas exclusivas e lançamentos, sem necessidade de desconto.",
    },
    "Fiéis de alto volume": {
        "emoji": "🍷",
        "descricao": "Renda alta, compram com frequência e têm o vinho como categoria preferida.",
        "acao": "Segundo público do lançamento: combos e programa de fidelidade.",
    },
    "Novos e ativos": {
        "emoji": "🌱",
        "descricao": "Clientes mais jovens e recentes, compraram há pouco tempo, gasto baixo e sensíveis a desconto.",
        "acao": "Campanhas digitais com desconto para aumentar o ticket médio.",
    },
    "Em risco de churn": {
        "emoji": "⚠️",
        "descricao": "Muito tempo sem comprar, gasto baixo, compram com desconto e quase não respondem a campanhas.",
        "acao": "Campanhas de reativação com cupons e produtos para a família.",
    },
}


### Carregamento do modelo
@st.cache_resource
def carregar_modelo(caminho):
    with open(caminho, "rb") as arquivo:
        return pickle.load(arquivo)


if not CAMINHO_MODELO.exists():
    st.error("Modelo não encontrado. Execute o notebook até a Fase 05 para gerar `Model/pipeline_segmentacao.pkl`.")
    st.stop()

modelo = carregar_modelo(CAMINHO_MODELO)

### Formulário com os dados do cliente
with st.sidebar:
    st.header("👤 Perfil")
    year_birth = st.number_input("Ano de nascimento", 1930, 2000, 1970)
    education = st.selectbox("Escolaridade", ["Basic", "2n Cycle", "Graduation", "Master", "PhD"], index=2)
    marital_status = st.selectbox("Estado civil", ["Single", "Together", "Married", "Divorced", "Widow"])
    income = st.number_input("Renda anual (US$)", 0, 200000, 50000, step=1000)
    kidhome = st.number_input("Crianças em casa", 0, 5, 0)
    teenhome = st.number_input("Adolescentes em casa", 0, 5, 0)
    lifetime = st.number_input("Meses como cliente", 0, 60, 15)
    recency = st.number_input("Dias desde a última compra", 0, 365, 30)

    st.header("🛍️ Gastos nos últimos 2 anos (US$)")
    mnt_wines = st.number_input("Vinhos", 0, 5000, 300)
    mnt_fruits = st.number_input("Frutas", 0, 5000, 25)
    mnt_meat = st.number_input("Carnes", 0, 5000, 150)
    mnt_fish = st.number_input("Peixes", 0, 5000, 35)
    mnt_sweet = st.number_input("Doces", 0, 5000, 25)
    mnt_gold = st.number_input("Ouro", 0, 5000, 40)

    st.header("🏬 Compras e campanhas")
    num_web = st.number_input("Compras pelo site", 0, 50, 4)
    num_catalog = st.number_input("Compras por catálogo", 0, 50, 2)
    num_store = st.number_input("Compras na loja", 0, 50, 6)
    num_deals = st.number_input("Compras com desconto", 0, 50, 2)
    num_visits = st.number_input("Visitas ao site no último mês", 0, 30, 5)
    accepted_cmp = st.slider("Campanhas aceitas (de 6)", 0, 6, 0)

dados = {
    "Year_Birth": year_birth, "Education": education, "Marital_Status": marital_status,
    "Income": income, "Kidhome": kidhome, "Teenhome": teenhome,
    "LifeTime": lifetime, "Recency": recency,
    "MntWines": mnt_wines, "MntFruits": mnt_fruits, "MntMeatProducts": mnt_meat,
    "MntFishProducts": mnt_fish, "MntSweetProducts": mnt_sweet, "MntGoldProds": mnt_gold,
    "NumWebPurchases": num_web, "NumCatalogPurchases": num_catalog, "NumStorePurchases": num_store,
    "NumDealsPurchases": num_deals, "NumWebVisitsMonth": num_visits, "AcceptedCmp": accepted_cmp,
}

### Previsão
if st.button("Identificar segmento", type="primary"):
    try:
        cliente = preparar_cliente(dados)
    except ValueError as erro:
        st.warning(str(erro))
        st.stop()

    cluster = modelo["pipeline"].predict(cliente)[0]
    segmento = modelo["segmentos"][cluster]
    info = SEGMENTOS[segmento]

    st.subheader(f"{info['emoji']} Segmento: {segmento}")
    st.markdown(f"**Perfil:** {info['descricao']}")
    st.success(f"**Ação recomendada:** {info['acao']}")

    # Comparação do cliente com a média do segmento
    perfil_medio = modelo["perfil_medio"].loc[segmento]
    comparacao = pd.DataFrame({
        "Cliente": cliente[perfil_medio.index].iloc[0],
        f"Média do segmento {segmento}": perfil_medio,
    }).round(1)
    comparacao.index = ["Renda anual", "Gasto total", "Total de compras", "Dias desde a última compra",
                        "Filhos em casa", "Campanhas aceitas"]
    st.markdown("#### Cliente x média do segmento")
    st.dataframe(comparacao, width="stretch")
