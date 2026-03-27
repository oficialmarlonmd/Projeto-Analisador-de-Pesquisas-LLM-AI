import sqlite3
import pandas as pd

# Verificar se existem dados
conn = sqlite3.connect('buscas_completas_CQ.db')
df = pd.read_sql_query('SELECT COUNT(*) as total FROM resultados_detalhados_CQ', conn)
conn.close()

total = df.iloc[0]['total']
print(f'📊 Total de artigos na base: {total}')

if total > 0:
    print('✅ Dados disponíveis para o chat científico!')
    print('🚀 O sistema RAG está pronto para funcionar!')
else:
    print('⚠️ Execute uma busca primeiro para gerar dados.')