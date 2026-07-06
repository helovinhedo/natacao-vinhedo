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
    "TIAGO": "TIAGO BERNAL",
    "VOLKER": "VOLKER PENK",
    "MURILO": "MURILO SANTOS",
    "LUCIANO": "LUCIANO DIAS GOBI",
    "MATIAS": "MATIAS KOLBE",
    "EDUARDO": "EDUARDO TREVISAN GONCALVES",
    "MARIANE": "MARIANE DE MORAES QUIRINO",
    "LARISSA": "LARISSA LIMA SOATO"
}

# Idades base dos atletas para cálculo automático de categoria de revezamento
IDADES_BASE_ATLETAS = {
    "CLAUDIA COLAMARINO": 55, "BRUNA LIMA VICENTE": 35, "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR": 40,
    "RAFAEL HIROSHI BRAZ DA SILVA": 35, "HELOÍSA DE SOUSA EVANGELISTA": 35, "TALITA CLIOGIA BARBOSA": 30,
    "CALEBE RAMOS RIBEIRO": 35, "RAFAEL MELLO": 35, "ANA REGINA OLIVAN LIMONGI": 40,
    "LARA FERREIRA DE SOUZA TONIN": 35, "FABIUS LUIZ PALARO": 50, "HELENA KIYOKA KOBAYASHI NABEIRO": 45,
    "TIAGO BERNAL": 45, "VOLKER PENK": 55, "MURILO SANTOS": 20, "LUCIANO DIAS GOBI": 50,
    "EDUARDO TREVISAN GONCALVES": 45, "MATIAS KOLBE": 40, "MARIANE DE MORAES QUIRINO": 30,
    "LARISSA LIMA SOATO": 25
}

# --- FUNÇÕES DE PADRONIZAÇÃO E LIMPEZA DE DADOS ---

def normalizar_nome_atleta(nome_bruto):
    if not isinstance(nome_bruto, str): return "Atleta Desconhecido"
    nome_upper = " ".join(nome_bruto.split()).upper()
    for chave, nome_oficial in DIC_ATLETAS.items():
        if chave in nome_upper: return nome_oficial
    return "Atleta Desconhecido"

def normalizar_prova(prova_str):
    """ Dicionário de Provas Inteligente: Unifica escritas FAP/UNAMI por estilo """
    if not isinstance(prova_str, str): return "Estilo Não Identificado"
    p = prova_str.upper()
    
    distancia = ""
    for d in ["25", "50", "100", "200", "400", "800", "1500"]:
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
    elif "MASC" in p or "HOMEN" in p or "HOMENS" in p: genero = "Masc"
    elif "MISTO" in p: genero = "Misto"
    
    if distancia and estilo and genero:
        return f"{distancia} {estilo} {genero}"
    elif distancia and estilo:
        return f"{distancia} {estilo}"
    return " ".join(prova_str.split())

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
    if centesimos >= 100:
        segundos += 1
        centesimos -= 100
    if minutos > 0: return f"{minutos}:{segundos:02d}.{centesimos:02d}"
    return f"{segundos:02d}.{centesimos:02d}"

def obter_pr_revezamento(df, atleta, estilo_procurado):
    df_atleta = df[(df["Atleta"] == atleta) & (df["Tempo"].notna())]
    df_prova = df_atleta[df_atleta["Prova"].str.contains(estilo_procurado, case=False)]
    df_prova = df_prova.copy()
    df_prova["Segundos"] = df_prova["Tempo"].apply(tempo_para_segundos)
    df_validos = df_prova[df_prova["Segundos"].notna()]
    if df_validos.empty: return float('inf'), "S/T"
    idx_min = df_validos["Segundos"].idxmin()
    return df_validos.loc[idx_min, "Segundos"], df_validos.loc[idx_min, "Tempo"]

# --- CAPTURA AVANÇADA DE DADOS DO PDF ---

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
    
    # Varredura inteligente de cabeçalho com aspas duplas corrigidas para evitar o erro do screenshot
    for l in linhas[:60]:
        l_clean = re.sub(r"\", "", l).strip()
        l_up = l_clean.upper()
        if any(k in l_up for k in ["CAMPEONATO PAULISTA", "COPA NATAÇÃO", "COPA NATAÇAO", "TROFÉU", "TROFEU", "TORNEIO"]):
            if not any(x in l_up for x in ["RESULTADOS", "BALIZAMENTO", "PROVA"]):
                local_etapa = l_clean
        match_d = re.search(r"(\d{2}/\d{2}/\d{4})", l)
        if match_d:
            data_prova = match_d.group(1)

    # Varredura de tabelas e linhas de atletas
    for idx, linha in enumerate(linhas):
        linha_upper = linha.upper()
        
        if "PROVA" in inline_p = linha_upper and any(w in linha_upper for w in ["METROS", "LIVRE", "BORBOLETA", "PEITO", "COSTAS", "MEDLEY"]):
            prova_atual = normalizar_prova(linha)
        elif re.match(r"^PROVA\s+\d+", linha_upper.strip()):
            partes_p = [linha]
            for j in range(1, 4):
                if idx + j < len(linhas):
                    next_l = linhas[idx+j].strip()
                    if any(w in next_l.upper() for w in ["LIVRE", "BORBOLETA", "PEITO", "COSTAS", "MEDLEY", "FEMININO", "MASCULINO", "MISTO", "FEM", "MASC"]):
                        partes_p.append(next_l)
            prova_atual = normalizar_prova(" ".join(partes_p))
            
        if "VINHEDO" in linha_upper or "VINHEDE" in linha_upper:
            linha_limpa = linha.replace('"', '').replace(';', ' ').strip()
            atleta_final = normalizar_nome_atleta(linha_limpa)
            
            if atleta_final == "Atleta Desconhecido":
                continue
                
            if any(w in linha_upper for w in ["AUSENTE", "N/C", "Ñ NADOU", "DESCLA", "DQL"]):
                tempo_final = "DQL" if ("DQL" in linha_upper or "DESCLA" in linha_upper) else "Ausente"
            else:
                match_minutos = re.findall(r"\b\d{1,2}[m:]\d{2}[s\.]\d{2}c?\b", linha_limpa, re.IGNORECASE)
                match_segundos = re.findall(r"\b\d{2}[\.,]\d{2}\b", linha_limpa)
                
                tempo_final = "S/T"
                if match_minutos:
                    tempo_final = padronizar_tempo_string(match_minutos[0])
                elif match_segundos:
                    candidatos = []
                    for c in match_segundos:
                        c_ponto = c.replace(',', '.')
                        if c_ponto.endswith('.00') and float(c_ponto) <= 20.0:
                            continue
                        candidatos.append(c)
                    if candidatos:
                        tempo_final = padronizar_tempo_string(candidatos[0])
                    elif match_segundos:
                        tempo_final = padronizar_tempo_string(match_segundos[0])
            
            linhas_encontradas.append({
                "Data": data_prova, "Local/Etapa": local_etapa, "Prova": prova_atual,
                "Atleta": atleta_final, "Categoria": "Master", "Tempo": tempo_final
            })
            
    return pd.DataFrame(linhas_encontradas)

# --- ENGINE INTERFACE ---

CSV_FILE = "historico_vinhedo.csv"

if os.path.exists(CSV_FILE):
    df_historico = pd.read_csv(CSV_FILE)
else:
    df_historico = pd.DataFrame(columns=["Data", "Local/Etapa", "Prova", "Atleta", "Categoria", "Tempo"])

if not df_historico.empty:
    df_historico["Atleta"] = df_historico["Atleta"].apply(normalizar_nome_atleta)
    df_historico["Prova"] = df_historico["Prova"].apply(normalizar_prova)
    df_historico["Tempo"] = df_historico["Tempo"].apply(padronizar_tempo_string)
    df_historico = df_historico[df_historico["Atleta"] != "Atleta Desconhecido"]

aba1, aba2, aba3, aba4 = st.tabs(["🔍 Consulta por Atleta", "🏊‍♂️ Simulador de Revezamentos", "📤 Alimentar Sistema", "🗄️ Base Geral CSV"])

with aba1:
    st.subheader("Ficha de Rendimento Individual")
    if not df_historico.empty:
        lista_atletas = sorted(df_historico["Atleta"].unique())
        atleta_sel = st.selectbox("Selecione o Atleta:", lista_atletas)
        
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
                st.warning("Este atleta não possui marcas numéricas válidas.")
        with col2:
            st.markdown("#### 📅 Histórico de Evolução Cronológica")
            df_atleta["Data_Dt"] = pd.to_datetime(df_atleta["Data"], format="%d/%m/%Y", errors="coerce")
            df_cronologico = df_atleta.sort_values(by="Data_Dt", ascending=False)[["Data", "Local/Etapa", "Prova", "Tempo"]]
            st.dataframe(df_cronologico, use_container_width=True, hide_index=True)
    else:
        st.info("O arquivo CSV histórico está vazio ou não foi encontrado. Alimente o sistema na aba de 'Alimentar Sistema'.")

with aba2:
    st.subheader("🚀 Simulador Estatístico de Revezamento Master (4x50m)")
    tipo_rev = st.radio("Estilo:", ["4x50m Livre", "4x50m Medley"], horizontal=True)
    lista_completa = sorted(list(IDADES_BASE_ATLETAS.keys()))
    atletas_escolhidos = st.multiselect("Selecione EXATAMENTE 4 atletas:", lista_completa)
    
    if len(atletas_escolhidos) == 4:
        soma_idades = sum(IDADES_BASE_ATLETAS[a] for a in atletas_escolhidos)
        cat_rev = "320+" if soma_idades >= 320 else ("280+" if soma_idades >= 280 else ("240+" if soma_idades >= 240 else ("200+" if soma_idades >= 200 else ("160+" if soma_idades >= 160 else ("120+" if soma_idades >= 120 else "80+")))))
        st.metric(label="Categoria Oficial", value=f"Classe {cat_rev}", delta=f"Idade Somada: {soma_idades} Anos")
        
        if tipo_rev == "4x50m Livre":
            tempo_total_seg = 0.0
            linhas_sim = []
            for a in atletas_escolhidos:
                seg, t_str = obter_pr_revezamento(df_historico, a, "Livre")
                tempo_total_seg += seg if seg != float('inf') else 35.0
                linhas_sim.append({"Atleta": a, "Estilo": "50m Livre", "PR Individual": t_str})
            st.table(pd.DataFrame(linhas_sim))
            st.subheader(f"⏱️ Tempo Total Estimado: {segundos_para_tempo(tempo_total_seg)}")
        else:
            estilos_m = ["Costas", "Peito", "Borboleta", "Livre"]
            mejor_t = float('inf')
            mejor_comb = None
            for perm in itertools.permutations(atletas_escolhidos):
                t_cos, _ = obter_pr_revezamento(df_historico, perm[0], "Costas")
                t_pei, _ = obter_pr_revezamento(df_historico, perm[1], "Peito")
                t_bor, _ = obter_pr_revezamento(df_historico, perm[2], "Borboleta")
                t_liv, _ = obter_pr_revezamento(df_historico, perm[3], "Livre")
                soma = t_cos + t_pei + t_bor + t_liv
                if soma < mejor_t:
                    mejor_t = soma
                    mejor_comb = perm
            if mejor_t != float('inf'):
                linhas_m = []
                for i, est_n in enumerate(estilos_m):
                    _, t_str = obter_pr_revezamento(df_historico, mejor_comb[i], est_n)
                    linhas_m.append({"Ordem": f"{i+1}º Nadador", "Atleta": mejor_comb[i], "Estilo (50m)": est_n, "Tempo Estimado": t_str})
                st.table(pd.DataFrame(linhas_m))
                st.subheader(f"⏱️ Tempo Otimizado Medley: {segundos_para_tempo(mejor_t)}")

with aba3:
    st.subheader("Entrada de Dados e Atualização do Painel")
    c_pdf, col_manual = st.columns(2)
    with c_pdf:
        st.markdown("### 📤 Upload de Relatórios oficiais (PDF)")
        uploaded_file = st.file_uploader("Arraste o PDF aqui:", type=["pdf"])
        if uploaded_file is not None:
            if st.button("Processar e Fundir Dados"):
                df_novos = processar_pdf(uploaded_file)
                if not df_novos.empty:
                    df_total = pd.concat([df_historico, df_novos]).drop_duplicates(subset=["Data", "Prova", "Atleta", "Tempo"])
                    df_total.to_csv(CSV_FILE, index=False)
                    st.success(f"Sucesso! {len(df_novos)} novos tempos unificados na base!")
                    st.rerun()
                else:
                    st.warning("Nenhum atleta mapeado encontrado nesse arquivo.")
    with col_manual:
        st.markdown("### ✍️ Lançamento Manual (Treinos / Borda)")
        lista_atletas_v = sorted(list(IDADES_BASE_ATLETAS.keys()))
        atleta_m = st.selectbox("Selecione o Atleta:", lista_atletas_v)
        prova_m = st.selectbox("Estilo/Distância da Prova:", [
            "50m Livre", "50m Peito", "50m Costas", "50m Borboleta",
            "100m Livre", "100m Peito", "100m Costas", "100m Borboleta", "100m Medley",
            "200m Livre", "200m Costas", "400m Livre"
        ])
        gen_m = st.selectbox("Gênero:", ["Fem", "Masc"])
        data_m = st.date_input("Data da Coleta:")
        local_m = st.text_input("Etapa/Local:", value="Treino SEL Vinhedo")
        tempo_m = st.text_input("Tempo Registrado (ex: 28.54 ou 1:04.25):", placeholder="MM:SS.CC ou SS.CC")
        
        if st.button("Gravar Tempo Manual"):
            if tempo_m and data_m:
                t_padrao = padronizar_tempo_string(tempo_m)
                nova_linha = pd.DataFrame([{
                    "Data": data_m.strftime("%d/%m/%Y"), "Local/Etapa": local_m, "Prova": f"{prova_m} {gen_m}",
                    "Atleta": atleta_m, "Categoria": "Master", "Tempo": t_padrao
                }])
                df_total = pd.concat([df_historico, nova_linha]).drop_duplicates()
                df_total.to_csv(CSV_FILE, index=False)
                st.success("Tempo de treino adicionado com sucesso!")
                st.rerun()

with aba4:
    st.subheader("Visualização Bruta do Histórico Permanente (CSV)")
    st.dataframe(df_historico, use_container_width=True, hide_index=True)
