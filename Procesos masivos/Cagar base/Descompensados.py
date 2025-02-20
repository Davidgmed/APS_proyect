import pandas as pd
import pyodbc

# Configuración de conexión a SQL Server
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=DESKTOP-6GJHETA\\SQLEXPRESS01;"
    "Database=el_bosque;"
    "Trusted_Connection=yes;"
)

# 1. Obtener datos de la tabla hta
query = "SELECT * FROM dbo.hta"
df = pd.read_sql(query, pyodbc.connect(conn_str))

# 2. Filtrar filas (equivalentes a pasos en Power Query)
# Filas filtradas2: Eliminar nulos y PAD=0
df = df[(df['PAS'].notnull()) &
        (df['PAD'].notnull()) &
        (df['PAD'] != 0)]

# Filas filtradas3: Eliminar alertas nulas
df = df[df['Alerta'].notnull()]

# 3. Agrupar y agregar (equivalente a Filas agrupadas)
grouped = df.groupby('LlaveGES2', as_index=False).agg({
    'PAS': 'max',
    'PAD': 'max',
    'Alerta': 'max',
    'Centro': 'max',
    'Sector': 'max',
    'RUT': 'max'
})

# Resultado final
print(grouped)