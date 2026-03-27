#!/usr/bin/env python3
"""
Script de teste mais detalhado para verificar HTML
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def analisar_html_scholar():
    """Analisa o HTML da página do Google Scholar"""
    print("🔍 ANÁLISE DETALHADA DO HTML")
    print("=" * 40)
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Testar busca simples
        url = "https://scholar.google.com.br/scholar?q=artificial+intelligence&as_ylo=2024"
        print(f"🌐 Acessando: {url}")
        
        driver.get(url)
        time.sleep(5)
        
        print(f"✅ Título: {driver.title}")
        print(f"✅ URL atual: {driver.current_url}")
        
        # Salvar HTML para análise
        html_content = driver.page_source
        
        # Procurar por diferentes padrões de resultados
        print("\n📊 ANÁLISE DE SELETORES:")
        
        seletores = [
            ("div.gs_ri", "Resultados padrão"),
            ("div[data-lid]", "Resultados com data-lid"),
            ("div.gs_r", "Resultados gs_r"),
            ("div.gs_rt", "Títulos gs_rt"),
            ("h3", "Títulos h3"),
            ("a[href*='/citations?']", "Links de citação"),
            (".gs_rt a", "Links de título"),
            ("[data-clk]", "Elementos com data-clk"),
            (".gs_a", "Autores"),
            (".gs_fl", "Footer links")
        ]
        
        for seletor, descricao in seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                print(f"   {seletor:20} -> {len(elementos):3} elementos ({descricao})")
                
                if elementos and len(elementos) <= 3:  # Mostrar detalhes para poucos elementos
                    for i, elem in enumerate(elementos[:3]):
                        try:
                            text = elem.text.strip()[:100]
                            print(f"      [{i}]: {text}")
                        except:
                            print(f"      [{i}]: <sem texto>")
                            
            except Exception as e:
                print(f"   {seletor:20} -> ERRO: {e}")
        
        # Verificar mensagens específicas
        print("\n🔍 VERIFICAÇÃO DE MENSAGENS:")
        mensagens_procurar = [
            "Sua pesquisa",
            "não retornou",
            "nenhum resultado",
            "No results",
            "Try different keywords",
            "Scholar não encontrou",
            "unusual traffic",
            "recaptcha"
        ]
        
        html_lower = html_content.lower()
        for msg in mensagens_procurar:
            if msg.lower() in html_lower:
                print(f"   ✅ Encontrado: '{msg}'")
        
        # Contar tipos de elementos
        print("\n📈 CONTAGEM DE ELEMENTOS:")
        elementos_contar = ["div", "a", "span", "p", "h1", "h2", "h3"]
        for elem in elementos_contar:
            count = len(driver.find_elements(By.TAG_NAME, elem))
            print(f"   {elem:5}: {count:4} elementos")
        
        # Salvar uma amostra do HTML
        print("\n💾 AMOSTRA DO HTML (primeiros 2000 caracteres):")
        print("-" * 50)
        print(html_content[:2000])
        print("-" * 50)
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    analisar_html_scholar()