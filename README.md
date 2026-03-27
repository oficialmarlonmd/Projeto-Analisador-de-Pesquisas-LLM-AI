# 📖 Sistema de Storytelling com Dados

Sistema avançado de web scraping com narrativa inteligente baseado nos **6 princípios fundamentais do Storytelling com Dados**.

## 🎯 Funcionalidades Implementadas

### 1. **Web Scraping Inteligente**
- ✅ Scraping automatizado do Google Scholar
- ✅ Termos em português e inglês para maior cobertura
- ✅ Anti-detecção avançada (User-Agent, headless mode)
- ✅ Retry logic e tratamento de erros
- ✅ Coleta de 40+ artigos científicos sobre criptografia pós-quântica

### 2. **Storytelling com Dados**
Implementa os **6 princípios fundamentais**:

#### 📊 **Lição 1: Entender o Contexto**
- **Público-alvo**: Pesquisadores e tomadores de decisão
- **Ação desejada**: Identificar tendências e oportunidades
- **Comunicação**: Dashboard interativo com narrativa sequencial

#### 🎨 **Lição 2: Apresentação Visual Adequada**
- **Gráfico Temporal** (Linha): Evolução das publicações
- **Distribuição de Tópicos** (Barras horizontais): Concentração temática
- **Palavras-chave** (Barras horizontais): Linguagem da pesquisa  
- **Análise de Sentimento** (Barras horizontais): Perspectivas identificadas

#### ✨ **Lição 3: Eliminar Saturação**
- Design minimalista sem elementos desnecessários
- Espaço branco estratégico
- Remoção de grades e bordas excessivas

#### 🎯 **Lição 4: Focalizar Atenção**
- **Cor principal**: #FF6B35 (laranja) para destaques
- **Cor contexto**: #666666 (cinza) para elementos secundários
- Contraste alto para melhor legibilidade

#### 🎨 **Lição 5: Design Acessível**
- Rótulos diretos nos gráficos
- Tipografia clara e hierarquizada
- Cores considerando daltonismo

#### 📚 **Lição 6: Estrutura Narrativa**
- **Início**: Contexto e panorama temporal
- **Meio**: Evidências e insights dos dados
- **Fim**: Conclusões e recomendações estratégicas

## 🏗️ Arquitetura do Sistema

```
📁 Sistema de Storytelling
├── 🐍 app.py                    # Flask app principal
├── 🕷️ selenium_simples.py       # Web scraping melhorado
├── 📖 storytelling.py           # Motor de storytelling
├── 📁 templates/
│   ├── 🏠 index.html           # Página inicial
│   ├── 📊 resultados.html      # Análises detalhadas  
│   └── 📚 storytelling.html    # Narrativa interativa
├── 📁 static/
│   ├── 🎨 css/style.css        # Estilos
│   └── 📊 js/                  # JavaScript interativo
└── 🗄️ buscas_completas_CQ.db   # Banco SQLite
```

## 🚀 Como Usar

### 1. **Realizar Busca**
```bash
# Iniciar servidor
python app.py

# Acessar: http://localhost:5000
# Configurar tópicos, período e quantidade mínima
# Executar busca automatizada
```

### 2. **Visualizar Storytelling**
```bash
# Após busca concluída, acessar:
http://localhost:5000/storytelling

# Ou através do botão na página inicial:
"📖 Storytelling com Dados"
```

### 3. **Navegação Narrativa**
- **Progresso visual** com barra de avanço
- **Seções sequenciais**: Introdução → Desenvolvimento → Conclusão  
- **Gráficos contextualizados** para cada insight
- **Recomendações estratégicas** baseadas nos dados

## 📈 Exemplo de Narrativa Gerada

```
📖 PANORAMA DA PESQUISA EM COMPUTAÇÃO QUÂNTICA (2020-2025)

🎯 INSIGHT PRINCIPAL:
"Crescimento de 6 publicações no período analisado"

📊 DOMINÂNCIA TEMÁTICA:
"'criptografia pós-quântica' representa 100.0% da produção científica"

🔍 LINGUAGEM DA PESQUISA:  
"'criptografia' é o termo mais recorrente"

🎯 PERSPECTIVAS:
"Cenário equilibrado (75.0%): Abordagem técnica e objetiva"

📋 RECOMENDAÇÕES:
• Área em expansão: Aumentar investimentos e colaborações
• Concentração temática: Considerar diversificação de pesquisa
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: Flask, SQLite, Pandas
- **Web Scraping**: Selenium, Chrome WebDriver
- **Visualização**: Chart.js, HTML5 Canvas
- **Análise**: NLTK, scikit-learn
- **Frontend**: Bootstrap, JavaScript ES6

## 🎨 Design Principles Aplicados

### Cores Estratégicas
- **#FF6B35**: Destaque principal (dados importantes)
- **#666666**: Contexto (eixos, labels secundários)  
- **#28a745, #dc3545**: Sentimento positivo/negativo

### Tipografia Hierarquizada
- **24px Bold**: Títulos principais
- **18px Normal**: Subtítulos
- **16px Bold + Cor**: Insights destacados
- **14px Normal**: Texto corpo

### Layout Responsivo
- Grid adaptativo para diferentes telas
- Animações suaves de transição
- Progressive disclosure das informações

## 📊 Análises Disponíveis

### 1. **Análise Temporal**
- Evolução das publicações por ano
- Identificação de tendências de crescimento/declínio
- Detecção de anos de pico de produção

### 2. **Análise Temática**
- Distribuição de tópicos de pesquisa
- Identificação de áreas dominantes
- Recomendações de diversificação

### 3. **Análise Linguística**  
- Palavras-chave mais frequentes
- Termos emergentes na área
- Densidade semântica dos textos

### 4. **Análise de Sentimento**
- Classificação positivo/negativo/neutro
- Score de intensidade emocional
- Interpretação do cenário geral

## 🔄 Fluxo de Dados

```
📥 Coleta (Google Scholar)
    ↓
🧹 Limpeza e Estruturação  
    ↓
🧠 Análise e Insights
    ↓
📖 Geração de Narrativa
    ↓  
🎨 Visualização Interativa
```

## 🎯 Próximas Melhorias

- [ ] Múltiplas fontes de dados (PubMed, IEEE, etc.)
- [ ] Análise de redes de citação
- [ ] Exportação de relatórios em PDF
- [ ] Dashboard em tempo real
- [ ] Machine Learning para insights avançados

---

## 📞 Como Contribuir

Este sistema implementa state-of-the-art em storytelling com dados científicos. Para contribuições:

1. Fork o projeto
2. Implemente melhorias seguindo os 6 princípios
3. Teste com dados reais
4. Submeta pull request

**Mantenha sempre o foco na clareza, redução de carga cognitiva e comunicação de insights acionáveis!** 🚀