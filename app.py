import streamlit as st
import pandas as pd
import re
import os
import itertools
from pypdf import PdfReader

st.set_page_config(page_title="Painel Natação Master", layout="wide")

# ==========================================
# --- DICIONÁRIOS DE UNIFICAÇÃO ---
# ==========================================
DIC_ATLETAS = {
    "CLAUDIA": "CLAUDIA COLAMARINO", "BRUNA": "BRUNA LIMA VICENTE",
    "ÁLVARO": "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR", "ALVARO": "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR",
    "HIROSHI": "RAFAEL HIROSHI BRAZ DA SILVA", "HELOISA": "HELOÍSA DE SOUSA EVANGELISTA",
    "HELOÍSA": "HELOÍSA DE SOUSA EVANGELISTA", "TALITA": "TALITA CLIOGIA BARBOSA",
    "CALEBE": "CALEBE RAMOS RIBEIRO", "MELLO": "RAFAEL MELLO",
    "REGINA": "ANA REGINA OLIVAN LIMONGI", "LARA": "LARA FERREIRA DE SOUZA TONIN",
    "FABIUS": "FABIUS LUIZ PALARO", "HELENA": "HELENA KIYOKA KOBAYASHI NABEIRO",
    "TIAGO": "TIAGO BERNAL", "VOLKER": "VOLKER PENK",
    "MURILO": "MURILO SANTOS", "LUCIANO": "LUCIANO DIAS GOBI",
    "MATIAS": "MATIAS KOLBE", "EDUARDO": "EDUARDO TREVISAN GONCALVES",
    "MARIANE": "MARIANE DE MORAES QUIRINO", "LARISSA": "LARISSA LIMA SOATO"
}

ANO_ATUAL = 2026
ANOS_NASCIMENTO = {
    "CLAUDIA COLAMARINO": 1971, "BRUNA LIMA VICENTE": 1988, "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR": 1986,
    "RAFAEL HIROSHI BRAZ DA SILVA": 1991, "HELOÍSA DE SOUSA EVANGELISTA": 1991, "TALITA CLIOGIA BARBOSA": 1996,
    "CALEBE RAMOS RIBEIRO": 1991, "RAFAEL MELLO": 1991, "ANA REGINA OLIVAN LIMONGI": 1986,
    "LARA FERREIRA DE SOUZA TONIN": 1991, "FABIUS LUIZ PALARO": 1976, "HELENA KIYOKA KOBAYASHI NABEIRO": 1981,
    "TIAGO BERNAL": 1981, "VOLKER PENK": 1971, "MURILO SANTOS": 2006, "LUCIANO DIAS GOBI": 1976,
    "EDUARDO TREVISAN GONCALVES": 1981, "MATIAS KOLBE": 1986, "MARIANE DE MORAES QUIRINO": 1996,
    "LARISSA LIMA SOATO": 2001
}

GENERO_ATLETAS = {
    "CLAUDIA COLAMARINO": "F", "BRUNA LIMA VICENTE": "F", "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR": "M",
    "RAFAEL HIROSHI BRAZ DA SILVA": "M", "HELOÍSA DE SOUSA EVANGELISTA": "F", "TALITA CLIOGIA BARBOSA": "F",
    "CALEBE RAMOS RIBEIRO": "M", "RAFAEL MELLO": "M", "ANA REGINA OLIVAN LIMONGI": "F",
    "LARA FERREIRA DE SOUZA TONIN": "F", "FABIUS LUIZ PALARO": "M", "HELENA KIYOKA KOBAYASHI NABEIRO": "F",
    "TIAGO BERNAL": "M", "VOLKER PENK": "M", "MURILO SANTOS": "M", "LUCIANO DIAS GOBI": "M",
    "EDUARDO TREVISAN GONCALVES": "M", "MATIAS KOLBE": "M", "MARIANE DE MORAES QUIRINO": "F",
    "LARISSA LIMA SOATO": "F"
}

# ==========================================
# --- FUNÇÕES DE PADRONIZAÇÃO E LIMPEZA ---
# ==========================================
def calcular_idade(atleta):
    return ANO_ATUAL - ANOS_NASCIMENTO.get(atleta, ANO_ATUAL - 30)

def obter_categoria_revezamento(soma_idades):
    if soma_idades >= 320: return "320+"
    elif soma_idades >= 280: return "280+"
    elif soma_idades >= 240: return "240+"
    elif soma_idades >= 200: return "200+"
    elif soma_idades >= 160: return "160+"
    elif soma_idades >= 120: return "120+"
    else: return "100+"

def normalizar_nome_atleta(nome_bruto):
    if not isinstance(nome_bruto, str): return "Atleta Desconhecido"
    nome_upper = " ".join(nome_bruto.split()).upper()
    for chave, nome_oficial in DIC_ATLETAS.items():
        if chave in nome_upper: return nome_oficial
    return "Atleta Desconhecido"

def normalizar_prova(prova_str):
    if not isinstance(prova_str, str): return "Estilo Não Identificado"
    p = re.sub(r'\(\d{2}/\d{2}/\d{4}\)', '', prova_str.upper())
    distancia = ""
    
    match_dist = re.search(r'(50|100|200|400|800|1500)\s*M', p)
    if match_dist:
        distancia = f"{match_dist.group(1)}m"
            
    estilo = ""
    if any(x in p for x in ["LIVRE", "CRAWL"]): estilo = "Livre"
    elif any(x in p for x in ["BORBOLETA", "GOLFINHO"]): estilo = "Borboleta"
    elif "COSTAS" in p: estilo = "Costas"
    elif "PEITO" in p: estilo = "Peito"
    elif any(x in p for x in ["MEDLEY", "ESTILOS"]): estilo = "Medley"
    
    genero = ""
    if re.search(r'FE.I.I.O|FEM|MOÇAS|MULHERES', p): genero = "Fem"
    elif re.search(r'MA.C.L.O|MASC|HOMEN|HOMENS', p): genero = "Masc"
    elif "MISTO" in p: genero = "Misto"
    
    if distancia and estilo and genero: return f"{distancia} {estilo} {genero}"
    elif distancia and estilo: return f"{distancia} {estilo}"
    return " ".join(prova_str.split())

def padronizar_tempo_string(tempo_str):
    t_clean = str(tempo_str).lower().strip().replace("c", "").replace("s", ".").replace("m", ":")
    t_clean = t_clean.replace(",", ".")
    if t_clean.startswith("00:"): t_clean = t_clean[3:]
    return t_clean

def tempo_para_segundos(tempo_str):
    try:
        t_str = str(tempo_str).strip()
        if t_str == "S/T" or t_str == "DQL" or t_str == "Ausente": return None
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
    if segundos_float == float('inf') or segundos_float is None or pd.isna(segundos_float): return "S/T"
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

# ==========================================
# --- CAPTURA DE DADOS DOS PDFs ---
# ==========================================
def processar_pdf_paulista(pdf_file, nome_evento_manual, data_evento_manual):
    reader = PdfReader(pdf_file)
    linhas_encontradas = []
    prova_atual = "Não identificada"
    faixa_atual = "Master"
    
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() + "\n"
        
    linhas = texto_completo.split("\n")

    for idx, inline_linha in enumerate(linhas):
        linha_upper = inline_linha.upper().strip()
        
        if "PROVA" in linha_upper and "METROS" in linha_upper:
            prova_atual = normalizar_prova(inline_linha)
        elif re.match(r'^PROVA\s+\d+', linha_upper):
            partes_p = [inline_linha]
            for j in range(1, 4):
                if idx + j < len(linhas):
                    next_l = linhas[idx+j].strip()
                    if any(w in next_l.upper() for w in ["LIVRE", "BORBOLETA", "PEITO", "COSTAS", "MEDLEY", "FEMININO", "MASCULINO", "MISTO", "FEM", "MASC"]):
                        partes_p.append(next_l)
            prova_atual = normalizar_prova(" ".join(partes_p))
            
        if "FAIXA:" in linha_upper:
            for j in range(0, 4):
                if idx + j < len(linhas):
                    busca_faixa = linhas[idx+j].upper().strip()
                    if "+" in busca_faixa or "MASTER" in busca_faixa:
                        faixa_limpa = busca_faixa.replace("FAIXA:", "").replace('"', '').replace(',', '').strip()
                        faixa_atual = re.sub(r'-+', '', faixa_limpa).strip()
                        faixa_atual = faixa_atual.replace("PRÉ- MASTER", "PRÉ-MASTER")
                        break
            
        if "VINHEDO" in linha_upper or "VINHEDE" in linha_upper:
            linha_limpa = inline_linha.replace('"', '').replace(';', ' ').strip()
            atleta_final = normalizar_nome_atleta(linha_limpa)
            
            if atleta_final == "Atleta Desconhecido": continue
                
            if any(w in linha_upper for w in ["AUSENTE", "N/C", "Ñ NADOU", "DESCLA", "DQL"]):
                tempo_final = "DQL" if ("DQL" in linha_upper or "DESCLA" in linha_upper) else "Ausente"
            else:
                match_minutos = re.findall(r'\b\d{1,2}[m:]\d{2}[s\.]\d{2}c?\b', linha_limpa, re.IGNORECASE)
                match_segundos = re.findall(r'\b\d{2}[\.,]\d{2}\b', linha_limpa)
                tempo_final = "S/T"
                
                if match_minutos:
                    tempo_final = padronizar_tempo_string(match_minutos[0])
                elif match_segundos:
                    candidatos = [c for c in match_segundos if not (c.replace(',', '.').endswith('.00') and float(c.replace(',', '.')) <= 20.0)]
                    if candidatos: tempo_final = padronizar_tempo_string(candidatos[0])
            
            linhas_encontradas.append({
                "Data": data_evento_manual, "Local/Etapa": nome_evento_manual, "Prova": prova_atual,
                "Atleta": atleta_final, "Categoria": faixa_atual, "Tempo": tempo_final
            })
            
    return pd.DataFrame(linhas_encontradas)

def processar_pdf_unami(pdf_file, nome_evento_manual, data_evento_manual):
    reader = PdfReader(pdf_file)
    linhas_encontradas = []
    prova_atual = "Não identificada"
    categoria_atual = "Master"
    
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() + "\n"
        
    linhas = texto_completo.split("\n")

    for idx, inline_linha in enumerate(linhas):
        linha_upper = inline_linha.upper().strip()
        
        if re.match(r'^PROVA\s*\d*', linha_upper):
            bloco_prova = linha_upper
            for j in range(1, 5):
                if idx + j < len(linhas):
                    bloco_prova += " " + linhas[idx+j].upper().strip()
            
            if re.search(r'(50|100|200|400|800|1500)\s*M', bloco_prova):
                prova_atual = normalizar_prova(bloco_prova)
                
                match_cat = re.search(r'\((\d{2}\+)\)', bloco_prova)
                if match_cat:
                    categoria_atual = match_cat.group(1)
            
        if "VINHEDO" in linha_upper or "VINHEDE" in linha_upper:
            linha_limpa = inline_linha.replace('"', '').replace(';', ' ').strip()
            atleta_final = normalizar_nome_atleta(linha_limpa)
            
            if atleta_final == "Atleta Desconhecido": continue
            
            if any(w in linha_upper for w in ["AUSENTE", "N/C", "Ñ NADOU", "DESCLA", "DQL"]):
                tempo_final = "DQL" if any(w in linha_upper for w in ["DESCLA", "DQL"]) else "Ausente"
            else:
                match_tempo = re.search(r'(?:\d{1,2}m)?\d{2}s\d{2}c?', linha_limpa, re.IGNORECASE)
                if match_tempo:
                    tempo_final = padronizar_tempo_string(match_tempo.group(0))
                else:
                    tempo_final = "S/T"
            
            linhas_encontradas.append({
                "Data": data_evento_manual, "Local/Etapa": nome_evento_manual, "Prova": prova_atual,
                "Atleta": atleta_final, "Categoria": categoria_atual, "Tempo": tempo_final
            })
            
    return pd.DataFrame(linhas_encontradas)

def processar_pdf(pdf_file, tipo_relatorio, nome_evento_manual, data_evento_manual):
    if tipo_relatorio == "UNAMI":
        return processar_pdf_unami(pdf_file, nome_evento_manual, data_evento_manual)
    else:
        return processar_pdf_paulista(pdf_file, nome_evento_manual, data_evento_manual)

# ==========================================
# --- ENGINE INTERFACE (STREAMLIT) INTELIGENTE ---
# ==========================================
CSV_FILE = "historico_vinhedo.csv"
colunas_padrao = ["Data", "Local/Etapa", "Prova", "Atleta", "Categoria", "Tempo"]

if os.path.exists(CSV_FILE):
    try:
        # SUPER MOTOR DE LEITURA ADAPTATIVA:
        # Tenta ler com Vírgula + UTF-8 (Padrão)
        df_historico = pd.read_csv(CSV_FILE, encoding="utf-8")
        if "Atleta" not in df_historico.columns:
            # Tenta com Ponto e Vírgula + UTF-8
            df_historico = pd.read_csv(CSV_FILE, sep=";", encoding="utf-8")
            
    except Exception:
        try:
            # Tenta ler no padrão do Excel Brasileiro (Ponto e Vírgula + Latin-1)
            df_historico = pd.read_csv(CSV_FILE, sep=";", encoding="latin1")
        except Exception:
            df_historico = pd.DataFrame(columns=colunas_padrao)
            
    # Remove colunas duplicadas que surgiram por edições manuais
    if "Atleta" in df_historico.columns:
        df_historico = df_historico.loc[:, ~df_historico.columns.duplicated()].copy()
        df_historico = df_historico.dropna(how="all")
    else:
        df_historico = pd.DataFrame(columns=colunas_padrao)
else:
    df_historico = pd.DataFrame(columns=colunas_padrao)

# Aplica as limpezas se a base contiver linhas válidas
if not df_historico.empty:
    df_historico["Atleta"] = df_historico["Atleta"].apply(normalizar_nome_atleta)
    df_historico["Prova"] = df_historico["Prova"].apply(normalizar_prova)
    df_historico["Tempo"] = df_historico["Tempo"].apply(padronizar_tempo_string)
    df_historico = df_historico[df_historico["Atleta"] != "Atleta Desconhecido"]

# Criação das Abas
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "👤 Visão Atleta", 
    "⏱️ Visão Treinador", 
    "🏊‍♂️ Simulador Revezamento", 
    "📤 Alimentar Base", 
    "📊 Estatísticas", 
    "🗄️ Gerenciamento e Backup"
])

# ------------------------------------------
# ABA 1: VISÃO ATLETA
# ------------------------------------------
with aba1:
    st.title("Ficha de Rendimento Individual")
    if not df_historico.empty:
        lista_atletas = sorted(df_historico["Atleta"].unique())
        atleta_sel = st.selectbox("Selecione o Atleta:", lista_atletas, key="consulta_atleta")
        
        df_atleta = df_historico[df_historico["Atleta"] == atleta_sel].copy()
        df_atleta["Segundos"] = df_atleta["Tempo"].apply(tempo_para_segundos)
        df_validos = df_atleta[df_atleta["Segundos"].notna()].copy()
        df_validos["Data_Dt"] = pd.to_datetime(df_validos["Data"], format="%d/%m/%Y", errors="coerce")
        
        st.markdown("#### 🥇 Melhores Tempos Históricos (PRs)")
        if not df_validos.empty:
            idx_melhores = df_validos.groupby("Prova")["Segundos"].idxmin()
            df_prs = df_validos.loc[idx_melhores, ["Prova", "Tempo", "Data", "Local/Etapa"]].rename(columns={"Tempo": "Tempo Recorde"})
            
            styler_prs = df_prs.style.set_properties(**{
                'background-color': '#fffbe6',
                'color': '#333333',
                'border-color': 'white',
                'font-weight': 'bold'
            })
            st.dataframe(styler_prs, use_container_width=True, hide_index=True)
        else:
            st.warning("Este atleta não possui marcas numéricas válidas.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("#### 📅 Histórico de Evolução Cronológica")
        df_cronologico = df_validos.sort_values(by="Data_Dt", ascending=False)[["Data", "Local/Etapa", "Prova", "Tempo"]]
        st.dataframe(df_cronologico, use_container_width=True, hide_index=True)
            
        st.markdown("---")
        st.markdown("#### 📈 Gráfico de Evolução (Segundos)")
        if not df_validos.empty:
            df_grafico = df_validos.dropna(subset=["Data_Dt"]).sort_values("Data_Dt")
            provas_disp = df_grafico["Prova"].unique()
            abas_graficos = st.tabs(list(provas_disp))
            
            for i, prova_nome in enumerate(provas_disp):
                with abas_graficos[i]:
                    df_p = df_grafico[df_grafico["Prova"] == prova_nome].copy()
                    df_chart = df_p.set_index("Data_Dt")[["Segundos"]]
                    st.line_chart(df_chart, use_container_width=True)
    else:
        st.info("O arquivo CSV histórico está vazio ou não foi encontrado.")

# ------------------------------------------
# ABA 2: VISÃO TREINADOR
# ------------------------------------------
with aba2:
    st.title("Ranking da Equipe por Prova")
    if not df_historico.empty:
        lista_provas = sorted(df_historico["Prova"].unique())
        prova_sel = st.selectbox("Selecione a Prova para ver o Ranking interno:", lista_provas)
        
        df_prova_rank = df_historico[df_historico["Prova"] == prova_sel].copy()
        df_prova_rank["Segundos"] = df_prova_rank["Tempo"].apply(tempo_para_segundos)
        df_prova_rank = df_prova_rank.dropna(subset=["Segundos"])
        
        if not df_prova_rank.empty:
            idx_melhores_rank = df_prova_rank.groupby("Atleta")["Segundos"].idxmin()
            df_top_atletas = df_prova_rank.loc[idx_melhores_rank].sort_values("Segundos")
            df_top_atletas["Posição"] = range(1, len(df_top_atletas) + 1)
            
            st.dataframe(
                df_top_atletas[["Posição", "Atleta", "Tempo", "Categoria", "Local/Etapa", "Data"]], 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("Não há tempos válidos registrados para esta prova.")
    else:
        st.info("A base está vazia.")

# ------------------------------------------
# ABA 3: SIMULADOR DE REVEZAMENTO
# ------------------------------------------
with aba3:
    st.title("🚀 Inteligência Estratégica: Top Revezamentos")
    st.markdown("Selecione os atletas. Se alguém estiver sem tempo (S/T), dê dois cliques na tabela abaixo e digite o tempo manualmente (ex: 28.50) antes de simular!")
    
    lista_completa = sorted(list(ANOS_NASCIMENTO.keys()))
    atletas_pool = st.multiselect("Selecione os atletas disponíveis:", lista_completa, default=lista_completa[:6])
    
    col_rev1, col_rev2 = st.columns(2)
    with col_rev1:
        tipo_rev = st.radio("Estilo do Revezamento:", ["4x50m Livre", "4x50m Medley"], horizontal=True)
    with col_rev2:
        genero_rev = st.radio("Categoria de Gênero:", ["Feminino", "Masculino", "Misto"], horizontal=True)
    
    st.markdown("#### ✍️ Ajuste Manual de Tempos (Baseado nos PRs)")
    df_tempos_base = pd.DataFrame({"Atleta": atletas_pool})
    
    if tipo_rev == "4x50m Livre":
        df_tempos_base["Livre"] = [obter_pr_revezamento(df_historico, a, "Livre")[1] for a in atletas_pool]
    else:
        df_tempos_base["Costas"] = [obter_pr_revezamento(df_historico, a, "Costas")[1] for a in atletas_pool]
        df_tempos_base["Peito"] = [obter_pr_revezamento(df_historico, a, "Peito")[1] for a in atletas_pool]
        df_tempos_base["Borboleta"] = [obter_pr_revezamento(df_historico, a, "Borboleta")[1] for a in atletas_pool]
        df_tempos_base["Livre"] = [obter_pr_revezamento(df_historico, a, "Livre")[1] for a in atletas_pool]

    df_editado = st.data_editor(df_tempos_base, use_container_width=True, hide_index=True, disabled=["Atleta"])
    
    def extrair_string(valor):
        if isinstance(valor, (list, tuple, set, pd.Series)):
            return str(valor[0])
        return str(valor)

    if st.button("Gerar Melhores Combinações"):
        dict_tempos = df_editado.set_index("Atleta").to_dict(orient="index")
        
        homens = [a for a in atletas_pool if GENERO_ATLETAS.get(a) == 'M']
        mulheres = [a for a in atletas_pool if GENERO_ATLETAS.get(a) == 'F']
        
        combinacoes_validas = []
        if genero_rev == "Masculino":
            combinacoes_validas = list(itertools.combinations(homens, 4))
        elif genero_rev == "Feminino":
            combinacoes_validas = list(itertools.combinations(mulheres, 4))
        elif genero_rev == "Misto":
            combos_m = list(itertools.combinations(homens, 2))
            combos_f = list(itertools.combinations(mulheres, 2))
            combinacoes_validas = [m + f for m in combos_m for f in combos_f]

        if not combinacoes_validas:
            st.error(f"Não foram selecionados atletas suficientes para formar um revezamento da categoria {genero_rev}.")
        else:
            resultados = []
            
            if tipo_rev == "4x50m Livre":
                for combo in combinacoes_validas:
                    tempos = []
                    combo_limpo = [extrair_string(a) for a in combo] 
                    
                    for a in combo_limpo:
                        t_str = dict_tempos.get(a, {}).get("Livre", "S/T")
                        t_sec = tempo_para_segundos(t_str)
                        tempos.append(t_sec if t_sec else float('inf'))
                        
                    if float('inf') not in tempos:
                        idade_total = sum(calcular_idade(a) for a in combo_limpo)
                        cat = obter_categoria_revezamento(idade_total)
                        resultados.append({
                            "Equipe": " / ".join(combo_limpo), "Categoria": cat,
                            "Soma Idades": idade_total, "Tempo Total (Seg)": sum(tempos),
                            "Tempo Estimado": segundos_para_tempo(sum(tempos))
                        })
            else:
                for combo in combinacoes_validas:
                    combo_limpo = [extrair_string(a) for a in combo] 
                    melhor_t = float('inf')
                    melhor_ordem = None
                    
                    for perm in itertools.permutations(combo_limpo):
                        t_cos_str = dict_tempos.get(perm[0], {}).get("Costas", "S/T")
                        t_pei_str = dict_tempos.get(perm[1], {}).get("Peito", "S/T")
                        t_bor_str = dict_tempos.get(perm[2], {}).get("Borboleta", "S/T")
                        t_liv_str = dict_tempos.get(perm[3], {}).get("Livre", "S/T")
                        
                        t_cos = tempo_para_segundos(t_cos_str) or float('inf')
                        t_pei = tempo_para_segundos(t_pei_str) or float('inf')
                        t_bor = tempo_para_segundos(t_bor_str) or float('inf')
                        t_liv = tempo_para_segundos(t_liv_str) or float('inf')
                        
                        soma = t_cos + t_pei + t_bor + t_liv
                        if soma < melhor_t:
                            melhor_t = soma
                            melhor_ordem = perm
                            
                    if melhor_t != float('inf'):
                        idade_total = sum(calcular_idade(a) for a in combo_limpo)
                        cat = obter_categoria_revezamento(idade_total)
                        resultados.append({
                            "Equipe": f"Costas: {melhor_ordem[0]} / Peito: {melhor_ordem[1]} / Borboleta: {melhor_ordem[2]} / Livre: {melhor_ordem[3]}", 
                            "Categoria": cat, "Soma Idades": idade_total, 
                            "Tempo Total (Seg)": melhor_t, "Tempo Estimado": segundos_para_tempo(melhor_t)
                        })

            if resultados:
                df_res = pd.DataFrame(resultados)
                categorias_encontradas = sorted(df_res["Categoria"].unique(), reverse=True)
                
                for cat in categorias_encontradas:
                    st.markdown(f"### 🏆 Categoria {cat} ({genero_rev})")
                    df_cat = df_res[df_res["Categoria"] == cat].sort_values("Tempo Total (Seg)").head(3)
                    st.table(df_cat[["Tempo Estimado", "Soma Idades", "Equipe"]])
            else:
                st.warning("Preencha tempos válidos na tabela acima para os atletas selecionados.")

# ------------------------------------------
# ABA 4: ALIMENTAR BASE
# ------------------------------------------
with aba4:
    st.subheader("Entrada de Dados e Atualização do Painel")
    c_pdf, col_manual = st.columns(2)
    with c_pdf:
        st.markdown("### 📤 Upload de Relatórios oficiais (PDF)")
        
        tipo_relatorio_selecionado = st.selectbox("Formato do Relatório PDF:", ["UNAMI", "Paulista (FAP)"])
        nome_evento_pdf = st.text_input("Nome/Local da Competição (Ex: Paulista de Inverno - Santo André):", key="nome_ev_pdf")
        data_evento_pdf = st.date_input("Data da Competição:", key="data_ev_pdf")
        uploaded_file = st.file_uploader("Arraste o PDF aqui:", type=["pdf"])
        
        if uploaded_file is not None:
            if not nome_evento_pdf:
                st.warning("⚠️ Por favor, digite o Nome da Competição acima antes de processar.")
            else:
                if st.button("Processar e Fundir Dados"):
                    data_formatada = data_evento_pdf.strftime("%d/%m/%Y")
                    df_novos = processar_pdf(uploaded_file, tipo_relatorio_selecionado, nome_evento_pdf, data_formatada)
                    
                    if not df_novos.empty:
                        df_total = pd.concat([df_historico, df_novos]).drop_duplicates(subset=["Data", "Prova", "Atleta", "Tempo"])
                        df_total.to_csv(CSV_FILE, index=False)
                        st.success(f"Sucesso! {len(df_novos)} novos tempos unificados na base!")
                        st.rerun()
                    else:
                        st.warning("Nenhum atleta mapeado foi encontrado neste arquivo.")
                        
    with col_manual:
        st.markdown("### ✍️ Lançamento Manual (Treinos / Borda)")
        lista_atletas_v = sorted(list(ANOS_NASCIMENTO.keys()))
        atleta_m = st.selectbox("Selecione o Atleta:", lista_atletas_v, key="manual_atleta")
        prova_m = st.selectbox("Estilo/Distância da Prova:", [
            "50m Livre", "50m Peito", "50m Costas", "50m Borboleta",
            "100m Livre", "100m Peito", "100m Costas", "100m Borboleta", "100m Medley",
            "200m Livre", "200m Costas", "400m Livre"
        ], key="manual_prova")
        gen_m = st.selectbox("Gênero da Prova:", ["Fem", "Masc", "Misto"], key="manual_gen")
        data_m = st.date_input("Data da Coleta:", key="manual_data")
        local_m = st.text_input("Etapa/Descrição do Local:", value="Treino SEL Vinhedo", key="manual_local")
        tempo_m = st.text_input("Tempo Registrado (ex: 28.54 ou 1:04.25):", placeholder="MM:SS.CC ou SS.CC", key="manual_tempo")
        
        if st.button("Gravar Tempo Manual"):
            if tempo_m and data_m:
                t_padrao = padronizar_tempo_string(tempo_m)
                nova_linha = pd.DataFrame([{
                    "Data": data_m.strftime("%d/%m/%Y"), "Local/Etapa": local_m, "Prova": f"{prova_m} {gen_m}",
                    "Atleta": atleta_m, "Categoria": "Master", "Tempo": t_padrao
                }])
                df_total = pd.concat([df_historico, nova_linha]).drop_duplicates(subset=["Data", "Prova", "Atleta", "Tempo"])
                df_total.to_csv(CSV_FILE, index=False)
                st.success("Tempo adicionado com sucesso!")
                st.rerun()

# ------------------------------------------
# ABA 5: ESTATÍSTICAS
# ------------------------------------------
with aba5:
    st.title("📊 Raio-X da Equipe")
    
    if not df_historico.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Atletas Mapeados", df_historico["Atleta"].nunique())
        c2.metric("Total de Quedas na Água (Provas)", len(df_historico))
        c3.metric("Total de Etapas Participadas", df_historico["Local/Etapa"].nunique())
        
        st.markdown("---")
        
        col_rank1, col_rank2 = st.columns(2)
        with col_rank1:
            st.markdown("#### 🏆 Atletas Mais Assíduos (Maior nº de provas)")
            assiduidade = df_historico["Atleta"].value_counts().reset_index()
            assiduidade.columns = ["Atleta", "Nº de Provas Nadadas"]
            st.dataframe(assiduidade.head(10), use_container_width=True, hide_index=True)
            
        with col_rank2:
            st.markdown("#### 🏟️ Etapas com Maior Delegação")
            delegacao = df_historico.groupby("Local/Etapa")["Atleta"].nunique().reset_index()
            delegacao.columns = ["Competição", "Tamanho da Equipe"]
            delegacao = delegacao.sort_values("Tamanho da Equipe", ascending=False)
            st.dataframe(delegacao, use_container_width=True, hide_index=True)
    else:
        st.info("Estatísticas não disponíveis (Base Vazia).")

# ------------------------------------------
# ABA 6: GERENCIAMENTO E BACKUP
# ------------------------------------------
with aba6:
    st.subheader("🗄️ Painel de Controle Administrativo do CSV")
    
    col_download, col_upload = st.columns(2)
    with col_download:
        st.markdown("### 📥 Salvar Backup")
        st.markdown("Faça o download da base atual em formato CSV para o seu computador.")
        if not df_historico.empty:
            csv_export = df_historico.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar historico_vinhedo.csv",
                data=csv_export,
                file_name='historico_vinhedo.csv',
                mime='text/csv',
                type="secondary"
            )
        else:
            st.info("A base está vazia. Nada para baixar.")
            
    with col_upload:
        st.markdown("### 🔄 Restaurar Backup")
        st.markdown("Suba o arquivo CSV de backup aqui para substituir a base atual.")
        backup_file = st.file_uploader("Envie o backup (CSV):", type=["csv"])
        if backup_file is not None:
            if st.button("Restaurar Base de Dados"):
                try:
                    df_backup = pd.read_csv(backup_file)
                    df_backup.to_csv(CSV_FILE, index=False)
                    st.success("Base restaurada com sucesso! A página será atualizada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo: {e}")

    st.markdown("---")
    st.markdown("### Visualização Bruta do Histórico Permanente")
    st.dataframe(df_historico, use_container_width=True, hide_index=True)
