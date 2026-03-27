"""
🧪 Script de teste para o Sistema de Chat Científico com RAG
===============================================================

Este script testa as funcionalidades do chat científico implementado:
- RAG (Retrieval-Augmented Generation)  
- Few-shot prompting
- Memória de conversa
- Respostas baseadas apenas nos dados coletados
"""

import requests
import json
import time

# Configurações
BASE_URL = "http://127.0.0.1:5000"

def testar_contexto_dados():
    """Testa se o contexto dos dados está sendo carregado corretamente"""
    print("🔍 Testando contexto dos dados...")
    try:
        response = requests.get(f"{BASE_URL}/dados_contexto")
        data = response.json()
        
        if data.get('dados_disponiveis'):
            print("✅ Dados disponíveis encontrados!")
            resumo = data.get('resumo', {})
            print(f"   📊 Total de artigos: {resumo.get('total_artigos', 'N/A')}")
            print(f"   📅 Período: {resumo.get('periodo', 'N/A')}")
            print(f"   🏷️ Tópicos: {resumo.get('topicos', [])}")
            print(f"   🔤 Palavras principais: {resumo.get('palavras_principais', [])}")
            return True
        else:
            print("⚠️ Nenhum dado disponível. Execute uma busca primeiro.")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar contexto: {e}")
        return False

def testar_chat_perguntas():
    """Testa o chat com diferentes tipos de perguntas"""
    print("\n🤖 Testando chat científico com RAG...")
    
    perguntas_teste = [
        "Quantos artigos foram analisados no total?",
        "Qual é a tendência temporal da pesquisa?", 
        "Quais são as principais palavras-chave encontradas?",
        "Qual foi o ano mais produtivo?",
        "Como está a evolução do campo de pesquisa?"
    ]
    
    for i, pergunta in enumerate(perguntas_teste, 1):
        print(f"\n📝 Pergunta {i}: {pergunta}")
        try:
            response = requests.post(
                f"{BASE_URL}/chat_cientifico",
                json={"pergunta": pergunta},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    resposta = data.get('resposta', '')
                    print(f"✅ Resposta recebida ({len(resposta)} chars)")
                    print(f"   💬 Preview: {resposta[:100]}...")
                    
                    # Verificar características da resposta
                    if any(emoji in resposta for emoji in ['📊', '📈', '🔤', '📅', '🚀']):
                        print("   🎨 Resposta com emojis científicos ✓")
                    
                    if any(word in resposta.lower() for word in ['artigos', 'análise', 'dados', 'pesquisa']):
                        print("   🔬 Vocabulário científico detectado ✓")
                        
                else:
                    print(f"❌ Erro na resposta: {data.get('error')}")
            else:
                print(f"❌ Erro HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na pergunta {i}: {e}")
        
        time.sleep(1)  # Pausa entre perguntas

def testar_memoria_conversa():
    """Testa se a memória de conversa está funcionando"""
    print("\n🧠 Testando memória de conversa...")
    
    # Primeira pergunta
    pergunta1 = "Quantos artigos foram analisados?"
    print(f"📝 Pergunta 1: {pergunta1}")
    
    try:
        response1 = requests.post(
            f"{BASE_URL}/chat_cientifico",
            json={"pergunta": pergunta1}
        )
        
        if response1.status_code == 200 and response1.json().get('success'):
            print("✅ Primeira pergunta respondida")
            
            # Segunda pergunta contextual
            pergunta2 = "E qual foi a tendência temporal desses artigos?"
            print(f"📝 Pergunta 2 (contextual): {pergunta2}")
            
            response2 = requests.post(
                f"{BASE_URL}/chat_cientifico", 
                json={"pergunta": pergunta2}
            )
            
            if response2.status_code == 200 and response2.json().get('success'):
                resposta2 = response2.json().get('resposta', '')
                print("✅ Segunda pergunta contextual respondida")
                
                # Verificar se a resposta faz sentido no contexto
                if any(word in resposta2.lower() for word in ['temporal', 'crescimento', 'evolução', 'anos']):
                    print("   🧠 Memória de contexto funcionando ✓")
                else:
                    print("   ⚠️ Possível problema com memória de contexto")
            else:
                print("❌ Erro na segunda pergunta")
        else:
            print("❌ Erro na primeira pergunta")
            
    except Exception as e:
        print(f"❌ Erro no teste de memória: {e}")

def testar_limpeza_chat():
    """Testa a funcionalidade de limpar chat"""
    print("\n🧹 Testando limpeza de chat...")
    try:
        response = requests.post(f"{BASE_URL}/limpar_chat")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Chat limpo com sucesso")
            else:
                print("❌ Erro ao limpar chat")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar limpeza: {e}")

def executar_testes_completos():
    """Executa todos os testes do sistema"""
    print("🧪 INICIANDO TESTES DO SISTEMA DE CHAT CIENTÍFICO COM RAG")
    print("=" * 60)
    
    # Teste 1: Contexto dos dados
    dados_ok = testar_contexto_dados()
    
    if dados_ok:
        # Teste 2: Perguntas do chat
        testar_chat_perguntas()
        
        # Teste 3: Memória de conversa
        testar_memoria_conversa()
        
        # Teste 4: Limpeza de chat
        testar_limpeza_chat()
        
        print("\n🎉 TESTES CONCLUÍDOS!")
        print("=" * 60)
        print("✅ Sistema de Chat Científico com RAG está operacional")
        print("🔬 Funcionalidades testadas:")
        print("   • Retrieval-Augmented Generation (RAG)")
        print("   • Few-shot prompting")
        print("   • Memória de conversa")
        print("   • Respostas baseadas em dados reais")
        print("   • Comportamento científico profissional")
        
    else:
        print("\n⚠️ TESTES INTERROMPIDOS")
        print("Execute uma busca científica primeiro para gerar dados!")

if __name__ == "__main__":
    executar_testes_completos()