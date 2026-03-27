import os
import re
import sqlite3
import time
import threading
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use backend não-interativo
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import base64
import io
import json
from flask import Flask, render_template, request, jsonify, url_for
try:
    from selenium_simples import executar_web_scraping_selenium_simples, progresso_busca as progresso_selenium
except ImportError:
    progresso_selenium = None
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
from nltk.corpus import stopwords
try:
    from storytelling import gerar_dados_storytelling
except ImportError:
    gerar_dados_storytelling = None

# === INTEGRAÇÃO LLM GROQ (QAARS) ===
try:
    from dotenv import load_dotenv
    from groq import Groq
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage
    
    # Carregar credenciais Groq
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Parâmetros otimizados para narrativa (Groq)
    MODEL_NAME = "llama-3.1-8b-instant"  # Modelo Production disponível
    TEMPERATURE = 0.2
    
    # Inicializar Groq Client e LLM
    if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
        try:
            groq_client = Groq(api_key=GROQ_API_KEY)
            
            groq_storyteller = ChatGroq(
                temperature=TEMPERATURE,
                groq_api_key=GROQ_API_KEY,
                model_name=MODEL_NAME,
                max_tokens=1000
            )
            
            # Manter compatibilidade com código existente
            watsonx_storyteller = groq_storyteller
            
            print(f"🚀 LLM Storyteller (Groq/{MODEL_NAME}) inicializado com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao conectar com Groq: {e}")
            groq_storyteller = "DEMO_MODE"
            watsonx_storyteller = "DEMO_MODE"
            print("🤖 Sistema QAARS inicializado em modo DEMO (erro de conexão Groq).")
    else:
        # Modo DEMO para demonstração sem chave válida
        groq_storyteller = "DEMO_MODE"
        watsonx_storyteller = "DEMO_MODE"
        print("🤖 Sistema QAARS inicializado em modo DEMO (chave Groq não configurada).")

except ImportError as e:
    groq_storyteller = None
    watsonx_storyteller = None
    print(f"⚠️ Dependências Groq não encontradas: {e}")
except Exception as e:
    groq_storyteller = None
    watsonx_storyteller = None
    print(f"❌ Erro ao inicializar Groq: {e}")
# ================================

# Inicializa Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

# Variáveis globais para controle de progresso
progresso_busca = {'status': 'idle', 'progresso': 0, 'total_resultados': 0, 'topico_atual': ''}

def verificar_nltk():
    """Verifica e baixa recursos NLTK necessários"""
    for recurso in ['stopwords', 'punkt']:
        try:
            nltk.data.find(f'corpora/{recurso}')
        except LookupError:
            nltk.download(recurso)

def executar_web_scraping(topicos_selecionados, ano_inicio, ano_fim, min_resultados):
    """Chama a versão simples do Selenium"""
    global progresso_busca
    
    try:
        # Limpar banco antes de iniciar nova busca (backup de segurança)
        print("🧹 Limpeza de segurança no app.py...")
        import sqlite3
        conn = sqlite3.connect("buscas_completas_CQ.db")
        cursor = conn.cursor()
        
        # Verificar dados existentes
        count_before = cursor.execute("SELECT COUNT(*) FROM resultados_detalhados_CQ").fetchone()[0]
        if count_before > 0:
            print(f"   ⚠️ Encontrados {count_before} registros antigos - removendo...")
            cursor.execute("DELETE FROM resultados_detalhados_CQ")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='resultados_detalhados_CQ'")
            conn.commit()
            print("   ✅ Limpeza de segurança concluída")
        else:
            print("   ✅ Banco já está limpo")
        
        conn.close()
        
        # Importar e sincronizar progresso
        import selenium_simples
        
        # Garantir que o progresso está sincronizado
        selenium_simples.progresso_busca = progresso_busca
        
        print(f"🎯 Iniciando busca para {len(topicos_selecionados)} tópicos")
        print(f"📊 Parâmetros: {ano_inicio}-{ano_fim}, min_resultados={min_resultados}")
        
        # Executar scraping
        selenium_simples.executar_web_scraping_selenium_simples(topicos_selecionados, ano_inicio, ano_fim, min_resultados)
        
        # Sincronizar progresso de volta
        progresso_busca.update(selenium_simples.progresso_busca)
        
        print("✅ Web scraping concluído com sucesso")
        
    except Exception as e:
        print(f"❌ Erro no web scraping: {e}")
        progresso_busca['status'] = f'erro: {str(e)}'
        progresso_busca['progresso'] = 0

def extrair_dados_rag():
    """Extrai dados estruturados do banco para RAG (Retrieval-Augmented Generation)"""
    try:
        conn = sqlite3.connect("buscas_completas_CQ.db")
        df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
        conn.close()
        
        if df.empty:
            return None
            
        # Estruturar dados para RAG
        dados_rag = {
            'metadados': {
                'total_artigos': len(df),
                'periodo': f"{df['ano_publicacao'].min():.0f}-{df['ano_publicacao'].max():.0f}",
                'topicos': df['termo'].unique().tolist(),
                'anos_analisados': len(df['ano_publicacao'].unique())
            },
            'analise_temporal': {},
            'palavras_chave': {},
            'artigos_detalhados': [],
            'estatisticas': {}
        }
        
        # Análise temporal
        df_anos = df.dropna(subset=['ano_publicacao'])
        df_anos['ano_publicacao'] = pd.to_numeric(df_anos['ano_publicacao'], errors='coerce')
        anos_count = df_anos['ano_publicacao'].value_counts().sort_index()
        
        dados_rag['analise_temporal'] = {
            'distribuicao': anos_count.to_dict(),
            'crescimento_percentual': ((anos_count.iloc[-1] - anos_count.iloc[0]) / anos_count.iloc[0] * 100) if len(anos_count) > 1 else 0,
            'tendencia': 'crescimento' if anos_count.iloc[-1] > anos_count.iloc[0] else 'declinio'
        }
        
        # Análise de palavras-chave
        texto_completo = (df['titulo'].fillna('') + ' ' + df['resumo'].fillna('')).str.lower()
        palavras = []
        for texto in texto_completo:
            palavras.extend(re.findall(r'\b[a-záàâãäéèêëíìîïóòôõöúùûüçñ]{4,}\b', texto))
        
        stopwords_custom = {
            'computacao', 'quantica', 'quântico', 'quantum', 'para', 'com', 'que', 
            'uma', 'como', 'sobre', 'dados', 'resultados', 'trabalho', 'estudo', 
            'pesquisa', 'neste', 'este', 'artigo', 'paper', 'análise'
        }
        
        palavras_filtradas = [p for p in palavras if p not in stopwords_custom]
        contador = Counter(palavras_filtradas)
        
        dados_rag['palavras_chave'] = {
            'top_10': dict(contador.most_common(10)),
            'total_palavras': len(palavras_filtradas),
            'vocabulario_unico': len(contador)
        }
        
        # Artigos detalhados (amostra)
        for _, artigo in df.head(10).iterrows():
            dados_rag['artigos_detalhados'].append({
                'titulo': artigo['titulo'],
                'ano': artigo['ano_publicacao'],
                'autores': artigo['autores'],
                'resumo_snippet': artigo['resumo'][:200] + '...' if pd.notna(artigo['resumo']) else 'N/A'
            })
        
        # Estatísticas gerais
        dados_rag['estatisticas'] = {
            'artigos_com_resumo': df['resumo'].notna().sum(),
            'artigos_com_autores': df['autores'].notna().sum(),
            'ano_mais_produtivo': int(anos_count.idxmax()) if not anos_count.empty else None,
            'producao_ano_mais_produtivo': int(anos_count.max()) if not anos_count.empty else 0
        }
        
        return dados_rag
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados RAG: {e}")
        return None

def gerar_resposta_cientifica_rag(pergunta, dados_rag, historico_conversa=None):
    """Gera resposta científica usando RAG com few-shot prompting e memória"""
    
    if not isinstance(groq_storyteller, ChatGroq) or not dados_rag:
        return "❌ Sistema de análise não disponível. Verifique se há dados coletados."
    
    try:
        # Construir contexto RAG baseado nos dados reais
        contexto_rag = f"""DADOS DA PESQUISA ATUAL (FONTE EXCLUSIVA):
📊 METADADOS:
- Total de artigos analisados: {dados_rag['metadados']['total_artigos']}
- Período coberto: {dados_rag['metadados']['periodo']}
- Tópicos: {', '.join(dados_rag['metadados']['topicos'])}
- Anos analisados: {dados_rag['metadados']['anos_analisados']}

📈 ANÁLISE TEMPORAL:
- Distribuição por ano: {dados_rag['analise_temporal']['distribuicao']}
- Crescimento: {dados_rag['analise_temporal']['crescimento_percentual']:.1f}%
- Tendência: {dados_rag['analise_temporal']['tendencia']}

🔤 PALAVRAS-CHAVE PRINCIPAIS:
{dict(list(dados_rag['palavras_chave']['top_10'].items())[:5])}

📚 ESTATÍSTICAS:
- Ano mais produtivo: {dados_rag['estatisticas']['ano_mais_produtivo']} ({dados_rag['estatisticas']['producao_ano_mais_produtivo']} artigos)
- Artigos com resumo: {dados_rag['estatisticas']['artigos_com_resumo']}
- Vocabulário único: {dados_rag['palavras_chave']['vocabulario_unico']} termos"""
        
        # Few-shot prompting para comportamento científico
        few_shot_examples = """EXEMPLOS DE RESPOSTAS CIENTÍFICAS ADEQUADAS:

Pergunta: "Quantos artigos foram analisados?"
Resposta: "📊 Foram analisados {total_artigos} artigos científicos no total, cobrindo o período de {periodo}. Esta amostra representa uma base sólida para análise quantitativa da evolução do campo."

Pergunta: "Qual é a tendência temporal da pesquisa?"
Resposta: "📈 A análise temporal revela uma tendência de {tendencia} com crescimento de {crescimento}% entre o primeiro e último ano do período. O ano de {ano_produtivo} foi o mais produtivo, com {producao_max} publicações, indicando um pico de interesse acadêmico."

Pergunta: "Quais são as principais palavras-chave?"
Resposta: "🔤 As cinco palavras-chave mais frequentes são: [lista baseada em dados reais]. Estes termos refletem o foco central da pesquisa e indicam os conceitos mais relevantes na literatura analisada."""
        
        # Construir histórico de conversa
        contexto_historico = ""
        if historico_conversa and len(historico_conversa) > 0:
            contexto_historico = "\nHISTÓRICO DA CONVERSA:\n"
            for i, msg in enumerate(historico_conversa[-6:]):  # Últimas 6 mensagens
                contexto_historico += f"{msg['role'].upper()}: {msg['content']}\n"
        
        # Prompt principal com instruções rígidas
        prompt_sistema = f"""Você é um ASSISTENTE CIENTÍFICO ESPECIALIZADO do Sistema QAARS (Quantum Academic Analysis & Research Storytelling).

🎯 MISSÃO: Responder perguntas sobre a análise científica atual usando EXCLUSIVAMENTE os dados fornecidos.

⚠️ REGRAS RIGOROSAS:
1. Use APENAS os dados da pesquisa atual fornecidos abaixo
2. NUNCA invente ou alucine informações
3. Se não houver dados específicos, diga "Os dados atuais não contêm essa informação"
4. Mantenha tom científico, objetivo e profissional
5. Cite números exatos dos dados fornecidos
6. Use emojis científicos (📊📈🔬📚) moderadamente
7. Estruture respostas em parágrafos claros
8. Considere o histórico da conversa para contexto

{few_shot_examples}

{contexto_rag}
{contexto_historico}

PERGUNTA DO USUÁRIO: {pergunta}

RESPONDA de forma científica, precisa e baseada EXCLUSIVAMENTE nos dados acima:"""
        
        # Fazer a consulta ao LLM
        response = groq_storyteller.invoke([HumanMessage(content=prompt_sistema)])
        
        return response.content.strip()
        
    except Exception as e:
        print(f"❌ Erro na geração RAG: {e}")
        return "❌ Erro ao processar sua pergunta. Tente novamente."

# Variável global para armazenar histórico de conversa
chat_history = []

def gerar_storytelling_llm(dados_agregados):
    """
    🤖 Sistema QAARS: Cria storytelling inteligente com Groq LLM
    Aplica as 6 Lições Fundamentais de Storytelling com Dados
    """
    if not isinstance(groq_storyteller, ChatGroq):
        return "**⚠️ Sistema QAARS Indisponível:** O motor de análise LLM não foi inicializado. Verifique a configuração do Groq."
    
    if not dados_agregados or not dados_agregados.get('top_palavras'):
        return "**⚠️ Dados Insuficientes:** Nenhum dado válido para análise. Execute uma busca primeiro."
    
    try:
        # 1. Extrair insights estruturados (Lição 1: Contexto)
        total_artigos = sum(dados_agregados.get('temporal', {}).get('data', []))
        periodo_anos = dados_agregados.get('temporal', {}).get('labels', [])
        
        # Top 3 palavras mais relevantes
        palavras_freq = dados_agregados.get('top_palavras', {})
        top_palavras = sorted(palavras_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Sentimento dominante
        sentimentos = dados_agregados.get('sentimentos', {})
        sent_positivo = sentimentos.get('positivo', 0)
        sent_negativo = sentimentos.get('negativo', 0)
        sent_neutro = sentimentos.get('neutro', 0)
        
        # Determinar tom dominante
        if sent_positivo > sent_negativo and sent_positivo > sent_neutro:
            tom_dominante = "otimista"
            perspectiva_desc = "focada em avanços e oportunidades"
        elif sent_negativo > sent_positivo and sent_negativo > sent_neutro:
            tom_dominante = "crítico"
            perspectiva_desc = "destacando desafios e limitações"
        else:
            tom_dominante = "equilibrado"
            perspectiva_desc = "balanceando oportunidades e desafios"
        
        # Tendência temporal
        dados_temporais = dados_agregados.get('temporal', {}).get('data', [])
        if len(dados_temporais) >= 2:
            crescimento = dados_temporais[-1] > dados_temporais[0]
            variacao_pct = ((dados_temporais[-1] - dados_temporais[0]) / dados_temporais[0]) * 100 if dados_temporais[0] > 0 else 0
        else:
            crescimento = None
            variacao_pct = 0
        
        # 2. Geração da Narrativa - Sistema QAARS com Groq LLM
        if isinstance(groq_storyteller, ChatGroq):
            # Versão LLM Real com Groq
            resumo_insights = {
                'escopo': {
                    'total_artigos': total_artigos,
                    'periodo': f"{periodo_anos[0]} - {periodo_anos[-1]}" if len(periodo_anos) > 1 else "período único"
                },
                'foco_pesquisa': {
                    'top_3_palavras': [palavra for palavra, freq in top_palavras],
                    'frequencias': [freq for palavra, freq in top_palavras]
                },
                'perspectiva': {
                    'tom_dominante': tom_dominante,
                    'distribuicao': f"Positivo: {sent_positivo}%, Negativo: {sent_negativo}%, Neutro: {sent_neutro}%"
                },
                'evolucao': {
                    'tendencia': "crescimento" if crescimento else "estabilidade" if crescimento is not None else "indeterminada",
                    'variacao_percentual': f"{variacao_pct:.1f}%" if crescimento is not None else "N/A"
                }
            }
            
            # Prompt estruturado para Groq
            prompt = f"""Você é um Analista Sênior de Pesquisa Acadêmica especialista em Storytelling Científico.

MISSÃO: Analisar os dados abaixo e criar uma narrativa persuasiva em Português-BR seguindo as 6 Lições de Storytelling com Dados.

ESTRUTURA OBRIGATÓRIA:

🎯 **CONTEXTO & DESCOBERTA**
- Apresente o escopo da análise e a descoberta mais impactante

📊 **EVIDÊNCIAS & ANÁLISE**  
- Foco de Pesquisa: Top 3 palavras-chave mais relevantes
- Perspectiva: Tom dominante da pesquisa (otimista/crítico/equilibrado)
- Evolução: Tendência temporal dos estudos

⚡ **SÍNTESE & AÇÃO**
- MENSAGEM PRINCIPAL (uma frase em negrito)
- PRÓXIMO PASSO (recomendação específica)

DADOS: {json.dumps(resumo_insights, ensure_ascii=False)}

REGRAS: Máximo 400 palavras, tom acadêmico, use Markdown, foque em insights."""

            try:
                # Chamar Groq LLM
                messages = [HumanMessage(content=prompt)]
                response = groq_storyteller.invoke(messages)
                narrativa = response.content
                
                print("🚀 Storytelling Groq LLM gerado com sucesso")
                return narrativa
                
            except Exception as e:
                print(f"⚠️ Erro Groq LLM: {e}")
                # Fallback para modo DEMO
                pass
        
        # Versão DEMO estruturada (fallback)
        
    except Exception as e:
        print(f"❌ Erro na geração de storytelling: {e}")
        return f"**Falha na Geração de Storytelling:** Erro no processamento dos dados. {str(e)}"

def gerar_graficos():
    """Gera todos os gráficos e retorna os caminhos"""
    try:
        # Garantir que o diretório de plots existe
        plots_dir = os.path.join('static', 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        
        # Verificar NLTK
        verificar_nltk()
        
        # Carregar dados
        conn = sqlite3.connect("buscas_completas_CQ.db")
        df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
        conn.close()
        
        if df.empty:
            return None
        
        graficos = {}
        
        # Configurar matplotlib com fonte compatível
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['font.size'] = 10
        
        # Preparar dados com processamento avançado
        df['texto_completo'] = df['titulo'].fillna('') + ' ' + df['resumo'].fillna('')
        
        # Limpeza mais rigorosa
        df['texto_limpo'] = df['texto_completo'].str.lower()
        df['texto_limpo'] = df['texto_limpo'].str.replace(r'[^\w\s]', ' ', regex=True)  # Remove pontuação
        df['texto_limpo'] = df['texto_limpo'].str.replace(r'\d+', '', regex=True)       # Remove números
        df['texto_limpo'] = df['texto_limpo'].str.replace(r'\s+', ' ', regex=True)      # Normaliza espaços
        df['texto_limpo'] = df['texto_limpo'].str.strip()
        
        # Stopwords expandidas com termos científicos genéricos
        stopwords_custom = set(stopwords.words('portuguese')).union(set(stopwords.words('english'))).union({
            # Termos genéricos de pesquisa
            'computacao', 'quantica', 'quântico', 'quantum', 'trabalho', 'estudo', 'pesquisa', 'paper',
            'article', 'estudo', 'revisao', 'analise', 'survey', 'research', 'study', 'analysis',
            'utilizacao', 'aplicacao', 'desenvolvimento', 'proposta', 'abordagem', 'metodologia',
            'implementacao', 'avaliacao', 'comparacao', 'experimental', 'theoretical',
            # Conectores e artigos
            'neste', 'este', 'esta', 'esse', 'essa', 'para', 'com', 'que', 'uma', 'como', 'sobre',
            'dados', 'resultados', 'caso', 'assim', 'ainda', 'pode', 'ser', 'mais', 'muito',
            'bem', 'entre', 'durante', 'através', 'mediante', 'também', 'já', 'apenas',
            # Termos de estrutura de artigos
            'introduction', 'conclusion', 'abstract', 'keywords', 'references', 'resumo', 'introducao',
            'conclusao', 'referencias', 'palavras', 'chave', 'método', 'método', 'metodo'
        })
        
        # Filtrar palavras com critérios mais rigorosos
        def filtrar_palavras_significativas(texto):
            palavras = texto.split()
            palavras_filtradas = []
            
            for palavra in palavras:
                # Manter apenas palavras de 4+ caracteres, não são stopwords e têm conteúdo significativo
                if (len(palavra) >= 4 and 
                    palavra not in stopwords_custom and 
                    not palavra.isdigit() and
                    palavra.isalpha() and  # Apenas letras
                    len(set(palavra)) > 2):  # Pelo menos 3 caracteres diferentes (evita 'aaaa')
                    palavras_filtradas.append(palavra)
            
            return ' '.join(palavras_filtradas)
        
        df['texto_filtrado'] = df['texto_limpo'].apply(filtrar_palavras_significativas)
        
        # 1. WordCloud
        try:
            plt.figure(figsize=(12, 6))
            texto = ' '.join(df['texto_filtrado'].dropna())
            if texto and len(texto.strip()) > 0:
                wordcloud = WordCloud(
                    width=800, 
                    height=400, 
                    background_color='white',
                    colormap='viridis',
                    max_words=100,
                    relative_scaling=0.5
                ).generate(texto)
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.title('Nuvem de Palavras-Chave', fontsize=16, fontweight='bold')
                plt.tight_layout()
                plt.savefig('static/plots/wordcloud.png', dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                graficos['wordcloud'] = 'plots/wordcloud.png'
                print("WordCloud gerado com sucesso!")
        except Exception as e:
            print(f"Erro ao gerar WordCloud: {e}")
            plt.close()
        
        # 2. Análise de Sentimento
        try:
            positivas = {'inovação', 'oportunidades', 'avanços', 'eficiente', 'sucesso', 'melhor', 'novo', 'promissor'}
            negativas = {'desafios', 'problemas', 'riscos', 'limitações', 'ameaça', 'dificuldade', 'complexo'}
            
            def sentimento(texto):
                if not isinstance(texto, str):
                    return 'Neutro'
                texto = texto.lower()
                p = sum(1 for w in positivas if w in texto)
                n = sum(1 for w in negativas if w in texto)
                return 'Positivo' if p > n else 'Negativo' if n > p else 'Neutro'
            
            df['sentimento'] = df['resumo'].apply(sentimento)
            
            plt.figure(figsize=(10, 6))
            sentimento_counts = df['sentimento'].value_counts()
            colors = ['#28a745', "#4d74df", '#6c757d']
            
            plt.pie(sentimento_counts.values, labels=sentimento_counts.index, 
                   autopct='%1.1f%%', colors=colors, startangle=90)
            plt.title('Análise de Sentimento dos Resumos', fontsize=16, fontweight='bold')
            plt.axis('equal')
            plt.tight_layout()
            plt.savefig('static/plots/sentimentos.png', dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            graficos['sentimentos'] = 'plots/sentimentos.png'
            print("Análise de sentimento gerada com sucesso!")
        except Exception as e:
            print(f"Erro ao gerar análise de sentimento: {e}")
            plt.close()
        
        # 3. Análise Temporal
        try:
            df['ano_publicacao'] = pd.to_numeric(df['ano_publicacao'], errors='coerce')
            df_anos = df.dropna(subset=['ano_publicacao'])
            df_anos = df_anos[(df_anos['ano_publicacao'] >= 1900) & (df_anos['ano_publicacao'] <= 2025)]
            df_anos['ano_publicacao'] = df_anos['ano_publicacao'].astype(int)
            
            if not df_anos.empty:
                plt.figure(figsize=(12, 6))
                anos_contagem = df_anos['ano_publicacao'].value_counts().sort_index()
                
                plt.bar(anos_contagem.index, anos_contagem.values, 
                       color='skyblue', edgecolor='navy', alpha=0.7)
                plt.title('Publicações por Ano', fontsize=16, fontweight='bold')
                plt.xlabel('Ano', fontsize=12)
                plt.ylabel('Número de Artigos', fontsize=12)
                plt.xticks(rotation=45)
                plt.grid(axis='y', alpha=0.3)
                
                # Adicionar valores nas barras
                for i, v in enumerate(anos_contagem.values):
                    plt.text(anos_contagem.index[i], v + 0.1, str(v), 
                           ha='center', va='bottom', fontweight='bold')
                
                plt.tight_layout()
                plt.savefig('static/plots/temporal.png', dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                graficos['temporal'] = 'plots/temporal.png'
                print("Gráfico temporal gerado com sucesso!")
        except Exception as e:
            print(f"Erro ao gerar gráfico temporal: {e}")
            plt.close()
        
        # 4. Tendências por Tópico
        try:
            if 'termo' in df.columns and not df_anos.empty:
                plt.figure(figsize=(14, 8))
                tendencias = df_anos.groupby(['ano_publicacao', 'termo']).size().unstack(fill_value=0)
                
                # Limitar a 10 tópicos mais frequentes para melhor visualização
                top_topicos = df['termo'].value_counts().head(10).index
                tendencias_top = tendencias[top_topicos]
                
                tendencias_top.plot(kind='line', marker='o', figsize=(14, 8), linewidth=2, markersize=6)
                plt.title('Tendência de Tópicos por Ano', fontsize=16, fontweight='bold')
                plt.xlabel('Ano', fontsize=12)
                plt.ylabel('Quantidade de Artigos', fontsize=12)
                plt.legend(title='Tópico', bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig('static/plots/tendencias.png', dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()
                graficos['tendencias'] = 'plots/tendencias.png'
                print("Gráfico de tendências gerado com sucesso!")
        except Exception as e:
            print(f"Erro ao gerar gráfico de tendências: {e}")
            plt.close()
        
        # 5. Top Palavras
        try:
            if texto and len(texto.strip()) > 0:
                palavras_freq = Counter(texto.split()).most_common(20)
                if palavras_freq:
                    palavras, frequencias = zip(*palavras_freq)
                    
                    plt.figure(figsize=(12, 8))
                    colors = plt.cm.viridis(range(len(palavras)))
                    bars = plt.barh(range(len(palavras)), frequencias, color=colors)
                    plt.yticks(range(len(palavras)), palavras)
                    plt.title('Top 20 Palavras Mais Frequentes', fontsize=16, fontweight='bold')
                    plt.xlabel('Frequência', fontsize=12)
                    plt.gca().invert_yaxis()
                    plt.grid(axis='x', alpha=0.3)
                    
                    # Adicionar valores nas barras
                    for i, (bar, freq) in enumerate(zip(bars, frequencias)):
                        plt.text(freq + max(frequencias) * 0.01, i, str(freq), 
                               va='center', ha='left', fontweight='bold')
                    
                    plt.tight_layout()
                    plt.savefig('static/plots/top_palavras.png', dpi=300, bbox_inches='tight', facecolor='white')
                    plt.close()
                    graficos['top_palavras'] = 'plots/top_palavras.png'
                    print("Gráfico de top palavras gerado com sucesso!")
        except Exception as e:
            print(f"Erro ao gerar gráfico de top palavras: {e}")
            plt.close()
        
        return graficos
        
    except Exception as e:
        print(f"Erro ao gerar gráficos: {e}")
        return None

@app.route('/')
def index():
    """Página home do sistema QAARS"""
    return render_template('home.html')

@app.route('/iniciar_busca')
def iniciar_busca():
    """Página de busca"""
    topicos_predefinidos = [
        "Computação Quântica na Criptografia",
        "Otimização Quântica em Finanças",
        "Inteligência Artificial e Aprendizado de Máquina Quântico",
        "Computação Quântica e Descoberta de Medicamentos",
        "Química Quântica Computacional",
        "Perspectivas Futuras da Computação Quântica",
        "Computação Quântica Pós-Quântica",
        "Desafios e Oportunidades na Era Quântica"
    ]
    return render_template('busca.html', topicos=topicos_predefinidos)

@app.route('/executar_busca', methods=['POST'])
def executar_busca():
    """Inicia o processo de web scraping"""
    try:
        print("📩 Recebendo requisição de busca...")
        dados = request.get_json()
        print(f"📋 Dados recebidos: {dados}")
        
        topicos_selecionados = dados.get('topicos', [])
        ano_inicio = int(dados.get('ano_inicio', 2024))
        ano_fim = int(dados.get('ano_fim', 2025))
        min_resultados = int(dados.get('min_resultados', 50))
        
        print(f"🎯 Tópicos: {topicos_selecionados}")
        print(f"📅 Período: {ano_inicio}-{ano_fim}")
        print(f"📊 Min resultados: {min_resultados}")
        
        if not topicos_selecionados:
            print("❌ Nenhum tópico selecionado")
            return jsonify({'erro': 'Nenhum tópico selecionado'}), 400
        
        # Resetar progresso completamente
        global progresso_busca
        progresso_busca = {
            'status': 'iniciando nova busca', 
            'progresso': 0, 
            'total_resultados': 0, 
            'topico_atual': '',
            'busca_id': f"{ano_inicio}-{ano_fim}-{len(topicos_selecionados)}"
        }
        print(f"🔄 Progresso resetado para nova busca")
        
        print("🧵 Iniciando thread de scraping...")
        # Iniciar o scraping em uma thread separada
        thread = threading.Thread(
            target=executar_web_scraping,
            args=(topicos_selecionados, ano_inicio, ano_fim, min_resultados),
            daemon=True
        )
        thread.start()
        
        print("✅ Thread iniciada com sucesso")
        return jsonify({'sucesso': True, 'mensagem': 'Busca iniciada com sucesso'})
    
    except Exception as e:
        print(f"❌ Erro na rota iniciar_busca: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/progresso')
def obter_progresso():
    """Retorna o progresso atual da busca"""
    global progresso_busca
    print(f"📊 Progresso solicitado: {progresso_busca}")
    return jsonify(progresso_busca)

@app.route('/resultados')
@app.route('/exibir_resultados')
def exibir_resultados():
    """Página para exibir os resultados e gráficos"""
    return render_template('resultados.html')

@app.route('/teste')
def teste_graficos():
    """Página de teste para Chart.js"""
    return render_template('teste.html')

@app.route('/dados_tabela')
def obter_dados_tabela():
    """Retorna os dados em formato JSON para a tabela"""
    try:
        conn = sqlite3.connect("buscas_completas_CQ.db")
        cursor = conn.cursor()
        
        # Buscar dados com SQL direto para garantir compatibilidade
        cursor.execute("SELECT * FROM resultados_detalhados_CQ ORDER BY id DESC LIMIT 1000")
        colunas = [description[0] for description in cursor.description]
        linhas = cursor.fetchall()
        
        # Converter para lista de dicionários
        dados = []
        for linha in linhas:
            registro = {}
            for i, coluna in enumerate(colunas):
                registro[coluna] = linha[i]
            dados.append(registro)
        
        conn.close()
        
        print(f"📊 Retornando {len(dados)} registros para a tabela")
        return jsonify(dados)
    
    except Exception as e:
        print(f"❌ Erro na rota dados_tabela: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/storytelling')
@app.route('/exibir_storytelling')
def exibir_storytelling():
    """Página de storytelling com dados"""
    try:
        # Verificar se existem dados no banco
        conn = sqlite3.connect("buscas_completas_CQ.db")
        df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
        conn.close()
        
        if df.empty:
            # Sem dados - mostrar página vazia
            return render_template('storytelling.html', resultados=None, topicos=None, anos=None)
        
        # Com dados - preparar informações básicas
        topicos = df['termo'].unique().tolist() if 'termo' in df.columns else []
        anos = df['ano_publicacao'].unique().tolist() if 'ano_publicacao' in df.columns else []
        resultados = df.to_dict('records')
        
        print(f"📖 Dados disponíveis para storytelling: {len(resultados)} artigos, {len(topicos)} tópicos")
        return render_template('storytelling.html', resultados=resultados, topicos=topicos, anos=anos)
        
    except Exception as e:
        print(f"❌ Erro ao carregar storytelling: {e}")
        return render_template('storytelling.html', resultados=None, topicos=None, anos=None)

@app.route('/chat_cientifico_page')
def chat_cientifico_page():
    """Exibe a página do chat científico"""
    return render_template('chat_cientifico.html')

@app.route('/chat_cientifico', methods=['POST'])
def chat_cientifico():
    """Endpoint para chat científico com RAG"""
    global chat_history
    
    try:
        data = request.get_json()
        pergunta = data.get('pergunta', '').strip()
        
        if not pergunta:
            return jsonify({
                'success': False,
                'error': 'Pergunta não pode estar vazia'
            })
        
        # Extrair dados RAG atuais
        dados_rag = extrair_dados_rag()
        
        if not dados_rag:
            return jsonify({
                'success': False,
                'error': 'Nenhum dado de pesquisa encontrado. Execute uma busca primeiro.',
                'resposta': '📊 Para fazer perguntas sobre análises, é necessário primeiro realizar uma busca científica. Vá em "Nova Busca" para coletar dados.'
            })
        
        # Gerar resposta com RAG
        resposta = gerar_resposta_cientifica_rag(pergunta, dados_rag, chat_history)
        
        # Atualizar histórico de conversa (máximo 10 pares)
        chat_history.append({'role': 'user', 'content': pergunta})
        chat_history.append({'role': 'assistant', 'content': resposta})
        
        # Manter apenas últimas 10 mensagens para eficiência
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]
        
        return jsonify({
            'success': True,
            'resposta': resposta,
            'total_artigos': dados_rag['metadados']['total_artigos'],
            'periodo': dados_rag['metadados']['periodo']
        })
        
    except Exception as e:
        print(f"❌ Erro no chat científico: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

@app.route('/limpar_chat', methods=['POST'])
def limpar_chat():
    """Limpa o histórico do chat"""
    global chat_history
    chat_history = []
    return jsonify({'success': True, 'message': 'Histórico limpo com sucesso'})

@app.route('/dados_contexto')
def dados_contexto():
    """Retorna contexto atual dos dados para o chat"""
    try:
        dados_rag = extrair_dados_rag()
        if not dados_rag:
            return jsonify({'dados_disponiveis': False})
            
        return jsonify({
            'dados_disponiveis': True,
            'resumo': {
                'total_artigos': dados_rag['metadados']['total_artigos'],
                'periodo': dados_rag['metadados']['periodo'],
                'topicos': dados_rag['metadados']['topicos'],
                'palavras_principais': list(dados_rag['palavras_chave']['top_10'].keys())[:5]
            }
        })
    except Exception as e:
        return jsonify({'dados_disponiveis': False, 'error': str(e)})

@app.route('/gerar_storytelling', methods=['POST'])
def gerar_storytelling_endpoint():
    """Endpoint para gerar storytelling com IA"""
    try:
        # Buscar dados do banco
        conn = sqlite3.connect("buscas_completas_CQ.db")
        df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
        conn.close()
        
        if df.empty:
            return jsonify({
                'success': False,
                'error': 'Nenhum dado encontrado. Execute uma busca primeiro.'
            })
        
        # Preparar dados agregados para o LLM
        dados_agregados = {
            'top_palavras': {},
            'temporal': {'labels': [], 'data': []},
            'sentimentos': {'positivo': 0, 'negativo': 0, 'neutro': 0}
        }
        
        # Análise temporal
        if 'ano_publicacao' in df.columns:
            temporal_data = df['ano_publicacao'].value_counts().sort_index()
            dados_agregados['temporal']['labels'] = temporal_data.index.tolist()
            dados_agregados['temporal']['data'] = temporal_data.values.tolist()
        
        # Análise de palavras-chave
        if 'titulo' in df.columns or 'resumo' in df.columns:
            texto_completo = (df['titulo'].fillna('') + ' ' + df['resumo'].fillna('')).str.lower()
            palavras = []
            for texto in texto_completo:
                palavras.extend(re.findall(r'\b[a-z]{4,}\b', texto))
            
            # Contar palavras e remover stopwords
            stopwords_custom = {'computacao', 'quantica', 'quântico', 'quantum', 'para', 'com', 'que', 'uma', 'como'}
            contador = Counter([p for p in palavras if p not in stopwords_custom])
            dados_agregados['top_palavras'] = dict(contador.most_common(10))
        
        # Análise de sentimentos simples
        palavras_positivas = {'inovação', 'avanços', 'eficiente', 'melhor', 'sucesso', 'promissor'}
        palavras_negativas = {'problema', 'limitação', 'desafio', 'dificuldade', 'erro'}
        
        for texto in texto_completo:
            texto_words = set(texto.split())
            if any(p in texto_words for p in palavras_positivas):
                dados_agregados['sentimentos']['positivo'] += 1
            elif any(n in texto_words for n in palavras_negativas):
                dados_agregados['sentimentos']['negativo'] += 1
            else:
                dados_agregados['sentimentos']['neutro'] += 1
        
        # Gerar storytelling com LLM
        narrativa_llm = gerar_storytelling_llm(dados_agregados)
        
        return jsonify({
            'success': True,
            'storytelling': narrativa_llm
        })
        
    except Exception as e:
        print(f"❌ Erro ao gerar storytelling: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

@app.route('/dados_storytelling')
def obter_dados_storytelling():
    """Retorna dados estruturados para storytelling"""
    try:
        if gerar_dados_storytelling:
            narrativa = gerar_dados_storytelling()
            if narrativa:
                print(f"📖 Narrativa de storytelling gerada com sucesso")
                return jsonify(narrativa)
            else:
                return jsonify({
                    'erro': 'Dados insuficientes para gerar narrativa',
                    'narrativa_vazia': True
                })
        else:
            return jsonify({'erro': 'Módulo de storytelling não disponível'}), 500
    except Exception as e:
        print(f"❌ Erro na rota dados_storytelling: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/dados_graficos')
def obter_dados_graficos():
    """Retorna os dados em formato JSON para gráficos interativos"""
    try:
        conn = sqlite3.connect("buscas_completas_CQ.db")
        df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
        conn.close()
        
        if df.empty:
            # Retornar dados vazios em vez de erro 404
            dados_vazios = {
                'sentimentos': {'labels': [], 'data': [], 'colors': []},
                'temporal': {'labels': [], 'data': []},
                'top_palavras': {'labels': [], 'data': []},
                'tendencias': {'anos': [], 'topicos': {}},
                'fontes': {'labels': [], 'data': []},
                'message': 'Nenhum dado encontrado. Execute uma busca primeiro.'
            }
            return jsonify(dados_vazios)
        
        # Verificar NLTK
        verificar_nltk()
        
        # Preparar dados
        df['texto_completo'] = df['titulo'].fillna('') + ' ' + df['resumo'].fillna('')
        df['texto_limpo'] = df['texto_completo'].str.lower().apply(lambda x: re.sub(r'[^a-z\s]', '', x))
        
        stopwords_custom = set(stopwords.words('portuguese')).union({
            'computacao', 'quantica', 'quântico', 'quantum', 'trabalho', 'estudo', 'pesquisa',
            'neste', 'este', 'para', 'com', 'que', 'uma', 'como', 'sobre', 'dados', 'resultados'
        })
        
        df['texto_filtrado'] = df['texto_limpo'].apply(lambda x: ' '.join([w for w in x.split() if w not in stopwords_custom]))
        
        dados_graficos = {}
        
        # 1. Análise de Sentimento
        try:
            positivas = {'inovação', 'oportunidades', 'avanços', 'eficiente', 'sucesso', 'melhor', 'novo', 'promissor'}
            negativas = {'desafios', 'problemas', 'riscos', 'limitações', 'ameaça', 'dificuldade', 'complexo'}
            
            def sentimento(texto):
                if not isinstance(texto, str):
                    return 'Neutro'
                texto = texto.lower()
                p = sum(1 for w in positivas if w in texto)
                n = sum(1 for w in negativas if w in texto)
                return 'Positivo' if p > n else 'Negativo' if n > p else 'Neutro'
            
            df['sentimento'] = df['resumo'].apply(sentimento)
            sentimento_counts = df['sentimento'].value_counts()
            
            dados_graficos['sentimentos'] = {
                'labels': sentimento_counts.index.tolist(),
                'data': sentimento_counts.values.tolist(),
                'colors': ['#28a745', '#dc3545', '#6c757d']
            }
        except Exception as e:
            print(f"Erro na análise de sentimento: {e}")
        
        # 2. Análise Temporal
        try:
            df['ano_publicacao'] = pd.to_numeric(df['ano_publicacao'], errors='coerce')
            df_anos = df.dropna(subset=['ano_publicacao'])
            df_anos = df_anos[(df_anos['ano_publicacao'] >= 1900) & (df_anos['ano_publicacao'] <= 2025)]
            df_anos['ano_publicacao'] = df_anos['ano_publicacao'].astype(int)
            
            if not df_anos.empty:
                anos_contagem = df_anos['ano_publicacao'].value_counts().sort_index()
                
                dados_graficos['temporal'] = {
                    'labels': anos_contagem.index.tolist(),
                    'data': anos_contagem.values.tolist()
                }
        except Exception as e:
            print(f"Erro na análise temporal: {e}")
        
        # 3. Top Palavras
        try:
            texto_total = ' '.join(df['texto_filtrado'].dropna())
            palavras = [word for word in texto_total.split() if len(word) > 3]
            
            if palavras:
                contador_palavras = Counter(palavras)
                top_palavras = contador_palavras.most_common(15)
                
                dados_graficos['top_palavras'] = {
                    'labels': [palavra for palavra, _ in top_palavras],
                    'data': [count for _, count in top_palavras]
                }
        except Exception as e:
            print(f"Erro no top palavras: {e}")
        
        # 4. Tendências por Tópico
        try:
            if 'termo' in df.columns and not df_anos.empty:
                tendencias = df_anos.groupby(['ano_publicacao', 'termo']).size().unstack(fill_value=0)
                top_topicos = df['termo'].value_counts().head(5).index
                
                dados_topicos = {}
                for topico in top_topicos:
                    if topico in tendencias.columns:
                        dados_topicos[topico] = tendencias[topico].to_dict()
                
                dados_graficos['tendencias'] = {
                    'anos': sorted(tendencias.index.tolist()),
                    'topicos': dados_topicos
                }
        except Exception as e:
            print(f"Erro nas tendências: {e}")
        
        # 5. Distribuição por Fonte
        try:
            if 'fonte_publicacao' in df.columns:
                fontes = df['fonte_publicacao'].fillna('Não informado').value_counts().head(10)
                
                dados_graficos['fontes'] = {
                    'labels': fontes.index.tolist(),
                    'data': fontes.values.tolist()
                }
        except Exception as e:
            print(f"Erro na distribuição por fonte: {e}")
        
        print(f"📊 Dados dos gráficos gerados com sucesso: {list(dados_graficos.keys())}")
        return jsonify(dados_graficos)
    
    except Exception as e:
        print(f"❌ Erro na rota dados_graficos: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/storytelling_llm')
def obter_storytelling_llm():
    """🤖 Sistema QAARS: Retorna storytelling inteligente com LLM"""
    try:
        print("🤖 Iniciando geração de storytelling LLM...")
        
        # 1. Obter dados agregados da função existente
        conn = sqlite3.connect("buscas_completas_CQ.db")
        df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
        conn.close()
        
        if df.empty:
            return jsonify({
                'narrativa': "**⚠️ Nenhum dado disponível:** Execute uma busca primeiro para gerar o storytelling inteligente.",
                'status': 'sem_dados'
            })
        
        # 2. Processar dados com o mesmo método dos gráficos
        verificar_nltk()
        
        # Aplicar o mesmo processamento melhorado
        df['texto_completo'] = df['titulo'].fillna('') + ' ' + df['resumo'].fillna('')
        df['texto_limpo'] = df['texto_completo'].str.lower()
        df['texto_limpo'] = df['texto_limpo'].str.replace(r'[^\w\s]', ' ', regex=True)
        df['texto_limpo'] = df['texto_limpo'].str.replace(r'\d+', '', regex=True)
        df['texto_limpo'] = df['texto_limpo'].str.replace(r'\s+', ' ', regex=True)
        df['texto_limpo'] = df['texto_limpo'].str.strip()
        
        # Mesmo filtro de stopwords melhorado
        stopwords_custom = set(stopwords.words('portuguese')).union(set(stopwords.words('english'))).union({
            'computacao', 'quantica', 'quântico', 'quantum', 'trabalho', 'estudo', 'pesquisa', 'paper',
            'article', 'estudo', 'revisao', 'analise', 'survey', 'research', 'study', 'analysis',
            'utilizacao', 'aplicacao', 'desenvolvimento', 'proposta', 'abordagem', 'metodologia',
            'implementacao', 'avaliacao', 'comparacao', 'experimental', 'theoretical',
            'neste', 'este', 'esta', 'esse', 'essa', 'para', 'com', 'que', 'uma', 'como', 'sobre',
            'dados', 'resultados', 'caso', 'assim', 'ainda', 'pode', 'ser', 'mais', 'muito',
            'bem', 'entre', 'durante', 'através', 'mediante', 'também', 'já', 'apenas',
            'introduction', 'conclusion', 'abstract', 'keywords', 'references', 'resumo', 'introducao',
            'conclusao', 'referencias', 'palavras', 'chave', 'método', 'metodo'
        })
        
        def filtrar_palavras_significativas(texto):
            palavras = texto.split()
            palavras_filtradas = []
            for palavra in palavras:
                if (len(palavra) >= 4 and palavra not in stopwords_custom and 
                    not palavra.isdigit() and palavra.isalpha() and len(set(palavra)) > 2):
                    palavras_filtradas.append(palavra)
            return ' '.join(palavras_filtradas)
        
        df['texto_filtrado'] = df['texto_limpo'].apply(filtrar_palavras_significativas)
        
        # 3. Criar dados agregados para LLM
        dados_agregados = {}
        
        # Sentimentos
        positivas = {'inovação', 'oportunidades', 'avanços', 'eficiente', 'sucesso', 'melhor', 'novo', 'promissor'}
        negativas = {'desafios', 'problemas', 'riscos', 'limitações', 'ameaça', 'dificuldade', 'complexo'}
        
        def sentimento(texto):
            if not isinstance(texto, str):
                return 'neutro'
            texto = texto.lower()
            p = sum(1 for w in positivas if w in texto)
            n = sum(1 for w in negativas if w in texto)
            return 'positivo' if p > n else 'negativo' if n > p else 'neutro'
        
        df['sentimento'] = df['resumo'].apply(sentimento)
        sentimento_counts = df['sentimento'].value_counts()
        dados_agregados['sentimentos'] = {
            'positivo': sentimento_counts.get('positivo', 0),
            'negativo': sentimento_counts.get('negativo', 0),
            'neutro': sentimento_counts.get('neutro', 0)
        }
        
        # Temporal
        df['ano_publicacao'] = pd.to_numeric(df['ano_publicacao'], errors='coerce')
        df_anos = df.dropna(subset=['ano_publicacao'])
        df_anos = df_anos[(df_anos['ano_publicacao'] >= 1900) & (df_anos['ano_publicacao'] <= 2025)]
        if not df_anos.empty:
            df_anos['ano_publicacao'] = df_anos['ano_publicacao'].astype(int)
            anos_contagem = df_anos['ano_publicacao'].value_counts().sort_index()
            dados_agregados['temporal'] = {
                'labels': anos_contagem.index.tolist(),
                'data': anos_contagem.values.tolist()
            }
        else:
            dados_agregados['temporal'] = {'labels': [], 'data': []}
        
        # Top palavras (corrigidas)
        texto_total = ' '.join(df['texto_filtrado'].dropna())
        palavras = [word for word in texto_total.split() if len(word) > 3]
        if palavras:
            contador_palavras = Counter(palavras)
            top_palavras = contador_palavras.most_common(15)
            dados_agregados['top_palavras'] = dict(top_palavras)
        else:
            dados_agregados['top_palavras'] = {}
        
        # Tendências e fontes
        if 'termo' in df.columns and not df_anos.empty:
            tendencias = df_anos.groupby(['ano_publicacao', 'termo']).size().unstack(fill_value=0)
            top_topicos = df['termo'].value_counts().head(5).index
            dados_topicos = {}
            for topico in top_topicos:
                if topico in tendencias.columns:
                    dados_topicos[topico] = tendencias[topico].to_dict()
            dados_agregados['tendencias'] = {'anos': sorted(tendencias.index.tolist()), 'topicos': dados_topicos}
        else:
            dados_agregados['tendencias'] = {'anos': [], 'topicos': {}}
            
        if 'fonte_publicacao' in df.columns:
            fontes = df['fonte_publicacao'].fillna('Não informado').value_counts().head(10)
            dados_agregados['fontes'] = dict(fontes)
        else:
            dados_agregados['fontes'] = {}
        
        # 4. Gerar storytelling com LLM
        narrativa_llm = gerar_storytelling_llm(dados_agregados)
        
        print("✅ Storytelling LLM gerado com sucesso")
        return jsonify({
            'narrativa': narrativa_llm,
            'status': 'success',
            'timestamp': time.time()
        })
        
    except Exception as e:
        print(f"❌ Erro no storytelling LLM: {e}")
        return jsonify({
            'narrativa': f"**Erro na Geração de Storytelling:** {str(e)}",
            'status': 'error'
        }), 500

if __name__ == '__main__':
    # Criar diretórios necessários
    os.makedirs('static/plots', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("Diretórios criados com sucesso!")
    print("Servidor iniciando...")
    
    # Executar aplicação
    app.run(debug=True, host='0.0.0.0', port=5000)
