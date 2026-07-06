import streamlit as st
import pandas as pd
import re
import os
from pypdf import PdfReader

# --- FUNÇÕES DE PADRONIZAÇÃO E CORREÇÃO DE ERROS ---

def normalizar_nome_atleta(nome):
    """ Corrige acentuações, espaços e truncamentos dos PDFs """
    if not isinstance(nome, str):
        return "Atleta Desconhecido"
    
    # Remove espaços duplos e padroniza para maiúsculas
    nome = " ".join(nome.split()).upper()
    
    # Substituições diretas para unificar nomes com acentos ou truncados
    if "HELOISA" in nome or "HELOÍSA" in nome:
        return "HELOÍSA DE SOUSA EVANGELISTA"
    if "HELENA" in nome and "KOBAYASHI" in nome:
        return "HELENA KIYOKA KOBAYASHI NABEIRO"
    if "BRUNA" in nome and "VICENTE" in nome:
        return "BRUNA LIMA VICENTE"
    if "ANA REGINA" in nome or "LIMONGI" in nome:
        return "ANA REGINA OLIVAN LIMONGI"
    if "TALITA" in nome and "BARBOSA" in nome:
        return "TALITA CLIOGIA BARBOSA"
    if "LARA" in nome and "TONIN" in nome:
        return "LARA FERREIRA DE SOUZA TONIN"
    if "TIAGO" in nome and "BERNAL" in nome:
        return "TIAGO BERNAL"
    if "ALVARO" in nome or "LOUZADA" in nome:
        return "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR"
    if "CALEBE" in nome and "RIBEIRO" in nome:
        return "CALEBE RAMOS RIBEIRO"
    if "FABIUS" in nome or "PALARO" in nome:
        return "FABIUS LUIZ PALARO"
    if "RAFAEL" in nome and "HIROSHI" in nome:
        return "RAFAEL HIROSHI BRAZ DA SILVA"
    if "RAFAEL" in nome and "MELLO" in nome:
        return "RAFAEL MELLO"
    if "MATIAS" in nome and "KOLBE" in nome:
        return "MATIAS KOLBE"
    if "LUCIANO" in nome and "GOBI" in nome:
        return "LUCIANO DIAS GOBI"
    if "VOLKER" in nome and "PENK" in nome:
        return "VOLKER PENK"
    if "MURILO" in nome and "SANTOS" in nome:
        return "MURILO SANTOS"
        
    return nome

def normalizar_prova(prova_str):
    """ Remove prefixos de numeração (ex: '13ª Prova - ') e limpa o estilo """
    if not isinstance(prova_str, str):
        return "Estilo Não Identificado"
    
    # Remove termos como '1ª Prova - ', 'Prova 3 - ', etc.
    prova_limpa = re.sub(r'^(\d+[\s\S]?\s*(PROVA|Prova)\s*[-–:]*)\s*', '', prova_str)
    
    # Padronizações comuns de escrita
    prova_limpa = " ".join(prova_limpa.split())
    prova_limpa = prova_limpa.replace("Feminino", "Fem").replace("Masculino", "Masc")
    
    return prova_limpa.strip()

def tempo_para_segundos(tempo_str):
    """ Converte strings de tempo (MM:SS.CC ou SS.CC) em segundos (float) para cálculo preciso de PR """
    try:
        tempo_str = str(tempo_str).strip()
        if ":" in tempo_str:
            minutos, resto = tempo_str.split(":")
            segundos, centesimos = resto.split(".")
            return int(minutos) * 60 + int(segundos) + int(centesimos) / 100
        else:
            segundos, centesimos = tempo_str.split(".")
            return int(segundos) + int(centesimos) / 100
    except:
        return float('inf') # Retorna infinito para tempos inválidos (DQL, N/C), ignorando-os no mínimo

def segundos_para_tempo(segundos_float):
    """ Converte float de segundos de volta para o formato padrão de natação MM:SS.CC """
    if segundos_float == float('inf'):
        return "S/T"
    minutos = int(segundos_float // 60)
    segundos = int(segundos_float % 60)
    centesimos = int(round((segundos_float % 1) * 100))
    
    if minutos > 0:
        return f"{minutos}:{segundos:02d}.{centesimos:02d}"
    else:
        return f"{segundos}.{centesimos:02d}"

def padronizar_tempo_string(tempo_str):
    """ Transforma formatos UNAMI (01m37s87c) e FAP (1:38.55) em string limpa padrão """
    tempo_str = str(tempo_str).lower().strip().replace("c", "").replace("s", ".").replace("m", ":")
    tempo_str = tempo_str.replace(",", ".")
    if tempo_str.startswith("00:"):
        tempo_str = tempo_str[3:]
    return tempo_str

# --- PROCESSAMENTO DO PDF ---

def processar_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    linhas_encontradas = []
    
    data_prova = "Disponível no PDF"
    local_etapa = "Campeonato de Natação"
    prova_atual = "Não identificada"
    
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() + "\n"
        
    linhas = texto_completo.split("\n")
    
    for linha in linhas:
        linha_upper = linha.upper()
        
        if "PROVA" in linha_upper and "METROS" in linha_upper:
            prova_atual = normalizar_prova(linha)
        if "DATA:" in linha_upper:
            match_data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
            if match_data: data_prova = match_data.group(1)
            
        if "VINHEDO" in linha_upper:
            partes = linha.split()
            tempos = [p for p in partes if re.match(r'^(\d+[:m]\d+[:s]\d+c?|\d+[\.,]\d+|\d+s\d+c)$', p)]
            
            atleta_bruto = "Atleta Vinhedo"
            for nome_chave in ["CLAUDIA", "BRUNA", "HELENA", "HELOISA", "LARA", "TALITA", "TIAGO", "ALVARO", "CALEBE", "FABIUS", "RAFAEL", "MATIAS", "LUCIANO", "VOLKER", "MURILO"]:
                if nome_chave in linha_upper:
                    atleta_bruto = linha.split("VINHEDO")[-1].strip() if "VINHEDO" in linha_upper else linha
            
            atleta_final = normalizar_nome_atleta(atleta_bruto)
            tempo_final = tempos[0] if tempos else "S/T"
            tempo_final = padronizar_tempo_string(tempo_final)
            
            if atleta_final != "ATLETA DESCONHECIDO":
                linhas_encontradas.append({
                    "Data": data_prova,
                    "Local/Etapa": local_etapa,
                    "Prova": prova_atual,
                    "Atleta": atleta_final,
                    "Categoria": "Master",
                    "Tempo": tempo_final
                })
            
    return pd.DataFrame(linhas_encontradas)

# --- INTERFACE STREAMLIT ---

CSV_FILE = "historico_vinhedo.csv"

st.set_page_config(page_title="SEL Vinhedo - Swim PRs", page_icon="🏊‍♂️", layout="wide")
st.title("🏊‍♂️ Painel de Controle de Tempos - SEL Vinhedo")

aba1, aba2, aba3 = st.tabs(["🔍 Pesquisar PRs de Atletas", "📤 Enviar Novo PDF", "🗄️ Histórico Geral"])

# Carrega e higieniza a base de dados ao abrir o app
if os.path.exists(CSV_FILE):
    df_historico = pd.read_csv(CSV_FILE)
    df_historico["Atleta"] = df_historico["Atleta"].apply(normalizar_nome_atleta)
    df_historico["Prova"] = df_historico["Prova"].apply(normalizar_prova)
    df_historico["Tempo"] = df_historico["Tempo"].apply(padronizar_tempo_string)
else:
    df_historico = pd.DataFrame(columns=["Data", "Local/Etapa", "Prova", "Atleta", "Categoria", "Tempo"])

with aba1:
    st.subheader("Recordes Pessoais Históricos (Personal Records)")
    
    if not df_historico.empty:
        lista_atletas = sorted(df_historico["Atleta"].dropna().unique())
        atleta_sel = st.selectbox("Selecione o Atleta para checar as marcas:", lista_atletas)
        
        # Filtra histórico do atleta selecionado
        df_atleta = df_historico[df_historico["Atleta"] == atleta_sel]
        
        # Filtra apenas registros com tempos válidos para cálculo matemático de PR
        df_validos = df_atleta[~df_atleta["Tempo"].isin(["dql", "n/c", "ausente", "s/t"])]
        
        # Converte tempos para segundos para aplicar a matemática do menor valor real
        df_validos["Segundos"] = df_validos["Tempo"].apply(tempo_para_segundos)
        
        # Agrupa por Prova limpa e encontra os menores segundos
        df_agrupado = df_validos.groupby("Prova")["Segundos"].min().reset_index()
        
        # Converte os segundos de volta para o formato de piscina legível (MM:SS.CC)
        df_agrupado["Melhor Tempo (PR)"] = df_agrupado["Segundos"].apply(segundos_para_tempo)
        df_final_prs = df_agrupado[["Prova", "Melhor Tempo (PR)"]]
        
        st.dataframe(df_final_prs, use_container_width=True, hide_index=True)
    else:
        st.info("O histórico está vazio. Faça o upload de arquivos na segunda aba.")

with aba2:
    st.subheader("Adicionar Resultados de Campeonatos")
    uploaded_file = st.file_uploader("Escolha o PDF do campeonato", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Processar e Salvar Dados"):
            with st.spinner("Processando e higienizando informações..."):
                df_novos = processar_pdf(uploaded_file)
                if not df_novos.empty:
                    df_total = pd.concat([df_historico, df_novos]).drop_duplicates(subset=["Data", "Prova", "Atleta", "Tempo"])
                    df_total.to_csv(CSV_FILE, index=False)
                    st.success(f"Sucesso! {len(df_novos)} novos tempos processados e unificados no banco de dados!")
                    st.rerun()
                else:
                    st.warning("Nenhum atleta da SEL Vinhedo foi localizado nas tabelas deste PDF.")

with aba3:
    st.subheader("Base de Dados Histórica Consolidada")
    st.dataframe(df_historico, use_container_width=True, hide_index=True)
