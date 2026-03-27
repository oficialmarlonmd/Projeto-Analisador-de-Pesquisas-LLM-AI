import time
import requests

print("🕐 Aguardando servidor inicializar...")
time.sleep(5)

print("🧭 TESTE SIMPLES DE NAVEGAÇÃO")
print("=" * 40)

try:
    # Teste básico da página principal
    response = requests.get("http://127.0.0.1:5000", timeout=10)
    if response.status_code == 200:
        print("✅ Página Principal: OK")
        
        # Teste do Chat Científico
        try:
            chat_response = requests.get("http://127.0.0.1:5000/chat_cientifico_page", timeout=10)
            if chat_response.status_code == 200:
                print("✅ Chat Científico: OK")
                print("🎉 NAVEGAÇÃO FUNCIONANDO!")
                print("\n📋 ABAS DISPONÍVEIS:")
                print("   • Home: http://127.0.0.1:5000/")
                print("   • Nova Busca: http://127.0.0.1:5000/iniciar_busca")
                print("   • Resultados: http://127.0.0.1:5000/resultados")
                print("   • Storytelling: http://127.0.0.1:5000/storytelling")
                print("   • Chat Científico: http://127.0.0.1:5000/chat_cientifico_page")
            else:
                print(f"❌ Chat Científico: Erro {chat_response.status_code}")
        except Exception as e:
            print(f"❌ Chat Científico: {e}")
            
    else:
        print(f"❌ Servidor respondeu com erro {response.status_code}")
        
except Exception as e:
    print(f"❌ Falha de conexão: {e}")
    print("💡 Verifique se o servidor está rodando: python app.py")