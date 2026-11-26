import streamlit as st
import pandas as pd
import re
import os
import io
import base64
import itertools
import requests
from datetime import datetime, timedelta
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextLine, LTChar

APP_NOME = "SEL Vinhedo Master"
APP_VERSAO = "v2.8"
APP_ATUALIZACAO = "26/11/2026"

st.set_page_config(page_title=f"Painel Natação Master - {APP_NOME}", layout="wide")

# ==========================================
# --- ARQUIVOS E COLUNAS OFICIAIS ---
# ==========================================
ANO_ATUAL = 2026
CSV_ELENCO = "elenco_vinhedo.csv"
CSV_FILE = "historico_vinhedo.csv"
CSV_ADVERSARIOS = "base_adversarios.csv"

COLUNAS_ELENCO = ["Atleta", "Apelidos_PDF", "Ano_Nascimento", "Genero", "Status"]
COLUNAS_VINHEDO = [
    "Data", "Campeonato", "Local/Etapa", "Prova", "Tipo_Prova",
    "Atleta", "Categoria", "Colocacao", "Tempo", "Pontos", "Recorde", "Integrantes"
]
COLUNAS_ADVERSARIOS = [
    "Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Matricula",
    "Atleta", "Equipe", "Colocacao", "Tempo", "Pontos", "Recorde"
]

ELENCO_PADRAO = [
    {"Atleta": "CLAUDIA COLAMARINO", "Apelidos_PDF": "CLAUDIA", "Ano_Nascimento": 1969, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "BRUNA LIMA VICENTE", "Apelidos_PDF": "BRUNA", "Ano_Nascimento": 1988, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR", "Apelidos_PDF": "ÁLVARO|ALVARO", "Ano_Nascimento": 1982, "Genero": "M", "Status": "Ativo"},
    {"Atleta": "RAFAEL HIROSHI BRAZ DA SILVA", "Apelidos_PDF": "HIROSHI", "Ano_Nascimento": 1987, "Genero": "M", "Status": "Ativo"},
    {"Atleta": "HELOÍSA DE SOUSA EVANGELISTA", "Apelidos_PDF": "HELOISA|HELOÍSA", "Ano_Nascimento": 1989, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "TALITA CLIOGIA BARBOSA", "Apelidos_PDF": "TALITA", "Ano_Nascimento": 1994, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "CALEBE RAMOS RIBEIRO", "Apelidos_PDF": "CALEBE", "Ano_Nascimento": 1987, "Genero": "M", "Status": "Ativo"},
    {"Atleta": "RAFAEL MELLO", "Apelidos_PDF": "MELLO", "Ano_Nascimento": 1988, "Genero": "M", "Status": "Inativo"},
    {"Atleta": "ANA REGINA OLIVAN LIMONGI", "Apelidos_PDF": "REGINA", "Ano_Nascimento": 1984, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "LARA FERREIRA DE SOUZA TONIN", "Apelidos_PDF": "LARA", "Ano_Nascimento": 1987, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "FABIUS LUIZ PALARO", "Apelidos_PDF": "FABIUS", "Ano_Nascimento": 1975, "Genero": "M", "Status": "Inativo"},
    {"Atleta": "HELENA KIYOKA KOBAYASHI NABEIRO", "Apelidos_PDF": "HELENA", "Ano_Nascimento": 1976, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "TIAGO BERNAL", "Apelidos_PDF": "TIAGO", "Ano_Nascimento": 1979, "Genero": "M", "Status": "Ativo"},
    {"Atleta": "VOLKER PENK", "Apelidos_PDF": "VOLKER", "Ano_Nascimento": 1967, "Genero": "M", "Status": "Inativo"},
    {"Atleta": "MURILO SANTOS", "Apelidos_PDF": "MURILO", "Ano_Nascimento": 2004, "Genero": "M", "Status": "Ativo"},
    {"Atleta": "LUCIANO DIAS GOBI", "Apelidos_PDF": "LUCIANO", "Ano_Nascimento": 1973, "Genero": "M", "Status": "Inativo"},
    {"Atleta": "MATIAS KOLBE", "Apelidos_PDF": "MATIAS", "Ano_Nascimento": 1981, "Genero": "M", "Status": "Inativo"},
    {"Atleta": "EDUARDO TREVISAN GONCALVES", "Apelidos_PDF": "EDUARDO", "Ano_Nascimento": 1976, "Genero": "M", "Status": "Ativo"},
    {"Atleta": "MARIANE DE MORAES QUIRINO", "Apelidos_PDF": "MARIANE", "Ano_Nascimento": 1992, "Genero": "F", "Status": "Ativo"},
    {"Atleta": "LARISSA LIMA SOATO", "Apelidos_PDF": "LARISSA", "Ano_Nascimento": 2001, "Genero": "F", "Status": "Inativo"},
    {"Atleta": "WAGNER ALVES BONADIO", "Apelidos_PDF": "WAGNER", "Ano_Nascimento": 1958, "Genero": "M", "Status": "Ativo"}
]

EQUIPES_ARN_REGEX = (
    r'SEL VINHEDO|PREFEITURA MUNICIPAL DE VINHEDO|MEDICINA BRAGAN[ÇC]A|UNIQUE CENTRO AQU[ÁA]TICO|'
    r'CT ACQUA|PREFEITURA MUNICIPAL DE SANTANA DE PARNA[ÍI]BA|PREFEITURA MUNICIPAL DE SANTANA DE PARNAIL|'
    r'PREFEITURA DE EXTREMA|CLUBE ATL[ÉE]TICO VALINHENSE|PREFEITURA MUNICIPAL DE PAUL[ÍI]NIA|'
    r'CLIP ACADEMIA|PREFEITURA DE VALINHOS|PREFEITURA DE JAGUARI[ÚU]NA|JAIR HENRIQUE STUDIO JIU JITSU|'
    r'DEEP ACADEMIA|SKYACQUA|MASTER RIO CLARO|UNICAMP - MASTER|ADA - ASSOCIA[ÇC][ÃA]O DESPORTIVA ATIBAIENSE|ARA[ÇC]ATUBA'
)

# ==========================================
# --- PERSISTÊNCIA AUTOMÁTICA NO GITHUB ---
# ==========================================
def github_configurado():
    try:
        return bool(st.secrets.get("GITHUB_TOKEN") and st.secrets.get("GITHUB_REPO"))
    except Exception:
        return False

def sincronizar_csv_github(caminho_arquivo, mensagem_commit="Atualização automática via Painel SEL Vinhedo"):
    """Envia o CSV atualizado direto para o repositório GitHub (evita perda ao hibernar)."""
    if not github_configurado() or not os.path.exists(caminho_arquivo):
        return False, "Secrets do GitHub não configurados."
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        branch = st.secrets.get("GITHUB_BRANCH", "main")
        url = f"https://api.github.com/repos/{repo}/contents/{caminho_arquivo}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        with open(caminho_arquivo, "rb") as f:
            conteudo_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Verifica se o arquivo já existe na branch para obter o SHA
        r_get = requests.get(url, headers=headers, params={"ref": branch}, timeout=10)
        payload = {
            "message": mensagem_commit,
            "content": conteudo_b64,
            "branch": branch
        }
        if r_get.status_code == 200:
            payload["sha"] = r_get.json().get("sha")

        r_put = requests.put(url, headers=headers, json=payload, timeout=15)
        if r_put.status_code in [200, 201]:
            return True, "Salvo no GitHub com sucesso!"
        return False, f"GitHub API ({r_put.status_code}): {r_put.text[:120]}"
    except Exception as e:
        return False, str(e)

def salvar_csv_persistente(df, caminho, msg_commit):
    """Salva localmente, limpa o cache de memória para leitura instantânea e sincroniza com o GitHub."""
    df.to_csv(caminho, index=False)
    st.cache_data.clear()
    ok_gh, msg_gh = sincronizar_csv_github(caminho, msg_commit)
    return ok_gh, msg_gh

# ==========================================
# --- FUNÇÕES DE PADRONIZAÇÃO E LIMPEZA ---
# ==========================================
def limpar_homoglifos_gregos(texto):
    if not isinstance(texto, str):
        return ""
    mapa = str.maketrans({
        "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I",
        "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T",
        "Υ": "Y", "Χ": "X", "α": "a", "ο": "o", "ρ": "p"
    })
    return texto.translate(mapa)

def limpar_nome_adversario(nome_bruto):
    if not isinstance(nome_bruto, str):
        return ""
    nome = limpar_homoglifos_gregos(nome_bruto)
    nome = re.sub(r'(\d)([A-ZÀ-ÿ])', r'\1 \2', nome)
    nome = re.sub(r'^\d+\s+', '', nome.strip())
    nome = re.sub(r'\|', ' ', nome)
    nome = re.sub(r'[^A-ZÀ-ÿa-z\s\.]', '', nome)
    nome = re.sub(r'\s+', ' ', nome).strip()
    return nome.title()

def normalizar_categoria(cat_str):
    if not isinstance(cat_str, str):
        return "Master"
    c = re.sub(r'[\{\}\^\$]', '', limpar_homoglifos_gregos(cat_str).upper()).strip()
    if "PRÉ" in c or "PRE" in c:
        return "PRÉ-MASTER"
    m = re.search(r'(\d{2,3})\s*\+?', c)
    if m and int(m.group(1)) >= 20:
        return f"{int(m.group(1))}+"
    return c if c else "Master"

def normalizar_data_str(data_str):
    if not isinstance(data_str, str) or not data_str.strip():
        return f"01/01/{ANO_ATUAL}"
    s = data_str.strip()
    dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.notna(dt):
        return dt.strftime("%d/%m/%Y")
    return s

def normalizar_prova_estrita(prova_str):
    """Retorna apenas nomes de provas limpos (ex: '100m Livre Fem'). Retorna None se for lixo."""
    if not isinstance(prova_str, str):
        return None
    p = re.sub(r'\(\d{2}/\d{2}/\d{4}\)', '', limpar_homoglifos_gregos(prova_str).upper())
    p = re.sub(r'PROVA\s*:?\s*\d{1,2}\s*-\s*', 'PROVA ', p)
    p = re.sub(r'PROVA\s*:?\s*\d{1,2}(?=(?:25|50|100|200|400|800|1500)\s*M)', 'PROVA ', p)

    distancia = ""
    match_rev = re.search(r'(4\s*X\s*(?:25|50|100))\s*M', p)
    if match_rev:
        distancia = match_rev.group(1).replace(" ", "").lower() + "m"
    else:
        match_dist = re.search(r'\b(25|50|100|200|400|800|1500)\s*M', p)
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

    prefixo = "Rev. " if "4x" in distancia else ""
    if distancia and estilo and genero:
        return f"{prefixo}{distancia} {estilo} {genero}"
    elif distancia and estilo:
        return f"{prefixo}{distancia} {estilo}"
    return None

def padronizar_tempo_string(tempo_str):
    if tempo_str is None or pd.isna(tempo_str):
        return "S/T"
    t_clean = str(tempo_str).lower().strip().replace(" ", "")
    if (
        t_clean in ["s/t", "dql", "ausente", "n/c", "", "9:99:99", "99:99:99", "9:99.99", "99:99.99"]
        or t_clean.startswith("d")
        or "99m99" in t_clean
        or "nadou" in t_clean
    ):
        if t_clean.startswith("d") or "99m99" in t_clean:
            return "DQL"
        if "nadou" in t_clean or t_clean in ["ausente", "n/c", "9:99:99", "99:99:99", "9:99.99", "99:99.99"]:
            return "Ausente"
        return t_clean.upper() if t_clean in ["s/t", "dql"] else "S/T"

    t_clean = t_clean.strip(":").replace("c", "").replace("s", ".").replace("m", ":").replace(",", ".")
    if t_clean.startswith("00:"):
        t_clean = t_clean[3:]
    if t_clean.count(":") == 2:
        partes_2 = t_clean.split(":")
        if partes_2[0] in ["0", "00"]:
            t_clean = f"{partes_2[1]}.{partes_2[2]}"
        else:
            t_clean = f"{partes_2[0]}:{partes_2[1]}.{partes_2[2]}"
    elif t_clean.count(":") == 1 and "." not in t_clean:
        p1, p2 = t_clean.split(":")
        t_clean = f"{p1}.{p2}"

    try:
        if ":" in t_clean:
            partes = t_clean.split(":")
            if len(partes) == 2 and "." in partes[1]:
                s, cs = partes[1].split(".")
                t_clean = f"{int(partes[0])}:{int(s):02d}.{cs[:2].ljust(2, '0')}"
        elif "." in t_clean:
            s, cs = t_clean.split(".")
            s_val = int(s) if s else 0
            t_clean = f"{s_val:02d}.{cs[:2].ljust(2, '0')}"
    except Exception:
        pass
    return t_clean

def tempo_para_segundos(tempo_str):
    try:
        t_str = str(tempo_str).strip()
        if t_str in ["S/T", "DQL", "Ausente", "None", "nan", ""]:
            return None
        if ":" in t_str:
            minutos, resto = t_str.split(":")
            segundos, centesimos = resto.split(".")
            val = float(minutos) * 60 + float(segundos) + float(centesimos) / 100
            return val if 0 < val < 5000 else None
        else:
            segundos, centesimos = t_str.split(".")
            val = float(segundos) + float(centesimos) / 100
            return val if 0 < val < 5000 else None
    except Exception:
        return None

def segundos_para_tempo(segundos_float):
    if segundos_float == float('inf') or segundos_float is None or pd.isna(segundos_float):
        return "S/T"
    minutos = int(segundos_float // 60)
    segundos = int(segundos_float % 60)
    centesimos = int(round((segundos_float % 1) * 100))
    if centesimos >= 100:
        segundos += 1
        centesimos -= 100
    if minutos > 0:
        return f"{minutos}:{segundos:02d}.{centesimos:02d}"
    return f"{segundos:02d}.{centesimos:02d}"

def formatar_colocacao_medalha(col):
    try:
        c = int(float(col))
        if c == 1: return "🥇 1º"
        elif c == 2: return "🥈 2º"
        elif c == 3: return "🥉 3º"
        elif c > 0: return f"{c}º"
        return "-"
    except Exception:
        return "-"

# ==========================================
# --- CARREGAMENTO EM CACHE (ALTA VELOCIDADE) ---
# ==========================================
@st.cache_data(show_spinner=False)
def carregar_elenco_cache():
    if os.path.exists(CSV_ELENCO):
        try:
            df_e = pd.read_csv(CSV_ELENCO, dtype=str).fillna("")
            if all(c in df_e.columns for c in COLUNAS_ELENCO) and not df_e.empty:
                df_e["Atleta"] = df_e["Atleta"].str.strip().str.upper()
                df_e["Ano_Nascimento"] = pd.to_numeric(df_e["Ano_Nascimento"], errors="coerce").fillna(1985).astype(int)
                df_e["Genero"] = df_e["Genero"].str.strip().str.upper().replace({"FEM": "F", "MASC": "M"})
                df_e["Status"] = df_e["Status"].str.strip().str.capitalize().replace({"": "Ativo"})
                return df_e[COLUNAS_ELENCO]
        except Exception:
            pass
    df_def = pd.DataFrame(ELENCO_PADRAO)
    df_def.to_csv(CSV_ELENCO, index=False)
    return df_def

df_elenco = carregar_elenco_cache()

DIC_ATLETAS = {}
ANOS_NASCIMENTO = {}
GENERO_ATLETAS = {}
ATLETAS_ATIVOS = []

for _, r_el in df_elenco.iterrows():
    nome_of = str(r_el["Atleta"]).strip().upper()
    if not nome_of:
        continue
    ANOS_NASCIMENTO[nome_of] = int(r_el["Ano_Nascimento"])
    GENERO_ATLETAS[nome_of] = str(r_el["Genero"]).strip().upper()
    if str(r_el["Status"]).strip().lower() == "ativo":
        ATLETAS_ATIVOS.append(nome_of)

    apelidos_raw = str(r_el["Apelidos_PDF"]).strip().upper()
    chaves = [c.strip() for c in apelidos_raw.split("|") if c.strip()]
    primeiro_nome = nome_of.split()[0]
    if primeiro_nome not in chaves:
        chaves.append(primeiro_nome)
    chaves.append(nome_of)
    for ch in chaves:
        DIC_ATLETAS[ch] = nome_of

ATLETAS_ATIVOS = sorted(list(set(ATLETAS_ATIVOS)))

def normalizar_nome_atleta(nome_bruto):
    if not isinstance(nome_bruto, str):
        return "Atleta Desconhecido"
    nome_upper = " ".join(limpar_homoglifos_gregos(nome_bruto).split()).upper()
    nome_upper = re.sub(r'(\d)([A-ZÀ-ÿ])', r'\1 \2', nome_upper)
    nome_upper = re.sub(r'([A-ZÀ-ÿ])(SEL\b)', r'\1 \2', nome_upper)
    for chave in sorted(DIC_ATLETAS.keys(), key=len, reverse=True):
        if re.search(rf'\b{re.escape(chave)}\b', nome_upper):
            return DIC_ATLETAS[chave]
    return "Atleta Desconhecido"

def calcular_idade(atleta, ano_ref=ANO_ATUAL):
    return ano_ref - ANOS_NASCIMENTO.get(atleta, ano_ref - 30)

def obter_faixa_etaria_atleta(atleta, ano_ref=ANO_ATUAL):
    idade = calcular_idade(atleta, ano_ref)
    if idade < 20:
        return "PRÉ-MASTER"
    return f"{(idade // 5) * 5}+"

def obter_categoria_revezamento(soma_idades):
    for limite in [320, 280, 240, 200, 160, 120, 100]:
        if soma_idades >= limite:
            return f"{limite}+"
    return "80+"

def obter_pr_revezamento(df, atleta, estilo_procurado):
    df_atleta = df[(df["Atleta"] == atleta) & (df["Tempo"].notna()) & (df["Tipo_Prova"] == "Individual")]
    df_prova = df_atleta[df_atleta["Prova"].str.contains(estilo_procurado, case=False, na=False)].copy()
    df_prova["Segundos"] = df_prova["Tempo"].apply(tempo_para_segundos)
    df_validos = df_prova[df_prova["Segundos"].notna()]
    if df_validos.empty:
        return float('inf'), "S/T"
    idx_min = df_validos["Segundos"].idxmin()
    return df_validos.loc[idx_min, "Segundos"], df_validos.loc[idx_min, "Tempo"]

@st.cache_data(show_spinner=False)
def carregar_bases_cache(dic_map):
    def ler_csv(caminho, colunas_esperadas):
        if not os.path.exists(caminho):
            return pd.DataFrame(columns=colunas_esperadas)
        df_lido = None
        for sep, enc in [(",", "utf-8"), (";", "utf-8"), (",", "latin1"), (";", "latin1")]:
            try:
                df_teste = pd.read_csv(caminho, sep=sep, encoding=enc, dtype=str)
                if "Atleta" in df_teste.columns:
                    df_lido = df_teste
                    break
            except Exception:
                continue
        if df_lido is None:
            return pd.DataFrame(columns=colunas_esperadas)
        df_lido = df_lido.loc[:, ~df_lido.columns.duplicated()].dropna(how="all").copy()
        for col in colunas_esperadas:
            if col not in df_lido.columns:
                df_lido[col] = "0" if col in ["Colocacao", "Pontos"] else ""
        return df_lido[colunas_esperadas].fillna("")

    df_h = ler_csv(CSV_FILE, COLUNAS_VINHEDO)
    df_a = ler_csv(CSV_ADVERSARIOS, COLUNAS_ADVERSARIOS)

    if not df_h.empty:
        df_h["Data"] = df_h["Data"].apply(normalizar_data_str)
        df_h["Atleta"] = df_h["Atleta"].apply(lambda x: "EQUIPE SEL VINHEDO" if str(x).upper() == "EQUIPE SEL VINHEDO" else normalizar_nome_atleta(x))
        df_h["Prova_Limpa"] = df_h["Prova"].apply(normalizar_prova_estrita)
        df_h["Prova"] = df_h["Prova_Limpa"].fillna(df_h["Prova"])
        df_h = df_h.drop(columns=["Prova_Limpa"])
        df_h["Tempo"] = df_h["Tempo"].apply(padronizar_tempo_string)
        df_h["Categoria"] = df_h["Categoria"].apply(normalizar_categoria)
        df_h["Colocacao"] = pd.to_numeric(df_h["Colocacao"], errors="coerce").fillna(0).astype(int)
        df_h["Pontos"] = pd.to_numeric(df_h["Pontos"], errors="coerce").fillna(0.0)
        df_h["Recorde"] = df_h["Recorde"].fillna("").astype(str)
        df_h["Integrantes"] = df_h["Integrantes"].fillna("").astype(str)
        df_h = df_h[(df_h["Atleta"] != "Atleta Desconhecido") & (~df_h["Prova"].str.contains("Não identificada", na=False))]

    if not df_a.empty:
        df_a["Data"] = df_a["Data"].apply(normalizar_data_str)
        df_a["Prova"] = df_a["Prova"].apply(normalizar_prova_estrita)
        df_a = df_a.dropna(subset=["Prova"]).copy()
        df_a["Tempo"] = df_a["Tempo"].apply(padronizar_tempo_string)
        df_a["Categoria"] = df_a["Categoria"].apply(normalizar_categoria)
        df_a["Matricula"] = df_a["Matricula"].apply(lambda x: re.sub(r'\.0$', '', str(x).strip()))

    return df_h, df_a

df_historico, df_adversarios = carregar_bases_cache(DIC_ATLETAS)

def obter_anos_ordenados(df):
    if df.empty:
        return [str(ANO_ATUAL)]
    anos = sorted(list(set(pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce").dt.year.dropna().astype(int).astype(str))), reverse=True)
    return anos if anos else [str(ANO_ATUAL)]

# ==========================================
# --- MOTOR VISUAL PDFMINER (COORDENADAS REAIS) ---
# ==========================================
def extrair_linhas_pdfminer(pdf_bytes, tol_y=3.5):
    """Extrai todas as linhas do PDF na orientação visual real (de cima para baixo, esquerda para direita)."""
    all_rows = []
    for pno, page_layout in enumerate(extract_pages(io.BytesIO(pdf_bytes))):
        spans = []
        def collect_lines(obj):
            if isinstance(obj, LTTextLine):
                cur_w, cur_x, last_x1 = "", None, None
                y0 = round(obj.bbox[1], 1)
                for ch in obj:
                    if isinstance(ch, LTChar):
                        c = ch.get_text()
                        if c.strip() == "":
                            if cur_w:
                                spans.append((cur_x, y0, cur_w))
                                cur_w, cur_x = "", None
                        else:
                            if cur_x is None:
                                cur_x = round(ch.bbox[0], 1)
                            elif last_x1 is not None and (ch.bbox[0] - last_x1) > 4.0:
                                spans.append((cur_x, y0, cur_w))
                                cur_w, cur_x = "", round(ch.bbox[0], 1)
                            cur_w += c
                        last_x1 = ch.bbox[2]
                if cur_w:
                    spans.append((cur_x, y0, cur_w))
            elif hasattr(obj, "__iter__"):
                for child in obj:
                    collect_lines(child)

        collect_lines(page_layout)
        spans.sort(key=lambda s: (-s[1], s[0]))
        rows = []
        for x0, y0, t in spans:
            placed = False
            if rows and abs(rows[-1]["y"] - y0) <= tol_y:
                # Impede fusão de cabeçalhos vazios sobrepostos na mesma coluna X
                collision = any(abs(ex_x - x0) < 8.0 for ex_x, _ in rows[-1]["items"])
                if not collision:
                    rows[-1]["items"].append((x0, t))
                    placed = True
            if not placed:
                rows.append({"page": pno + 1, "y": y0, "items": [(x0, t)]})
        for r in rows:
            r["items"].sort(key=lambda i: i[0])
            r["text"] = " ".join([t for _, t in r["items"]])
        all_rows.extend(rows)
    return all_rows

def detectar_metadados_visuais(rows_p1, nome_arquivo):
    nome_arq_clean = os.path.splitext(nome_arquivo)[0]
    linhas_topo = [limpar_homoglifos_gregos(r["text"]).strip() for r in rows_p1[:10] if r["text"].strip()]
    texto_topo = " ".join(linhas_topo)

    # Data: prioriza data no nome do arquivo, senão busca nas primeiras linhas visuais do cabeçalho
    data_detectada = None
    m_arq_data = re.search(r'(\d{2})[-/](\d{2})[-/](\d{4})', nome_arq_clean)
    if m_arq_data:
        data_detectada = f"{m_arq_data.group(1)}/{m_arq_data.group(2)}/{m_arq_data.group(3)}"
    else:
        cab_sem_rec = re.sub(r'Record\s+\d{1,2}m\d{2}s\d{2}c?\s+\d{2}/\d{2}/\d{4}', '', texto_topo, flags=re.IGNORECASE)
        datas_cab = re.findall(r'\b(\d{1,2}/\d{1,2}/\d{4})(?!\s+\d{2}:\d{2})', cab_sem_rec)
        if datas_cab:
            data_detectada = normalizar_data_str(datas_cab[0])
    if not data_detectada:
        data_detectada = f"01/01/{ANO_ATUAL}"

    # Nome da etapa: se o nome do arquivo já tiver descrição após a data (ex: "04-07-2026_Paulista de Inverno - Santo André"), usa ela limpa
    resto_arq = re.sub(r'^\d{2}[-/]\d{2}[-/]\d{4}[_\-\s]*', '', nome_arq_clean).replace("_", " ").strip()
    nome_evento = ""
    for l in linhas_topo:
        lu = l.upper()
        if any(k in lu for k in ["TROFEU", "TROFÉU", "COPA", "TORNEIO", "ETAPA", "FESTIVAL", "CAMPEONATO", "MASTER DE NATAÇÃO ARN"]):
            if not any(bad in lu for bad in ["COL.", "MATR.", "FAIXA:", "PROVA", "RECORD"]):
                cand = re.sub(r'\s*-\s*\d{1,2}/\d{1,2}/\d{4}.*$', '', l)
                cand = re.sub(r'^\d{2}/\d{2}/\d{4}\s*', '', cand).strip()
                if len(cand) >= 5:
                    nome_evento = cand
                    break

    if not nome_evento or "PAULISTA" in resto_arq.upper():
        if len(resto_arq) >= 5 and resto_arq != nome_arq_clean:
            nome_evento = resto_arq
    if not nome_evento:
        nome_evento = resto_arq or nome_arq_clean

    return data_detectada, nome_evento

# ==========================================
# --- 4 PARSERS ESPECIALIZADOS POR COORDENADAS ---
# ==========================================
def processar_unami_individual(rows, nome_evento, data_evento):
    vinhedo, adv = [], []
    prova_atual = None
    cat_atual = "Master"

    for idx, r in enumerate(rows):
        left_txt = limpar_gregos(" ".join([t for x, t in r["items"] if x < 185])).strip()
        if re.match(r'^PROVA\s+\d+', left_txt.upper()):
            cab_parts = [left_txt]
            for j in range(idx + 1, min(idx + 6, len(rows))):
                lj = limpar_gregos(" ".join([t for x, t in rows[j]["items"] if x < 185])).strip()
                if re.match(r'^PROVA\s+\d+', lj.upper()) or lj.upper().startswith("POS"):
                    break
                cab_parts.append(lj)
            cab_left = " ".join(cab_parts)
            p_cand = normalizar_prova_estrita(cab_left)
            if p_cand:
                prova_atual = p_cand
            m_c = re.search(r'\((\d{2,3}\+)\)', cab_left)
            if m_c:
                cat_atual = normalizar_categoria(m_c.group(1))

        if not prova_atual or "Rev." in prova_atual:
            continue

        pos_str = "".join([t for x, t in r["items"] if x < 38]).strip()
        mat_str = "".join([t for x, t in r["items"] if 38 <= x < 88]).strip()
        if re.match(r'^\d{1,2}$', pos_str) and re.match(r'^\d{1,6}$', mat_str):
            colocacao = int(pos_str)
            matricula = mat_str.lstrip("0") or mat_str
            mid_right = limpar_gregos(" ".join([t for x, t in r["items"] if x >= 88])).strip()
            mid_right = re.sub(r'([A-Za-zÀ-ÿ])(\d{2}m\d{2}s\d{2}c?)', r'\1 \2', mid_right)
            mid_right = re.sub(r'([a-zà-ÿ])(SEL\s+Vinhedo)', r'\1 \2', mid_right, flags=re.IGNORECASE)

            adj_status = ""
            for adj_i in [idx - 1, idx + 1]:
                if 0 <= adj_i < len(rows) and rows[adj_i]["page"] == r["page"] and abs(rows[adj_i]["y"] - r["y"]) <= 5.5:
                    adj_status += " " + " ".join([t for x, t in rows[adj_i]["items"] if x >= 510])

            linha_completa = f"{mid_right} {adj_status}".strip()
            up_comp = linha_completa.upper()

            if colocacao == 0 or any(w in up_comp for w in ["DESCLA", "D*D*", "DQL"]):
                tempo_f, pts_f, colocacao = "DQL", 0.0, 0
            elif any(w in up_comp for w in ["AUSENTE", "Ñ NADOU", "NADOU"]):
                tempo_f, pts_f, colocacao = "Ausente", 0.0, 0
            else:
                m_t = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)', linha_completa, re.IGNORECASE)
                tempo_f = padronizar_tempo_string(m_t.group(1)) if m_t else "S/T"
                m_p = re.search(r'(?<!\d)(\d{1,2},\d{2})(?!\d)', mid_right)
                pts_f = float(m_p.group(1).replace(",", ".")) if m_p else 0.0

            eh_rec = (pts_f >= 15.0) or ("RECORD" in up_comp)
            rec_flag = "Recorde UNAMI" if eh_rec else ""

            nome_part = limpar_gregos(" ".join([t for x, t in r["items"] if 88 <= x < 272])).strip()
            eq_part = limpar_gregos(" ".join([t for x, t in r["items"] if 272 <= x < 418])).strip()
            eq_part = re.sub(r'\d{1,2}m\d{2}s\d{2}c?.*$', '', eq_part).strip()
            if nome_part.upper().endswith("SEL") and "VINHEDO" in eq_part.upper():
                nome_part = nome_part[:-3].strip()
                eq_part = "SEL " + eq_part

            if "VINHEDO" in up_comp or "VINHEDE" in up_comp:
                atl_of = normalizar_nome_atleta(f"{nome_part} {eq_part}")
                if atl_of != "Atleta Desconhecido":
                    vinhedo.append({
                        "Data": data_evento, "Campeonato": "UNAMI", "Local/Etapa": nome_evento,
                        "Prova": prova_atual, "Tipo_Prova": "Individual", "Atleta": atl_of,
                        "Categoria": cat_atual, "Colocacao": colocacao, "Tempo": tempo_f,
                        "Pontos": pts_f, "Recorde": rec_flag, "Integrantes": ""
                    })
            else:
                if tempo_para_segundos(tempo_f) is not None and "25m" not in prova_atual:
                    nome_clean = limpar_nome_adversario(nome_part)
                    if len(nome_clean) >= 3:
                        adv.append({
                            "Data": data_evento, "Campeonato": "UNAMI", "Local/Etapa": nome_evento,
                            "Prova": prova_atual, "Categoria": cat_atual, "Matricula": matricula,
                            "Atleta": nome_clean, "Equipe": (eq_part[:35] or "UNAMI"),
                            "Colocacao": colocacao, "Tempo": tempo_f, "Pontos": pts_f, "Recorde": rec_flag
                        })
    return pd.DataFrame(vinhedo), pd.DataFrame(adv)

def processar_unami_revezamentos(rows, nome_evento, data_evento):
    vinhedo = []
    prova_atual = "Rev. 4x50m Medley"
    cat_atual = "Master"

    idx = 0
    while idx < len(rows):
        r = rows[idx]
        left_txt = limpar_gregos(" ".join([t for x, t in r["items"] if x < 170])).strip()
        if re.match(r'^PROVA\s+\d+', left_txt.upper()):
            cab_parts = [left_txt]
            for j in range(idx + 1, min(idx + 5, len(rows))):
                lj = limpar_gregos(" ".join([t for x, t in rows[j]["items"] if x < 170])).strip()
                if re.match(r'^PROVA\s+\d+', lj.upper()) or lj.upper().startswith("POS"):
                    break
                cab_parts.append(lj)
            p_cand = normalizar_prova_estrita(" ".join(cab_parts))
            if p_cand:
                prova_atual = p_cand if "Rev." in p_cand else f"Rev. {p_cand}"

        pos_str = "".join([t for x, t in r["items"] if x < 38]).strip()
        tid_str = "".join([t for x, t in r["items"] if 38 <= x < 88]).strip()
        rest_str = limpar_gregos(" ".join([t for x, t in r["items"] if x >= 88])).strip()

        if re.match(r'^\d{1,2}$', pos_str) and re.match(r'^\d{2,6}$', tid_str) and ("_" in rest_str or re.search(r'\b(80|100|120|160|200|240|280|320)\+', rest_str)):
            colocacao = int(pos_str)
            m_c = re.search(r'(80|100|120|160|200|240|280|320)\+', rest_str)
            if m_c:
                cat_atual = f"{m_c.group(1)}+"

            adj_status = ""
            for adj_i in [idx - 1, idx + 1]:
                if 0 <= adj_i < len(rows) and rows[adj_i]["page"] == r["page"] and abs(rows[adj_i]["y"] - r["y"]) <= 5.5:
                    adj_status += " " + " ".join([t for x, t in rows[adj_i]["items"] if x >= 510])

            integrantes = []
            k = idx + 1
            while k < len(rows):
                rk = rows[k]
                kp = "".join([t for x, t in rk["items"] if x < 38]).strip()
                kt = "".join([t for x, t in rk["items"] if 38 <= x < 88]).strip()
                k_full = limpar_gregos(rk["text"]).strip()
                if (re.match(r'^\d{1,2}$', kp) and re.match(r'^\d{2,6}$', kt)) or k_full.upper().startswith("DIST") or k_full.upper().startswith("PROVA"):
                    break
                atl_c = normalizar_nome_atleta(k_full)
                if atl_c != "Atleta Desconhecido" and atl_c not in integrantes:
                    integrantes.append(atl_c)
                k += 1

            if "VINHEDO" in rest_str.upper() or "VINHEDE" in rest_str.upper():
                up_r = (rest_str + " " + adj_status).upper()
                if colocacao == 0 or any(w in up_r for w in ["DESCLA", "D*D*", "DQL"]):
                    tempo_f, pts_f, colocacao = "DQL", 0.0, 0
                elif any(w in up_r for w in ["AUSENTE", "Ñ NADOU", "NADOU"]):
                    tempo_f, pts_f, colocacao = "Ausente", 0.0, 0
                else:
                    m_t = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)', rest_str, re.IGNORECASE)
                    tempo_f = padronizar_tempo_string(m_t.group(1)) if m_t else "S/T"
                    m_p = re.search(r'(?<!\d)(\d{1,2},\d{2})(?!\d)', rest_str)
                    pts_f = float(m_p.group(1).replace(",", ".")) if m_p else 0.0

                eh_rec = (pts_f >= 25.0) or ("RECORD" in up_r)
                rec_flag = "Recorde UNAMI" if eh_rec else ""

                vinhedo.append({
                    "Data": data_evento, "Campeonato": "UNAMI", "Local/Etapa": nome_evento,
                    "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": "EQUIPE SEL VINHEDO",
                    "Categoria": cat_atual, "Colocacao": colocacao, "Tempo": tempo_f,
                    "Pontos": pts_f, "Recorde": rec_flag, "Integrantes": " / ".join(integrantes)
                })
                for atl in integrantes:
                    vinhedo.append({
                        "Data": data_evento, "Campeonato": "UNAMI", "Local/Etapa": nome_evento,
                        "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": atl,
                        "Categoria": cat_atual, "Colocacao": colocacao, "Tempo": tempo_f,
                        "Pontos": 0.0, "Recorde": rec_flag, "Integrantes": " / ".join(integrantes)
                    })
            idx = k
            continue
        idx += 1

    return pd.DataFrame(vinhedo), pd.DataFrame(columns=COLUNAS_ADVERSARIOS)

def processar_pdf_paulista(rows, nome_evento, data_evento):
    vinhedo_rows, adversarios_rows = [], []
    prova_atual = None
    faixa_atual = "Master"
    eh_revezamento = False

    idx = 0
    while idx < len(rows):
        r = rows[idx]
        col_txt = " ".join([t for x, t in r["items"] if x < 48]).strip()
        matr_txt = " ".join([t for x, t in r["items"] if 48 <= x < 82]).strip()
        nome_txt = " ".join([t for x, t in r["items"] if 82 <= x < 305]).strip()
        eq_txt = " ".join([t for x, t in r["items"] if 305 <= x < 415]).strip()
        tempo_txt = " ".join([t for x, t in r["items"] if 415 <= x < 460]).strip()
        rec_txt = " ".join([t for x, t in r["items"] if x >= 512]).strip()

        full_line = limpar_homoglifos_gregos(f"{col_txt} {matr_txt} {nome_txt} {eq_txt}").upper()

        if "PROVA" in full_line and ("METROS" in full_line or "REVEZAMENTO" in full_line) and "RECORDE" not in full_line:
            p_cand = normalizar_prova_estrita(full_line)
            if p_cand:
                prova_atual = p_cand
                eh_revezamento = "REVEZAMENTO" in full_line or "Rev." in prova_atual

        if col_txt.upper().startswith("FAIXA"):
            fx_raw = limpar_homoglifos_gregos(f"{col_txt} {matr_txt} {nome_txt}").upper()
            if "PRÉ" in fx_raw or "PRE" in fx_raw:
                faixa_atual = "PRÉ-MASTER"
            else:
                m_f = re.search(r'(\d{2,3})', fx_raw)
                if m_f and int(m_f.group(1)) >= 20:
                    faixa_atual = f"{m_f.group(1)}+"

        is_result_row = bool(prova_atual and re.match(r'^(\d{1,2}[°º]|N/C|DQL)$', col_txt.strip(), re.IGNORECASE))
        if is_result_row:
            col_clean = col_txt.strip().upper()
            col_num = 0 if col_clean in ["N/C", "DQL"] else int(re.sub(r'\D', '', col_clean))

            m_mat_split = re.match(r'^(\d{3,7})\s*(.*)$', matr_txt)
            if m_mat_split:
                matricula = m_mat_split.group(1)
                if m_mat_split.group(2):
                    nome_txt = (m_mat_split.group(2) + " " + nome_txt).strip()
            else:
                matricula = ""

            rec_match = re.search(r'\b(RSP|RS|RB)\b', rec_txt.upper())
            rec_flag = f"Recorde ({rec_match.group(1)})" if rec_match else ""

            integrantes = []
            k = idx + 1
            while k < len(rows):
                rk = rows[k]
                k_col = " ".join([t for x, t in rk["items"] if x < 48]).strip()
                k_mat = " ".join([t for x, t in rk["items"] if 48 <= x < 82]).strip()
                k_nom = " ".join([t for x, t in rk["items"] if 82 <= x < 305]).strip()
                k_full = limpar_homoglifos_gregos(f"{k_col} {k_mat} {k_nom}").upper()
                if re.match(r'^(\d{1,2}[°º]|N/C|DQL)$', k_col, re.IGNORECASE) or k_col.upper().startswith("FAIXA") or ("PROVA" in k_full and "METROS" in k_full):
                    break
                if any(h in k_full for h in ["CAMPEONATO PAULISTA", "TROFÉU", "TROFEU", "RESULTADOS", "ABMN COMPETIÇÃO", "VISITE NOSSO SITE", "COL. MATR."]):
                    k += 1
                    continue
                if eh_revezamento and k_mat:
                    atl_sub = normalizar_nome_atleta(f"{k_mat} {k_nom}")
                    if atl_sub != "Atleta Desconhecido" and atl_sub not in integrantes:
                        integrantes.append(atl_sub)
                k += 1

            tempo_final = padronizar_tempo_string(tempo_txt) if tempo_txt else ("DQL" if col_clean == "DQL" else "Ausente")
            col_final = col_num if tempo_para_segundos(tempo_final) is not None else 0

            eq_upper = limpar_homoglifos_gregos(eq_txt).upper()
            if "VINHEDO" in eq_upper or "VINHEDO" in limpar_homoglifos_gregos(nome_txt).upper():
                if eh_revezamento:
                    vinhedo_rows.append({"Data": data_evento, "Campeonato": "Paulista", "Local/Etapa": nome_evento, "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": "EQUIPE SEL VINHEDO", "Categoria": faixa_atual, "Colocacao": col_final, "Tempo": tempo_final, "Pontos": 0.0, "Recorde": rec_flag, "Integrantes": " / ".join(integrantes)})
                    for atl in integrantes:
                        vinhedo_rows.append({"Data": data_evento, "Campeonato": "Paulista", "Local/Etapa": nome_evento, "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": atl, "Categoria": faixa_atual, "Colocacao": col_final, "Tempo": tempo_final, "Pontos": 0.0, "Recorde": rec_flag, "Integrantes": " / ".join(integrantes)})
                else:
                    atl_of = normalizar_nome_atleta(nome_txt)
                    if atl_of != "Atleta Desconhecido":
                        vinhedo_rows.append({"Data": data_evento, "Campeonato": "Paulista", "Local/Etapa": nome_evento, "Prova": prova_atual, "Tipo_Prova": "Individual", "Atleta": atl_of, "Categoria": faixa_atual, "Colocacao": col_final, "Tempo": tempo_final, "Pontos": 0.0, "Recorde": rec_flag, "Integrantes": ""})
            else:
                if not eh_revezamento and tempo_para_segundos(tempo_final) is not None and matricula:
                    nome_adv = limpar_nome_adversario(nome_txt)
                    eq_adv = limpar_homoglifos_gregos(eq_txt).strip() or "Paulista"
                    if len(nome_adv) >= 3:
                        adversarios_rows.append({"Data": data_evento, "Campeonato": "Paulista", "Local/Etapa": nome_evento, "Prova": prova_atual, "Categoria": faixa_atual, "Matricula": matricula, "Atleta": nome_adv, "Equipe": eq_adv[:35], "Colocacao": col_final, "Tempo": tempo_final, "Pontos": 0.0, "Recorde": rec_flag})

            idx = k
            continue
        idx += 1

    return pd.DataFrame(vinhedo_rows), pd.DataFrame(adversarios_rows)

def processar_pdf_arn(rows, nome_evento, data_evento):
    vinhedo_rows, adversarios_rows = [], []
    prova_atual = None
    categoria_atual = "Master"

    for idx, r in enumerate(rows):
        linha = limpar_homoglifos_gregos(r["text"]).strip()
        linha_upper = linha.upper()

        if linha_upper.startswith("PROVA:"):
            p_cand = normalizar_prova_estrita(linha)
            if p_cand:
                prova_atual = p_cand

        if linha_upper.startswith("CATEGORIA:"):
            categoria_atual = normalizar_categoria(linha)

        if not prova_atual:
            continue

        pos_str = "".join([t for x, t in r["items"] if x < 45]).strip()
        mat_str = "".join([t for x, t in r["items"] if 45 <= x < 82]).strip()
        if re.match(r'^\d{1,3}$', pos_str) and re.match(r'^\d{5,7}$', mat_str):
            pos_raw = int(pos_str)
            nome_part = limpar_homoglifos_gregos(" ".join([t for x, t in r["items"] if 82 <= x < 270])).strip()
            eq_part = limpar_homoglifos_gregos(" ".join([t for x, t in r["items"] if 270 <= x < 445])).strip()
            res_part = limpar_homoglifos_gregos(" ".join([t for x, t in r["items"] if x >= 445])).strip()

            # Separa caso equipe longa encoste no tempo (ex: "Parnaiba00:47:64")
            m_colado = re.search(r'(d?\d{1,2}:\d{2}:\d{1,2})', eq_part, re.IGNORECASE)
            if m_colado:
                res_part = m_colado.group(1) + " " + res_part
                eq_part = eq_part[:m_colado.start()].strip()

            prox_l = limpar_homoglifos_gregos(rows[idx + 1]["text"]).strip().upper() if idx + 1 < len(rows) else ""
            eh_descl = ("DESCL" in res_part.upper()) or prox_l.startswith("DESCL") or bool(re.search(r'\bd\d{1,2}:\d{2}', res_part, re.IGNORECASE))
            eh_rec = ("RECORD" in res_part.upper()) or (prox_l == "RECORD")
            rec_flag = "Recorde ARN" if eh_rec else ""

            if pos_raw == 999 or "9:99:99" in res_part or "99:99:99" in res_part or not res_part:
                tempo_final, colocacao = "Ausente", 0
            elif eh_descl:
                tempo_final, colocacao = "DQL", 0
            else:
                colocacao = pos_raw
                m_t_arn = re.search(r'(\d{1,2}:\d{2}:\d{2})', res_part)
                tempo_final = padronizar_tempo_string(m_t_arn.group(1)) if m_t_arn else "S/T"

            if "VINHEDO" in eq_part.upper():
                atl_of = normalizar_nome_atleta(nome_part)
                if atl_of != "Atleta Desconhecido":
                    vinhedo_rows.append({"Data": data_evento, "Campeonato": "ARN", "Local/Etapa": nome_evento, "Prova": prova_atual, "Tipo_Prova": "Individual", "Atleta": atl_of, "Categoria": categoria_atual, "Colocacao": colocacao, "Tempo": tempo_final, "Pontos": 0.0, "Recorde": rec_flag, "Integrantes": ""})
            else:
                if tempo_para_segundos(tempo_final) is not None and "25m" not in prova_atual:
                    nome_adv = limpar_nome_adversario(nome_part)
                    if len(nome_adv) >= 3:
                        adversarios_rows.append({"Data": data_evento, "Campeonato": "ARN", "Local/Etapa": nome_evento, "Prova": prova_atual, "Categoria": categoria_atual, "Matricula": mat_str, "Atleta": nome_adv, "Equipe": (eq_part[:35] or "ARN"), "Colocacao": colocacao, "Tempo": tempo_final, "Pontos": 0.0, "Recorde": rec_flag})

    return pd.DataFrame(vinhedo_rows), pd.DataFrame(adversarios_rows)

# ==========================================
# --- RESUMO AUTOMÁTICO PÓS-IMPORTAÇÃO (WHATSAPP) ---
# ==========================================
def gerar_resumo_pos_importacao(df_hist_antigo, df_novos):
    if df_novos.empty:
        return pd.DataFrame(), ""

    resumo_rows = []
    etapas_unicas = df_novos[["Data", "Campeonato", "Local/Etapa"]].drop_duplicates()
    linhas_zap = []

    for _, et in etapas_unicas.iterrows():
        dt_et, camp_et, loc_et = et["Data"], et["Campeonato"], et["Local/Etapa"]
        sub_et = df_novos[(df_novos["Data"] == dt_et) & (df_novos["Campeonato"] == camp_et) & (df_novos["Local/Etapa"] == loc_et)]

        med_et = sub_et[((sub_et["Tipo_Prova"] == "Individual") | (sub_et["Atleta"] == "EQUIPE SEL VINHEDO")) & (sub_et["Colocacao"].isin([1, 2, 3]))]
        o, p, b = (med_et["Colocacao"] == 1).sum(), (med_et["Colocacao"] == 2).sum(), (med_et["Colocacao"] == 3).sum()
        pts_et = sub_et["Pontos"].sum() if camp_et == "UNAMI" else 0.0
        recs_et = sub_et[((sub_et["Tipo_Prova"] == "Individual") | (sub_et["Atleta"] == "EQUIPE SEL VINHEDO")) & (sub_et["Recorde"].str.strip() != "")]

        linhas_zap.append(f"🏊‍♂️ *Resumo SEL Vinhedo — {loc_et} ({dt_et})*")
        cab_med = f"🏅 Medalhas: {o}🥇 {p}🥈 {b}🥉"
        if camp_et == "UNAMI":
            cab_med += f" | 🏆 Pontos: *{pts_et:.2f}*".replace(".", ",")
        if len(recs_et) > 0:
            cab_med += f" | ⚡ Recordes: *{len(recs_et)}*"
        linhas_zap.append(cab_med)
        linhas_zap.append("")

        ind_et = sub_et[sub_et["Tipo_Prova"] == "Individual"].sort_values(["Atleta", "Prova"])
        for _, r in ind_et.iterrows():
            atl, prv, tp = r["Atleta"], r["Prova"], r["Tempo"]
            col_txt = formatar_colocacao_medalha(r["Colocacao"])
            seg_novo = tempo_para_segundos(tp)

            hist_ant = df_hist_antigo[(df_hist_antigo["Atleta"] == atl) & (df_hist_antigo["Prova"] == prv) & (df_hist_antigo["Tipo_Prova"] == "Individual")].copy()
            hist_ant["Seg"] = hist_ant["Tempo"].apply(tempo_para_segundos)
            segs_ant = sorted(hist_ant["Seg"].dropna().tolist())

            if seg_novo is None:
                destaque = tp
            elif not segs_ant:
                destaque = "🆕 1ª Marca Oficial!"
            else:
                melhor_ant = segs_ant[0]
                dif = seg_novo - melhor_ant
                if seg_novo < melhor_ant:
                    destaque = f"🔥 NOVO PR! (-{abs(dif):.2f}s)"
                elif seg_novo == melhor_ant:
                    destaque = "⚡ Igualou PR!"
                else:
                    pos_h = sum(1 for s in segs_ant if s < seg_novo) + 1
                    if pos_h == 2:
                        destaque = f"🥈 2º Melhor Tempo (+{dif:.2f}s)"
                    elif pos_h == 3:
                        destaque = f"🥉 3º Melhor Tempo (+{dif:.2f}s)"
                    else:
                        destaque = f"+{dif:.2f}s do PR"

            if r["Recorde"]:
                destaque = f"⚡ {r['Recorde']} • {destaque}"

            resumo_rows.append({"Etapa": loc_et, "Data": dt_et, "Atleta": atl, "Prova": prv, "Colocação": col_txt, "Tempo": tp, "Análise PR": destaque})
            linhas_zap.append(f"• *{atl.title()}* ({prv}): {col_txt} | *{tp}* — {destaque}")

        rev_et = sub_et[sub_et["Atleta"] == "EQUIPE SEL VINHEDO"]
        if not rev_et.empty:
            linhas_zap.append("")
            linhas_zap.append("🤝 *Revezamentos:*")
            for _, rv in rev_et.iterrows():
                col_rv = formatar_colocacao_medalha(rv["Colocacao"])
                linhas_zap.append(f"• {rv['Prova']} ({rv['Categoria']}): {col_rv} | *{rv['Tempo']}* ({rv['Integrantes']})")
        linhas_zap.append("\n" + "-" * 25 + "\n")

    return pd.DataFrame(resumo_rows), "\n".join(linhas_zap).strip()

# ==========================================
# --- MENU LATERAL DE NAVEGAÇÃO ---
# ==========================================
with st.sidebar:
    st.markdown(f"## 🏊‍♂️ {APP_NOME}")
    st.caption(f"Versão {APP_VERSAO} • Atualizado em {APP_ATUALIZACAO}")
    if github_configurado():
        st.success("☁️ Auto-Save GitHub: Ativo")
    else:
        st.warning("⚠️ Auto-Save GitHub: Configure os Secrets")
    st.markdown("---")
    tela_selecionada = st.radio(
        "Escolha o que deseja ver:",
        [
            "🏆 Medalhas & Pontos da Equipe",
            "🏊 Meus Tempos & Medalhas",
            "🎯 Onde Tenho Mais Chances?",
            "⏱️ Melhores Tempos da Equipe",
            "🚀 Montar Revezamento",
            "✍️ Lançar Tempos de Treino",
            "📤 Importar PDFs de Provas",
            "🗄️ Backup, Elenco & Tabela"
        ]
    )
    st.markdown("---")

with st.expander("🧭 Não sabe onde clicar? Veja o que tem em cada aba"):
    st.markdown("""
- **🏆 Medalhas & Pontos da Equipe:** Pontuação geral de Vinhedo na UNAMI, quadro de medalhas por atleta, revezamentos e mural de recordes.
- **🏊 Meus Tempos & Medalhas:** Seus recordes pessoais (PRs), suas medalhas, pontos e gráfico de evolução.
- **🎯 Onde Tenho Mais Chances?:** Compara seus tempos com os rivais da sua faixa etária para mostrar suas provas mais fortes.
- **⏱️ Melhores Tempos da Equipe:** Consulta os melhores tempos da equipe em cada prova.
- **🚀 Montar Revezamento:** Simula as melhores formações de revezamento e mostra o histórico oficial da equipe.
- **✍️ Lançar Tempos de Treino:** Tabela estilo Excel para o treinador lançar a prova e o tempo de cada nadador e gerar o resumo de PRs do dia.
- **📤 Importar PDFs de Provas:** Importação separada por tipo (UNAMI Individual, UNAMI Revezamentos, Paulista e ARN) com gravação automática no GitHub.
- **🗄️ Backup, Elenco & Tabela:** Gerenciar atletas ativos/inativos, cadastrar novos nadadores, baixar backup CSV ou editar a tabela.
    """)

# ------------------------------------------
# TELA 1: MEDALHAS & PONTOS DA EQUIPE
# ------------------------------------------
if tela_selecionada == "🏆 Medalhas & Pontos da Equipe":
    st.title("🏆 Medalhas, Recordes & Troféu UNAMI")

    if not df_historico.empty:
        anos_disp = obter_anos_ordenados(df_historico)
        opcoes_ano = anos_disp + ["Todos os Anos"]
        camps_disp = ["Todos os Campeonatos"] + sorted([c for c in df_historico["Campeonato"].unique() if c and c != "Treino"])

        col_f1, col_f2 = st.columns(2)
        with col_f1: ano_sel = st.selectbox("Temporada (Padrão: Ano mais recente):", opcoes_ano, index=0)
        with col_f2: camp_sel = st.selectbox("Campeonato (Medalhas & Participação):", camps_disp, index=0)

        df_filtrado = df_historico[df_historico["Campeonato"] != "Treino"].copy()
        df_filtrado["Ano_Str"] = pd.to_datetime(df_filtrado["Data"], format="%d/%m/%Y", errors="coerce").dt.year.fillna(0).astype(int).astype(str)

        if ano_sel != "Todos os Anos":
            df_filtrado = df_filtrado[df_filtrado["Ano_Str"] == ano_sel]

        df_unami_ano = df_filtrado[df_filtrado["Campeonato"] == "UNAMI"]
        pontos_gerais_vinhedo = df_unami_ano["Pontos"].sum()
        pts_ind_vinhedo = df_unami_ano[df_unami_ano["Tipo_Prova"] == "Individual"]["Pontos"].sum()
        pts_rev_vinhedo = df_unami_ano[df_unami_ano["Tipo_Prova"] == "Revezamento"]["Pontos"].sum()

        df_med = df_filtrado if camp_sel == "Todos os Campeonatos" else df_filtrado[df_filtrado["Campeonato"] == camp_sel]

        df_equipe_meds = df_med[((df_med["Tipo_Prova"] == "Individual") | (df_med["Atleta"] == "EQUIPE SEL VINHEDO")) & (df_med["Colocacao"].isin([1, 2, 3]))]
        ouros_eq = (df_equipe_meds["Colocacao"] == 1).sum()
        pratas_eq = (df_equipe_meds["Colocacao"] == 2).sum()
        bronzes_eq = (df_equipe_meds["Colocacao"] == 3).sum()
        recordes_eq = df_med[((df_med["Tipo_Prova"] == "Individual") | (df_med["Atleta"] == "EQUIPE SEL VINHEDO")) & (df_med["Recorde"].str.strip() != "")]

        df_pessoas_periodo = df_med[df_med["Atleta"] != "EQUIPE SEL VINHEDO"]

        st.markdown(f"### 🏅 Desempenho Consolidado SEL Vinhedo — {ano_sel}")
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("🏆 Pontos UNAMI", f"{pontos_gerais_vinhedo:.2f}".replace(".", ","), f"Ind: {pts_ind_vinhedo:.1f} | Rev: {pts_rev_vinhedo:.1f}")
        k2.metric("🥇 Ouros", int(ouros_eq))
        k3.metric("🥈 Pratas", int(pratas_eq))
        k4.metric("🥉 Bronzes", int(bronzes_eq))
        k5.metric("⚡ Recordes", len(recordes_eq))
        k6.metric("🏊 Atletas no Período", df_pessoas_periodo["Atleta"].nunique())

        st.markdown("---")

        if not df_unami_ano.empty:
            st.markdown("#### 📈 Pontuação de SEL Vinhedo por Etapa (UNAMI)")
            df_etapas = df_unami_ano.groupby(["Data", "Local/Etapa", "Tipo_Prova"])["Pontos"].sum().unstack(fill_value=0).reset_index()
            if "Individual" not in df_etapas.columns: df_etapas["Individual"] = 0.0
            if "Revezamento" not in df_etapas.columns: df_etapas["Revezamento"] = 0.0
            df_etapas["Total Etapa"] = df_etapas["Individual"] + df_etapas["Revezamento"]
            st.dataframe(df_etapas[["Data", "Local/Etapa", "Individual", "Revezamento", "Total Etapa"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown(f"#### 🏆 Corrida pelo Troféu: Pontos UNAMI ({ano_sel})")
            df_pts_pessoa = df_unami_ano[df_unami_ano["Atleta"] != "EQUIPE SEL VINHEDO"]
            if not df_pts_pessoa.empty:
                rank_pts = df_pts_pessoa.groupby("Atleta").agg(Pontos_UNAMI=("Pontos", "sum"), Provas_UNAMI=("Prova", "count")).reset_index().sort_values(by=["Pontos_UNAMI", "Provas_UNAMI"], ascending=[False, True])
                rank_pts["Pos"] = [f"🏆 {i}º" if i <= 3 else f"{i}º" for i in range(1, len(rank_pts) + 1)]
                st.dataframe(rank_pts[["Pos", "Atleta", "Pontos_UNAMI", "Provas_UNAMI"]].rename(columns={"Pontos_UNAMI": "Pontos", "Provas_UNAMI": "Provas"}), use_container_width=True, hide_index=True)
            else: st.info("Sem pontos da UNAMI registrados para este filtro.")

        with col_r2:
            st.markdown(f"#### 🥇 Quadro de Medalhas por Atleta ({camp_sel})")
            if not df_pessoas_periodo.empty:
                atletas_com_provas = sorted(df_pessoas_periodo["Atleta"].unique())
                linhas_quadro = []
                for atl in atletas_com_provas:
                    sub = df_pessoas_periodo[df_pessoas_periodo["Atleta"] == atl]
                    o_tot, p_tot, b_tot = (sub["Colocacao"] == 1).sum(), (sub["Colocacao"] == 2).sum(), (sub["Colocacao"] == 3).sum()
                    o_rev, p_rev, b_rev = ((sub["Colocacao"] == 1) & (sub["Tipo_Prova"] == "Revezamento")).sum(), ((sub["Colocacao"] == 2) & (sub["Tipo_Prova"] == "Revezamento")).sum(), ((sub["Colocacao"] == 3) & (sub["Tipo_Prova"] == "Revezamento")).sum()
                    recs = (sub["Recorde"].str.strip() != "").sum()
                    linhas_quadro.append({"Atleta": atl, "🥇 Ouro": int(o_tot), "🥈 Prata": int(p_tot), "🥉 Bronze": int(b_tot), "Total": int(o_tot + p_tot + b_tot), "Sendo Rev.": f"{o_rev}🥇 {p_rev}🥈 {b_rev}🥉" if (o_rev + p_rev + b_rev) > 0 else "-", "⚡ Rec.": int(recs)})
                st.dataframe(pd.DataFrame(linhas_quadro).sort_values(by=["🥇 Ouro", "🥈 Prata", "🥉 Bronze", "Atleta"], ascending=[False, False, False, True]), use_container_width=True, hide_index=True)
            else: st.info("Nenhuma prova registrada neste filtro.")

        st.markdown("---")
        st.markdown(f"#### 🤝 Quadro de Medalhas & Resultados — Revezamentos SEL Vinhedo ({ano_sel})")
        df_rev_equipe = df_med[df_med["Atleta"] == "EQUIPE SEL VINHEDO"].copy()
        if not df_rev_equipe.empty:
            c_rev1, c_rev2, c_rev3, c_rev4 = st.columns(4)
            c_rev1.metric("🥇 Ouros em Rev.", int((df_rev_equipe["Colocacao"] == 1).sum()))
            c_rev2.metric("🥈 Pratas em Rev.", int((df_rev_equipe["Colocacao"] == 2).sum()))
            c_rev3.metric("🥉 Bronzes em Rev.", int((df_rev_equipe["Colocacao"] == 3).sum()))
            c_rev4.metric("Total Pódios Rev.", int(df_rev_equipe["Colocacao"].isin([1, 2, 3]).sum()))
            df_rev_exibir = df_rev_equipe.copy()
            df_rev_exibir["Colocação"] = df_rev_exibir["Colocacao"].apply(formatar_colocacao_medalha)
            st.dataframe(df_rev_exibir[["Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Colocação", "Tempo", "Pontos", "Integrantes", "Recorde"]], use_container_width=True, hide_index=True)
        else: st.info("Nenhum revezamento registrado neste período.")

        if not recordes_eq.empty:
            st.markdown("---")
            st.markdown(f"#### ⚡ Mural de Recordes Quebrados ({ano_sel})")
            df_rec_show = recordes_eq.copy()
            df_rec_show["Atleta / Equipe"] = df_rec_show.apply(lambda r: f"EQUIPE ({r['Integrantes']})" if r["Atleta"] == "EQUIPE SEL VINHEDO" and r["Integrantes"] else r["Atleta"], axis=1)
            st.dataframe(df_rec_show[["Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Atleta / Equipe", "Tempo", "Recorde"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown(f"### 📊 Estatísticas de Participação & Delegação ({ano_sel})")
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st.markdown("#### 🏊 Volume de Caídas na Água por Atleta")
            if not df_pessoas_periodo.empty:
                assiduidade = df_pessoas_periodo["Atleta"].value_counts().reset_index()
                assiduidade.columns = ["Atleta", "Nº de Provas (Ind + Rev)"]
                st.dataframe(assiduidade, use_container_width=True, hide_index=True)
        with col_st2:
            st.markdown("#### 🏟️ Tamanho da Delegação por Etapa")
            if not df_pessoas_periodo.empty:
                delegacao = df_pessoas_periodo.groupby(["Data", "Campeonato", "Local/Etapa"])["Atleta"].nunique().reset_index()
                delegacao.columns = ["Data", "Campeonato", "Competição", "Atletas Presentes"]
                st.dataframe(delegacao.sort_values("Atletas Presentes", ascending=False), use_container_width=True, hide_index=True)
    else: st.info("A base está vazia. Vá em '📤 Importar PDFs de Provas' para carregar os resultados.")

# ------------------------------------------
# TELA 2: MEUS TEMPOS & MEDALHAS
# ------------------------------------------
elif tela_selecionada == "🏊 Meus Tempos & Medalhas":
    st.title("🏊 Meus Tempos, Medalhas & Evolução")
    if not df_historico.empty:
        df_atletas_only = df_historico[df_historico["Atleta"] != "EQUIPE SEL VINHEDO"].copy()
        todos_com_hist = sorted(df_atletas_only["Atleta"].unique())
        ativos_com_hist = [a for a in todos_com_hist if a in ATLETAS_ATIVOS]

        col_a0, col_a1, col_a2 = st.columns([1, 2, 1])
        with col_a0:
            mostrar_inativos = st.checkbox("Incluir ex-atletas", value=False)
        lista_atletas = todos_com_hist if mostrar_inativos else (ativos_com_hist or todos_com_hist)
        anos_disp = obter_anos_ordenados(df_atletas_only)

        with col_a1: atleta_sel = st.selectbox("Selecione o Atleta:", lista_atletas, key="consulta_atleta")
        with col_a2: ano_atleta_sel = st.selectbox("Temporada (Cards e Histórico):", anos_disp + ["Todos os Anos"], index=0)

        df_atleta = df_atletas_only[df_atletas_only["Atleta"] == atleta_sel].copy()
        df_atleta["Segundos"] = df_atleta["Tempo"].apply(tempo_para_segundos)
        df_atleta["Data_Dt"] = pd.to_datetime(df_atleta["Data"], format="%d/%m/%Y", errors="coerce")
        df_atleta["Ano_Str"] = df_atleta["Data_Dt"].dt.year.fillna(0).astype(int).astype(str)

        df_atleta_periodo = df_atleta if ano_atleta_sel == "Todos os Anos" else df_atleta[df_atleta["Ano_Str"] == ano_atleta_sel]

        pts_atleta = df_atleta_periodo[df_atleta_periodo["Campeonato"] == "UNAMI"]["Pontos"].sum()
        ouros_a = (df_atleta_periodo["Colocacao"] == 1).sum()
        pratas_a = (df_atleta_periodo["Colocacao"] == 2).sum()
        bronzes_a = (df_atleta_periodo["Colocacao"] == 3).sum()
        recs_a = (df_atleta_periodo["Recorde"].str.strip() != "").sum()

        st.markdown(f"#### 🏅 Conquistas de {atleta_sel} ({ano_atleta_sel})")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🏆 Pontos UNAMI", f"{pts_atleta:.2f}".replace(".", ","))
        m2.metric("🥇 Ouros", int(ouros_a))
        m3.metric("🥈 Pratas", int(pratas_a))
        m4.metric("🥉 Bronzes", int(bronzes_a))
        m5.metric("⚡ Recordes", int(recs_a))

        st.markdown("---")
        st.markdown("#### ⏱️ Melhores Tempos Históricos (PRs Individuais - Todos os Anos)")
        df_validos_ind = df_atleta[(df_atleta["Segundos"].notna()) & (df_atleta["Tipo_Prova"] == "Individual")].copy()
        if not df_validos_ind.empty:
            idx_melhores = df_validos_ind.groupby("Prova")["Segundos"].idxmin()
            df_prs = df_validos_ind.loc[idx_melhores, ["Prova", "Tempo", "Data", "Local/Etapa", "Campeonato"]].rename(columns={"Tempo": "Tempo Recorde"})
            st.dataframe(df_prs.style.set_properties(**{'background-color': '#fffbe6', 'color': '#333333', 'border-color': 'white', 'font-weight': 'bold'}), use_container_width=True, hide_index=True)
        else: st.warning("Este atleta não possui marcas individuais numéricas válidas.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"#### 📅 Histórico Completo de Participações ({ano_atleta_sel})")
        df_cronologico = df_atleta_periodo.sort_values(by="Data_Dt", ascending=False).copy()
        df_cronologico["Colocação"] = df_cronologico["Colocacao"].apply(formatar_colocacao_medalha)
        st.dataframe(df_cronologico[["Data", "Campeonato", "Local/Etapa", "Tipo_Prova", "Prova", "Categoria", "Colocação", "Tempo", "Pontos", "Recorde"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 📈 Gráfico de Evolução (Segundos - Provas Individuais)")
        if not df_validos_ind.empty:
            df_grafico = df_validos_ind.dropna(subset=["Data_Dt"]).sort_values("Data_Dt")
            provas_disp = df_grafico["Prova"].unique()
            abas_graficos = st.tabs(list(provas_disp))
            for i, prova_nome in enumerate(provas_disp):
                with abas_graficos[i]:
                    st.line_chart(df_grafico[df_grafico["Prova"] == prova_nome].set_index("Data_Dt")[["Segundos"]], use_container_width=True)
    else: st.info("O histórico está vazio.")

# ------------------------------------------
# TELA 3: ONDE TENHO MAIS CHANCES? (RADAR DE PROVAS)
# ------------------------------------------
elif tela_selecionada == "🎯 Onde Tenho Mais Chances?":
    st.title("🎯 Onde Tenho Mais Chances?")
    st.markdown("Compara os seus **melhores tempos (PRs)** com os tempos reais dos **adversários da sua faixa etária**.")

    if df_historico.empty or df_adversarios.empty:
        st.info("Importe os PDFs na aba '📤 Importar PDFs de Provas' para ativar o comparador.")
    else:
        todos_com_hist = sorted([a for a in df_historico["Atleta"].unique() if a != "EQUIPE SEL VINHEDO"])
        ativos_com_hist = [a for a in todos_com_hist if a in ATLETAS_ATIVOS]
        lista_atletas = ativos_com_hist if ativos_com_hist else todos_com_hist
        camps_radar_disp = ["Todos"] + sorted([c for c in df_adversarios["Campeonato"].unique() if c])

        col_r1, col_r2, col_r3, col_r4 = st.columns([2, 1, 1, 1])
        with col_r1: atleta_radar = st.selectbox("Selecione o Atleta:", lista_atletas)
        with col_r2: ano_ref_radar = st.number_input("Ano da Competição:", min_value=2025, max_value=2030, value=2027)
        with col_r3: janela_tempo = st.selectbox("Janela de Adversários:", ["Últimos 12 meses", "Últimos 6 meses", "Toda a base"], index=0)
        with col_r4: camp_radar = st.selectbox("Campeonato:", camps_radar_disp, index=0)

        faixa_atleta = obter_faixa_etaria_atleta(atleta_radar, ano_ref_radar)
        faixa_anterior = obter_faixa_etaria_atleta(atleta_radar, ano_ref_radar - 1)
        msg_cat = f"👤 **{atleta_radar}** | Idade em {ano_ref_radar}: **{calcular_idade(atleta_radar, ano_ref_radar)} anos** → Categoria: **{faixa_atleta}**"
        if faixa_atleta != faixa_anterior:
            msg_cat += f" 🎉 *(Acabou de subir da {faixa_anterior} — entra como o mais jovem da nova faixa!)*"
        st.info(msg_cat)

        df_atl_ind = df_historico[(df_historico["Atleta"] == atleta_radar) & (df_historico["Tipo_Prova"] == "Individual")].copy()
        df_atl_ind["Segundos"] = df_atl_ind["Tempo"].apply(tempo_para_segundos)
        df_atl_ind = df_atl_ind.dropna(subset=["Segundos"])

        df_adv_base = df_adversarios.copy()
        df_adv_base["Data_Dt"] = pd.to_datetime(df_adv_base["Data"], format="%d/%m/%Y", errors="coerce")

        if janela_tempo != "Toda a base" and not df_adv_base["Data_Dt"].dropna().empty:
            dias = 365 if janela_tempo == "Últimos 12 meses" else 183
            df_adv_base = df_adv_base[df_adv_base["Data_Dt"] >= (df_adv_base["Data_Dt"].max() - timedelta(days=dias))]

        if camp_radar != "Todos":
            df_adv_base = df_adv_base[df_adv_base["Campeonato"] == camp_radar]

        df_adv_base["Segundos"] = df_adv_base["Tempo"].apply(tempo_para_segundos)
        df_adv_base = df_adv_base.dropna(subset=["Segundos"])

        if df_atl_ind.empty:
            st.warning("Este atleta ainda não possui tempos individuais válidos para simular.")
        else:
            prs_atleta = df_atl_ind.groupby("Prova")["Segundos"].min().reset_index()
            analise_provas = []

            for _, row in prs_atleta.iterrows():
                df_comp = df_adv_base[(df_adv_base["Prova"] == row["Prova"]) & (df_adv_base["Categoria"] == faixa_atleta)].copy()
                if df_comp.empty:
                    continue

                df_comp["Chave_Rival"] = df_comp.apply(lambda r: r["Matricula"] if str(r["Matricula"]).strip() != "" else r["Atleta"], axis=1)
                melhores_adv = df_comp.groupby("Chave_Rival")["Segundos"].min().sort_values()
                rivais_mais_rapidos = (melhores_adv < row["Segundos"]).sum()
                posicao_estimada = rivais_mais_rapidos + 1

                tempo_ouro = melhores_adv.iloc[0]
                tempo_bronze = melhores_adv.iloc[min(2, len(melhores_adv) - 1)]

                if posicao_estimada == 1: chance_txt = "🔥 Favorito ao Ouro"
                elif posicao_estimada <= 3: chance_txt = "🏅 Zona de Pódio"
                elif (row["Segundos"] - tempo_bronze) <= 1.5: chance_txt = "⚡ Na briga (<1.5s do pódio)"
                else: chance_txt = "📊 Intermediário"

                analise_provas.append({"Prova": row["Prova"], "Seu PR": segundos_para_tempo(row["Segundos"]), "Posição Simulada": f"{posicao_estimada}º de {len(melhores_adv) + 1}", "Pos_Num": posicao_estimada, "Cenário": chance_txt, "Melhor Rival (Ouro)": segundos_para_tempo(tempo_ouro), "Dif. p/ Ouro": f"{(row['Segundos'] - tempo_ouro):+.2f}s", "Corte Pódio (3º)": segundos_para_tempo(tempo_bronze), "Dif. p/ Bronze": f"{(row['Segundos'] - tempo_bronze):+.2f}s"})

            if analise_provas:
                df_radar = pd.DataFrame(analise_provas).sort_values(by=["Pos_Num", "Dif. p/ Bronze"])
                st.markdown(f"### 📊 Ranking das Suas Melhores Provas na Categoria {faixa_atleta}")
                st.dataframe(df_radar.drop(columns=["Pos_Num"]), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("#### 🔍 Quem são seus principais rivais em cada prova?")
                prova_detalhe = st.selectbox("Escolha uma prova para ver os tempos dos adversários:", df_radar["Prova"].tolist())
                df_rivais_det = df_adv_base[(df_adv_base["Prova"] == prova_detalhe) & (df_adv_base["Categoria"] == faixa_atleta)].copy()
                df_rivais_det["Chave_Rival"] = df_rivais_det.apply(lambda r: r["Matricula"] if str(r["Matricula"]).strip() != "" else r["Atleta"], axis=1)
                df_top_rivais = df_rivais_det.loc[df_rivais_det.groupby("Chave_Rival")["Segundos"].idxmin()].sort_values("Segundos").head(15)
                df_top_rivais["Rank"] = range(1, len(df_top_rivais) + 1)
                st.dataframe(df_top_rivais[["Rank", "Atleta", "Equipe", "Tempo", "Local/Etapa", "Data"]], use_container_width=True, hide_index=True)
            else:
                st.warning(f"Ainda não há registros de adversários na categoria **{faixa_atleta}** nesta janela de tempo.")

# ------------------------------------------
# TELA 4: MELHORES TEMPOS DA EQUIPE
# ------------------------------------------
elif tela_selecionada == "⏱️ Melhores Tempos da Equipe":
    st.title("⏱️ Melhores Tempos da Equipe por Prova")
    if not df_historico.empty:
        col_mt1, col_mt2 = st.columns([3, 1])
        with col_mt2:
            inc_ex_mt = st.checkbox("Incluir ex-atletas", value=False, key="mt_ex")
        df_ind = df_historico[df_historico["Tipo_Prova"] == "Individual"].copy()
        if not inc_ex_mt and ATLETAS_ATIVOS:
            df_ind = df_ind[df_ind["Atleta"].isin(ATLETAS_ATIVOS)]

        lista_provas = sorted(df_ind["Prova"].unique())
        with col_mt1:
            prova_sel = st.selectbox("Selecione a Prova para consultar os tempos da equipe:", lista_provas, key="treinador_prova_sel")

        df_prova_rank = df_ind[df_ind["Prova"] == prova_sel].copy()
        df_prova_rank["Segundos"] = df_prova_rank["Tempo"].apply(tempo_para_segundos)
        df_prova_rank = df_prova_rank.dropna(subset=["Segundos"])

        if not df_prova_rank.empty:
            df_top_atletas = df_prova_rank.loc[df_prova_rank.groupby("Atleta")["Segundos"].idxmin()].sort_values("Segundos")
            df_top_atletas["Ordem"] = range(1, len(df_top_atletas) + 1)
            st.dataframe(df_top_atletas[["Ordem", "Atleta", "Tempo", "Categoria", "Local/Etapa", "Data"]], use_container_width=True, hide_index=True)
        else:
            st.warning("Não há tempos válidos registrados para esta prova.")
    else:
        st.info("A base está vazia.")

# ------------------------------------------
# TELA 5: MONTAR REVEZAMENTO (APENAS ATIVOS)
# ------------------------------------------
elif tela_selecionada == "🚀 Montar Revezamento":
    st.title("🚀 Simulador & Histórico de Revezamentos")

    col_rev1, col_rev2, col_rev3 = st.columns(3)
    with col_rev1: tipo_rev = st.radio("Estilo do Revezamento:", ["4x50m Livre", "4x50m Medley"], horizontal=True)
    with col_rev2: genero_rev = st.radio("Categoria de Gênero:", ["Feminino", "Masculino", "Misto"], horizontal=True)
    with col_rev3: ano_rev = st.number_input("Ano base para idade:", min_value=2025, max_value=2030, value=2027)

    lista_base_rev = ATLETAS_ATIVOS if ATLETAS_ATIVOS else sorted(list(ANOS_NASCIMENTO.keys()))
    if genero_rev == "Masculino": lista_filtrada = [a for a in lista_base_rev if GENERO_ATLETAS.get(a) == 'M']
    elif genero_rev == "Feminino": lista_filtrada = [a for a in lista_base_rev if GENERO_ATLETAS.get(a) == 'F']
    else: lista_filtrada = lista_base_rev

    atletas_pool = st.multiselect("Selecione os atletas ativos disponíveis para compor:", lista_filtrada, default=lista_filtrada[:6] if len(lista_filtrada) >= 6 else lista_filtrada)

    st.markdown("#### ✍️ Ajuste Manual de Tempos (Baseado nos PRs)")
    if atletas_pool:
        df_tempos_base = pd.DataFrame({"Atleta": atletas_pool})
        if tipo_rev == "4x50m Livre":
            df_tempos_base["Livre"] = [obter_pr_revezamento(df_historico, a, "50m Livre")[1] for a in atletas_pool]
        else:
            df_tempos_base["Costas"] = [obter_pr_revezamento(df_historico, a, "50m Costas")[1] for a in atletas_pool]
            df_tempos_base["Peito"] = [obter_pr_revezamento(df_historico, a, "50m Peito")[1] for a in atletas_pool]
            df_tempos_base["Borboleta"] = [obter_pr_revezamento(df_historico, a, "50m Borboleta")[1] for a in atletas_pool]
            df_tempos_base["Livre"] = [obter_pr_revezamento(df_historico, a, "50m Livre")[1] for a in atletas_pool]

        df_editado = st.data_editor(df_tempos_base, use_container_width=True, hide_index=True, disabled=["Atleta"], key="editor_rev_tempos")

        def extrair_string(valor):
            if isinstance(valor, (list, tuple, set, pd.Series)): return str(valor[0])
            return str(valor)

        if st.button("Gerar Melhores Combinações"):
            dict_tempos = df_editado.set_index("Atleta").to_dict(orient="index")
            homens, mulheres = [a for a in atletas_pool if GENERO_ATLETAS.get(a) == 'M'], [a for a in atletas_pool if GENERO_ATLETAS.get(a) == 'F']
            combinacoes_validas = []
            if genero_rev == "Masculino": combinacoes_validas = list(itertools.combinations(homens, 4))
            elif genero_rev == "Feminino": combinacoes_validas = list(itertools.combinations(mulheres, 4))
            elif genero_rev == "Misto": combinacoes_validas = [m + f for m in list(itertools.combinations(homens, 2)) for f in list(itertools.combinations(mulheres, 2))]

            if not combinacoes_validas: st.error(f"Não há atletas suficientes selecionados para formar um revezamento ({genero_rev}).")
            else:
                resultados = []
                if tipo_rev == "4x50m Livre":
                    for combo in combinacoes_validas:
                        tempos = [tempo_para_segundos(dict_tempos.get(extrair_string(a), {}).get("Livre", "S/T")) or float('inf') for a in combo]
                        if float('inf') not in tempos:
                            idade_total = sum(calcular_idade(extrair_string(a), ano_rev) for a in combo)
                            resultados.append({"Equipe": " / ".join([extrair_string(a) for a in combo]), "Categoria": obter_categoria_revezamento(idade_total), "Soma Idades": idade_total, "Tempo Total (Seg)": sum(tempos), "Tempo Estimado": segundos_para_tempo(sum(tempos))})
                else:
                    for combo in combinacoes_validas:
                        combo_limpo, melhor_t, melhor_ordem = [extrair_string(a) for a in combo], float('inf'), None
                        for perm in itertools.permutations(combo_limpo):
                            soma = (tempo_para_segundos(dict_tempos.get(perm[0], {}).get("Costas", "S/T")) or float('inf')) + (tempo_para_segundos(dict_tempos.get(perm[1], {}).get("Peito", "S/T")) or float('inf')) + (tempo_para_segundos(dict_tempos.get(perm[2], {}).get("Borboleta", "S/T")) or float('inf')) + (tempo_para_segundos(dict_tempos.get(perm[3], {}).get("Livre", "S/T")) or float('inf'))
                            if soma < melhor_t: melhor_t, melhor_ordem = soma, perm
                        if melhor_t != float('inf'):
                            idade_total = sum(calcular_idade(a, ano_rev) for a in combo_limpo)
                            resultados.append({"Equipe": f"Costas: {melhor_ordem[0]} / Peito: {melhor_ordem[1]} / Borboleta: {melhor_ordem[2]} / Livre: {melhor_ordem[3]}", "Categoria": obter_categoria_revezamento(idade_total), "Soma Idades": idade_total, "Tempo Total (Seg)": melhor_t, "Tempo Estimado": segundos_para_tempo(melhor_t)})

                if resultados:
                    df_res = pd.DataFrame(resultados)
                    for cat in sorted(df_res["Categoria"].unique(), reverse=True):
                        st.markdown(f"### 🏆 Categoria {cat} ({genero_rev})")
                        st.table(df_res[df_res["Categoria"] == cat].sort_values("Tempo Total (Seg)").head(3)[["Tempo Estimado", "Soma Idades", "Equipe"]])
                else: st.warning("Preencha marcas válidas na tabela de ajustes para gerar as simulações.")
    else: st.info("Selecione atletas para iniciar a montagem do revezamento.")

    st.markdown("---")
    st.markdown("### 📜 Histórico Real de Revezamentos SEL Vinhedo")
    if not df_historico.empty:
        df_rev_hist = df_historico[df_historico["Atleta"] == "EQUIPE SEL VINHEDO"].copy()
        if not df_rev_hist.empty:
            df_rev_hist["Data_Dt"] = pd.to_datetime(df_rev_hist["Data"], format="%d/%m/%Y", errors="coerce")
            df_rev_hist = df_rev_hist.sort_values("Data_Dt", ascending=False)
            df_rev_hist["Colocação"] = df_rev_hist["Colocacao"].apply(formatar_colocacao_medalha)
            st.dataframe(df_rev_hist[["Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Colocação", "Tempo", "Pontos", "Integrantes", "Recorde"]], use_container_width=True, hide_index=True)
        else: st.info("Nenhum revezamento oficial importado ainda.")

# ------------------------------------------
# TELA 6: LANÇAR TEMPOS DE TREINO (PROVA POR LINHA + RESUMO PRs)
# ------------------------------------------
elif tela_selecionada == "✍️ Lançar Tempos de Treino":
    st.title("✍️ Lançamento Rápido de Treinos (Tomada de Tempo)")
    st.markdown("Escolha a **Prova** na linha de cada atleta ativo que nadou (a partir de **50m**), digite o **Tempo** e clique em **Salvar Tempos** para gravar e ver o resumo de PRs na hora.")

    OPCOES_PROVAS_TREINO = [
        "50m Livre", "50m Costas", "50m Peito", "50m Borboleta",
        "100m Livre", "100m Costas", "100m Peito", "100m Borboleta", "100m Medley",
        "200m Livre", "200m Costas", "200m Peito", "200m Borboleta", "200m Medley",
        "400m Livre", "800m Livre", "1500m Livre"
    ]

    col_t1, col_t2, col_t3 = st.columns([1, 2, 1])
    with col_t1: data_treino = st.date_input("1. Data do Treino:")
    with col_t2: local_treino = st.text_input("2. Descrição / Local:", value="Tomada de Tempo - Treino")
    with col_t3: prova_padrao_linha = st.selectbox("3. Prova padrão na grade:", OPCOES_PROVAS_TREINO)

    atletas_chamada = ATLETAS_ATIVOS if ATLETAS_ATIVOS else sorted(list(ANOS_NASCIMENTO.keys()))
    df_grade_treino = pd.DataFrame({
        "Atleta": atletas_chamada,
        "Gênero": ["Fem" if GENERO_ATLETAS.get(a) == "F" else "Masc" for a in atletas_chamada],
        "Prova": [prova_padrao_linha for _ in atletas_chamada],
        "Tempo (ex: 29.45 ou 1:05.10)": ["" for _ in atletas_chamada]
    })

    st.markdown("#### 📋 Selecione a Prova na linha e digite o Tempo apenas de quem nadou:")
    df_treino_editado = st.data_editor(
        df_grade_treino,
        use_container_width=True,
        hide_index=True,
        disabled=["Atleta", "Gênero"],
        column_config={
            "Prova": st.column_config.SelectboxColumn("Prova (50m+)", options=OPCOES_PROVAS_TREINO, required=True)
        },
        height=550,
        key=f"grade_rapida_treinador_{prova_padrao_linha}"
    )

    if st.button("💾 Salvar Todos os Tempos Preenchidos", type="primary"):
        novas_linhas_treino, erros_formato = [], []
        ano_treino = data_treino.year
        data_str_t = data_treino.strftime("%d/%m/%Y")

        for _, row in df_treino_editado.iterrows():
            t_raw = str(row["Tempo (ex: 29.45 ou 1:05.10)"]).strip()
            if t_raw and t_raw.lower() != "nan":
                t_pad = padronizar_tempo_string(t_raw)
                if tempo_para_segundos(t_pad) is None:
                    erros_formato.append(f"{row['Atleta']} ({t_raw})")
                else:
                    prova_completa = f"{row['Prova']} {row['Gênero']}"
                    novas_linhas_treino.append({
                        "Data": data_str_t, "Campeonato": "Treino", "Local/Etapa": local_treino,
                        "Prova": prova_completa, "Tipo_Prova": "Individual", "Atleta": row["Atleta"],
                        "Categoria": obter_faixa_etaria_atleta(row["Atleta"], ano_treino),
                        "Colocacao": 0, "Tempo": t_pad, "Pontos": 0.0, "Recorde": "", "Integrantes": ""
                    })

        if erros_formato:
            st.error(f"⚠️ Verifique o formato do tempo (use ponto para centésimos, ex: `31.45` ou `1:12.30`): {', '.join(erros_formato)}")
        elif novas_linhas_treino:
            df_novos_t = pd.DataFrame(novas_linhas_treino)
            df_total = pd.concat([df_historico, df_novos_t], ignore_index=True).drop_duplicates(
                subset=["Data", "Campeonato", "Prova", "Tipo_Prova", "Atleta", "Tempo"]
            )
            ok_gh, _ = salvar_csv_persistente(df_total, CSV_FILE, f"Treino salvo ({data_str_t})")

            resumo_dia = []
            linhas_zap = [f"🏊‍♂️ *Tomada de Tempo — {data_str_t}* ({local_treino})", ""]
            for item in novas_linhas_treino:
                atl, prv, tp_novo = item["Atleta"], item["Prova"], item["Tempo"]
                seg_novo = tempo_para_segundos(tp_novo)

                hist_ant = df_historico[(df_historico["Atleta"] == atl) & (df_historico["Prova"] == prv) & (df_historico["Tipo_Prova"] == "Individual")].copy()
                hist_ant["Seg"] = hist_ant["Tempo"].apply(tempo_para_segundos)
                segs_ant = sorted(hist_ant["Seg"].dropna().tolist())

                if not segs_ant:
                    status_pr, melhor_ant_str, dif_str = "🆕 1ª Marca Registrada!", "-", "-"
                else:
                    melhor_ant = segs_ant[0]
                    melhor_ant_str = segundos_para_tempo(melhor_ant)
                    dif = seg_novo - melhor_ant
                    dif_str = f"{dif:+.2f}s"
                    if seg_novo < melhor_ant:
                        status_pr = f"🔥 NOVO PR! (Baixou {abs(dif):.2f}s)"
                    elif seg_novo == melhor_ant:
                        status_pr = "⚡ Igualou o PR!"
                    else:
                        pos_hist = sum(1 for s in segs_ant if s < seg_novo) + 1
                        if pos_hist == 2: status_pr = f"🥈 2º Melhor Tempo! (+{dif:.2f}s do PR)"
                        elif pos_hist == 3: status_pr = f"🥉 3º Melhor Tempo! (+{dif:.2f}s do PR)"
                        else: status_pr = f"⏱️ {pos_hist}º melhor marca (+{dif:.2f}s do PR)"

                resumo_dia.append({"Atleta": atl, "Prova": prv, "Tempo Hoje": tp_novo, "Melhor Anterior": melhor_ant_str, "Dif. p/ PR": dif_str, "Resultado": status_pr})
                linhas_zap.append(f"• *{atl.title()}* ({prv}): *{tp_novo}* — {status_pr}")

            st.session_state["ultimo_resumo_treino"] = pd.DataFrame(resumo_dia)
            st.session_state["ultimo_texto_zap"] = "\n".join(linhas_zap)
            msg_extra = " e sincronizado no GitHub!" if ok_gh else "!"
            st.success(f"✅ {len(novas_linhas_treino)} tempo(s) salvos{msg_extra}")
            st.rerun()
        else:
            st.warning("Nenhum tempo foi digitado na tabela.")

    if "ultimo_resumo_treino" in st.session_state and not st.session_state["ultimo_resumo_treino"].empty:
        st.markdown("---")
        st.markdown("### 🏅 Resumo do Treino Salvo (Comparativo com Histórico)")
        st.dataframe(st.session_state["ultimo_resumo_treino"], use_container_width=True, hide_index=True)
        with st.expander("📲 Copiar Resumo Formatado para o WhatsApp da Equipe", expanded=True):
            st.code(st.session_state.get("ultimo_texto_zap", ""), language="text")

# ------------------------------------------
# TELA 7: IMPORTAR PDFS POR CANAL ESPECIALIZADO + RESUMO WHATSAPP
# ------------------------------------------
elif tela_selecionada == "📤 Importar PDFs de Provas":
    st.title("📤 Importar Resultados Oficiais (Por Tipo)")
    st.markdown("Escolha o **tipo de arquivo** abaixo para subir vários PDFs de uma vez com leitura por coordenadas visuais. Ao confirmar, os dados são salvos automaticamente no GitHub e geram o resumo para o WhatsApp.")

    canal_import = st.radio(
        "1. Qual tipo de PDF você vai subir agora?",
        [
            "🏊 UNAMI — Provas Individuais (Lê atletas, pontos, recordes e rivais 50m+)",
            "🤝 UNAMI — Revezamentos (Lê equipes, integrantes e pontos de revezamento)",
            "🏆 Paulista — FAP/ABMN (Lê individual e revezamentos pelas colunas)",
            "⏱️ ARN / Chegada.net (Etapas Master ARN)"
        ]
    )

    if "UNAMI — Provas Individuais" in canal_import: tipo_canal = "UNAMI_IND"
    elif "UNAMI — Revezamentos" in canal_import: tipo_canal = "UNAMI_REV"
    elif "Paulista" in canal_import: tipo_canal = "PAULISTA"
    else: tipo_canal = "ARN"

    uploaded_files = st.file_uploader(
        "2. Selecione ou arraste todos os PDFs desse tipo aqui:",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"uploader_{tipo_canal}"
    )

    if uploaded_files:
        if st.button("🔍 1. Analisar PDFs e Gerar Prévia"):
            previa_resumo, vinhedo_buffer, adv_buffer = [], [], []
            barra = st.progress(0)
            for idx_f, arq_pdf in enumerate(uploaded_files):
                try:
                    pdf_bytes = arq_pdf.read()
                    tol = 2.5 if tipo_canal == "PAULISTA" else 3.5
                    rows_doc = extrair_linhas_pdfminer(pdf_bytes, tol_y=tol)
                    rows_p1 = [r for r in rows_doc if r["page"] == 1]
                    data_det, nome_det = detectar_metadados_visuais(rows_p1, arq_pdf.name)

                    if tipo_canal == "UNAMI_IND":
                        df_v, df_adv = processar_unami_individual(rows_doc, nome_det, data_det)
                        camp_label = "UNAMI"
                    elif tipo_canal == "UNAMI_REV":
                        df_v, df_adv = processar_unami_revezamentos(rows_doc, nome_det, data_det)
                        camp_label = "UNAMI"
                    elif tipo_canal == "PAULISTA":
                        df_v, df_adv = processar_pdf_paulista(rows_doc, nome_det, data_det)
                        camp_label = "Paulista"
                    else:
                        df_v, df_adv = processar_pdf_arn(rows_doc, nome_det, data_det)
                        camp_label = "ARN"

                    pts_soma = df_v["Pontos"].sum() if not df_v.empty else 0.0
                    recs_qtd = (df_v[((df_v["Tipo_Prova"] == "Individual") | (df_v["Atleta"] == "EQUIPE SEL VINHEDO"))]["Recorde"].str.strip() != "").sum() if not df_v.empty else 0
                    previa_resumo.append({
                        "Arquivo": arq_pdf.name, "Campeonato": camp_label, "Data": data_det,
                        "Nome da Etapa": nome_det, "Reg. Vinhedo": len(df_v),
                        "Pontos UNAMI": float(pts_soma), "Recordes": int(recs_qtd), "Rivais": len(df_adv)
                    })
                    if not df_v.empty:
                        df_v["_Arquivo_Origem"] = arq_pdf.name
                        vinhedo_buffer.append(df_v)
                    if not df_adv.empty:
                        df_adv["_Arquivo_Origem"] = arq_pdf.name
                        adv_buffer.append(df_adv)
                except Exception as e:
                    previa_resumo.append({"Arquivo": arq_pdf.name, "Campeonato": "ERRO", "Data": "", "Nome da Etapa": str(e), "Reg. Vinhedo": 0, "Pontos UNAMI": 0.0, "Recordes": 0, "Rivais": 0})
                barra.progress((idx_f + 1) / len(uploaded_files))

            st.session_state["previa_resumo"] = pd.DataFrame(previa_resumo)
            st.session_state["vinhedo_buffer"] = pd.concat(vinhedo_buffer, ignore_index=True) if vinhedo_buffer else pd.DataFrame()
            st.session_state["adv_buffer"] = pd.concat(adv_buffer, ignore_index=True) if adv_buffer else pd.DataFrame()

    if "previa_resumo" in st.session_state and not st.session_state["previa_resumo"].empty:
        st.markdown("---")
        st.markdown("### 🔎 Prévia da Importação (Você pode corrigir Data, Campeonato ou Nome da Etapa abaixo antes de salvar)")
        df_previa_edit = st.data_editor(
            st.session_state["previa_resumo"],
            use_container_width=True,
            hide_index=True,
            disabled=["Arquivo", "Reg. Vinhedo", "Pontos UNAMI", "Recordes", "Rivais"],
            key="editor_previa_lote"
        )

        if st.button("✅ 2. Confirmar e Salvar Tudo na Base", type="primary"):
            mapa_meta = df_previa_edit.set_index("Arquivo").to_dict(orient="index")
            df_v_final = st.session_state.get("vinhedo_buffer", pd.DataFrame()).copy()
            df_adv_final = st.session_state.get("adv_buffer", pd.DataFrame()).copy()

            if not df_v_final.empty:
                for arq_nome, meta in mapa_meta.items():
                    mask = df_v_final["_Arquivo_Origem"] == arq_nome
                    df_v_final.loc[mask, "Campeonato"] = meta["Campeonato"]
                    df_v_final.loc[mask, "Data"] = normalizar_data_str(meta["Data"])
                    df_v_final.loc[mask, "Local/Etapa"] = meta["Nome da Etapa"]
                    if meta["Campeonato"] != "UNAMI":
                        df_v_final.loc[mask, "Pontos"] = 0.0
                df_v_final = df_v_final.drop(columns=["_Arquivo_Origem"])

                df_res_imp, txt_zap_imp = gerar_resumo_pos_importacao(df_historico, df_v_final)
                st.session_state["ultimo_resumo_import"] = df_res_imp
                st.session_state["ultimo_zap_import"] = txt_zap_imp

                df_total = pd.concat([df_historico, df_v_final], ignore_index=True).drop_duplicates(
                    subset=["Data", "Campeonato", "Prova", "Tipo_Prova", "Atleta", "Tempo"]
                )
                salvar_csv_persistente(df_total, CSV_FILE, f"Importação Vinhedo ({tipo_canal})")

            if not df_adv_final.empty:
                for arq_nome, meta in mapa_meta.items():
                    mask = df_adv_final["_Arquivo_Origem"] == arq_nome
                    df_adv_final.loc[mask, "Campeonato"] = meta["Campeonato"]
                    df_adv_final.loc[mask, "Data"] = normalizar_data_str(meta["Data"])
                    df_adv_final.loc[mask, "Local/Etapa"] = meta["Nome da Etapa"]
                df_adv_final = df_adv_final.drop(columns=["_Arquivo_Origem"])
                df_adv_total = pd.concat([df_adversarios, df_adv_final], ignore_index=True).drop_duplicates(
                    subset=["Data", "Campeonato", "Prova", "Categoria", "Matricula", "Atleta", "Tempo"]
                )
                salvar_csv_persistente(df_adv_total, CSV_ADVERSARIOS, f"Importação Rivais ({tipo_canal})")

            del st.session_state["previa_resumo"], st.session_state["vinhedo_buffer"], st.session_state["adv_buffer"]
            st.success("🎉 Todos os arquivos foram salvos e sincronizados!")
            st.rerun()

    if "ultimo_resumo_import" in st.session_state and not st.session_state["ultimo_resumo_import"].empty:
        st.markdown("---")
        st.markdown("### 🏅 Resumo dos Resultados Importados (Análise de PRs & Medalhas)")
        st.dataframe(st.session_state["ultimo_resumo_import"], use_container_width=True, hide_index=True)
        with st.expander("📲 Copiar Resumo da Competição para o WhatsApp da Equipe", expanded=True):
            st.code(st.session_state.get("ultimo_zap_import", ""), language="text")

# ------------------------------------------
# TELA 8: BACKUP, ELENCO & EDITAR TABELA
# ------------------------------------------
elif tela_selecionada == "🗄️ Backup, Elenco & Tabela":
    st.title("🗄️ Backup, Elenco & Edição Administrativa")

    st.markdown("### 👥 Cadastro & Status do Elenco (Ativos vs. Ex-Atletas)")
    st.markdown("Altere o **Status** (`Ativo` ou `Inativo`) ou adicione novos atletas que entrarem em 2027 direto na tabela abaixo:")
    df_elenco_edit = st.data_editor(
        df_elenco,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=["Ativo", "Inativo"], required=True),
            "Genero": st.column_config.SelectboxColumn("Gênero", options=["F", "M"], required=True)
        },
        key="editor_elenco_admin"
    )
    if st.button("💾 Salvar Alterações no Elenco"):
        ok_gh, _ = salvar_csv_persistente(df_elenco_edit, CSV_ELENCO, "Atualização do Elenco")
        st.success("✅ Cadastro do elenco atualizado" + (" e salvo no GitHub!" if ok_gh else "!"))
        st.rerun()

    st.markdown("---")
    col_download, col_upload = st.columns(2)
    with col_download:
        st.markdown("### 📥 Salvar Backups Locais (CSV)")
        if not df_historico.empty:
            st.download_button(label="Baixar historico_vinhedo.csv", data=df_historico.to_csv(index=False).encode('utf-8'), file_name='historico_vinhedo.csv', mime='text/csv')
        if not df_adversarios.empty:
            st.download_button(label="Baixar base_adversarios.csv", data=df_adversarios.to_csv(index=False).encode('utf-8'), file_name='base_adversarios.csv', mime='text/csv')
        st.download_button(label="Baixar elenco_vinhedo.csv", data=df_elenco.to_csv(index=False).encode('utf-8'), file_name='elenco_vinhedo.csv', mime='text/csv')

    with col_upload:
        st.markdown("### 🔄 Restaurar Backup (Vinhedo)")
        backup_file = st.file_uploader("Envie o backup (CSV):", type=["csv"], key="uploader_backup_admin")
        if backup_file is not None:
            if st.button("Restaurar Base de Dados"):
                try:
                    df_bkp = pd.read_csv(backup_file, dtype=str)
                    salvar_csv_persistente(df_bkp, CSV_FILE, "Restauração de Backup")
                    st.success("Base restaurada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo: {e}")

    st.markdown("---")
    with st.expander("🗑️ Zerar Bases para Reimportação Limpa"):
        st.warning("Isso limpa os resultados atuais (mantendo o cadastro de elenco) localmente e no GitHub para você subir os PDFs limpos.")
        if st.button("Confirmar: Limpar Resultados Agora"):
            salvar_csv_persistente(pd.DataFrame(columns=COLUNAS_VINHEDO), CSV_FILE, "Zerar base Vinhedo para reimportação limpa")
            salvar_csv_persistente(pd.DataFrame(columns=COLUNAS_ADVERSARIOS), CSV_ADVERSARIOS, "Zerar base Rivais para reimportação limpa")
            st.success("Bases zeradas localmente e no GitHub!")
            st.rerun()

    st.markdown("---")
    st.markdown("### ✏️ Edição Direta da Base de Resultados (Clique duas vezes para editar)")
    if not df_historico.empty:
        df_edit_admin = st.data_editor(df_historico, use_container_width=True, num_rows="dynamic", key="admin_editor_vinhedo")
        if st.button("💾 Salvar Alterações na Tabela"):
            ok_gh, _ = salvar_csv_persistente(df_edit_admin, CSV_FILE, "Edição manual da base de resultados")
            st.success("Alterações salvas" + (" e sincronizadas no GitHub!" if ok_gh else "!"))
            st.rerun()
