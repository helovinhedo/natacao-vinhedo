import streamlit as st
import pandas as pd
import re
import os
import itertools
from pypdf import PdfReader

# --- DICIONÁRIOS DE UNIFICAÇÃO (BLINDAGEM DE DADOS) ---

DIC_ATLETAS = {
    "CLAUDIA": "CLAUDIA COLAMARINO",
    "BRUNA": "BRUNA LIMA VICENTE",
    "ÁLVARO": "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR",
    "ALVARO": "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR",
    "HIROSHI": "RAFAEL HIROSHI BRAZ DA SILVA",
    "HELOISA": "HELOÍSA DE SOUSA EVANGELISTA",
    "HELOÍSA": "HELOÍSA DE SOUSA EVANGELISTA",
    "TALITA": "TALITA CLIOGIA BARBOSA",
    "CALEBE": "CALEBE RAMOS RIBEIRO",
    "MELLO": "RAFAEL MELLO",
    "REGINA": "ANA REGINA OLIVAN LIMONGI",
    "LARA": "LARA FERREIRA DE SOUZA TONIN",
    "FABIUS": "FABIUS LUIZ PALARO",
    "HELENA": "HELENA KIYOKA KOBAYASHI NABEIRO",
    "TIAGO": "TIAGO BERNAL"
}

# Mapeamento de idades base por categoria para cálculo de revezamento master
IDADES_BASE_ATLETAS = {
    "CLAUDIA COLAMARINO": 55,
    "BRUNA LIMA VICENTE": 35,
    "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR": 40,
    "RAFAEL HIROSHI BRAZ DA SILVA": 35,
    "HELOÍSA DE SOUSA EVANGELISTA": 35,
    "TALITA CLIOGIA BARBOSA": 30,
    "CALEBE RAMOS RIBEIRO": 35,
    "RAFAEL MELLO": 35,
    "ANA REGINA OLIVAN LIMONGI": 40,
    "LARA FERREIRA DE SOUZA TONIN": 35,
    "FABIUS LUIZ PALARO": 50,
    "HELENA KIYOKA KOBAYASHI NABEIRO": 45,
    "TIAGO BERNAL": 45
}

def normalizar_nome_atleta(nome_bruto):
    if not isinstance(nome_bruto, str): return "Atleta Desconhecido"
    nome_upper = " ".join(nome_bruto.split()).upper()
    for chave, nome_oficial in DIC_ATLETAS.items():
        if chave in nome_upper: return nome_oficial
    return "Atleta Desconhecido"

def normalizar_prova(prova_str):
    """ DICIONÁRIO DE PROVAS INTELIGENTE: Identifica distância, estilo e gênero de qualquer string """
    if not isinstance(prova_str, str): return "Estilo Não Identificado"
    p = prova_str.upper()
    
    distancia = ""
    for d in ["50", "100", "200", "400", "800", "1500"]:
        if d in p: 
            distancia = f"{d}m"
            break
            
    estilo = ""
    if "LIVRE" in p or "CRAWL" in p: estilo = "Livre"
    elif "BORBOLETA" in p or "GOLFINHO" in p: estilo = "Borboleta"
    elif "COSTAS" in p: estilo = "Costas"
    elif "PEITO" in p: estilo = "Peito"
    elif "MEDLEY" in p or "ESTILOS" in p: estilo = "Medley"
    
    genero = ""
    if "FEM" in p or "MOÇAS" in p or "MULHERES" in p: genero = "Fem"
    elif "MASC" in p or "RAPAZES" in p or "HOMENS" in p: genero = "Masc"
    elif "MISTO" in p: genero = "Misto"
    
    if distancia and estilo and genero: return f"{distancia} {estilo} {genero}"
    if distancia and estilo: return f"{distancia} {estilo}"
    return " ".join(prova_str.split()).title()

def padronizar_tempo_string(tempo_str):
    t_clean = str(tempo_str).lower().strip().replace("c", "").replace("s", ".").replace("m", ":")
    t_clean = t_clean.replace(",", ".")
    if t_clean.startswith("00:"): t_clean = t_clean[3:]
    return t_clean

def tempo_para_segundos(tempo_str):
    try:
        t_str = str(tempo_str).strip()
        if ":" in t_str:
            minutos, resto = t_str.split(":")
            segundos, centesimos = resto.split(".")
            return float(minutos) * 60 + float(segundos) + float(centesimos) / 100
        else:
            segundos, centesimos = t_str.split(".")
            val = float(segundos) + float(centesimos) / 100
            return val if val > 0 else None
    except:
        return None

def segundos_para_tempo(segundos_float):
    if segundos_float == float('inf') or segundos_float is None: return "S/T"
    minutos = int(segundos_float // 60)
    segundos = int(segundos_float % 60)
    centesimos = int(round((segundos_float % 1) * 100))
    if minutos > 0: return f"{minutos}:{segundos:02d}.{centesimos:02d}"
    return f"{segundos:02d}.{centesimos:02d}"

# --- TRATAMENTO DE REVEZAMENTO ---

def obter_pr_revezamento(df, atleta, estilo_procurado):
    df_atleta = df[(df["Atleta"] == atleta) & (df["Tempo"].notna())]
    df_prova = df_atleta[df_atleta["Prova"].str.contains(estilo_procurado, case=False)]
    
    df_prova = df_prova.copy()
    df_prova["Segundos"] = df_prova["Tempo"].apply(tempo_para_segundos)
    df_validos = df_prova[df_prova["Segundos"].notna()]
    
    if df_validos.empty: return float('inf'), "S/T"
    idx_min = df_validos["Segundos"].idxmin()
    return df_validos.loc[idx_min, "Segundos"], df_validos.loc[idx_min, "Tempo"]

# --- PROCESSAMENTO DO PDF ---

def processar_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    linhas_encontradas = []
    data_prova, local_etapa, prova_atual = "Disponível no PDF", "Campeonato de Natação", "Não identificada"
    
    texto_completo = ""
    for page in reader.pages: texto_completo += page.extract_text() + "\n"
    linhas = texto_completo.split("\n")
    
    for linha in linhas:
        linha_upper = linha.upper()
        if "PROVA" in linha_upper and "METROS" in linha_upper: prova_atual = normalizar_prova(linha)
        if "DATA:" in linha_upper:
            match_data = re.search(r'(\d{2}/\d{2}/\d{4})', linha)
            if match_data: data_prova = match_data.group(1)
            
        if "VINHEDO" in linha_upper or "VINHEDE" in linha_upper:
            partes = linha.split()
            tempos = [p for p in partes if re.match(r'^(\d+[:m]\d+[:s]\d+c?|\d+[\.,]\d+|\d+s\d+c)$', p)]
            tempo_bruto = tempos[0] if tempos else "S/T"
            tempo_final = padronizar_tempo_string(tempo_bruto)
            atleta_final = normalizar_nome_atleta(linha)
            
            if atleta_final != "Atleta Desconhecido":
                linhas_encontradas.append({
                    "Data": data_prova, "Local/Etapa": local_etapa, "Prova": prova_atual,
                    "Atleta": atleta_final, "Categoria": "Master", "Tempo": tempo_final
                })
    return pd.DataFrame(linhas_encontradas)

# --- CONFIGURAÇÃO DA INTERFACE ---

CSV_FILE = "historico_vinhedo.csv"
st.set_page_config(page_title="SEL Vinhedo - Swim Analytics", page_icon="🏊‍♂️", layout="wide")
st.title("🏊‍♂️ Painel Avançado de Controle de Tempos - SEL Vinhedo")

if os.path.exists(CSV_FILE):
    df_historico = pd.read_csv(CSV_FILE)
    df_historico["Atleta"] = df_historico["Atleta"].apply(normalizar_nome_atleta)
    df_historico["Prova"] = df_historico["Prova"].apply(normalizar_prova)
    df_historico["Tempo"] = df_historico["Tempo"].apply(padronizar_tempo_string)
    df_historico = df_historico[df_historico["Atleta"] != "Atleta Desconhecido"]
else:
    df_historico = pd.DataFrame(columns=["Data", "Local/Etapa", "Prova", "Atleta", "Categoria", "Tempo"])

menu_abas = ["🔍 Consulta por Atleta", "🏊‍♂️ Simulador de Revezamentos", "📥 Alimentar Sistema", "🗄️ Base Geral CSV"]
aba1, aba2, aba3, aba4 = st.tabs(menu_abas)

with aba1:
    st.subheader("Ficha de Rendimento Individual")
    if not df_historico.empty:
        lista_atletas = sorted(df_historico["Atleta"].unique())
        atleta_sel = st.selectbox("Selecione o Atleta:", lista_atletas, key="busca_atleta")
        
        df_atleta = df_historico[df_historico["Atleta"] == atleta_sel].copy()
        df_atleta["Segundos"] = df_atleta["Tempo"].apply(tempo_para_segundos)
        df_validos = df_atleta[df_atleta["Segundos"].notna()].copy()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🥇 Recordes Pessoais Atuais (PRs)")
            if not df_validos.empty:
                idx_melhores = df_validos.groupby("Prova")["Segundos"].idxmin()
                df_prs = df_validos.loc[idx_melhores, ["Prova", "Tempo", "Data", "Local/Etapa"]].rename(columns={"Tempo": "Tempo Recorde"})
                st.dataframe(df_prs, use_container_width=True, hide_index=True)
            else:
                st.warning("Sem tempos válidos calculados.")
                
        with col2:
            st.markdown("#### 📅 Histórico Cronológico de Provas")
            try:
                df_atleta["Data_Formatada"] = pd.to_datetime(df_atleta["Data"], format="%d/%m/%Y", errors="coerce")
                df_cronologico = df_atleta.sort_values(by="Data_Formatada", ascending=False)[["Data", "Local/Etapa", "Prova", "Tempo"]]
                st.dataframe(df_cronologico, use_container_width=True, hide_index=True)
            except:
                st.dataframe(df_atleta[["Data", "Local/Etapa", "Prova", "Tempo"]], use_container_width=True, hide_index=True)

with aba2:
    st.subheader("🚀 Simulador Estatístico de Revezamento Master (4x50m)")
    if not df_historico.empty:
        tipo_rev = st.radio("Estilo do Revezamento:", ["4x50m Livre", "4x50m Medley"], horizontal=True)
        tipo_gen = st.radio("Gênero do Revezamento:", ["Masculino", "Feminino", "Misto"], horizontal=True)
        
        lista_completa = sorted(list(IDADES_BASE_ATLETAS.keys()))
        atletas_escolhidos = st.multiselect("Selecione EXATAMENTE 4 atletas para montar o quarteto:", lista_completa)
        
        if len(atletas_escolhidos) == 4:
            st.markdown("---")
            # Validação de gênero se não for misto
            # Cálculo de Categoria
            soma_idades = sum(IDADES_BASE_ATLETAS[a] for a in atletas_escolhidos)
            cat_rev = "320+" if soma_idades >= 320 else ("280+" if soma_idades >= 280 else ("240+" if soma_idades >= 240 else ("200+" if soma_idades >= 200 else ("160+" if soma_idades >= 160 else ("120+" if soma_idades >= 120 else "80+")))))
            
            st.metric(label="Categoria Oficial do Revezamento", value=f"Classe {cat_rev}", delta=f"Soma das Idades Base: {soma_idades} Anos")
            
            if tipo_rev == "4x50m Livre":
                st.markdown("#### Formação Sugerida (Ordem de Entrada Livre)")
                tempo_total_seg = 0.0
                linhas_simulacao = []
                for a in atletas_escolhidos:
                    seg, t_str = obter_pr_revezamento(df_historico, a, "50m Livre")
                    tempo_total_seg += seg if seg != float('inf') else 30.0 # penalidade se não tiver tempo
                    linhas_simulacao.append({"Atleta": a, "Estilo/Nado": "50m Livre", "Melhor Tempo Individual": t_str})
                st.table(pd.DataFrame(linhas_simulacao))
                st.subheader(f"⏱️ Tempo Total Estimado do Revezamento: {segundos_para_tempo(tempo_total_seg)}")
                
            elif tipo_rev == "4x50m Medley":
                st.markdown("#### 🧠 Otimização Algorítmica de Formação Medley (Mais Rápida Possível)")
                estilos_medley = ["50m Costas", "50m Peito", "50m Borboleta", "50m Livre"]
                
                melhor_tempo_medley = float('inf')
                melhor_combinacao = None
                
                # Testa todas as 24 permutações de nado possíveis entre os 4 nadadores escolhidos
                for perm in itertools.permutations(atletas_escolhidos):
                    t_costas, _ = obter_pr_revezamento(df_historico, perm[0], "50m Costas")
                    t_peito, _ = obter_pr_revezamento(df_historico, perm[1], "50m Peito")
                    t_borb, _ = obter_pr_revezamento(df_historico, perm[2], "50m Borboleta")
                    t_livre, _ = obter_pr_revezamento(df_historico, perm[3], "50m Livre")
                    
                    soma_perm = t_costas + t_peito + t_borb + t_livre
                    if soma_perm < melhor_tempo_medley:
                        melhor_tempo_medley = soma_perm
                        melhor_combinacao = perm
                
                if melhor_tempo_medley != float('inf'):
                    linhas_medley = []
                    for i, estilo_nome in enumerate(estilos_medley):
                        _, t_str = obter_pr_revezamento(df_historico, melhor_combinacao[i], estilo_nome)
                        linhas_medley.append({"Ordem": f"{i+1}º Nadador", "Atleta": melhor_combinacao[i], "Estilo": estilo_nome.split()[-1], "Tempo Estimado": t_str})
                    st.table(pd.DataFrame(linhas_medley))
                    st.subheader(f"⏱️ Tempo Mínimo Otimizado do Revezamento Medley: {segundos_para_tempo(melhor_tempo_medley)}")
                else:
                    st.error("Não foi possível calcular. Um ou mais atletas selecionados não possuem tempos cadastrados em estilos de Medley.")
        else:
            st.info("Por favor, selecione exatamente 4 atletas para ativar a simulação de tempos.")

with aba3:
    st.subheader("Entrada de Dados e Atualização do Sistema")
    col_pdf, col_manual = st.columns(2)
    
    with col_pdf:
        st.markdown("### 📤 Upload de Relatórios PDF")
        uploaded_file = st.file_uploader("Arraste o PDF oficial da competição aqui:", type=["pdf"])
        if uploaded_file is not None:
            if st.button("Processar e Fundir PDF"):
                with st.spinner("Extraindo e Higienizando registros..."):
                    df_novos = processar_pdf(uploaded_file)
                    if not df_novos.empty:
                        df_total = pd.concat([df_historico, df_novos]).drop_duplicates(subset=["Data", "Prova", "Atleta", "Tempo"])
                        df_total.to_csv(CSV_FILE, index=False)
                        st.success(f"Sucesso! {len(df_novos)} novos tempos unificados na base!")
                        st.rerun()
                    else:
                        st.warning("Nenhum atleta de Vinhedo localizado neste documento.")
                        
    with col_manual:
        st.markdown("### ✍️ Lançamento Manual (Treinos / Cronometragem de Borda)")
        lista_atletas_v = sorted(list(IDADES_BASE_ATLETAS.keys()))
        atleta_m = st.selectbox("Selecione o Atleta:", lista_atletas_v)
        prova_m = st.selectbox("Estilo/Distância da Prova:", [
            "50m Livre Masc", "50m Livre Fem", "50m Peito Masc", "50m Peito Fem",
            "50m Costas Masc", "50m Costas Fem", "50m Borboleta Masc", "50m Borboleta Fem",
            "100m Livre Masc", "100m Livre Fem", "100m Peito Masc", "100m Peito Fem",
            "100m Costas Masc", "100m Costas Fem", "100m Borboleta Masc", "100m Borboleta Fem",
            "100m Medley Masc", "100m Medley Fem", "200m Livre Masc", "200m Livre Fem",
            "400m Livre Masc", "400m Livre Fem"
        ])
        data_m = st.date_input("Data da Coleta:")
        local_m = st.text_input("Etapa/Descrição do Local:", value="Treino SEL Vinhedo")
        tempo_m = st.text_input("Tempo Registrado (ex: 28.54 ou 1:04.25):", placeholder="MM:SS.CC ou SS.CC")
        
        if st.button("Gravar Tempo Manual"):
            if tempo_m and data_m:
                t_padrao = padronizar_tempo_string(tempo_m)
                nova_linha = pd.DataFrame([{
                    "Data": data_m.strftime("%d/%m/%Y"), "Local/Etapa": local_m, "Prova": normalizar_prova(prova_m),
                    "Atleta": atleta_m, "Categoria": "Master", "Tempo": t_padrao
                }])
                df_total = pd.concat([df_historico, nova_linha]).drop_duplicates()
                df_total.to_csv(CSV_FILE, index=False)
                st.success("Tempo de treino adicionado com sucesso!")
                st.rerun()

with aba4:
    st.subheader("Visualização Bruta do Histórico Permanente (CSV)")
    st.dataframe(df_historico, use_container_width=True, hide_index=True)
