import streamlit as st
import pandas as pd
import re
import os
from pypdf import PdfReader

# Configuração do Banco de Dados Local
CSV_FILE = "historico_vinhedo.csv"

# Inicializa o arquivo se não existir
if not os.path.exists(CSV_FILE):
    df_init = pd.DataFrame(columns=["Data", "Local/Etapa", "Prova", "Atleta", "Categoria", "Tempo"])
    df_init.to_csv(CSV_FILE, index=False)

def carregar_dados():
    return pd.read_csv(CSV_FILE)

def padronizar_tempo(tempo_str):
    """Converte formatos UNAMI (01m37s87c) e FAP (1:38.55) em formato limpo para o Sheets"""
    tempo_str = str(tempo_str).strip().replace("c", "").replace("s", ".").replace("m", ":")
    # Remove zeros a esquerda desnecessários (00:32.06 -> 32.06)
    if tempo_str.startswith("00:"):
        tempo_str = tempo_str[3:]
    if tempo_str.startswith("0") and ":" in tempo_str:
        tempo_str = tempo_str[1:]
    return tempo_str

def processar_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    linhas_encontradas = []
    
    # Captura metadados básicos do topo do arquivo de natação
    data_prova = "Disponível no PDF"
    local_etapa = "Campeonato de Natação"
    prova_atual = "Não identificada"
    
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() + "\n"
        
    linhas = texto_completo.split("\n")
    
    for linha in lines:
        linha_upper = linha.upper()
        
        # Detecta mudança de prova no PDF
        if "PROVA" in linha_upper and "METROS" in linha_upper:
            prova_atual = linha.strip()
        if "DATA:" in linha_upper:
            match_data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
            if match_data: data_prova = match_data.group(1)
            
        # Filtra os atletas vinculados a Vinhedo
        if "VINHEDO" in linha_upper:
            # Limpeza e extração por Expressão Regular baseada nos layouts FAP/UNAMI
            partes = linha.split()
            # Localiza estruturas de tempo nas pontas da linha
            tempos = [p for partes in partes if re.match(r'^(\d+[:m]\d+[:s]\d+c?|\d+\.\d+|\d+s\d+c)$', p)]
            
            # Reconhecimento básico de nomes de atletas do time
            atleta = "Atleta Vinhedo"
            for nome_chave in ["CLAUDIA", "BRUNA", "HELENA", "HELOISA", "LARA", "TALITA", "TIAGO", "ALVARO", "CALEBE", "FABIUS", "RAFAEL", "MATIAS", "LUCIANO", "VOLKER"]:
                if nome_chave in linha_upper:
                    # Reconstrói o nome completo aproximado baseado no contexto da linha
                    atleta = [l for l in linha.split() if nome_chave in l.upper()][0] # Simplificado para o script
            
            tempo_final = tempos[0] if tempos else "S/T"
            tempo_final = padronizar_tempo(tempo_final)
            
            linhas_encontradas.append({
                "Data": data_prova,
                "Local/Etapa": local_etapa,
                "Prova": prova_atual,
                "Atleta": atleta,
                "Categoria": "Master",
                "Tempo": tempo_final
            })
            
    return pd.DataFrame(linhas_encontradas)

# --- INTERFACE DO STREAMLIT ---
st.set_page_config(page_title="SEL Vinhedo - Swim PRs", page_icon="🏊‍♂️", layout="wide")
st.title("🏊‍♂️ Painel de Controle de Tempos - SEL Vinhedo")

aba1, aba2, aba3 = st.tabs(["🔍 Pesquisar PRs de Atletas", "📤 Enviar Novo PDF", "🗄️ Histórico Geral"])

with aba1:
    st.subheader("Recordes Pessoais (Personal Records)")
    df_historico = carregar_dados()
    
    if not df_historico.empty:
        lista_atletas = sorted(df_historico["Atleta"].dropna().unique())
        atleta_sel = st.selectbox("Selecione o Atleta para checar as marcas:", lista_atletas)
        
        # Filtra dados do atleta e descarta cadastros sem tempos válidos (DQL, N/C, Ausente)
        df_atleta = df_historico[df_historico["Atleta"] == atleta_sel]
        df_validos = df_atleta[~df_atleta["Tempo"].isin(["DQL", "N/C", "Ausente", "S/T"])]
        
        # Calcula o melhor tempo (PR) agrupado por tipo de prova
        df_prs = df_validos.groupby("Prova")["Tempo"].min().reset_index()
        
        st.dataframe(df_prs, use_container_width=True, hide_index=True)
    else:
        st.info("O banco de dados ainda está vazio. Suba o histórico na Aba 2.")

with aba2:
    st.subheader("Adicionar Resultados de Campeonatos")
    st.write("Arraste o arquivo PDF gerado pela federação aqui. O sistema vai ler, extrair os tempos de Vinhedo e salvar automaticamente.")
    
    uploaded_file = st.file_uploader("Escolha o PDF do campeonato", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Processar e Salvar Dados"):
            with st.spinner("Processando informações..."):
                df_novos = processar_pdf(uploaded_file)
                if not df_novos.empty:
                    df_total = pd.concat([carregar_dados(), df_novos]).drop_duplicates()
                    df_total.to_csv(CSV_FILE, index=False)
                    st.success(f"Sucesso! {len(df_novos)} novos tempos adicionados ao histórico!")
                else:
                    st.warning("Nenhum atleta da SEL Vinhedo foi identificado neste PDF.")

with aba3:
    st.subheader("Histórico Completo Base de Dados")
    st.dataframe(carregar_dados(), use_container_width=True)
