"""
🔍 Teste de Navegação - Sistema QAARS
=====================================

Verifica se todas as abas de navegação estão funcionando corretamente
"""

import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def testar_rota(rota, nome):
    """Testa se uma rota está acessível"""
    try:
        response = requests.get(f"{BASE_URL}{rota}", timeout=5)
        if response.status_code == 200:
            print(f"✅ {nome}: OK ({rota})")
            return True
        else:
            print(f"❌ {nome}: Erro {response.status_code} ({rota})")
            return False
    except Exception as e:
        print(f"❌ {nome}: Falha de conexão - {str(e)} ({rota})")
        return False

def testar_todas_abas():
    """Testa todas as abas de navegação"""
    print("🧭 TESTE DE NAVEGAÇÃO - SISTEMA QAARS")
    print("=" * 50)
    
    rotas = [
        ('/', 'Home/Página Principal'),
        ('/iniciar_busca', 'Nova Busca'),
        ('/resultados', 'Resultados/Análises'),
        ('/storytelling', 'Storytelling'),
        ('/exibir_storytelling', 'Storytelling (rota alternativa)'),
        ('/chat_cientifico_page', 'Chat Científico'),
        ('/dados_contexto', 'API - Contexto dos Dados'),
    ]
    
    sucessos = 0
    total = len(rotas)
    
    for rota, nome in rotas:
        if testar_rota(rota, nome):
            sucessos += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO: {sucessos}/{total} rotas funcionando")
    
    if sucessos == total:
        print("🎉 TODAS AS ABAS ESTÃO FUNCIONANDO!")
        print("✅ Sistema de navegação totalmente operacional")
    else:
        print(f"⚠️ {total - sucessos} problemas encontrados")
        print("💡 Verifique se o servidor Flask está rodando")
    
    return sucessos == total

if __name__ == "__main__":
    # Verificar se o servidor está rodando
    try:
        response = requests.get(BASE_URL, timeout=3)
        print(f"🚀 Servidor detectado em {BASE_URL}")
        testar_todas_abas()
    except:
        print(f"❌ Servidor não encontrado em {BASE_URL}")
        print("💡 Execute: python app.py")
        sys.exit(1)