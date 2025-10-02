import streamlit as st
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# Função específica site IFUSP

def obter_eventos_ifusp():
    url_base = "https://portal.if.usp.br"
    url = f"{url_base}/ifusp/pt-br/eventos"

    try:
        response = requests.get(url, verify=True)
        soup = BeautifulSoup(response.content, "html.parser")
        eventos = []

        blocos_eventos = soup.find_all("div", class_="content")

        for bloco in blocos_eventos:
            titulo_tag = bloco.select_one("div.field-name-body h5")
            data_tag = bloco.select_one("div.field-name-field-data-inicio-evento span.date-display-single")
            link_tag = bloco.select_one("footer a")

            if titulo_tag and data_tag:
                titulo = titulo_tag.get_text(strip=True).replace("\xa0", " ")
                data = data_tag.get_text(strip=True)
                data = data[0].upper() + data[1:] if data else data
                link = urljoin(url_base, link_tag.get("href")) if link_tag else url

                if "2025" in data or "2025" in titulo:
                        eventos.append({
                            "titulo": titulo,
                            "data": data,
                            "link": link
                    })

        if not eventos:
            return [{"titulo": "Nenhum evento de 2025 encontrado no IFUSP.", "data": "", "link": ""}]
        return eventos

    except Exception as e:
        return [{"titulo": f"[ERRO - IFUSP] {str(e)}", "data": "", "link": ""}]
    
    # Função específica site IFSC-USP

def obter_eventos_ifsc_usp():
    url = "https://www2.ifsc.usp.br/portal-ifsc/eventos/"

    try:
        response = requests.get(url, verify=True)
        soup = BeautifulSoup(response.content, "html.parser")
        eventos = []

        artigos = soup.select("section.latest_news article")

        for artigo in artigos:
            titulo_tag = artigo.select_one("h5.clean_heading a.title")
            data_tag = artigo.select_one("span.date")

            if titulo_tag and data_tag:
                titulo = titulo_tag.get_text(strip=True)
                data = data_tag.get_text(strip=True)
                link = titulo_tag.get("href")

                if "2025" in data or "2025" in titulo:
                    eventos.append({
                        "titulo": titulo,
                        "data": data,
                        "link": link
                    })

        if not eventos:
            return [{"titulo": "Nenhum evento de 2025 encontrado no IFSC-USP.", "data": "", "link": ""}]
        return eventos

    except Exception as e:
        return [{"titulo": f"[ERRO - IFSC-USP] {str(e)}", "data": "", "link": ""}]
    
    # Função específica site IFT

def obter_eventos_ift():
    url = "https://www.ictp-saifr.org/2025-embed-activities/"

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        eventos = []

        paragrafos = soup.find_all("p", style="text-align: center;")

        for p in paragrafos:
            link_tag = p.find("a")
            texto_completo = p.get_text(separator="\n", strip=True).split("\n")

            if link_tag and len(texto_completo) >= 2:
                titulo = link_tag.get_text(strip=True)
                data_en = texto_completo[1]
                data_pt = converter_data_ingles_para_portugues(data_en)
                link = link_tag["href"]

                if re.match(r"^\s*[a-z]+\s*[-–]\s*[a-z]+\s*,?\s*\d{4}\s*$", data_en.lower()):
                    continue

                if "2025" in data_pt or "2025" in titulo:
                    eventos.append({
                        "titulo": titulo,
                        "data": data_pt,
                        "link": link
                    })

        if not eventos:
            return [{"titulo": "Nenhum evento encontrado na página do IFT.", "data": "", "link": ""}]
        return eventos

    except Exception as e:
        return [{"titulo": f"[ERRO - IFT] {str(e)}", "data_en": "", "link": ""}]
    
    # Função específica site UFRJ

def obter_eventos_ufrj():
    url = "https://www.if.ufrj.br/eventos/list/"

    try:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.content, "html.parser")
        eventos = []

        blocos_eventos = soup.select("div.tribe-events-loop > div[id^='post-']")

        for bloco in blocos_eventos:
            titulo_tag = bloco.select_one("h3.tribe-events-list-event-title a")
            data_inicio_tag = bloco.select_one("span.tribe-event-date-start")
            data_fim_tag = bloco.select_one("span.tribe-event-date-end")

            if not (titulo_tag and data_inicio_tag):
                continue

            titulo = titulo_tag.get_text(strip=True)
            link = titulo_tag["href"]
            title_attr = titulo_tag.get("title", "")

            data_inicio = data_inicio_tag.get_text(strip=True)
            data_fim = data_fim_tag.get_text(strip=True) if data_fim_tag else ""

            def extrair_dia_mes(texto):
                match = re.search(r"(\d{1,2}) de ([a-zç]+)", texto.lower())
                return match.groups() if match else ("", "")

            def extrair_ano(texto):
                match = re.search(r"\d{2}/\d{2}/(\d{4})", texto)
                return match.group(1) if match else "2025"

            dia_i, mes_i = extrair_dia_mes(data_inicio)
            dia_f, mes_f = extrair_dia_mes(data_fim)
            ano = extrair_ano(title_attr)

            if not (dia_i and mes_i and ano):
                continue

            if dia_f and mes_f:
                if mes_i == mes_f:
                    data_formatada = f"{dia_i}–{dia_f} de {mes_i} de {ano}"
                else:
                    data_formatada = f"{dia_i} de {mes_i} a {dia_f} de {mes_f} de {ano}"
            else:
                data_formatada = f"{dia_i} de {mes_i} de {ano}"

            eventos.append({
                "titulo": titulo,
                "data": data_formatada,
                "link": link
            })

        if not eventos:
            return [{"titulo": "Nenhum evento de 2025 encontrado na UFRJ.", "data": "", "link": ""}]
        return eventos

    except Exception as e:
        return [{"titulo": f"[ERRO - UFRJ] {str(e)}", "data": "", "link": ""}]
    
    # Função para demais sites

def extrair_eventos_generico(url, seletor_item, site_nome):
    try:
        response = requests.get(url, verify=True)
        soup = BeautifulSoup(response.content, "html.parser")
        eventos = []

        for tag in soup.select(seletor_item):
            texto = tag.get_text(strip=True)
            link = tag.get("href")

            if not link or not link.startswith("http"):
                link = url  # fallback: usar a página principal

            if "2025" in texto and any(palavra in texto.lower() for palavra in ["evento", "seminário", "colóquio"]):
                eventos.append({
                    "titulo": texto,
                    "data": "2025",  # como o ano é a única data garantida, usamos isso como placeholder
                    "link": link
                })

        if not eventos:
            return [{"titulo": f"Nenhum evento de 2025 encontrado no {site_nome}.", "data": "", "link": ""}]
        return eventos
    except Exception as e:
        return [{"titulo": f"[ERRO - {site_nome}] {str(e)}", "data": "", "link": ""}]
    
    # Função datas

def data_futura_ou_em_2025(data_str):
    try:
        if "2025" not in data_str:
            return False

        match_intervalo = re.search(r"(\d{1,2})\s*(?:a|–|-)\s*(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", data_str.lower())
        if match_intervalo:
            dia_inicio, _, mes_str, ano = match_intervalo.groups()
        else:

            match = re.search(r"(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", data_str.lower())
            if match:
                dia_inicio, mes_str, ano = match.groups()
            else:
                return True

        meses = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
            "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }

        mes = meses.get(mes_str)
        if not mes:
            return True

        data_evento = datetime(int(ano), mes, int(dia_inicio))
        return data_evento >= datetime.today()

    except:
        return True
    
    # Função formatação de datas

def formatar_data_padrao(data_str):
    if not data_str:
        return ""

    data_str = data_str.strip().lower()

    meses = {
        "janeiro": "janeiro", "fevereiro": "fevereiro", "março": "março", "abril": "abril",
        "maio": "maio", "junho": "junho", "julho": "julho", "agosto": "agosto",
        "setembro": "setembro", "outubro": "outubro", "novembro": "novembro", "dezembro": "dezembro"
    }

    match_intervalo = re.match(r"(\d{1,2})\s*[a–-]\s*(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", data_str)
    if match_intervalo:
        dia_ini, dia_fim, mes, ano = match_intervalo.groups()
        mes_pt = meses.get(mes, mes)
        return f"{dia_ini} a {dia_fim} de {mes_pt} de {ano}"

    match_intervalo_mes = re.match(r"(\d{1,2})\s*de\s*([a-zç]+)\s*[a–-]\s*(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", data_str)
    if match_intervalo_mes:
        dia1, mes1, dia2, mes2, ano = match_intervalo_mes.groups()
        mes1_pt = meses.get(mes1, mes1)
        mes2_pt = meses.get(mes2, mes2)
        return f"{dia1} de {mes1_pt} a {dia2} de {mes2_pt} de {ano}"

    match_unica = re.match(r"(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", data_str)
    if match_unica:
        dia, mes, ano = match_unica.groups()
        mes_pt = meses.get(mes, mes)
        return f"{dia} de {mes_pt} de {ano}"

    return data_str

# Função tradução de datas

def converter_data_ingles_para_portugues(data_en):
    meses = {
        "january": "janeiro", "february": "fevereiro", "march": "março",
        "april": "abril", "may": "maio", "june": "junho", "july": "julho",
        "august": "agosto", "september": "setembro", "october": "outubro",
        "november": "novembro", "december": "dezembro"
    }

    data_en = data_en.lower().strip()

    match_intervalo_meses = re.match(
        r"([a-z]+)\s+(\d{1,2})\s*[-–]\s*([a-z]+)\s+(\d{1,2}),?\s*(\d{4})", data_en
    )
    if match_intervalo_meses:
        mes1, dia1, mes2, dia2, ano = match_intervalo_meses.groups()
        mes1_pt = meses.get(mes1, mes1)
        mes2_pt = meses.get(mes2, mes2)
        return f"{dia1} de {mes1_pt} a {dia2} de {mes2_pt} de {ano}"

    match_range = re.match(r"([a-z]+)\s+(\d{1,2})\s*[-–]\s*(\d{1,2}),?\s*(\d{4})", data_en)
    if match_range:
        mes, dia_inicio, dia_fim, ano = match_range.groups()
        mes_pt = meses.get(mes, mes)
        return f"{dia_inicio}–{dia_fim} de {mes_pt} de {ano}"

    match_unico = re.match(r"([a-z]+)\s+(\d{1,2}),?\s*(\d{4})", data_en)
    if match_unico:
        mes, dia, ano = match_unico.groups()
        mes_pt = meses.get(mes, mes)
        return f"{dia} de {mes_pt} de {ano}"

    return data_en

# Função eventos duplicados

def remover_eventos_duplicados(eventos):
    vistos = set()
    unicos = []
    for e in eventos:
        chave = (e["titulo"], e["data"])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(e)
    return unicos

# Função eventos 1 dia

def evento_tem_intervalo(data_str):
    if not data_str:
        return False

    data_str = data_str.lower()

    if re.search(r"\b(\d{1,2})\s*(a|–|-)\s*(\d{1,2})\s*de\s*[a-zç]+(?:\s*de\s*\d{4})?", data_str):
        return True

    if re.search(r"\b\d{1,2}\s*de\s*[a-zç]+\s*(a|–|-)\s*\d{1,2}\s*de\s*[a-zç]+\s*de\s*\d{4}", data_str):
        return True

    if re.search(r"entre\s*\d{1,2}\s*(e|a|–|-)\s*\d{1,2}\s*de\s*[a-zç]+\s*de\s*\d{4}", data_str):
        return True

    return False

# Funções genéricas

# Brasília
def obter_eventos_cif_unb():
    return extrair_eventos_generico("https://cif.unb.br/", "h3, h4, li, p, span, a", "CIF-UnB")

# São Paulo
def obter_eventos_unicamp():
    return extrair_eventos_generico("https://sites.ifi.unicamp.br/eventos/", "h3, h4, li, p, span, a", "UNICAMP")

def obter_eventos_cbpf():
    return extrair_eventos_generico("https://www.gov.br/cbpf/pt-br/eventos", "h3, h4, li, p, span, a", "CBPF")

# Espírito Santo
def obter_eventos_ufes():
    return extrair_eventos_generico("https://fisica.alegre.ufes.br/tags/evento", "h3, h4, li, p, span, a", "UFES")

# Minas Gerais
def obter_eventos_ufmg():
    return extrair_eventos_generico("https://www.fisica.ufmg.br/eventos/", "h3, h4, li, p, span, a", "UFMG")

def obter_eventos_ufop():
    return extrair_eventos_generico("https://fisica.ufop.br/calendar/upcoming", "h3, h4, li, p, span, a", "UFOP")

# Goiás
def obter_eventos_ufg():
    return extrair_eventos_generico("https://if.ufg.br/p/47120-workshop-do-ppgf", "h3, h4, li, p, span, a", "UFG")

# Mato Grosso do Sul
def obter_eventos_ufms():
    return extrair_eventos_generico("https://petfisica.ufms.br/eventos/", "h3, h4, li, p, span, a", "UFMS")

# Função principal

def listar_eventos(cidade):
    cidade = cidade.lower()
    eventos = []

    if cidade in ["brasília", "brasilia", "df", "todos"]:
        eventos += [{"local": "📍 Brasília (CIF-UnB)", **e} for e in obter_eventos_cif_unb()]

    if cidade in ["são paulo", "sao paulo", "sp", "todos"]:
        eventos += [{"local": "📍 São Paulo (IFUSP)", **e} for e in obter_eventos_ifusp()]
        eventos += [{"local": "📍 São Paulo (IFSC-USP)", **e} for e in obter_eventos_ifsc_usp()]
        eventos += [{"local": "📍 São Paulo (UNICAMP)", **e} for e in obter_eventos_unicamp()]
        eventos += [{"local": "📍 São Paulo (IFT-UNESP)", **e} for e in obter_eventos_ift()]

    if cidade in ["rio de janeiro", "rj", "todos"]:
        eventos += [{"local": "📍 Rio de Janeiro (UFRJ)", **e} for e in obter_eventos_ufrj()]
        eventos += [{"local": "📍 Rio de Janeiro (CBPF)", **e} for e in obter_eventos_cbpf()]

    if cidade in ["espírito santo", "espirito santo", "es", "todos"]:
        eventos += [{"local": "📍 Esírito Santo (UFES)", **e} for e in obter_eventos_ufes()]

    if cidade in ["minas gerais", "mg", "todos"]:
        eventos += [{"local": "📍 Minas Gerais (UFMG)", **e} for e in obter_eventos_ufmg()]
        eventos += [{"local": "📍 Minas Gerais (UFOP)", **e} for e in obter_eventos_ufop()]

    if cidade in ["goiás", "goias", "go", "todos"]:
        eventos += [{"local": "📍 Goiás (UFG)", **e} for e in obter_eventos_ufg()]

    if cidade in ["mato grosso do sul", "ms", "todos"]:
        eventos += [{"local": "📍 Mato Grosso do Sul (UFMS)", **e} for e in obter_eventos_ufms()]

    eventos = [e for e in eventos if data_futura_ou_em_2025(e['data'])]
    eventos = [e for e in eventos if evento_tem_intervalo(e['data'])]
    eventos = remover_eventos_duplicados(eventos)

    for evento in eventos:
        evento["data"] = formatar_data_padrao(evento["data"])

    eventos.sort(key=lambda e: converter_para_datetime(e["data"])) # ordem cronológica

    return eventos if eventos else [{"titulo": "Nenhuma cidade reconhecida.", "data": "", "link": "", "local": ""}]

# Função para ordem cronológica

def converter_para_datetime(data_str):
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
        "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }

    try:
        match = re.search(r"(\d{1,2})\s*de\s*([a-zç]+)\s*de\s*(\d{4})", data_str.lower())
        if match:
            dia, mes_str, ano = match.groups()
            mes = meses.get(mes_str)
            if mes:
                return datetime(int(ano), mes, int(dia))
    except:
        pass
    return datetime.max  # se não conseguir converter, manda pro fim da lista

st.set_page_config(page_title="Eventos de Física", layout="centered")

st.title("🔭 Sistema de Eventos de Física")
st.markdown("### Consulte eventos de Física em universidades brasileiras")

cidade_desejada = st.text_input("Digite uma cidade, estado (ex: Brasília, Rio de Janeiro, São Paulo) ou 'Todos':", "")

if st.button("🔎 Buscar eventos"):
    st.write(f"### Resultados para **{cidade_desejada.title()}** em 2025:")

    eventos = listar_eventos(cidade_desejada)

    if not eventos:
        st.warning("Nenhum evento encontrado.")
    else:
        for evento in eventos:
            with st.container():
                st.markdown(f"**{evento['local']}**")
                st.markdown(f"📌 {evento['titulo']}")
                st.markdown(f"🗓️ {evento['data']}")
                if evento['link']:
                    st.markdown(f"[🔗 Mais informações]({evento['link']})")
                st.markdown("---")
