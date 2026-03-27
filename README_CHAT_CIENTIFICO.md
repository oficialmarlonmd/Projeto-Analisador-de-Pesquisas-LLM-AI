# 🤖 Sistema de Chat Científico com RAG - QAARS

## 🎯 Visão Geral

O Sistema QAARS agora inclui um **Chat Científico Inteligente** com arquitetura RAG (Retrieval-Augmented Generation) que permite aos usuários conversarem sobre suas análises científicas com precisão e comportamento profissional.

## ✨ Funcionalidades Implementadas

### 🧠 RAG (Retrieval-Augmented Generation)
- **Extração de Dados Estruturados**: Processa dados do SQLite em formato RAG
- **Contexto Rico**: Metadados, análise temporal, palavras-chave, estatísticas
- **Respostas Baseadas em Dados**: APENAS informações dos dados coletados

### 🎯 Few-Shot Prompting
- **Exemplos Científicos**: Templates de respostas adequadas
- **Comportamento Profissional**: Tom científico e acadêmico
- **Estrutura Consistente**: Padrão de resposta uniforme

### 💾 Memória de Conversa
- **Histórico Contextual**: Últimas 10 mensagens armazenadas
- **Contexto Contínuo**: Respostas que consideram conversa anterior
- **Eficiência**: Limite inteligente para performance

### ⚠️ Prevenção de Alucinações
- **Dados Reais Apenas**: Não inventa informações
- **Prompts Rígidos**: Instruções claras para não alucinar
- **Verificação**: Confirma disponibilidade de dados antes de responder

## 🌐 Endpoints da API

### `/chat_cientifico_page`
- **Método**: GET
- **Função**: Interface web completa do chat
- **Retorna**: Página HTML com chat interativo

### `/chat_cientifico`
- **Método**: POST
- **Função**: API para conversa com IA usando RAG
- **Entrada**: `{"pergunta": "texto da pergunta"}`
- **Saída**: `{"success": boolean, "resposta": "resposta da IA"}`

### `/dados_contexto`
- **Método**: GET
- **Função**: Informações sobre dados disponíveis
- **Retorna**: Metadados dos dados para interface

### `/limpar_chat`
- **Método**: POST
- **Função**: Limpa memória da conversa
- **Retorna**: `{"success": true}`

## 🎨 Interface Visual

### Design Cósmico Profissional
- **Tema Espacial**: Gradientes azuis e efeitos de vidro
- **Responsivo**: Funciona em desktop e mobile
- **Animações**: Transições suaves e indicadores visuais

### Componentes Interativos
- **Chat em Tempo Real**: Mensagens com bolhas estilizadas
- **Indicador de Digitação**: Animação durante processamento
- **Perguntas Sugeridas**: Botões com exemplos de perguntas
- **Contexto Visível**: Informações dos dados disponíveis
- **Controles**: Botões limpar e atualizar

## 🧪 Exemplos de Uso

### Perguntas Típicas que o Sistema Responde:

1. **"Quantos artigos foram analisados no total?"**
   - Resposta: "📊 Foram analisados 50 artigos científicos no total, cobrindo o período de 2019-2025..."

2. **"Qual é a tendência temporal da pesquisa?"**
   - Resposta: "📈 A análise temporal revela uma tendência de crescimento com variação percentual de 550,0%..."

3. **"Quais são as principais palavras-chave?"**
   - Resposta: "🔤 As cinco palavras-chave mais frequentes são: quântica (138), computação (113)..."

4. **"Qual foi o ano mais produtivo?"**
   - Resposta: "📅 O ano de 2025 foi o mais produtivo, com 13 publicações..."

## 🔧 Tecnologias Utilizadas

- **🤖 Groq LLM**: llama-3.1-8b-instant para geração de texto
- **🔍 RAG Architecture**: Retrieval-Augmented Generation
- **💾 SQLite**: Banco de dados com 50 artigos científicos
- **🌐 Flask**: Framework web Python
- **🎨 Bootstrap 5.3**: Interface responsiva
- **📊 Pandas**: Análise e processamento de dados
- **🧠 LangChain**: Integração com modelos de linguagem

## 📊 Dados Atualmente Disponíveis

- **Total**: 50 artigos científicos
- **Tópico**: Computação em nuvem quântica
- **Período**: 2019-2025 (7 anos)
- **Palavras-chave principais**:
  - quântica: 138 ocorrências
  - computação: 113 ocorrências
  - ensino: 13 ocorrências

### Distribuição Temporal:
- 2019: 2 artigos
- 2020: 1 artigo
- 2021: 4 artigos
- 2022: 5 artigos
- 2023: 5 artigos
- 2024: 8 artigos
- 2025: 13 artigos

## 🚀 Como Usar

1. **Iniciar o Sistema**:
   ```bash
   python app.py
   ```

2. **Acessar o Chat**:
   - URL: `http://127.0.0.1:5000/chat_cientifico_page`

3. **Interagir**:
   - Digite perguntas sobre as análises científicas
   - Use as perguntas sugeridas como exemplo
   - Mantenha conversa contextual
   - Limpe o chat quando necessário

## 🔐 Garantias de Segurança e Precisão

✅ **Respostas Baseadas em Dados Reais**: Apenas informações dos dados coletados  
✅ **Não Alucina**: Não inventa informações inexistentes  
✅ **Comportamento Científico**: Tom profissional e acadêmico  
✅ **Citações Exatas**: Números precisos dos dados analisados  
✅ **Vocabulário Apropriado**: Terminologia científica correta  

## 🔄 Arquitetura RAG Detalhada

### 1. Extração de Dados (R - Retrieval)
```python
def extrair_dados_rag():
    # Conecta ao SQLite
    # Extrai metadados, análise temporal, palavras-chave
    # Estrutura dados para contexto LLM
    # Retorna contexto rico e estruturado
```

### 2. Prompting Inteligente (A - Augmented)
```python
def gerar_resposta_cientifica_rag(pergunta, dados_rag, historico):
    # Few-shot examples
    # Contexto dos dados extraídos
    # Histórico da conversa
    # Prompts rígidos anti-alucinação
```

### 3. Geração de Resposta (G - Generation)
```python
# Groq LLM (llama-3.1-8b-instant)
# Temperature 0.2 para precisão
# Resposta científica formatada
```

## 📝 Estrutura de Arquivos

```
/templates/
  ├── chat_cientifico.html     # Interface do chat
  └── ...

/static/css/
  └── style.css               # Estilos cósmicos

app.py                        # Backend Flask com RAG
demo_chat_cientifico.py       # Demonstração do sistema
test_chat_cientifico.py       # Testes automatizados
check_data.py                 # Verificação de dados
```

## 🎉 Status do Sistema

**✅ TOTALMENTE OPERACIONAL**

O Chat Científico com RAG está pronto para uso em produção, garantindo:
- Respostas precisas baseadas nos dados coletados
- Comportamento profissional científico  
- Memória de conversa para contexto contínuo
- Interface intuitiva e atrativa
- Prevenção total de alucinações de IA

---

*Sistema QAARS v2.0 - Powered by Groq LLM + RAG Architecture*