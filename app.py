import streamlit as st
import pandas as pd
import re
import os
import itertools
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

# ==========================================
# --- FUNÇÕES DE PADRONIZAÇÃO E LIMPEZA ---
# ==========================================
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
    nome_upper = " ".join(nome_bruto.split()).upper()
    for chave, nome_oficial in DIC_ATLETAS.items():
        if re.search(rf'\b{re.escape(chave)}\b', nome_upper):
            return nome_oficial
    return "Atleta Desconhecido"

def limpar_nome_adversario(nome_bruto):
    if not isinstance(nome_bruto, str):
        return ""
    nome = re.sub(r'^\d+\s+', '', nome_bruto.strip())
    nome = re.sub(r'\s+', ' ', nome).strip()
    return nome.title()

def normalizar_categoria(cat_str):
    if not isinstance(cat_str, str):
        return "Master"
    c = cat_str.upper().strip()
    if "PRÉ" in c or "PRE" in c:
        return "PRÉ-MASTER"
    m = re.search(r'(\d{2,3}\+)', c)
    if m:
        return m.group(1)
    return c if c else "Master"

def normalizar_prova(prova_str):
    if not isinstance(prova_str, str):
        return "Estilo Não Identificado"
    p = re.sub(r'\(\d{2}/\d{2}/\d{4}\)', '', prova_str.upper())

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
    t_clean = str(tempo_str).lower().strip()
    if t_clean in ["s/t", "dql", "ausente", "n/c", ""]:
        return t_clean.upper() if t_clean in ["s/t", "dql"] else ("Ausente" if t_clean in ["ausente", "n/c"] else "S/T")
    t_clean = t_clean.replace("c", "").replace("s", ".").replace("m", ":").replace(",", ".")
    if t_clean.startswith("00:"):
        t_clean = t_clean[3:]
    # Se vier no formato 25.49 ou 1:08.12, padronizar segundos com 2 casas
    if ":" in t_clean:
        partes = t_clean.split(":")
        if len(partes) == 2 and "." in partes[1]:
            s, cs = partes[1].split(".")
            t_clean = f"{int(partes[0])}:{int(s):02d}.{cs[:2].ljust(2, '0')}"
    elif "." in t_clean:
        s, cs = t_clean.split(".")
        t_clean = f"{int(s):02d}.{cs[:2].ljust(2, '0')}"
    return t_clean

def tempo_para_segundos(tempo_str):
    try:
        t_str = str(tempo_str).strip()
        if t_str in ["S/T", "DQL", "Ausente", "None", "nan", ""]:
            return None
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
    except:
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
# --- CAPTURA DE DADOS DOS PDFs ---
# ==========================================
def processar_pdf_unami(pdf_file, nome_evento_manual, data_evento_manual):
    reader = PdfReader(pdf_file)
    vinhedo_rows = []
    adversarios_rows = []

    texto_completo = ""
    for page in reader.pages:
        texto_completo += (page.extract_text() or "") + "\n"

    linhas = [l.strip() for l in texto_completo.split("\n") if l.strip()]

    prova_atual = "Não identificada"
    categoria_atual = "Master"
    eh_revezamento = False

    i = 0
    while i < len(linhas):
        linha = linhas[i]
        linha_upper = linha.upper()

        # Detecta cabeçalho de Prova na UNAMI
        if re.match(r'^PROVA\s+\d+', linha_upper):
            bloco_cab = " ".join(linhas[i:min(i+7, len(linhas))])
            if re.search(r'(?:4\s*X\s*)?(25|50|100|200|400|800|1500)\s*M', bloco_cab, re.IGNORECASE):
                prova_atual = normalizar_prova(bloco_cab)
                eh_revezamento = "4x" in prova_atual.lower()
                cat_match = re.search(r'\(?(\d{2,3}\+)\)?', bloco_cab)
                if cat_match:
                    categoria_atual = normalizar_categoria(cat_match.group(1))

        # Atualiza categoria caso apareça isolada (ex: A(20+), $G(50+), 1(60+))
        cat_inline = re.search(r'(?:[A-P1I]\s*)?\((\d{2,3}\+)\)', linha_upper)
        if cat_inline and "RECORD" not in linha_upper and "INDICE" not in linha_upper and "_" not in linha_upper:
            categoria_atual = normalizar_categoria(cat_inline.group(1))

        # --- MODO REVEZAMENTO UNAMI ---
        # Ex: "3 976 SEL Vinhedo_A_80+_M" ou "1 28286 Clube Araraquarense FundesPort_C_80+_F"
        rev_team_match = re.match(r'^(\d+)\s+(\d{3,6})\s+(.+?_[A-Z0-9]+_(\d{2,3}\+)[_\s]*[FMX]?.*)$', linha, re.IGNORECASE)
        if rev_team_match or (eh_revezamento and re.match(r'^\d+\s+\d{3,6}\s+.+_\d{2,3}\+', linha)):
            colocacao = int(re.match(r'^(\d+)', linha).group(1))
            categoria_atual = normalizar_categoria(re.search(r'(\d{2,3}\+)', linha).group(1))
            bloco_rev = " ".join(linhas[i:min(i+16, len(linhas))])

            eh_vinhedo = ("VINHEDO" in bloco_rev.upper() or "VINHEDE" in bloco_rev.upper())
            if eh_vinhedo:
                # Tempo e Pontos do revezamento
                m_tp = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)\s+(\d+,\d{2})', bloco_rev, re.IGNORECASE)
                if m_tp:
                    tempo_final = padronizar_tempo_string(m_tp.group(1))
                    pontos_final = float(m_tp.group(2).replace(",", "."))
                elif any(w in bloco_rev.upper() for w in ["DESCLA", "D*D*", "DQL"]):
                    tempo_final = "DQL"
                    pontos_final = 0.0
                    colocacao = 0
                elif "AUSENTE" in bloco_rev.upper() or "Ñ NADOU" in bloco_rev.upper():
                    tempo_final = "Ausente"
                    pontos_final = 0.0
                    colocacao = 0
                else:
                    tempo_final = "S/T"
                    pontos_final = 0.0

                recorde_flag = "Recorde UNAMI" if re.search(r'\bRECORD\b', bloco_rev.split("Dist")[0], re.IGNORECASE) else ""

                # Identifica integrantes mapeados de Vinhedo nas próximas linhas
                integrantes_vinhedo = []
                for sub_l in linhas[i+1:min(i+12, len(linhas))]:
                    if re.match(r'^\d+\s+\d{3,6}\s+', sub_l) or sub_l.upper().startswith("PROVA "):
                        break
                    atleta_cand = normalizar_nome_atleta(sub_l)
                    if atleta_cand != "Atleta Desconhecido" and atleta_cand not in integrantes_vinhedo:
                        integrantes_vinhedo.append(atleta_cand)

                # Linha da equipe (pontuação oficial de SEL Vinhedo no revezamento)
                vinhedo_rows.append({
                    "Data": data_evento_manual,
                    "Campeonato": "UNAMI",
                    "Local/Etapa": nome_evento_manual,
                    "Prova": prova_atual,
                    "Tipo_Prova": "Revezamento",
                    "Atleta": "EQUIPE SEL VINHEDO",
                    "Categoria": categoria_atual,
                    "Colocacao": colocacao,
                    "Tempo": tempo_final,
                    "Pontos": pontos_final,
                    "Recorde": recorde_flag,
                    "Integrantes": " / ".join(integrantes_vinhedo)
                })

                # Linhas individuais dos atletas de Vinhedo para contabilizar medalhas totais
                for atl in integrantes_vinhedo:
                    vinhedo_rows.append({
                        "Data": data_evento_manual,
                        "Campeonato": "UNAMI",
                        "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual,
                        "Tipo_Prova": "Revezamento",
                        "Atleta": atl,
                        "Categoria": categoria_atual,
                        "Colocacao": colocacao,
                        "Tempo": tempo_final,
                        "Pontos": 0.0,  # Pontos do revezamento já somam na linha EQUIPE SEL VINHEDO
                        "Recorde": recorde_flag,
                        "Integrantes": " / ".join(integrantes_vinhedo)
                    })
            i += 1
            continue

        # --- MODO INDIVIDUAL UNAMI ---
        # Padrão: Pos (1..30) + Matrícula (2..6 dígitos) + Nome
        ind_match = re.match(r'^(\d{1,2})\s+(\d{2,6})\s+([A-ZÀ-ÿ].+)$', linha)
        if not eh_revezamento and ind_match and "RECORD" not in linha_upper and "PROVA" not in linha_upper:
            colocacao = int(ind_match.group(1))
            resto_linha = ind_match.group(3)
            # Junta até 4 linhas seguintes até encontrar o Tempo + Pontos (ex: 00m31s36c 10,00) ou Ausente/Descla
            bloco_atleta = resto_linha
            j = i + 1
            while j < min(i + 6, len(linhas)):
                prox = linhas[j]
                if re.match(r'^\d{1,2}\s+\d{2,6}\s+[A-ZÀ-ÿ]', prox) or prox.upper().startswith("PROVA ") or prox.upper().startswith("DIST"):
                    break
                bloco_atleta += " " + prox
                if re.search(r'\d+,\d{2}', prox):
                    break
                j += 1

            bloco_upper = bloco_atleta.upper()
            eh_vinhedo = ("VINHEDO" in bloco_upper or "VINHEDE" in bloco_upper)

            if any(w in bloco_upper for w in ["DESCLA", "D*D*", "DQL"]):
                tempo_final = "DQL"
                pontos_final = 0.0
                colocacao = 0
            elif any(w in bloco_upper for w in ["AUSENTE", "Ñ NADOU", "N/C"]):
                tempo_final = "Ausente"
                pontos_final = 0.0
                colocacao = 0
            else:
                m_tempo = re.search(r'(\d{1,2}m\d{2}s\d{2}c?)', bloco_atleta, re.IGNORECASE)
                tempo_final = padronizar_tempo_string(m_tempo.group(1)) if m_tempo else "S/T"
                m_pts = re.search(r'\b(\d{1,2},\d{2})\b', bloco_atleta)
                pontos_final = float(m_pts.group(1).replace(",", ".")) if m_pts else 0.0

            recorde_flag = "Recorde UNAMI" if re.search(r'\bRECORD\b', bloco_atleta, re.IGNORECASE) else ""

            if eh_vinhedo:
                atleta_oficial = normalizar_nome_atleta(bloco_atleta)
                if atleta_oficial != "Atleta Desconhecido":
                    vinhedo_rows.append({
                        "Data": data_evento_manual,
                        "Campeonato": "UNAMI",
                        "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual,
                        "Tipo_Prova": "Individual",
                        "Atleta": atleta_oficial,
                        "Categoria": categoria_atual,
                        "Colocacao": colocacao,
                        "Tempo": tempo_final,
                        "Pontos": pontos_final,
                        "Recorde": recorde_flag,
                        "Integrantes": ""
                    })
            else:
                # Salva adversário com tempo válido para o Radar de Provas
                if tempo_para_segundos(tempo_final) is not None:
                    nome_adv = limpar_nome_adversario(re.split(r'\d{2}m\d{2}s|SEL |EC |TCC|ARARAQUARENSE|LIMEIRA|GRAN |MASTER|BAURU|SAO JOAO|BARRA|CORPO|NATA|CLUBE|ACADEMIA|PREF|VINHAS|N1/', resto_linha, maxsplit=1)[0])
                    adversarios_rows.append({
                        "Data": data_evento_manual,
                        "Campeonato": "UNAMI",
                        "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual,
                        "Categoria": categoria_atual,
                        "Atleta": nome_adv or "Adversário",
                        "Equipe": "Adversário UNAMI",
                        "Colocacao": colocacao,
                        "Tempo": tempo_final,
                        "Pontos": pontos_final,
                        "Recorde": recorde_flag
                    })

        i += 1

    return pd.DataFrame(vinhedo_rows), pd.DataFrame(adversarios_rows)


def processar_pdf_paulista(pdf_file, nome_evento_manual, data_evento_manual):
    reader = PdfReader(pdf_file)
    vinhedo_rows = []
    adversarios_rows = []

    texto_completo = ""
    for page in reader.pages:
        texto_completo += (page.extract_text() or "") + "\n"

    linhas = [l.strip() for l in texto_completo.split("\n") if l.strip()]

    prova_atual = "Não identificada"
    faixa_atual = "Master"
    eh_revezamento = False

    i = 0
    while i < len(linhas):
        linha = linhas[i]
        linha_upper = linha.upper()

        # Cabeçalho de prova Paulista: "1ª PROVA - 400 METROS LIVRE FEMININO" ou "10ª PROVA - REVEZAMENTO..."
        if "PROVA" in linha_upper and ("METROS" in linha_upper or "REVEZAMENTO" in linha_upper):
            prova_atual = normalizar_prova(linha)
            eh_revezamento = "REVEZAMENTO" in linha_upper or "4x" in prova_atual.lower()

        # Faixa etária: "FAIXA: 35 +" ou "FAIXA: PRÉ-MASTER"
        if "FAIXA:" in linha_upper:
            bloco_faixa = " ".join(linhas[i:min(i+4, len(linhas))]).upper()
            if "PRÉ" in bloco_faixa or "PRE" in bloco_faixa:
                faixa_atual = "PRÉ-MASTER"
            else:
                m_f = re.search(r'(\d{2,3})\s*\+', bloco_faixa)
                if m_f:
                    faixa_atual = f"{m_f.group(1)}+"

        # --- REVEZAMENTO PAULISTA ---
        if eh_revezamento and ("VINHEDO" in linha_upper or "SECRETARIA MUNICIPAL DE ESPORTES E LAZER DE" in linha_upper):
            bloco_rev = " ".join(linhas[max(0, i-2):min(i+12, len(linhas))])
            if "VINHEDO" in bloco_rev.upper():
                m_col = re.search(r'\b(\d{1,2})[°º]\b', bloco_rev)
                colocacao = int(m_col.group(1)) if m_col else 0
                m_tempo = re.search(r'\b(\d{1,2}:\d{2}\.\d{2})\b', bloco_rev)
                tempo_final = padronizar_tempo_string(m_tempo.group(1)) if m_tempo else "S/T"
                rec_match = re.search(r'\b(RSP|RS|RB)\b', bloco_rev)
                recorde_flag = f"Recorde ({rec_match.group(1)})" if rec_match else ""

                integrantes = []
                for sub_l in linhas[i+1:min(i+12, len(linhas))]:
                    if re.match(r'^\d{1,2}[°º]\b', sub_l) or "FAIXA:" in sub_l.upper() or "PROVA" in sub_l.upper():
                        break
                    atl_cand = normalizar_nome_atleta(sub_l)
                    if atl_cand != "Atleta Desconhecido" and atl_cand not in integrantes:
                        integrantes.append(atl_cand)

                vinhedo_rows.append({
                    "Data": data_evento_manual,
                    "Campeonato": "Paulista",
                    "Local/Etapa": nome_evento_manual,
                    "Prova": prova_atual,
                    "Tipo_Prova": "Revezamento",
                    "Atleta": "EQUIPE SEL VINHEDO",
                    "Categoria": faixa_atual,
                    "Colocacao": colocacao,
                    "Tempo": tempo_final,
                    "Pontos": 0.0,
                    "Recorde": recorde_flag,
                    "Integrantes": " / ".join(integrantes)
                })

                for atl in integrantes:
                    vinhedo_rows.append({
                        "Data": data_evento_manual,
                        "Campeonato": "Paulista",
                        "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual,
                        "Tipo_Prova": "Revezamento",
                        "Atleta": atl,
                        "Categoria": faixa_atual,
                        "Colocacao": colocacao,
                        "Tempo": tempo_final,
                        "Pontos": 0.0,
                        "Recorde": recorde_flag,
                        "Integrantes": " / ".join(integrantes)
                    })
                i += 6
                continue

        # --- INDIVIDUAL PAULISTA ---
        # Ex: "7° 137013 ÁLVARO LOUZADA DE OLIVEIRA JUNIOR SEL VINHEDO 29.79 3,00 126,50"
        ind_p = re.match(r'^(\d{1,2})[°º]\s+(\d{3,7})\s+(.+)$', linha)
        if not eh_revezamento and ind_p:
            colocacao = int(ind_p.group(1))
            bloco_p = " ".join(linhas[i:min(i+5, len(linhas))])
            bloco_p_upper = bloco_p.upper()

            # Captura tempo (MM:SS.CC ou SS.CC) que não seja parcial entre parênteses
            bloco_sem_parciais = re.sub(r'\([^\)]*\)', '', bloco_p)
            bloco_sem_parciais = re.sub(r'\b\d{2,3}m\s*:?\s*\d{1,2}[:\.]\d{2}(?:\.\d{2})?', '', bloco_sem_parciais)
            m_t = re.search(r'\b(\d{1,2}:\d{2}\.\d{2}|\d{2}\.\d{2})\b', bloco_sem_parciais)
            tempo_final = padronizar_tempo_string(m_t.group(1)) if m_t else "S/T"

            rec_match = re.search(r'\b(RSP|RS|RB)\b', bloco_p)
            recorde_flag = f"Recorde ({rec_match.group(1)})" if rec_match else ""

            if "VINHEDO" in bloco_p_upper:
                atleta_oficial = normalizar_nome_atleta(bloco_p)
                if atleta_oficial != "Atleta Desconhecido":
                    vinhedo_rows.append({
                        "Data": data_evento_manual,
                        "Campeonato": "Paulista",
                        "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual,
                        "Tipo_Prova": "Individual",
                        "Atleta": atleta_oficial,
                        "Categoria": faixa_atual,
                        "Colocacao": colocacao,
                        "Tempo": tempo_final,
                        "Pontos": 0.0,  # Paulista não pontua para troféu anual
                        "Recorde": recorde_flag,
                        "Integrantes": ""
                    })
            else:
                if tempo_para_segundos(tempo_final) is not None:
                    nome_adv = limpar_nome_adversario(re.split(r'\b(?:T\.C\.|AD |TNT|SMEC|PINHEIROS|LIMEIRA|RIO CLARO|BARDI|OKUDA|EEF|C\.T\.|GRAN|1º DE MAIO|ACADEMIA|M\. RIO)', ind_p.group(3), maxsplit=1)[0])
                    adversarios_rows.append({
                        "Data": data_evento_manual,
                        "Campeonato": "Paulista",
                        "Local/Etapa": nome_evento_manual,
                        "Prova": prova_atual,
                        "Categoria": faixa_atual,
                        "Atleta": nome_adv or "Adversário",
                        "Equipe": "Adversário Paulista",
                        "Colocacao": colocacao,
                        "Tempo": tempo_final,
                        "Pontos": 0.0,
                        "Recorde": recorde_flag
                    })

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
    "Data", "Campeonato", "Local/Etapa", "Prova", "Categoria",
    "Atleta", "Equipe", "Colocacao", "Tempo", "Pontos", "Recorde"
]

def carregar_csv_seguro(caminho, colunas_esperadas):
    if not os.path.exists(caminho):
        return pd.DataFrame(columns=colunas_esperadas)
    df_lido = None
    for sep, enc in [(",", "utf-8"), (";", "utf-8"), (",", "latin1"), (";", "latin1")]:
        try:
            df_teste = pd.read_csv(caminho, sep=sep, encoding=enc)
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
            elif col in ["Colocacao", "Pontos"]: df_lido[col] = 0
            else: df_lido[col] = ""
    return df_lido[colunas_esperadas]

df_historico = carregar_csv_seguro(CSV_FILE, COLUNAS_VINHEDO)
df_adversarios = carregar_csv_seguro(CSV_ADVERSARIOS, COLUNAS_ADVERSARIOS)

if not df_historico.empty:
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
    df_adversarios["Prova"] = df_adversarios["Prova"].apply(normalizar_prova)
    df_adversarios["Tempo"] = df_adversarios["Tempo"].apply(padronizar_tempo_string)
    df_adversarios["Categoria"] = df_adversarios["Categoria"].apply(normalizar_categoria)

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
        "Selecione o Painel:",
        [
            "🏆 Quadro de Medalhas & Troféu",
            "👤 Visão Atleta",
            "🎯 Radar de Provas",
            "⏱️ Visão Treinador",
            "📊 Estatísticas",
            "🚀 Simulador Revezamento",
            "📤 Alimentar Base",
            "🗄️ Gerenciamento e Backup"
        ]
    )
    st.markdown("---")

# ------------------------------------------
# TELA 1: QUADRO DE MEDALHAS & TROFÉU
# ------------------------------------------
if tela_selecionada == "🏆 Quadro de Medalhas & Troféu":
    st.title("🏆 Quadro de Medalhas, Recordes & Troféu UNAMI")

    if not df_historico.empty:
        anos_disp = obter_anos_ordenados(df_historico)
        opcoes_ano = anos_disp + ["Todos os Anos"]

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            ano_sel = st.selectbox("Temporada (Padrão: Ano mais recente):", opcoes_ano, index=0)
        with col_f2:
            camp_sel = st.selectbox("Campeonato (Medalhas):", ["Todos (UNAMI + Paulista)", "UNAMI", "Paulista"], index=0)

        df_filtrado = df_historico.copy()
        df_filtrado["Ano_Str"] = pd.to_datetime(df_filtrado["Data"], format="%d/%m/%Y", errors="coerce").dt.year.fillna(0).astype(int).astype(str)

        if ano_sel != "Todos os Anos":
            df_filtrado = df_filtrado[df_filtrado["Ano_Str"] == ano_sel]

        # Pontuação Geral da Equipe na UNAMI (sempre considerando apenas UNAMI, como definido)
        df_unami_ano = df_filtrado[df_filtrado["Campeonato"] == "UNAMI"]
        pontos_gerais_vinhedo = df_unami_ano["Pontos"].sum()
        pts_ind_vinhedo = df_unami_ano[df_unami_ano["Tipo_Prova"] == "Individual"]["Pontos"].sum()
        pts_rev_vinhedo = df_unami_ano[df_unami_ano["Tipo_Prova"] == "Revezamento"]["Pontos"].sum()

        # Filtro de campeonato para quadro de medalhas
        if camp_sel == "UNAMI":
            df_med = df_filtrado[df_filtrado["Campeonato"] == "UNAMI"]
        elif camp_sel == "Paulista":
            df_med = df_filtrado[df_filtrado["Campeonato"] == "Paulista"]
        else:
            df_med = df_filtrado

        # Medalhas da Equipe (Individual + 1 por Revezamento de Equipe)
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

        st.markdown(f"### 🏅 Desempenho Geral SEL Vinhedo — {ano_sel}")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("🏆 Pontos UNAMI (Equipe)", f"{pontos_gerais_vinhedo:.2f}".replace(".", ","), f"Ind: {pts_ind_vinhedo:.1f} | Rev: {pts_rev_vinhedo:.1f}")
        k2.metric("🥇 Ouros", int(ouros_eq))
        k3.metric("🥈 Pratas", int(pratas_eq))
        k4.metric("🥉 Bronzes", int(bronzes_eq))
        k5.metric("⚡ Recordes", len(recordes_eq))

        st.markdown("---")

        # --- PONTUAÇÃO POR ETAPA UNAMI ---
        if not df_unami_ano.empty:
            st.markdown("#### 📈 Pontuação de SEL Vinhedo por Etapa (UNAMI)")
            df_etapas = df_unami_ano.groupby(["Data", "Local/Etapa", "Tipo_Prova"])["Pontos"].sum().unstack(fill_value=0).reset_index()
            if "Individual" not in df_etapas.columns: df_etapas["Individual"] = 0.0
            if "Revezamento" not in df_etapas.columns: df_etapas["Revezamento"] = 0.0
            df_etapas["Total Etapa"] = df_etapas["Individual"] + df_etapas["Revezamento"]
            st.dataframe(df_etapas[["Data", "Local/Etapa", "Individual", "Revezamento", "Total Etapa"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        col_r1, col_r2 = st.columns(2)

        # --- RANKING DE PONTOS POR PESSOA (UNAMI) ---
        with col_r1:
            st.markdown(f"#### 🏆 Ranking Individual de Pontos UNAMI ({ano_sel})")
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

        # --- QUADRO DE MEDALHAS POR PESSOA (INDIVIDUAL + REVEZAMENTO) ---
        with col_r2:
            st.markdown(f"#### 🥇 Quadro de Medalhas por Atleta ({camp_sel})")
            df_med_pessoas = df_med[df_med["Atleta"] != "EQUIPE SEL VINHEDO"].copy()
            if not df_med_pessoas.empty:
                atletas_com_provas = sorted(df_med_pessoas["Atleta"].unique())
                linhas_quadro = []
                for atl in atletas_com_provas:
                    sub = df_med_pessoas[df_med_pessoas["Atleta"] == atl]
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

        # --- QUADRO À PARTE: REVEZAMENTOS DE VINHEDO ---
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

        # --- MURAL DE RECORDES ---
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
    else:
        st.info("A base está vazia. Vá em '📤 Alimentar Base' para importar os PDFs.")

# ------------------------------------------
# TELA 2: VISÃO ATLETA
# ------------------------------------------
elif tela_selecionada == "👤 Visão Atleta":
    st.title("Ficha de Rendimento Individual")
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

        # Cards de Conquistas do Atleta
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
        st.info("O arquivo CSV histórico está vazio ou não foi encontrado.")

# ------------------------------------------
# TELA 3: RADAR DE PROVAS (COMPARATIVO)
# ------------------------------------------
elif tela_selecionada == "🎯 Radar de Provas":
    st.title("🎯 Radar de Provas: Onde você tem mais chances?")
    st.markdown("Compara os seus **melhores tempos (PRs)** com todos os resultados reais da sua **faixa etária** registrados nos campeonatos importados.")

    if df_historico.empty or df_adversarios.empty:
        st.info("Importe pelo menos um PDF completo (UNAMI ou Paulista) na aba '📤 Alimentar Base' para ativar a comparação com os adversários.")
    else:
        lista_atletas = sorted([a for a in df_historico["Atleta"].unique() if a != "EQUIPE SEL VINHEDO"])
        col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
        with col_r1:
            atleta_radar = st.selectbox("Selecione o Atleta:", lista_atletas)
        with col_r2:
            ano_ref_radar = st.number_input("Ano de referência para faixa etária:", min_value=2025, max_value=2030, value=2027)
        with col_r3:
            camp_radar = st.selectbox("Base de Adversários:", ["Todos", "UNAMI", "Paulista"])

        faixa_atleta = obter_faixa_etaria_atleta(atleta_radar, ano_ref_radar)
        st.info(f"👤 **{atleta_radar}** | Idade em {ano_ref_radar}: **{calcular_idade(atleta_radar, ano_ref_radar)} anos** → Categoria: **{faixa_atleta}**")

        # PRs individuais do atleta
        df_atl_ind = df_historico[(df_historico["Atleta"] == atleta_radar) & (df_historico["Tipo_Prova"] == "Individual")].copy()
        df_atl_ind["Segundos"] = df_atl_ind["Tempo"].apply(tempo_para_segundos)
        df_atl_ind = df_atl_ind.dropna(subset=["Segundos"])

        df_adv_base = df_adversarios.copy()
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

                # Busca adversários da mesma prova e mesma faixa etária
                df_comp = df_adv_base[(df_adv_base["Prova"] == prova_nome) & (df_adv_base["Categoria"] == faixa_atleta)]
                if df_comp.empty:
                    continue

                # Melhor tempo histórico de cada adversário único naquela prova/faixa
                melhores_adv = df_comp.groupby("Atleta")["Segundos"].min().sort_values()
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
                st.markdown(f"### 📊 Ranking de Competitividade na Categoria {faixa_atleta}")
                st.dataframe(
                    df_radar.drop(columns=["Pos_Num"]),
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")
                st.markdown("#### 🔍 Detalhamento dos Principais Rivais por Prova")
                prova_detalhe = st.selectbox("Escolha uma prova para ver os tempos dos adversários:", df_radar["Prova"].tolist())
                df_rivais_det = df_adv_base[(df_adv_base["Prova"] == prova_detalhe) & (df_adv_base["Categoria"] == faixa_atleta)].copy()
                idx_min_adv = df_rivais_det.groupby("Atleta")["Segundos"].idxmin()
                df_top_rivais = df_rivais_det.loc[idx_min_adv].sort_values("Segundos").head(10)
                df_top_rivais["Rank"] = range(1, len(df_top_rivais) + 1)
                st.dataframe(
                    df_top_rivais[["Rank", "Atleta", "Tempo", "Local/Etapa", "Data"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning(f"Ainda não há registros de adversários na categoria **{faixa_atleta}** para as provas que {atleta_radar} já nadou.")

# ------------------------------------------
# TELA 4: VISÃO TREINADOR
# ------------------------------------------
elif tela_selecionada == "⏱️ Visão Treinador":
    st.title("Ranking Interno da Equipe por Prova")
    if not df_historico.empty:
        df_ind = df_historico[df_historico["Tipo_Prova"] == "Individual"].copy()
        lista_provas = sorted(df_ind["Prova"].unique())
        prova_sel = st.selectbox("Selecione a Prova para ver o Ranking interno:", lista_provas, key="treinador_prova_sel")

        df_prova_rank = df_ind[df_ind["Prova"] == prova_sel].copy()
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
# TELA 5: ESTATÍSTICAS
# ------------------------------------------
elif tela_selecionada == "📊 Estatísticas":
    st.title("📊 Raio-X de Participação da Equipe")

    if not df_historico.empty:
        df_pessoas = df_historico[df_historico["Atleta"] != "EQUIPE SEL VINHEDO"].copy()
        anos_disponiveis = obter_anos_ordenados(df_pessoas) + ["Todos os Anos"]
        ano_selecionado = st.selectbox("Selecione a Temporada para Análise:", anos_disponiveis, index=0, key="stats_ano_filter")

        if ano_selecionado == "Todos os Anos":
            df_stats = df_pessoas
            st.markdown("### 🌎 Métricas Globais (Histórico Acumulado)")
        else:
            df_stats = df_pessoas[pd.to_datetime(df_pessoas["Data"], format="%d/%m/%Y", errors="coerce").dt.year == int(ano_selecionado)]
            st.markdown(f"### 📅 Métricas Consolidadas da Temporada {ano_selecionado}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Atletas Ativos no Período", df_stats["Atleta"].nunique())
        c2.metric("Total de Caídas na Água", len(df_stats))
        c3.metric("Total de Etapas/Competições", df_stats["Local/Etapa"].nunique())

        st.markdown("---")

        col_rank1, col_rank2 = st.columns(2)
        with col_rank1:
            st.markdown(f"#### 🏊 Atletas com Maior Volume de Provas ({ano_selecionado})")
            assiduidade = df_stats["Atleta"].value_counts().reset_index()
            assiduidade.columns = ["Atleta", "Nº de Provas (Ind + Rev)"]
            st.dataframe(assiduidade.head(15), use_container_width=True, hide_index=True)

        with col_rank2:
            st.markdown(f"#### 🏟️ Eventos com Maior Delegação de Vinhedo ({ano_selecionado})")
            delegacao = df_stats.groupby(["Data", "Campeonato", "Local/Etapa"])["Atleta"].nunique().reset_index()
            delegacao.columns = ["Data", "Campeonato", "Competição", "Atletas Presentes"]
            delegacao = delegacao.sort_values("Atletas Presentes", ascending=False)
            st.dataframe(delegacao, use_container_width=True, hide_index=True)
    else:
        st.info("Estatísticas não disponíveis (Base Vazia).")

# ------------------------------------------
# TELA 6: SIMULADOR DE REVEZAMENTO
# ------------------------------------------
elif tela_selecionada == "🚀 Simulador Revezamento":
    st.title("🚀 Inteligência Estratégica: Top Revezamentos")

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

# ------------------------------------------
# TELA 7: ALIMENTAR BASE
# ------------------------------------------
elif tela_selecionada == "📤 Alimentar Base":
    st.subheader("Entrada de Dados e Atualização do Painel")
    c_pdf, col_manual = st.columns(2)
    with c_pdf:
        st.markdown("### 📤 Upload de Relatórios Oficiais (PDF)")
        tipo_relatorio_selecionado = st.selectbox("Formato do Relatório PDF:", ["UNAMI", "Paulista (FAP)"])
        nome_evento_pdf = st.text_input("Nome/Local da Competição (Ex: 13º Troféu EC Barbarense):", key="nome_ev_pdf")
        data_evento_pdf = st.date_input("Data da Competição:", key="data_ev_pdf")
        uploaded_file = st.file_uploader("Arraste o PDF aqui (Individual ou Revezamento):", type=["pdf"])

        if uploaded_file is not None:
            if not nome_evento_pdf:
                st.warning("⚠️ Por favor, digite o Nome da Competição acima antes de processar.")
            else:
                if st.button("Processar e Fundir Dados"):
                    data_formatada = data_evento_pdf.strftime("%d/%m/%Y")
                    df_novos_v, df_novos_adv = processar_pdf(
                        uploaded_file, tipo_relatorio_selecionado, nome_evento_pdf, data_formatada
                    )

                    if not df_novos_v.empty:
                        df_total = pd.concat([df_historico, df_novos_v]).drop_duplicates(
                            subset=["Data", "Campeonato", "Prova", "Tipo_Prova", "Atleta", "Tempo"]
                        )
                        df_total.to_csv(CSV_FILE, index=False)

                        if not df_novos_adv.empty:
                            df_adv_total = pd.concat([df_adversarios, df_novos_adv]).drop_duplicates(
                                subset=["Data", "Campeonato", "Prova", "Categoria", "Atleta", "Tempo"]
                            )
                            df_adv_total.to_csv(CSV_ADVERSARIOS, index=False)

                        st.success(f"Sucesso! {len(df_novos_v)} registros de Vinhedo e {len(df_novos_adv)} marcas de adversários unificados!")
                        st.rerun()
                    else:
                        st.warning("Nenhum atleta ou revezamento de SEL Vinhedo foi encontrado neste arquivo.")

    with col_manual:
        st.markdown("### ✍️ Lançamento Manual (Treinos / Correções)")
        camp_m = st.selectbox("Campeonato / Contexto:", ["UNAMI", "Paulista", "Treino / Controle"], key="manual_camp")
        tipo_m = st.selectbox("Tipo de Prova:", ["Individual", "Revezamento"], key="manual_tipo")
        lista_atletas_v = ["EQUIPE SEL VINHEDO"] + sorted(list(ANOS_NASCIMENTO.keys()))
        atleta_m = st.selectbox("Selecione o Atleta (ou Equipe):", lista_atletas_v, key="manual_atleta")
        prova_m = st.selectbox("Estilo/Distância da Prova:", [
            "25m Livre", "25m Costas", "25m Peito", "25m Borboleta",
            "50m Livre", "50m Peito", "50m Costas", "50m Borboleta",
            "100m Livre", "100m Peito", "100m Costas", "100m Borboleta", "100m Medley",
            "200m Livre", "200m Costas", "400m Livre",
            "Rev. 4x25m Livre", "Rev. 4x50m Livre", "Rev. 4x50m Medley"
        ], key="manual_prova")
        gen_m = st.selectbox("Gênero da Prova:", ["Fem", "Masc", "Misto"], key="manual_gen")
        cat_m = st.text_input("Categoria (ex: 35+, 40+, 160+):", value="40+", key="manual_cat")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            colocacao_m = st.number_input("Colocação (0 se treino):", min_value=0, max_value=50, value=1, key="manual_col")
        with col_m2:
            pontos_m = st.number_input("Pontos (Apenas UNAMI):", min_value=0.0, max_value=30.0, value=0.0, step=0.5, key="manual_pts")
        data_m = st.date_input("Data da Coleta:", key="manual_data")
        local_m = st.text_input("Etapa/Descrição do Local:", value="Treino SEL Vinhedo", key="manual_local")
        tempo_m = st.text_input("Tempo Registrado (ex: 28.54 ou 1:04.25):", placeholder="MM:SS.CC ou SS.CC", key="manual_tempo")
        rec_m = st.text_input("Recorde (opcional, ex: Recorde UNAMI):", value="", key="manual_rec")

        if st.button("Gravar Registro Manual"):
            if tempo_m and data_m:
                t_padrao = padronizar_tempo_string(tempo_m)
                pts_final_m = pontos_m if camp_m == "UNAMI" else 0.0
                nova_linha = pd.DataFrame([{
                    "Data": data_m.strftime("%d/%m/%Y"),
                    "Campeonato": camp_m,
                    "Local/Etapa": local_m,
                    "Prova": f"{prova_m} {gen_m}",
                    "Tipo_Prova": tipo_m,
                    "Atleta": atleta_m,
                    "Categoria": normalizar_categoria(cat_m),
                    "Colocacao": int(colocacao_m),
                    "Tempo": t_padrao,
                    "Pontos": float(pts_final_m),
                    "Recorde": rec_m,
                    "Integrantes": ""
                }])
                df_total = pd.concat([df_historico, nova_linha]).drop_duplicates(
                    subset=["Data", "Campeonato", "Prova", "Tipo_Prova", "Atleta", "Tempo"]
                )
                df_total.to_csv(CSV_FILE, index=False)
                st.success("Registro adicionado com sucesso!")
                st.rerun()

# ------------------------------------------
# TELA 8: GERENCIAMENTO E BACKUP
# ------------------------------------------
elif tela_selecionada == "🗄️ Gerenciamento e Backup":
    st.subheader("🗄️ Painel de Controle Administrativo do CSV")

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
                    df_backup = pd.read_csv(backup_file)
                    df_backup.to_csv(CSV_FILE, index=False)
                    st.success("Base restaurada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo: {e}")

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
