#!/usr/bin/env python3
"""
Versão SUPER SIMPLES do web scraping com Selenium
"""

import os
import re
import sqlite3
import time
import threading

# Variável global para compatibilidade com app.py
progresso_busca = {'status': 'idle', 'progresso': 0, 'total_resultados': 0, 'topico_atual': ''}

def executar_web_scraping_selenium_simples(topicos_selecionados, ano_inicio, ano_fim, min_resultados, debug_mode=False):
    """Versão mais simples possível com Selenium"""
    global progresso_busca
    
    try:
        print("🚀 Iniciando Selenium SIMPLES...")
        print(f"🔄 Resetando progresso para nova busca...")
        progresso_busca['status'] = 'iniciando selenium'
        progresso_busca['progresso'] = 0
        progresso_busca['total_resultados'] = 0
        progresso_busca['topico_atual'] = ''
        
        # Tentar Chrome primeiro (mais simples)
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            
            print("📦 Configurando Chrome...")
            
            # Opções mínimas do Chrome com anti-detecção
            chrome_options = Options()
            if not debug_mode:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Criar driver (Selenium vai tentar encontrar automaticamente)
            print("🌐 Iniciando Chrome...")
            driver = webdriver.Chrome(options=chrome_options)
            
            # Executar script para esconder que é automação
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome iniciado com sucesso!")
            
        except Exception as e_chrome:
            print(f"❌ Chrome falhou: {e_chrome}")
            
            # Tentar Edge se Chrome falhar
            try:
                print("📦 Tentando Edge...")
                edge_options = webdriver.EdgeOptions()
                edge_options.add_argument("--headless")
                edge_options.add_argument("--no-sandbox")
                
                driver = webdriver.Edge(options=edge_options)
                print("✅ Edge iniciado com sucesso!")
                
            except Exception as e_edge:
                print(f"❌ Edge falhou: {e_edge}")
                progresso_busca['status'] = f'erro: Nenhum navegador disponível. Instale Chrome ou Edge.'
                return
        
        progresso_busca['status'] = 'navegador iniciado'
        progresso_busca['progresso'] = 15
        
        # Configurar banco de dados
        print("💾 Configurando banco...")
        conn = sqlite3.connect("buscas_completas_CQ.db")
        cursor = conn.cursor()
        
        # Limpar dados antigos antes de iniciar nova busca
        print("🧹 Limpando dados antigos...")
        try:
            # Verificar quantos registros existem antes da limpeza
            count_before = cursor.execute("SELECT COUNT(*) FROM resultados_detalhados_CQ").fetchone()[0]
            print(f"   📋 Registros existentes: {count_before}")
            
            # Fazer limpeza completa
            cursor.execute("DELETE FROM resultados_detalhados_CQ")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='resultados_detalhados_CQ'")
            
            # Forçar commit imediato
            conn.commit()
            
            # Verificar se limpeza foi efetiva
            count_after = cursor.execute("SELECT COUNT(*) FROM resultados_detalhados_CQ").fetchone()[0]
            print(f"   ✅ Registros após limpeza: {count_after}")
            
        except Exception as e:
            print(f"   ⚠️ Aviso na limpeza: {e}")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados_detalhados_CQ (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                ano_publicacao INTEGER,
                autores TEXT,
                fonte_publicacao TEXT,
                resumo TEXT,
                url_artigo TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✅ Banco limpo e configurado para nova busca!")
        
        total_resultados = 0
        
        # Processar cada tópico
        for i, topico in enumerate(topicos_selecionados):
            print(f"🔍 Buscando: {topico}")
            progresso_busca['topico_atual'] = topico
            progresso_busca['progresso'] = 15 + ((i / len(topicos_selecionados)) * 80)
            
            # Traduzir/melhorar termos de busca em português para inglês (melhor cobertura)
            traducoes = {
                'algoritmos quânticos': ['quantum algorithms', 'quantum computing algorithms'],
                'criptografia pós-quântica': ['post-quantum cryptography', 'quantum-resistant cryptography'],
                'computação quântica': ['quantum computing', 'quantum computation'],
                'machine learning quântico': ['quantum machine learning', 'quantum ML'],
                'inteligência artificial quântica': ['quantum artificial intelligence', 'quantum AI']
            }
            
            # Lista de termos para tentar
            termos_para_testar = [topico]  # Termo original primeiro
            if topico.lower() in traducoes:
                termos_para_testar.extend(traducoes[topico.lower()])
            
            resultados_coletados_topico = 0
            
            # Tentar cada termo até conseguir resultados suficientes
            for termo_atual in termos_para_testar:
                if resultados_coletados_topico >= min_resultados:
                    break
                    
                print(f"  🎯 Testando termo: '{termo_atual}'")
                
                # URL simples do Google Scholar
                query = termo_atual.replace(' ', '+')
                url = f"https://scholar.google.com.br/scholar?q={query}&as_ylo={ano_inicio}&as_yhi={ano_fim}"
                
                print(f"  📄 Acessando: {url}")
                
                try:
                    resultados_coletados_termo = 0
                    pagina_atual = 0
                    encontrou_resultados = False
                    
                    # Loop para coletar a quantidade desejada de resultados
                    while resultados_coletados_termo < (min_resultados - resultados_coletados_topico) and pagina_atual < 5:
                        # Calcular offset para paginação
                        start_param = pagina_atual * 10
                        url_pagina = f"{url}&start={start_param}"
                        
                        print(f"    📄 Acessando página {pagina_atual + 1}: {url_pagina}")
                        
                        # Abrir página com retry logic
                        max_tentativas = 3
                        page_loaded = False
                        for tentativa in range(max_tentativas):
                            try:
                                driver.get(url_pagina)
                                time.sleep(5 + tentativa)  # Aguardar mais tempo a cada tentativa
                                
                                # Verificar se a página carregou
                                if driver.title and "Google" in driver.title:
                                    page_loaded = True
                                    break
                                else:
                                    print(f"       ⚠️ Tentativa {tentativa + 1}: página não carregou corretamente")
                                    if tentativa < max_tentativas - 1:
                                        time.sleep(2)
                            except Exception as e_load:
                                print(f"       ❌ Erro ao carregar página (tentativa {tentativa + 1}): {e_load}")
                                if tentativa < max_tentativas - 1:
                                    time.sleep(3)
                        
                        if not page_loaded:
                            print("    ❌ Não foi possível carregar a página após várias tentativas")
                            break
                        
                        # Verificar se a página carregou corretamente
                        page_source = driver.page_source
                        if "unusual traffic" in page_source.lower() or "não conseguimos processar" in page_source.lower():
                            print("    ⚠️ Google Scholar detectou tráfego automatizado. Aguardando...")
                            time.sleep(10)
                            driver.refresh()
                            time.sleep(5)
                            page_source = driver.page_source
                        
                        # Tentar diferentes seletores CSS
                        resultados = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
                        if not resultados:
                            # Tentar seletor alternativo
                            resultados = driver.find_elements(By.CSS_SELECTOR, "div[data-lid]")
                        if not resultados:
                            # Tentar seletor mais genérico
                            resultados = driver.find_elements(By.CSS_SELECTOR, "div.gs_r")
                        
                        print(f"    📋 Encontrados {len(resultados)} resultados na página {pagina_atual + 1}")
                        
                        # Debug: mostrar parte do HTML se não há resultados
                        if len(resultados) == 0:
                            # Verificar mensagens específicas
                            page_lower = page_source.lower()
                            if "sua pesquisa" in page_lower and "não retornou" in page_lower:
                                print(f"    📭 Google Scholar: 'Sua pesquisa não retornou nenhum resultado' para '{termo_atual}'")
                                break  # Não há resultados para este termo, tentar próximo
                            elif "no results found" in page_lower:
                                print(f"    📭 Google Scholar: 'No results found' para '{termo_atual}'")
                                break
                            else:
                                print(f"    🔍 Debug - procurando por elementos na página...")
                                all_divs = driver.find_elements(By.TAG_NAME, "div")
                                print(f"       Total de divs encontradas: {len(all_divs)}")
                                if "scholar.google" not in driver.current_url:
                                    print(f"       ⚠️ URL inesperada: {driver.current_url}")
                        
                        # Se não há mais resultados, parar
                        if len(resultados) == 0:
                            print(f"    ❌ Não há mais resultados disponíveis para '{termo_atual}'")
                            break
                        
                        encontrou_resultados = True
                        
                        # Calcular quantos resultados processar nesta página
                        resultados_restantes = (min_resultados - resultados_coletados_topico) - resultados_coletados_termo
                        resultados_processar = min(len(resultados), resultados_restantes)
                        
                        # Extrair dados de cada resultado
                        for j, resultado in enumerate(resultados[:resultados_processar]):
                            try:
                                # Título (simples)
                                titulo = "Título não encontrado"
                                url_artigo = None
                                try:
                                    titulo_elem = resultado.find_element(By.CSS_SELECTOR, "h3 a")
                                    titulo = titulo_elem.text
                                    url_artigo = titulo_elem.get_attribute("href")
                                except:
                                    pass
                                
                                # Autores (simples)
                                autores = "N/A"
                                fonte = "N/A"
                                ano = None
                                try:
                                    autor_elem = resultado.find_element(By.CSS_SELECTOR, "div.gs_a")
                                    texto_autor = autor_elem.text
                                    
                                    # Extrair ano (regex simples)
                                    ano_match = re.search(r'(20\d{2})', texto_autor)
                                    if ano_match:
                                        ano = int(ano_match.group(1))
                                    
                                    # Dividir autores e fonte
                                    if ' - ' in texto_autor:
                                        partes = texto_autor.split(' - ')
                                        autores = partes[0].strip()
                                        if len(partes) > 1:
                                            fonte = partes[1].strip()
                                    else:
                                        autores = texto_autor.strip()
                                except:
                                    pass
                                
                                # Resumo (simples)
                                resumo = None
                                try:
                                    resumo_elem = resultado.find_element(By.CSS_SELECTOR, "div.gs_rs")
                                    resumo = resumo_elem.text
                                except:
                                    pass
                                
                                # Salvar no banco (usando o tópico original, não o termo traduzido)
                                cursor.execute(
                                    "INSERT INTO resultados_detalhados_CQ (termo, titulo, ano_publicacao, autores, fonte_publicacao, resumo, url_artigo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (topico, titulo, ano, autores, fonte, resumo, url_artigo)
                                )
                                
                                total_resultados += 1
                                resultados_coletados_termo += 1
                                resultados_coletados_topico += 1
                                print(f"       ✅ {resultados_coletados_topico}/{min_resultados}. {titulo[:50]}...")
                                
                            except Exception as e_item:
                                print(f"       ⚠️ Erro no item {j+1}: {e_item}")
                        
                        conn.commit()
                        
                        # Se já coletamos o suficiente, parar
                        if resultados_coletados_topico >= min_resultados:
                            break
                        
                        # Próxima página
                        pagina_atual += 1
                        
                        # Limite de segurança para evitar loop infinito
                        if pagina_atual >= 5:  # Máximo 5 páginas por termo
                            print(f"    ⚠️ Limite de páginas atingido (5 páginas) para '{termo_atual}'")
                            break
                        
                        # Pausa entre páginas
                        time.sleep(2)
                    
                    if encontrou_resultados:
                        print(f"  ✅ Coletados {resultados_coletados_termo} resultados para '{termo_atual}'")
                    else:
                        print(f"  📭 Nenhum resultado encontrado para '{termo_atual}'")
                    
                except Exception as e_termo:
                    print(f"  ❌ Erro no termo '{termo_atual}': {e_termo}")
                
                # Pausa entre termos
                time.sleep(2)
            
            print(f"✅ Total coletado para '{topico}': {resultados_coletados_topico} resultados")
            
            # Pausa entre tópicos
            time.sleep(3)
        
        # Finalizar
        progresso_busca['total_resultados'] = total_resultados
        progresso_busca['progresso'] = 100
        progresso_busca['status'] = 'concluido'
        
        print(f"🎉 Concluído! Total: {total_resultados} resultados")
        
        # Fechar tudo
        driver.quit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        progresso_busca['status'] = f'erro: {str(e)}'
        if 'driver' in locals():
            driver.quit()
        if 'conn' in locals():
            conn.close()

# Teste direto
if __name__ == "__main__":
    print("🧪 TESTE SELENIUM SIMPLES")
    print("=" * 30)
    
    # Teste com um tópico
    topicos = ["computação quântica"]
    executar_web_scraping_selenium_simples(topicos, 2024, 2025, 3)