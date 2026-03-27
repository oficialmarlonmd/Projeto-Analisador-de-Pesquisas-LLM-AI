#!/usr/bin/env python3
"""
Sistema de Storytelling com Dados
Implementa os 6 princípios fundamentais para transformar dados em narrativas impactantes
"""

import sqlite3
import pandas as pd
import re
from collections import Counter
from datetime import datetime

class DataStorytellingEngine:
    """Motor de Storytelling com Dados baseado nas 6 lições fundamentais"""
    
    def __init__(self, db_path="buscas_completas_CQ.db"):
        self.db_path = db_path
        self.cor_principal = "#FF6B35"  # Laranja vibrante para destaques
        self.cor_contexto = "#666666"   # Cinza para contexto
        self.cor_secundaria = "#E8E8E8" # Cinza claro para background
        
    def definir_contexto(self):
        """Lição 1: Entender o Contexto - Quem, O Quê, Como"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
            conn.close()
            
            if df.empty:
                return None
                
            # Análise do contexto
            topicos = df['termo'].value_counts()
            periodo = self._extrair_periodo(df)
            total_artigos = len(df)
            
            # Definir público e ação
            contexto = {
                'publico_alvo': 'Pesquisadores e tomadores de decisão em Computação Quântica',
                'acao_desejada': 'Identificar tendências emergentes e oportunidades de pesquisa',
                'comunicacao': 'Dashboard interativo com narrativa sequencial',
                'topicos_principais': topicos.head(3).to_dict(),
                'periodo': periodo,
                'total_artigos': total_artigos,
                'tipo_analise': 'Explanatória' if total_artigos > 0 else 'Exploratória'
            }
            
            return contexto
            
        except Exception as e:
            print(f"Erro ao definir contexto: {e}")
            return None
    
    def _extrair_periodo(self, df):
        """Extrai o período temporal dos dados"""
        df['ano_publicacao'] = pd.to_numeric(df['ano_publicacao'], errors='coerce')
        anos_validos = df['ano_publicacao'].dropna()
        if not anos_validos.empty:
            return {
                'ano_inicio': int(anos_validos.min()),
                'ano_fim': int(anos_validos.max()),
                'anos_cobertura': len(anos_validos.unique())
            }
        return {'ano_inicio': None, 'ano_fim': None, 'anos_cobertura': 0}
    
    def gerar_insights_principais(self):
        """Identifica os insights-chave para a narrativa"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM resultados_detalhados_CQ", conn)
            conn.close()
            
            insights = {}
            
            # 1. Tendência Temporal
            df['ano_publicacao'] = pd.to_numeric(df['ano_publicacao'], errors='coerce')
            df_anos = df.dropna(subset=['ano_publicacao'])
            if not df_anos.empty:
                anos_count = df_anos['ano_publicacao'].value_counts().sort_index()
                if len(anos_count) >= 2:
                    crescimento = anos_count.iloc[-1] - anos_count.iloc[0]
                    tendencia = "crescente" if crescimento > 0 else "decrescente" if crescimento < 0 else "estável"
                    insights['tendencia_temporal'] = {
                        'tipo': tendencia,
                        'crescimento_absoluto': crescimento,
                        'ano_pico': anos_count.idxmax(),
                        'publicacoes_pico': anos_count.max()
                    }
            
            # 2. Tópico Dominante
            if 'termo' in df.columns:
                topicos = df['termo'].value_counts()
                topico_principal = topicos.index[0]
                participacao = (topicos.iloc[0] / len(df)) * 100
                insights['topico_dominante'] = {
                    'nome': topico_principal,
                    'participacao_percentual': round(participacao, 1),
                    'quantidade': topicos.iloc[0]
                }
            
            # 2. Análise de Sentimento
            insights['sentimento'] = self._analisar_sentimento_avancado(df)
            
            # 3. Palavras-chave emergentes
            insights['palavras_emergentes'] = self._extrair_palavras_chave(df)
            
            return insights
            
        except Exception as e:
            print(f"Erro ao gerar insights: {e}")
            return {}
    
    def _analisar_sentimento_avancado(self, df):
        """Análise de sentimento mais sofisticada"""
        # Expandir vocabulários de sentimento
        palavras_positivas = {
            'inovação', 'inovador', 'avanços', 'avanço', 'eficiente', 'eficiência', 
            'sucesso', 'melhor', 'melhoria', 'novo', 'nova', 'promissor', 'promissora',
            'oportunidades', 'oportunidade', 'potencial', 'vantagem', 'benefício',
            'otimização', 'aprimoramento', 'superior', 'revolucionário', 'breakthrough'
        }
        
        palavras_negativas = {
            'desafios', 'desafio', 'problemas', 'problema', 'riscos', 'risco',
            'limitações', 'limitação', 'ameaça', 'dificuldade', 'complexo', 'complexa',
            'obstáculo', 'barreira', 'falha', 'erro', 'instabilidade', 'ruído'
        }
        
        def calcular_sentimento(texto):
            if not isinstance(texto, str):
                return 'Neutro', 0
            
            texto_lower = texto.lower()
            score_positivo = sum(1 for palavra in palavras_positivas if palavra in texto_lower)
            score_negativo = sum(1 for palavra in palavras_negativas if palavra in texto_lower)
            
            if score_positivo > score_negativo:
                return 'Positivo', score_positivo - score_negativo
            elif score_negativo > score_positivo:
                return 'Negativo', score_negativo - score_positivo
            else:
                return 'Neutro', 0
        
        try:
            # Aplicar análise de forma mais robusta
            resultados_sentimento = []
            scores = []
            
            for index, row in df.iterrows():
                resumo = row.get('resumo', '')
                sent, score = calcular_sentimento(resumo)
                resultados_sentimento.append(sent)
                scores.append(score)
            
            # Contar sentimentos
            from collections import Counter
            sentimento_counts = Counter(resultados_sentimento)
            sentimento_dominante = max(sentimento_counts, key=sentimento_counts.get)
            
            return {
                'dominante': sentimento_dominante,
                'distribuicao': dict(sentimento_counts),
                'score_medio': sum(scores) / len(scores) if scores else 0,
                'interpretacao': self._interpretar_sentimento(sentimento_dominante, sentimento_counts)
            }
            
        except Exception as e:
            print(f"Erro na análise de sentimento: {e}")
            return {
                'dominante': 'Neutro',
                'distribuicao': {'Neutro': len(df)},
                'score_medio': 0,
                'interpretacao': 'Análise de sentimento em desenvolvimento'
            }
    
    def _interpretar_sentimento(self, dominante, counts):
        """Gera interpretação textual do sentimento"""
        total = sum(counts.values())
        perc_dominante = (counts[dominante] / total) * 100
        
        if dominante == 'Positivo':
            if perc_dominante > 60:
                return f"Cenário amplamente otimista ({perc_dominante:.1f}%): Foco em inovações e oportunidades"
            else:
                return f"Tendência positiva moderada ({perc_dominante:.1f}%): Equilibrio entre oportunidades e desafios"
        elif dominante == 'Negativo':
            if perc_dominante > 60:
                return f"Cenário desafiador ({perc_dominante:.1f}%): Foco em limitações e obstáculos"
            else:
                return f"Presença significativa de desafios ({perc_dominante:.1f}%): Área em desenvolvimento"
        else:
            return f"Cenário equilibrado ({perc_dominante:.1f}%): Abordagem técnica e objetiva"
    
    def _extrair_palavras_chave(self, df):
        """Extrai e analisa palavras-chave emergentes"""
        try:
            # Combinar título e resumo
            texto_completo = ' '.join(df['titulo'].fillna('') + ' ' + df['resumo'].fillna(''))
            texto_limpo = re.sub(r'[^a-záàâãéèêíìîóòôõúùûç\s]', '', texto_completo.lower())
            
            # Stopwords customizadas para computação quântica
            stopwords_custom = {
                'computacao', 'quantica', 'quântico', 'quântica', 'quantum', 'trabalho', 
                'estudo', 'pesquisa', 'neste', 'este', 'esta', 'para', 'com', 'que', 
                'uma', 'como', 'sobre', 'dados', 'resultados', 'artigo', 'paper',
                'utilizando', 'através', 'baseado', 'proposto', 'apresenta', 'são',
                'foi', 'ser', 'ter', 'fazer', 'dos', 'das', 'por', 'mais', 'muito'
            }
            
            # Filtrar palavras
            palavras = [palavra for palavra in texto_limpo.split() 
                       if len(palavra) > 3 and palavra not in stopwords_custom]
            
            # Contar e retornar top palavras
            contador = Counter(palavras)
            top_palavras = contador.most_common(10)
            
            return {
                'top_10': top_palavras,
                'palavra_dominante': top_palavras[0] if top_palavras else None,
                'diversidade': len(set(palavras)),
                'densidade': len(palavras) / len(df) if len(df) > 0 else 0
            }
            
        except Exception as e:
            print(f"Erro na extração de palavras-chave: {e}")
            return {}
    
    def criar_narrativa_estruturada(self):
        """Lição 6: Contar uma História - Estrutura narrativa completa"""
        contexto = self.definir_contexto()
        insights = self.gerar_insights_principais()
        
        if not contexto or not insights:
            return None
        
        # Estrutura: Início, Meio, Fim
        narrativa = {
            'inicio': self._criar_introducao(contexto, insights),
            'meio': self._criar_desenvolvimento(insights),
            'fim': self._criar_conclusao(insights),
            'configuracao_visual': self._definir_configuracao_visual()
        }
        
        return narrativa
    
    def _criar_introducao(self, contexto, insights):
        """Início: Contexto e Problema"""
        periodo_texto = f"{contexto['periodo']['ano_inicio']}-{contexto['periodo']['ano_fim']}" if contexto['periodo']['ano_inicio'] else "período analisado"
        
        introducao = {
            'titulo_principal': f"Panorama da Pesquisa em Computação Quântica ({periodo_texto})",
            'subtitulo': f"Análise de {contexto['total_artigos']} publicações científicas",
            'problema': "Como as tendências de pesquisa em computação quântica estão evoluindo e quais áreas apresentam maior potencial?",
            'contexto_visual': 'grafico_temporal',
            'mensagem_chave': self._gerar_mensagem_temporal(insights)
        }
        
        return introducao
    
    def _criar_desenvolvimento(self, insights):
        """Meio: Dados e Insights"""
        desenvolvimento = {
            'secao_1': {
                'titulo': "Dominância Temática na Pesquisa",
                'visual': 'distribuicao_topicos',
                'insight': f"'{insights.get('topico_dominante', {}).get('nome', 'N/A')}' representa {insights.get('topico_dominante', {}).get('participacao_percentual', 0):.1f}% da produção científica",
                'interpretacao': "Concentração de esforços de pesquisa indica maturidade ou emergência da área"
            },
            'secao_2': {
                'titulo': "Linguagem e Foco da Pesquisa",
                'visual': 'palavras_chave',
                'insight': f"'{insights.get('palavras_emergentes', {}).get('palavra_dominante', ['', 0])[0]}' é o termo mais recorrente",
                'interpretacao': "Palavras-chave revelam as prioridades e direções da comunidade científica"
            }
        }
        
        return desenvolvimento
    
    def _criar_conclusao(self, insights):
        """Fim: Conclusão e Chamada para Ação"""
        sentimento_info = insights.get('sentimento', {})
        
        conclusao = {
            'titulo': "Perspectivas e Recomendações Estratégicas",
            'visual': 'analise_sentimento',
            'insight_principal': sentimento_info.get('interpretacao', 'Cenário em análise'),
            'recomendacoes': self._gerar_recomendacoes(insights),
            'chamada_acao': "Direcionar investimentos e esforços de pesquisa nas áreas identificadas como emergentes"
        }
        
        return conclusao
    
    def _gerar_mensagem_temporal(self, insights):
        """Gera mensagem sobre tendência temporal"""
        tendencia = insights.get('tendencia_temporal', {})
        if tendencia:
            tipo = tendencia.get('tipo', 'estável')
            if tipo == 'crescente':
                return f"Crescimento de {tendencia.get('crescimento_absoluto', 0)} publicações no período analisado"
            elif tipo == 'decrescente':
                return f"Declínio de {abs(tendencia.get('crescimento_absoluto', 0))} publicações no período analisado"
            else:
                return "Produção científica mantém-se estável no período"
        return "Análise temporal em desenvolvimento"
    
    def _gerar_recomendacoes(self, insights):
        """Gera recomendações baseadas nos insights"""
        recomendacoes = []
        
        # Recomendação baseada em tendência temporal
        tendencia = insights.get('tendencia_temporal', {})
        if tendencia and tendencia.get('tipo') == 'crescente':
            recomendacoes.append("Área em expansão: Aumentar investimentos e colaborações")
        elif tendencia and tendencia.get('tipo') == 'decrescente':
            recomendacoes.append("Área em declínio: Investigar causas e novas direções")
        
        # Recomendação baseada em sentimento
        sentimento = insights.get('sentimento', {})
        if sentimento.get('dominante') == 'Positivo':
            recomendacoes.append("Cenário otimista: Acelerar desenvolvimento e aplicação prática")
        elif sentimento.get('dominante') == 'Negativo':
            recomendacoes.append("Desafios identificados: Focar em soluções e superação de limitações")
        
        # Recomendação baseada no tópico dominante
        topico = insights.get('topico_dominante', {})
        if topico and topico.get('participacao_percentual', 0) > 50:
            recomendacoes.append(f"Concentração em '{topico.get('nome')}': Considerar diversificação de pesquisa")
        
        return recomendacoes if recomendacoes else ["Continuar monitoramento e análise das tendências"]
    
    def _definir_configuracao_visual(self):
        """Lições 2-5: Configuração visual seguindo princípios de design"""
        return {
            'cores': {
                'principal': self.cor_principal,
                'contexto': self.cor_contexto,
                'background': self.cor_secundaria
            },
            'tipografia': {
                'titulo_principal': {'tamanho': 24, 'peso': 'bold'},
                'subtitulo': {'tamanho': 18, 'peso': 'normal'},
                'corpo': {'tamanho': 14, 'peso': 'normal'},
                'destaque': {'tamanho': 16, 'peso': 'bold', 'cor': self.cor_principal}
            },
            'principios': {
                'eliminar_ruido': True,
                'rotulos_diretos': True,
                'contraste_alto': True,
                'espaco_branco': 'generoso'
            }
        }

def gerar_dados_storytelling():
    """Função principal para gerar dados de storytelling"""
    engine = DataStorytellingEngine()
    return engine.criar_narrativa_estruturada()

if __name__ == "__main__":
    # Teste do sistema
    engine = DataStorytellingEngine()
    narrativa = engine.criar_narrativa_estruturada()
    
    if narrativa:
        print("📖 NARRATIVA DE STORYTELLING COM DADOS")
        print("=" * 50)
        print(f"INÍCIO: {narrativa['inicio']['titulo_principal']}")
        print(f"PROBLEMA: {narrativa['inicio']['problema']}")
        print(f"INSIGHT: {narrativa['inicio']['mensagem_chave']}")
        print("\nMEIO:")
        for secao in narrativa['meio'].values():
            if isinstance(secao, dict):
                print(f"  {secao['titulo']}: {secao['insight']}")
        print(f"\nFIM: {narrativa['fim']['insight_principal']}")
        print("RECOMENDAÇÕES:")
        for rec in narrativa['fim']['recomendacoes']:
            print(f"  • {rec}")
    else:
        print("Nenhuma narrativa gerada (dados insuficientes)")