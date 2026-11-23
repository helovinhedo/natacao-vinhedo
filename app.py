import streamlit as st
import pandas as pd
import re
import os
import itertools
from datetime import datetime, timedelta
from pypdf import PdfReader

st.set_page_config(page_title="Painel Natação Master - SEL Vinhedo", layout="wide")

# ==========================================
# --- DICIONÁRIOS DE UNIFICAÇÃO ---
# ==========================================
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
    "LARISSA": "LARISSA LIMA SOATO",
    "WAGNER": "WAGNER ALVES BONADIO"
}

ANO_ATUAL = 2026
ANOS_NASCIMENTO = {
    "CLAUDIA COLAMARINO": 1969, "BRUNA LIMA VICENTE": 1988, "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR": 1982,
    "RAFAEL HIROSHI BRAZ DA SILVA": 1987, "HELOÍSA DE SOUSA EVANGELISTA": 1989, "TALITA CLIOGIA BARBOSA": 1994,
    "CALEBE RAMOS RIBEIRO": 1987, "RAFAEL MELLO": 1988, "ANA REGINA OLIVAN LIMONGI": 1984,
    "LARA FERREIRA DE SOUZA TONIN": 1987, "FABIUS LUIZ PALARO": 1975, "HELENA KIYOKA KOBAYASHI NABEIRO": 1976,
    "TIAGO BERNAL": 1979, "VOLKER PENK": 1967, "MURILO SANTOS": 2004, "LUCIANO DIAS GOBI": 1973,
    "EDUARDO TREVISAN GONCALVES": 1976, "MATIAS KOLBE": 1981, "MARIANE DE MORAES QUIRINO": 1992,
    "LARISSA LIMA SOATO": 2001, "WAGNER ALVES BONADIO": 1958
}

GENERO_ATLETAS = {
    "CLAUDIA COLAMARINO": "F", "BRUNA LIMA VICENTE": "F", "ÁLVARO LOUZADA DE OLIVEIRA JUNIOR": "M",
    "RAFAEL HIROSHI BRAZ DA SILVA": "M", "HELOÍSA DE SOUSA EVANGELISTA": "F", "TALITA CLIOGIA BARBOSA": "F",
    "CALEBE RAMOS RIBEIRO": "M", "RAFAEL MELLO": "M", "ANA REGINA OLIVAN LIMONGI": "F",
    "LARA FERREIRA DE SOUZA TONIN": "F", "FABIUS LUIZ PALARO": "M", "HELENA KIYOKA KOBAYASHI NABEIRO": "F",
    "TIAGO BERNAL": "M", "VOLKER PENK": "M", "MURILO SANTOS": "M", "LUCIANO DIAS GOBI": "M",
    "EDUARDO TREVISAN GONCALVES": "M", "MATIAS KOLBE": "M", "MARIANE DE MORAES QUIRINO": "F",
    "LARISSA LIMA SOATO": "F", "WAGNER ALVES BONADIO": "M"
}

EQUIPES_CONHECIDAS_REGEX = (
    r'SEL VINHEDO|VINHEDE|ARARAQUARENSE|LIMEIRA MASTER|GRAN SAO JOAO|MASTER RIO CLARO|M\. RIO CLARO|'
    r'BAURU MASTER|SAO JOAO NATACAO|BARRA BONITA|CORPO & ENERGIA|CORPO E ENERGIA|NATA[ÇC][ÃA]O NENINHO|'
    r'CLUBE DE CAMPO|CC PIRACICABA|ACADEMIA PEDRO LEITE|PREF\.? VALINHOS|PREFEITURA DE VALINHOS|'
    r'VINHAS NATA[ÇC][ÃA]O|N1/RIBEIRAO|N1/RIB|T\.?C\.?\s*CAMPINAS|TCCAMPINAS|TENIS CLUBE CAMPINAS|'
    r'E\.?C\.?\s*BARBARENSE|ASS ATL[ÉE]TICA ARARENSE|VIVA ESPORTE|PERSONAL VI ROSA|CRIS BORGES|'
    r'SHARK SANTOS|MOLHA[ÇC][ÃA]O|APAN PAULISTA|LIGA CENTRAL|ACQUA TRAINING|BARDI SWIMMING|'
    r'OKUDA ASSESSORIA|EEF PMESP|C\.?T\.?\s*CATANDUVA|MASTERS CTC|1º DE MAIO|PINHEIROS|'
    r'AD SANTO ANDR[ÉE]|TNT SP|SMEC FRANCA|C\. MILITAR|HEBRAICA|PAINEIRAS|CUBO D|JUVENTUS|'
    r'BOTO COR DE ROSA|SOCIEDADE HIPICA|CLUBE PIRASSUNUNGA|CLUBE MOGIANO|GREMIO U SAO ROQUENSE|'
    r'ARRUDA TEAM|FREE PLAY|CAMPINEIRO REGATAS|BOTUCATUENSE|MASTER SANTO ANDRE|USSR/UNICAMP|AABB/SP|'
    r'PRIMCPPESP|CORTE\'?S|SPATIUM|FAST & FUN|CHIORO SWIM|R2 SPORTS|MOV/PG|GUS-SP|N1/ML|ORSELLI|BARDI & OKUDA'
)

# ==========================================
# --- FUNÇÕES DE PADRONIZAÇÃO E LIMPEZA ---
# ==========================================
def limpar_homoglifos_gregos(texto):
    """Converte caracteres gregos extraídos pelo pypdf (ex: ΑΝΑ -> ANA) para alfabeto latino."""
    if not isinstance(texto, str):
        return ""
    mapa = str.maketrans({
        "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I",
        "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T",
        "Υ": "Y", "Χ": "X", "α": "a", "ο": "o", "ρ": "p"
    })
    return texto.translate(mapa)

def calcular_idade(atleta, ano_ref=ANO_ATUAL):
    return ano_ref - ANOS_NASCIMENTO.get(atleta, ano_ref - 30)

def obter_faixa_etaria_atleta(atleta, ano_ref=ANO_ATUAL):
    idade = calcular_idade(atleta, ano_ref)
    if idade < 20:
        return "PRÉ-MASTER"
    faixa_base = (idade // 5) * 5
    return f"{faixa_base}+"

def obter_categoria_revezamento(soma_idades):
    if soma_idades >= 320: return "320+"
    elif soma_idades >= 280: return "280+"
    elif soma_idades >= 240: return "240+"
    elif soma_idades >= 200: return "200+"
    elif soma_idades >= 160: return "160+"
    elif soma_idades >= 120: return "120+"
    elif soma_idades >= 100: return "100+"
    else: return "80+"

def normalizar_nome_atleta(nome_bruto):
    if not isinstance(nome_bruto, str):
        return "Atleta Desconhecido"
    nome_upper = " ".join(limpar_homoglifos_gregos(nome_bruto).split()).upper()
    for chave, nome_oficial in DIC_ATLETAS.items():
        if re.search(rf'\b{re.escape(chave)}\b', nome_upper):
            return nome_oficial
    return "Atleta Desconhecido"

def limpar_nome_adversario(nome_bruto):
    if not isinstance(nome_bruto, str):
        return ""
    nome = limpar_homoglifos_gregos(nome_bruto)
    nome = re.sub(r'^\d+\s+', '', nome.strip())
    nome = re.sub(r'\|', ' ', nome)
    nome = re.sub(r'[^A-ZÀ-ÿa-z\s\.]', '', nome)
    nome = re.sub(r'\s+', ' ', nome).strip()
    return nome.title()

def normalizar_categoria(cat_str):
    if not isinstance(cat_str, str):
        return "Master"
    c = re.sub(r'[\{\}\^]', '', limpar_homoglifos_gregos(cat_str).upper()).strip()
    if "PRÉ" in c or "PRE" in c:
        return "PRÉ-MASTER"
    m = re.search(r'(\d{2,3})\s*\+?', c)
    if m:
        val = int(m.group(1))
        if val >= 20:
            return f"{val}+"
    return c if c else "Master"

def normalizar_data_str(data_str):
    if not isinstance(data_str, str) or not data_str.strip():
        return f"01/01/{ANO_ATUAL}"
    s = data_str.strip()
    dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.notna(dt):
        return dt.strftime("%d/%m/%Y")
    return s

def normalizar_prova(prova_str):
    if not isinstance(prova_str, str):
        return "Estilo Não Identificado"
    p = re.sub(r'\(\d{2}/\d{2}/\d{4}\)', '', limpar_homoglifos_gregos(prova_str).upper())

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
    return " ".join(prova_str.split())

def padronizar_tempo_string(tempo_str):
    if tempo_str is None or pd.isna(tempo_str):
        return "S/T"
    t_clean = str(tempo_str).lower().strip().replace(" ", "")
    if t_clean in ["s/t", "dql", "ausente", "n/c", ""]:
        return t_clean.upper() if t_clean in ["s/t", "dql"] else ("Ausente" if t_clean in ["ausente", "n/c"] else "S/T")
    t_clean = t_clean.replace("c", "").replace("s", ".").replace("m", ":").replace(",", ".")
    if t_clean.startswith("00:"):
        t_clean = t_clean[3:]
    if t_clean.count(":") == 2:
        partes_2 = t_clean.split(":")
        t_clean = f"{partes_2[0]}:{partes_2[1]}.{partes_2[2]}"
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
            return val if val > 0 else None
        else:
            segundos, centesimos = t_str.split(".")
            val = float(segundos) + float(centesimos) / 100
            return val if val > 0 else None
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

def obter_pr_revezamento(df, atleta, estilo_procurado):
    df_atleta = df[(df["Atleta"] == atleta) & (df["Tempo"].notna()) & (df["Tipo_Prova"] == "Individual")]
    df_prova = df_atleta[df_atleta["Prova"].str.contains(estilo_procurado, case=False, na=False)].copy()
    df_prova["Segundos"] = df_prova["Tempo"].apply(tempo_para_segundos)
    df_validos = df_prova[df_prova["Segundos"].notna()]
    if df_validos.empty:
        return float('inf'), "S/T"
    idx_min = df_validos["Segundos"].idxmin()
    return df_validos.loc[idx_min, "Segundos"], df_validos.loc[idx_min, "Tempo"]

# ==========================================
# --- DETECÇÃO AUTOMÁTICA DE METADADOS DO PDF ---
# ==========================================
def detectar_metadados_pdf(texto_pag1, nome_arquivo):
    texto_limpo = limpar_homoglifos_gregos(texto_pag1)
    texto_up = texto_limpo.upper()
    nome_arq_clean = os.path.splitext(nome_arquivo)[0]

    # Verifica UNAMI primeiro para não confundir com a equipe adversária "APAN Paulista"
    if "UNAMI" in texto_up or "UNIAO DE NADADORES" in texto_up or "UNIÃO DE NADADORES" in texto_up:
        campeonato = "UNAMI"
    elif any(k in texto_up for k in ["FEDERACAO AQUATICA PAULISTA", "FEDERAÇÃO AQUÁTICA PAULISTA", "ABMN", "SWIM IT UP", "2.87FAP", "2.72SP", "2.81"]):
        campeonato = "Paulista"
    else:
        campeonato = "UNAMI"

    cabecalho_limpo = re.sub(r'Record\s+\d{1,2}m\d{2}s\d{2}c?\s+\d{2}/\d{2}/\d{4}', '', texto_limpo[:1000], flags=re.IGNORECASE)

    data_detectada = None
    m_arq_data = re.search(r'(\d{2})[-/](\d{2})[-/](\d{4})', nome_arq_clean)
    if m_arq_data:
        data_detectada = f"{m_arq_data.group(1)}/{m_arq_data.group(2)}/{m_arq_data.group(3)}"
    else:
        datas_cab = re.findall(r'\b(\d{2}/\d{2}/\d{4})(?!\s+\d{2}:\d{2})', cabecalho_limpo)
        if datas_cab:
            data_detectada = datas_cab[0]
        else:
            datas_any = re.findall(r'\b(\d{2}/\d{2}/\d{4})\b', cabecalho_limpo)
            if datas_any:
                data_detectada = datas_any[0]

    if not data_detectada:
        data_detectada = f"01/01/{ANO_ATUAL}"

    nome_evento = ""
    linhas_p1 = [l.strip() for l in texto_limpo.split("\n") if l.strip()]

    if campeonato == "UNAMI":
        for l in linhas_p1[:12]:
            if any(k in l.upper() for k in ["TROFEU", "TROFÉU", "COPA", "TORNEIO", "ETAPA", "FESTIVAL", "CAMPEONATO"]):
                nome_evento = re.sub(r'\d{2}/\d{2}/\d{4}.*$', '', l).strip()
                break
        if not nome_evento and len(linhas_p1) >= 4:
            candidatos = [
                l for l in linhas_p1[:10]
                if not any(x in l.upper() for x in ["UNAMI", "NATAÇÃO MASTER", "RELATÓRIO", "MEDALHAS", "PROVA", "RECORD"])
                and not re.match(r'^[\d/: ]+$', l)
            ]
            if candidatos:
                nome_evento = " - ".join(candidatos[:2])
    else:
        for l in linhas_p1[:10]:
            if "CAMPEONATO" in l.upper() or "TROFÉU" in l.upper():
                nome_evento = l
                break

    if not nome_evento:
        nome_evento = re.sub(r'^\d{2}[-/]\d{2}[-/]\d{4}[_\-\s]*', '', nome_arq_clean).replace("_", " ").strip() or nome_arq_clean

    return campeonato, data_detectada, nome_evento
# ==========================================
# --- PARSERS UNIFICADOS E À PROVA DE ERROS ---
# ==========================================
def extrair_dados_adversario_unami(bloco_linhas):
    texto = " ".join(bloco_linhas[:4]).replace("|", " ")
    texto = re.sub(r'\s+', ' ', texto).strip()

    # Busca matrícula numérica (3 a 6 dígitos) mesmo que posição/pontos tenham quebrado antes
    m_id = re.search(r'(?:^|\s)(?:\d{1,2}\s+)?(?:\d{1,2},\d{2}\s+)?(0?\d{3,6})\s+([A-ZÀ-ÿ].+)$', texto)
    if m_id:
        matricula = m_id.group(1).lstrip("0") or m_id.group(1)
        resto = m_id.group(2)
    else:
        m_mat_only = re.search(r'\b(0?\d{4,6})\b', texto)
        matricula = (m_mat_only.group(1).lstrip("0") or m_mat_only.group(1)) if m_mat_only else ""
        resto = re.sub(r'^[\d\s,]+', '', texto)

    m_eq = re.search(rf'({EQUIPES_CONHECIDAS_REGEX})', resto, re.IGNORECASE)
    if m_eq:
        nome_raw = resto[:m_eq.start()].strip()
        equipe_raw = resto[m_eq.start():].split("00m")[0].split("01m")[0].split("02m")[0].split("03m")[0].split("Dist")[0].strip()
    else:
        nome_raw = re.split(r'\d{2}m\d{2}s|D\*D\*|ñ nadou|Ausente|Descla', resto, maxsplit=1)[0].strip()
        equipe_raw = "Equipe UNAMI"

    nome_limpo = limpar_nome_adversario(nome_raw)
    if len(nome_limpo) < 3:
        nome_limpo = f"Atleta #{matricula}" if matricula else "Adversário"

    return matricula, nome_limpo, (equipe_raw[:35] if equipe_raw else "Equipe UNAMI")


def processar_pdf_unami(pdf_file, nome_evento_manual, data_evento_manual):
    reader = PdfReader(pdf_file)
    vinhedo_rows = []
    adversarios_rows = []

    texto_completo = ""
    for page in reader.pages:
        texto_completo += limpar_homoglifos_gregos(page.extract_text() or "") + "\n"

    linhas = [l.strip() for l in texto_completo.split("\n") if l.strip()]

    prova_atual = "Não identificada"
    categoria_atual = "Master"
    eh_revezamento = False

    PADRAO_CATEGORIA_REV = r'(?:_[A-Z0-9]+[\s_]+|\b[A-Z]\s+)(80|100|120|160|200|240|280|320)\+'

    i = 0
    while i < len(linhas):
        linha = linhas[i]
        linha_upper = linha.upper()
        linha_cat_clean = re.sub(r'[\{\}\^]', '', linha_upper)

        # 1. Cabeçalho de Prova UNAMI
        if re.match(r'^PROVA(?:\s+\d+)?\b', linha_upper):
            bloco_cab = re.sub(r'[\{\}\^]', '', " ".join(linhas[i:min(i+8, len(linhas))]))
            if re.search(r'(?:4\s*X\s*)?(25|50|100|200|400|800|1500)\s*M', bloco_cab, re.IGNORECASE):
                prova_atual = normalizar_prova(bloco_cab)
                eh_revezamento = "4x" in prova_atual.lower()
                cat_match = re.search(r'\(?(\d{2,3}\+)\)?', bloco_cab)
                if cat_match:
                    categoria_atual = normalizar_categoria(cat_match.group(1))

        # 2. Categoria isolada
        if "RECORD" not in linha_cat_clean and "INDICE" not in linha_cat_clean and "VINHEDO" not in linha_cat_clean and "_" not in linha_cat_clean:
            cat_inline = re.search(r'(?:[A-P1I\$]\s*)?\((\d{2,3}\+)\)', linha_cat_clean)
            if cat_inline:
                categoria_atual = normalizar_categoria(cat_inline.group(1))
            elif re.search(r'\b(\d{2,3})\^?\{\+\}', linha_upper):
                m_brace = re.search(r'\b(\d{2,3})\^?\{\+\}', linha_upper)
                categoria_atual = normalizar_categoria(m_brace.group(1))

        # 3. REVEZAMENTO UNAMI
        eh_linha_equipe_rev = (
            ("VINHEDO" in linha_upper or "VINHEDE" in linha_upper)
            and normalizar_nome_atleta(linha) == "Atleta Desconhecido"
            and (
                eh_revezamento
                or bool(re.search(PADRAO_CATEGORIA_REV, linha_upper))
                or (i + 1 < len(linhas) and bool(re.search(PADRAO_CATEGORIA_REV, linhas[i+1].upper())))
            )
        )

        if eh_linha_equipe_rev:
            bloco_titulo_rev = (linha_upper + " " + (linhas[i+1].upper() if i + 1 < len(linhas) else ""))
            m_cat_rev = re.search(r'\b(80|100|120|160|200|240|280|320)\+', bloco_titulo_rev)
            if m_cat_rev:
                categoria_atual = normalizar_categoria(m_cat_rev.group(1))

            linhas_antes_rev = []
            for back in range(max(0, i-2), i):
                l_b = linhas[back]
                if not any(x in l_b.upper() for x in ["TOTAL:", "DIST", "PROVA", "RECORD"]) and not re.search(PADRAO_CATEGORIA_REV, l_b.upper()):
                    linhas_antes_rev.append(l_b)

            bloco_rev_linhas = linhas_antes_rev + [linha]
            k = i + 1
            while k < min(i + 25, len(linhas)):
                lk = linhas[k]
                lk_up = lk.upper()
                if k > i + 1 and (re.search(PADRAO_CATEGORIA_REV, lk_up) or re.match(r'^PROVA(?:\s+\d+)?\b', lk_up)):
                    break
                bloco_rev_linhas.append(lk)
                k += 1

            bloco_rev = " ".join(bloco_rev_linhas)
            bloco_rev_up = bloco_rev.upper()

            trecho_col = " ".join(linhas_antes_rev + [linha])
            m_col = re.search(r'(?:^|\s)(\d{1,2})\s+\d{3,6}\b', trecho_col)
            colocacao = int(m_col.group(1)) if m_col else 0

            if any(w in bloco_rev_up for w in ["DESCLA", "D*D*", "DQL", "ERRO CATEGORIA"]):
                tempo_final, pontos_final, colocacao = "DQL", 0.0, 0
            elif any(w in bloco_rev_up for w in ["AUSENTE", "Ñ NADOU"]):
                tempo_final, pontos_final, colocacao = "Ausente", 0.0, 0
            else:
                sem_parciais_rev = re.sub(r'\([^\)]*\)', '', bloco_rev)
                sem_parciais_rev = re.sub(r'\b(?:25|50|100|150|200|250|300|350|400)m\s+\d{1,2}m\d{2}s\d{2}c?', '', sem_parciais_rev, flags=re.IGNORECASE)
                m_tp = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)\s*(?<!\d)(\d{1,2},\d{2})(?!\d)', sem_parciais_rev, re.IGNORECASE)
                if m_tp:
                    tempo_final = padronizar_tempo_string(m_tp.group(1))
                    pontos_final = float(m_tp.group(2).replace(",", "."))
                else:
                    m_t_only = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)', sem_parciais_rev, re.IGNORECASE)
                    tempo_final = padronizar_tempo_string(m_t_only.group(1)) if m_t_only else "S/T"
                    m_p_only = re.search(r'(?<!\d)(\d{1,2},\d{2})(?!\d)', sem_parciais_rev)
                    pontos_final = float(m_p_only.group(1).replace(",", ".")) if m_p_only else 0.0

            eh_rec_rev = bool(re.search(r'(?:^|\b|\d)RECORD\b', bloco_rev, re.IGNORECASE)) or (pontos_final >= 25.0)
            recorde_flag = "Recorde UNAMI" if eh_rec_rev else ""

            integrantes_vinhedo = []
            for sub_l in bloco_rev_linhas[len(linhas_antes_rev)+1:]:
                atl_cand = normalizar_nome_atleta(sub_l)
                if atl_cand != "Atleta Desconhecido" and atl_cand not in integrantes_vinhedo:
                    integrantes_vinhedo.append(atl_cand)

            vinhedo_rows.append({
                "Data": data_evento_manual, "Campeonato": "UNAMI", "Local/Etapa": nome_evento_manual,
                "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": "EQUIPE SEL VINHEDO",
                "Categoria": categoria_atual, "Colocacao": colocacao, "Tempo": tempo_final,
                "Pontos": pontos_final, "Recorde": recorde_flag, "Integrantes": " / ".join(integrantes_vinhedo)
            })
            for atl in integrantes_vinhedo:
                vinhedo_rows.append({
                    "Data": data_evento_manual, "Campeonato": "UNAMI", "Local/Etapa": nome_evento_manual,
                    "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": atl,
                    "Categoria": categoria_atual, "Colocacao": colocacao, "Tempo": tempo_final,
                    "Pontos": 0.0, "Recorde": recorde_flag, "Integrantes": " / ".join(integrantes_vinhedo)
                })
            i = max(i + 1, k)
            continue

        # 4. INDIVIDUAL VINHEDO (Captura 15,00Record colado e não corta antes do tempo do próximo nadador)
        if not eh_revezamento and ("VINHEDO" in linha_upper or "VINHEDE" in linha_upper):
            bloco_nome = " ".join(linhas[max(0, i-3):min(i+4, len(linhas))])
            atleta_oficial = normalizar_nome_atleta(bloco_nome)

            if atleta_oficial != "Atleta Desconhecido":
                # Coleta até 2 linhas anteriores somente se pertencerem ao próprio atleta (antes de outro nadador)
                linhas_prev = []
                for back in range(i - 1, max(-1, i - 3), -1):
                    lb = linhas[back]
                    lb_up = lb.upper()
                    if re.search(rf'\b({EQUIPES_CONHECIDAS_REGEX})\b', lb_up) or re.search(r'\d{1,2}m\d{2}s\d{2}c?', lb, re.IGNORECASE):
                        break
                    linhas_prev.insert(0, lb)

                trecho_pos = " ".join(linhas_prev + [linha]).replace("|", " ")
                m_pos = re.search(r'(?:^|\s)(\d{1,2})\s+(?:\d{1,2},\d{2}\s+)?\d{2,6}(?:\s|$)', trecho_pos)
                if not m_pos:
                    m_pos = re.search(r'(?:^|\s)(\d{1,2})\s+[A-ZÀ-ÿ]', trecho_pos)
                colocacao = int(m_pos.group(1)) if m_pos else 0

                # Verifica se o próprio atleta já está Ausente/DQL logo nas linhas imediatas
                status_imediato = " ".join(linhas_prev + linhas[i:min(i+3, len(linhas))]).upper()
                eh_ausente_ou_dql = any(w in status_imediato for w in ["DESCLA", "D*D*", "DQL", "AUSENTE", "Ñ NADOU", "N/C"])

                linhas_seq = linhas_prev + [linha]
                if not eh_ausente_ou_dql:
                    tempos_finais_vistos = 0
                    for k in range(i + 1, min(i + 16, len(linhas))):
                        lk = linhas[k]
                        lk_up = lk.upper()
                        lk_cat = re.sub(r'[\{\}\^]', '', lk_up)
                        if re.match(r'^PROVA(?:\s+\d+)?\b', lk_up) or re.match(r'^(?:[A-P1I\$]\s*)?\(\d{2,3}\+\)', lk_cat):
                            break
                        # Para apenas quando chegar o TEMPO FINAL do próximo nadador (assim captura 15,00Record mesmo se vier após o nome do 2º lugar)
                        if "(" not in lk and not re.match(r'^(?:25|50|100|150|200|250|300|350|400)M\b', lk_up):
                            if re.search(r'\d{1,2}m\d{2}s\d{2}c?', lk, re.IGNORECASE):
                                if tempos_finais_vistos >= 1:
                                    break
                                tempos_finais_vistos += 1
                        linhas_seq.append(lk)

                bloco_fim = " ".join(linhas_seq)
                bloco_fim_up = bloco_fim.upper()

                if any(w in status_imediato for w in ["DESCLA", "D*D*", "DQL"]):
                    tempo_final, pontos_final, colocacao = "DQL", 0.0, 0
                elif any(w in status_imediato for w in ["AUSENTE", "Ñ NADOU", "N/C"]):
                    tempo_final, pontos_final, colocacao = "Ausente", 0.0, 0
                else:
                    sem_parciais = re.sub(r'\([^\)]*\)', '', bloco_fim)
                    sem_parciais = re.sub(r'\b(?:25|50|100|150|200|250|300|350|400)m\s+\d{1,2}m\d{2}s\d{2}c?', '', sem_parciais, flags=re.IGNORECASE)
                    m_t = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)', sem_parciais, re.IGNORECASE)
                    tempo_final = padronizar_tempo_string(m_t.group(1)) if m_t else "S/T"
                    # (?<!\d)(\d{1,2},\d{2})(?!\d) funciona mesmo quando vem colado como "15,00Record"
                    m_pts = re.search(r'(?<!\d)(\d{1,2},\d{2})(?!\d)', sem_parciais)
                    pontos_final = float(m_pts.group(1).replace(",", ".")) if m_pts else 0.0

                eh_recorde = (pontos_final >= 15.0) or bool(re.search(r'(?:^|\b|\d)RECORD\b', bloco_fim, re.IGNORECASE))
                recorde_flag = "Recorde UNAMI" if eh_recorde else ""

                vinhedo_rows.append({
                    "Data": data_evento_manual, "Campeonato": "UNAMI", "Local/Etapa": nome_evento_manual,
                    "Prova": prova_atual, "Tipo_Prova": "Individual", "Atleta": atleta_oficial,
                    "Categoria": categoria_atual, "Colocacao": colocacao, "Tempo": tempo_final,
                    "Pontos": pontos_final, "Recorde": recorde_flag, "Integrantes": ""
                })

        # 5. ADVERSÁRIOS UNAMI
        elif not eh_revezamento and re.search(r'\d{1,2}m\d{2}s\d{2}c?', linha, re.IGNORECASE):
            if "(" not in linha and "RECORD" not in linha_upper and "INDICE" not in linha_upper and not re.match(r'^(25|50|100|150|200|250|300|350|400)M\b', linha_upper):
                janela_adv = linhas[max(0, i-4):min(i+2, len(linhas))]
                bloco_adv = " ".join(janela_adv)
                if "VINHEDO" not in bloco_adv.upper() and "VINHEDE" not in bloco_adv.upper() and "RECORD" not in linhas[max(0, i-1)].upper():
                    m_t = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)', linha, re.IGNORECASE)
                    t_adv = padronizar_tempo_string(m_t.group(1)) if m_t else "S/T"
                    if tempo_para_segundos(t_adv) is not None:
                        mat_adv, nome_adv, equipe_adv = extrair_dados_adversario_unami(janela_adv)
                        adversarios_rows.append({
                            "Data": data_evento_manual, "Campeonato": "UNAMI", "Local/Etapa": nome_evento_manual,
                            "Prova": prova_atual, "Categoria": categoria_atual, "Matricula": mat_adv,
                            "Atleta": nome_adv, "Equipe": equipe_adv, "Colocacao": 0,
                            "Tempo": t_adv, "Pontos": 0.0, "Recorde": ""
                        })

        i += 1

    return pd.DataFrame(vinhedo_rows), pd.DataFrame(adversarios_rows)


def processar_pdf_paulista(pdf_file, nome_evento_manual, data_evento_manual):
    reader = PdfReader(pdf_file)
    vinhedo_rows = []
    adversarios_rows = []

    texto_completo = ""
    for page in reader.pages:
        texto_completo += limpar_homoglifos_gregos(page.extract_text() or "") + "\n"

    linhas = [l.strip() for l in texto_completo.split("\n") if l.strip()]

    prova_atual = "Não identificada"
    faixa_atual = "Master"
    eh_revezamento = False

    i = 0
    while i < len(linhas):
        linha = linhas[i]
        linha_upper = linha.upper()

        if "PROVA" in linha_upper and ("METROS" in linha_upper or "REVEZAMENTO" in linha_upper):
            prova_atual = normalizar_prova(linha)
            eh_revezamento = "REVEZAMENTO" in linha_upper or "4x" in prova_atual.lower()

        if "FAIXA:" in linha_upper:
            bloco_faixa = " ".join(linhas[i:min(i+4, len(linhas))]).upper()
            if "PRÉ" in bloco_faixa or "PRE" in bloco_faixa:
                faixa_atual = "PRÉ-MASTER"
            else:
                m_f = re.search(r'FAIXA\s*:?\s*\|?\s*(\d{2,3})\s*\+?', bloco_faixa)
                if m_f and int(m_f.group(1)) >= 20:
                    faixa_atual = f"{m_f.group(1)}+"

        # REVEZAMENTOS PAULISTA
        if eh_revezamento and ("VINHEDO" in linha_upper or "SECRETARIA MUNICIPAL DE ESPORTES E LAZER" in linha_upper):
            trecho_cab_rev = " ".join(linhas[max(0, i-2):min(i+3, len(linhas))])
            trecho_cab_up = trecho_cab_rev.upper()

            if "VINHEDO" in trecho_cab_up:
                colocacao = extrair_colocacao_paulista(trecho_cab_rev)

                bloco_rev_linhas = [linha]
                k = i + 1
                while k < min(i + 15, len(linhas)):
                    lk = linhas[k]
                    lk_up = lk.upper()
                    if any(tag in lk_up for tag in ["FAIXA:", "PROVA", "RECORDE MUNDIAL", "RECORDE PAULISTA", "VISITE NOSSO SITE"]):
                        break
                    eh_novo_rev = bool(re.match(r'^(?:\d{1,2}[°º]|(?:[1-9]0)|DQL)\b', lk))
                    eh_nc_outro = lk_up.startswith("N/C") and normalizar_nome_atleta(lk) == "Atleta Desconhecido"
                    if eh_novo_rev or eh_nc_outro:
                        break
                    bloco_rev_linhas.append(lk)
                    k += 1

                bloco_rev = " ".join(bloco_rev_linhas)

                if any(w in trecho_cab_up for w in ["DQL", "DESCLA"]):
                    tempo_final, colocacao = "DQL", 0
                elif any(w in trecho_cab_up for w in ["N/C", "AUSENTE"]):
                    tempo_final, colocacao = "Ausente", 0
                else:
                    sem_parciais_rev = re.sub(r'\([^\)]*\)', '', bloco_rev)
                    m_tempo = re.search(r'\b(\d{1,2}:\d{2}\.\d{2})\b', sem_parciais_rev)
                    tempo_final = padronizar_tempo_string(m_tempo.group(1)) if m_tempo else "S/T"

                rec_match = re.search(r'\b(RSP|RS|RB)\b', bloco_rev)
                recorde_flag = f"Recorde ({rec_match.group(1)})" if rec_match else ""

                integrantes = []
                for sub_l in bloco_rev_linhas:
                    atl_cand = normalizar_nome_atleta(sub_l)
                    if atl_cand != "Atleta Desconhecido" and atl_cand not in integrantes:
                        integrantes.append(atl_cand)

                vinhedo_rows.append({
                    "Data": data_evento_manual, "Campeonato": "Paulista", "Local/Etapa": nome_evento_manual,
                    "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": "EQUIPE SEL VINHEDO",
                    "Categoria": faixa_atual, "Colocacao": colocacao, "Tempo": tempo_final,
                    "Pontos": 0.0, "Recorde": recorde_flag, "Integrantes": " / ".join(integrantes)
                })
                for atl in integrantes:
                    vinhedo_rows.append({
                        "Data": data_evento_manual, "Campeonato": "Paulista", "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual, "Tipo_Prova": "Revezamento", "Atleta": atl,
                        "Categoria": faixa_atual, "Colocacao": colocacao, "Tempo": tempo_final,
                        "Pontos": 0.0, "Recorde": recorde_flag, "Integrantes": " / ".join(integrantes)
                    })
                i = max(i + 1, k)
                continue

        # INDIVIDUAL VINHEDO PAULISTA
        if not eh_revezamento and "VINHEDO" in linha_upper:
            trecho_antes = " ".join(linhas[max(0, i-3):i+1])
            atleta_oficial = normalizar_nome_atleta(trecho_antes)
            if atleta_oficial == "Atleta Desconhecido":
                atleta_oficial = normalizar_nome_atleta(" ".join(linhas[max(0, i-3):min(i+3, len(linhas))]))

            if atleta_oficial != "Atleta Desconhecido":
                colocacao = extrair_colocacao_paulista(trecho_antes)

                bloco_linhas = [linhas[max(0, i-1)], linha]
                k = i + 1
                while k < min(i + 9, len(linhas)):
                    lk = linhas[k]
                    lk_up = lk.upper()
                    if (
                        re.match(r'^(?:\d{1,2}[°º]|(?:[1-9]0)|N/C|DQL)\b', lk)
                        or re.match(r'^\d{4,7}\s+[A-ZÀ-ÿ]', lk)
                        or "FAIXA:" in lk_up
                        or "PROVA" in lk_up
                        or "RECORDE MUNDIAL" in lk_up
                        or "RECORDE SUL-AMERICANO" in lk_up
                        or "RECORDE BRASILEIRO" in lk_up
                        or "RECORDE PAULISTA" in lk_up
                        or "VISITE NOSSO SITE" in lk_up
                    ):
                        break
                    bloco_linhas.append(lk)
                    k += 1

                bloco_p = " ".join(bloco_linhas)

                if any(w in (trecho_antes + " " + bloco_p).upper() for w in ["DQL", "DESCLA"]):
                    tempo_final, colocacao = "DQL", 0
                elif any(w in (trecho_antes + " " + bloco_p).upper() for w in ["N/C", "AUSENTE"]):
                    tempo_final, colocacao = "Ausente", 0
                else:
                    sem_parciais = re.sub(r'\([^\)]*\)', '', bloco_p)
                    sem_parciais = re.sub(r'\b\d{2,3}m\s*:?\s*\d{1,2}[:\.]\d{2}(?:\.\d{2})?', '', sem_parciais)
                    m_t = re.search(r'\b(\d{1,2}:\d{2}\.\d{2}|\d{2}\.\d{2})\b', sem_parciais)
                    tempo_final = padronizar_tempo_string(m_t.group(1)) if m_t else "S/T"

                rec_match = re.search(r'\b(RSP|RS|RB)\b', bloco_p)
                recorde_flag = f"Recorde ({rec_match.group(1)})" if rec_match else ""

                vinhedo_rows.append({
                    "Data": data_evento_manual, "Campeonato": "Paulista", "Local/Etapa": nome_evento_manual,
                    "Prova": prova_atual, "Tipo_Prova": "Individual", "Atleta": atleta_oficial,
                    "Categoria": faixa_atual, "Colocacao": colocacao, "Tempo": tempo_final,
                    "Pontos": 0.0, "Recorde": recorde_flag, "Integrantes": ""
                })
                i = max(i + 1, k)
                continue

        # ADVERSÁRIOS PAULISTA
        ind_adv = re.match(r'^(\d{1,2}[°º]|(?:[1-9]0))\s+(\d{3,7})\s+(.+)$', linha)
        if not eh_revezamento and ind_adv:
            colocacao = extrair_colocacao_paulista(ind_adv.group(1))
            mat_p = ind_adv.group(2).lstrip("0") or ind_adv.group(2)

            bloco_linhas = [linha]
            k = i + 1
            while k < min(i + 9, len(linhas)):
                lk = linhas[k]
                lk_up = lk.upper()
                if (
                    re.match(r'^(?:\d{1,2}[°º]|(?:[1-9]0)|N/C|DQL)\b', lk)
                    or "FAIXA:" in lk_up
                    or "PROVA" in lk_up
                    or "RECORDE MUNDIAL" in lk_up
                    or "VISITE NOSSO SITE" in lk_up
                ):
                    break
                bloco_linhas.append(lk)
                k += 1

            bloco_p = " ".join(bloco_linhas)
            if "VINHEDO" not in bloco_p.upper():
                sem_parciais = re.sub(r'\([^\)]*\)', '', bloco_p)
                sem_parciais = re.sub(r'\b\d{2,3}m\s*:?\s*\d{1,2}[:\.]\d{2}(?:\.\d{2})?', '', sem_parciais)
                m_t = re.search(r'\b(\d{1,2}:\d{2}\.\d{2}|\d{2}\.\d{2})\b', sem_parciais)
                t_adv = padronizar_tempo_string(m_t.group(1)) if m_t else "S/T"
                if tempo_para_segundos(t_adv) is not None:
                    resto_p = ind_adv.group(3).replace("|", " ")
                    m_eq = re.search(rf'({EQUIPES_CONHECIDAS_REGEX})', resto_p, re.IGNORECASE)
                    if m_eq:
                        nome_adv = limpar_nome_adversario(resto_p[:m_eq.start()])
                        eq_adv = m_eq.group(0).upper()
                    else:
                        nome_adv = limpar_nome_adversario(re.split(r'\d{1,2}[:\.]\d{2}', resto_p)[0])
                        eq_adv = "Paulista"
                    adversarios_rows.append({
                        "Data": data_evento_manual, "Campeonato": "Paulista", "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual, "Categoria": faixa_atual, "Matricula": mat_p,
                        "Atleta": nome_adv or f"Atleta #{mat_p}", "Equipe": eq_adv, "Colocacao": colocacao,
                        "Tempo": t_adv, "Pontos": 0.0, "Recorde": ""
                    })
            i = max(i + 1, k)
            continue

        i += 1

    return pd.DataFrame(vinhedo_rows), pd.DataFrame(adversarios_rows)


def processar_pdf(pdf_file, tipo_relatorio, nome_evento_manual, data_evento_manual):
    if tipo_relatorio == "UNAMI":
        return processar_pdf_unami(pdf_file, nome_evento_manual, data_evento_manual)
    else:
        return processar_pdf_paulista(pdf_file, nome_evento_manual, data_evento_manual)

# ==========================================
# --- CARREGAMENTO E MIGRAÇÃO DE BASES ---
# ==========================================
CSV_FILE = "historico_vinhedo.csv"
CSV_ADVERSARIOS = "base_adversarios.csv"

COLUNAS_VINHEDO = [
    "Data", "Campeonato", "Local/Etapa", "Prova", "Tipo_Prova",
    "Atleta", "Categoria", "Colocacao", "Tempo", "Pontos", "Recorde", "Integrantes"
]
COLUNAS_ADVERSARIOS = [
    "Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Matricula",
    "Atleta", "Equipe", "Colocacao", "Tempo", "Pontos", "Recorde"
]

def carregar_csv_seguro(caminho, colunas_esperadas):
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
            if col == "Campeonato": df_lido[col] = "UNAMI"
            elif col == "Tipo_Prova": df_lido[col] = "Individual"
            elif col in ["Colocacao", "Pontos"]: df_lido[col] = "0"
            else: df_lido[col] = ""
    return df_lido[colunas_esperadas].fillna("")

df_historico = carregar_csv_seguro(CSV_FILE, COLUNAS_VINHEDO)
df_adversarios = carregar_csv_seguro(CSV_ADVERSARIOS, COLUNAS_ADVERSARIOS)

if not df_historico.empty:
    df_historico["Data"] = df_historico["Data"].apply(normalizar_data_str)
    df_historico["Atleta"] = df_historico["Atleta"].apply(
        lambda x: "EQUIPE SEL VINHEDO" if str(x).upper() == "EQUIPE SEL VINHEDO" else normalizar_nome_atleta(x)
    )
    df_historico["Prova"] = df_historico["Prova"].apply(normalizar_prova)
    df_historico["Tempo"] = df_historico["Tempo"].apply(padronizar_tempo_string)
    df_historico["Categoria"] = df_historico["Categoria"].apply(normalizar_categoria)
    df_historico["Colocacao"] = pd.to_numeric(df_historico["Colocacao"], errors="coerce").fillna(0).astype(int)
    df_historico["Pontos"] = pd.to_numeric(df_historico["Pontos"], errors="coerce").fillna(0.0)
    df_historico["Recorde"] = df_historico["Recorde"].fillna("").astype(str)
    df_historico["Integrantes"] = df_historico["Integrantes"].fillna("").astype(str)
    df_historico = df_historico[df_historico["Atleta"] != "Atleta Desconhecido"]

if not df_adversarios.empty:
    df_adversarios["Data"] = df_adversarios["Data"].apply(normalizar_data_str)
    df_adversarios["Prova"] = df_adversarios["Prova"].apply(normalizar_prova)
    df_adversarios["Tempo"] = df_adversarios["Tempo"].apply(padronizar_tempo_string)
    df_adversarios["Categoria"] = df_adversarios["Categoria"].apply(normalizar_categoria)
    df_adversarios["Matricula"] = df_adversarios["Matricula"].apply(lambda x: re.sub(r'\.0$', '', str(x).strip()))

def obter_anos_ordenados(df):
    if df.empty:
        return [str(ANO_ATUAL)]
    anos = sorted(
        list(set(pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce").dt.year.dropna().astype(int).astype(str))),
        reverse=True
    )
    return anos if anos else [str(ANO_ATUAL)]

# ==========================================
# --- MENU LATERAL DE NAVEGAÇÃO ---
# ==========================================
with st.sidebar:
    st.markdown("## 🏊‍♂️ SEL Vinhedo Master")
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
            "🗄️ Backup & Editar Tabela"
        ]
    )
    st.markdown("---")

# --- GLOSSÁRIO COMPACTO NO TOPO PARA CELULAR ---
with st.expander("🧭 Não sabe onde clicar? Veja o que tem em cada aba"):
    st.markdown("""
- **🏆 Medalhas & Pontos da Equipe:** Pontuação geral de Vinhedo na UNAMI, quadro de medalhas por atleta, revezamentos e mural de recordes.
- **🏊 Meus Tempos & Medalhas:** Seus recordes pessoais (PRs), suas medalhas, pontos e gráfico de evolução.
- **🎯 Onde Tenho Mais Chances?:** Compara seus tempos com os rivais da sua faixa etária para mostrar suas provas mais fortes.
- **⏱️ Melhores Tempos da Equipe:** Consulta os melhores tempos da equipe em cada prova.
- **🚀 Montar Revezamento:** Simula as melhores formações de revezamento e mostra o histórico oficial da equipe.
- **✍️ Lançar Tempos de Treino:** Tabela rápida estilo Excel para o treinador anotar tempos de treino (50m em diante).
- **📤 Importar PDFs de Provas:** Área para subir os resultados oficiais em PDF (UNAMI e Paulista) em lote.
- **🗄️ Backup & Editar Tabela:** Baixar backup em CSV, restaurar ou corrigir qualquer linha da base.
    """)

# ------------------------------------------
# TELA 1: MEDALHAS & PONTOS DA EQUIPE
# ------------------------------------------
if tela_selecionada == "🏆 Medalhas & Pontos da Equipe":
    st.title("🏆 Medalhas, Recordes & Troféu UNAMI")

    if not df_historico.empty:
        anos_disp = obter_anos_ordenados(df_historico)
        opcoes_ano = anos_disp + ["Todos os Anos"]

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            ano_sel = st.selectbox("Temporada (Padrão: Ano mais recente):", opcoes_ano, index=0)
        with col_f2:
            camp_sel = st.selectbox("Campeonato (Medalhas & Participação):", ["Todos (UNAMI + Paulista)", "UNAMI", "Paulista"], index=0)

        df_filtrado = df_historico.copy()
        df_filtrado["Ano_Str"] = pd.to_datetime(df_filtrado["Data"], format="%d/%m/%Y", errors="coerce").dt.year.fillna(0).astype(int).astype(str)

        if ano_sel != "Todos os Anos":
            df_filtrado = df_filtrado[df_filtrado["Ano_Str"] == ano_sel]

        df_unami_ano = df_filtrado[df_filtrado["Campeonato"] == "UNAMI"]
        pontos_gerais_vinhedo = df_unami_ano["Pontos"].sum()
        pts_ind_vinhedo = df_unami_ano[df_unami_ano["Tipo_Prova"] == "Individual"]["Pontos"].sum()
        pts_rev_vinhedo = df_unami_ano[df_unami_ano["Tipo_Prova"] == "Revezamento"]["Pontos"].sum()

        if camp_sel == "UNAMI":
            df_med = df_filtrado[df_filtrado["Campeonato"] == "UNAMI"]
        elif camp_sel == "Paulista":
            df_med = df_filtrado[df_filtrado["Campeonato"] == "Paulista"]
        else:
            df_med = df_filtrado

        df_equipe_meds = df_med[
            ((df_med["Tipo_Prova"] == "Individual") | (df_med["Atleta"] == "EQUIPE SEL VINHEDO"))
            & (df_med["Colocacao"].isin([1, 2, 3]))
        ]
        ouros_eq = (df_equipe_meds["Colocacao"] == 1).sum()
        pratas_eq = (df_equipe_meds["Colocacao"] == 2).sum()
        bronzes_eq = (df_equipe_meds["Colocacao"] == 3).sum()
        recordes_eq = df_med[
            ((df_med["Tipo_Prova"] == "Individual") | (df_med["Atleta"] == "EQUIPE SEL VINHEDO"))
            & (df_med["Recorde"].str.strip() != "")
        ]

        df_pessoas_periodo = df_med[df_med["Atleta"] != "EQUIPE SEL VINHEDO"]

        st.markdown(f"### 🏅 Desempenho Consolidado SEL Vinhedo — {ano_sel}")
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("🏆 Pontos UNAMI", f"{pontos_gerais_vinhedo:.2f}".replace(".", ","), f"Ind: {pts_ind_vinhedo:.1f} | Rev: {pts_rev_vinhedo:.1f}")
        k2.metric("🥇 Ouros", int(ouros_eq))
        k3.metric("🥈 Pratas", int(pratas_eq))
        k4.metric("🥉 Bronzes", int(bronzes_eq))
        k5.metric("⚡ Recordes", len(recordes_eq))
        k6.metric("🏊 Atletas Ativos", df_pessoas_periodo["Atleta"].nunique())

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
                rank_pts = df_pts_pessoa.groupby("Atleta").agg(
                    Pontos_UNAMI=("Pontos", "sum"),
                    Provas_UNAMI=("Prova", "count")
                ).reset_index().sort_values(by=["Pontos_UNAMI", "Provas_UNAMI"], ascending=[False, True])
                rank_pts["Pos"] = [f"🏆 {i}º" if i <= 3 else f"{i}º" for i in range(1, len(rank_pts) + 1)]
                rank_pts = rank_pts[["Pos", "Atleta", "Pontos_UNAMI", "Provas_UNAMI"]].rename(
                    columns={"Pontos_UNAMI": "Pontos", "Provas_UNAMI": "Provas"}
                )
                st.dataframe(rank_pts, use_container_width=True, hide_index=True)
            else:
                st.info("Sem pontos da UNAMI registrados para este filtro.")

        with col_r2:
            st.markdown(f"#### 🥇 Quadro de Medalhas por Atleta ({camp_sel})")
            if not df_pessoas_periodo.empty:
                atletas_com_provas = sorted(df_pessoas_periodo["Atleta"].unique())
                linhas_quadro = []
                for atl in atletas_com_provas:
                    sub = df_pessoas_periodo[df_pessoas_periodo["Atleta"] == atl]
                    o_tot = (sub["Colocacao"] == 1).sum()
                    p_tot = (sub["Colocacao"] == 2).sum()
                    b_tot = (sub["Colocacao"] == 3).sum()
                    o_rev = ((sub["Colocacao"] == 1) & (sub["Tipo_Prova"] == "Revezamento")).sum()
                    p_rev = ((sub["Colocacao"] == 2) & (sub["Tipo_Prova"] == "Revezamento")).sum()
                    b_rev = ((sub["Colocacao"] == 3) & (sub["Tipo_Prova"] == "Revezamento")).sum()
                    recs = (sub["Recorde"].str.strip() != "").sum()
                    linhas_quadro.append({
                        "Atleta": atl,
                        "🥇 Ouro": int(o_tot),
                        "🥈 Prata": int(p_tot),
                        "🥉 Bronze": int(b_tot),
                        "Total": int(o_tot + p_tot + b_tot),
                        "Sendo Rev.": f"{o_rev}🥇 {p_rev}🥈 {b_rev}🥉" if (o_rev + p_rev + b_rev) > 0 else "-",
                        "⚡ Rec.": int(recs)
                    })
                df_quadro_pessoas = pd.DataFrame(linhas_quadro).sort_values(
                    by=["🥇 Ouro", "🥈 Prata", "🥉 Bronze", "Atleta"],
                    ascending=[False, False, False, True]
                )
                st.dataframe(df_quadro_pessoas, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma prova registrada neste filtro.")

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
            st.dataframe(
                df_rev_exibir[["Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Colocação", "Tempo", "Pontos", "Integrantes", "Recorde"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum revezamento registrado neste período.")

        if not recordes_eq.empty:
            st.markdown("---")
            st.markdown(f"#### ⚡ Mural de Recordes Quebrados ({ano_sel})")
            df_rec_show = recordes_eq.copy()
            df_rec_show["Atleta / Equipe"] = df_rec_show.apply(
                lambda r: f"EQUIPE ({r['Integrantes']})" if r["Atleta"] == "EQUIPE SEL VINHEDO" and r["Integrantes"] else r["Atleta"],
                axis=1
            )
            st.dataframe(
                df_rec_show[["Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Atleta / Equipe", "Tempo", "Recorde"]],
                use_container_width=True,
                hide_index=True
            )

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
                delegacao = delegacao.sort_values("Atletas Presentes", ascending=False)
                st.dataframe(delegacao, use_container_width=True, hide_index=True)
    else:
        st.info("A base está vazia. Vá em '📤 Importar PDFs de Provas' para carregar os resultados.")

# ------------------------------------------
# TELA 2: MEUS TEMPOS & MEDALHAS
# ------------------------------------------
elif tela_selecionada == "🏊 Meus Tempos & Medalhas":
    st.title("🏊 Meus Tempos, Medalhas & Evolução")
    if not df_historico.empty:
        df_atletas_only = df_historico[df_historico["Atleta"] != "EQUIPE SEL VINHEDO"].copy()
        lista_atletas = sorted(df_atletas_only["Atleta"].unique())
        anos_disp = obter_anos_ordenados(df_atletas_only)

        col_a1, col_a2 = st.columns([2, 1])
        with col_a1:
            atleta_sel = st.selectbox("Selecione o Atleta:", lista_atletas, key="consulta_atleta")
        with col_a2:
            ano_atleta_sel = st.selectbox("Temporada (Cards e Histórico):", anos_disp + ["Todos os Anos"], index=0)

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
            df_prs = df_validos_ind.loc[idx_melhores, ["Prova", "Tempo", "Data", "Local/Etapa", "Campeonato"]].rename(
                columns={"Tempo": "Tempo Recorde"}
            )
            styler_prs = df_prs.style.set_properties(**{
                'background-color': '#fffbe6',
                'color': '#333333',
                'border-color': 'white',
                'font-weight': 'bold'
            })
            st.dataframe(styler_prs, use_container_width=True, hide_index=True)
        else:
            st.warning("Este atleta não possui marcas individuais numéricas válidas.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"#### 📅 Histórico Completo de Participações ({ano_atleta_sel})")
        df_cronologico = df_atleta_periodo.sort_values(by="Data_Dt", ascending=False).copy()
        df_cronologico["Colocação"] = df_cronologico["Colocacao"].apply(formatar_colocacao_medalha)
        st.dataframe(
            df_cronologico[["Data", "Campeonato", "Local/Etapa", "Tipo_Prova", "Prova", "Categoria", "Colocação", "Tempo", "Pontos", "Recorde"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.markdown("#### 📈 Gráfico de Evolução (Segundos - Provas Individuais)")
        if not df_validos_ind.empty:
            df_grafico = df_validos_ind.dropna(subset=["Data_Dt"]).sort_values("Data_Dt")
            provas_disp = df_grafico["Prova"].unique()
            abas_graficos = st.tabs(list(provas_disp))
            for i, prova_nome in enumerate(provas_disp):
                with abas_graficos[i]:
                    df_p = df_grafico[df_grafico["Prova"] == prova_nome].copy()
                    df_chart = df_p.set_index("Data_Dt")[["Segundos"]]
                    st.line_chart(df_chart, use_container_width=True)
    else:
        st.info("O histórico está vazio.")

# ------------------------------------------
# TELA 3: ONDE TENHO MAIS CHANCES? (RADAR DE PROVAS)
# ------------------------------------------
elif tela_selecionada == "🎯 Onde Tenho Mais Chances?":
    st.title("🎯 Onde Tenho Mais Chances?")
    st.markdown("Compara os seus **melhores tempos (PRs)** com os tempos reais dos **adversários da sua faixa etária**.")

    if df_historico.empty or df_adversarios.empty:
        st.info("Importe os PDFs na aba '📤 Importar PDFs de Provas' para ativar o comparador.")
    else:
        lista_atletas = sorted([a for a in df_historico["Atleta"].unique() if a != "EQUIPE SEL VINHEDO"])
        col_r1, col_r2, col_r3, col_r4 = st.columns([2, 1, 1, 1])
        with col_r1:
            atleta_radar = st.selectbox("Selecione o Atleta:", lista_atletas)
        with col_r2:
            ano_ref_radar = st.number_input("Ano da Competição:", min_value=2025, max_value=2030, value=2027)
        with col_r3:
            janela_tempo = st.selectbox("Janela de Adversários:", ["Últimos 12 meses", "Últimos 6 meses", "Toda a base"], index=0)
        with col_r4:
            camp_radar = st.selectbox("Campeonato:", ["Todos", "UNAMI", "Paulista"], index=0)

        faixa_atleta = obter_faixa_etaria_atleta(atleta_radar, ano_ref_radar)
        faixa_anterior = obter_faixa_etaria_atleta(atleta_radar, ano_ref_radar - 1)
        mudou_cat = (faixa_atleta != faixa_anterior)

        msg_cat = f"👤 **{atleta_radar}** | Idade em {ano_ref_radar}: **{calcular_idade(atleta_radar, ano_ref_radar)} anos** → Categoria: **{faixa_atleta}**"
        if mudou_cat:
            msg_cat += f" 🎉 *(Acabou de subir da {faixa_anterior} — entra como o mais jovem da nova faixa!)*"
        st.info(msg_cat)

        df_atl_ind = df_historico[(df_historico["Atleta"] == atleta_radar) & (df_historico["Tipo_Prova"] == "Individual")].copy()
        df_atl_ind["Segundos"] = df_atl_ind["Tempo"].apply(tempo_para_segundos)
        df_atl_ind = df_atl_ind.dropna(subset=["Segundos"])

        df_adv_base = df_adversarios.copy()
        df_adv_base["Data_Dt"] = pd.to_datetime(df_adv_base["Data"], format="%d/%m/%Y", errors="coerce")

        if janela_tempo != "Toda a base" and not df_adv_base["Data_Dt"].dropna().empty:
            data_max = df_adv_base["Data_Dt"].max()
            dias = 365 if janela_tempo == "Últimos 12 meses" else 183
            df_adv_base = df_adv_base[df_adv_base["Data_Dt"] >= (data_max - timedelta(days=dias))]

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
                prova_nome = row["Prova"]
                meu_tempo_seg = row["Segundos"]

                df_comp = df_adv_base[(df_adv_base["Prova"] == prova_nome) & (df_adv_base["Categoria"] == faixa_atleta)].copy()
                if df_comp.empty:
                    continue

                df_comp["Chave_Rival"] = df_comp.apply(
                    lambda r: r["Matricula"] if str(r["Matricula"]).strip() != "" else r["Atleta"], axis=1
                )
                melhores_adv = df_comp.groupby("Chave_Rival")["Segundos"].min().sort_values()
                total_rivais = len(melhores_adv)
                rivais_mais_rapidos = (melhores_adv < meu_tempo_seg).sum()
                posicao_estimada = rivais_mais_rapidos + 1

                tempo_ouro = melhores_adv.iloc[0]
                tempo_bronze = melhores_adv.iloc[min(2, total_rivais - 1)]
                dif_ouro = meu_tempo_seg - tempo_ouro
                dif_bronze = meu_tempo_seg - tempo_bronze

                if posicao_estimada == 1:
                    chance_txt = "🔥 Favorito ao Ouro"
                elif posicao_estimada <= 3:
                    chance_txt = "🏅 Zona de Pódio"
                elif dif_bronze <= 1.5:
                    chance_txt = "⚡ Na briga (<1.5s do pódio)"
                else:
                    chance_txt = "📊 Intermediário"

                analise_provas.append({
                    "Prova": prova_nome,
                    "Seu PR": segundos_para_tempo(meu_tempo_seg),
                    "Posição Simulada": f"{posicao_estimada}º de {total_rivais + 1}",
                    "Pos_Num": posicao_estimada,
                    "Cenário": chance_txt,
                    "Melhor Rival (Ouro)": segundos_para_tempo(tempo_ouro),
                    "Dif. p/ Ouro": f"{dif_ouro:+.2f}s",
                    "Corte Pódio (3º)": segundos_para_tempo(tempo_bronze),
                    "Dif. p/ Bronze": f"{dif_bronze:+.2f}s"
                })

            if analise_provas:
                df_radar = pd.DataFrame(analise_provas).sort_values(by=["Pos_Num", "Dif. p/ Bronze"])
                st.markdown(f"### 📊 Ranking das Suas Melhores Provas na Categoria {faixa_atleta}")
                st.dataframe(
                    df_radar.drop(columns=["Pos_Num"]),
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")
                st.markdown("#### 🔍 Quem são seus principais rivais em cada prova?")
                prova_detalhe = st.selectbox("Escolha uma prova para ver os tempos dos adversários:", df_radar["Prova"].tolist())
                df_rivais_det = df_adv_base[(df_adv_base["Prova"] == prova_detalhe) & (df_adv_base["Categoria"] == faixa_atleta)].copy()
                df_rivais_det["Chave_Rival"] = df_rivais_det.apply(
                    lambda r: r["Matricula"] if str(r["Matricula"]).strip() != "" else r["Atleta"], axis=1
                )
                idx_min_adv = df_rivais_det.groupby("Chave_Rival")["Segundos"].idxmin()
                df_top_rivais = df_rivais_det.loc[idx_min_adv].sort_values("Segundos").head(15)
                df_top_rivais["Rank"] = range(1, len(df_top_rivais) + 1)
                st.dataframe(
                    df_top_rivais[["Rank", "Atleta", "Equipe", "Tempo", "Local/Etapa", "Data"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning(f"Ainda não há registros de adversários na categoria **{faixa_atleta}** nesta janela de tempo.")

# ------------------------------------------
# TELA 4: MELHORES TEMPOS DA EQUIPE
# ------------------------------------------
elif tela_selecionada == "⏱️ Melhores Tempos da Equipe":
    st.title("⏱️ Melhores Tempos da Equipe por Prova")
    if not df_historico.empty:
        df_ind = df_historico[df_historico["Tipo_Prova"] == "Individual"].copy()
        lista_provas = sorted(df_ind["Prova"].unique())
        prova_sel = st.selectbox("Selecione a Prova para consultar os tempos da equipe:", lista_provas, key="treinador_prova_sel")

        df_prova_rank = df_ind[df_ind["Prova"] == prova_sel].copy()
        df_prova_rank["Segundos"] = df_prova_rank["Tempo"].apply(tempo_para_segundos)
        df_prova_rank = df_prova_rank.dropna(subset=["Segundos"])

        if not df_prova_rank.empty:
            idx_melhores_rank = df_prova_rank.groupby("Atleta")["Segundos"].idxmin()
            df_top_atletas = df_prova_rank.loc[idx_melhores_rank].sort_values("Segundos")
            df_top_atletas["Ordem"] = range(1, len(df_top_atletas) + 1)

            st.dataframe(
                df_top_atletas[["Ordem", "Atleta", "Tempo", "Categoria", "Local/Etapa", "Data"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Não há tempos válidos registrados para esta prova.")
    else:
        st.info("A base está vazia.")

# ------------------------------------------
# TELA 5: MONTAR REVEZAMENTO
# ------------------------------------------
elif tela_selecionada == "🚀 Montar Revezamento":
    st.title("🚀 Simulador & Histórico de Revezamentos")

    col_rev1, col_rev2, col_rev3 = st.columns(3)
    with col_rev1:
        tipo_rev = st.radio("Estilo do Revezamento:", ["4x50m Livre", "4x50m Medley"], horizontal=True)
    with col_rev2:
        genero_rev = st.radio("Categoria de Gênero:", ["Feminino", "Masculino", "Misto"], horizontal=True)
    with col_rev3:
        ano_rev = st.number_input("Ano base para idade:", min_value=2025, max_value=2030, value=2027)

    lista_completa = sorted(list(ANOS_NASCIMENTO.keys()))
    if genero_rev == "Masculino":
        lista_filtrada = [a for a in lista_completa if GENERO_ATLETAS.get(a) == 'M']
    elif genero_rev == "Feminino":
        lista_filtrada = [a for a in lista_completa if GENERO_ATLETAS.get(a) == 'F']
    else:
        lista_filtrada = lista_completa

    atletas_pool = st.multiselect(
        "Selecione os atletas disponíveis para compor:",
        lista_filtrada,
        default=lista_filtrada[:6] if len(lista_filtrada) >= 6 else lista_filtrada
    )

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
                st.error(f"Não há atletas suficientes selecionados para formar um revezamento ({genero_rev}).")
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
                            idade_total = sum(calcular_idade(a, ano_rev) for a in combo_limpo)
                            cat = obter_categoria_revezamento(idade_total)
                            resultados.append({
                                "Equipe": " / ".join(combo_limpo),
                                "Categoria": cat,
                                "Soma Idades": idade_total,
                                "Tempo Total (Seg)": sum(tempos),
                                "Tempo Estimado": segundos_para_tempo(sum(tempos))
                            })
                else:
                    for combo in combinacoes_validas:
                        combo_limpo = [extrair_string(a) for a in combo]
                        melhor_t = float('inf')
                        melhor_ordem = None

                        for perm in itertools.permutations(combo_limpo):
                            t_cos = tempo_para_segundos(dict_tempos.get(perm[0], {}).get("Costas", "S/T")) or float('inf')
                            t_pei = tempo_para_segundos(dict_tempos.get(perm[1], {}).get("Peito", "S/T")) or float('inf')
                            t_bor = tempo_para_segundos(dict_tempos.get(perm[2], {}).get("Borboleta", "S/T")) or float('inf')
                            t_liv = tempo_para_segundos(dict_tempos.get(perm[3], {}).get("Livre", "S/T")) or float('inf')

                            soma = t_cos + t_pei + t_bor + t_liv
                            if soma < melhor_t:
                                melhor_t = soma
                                melhor_ordem = perm

                        if melhor_t != float('inf'):
                            idade_total = sum(calcular_idade(a, ano_rev) for a in combo_limpo)
                            cat = obter_categoria_revezamento(idade_total)
                            resultados.append({
                                "Equipe": f"Costas: {melhor_ordem[0]} / Peito: {melhor_ordem[1]} / Borboleta: {melhor_ordem[2]} / Livre: {melhor_ordem[3]}",
                                "Categoria": cat,
                                "Soma Idades": idade_total,
                                "Tempo Total (Seg)": melhor_t,
                                "Tempo Estimado": segundos_para_tempo(melhor_t)
                            })

                if resultados:
                    df_res = pd.DataFrame(resultados)
                    categorias_encontradas = sorted(df_res["Categoria"].unique(), reverse=True)
                    for cat in categorias_encontradas:
                        st.markdown(f"### 🏆 Categoria {cat} ({genero_rev})")
                        df_cat = df_res[df_res["Categoria"] == cat].sort_values("Tempo Total (Seg)").head(3)
                        st.table(df_cat[["Tempo Estimado", "Soma Idades", "Equipe"]])
                else:
                    st.warning("Preencha marcas válidas na tabela de ajustes para gerar as simulações.")
    else:
        st.info("Selecione atletas para iniciar a montagem do revezamento.")

    st.markdown("---")
    st.markdown("### 📜 Histórico Real de Revezamentos SEL Vinhedo")
    if not df_historico.empty:
        df_rev_hist = df_historico[df_historico["Atleta"] == "EQUIPE SEL VINHEDO"].copy()
        if not df_rev_hist.empty:
            df_rev_hist["Data_Dt"] = pd.to_datetime(df_rev_hist["Data"], format="%d/%m/%Y", errors="coerce")
            df_rev_hist = df_rev_hist.sort_values("Data_Dt", ascending=False)
            df_rev_hist["Colocação"] = df_rev_hist["Colocacao"].apply(formatar_colocacao_medalha)
            st.dataframe(
                df_rev_hist[["Data", "Campeonato", "Local/Etapa", "Prova", "Categoria", "Colocação", "Tempo", "Pontos", "Integrantes", "Recorde"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum revezamento oficial importado ainda.")

# ------------------------------------------
# TELA 6: LANÇAR TEMPOS DE TREINO (EXCLUSIVA TREINADOR - 50M EM DIANTE)
# ------------------------------------------
elif tela_selecionada == "✍️ Lançar Tempos de Treino":
    st.title("✍️ Lançamento Rápido de Treinos (Tomada de Tempo)")
    st.markdown("Escolha a **Prova** (50m em diante) e a **Data**, digite o tempo apenas de quem nadou na coluna **Tempo** e clique em **Salvar Tempos**.")

    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        prova_treino = st.selectbox("1. Qual foi a prova?", [
            "50m Livre", "50m Costas", "50m Peito", "50m Borboleta",
            "100m Livre", "100m Costas", "100m Peito", "100m Borboleta", "100m Medley",
            "200m Livre", "200m Costas", "200m Peito", "200m Borboleta", "200m Medley",
            "400m Livre", "800m Livre", "1500m Livre"
        ])
    with col_t2:
        data_treino = st.date_input("2. Data do Treino:")
    with col_t3:
        local_treino = st.text_input("3. Descrição / Local:", value="Tomada de Tempo - Treino")

    lista_todos_atletas = sorted(list(ANOS_NASCIMENTO.keys()))
    df_grade_treino = pd.DataFrame({
        "Atleta": lista_todos_atletas,
        "Gênero": ["Fem" if GENERO_ATLETAS.get(a) == "F" else "Masc" for a in lista_todos_atletas],
        "Tempo (ex: 29.45 ou 1:05.10)": ["" for _ in lista_todos_atletas]
    })

    st.markdown("#### 📋 Digite os tempos na tabela abaixo (deixe em branco quem não nadou):")
    df_treino_editado = st.data_editor(
        df_grade_treino,
        use_container_width=True,
        hide_index=True,
        disabled=["Atleta", "Gênero"],
        height=550,
        key="grade_rapida_treinador"
    )

    if st.button("💾 Salvar Todos os Tempos Preenchidos", type="primary"):
        novas_linhas_treino = []
        erros_formato = []
        ano_treino = data_treino.year

        for _, row in df_treino_editado.iterrows():
            t_raw = str(row["Tempo (ex: 29.45 ou 1:05.10)"]).strip()
            if t_raw and t_raw.lower() != "nan":
                t_pad = padronizar_tempo_string(t_raw)
                if tempo_para_segundos(t_pad) is None:
                    erros_formato.append(f"{row['Atleta']} ({t_raw})")
                else:
                    novas_linhas_treino.append({
                        "Data": data_treino.strftime("%d/%m/%Y"),
                        "Campeonato": "Treino",
                        "Local/Etapa": local_treino,
                        "Prova": f"{prova_treino} {row['Gênero']}",
                        "Tipo_Prova": "Individual",
                        "Atleta": row["Atleta"],
                        "Categoria": obter_faixa_etaria_atleta(row["Atleta"], ano_treino),
                        "Colocacao": 0,
                        "Tempo": t_pad,
                        "Pontos": 0.0,
                        "Recorde": "",
                        "Integrantes": ""
                    })

        if erros_formato:
            st.error(f"⚠️ Verifique o formato do tempo (use ponto para centésimos, ex: `31.45` ou `1:12.30`): {', '.join(erros_formato)}")
        elif novas_linhas_treino:
            df_novos_t = pd.DataFrame(novas_linhas_treino)
            df_total = pd.concat([df_historico, df_novos_t], ignore_index=True).drop_duplicates(
                subset=["Data", "Campeonato", "Prova", "Tipo_Prova", "Atleta", "Tempo"]
            )
            df_total.to_csv(CSV_FILE, index=False)
            st.success(f"✅ {len(novas_linhas_treino)} tempo(s) de treino salvos com sucesso!")
            st.rerun()
        else:
            st.warning("Nenhum tempo foi digitado na tabela.")

# ------------------------------------------
# TELA 7: IMPORTAR PDFS DE PROVAS (EM LOTE COM PRÉVIA)
# ------------------------------------------
elif tela_selecionada == "📤 Importar PDFs de Provas":
    st.title("📤 Importar Resultados Oficiais (PDFs em Lote)")
    st.markdown("Selecione **todos os PDFs de uma vez** (individuais e/ou revezamentos). O sistema lê os dados, mostra uma **prévia para conferência** e só salva quando você confirmar.")

    uploaded_files = st.file_uploader(
        "Selecione ou arraste todos os PDFs aqui:",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🔍 1. Analisar PDFs e Gerar Prévia"):
            previa_resumo = []
            vinhedo_buffer = []
            adv_buffer = []

            barra = st.progress(0)
            for idx_f, arq_pdf in enumerate(uploaded_files):
                try:
                    reader_tmp = PdfReader(arq_pdf)
                    texto_p1 = reader_tmp.pages[0].extract_text() or "" if reader_tmp.pages else ""
                    arq_pdf.seek(0)

                    camp_det, data_det, nome_det = detectar_metadados_pdf(texto_p1, arq_pdf.name)
                    df_v, df_adv = processar_pdf(arq_pdf, camp_det, nome_det, data_det)

                    pts_soma = df_v["Pontos"].sum() if not df_v.empty else 0.0
                    recs_qtd = (df_v["Recorde"].str.strip() != "").sum() if not df_v.empty else 0

                    previa_resumo.append({
                        "Arquivo": arq_pdf.name,
                        "Campeonato": camp_det,
                        "Data": data_det,
                        "Nome da Etapa": nome_det,
                        "Reg. Vinhedo": len(df_v),
                        "Pontos UNAMI": float(pts_soma),
                        "Recordes": int(recs_qtd),
                        "Rivais": len(df_adv)
                    })

                    if not df_v.empty:
                        df_v["_Arquivo_Origem"] = arq_pdf.name
                        vinhedo_buffer.append(df_v)
                    if not df_adv.empty:
                        df_adv["_Arquivo_Origem"] = arq_pdf.name
                        adv_buffer.append(df_adv)

                except Exception as e:
                    previa_resumo.append({
                        "Arquivo": arq_pdf.name,
                        "Campeonato": "ERRO",
                        "Data": "",
                        "Nome da Etapa": str(e),
                        "Reg. Vinhedo": 0,
                        "Pontos UNAMI": 0.0,
                        "Recordes": 0,
                        "Rivais": 0
                    })
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

                df_total = pd.concat([df_historico, df_v_final], ignore_index=True).drop_duplicates(
                    subset=["Data", "Campeonato", "Prova", "Tipo_Prova", "Atleta", "Tempo"]
                )
                df_total.to_csv(CSV_FILE, index=False)

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
                df_adv_total.to_csv(CSV_ADVERSARIOS, index=False)

            del st.session_state["previa_resumo"]
            del st.session_state["vinhedo_buffer"]
            del st.session_state["adv_buffer"]
            st.success("🎉 Todos os arquivos foram salvos com sucesso!")
            st.rerun()

# ------------------------------------------
# TELA 8: BACKUP & EDITAR TABELA
# ------------------------------------------
elif tela_selecionada == "🗄️ Backup & Editar Tabela":
    st.title("🗄️ Backup & Edição Administrativa")

    col_download, col_upload = st.columns(2)
    with col_download:
        st.markdown("### 📥 Salvar Backups")
        if not df_historico.empty:
            csv_export = df_historico.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar historico_vinhedo.csv",
                data=csv_export,
                file_name='historico_vinhedo.csv',
                mime='text/csv'
            )
        if not df_adversarios.empty:
            csv_adv_export = df_adversarios.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar base_adversarios.csv",
                data=csv_adv_export,
                file_name='base_adversarios.csv',
                mime='text/csv'
            )

    with col_upload:
        st.markdown("### 🔄 Restaurar Backup (Vinhedo)")
        backup_file = st.file_uploader("Envie o backup (CSV):", type=["csv"], key="uploader_backup_admin")
        if backup_file is not None:
            if st.button("Restaurar Base de Dados"):
                try:
                    df_backup = pd.read_csv(backup_file, dtype=str)
                    df_backup.to_csv(CSV_FILE, index=False)
                    st.success("Base restaurada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo: {e}")

    st.markdown("---")
    with st.expander("🗑️ Zerar Bases para Reimportação Limpa"):
        st.warning("Isso limpa os dados atuais para você subir os PDFs do zero e baixar o CSV novo.")
        if st.button("Confirmar: Limpar Tudo Agora"):
            pd.DataFrame(columns=COLUNAS_VINHEDO).to_csv(CSV_FILE, index=False)
            pd.DataFrame(columns=COLUNAS_ADVERSARIOS).to_csv(CSV_ADVERSARIOS, index=False)
            st.success("Bases zeradas!")
            st.rerun()

    st.markdown("---")
    st.markdown("### ✏️ Edição Direta da Base (Clique duas vezes para editar e salve abaixo)")
    if not df_historico.empty:
        df_edit_admin = st.data_editor(
            df_historico,
            use_container_width=True,
            num_rows="dynamic",
            key="admin_editor_vinhedo"
        )
        if st.button("💾 Salvar Alterações na Tabela"):
            df_edit_admin.to_csv(CSV_FILE, index=False)
            st.success("Alterações salvas com sucesso!")
            st.rerun()
