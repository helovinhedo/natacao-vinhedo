import streamlit as st
import pandas as pd
import re
import os
import itertools
from pypdf import PdfReader

st.set_page_config(page_title="Painel Natação Master", layout="wide")

# --- DICIONÁRIOS DE UNIFICAÇÃO ---

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
    "CLAUDIA COLAMARINO": 1971, "BRUNA LIMA VICENTE": 1991, "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR": 1986,
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

# --- FUNÇÕES DE PADRONIZAÇÃO E LIMPEZA ---

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

# --- CAPTURA DE DADOS DO PDF ---

def processar_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    linhas_encontradas = []
    
    data_prova = ""
    campeonato_nome = ""
    local_nome = ""
    prova_atual = "Não identificada"
    faixa_atual = "Master"
    
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() + "\n"
        
    linhas = texto_completo.split("\n")
    
    # 1. CAPTURA DE CABEÇALHO GLOBAL (Sem limite de linhas)
    for l in linhas:
        l_up = l.upper().strip()
        
        # Pega a data
        if not data_prova:
            match_d = re.search(r'(\d{2}/\d{2}/\d{4})', l)
            if match_d:
                data_prova = match_d.group(1)
                
        # Pega o nome do campeonato
        if not campeonato_nome and any(k in l_up for k in ["CAMPEONATO", "COPA", "TROFÉU", "TORNEIO", "FESTIVAL", "CIRCUITO"]):
            # Exclui linhas de controle
            if not any(x in l_up for x in ["ABMN", "RESULTADOS", "SWIM IT UP", "PROVA", "FAIXA", "VISITE"]):
                campeonato_nome = l.replace("'", "").strip()
        
        # Pega o local
        if not local_nome and "-" in l_up and "/" in l_up:
            # Exclui linhas como "04/07/2026 (25 METROS, 10 RAIAS)" ou links
            if not any(x in l_up for x in ["METROS", "RAIAS", "DATA:", "VISITE", "PROVA", "PÁGINA"]):
                local_nome = l.replace("'", "").strip()
                
        # Se achou os 3, não precisa mais perder tempo procurando cabeçalho
        if campeonato_nome and local_nome and data_prova:
            break

    # Fallbacks de segurança
    campeonato_nome = campeonato_nome if campeonato_nome else "Competição Não Identificada"
    data_prova = data_prova if data_prova else "Data Não Identificada"
    
    if campeonato_nome != "Competição Não Identificada" and local_nome:
        local_etapa_final = f"{campeonato_nome} - {local_nome}"
    else:
        local_etapa_final = campeonato_nome

    # 2. VARREDURA DE ATLETAS E TEMPOS
    for idx, linha in enumerate(linhas):
        linha_upper = linha.upper().strip()
        
        # Captura da Prova
        if "PROVA" in linha_upper and any(w in linha_upper for w in ["METROS", "LIVRE", "BORBOLETA", "PEITO", "COSTAS", "MEDLEY"]):
            prova_atual = normalizar_prova(linha)
        elif re.match(r'^PROVA\s+\d+', linha_upper):
            partes_p = [linha]
            for j in range(1, 4):
                if idx + j < len(linhas):
                    next_l = linhas[idx+j].strip()
                    if any(w in next_l.upper() for w in ["LIVRE", "BORBOLETA", "PEITO", "COSTAS", "MEDLEY", "FEMININO", "MASCULINO", "MISTO", "FEM", "MASC"]):
                        partes_p.append(next_l)
            prova_atual = normalizar_prova(" ".join(partes_p))
            
        # Captura da Categoria (Faixa Etária)
        if "FAIXA:" in linha_upper:
            for j in range(0, 4):
                if idx + j < len(linhas):
                    busca_faixa = linhas[idx+j].upper().strip()
                    if "+" in busca_faixa or "MASTER" in busca_faixa:
                        faixa_limpa = busca_faixa.replace("FAIXA:", "").replace('"', '').replace(',', '').strip()
                        faixa_atual = re.sub(r'-+', '', faixa_limpa).strip()
                        faixa_atual = faixa_atual.replace("PRÉ- MASTER", "PRÉ-MASTER")
                        break
            
        # Captura do Atleta e Tempo
        if "VINHEDO" in linha_upper or "VINHEDE" in linha_upper:
            linha_limpa = linha.replace('"', '').replace(';', ' ').strip()
            atleta_final = normalizar_nome_atleta(linha_limpa)
            
            if atleta_final == "Atleta Desconhecido":
                continue
                
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
                    if candidatos:
                        tempo_final = padronizar_tempo_string(candidatos[0])
            
            linhas_encontradas.append({
                "Data": data_prova, "Local/Etapa": local_etapa_final, "Prova": prova_atual,
                "Atleta": atleta_final, "Categoria": faixa_atual, "Tempo": tempo_final
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

aba1, aba2, aba3, aba4 = st.tabs(["🔍 Consulta por Atleta", "🏊‍♂️ Simulador Automático de Revezamento", "📤 Alimentar Sistema", "🗄️ Base Geral CSV"])

with aba1:
    st.title("Ficha de Rendimento Individual")
    if not df_historico.empty:
        lista_atletas = sorted(df_historico["Atleta"].unique())
        atleta_sel = st.selectbox("Selecione o Atleta:", lista_atletas)
        
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

with aba2:
    st.title("🚀 Inteligência Estratégica: Top Revezamentos")
    st.markdown("Neste simulador, o sistema calcula as combinações filtrando pelo gênero correto e otimizando pela categoria de idade real.")
    
    lista_completa = sorted(list(ANOS_NASCIMENTO.keys()))
    atletas_pool = st.multiselect("Selecione a base de atletas para simular (Padrão: Todos):", lista_completa, default=lista_completa)
    
    col_rev1, col_rev2 = st.columns(2)
    with col_rev1:
        tipo_rev = st.radio("Estilo do Revezamento:", ["4x50m Livre", "4x50m Medley"], horizontal=True)
    with col_rev2:
        genero_rev = st.radio("Categoria de Gênero:", ["Feminino", "Masculino", "Misto"], horizontal=True)
    
    if st.button("Gerar Melhores Combinações"):
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
                    tempos = [obter_pr_revezamento(df_historico, a, "Livre")[0] for a in combo]
                    if float('inf') not in tempos:
                        idade_total = sum(calcular_idade(a) for a in combo)
                        cat = obter_categoria_revezamento(idade_total)
                        resultados.append({
                            "Equipe": " / ".join(combo), "Categoria": cat,
                            "Soma Idades": idade_total, "Tempo Total (Seg)": sum(tempos),
                            "Tempo Estimado": segundos_para_tempo(sum(tempos))
                        })
            else:
                for combo in combinacoes_validas:
                    melhor_t = float('inf')
                    melhor_ordem = None
                    for perm in itertools.permutations(combo):
                        t_cos, _ = obter_pr_revezamento(df_historico, perm[0], "Costas")
                        t_pei, _ = obter_pr_revezamento(df_historico, perm[1], "Peito")
                        t_bor, _ = obter_pr_revezamento(df_historico, perm[2], "Borboleta")
                        t_liv, _ = obter_pr_revezamento(df_historico, perm[3], "Livre")
                        soma = t_cos + t_pei + t_bor + t_liv
                        if soma < melhor_t:
                            melhor_t = soma
                            melhor_ordem = perm
                            
                    if melhor_t != float('inf'):
                        idade_total = sum(calcular_idade(a) for a in combo)
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
                st.warning("Não há tempos válidos registrados para formar combinações completas com estes atletas neste estilo.")

with aba3:
    st.subheader("Entrada de Dados e Atualização do Painel")
    c_pdf, col_manual = st.columns(2)
    with c_pdf:
        st.markdown("### 📤 Upload de Relatórios oficiais (PDF)")
        st.markdown("*Agora otimizado para o padrão ABMN.*")
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
                    st.warning("Nenhum atleta mapeado foi encontrado neste arquivo.")
    with col_manual:
        st.markdown("### ✍️ Lançamento Manual (Treinos / Borda)")
        lista_atletas_v = sorted(list(ANOS_NASCIMENTO.keys()))
        atleta_m = st.selectbox("Selecione o Atleta:", lista_atletas_v)
        prova_m = st.selectbox("Estilo/Distância da Prova:", [
            "50m Livre", "50m Peito", "50m Costas", "50m Borboleta",
            "100m Livre", "100m Peito", "100m Costas", "100m Borboleta", "100m Medley",
            "200m Livre", "200m Costas", "400m Livre"
        ])
        gen_m = st.selectbox("Gênero da Prova:", ["Fem", "Masc", "Misto"])
        data_m = st.date_input("Data da Coleta:")
        local_m = st.text_input("Etapa/Descrição do Local:", value="Treino SEL Vinhedo")
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
                st.success("Tempo adicionado com sucesso!")
                st.rerun()

with aba4:
    st.subheader("🗄️ Gerenciamento da Base de Dados (CSV)")
    
    col_download, col_upload = st.columns(2)
    
    with col_download:
        st.markdown("### 📥 Salvar Backup")
        st.markdown("Faça o download da base atual antes de atualizar o código no GitHub para não perder dados.")
        if not df_historico.empty:
            csv_export = df_historico.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar historico_vinhedo.csv",
                data=csv_export,
                file_name='historico_vinhedo.csv',
                mime='text/csv',
                type="primary"
            )
        else:
            st.info("A base está vazia. Nada para baixar.")
            
    with col_upload:
        st.markdown("### 🔄 Restaurar Backup")
        st.markdown("Se o servidor resetou, faça o upload do seu CSV salvo aqui para restaurar a base.")
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
