import dash
from dash import html, dcc, Input, Output
import pandas as pd
import plotly.express as px
import base64
import datetime
import random
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# URI con tu usuario y contraseña
uri = f"mongodb+srv://erickfabian845:kikini1@cluster0.v22gzsc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    # Conexión con API de servidor moderna
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["autosDB"]
    collection = db["precio_autos"]

    # Probar si hay conexión y documentos
    count = collection.count_documents({})
    print(f"✅ Conexión exitosa a MongoDB. Documentos en colección: {count}")

except Exception as e:
    print("❌ Error al conectar con MongoDB Atlas:")
    print(e)

# Función para consultar datos con filtros
def query_data(filters=None):
    if filters:
        query = {}
        if 'Manufacturer' in filters and filters['Manufacturer']:
            query['Manufacturer'] = {'$in': filters['Manufacturer']}
        if 'Model' in filters and filters['Model']:
            query['Model'] = {'$in': filters['Model']}
        if 'Category' in filters and filters['Category']:
            query['Category'] = {'$in': filters['Category']}
        if 'Fuel type' in filters and filters['Fuel type']:
            query['Fuel type'] = {'$in': filters['Fuel type']}
        if 'Cylinders' in filters and filters['Cylinders']:
            query['Cylinders'] = {'$in': [int(c) if isinstance(c, str) and c.replace('.','',1).isdigit() else c for c in filters['Cylinders']]}
        
        data = list(collection.find(query))
    else:
        data = list(collection.find())
    
    df = pd.DataFrame(data)
    
    # Procesamiento de datos
    if not df.empty:
        df_filtered = df[[ 
            'Model', 'Category', 'Price', 'Production cost US',
            'Import tariff (%)', 'Import tariff amount',
            'Total cost from Mexico (with tariff)', 'Manufacturer',
            'Fuel type', 'Cylinders', 'Gear box type'
        ]].copy()

        numeric_cols = ['Price', 'Production cost US', 'Import tariff (%)',
                      'Import tariff amount', 'Total cost from Mexico (with tariff)']
        for col in numeric_cols:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').round(2)
        
        # Simular columna de fecha para línea del tiempo
        start_date = datetime.datetime(2022, 1, 1)
        df_filtered['Date'] = [start_date + datetime.timedelta(days=random.randint(0, 1200)) for _ in range(len(df_filtered))]
        
        return df_filtered
    else:
        return pd.DataFrame()

# Función para generar gráficas normales
def generate_chart(df, dimension, title):
    if df.empty or dimension not in df.columns:
        return px.bar(title=f"No data available for {title}")
    
    grouped = df.groupby(dimension).agg({
        'Total cost from Mexico (with tariff)': 'mean',
        'Production cost US': 'mean'
    }).reset_index()
    grouped = grouped.rename(columns={
        'Total cost from Mexico (with tariff)': 'Mexico + Tariff',
        'Production cost US': 'USA'
    })
    melted = pd.melt(grouped, id_vars=dimension,
                    value_vars=['Mexico + Tariff', 'USA'],
                    var_name='Production Origin', value_name='Average Cost')
    fig = px.bar(melted, x=dimension, y='Average Cost', color='Production Origin', barmode='group',
                title=title, color_discrete_map={'Mexico + Tariff': '#60809c', 'USA': '#1A2A3A'})
    fig.update_layout(xaxis_tickangle=-90)
    return fig

# Función especial para gráfica de cilindros
def generate_cylinders_chart(df):
    if df.empty or 'Cylinders' not in df.columns:
        return px.bar(title="No data available for Cylinders")
    
    # Convertir cilindros a enteros y luego a strings para mostrar como categorías
    df = df.copy()
    df['Cylinders'] = df['Cylinders'].astype(float).astype(int).astype(str)
    
    # Filtrar solo cilindros con datos
    valid_cylinders = df['Cylinders'].unique()
    
    grouped = df.groupby('Cylinders').agg({
        'Total cost from Mexico (with tariff)': 'mean',
        'Production cost US': 'mean'
    }).reset_index()
    grouped = grouped.rename(columns={
        'Total cost from Mexico (with tariff)': 'Mexico + Tariff',
        'Production cost US': 'USA'
    })
    melted = pd.melt(grouped, id_vars='Cylinders',
                    value_vars=['Mexico + Tariff', 'USA'],
                    var_name='Production Origin', value_name='Average Cost')
    
    fig = px.bar(melted, x='Cylinders', y='Average Cost', color='Production Origin', 
                 barmode='group', category_orders={"Cylinders": sorted(valid_cylinders, key=lambda x: int(x))},
                 title='Cost by Cylinders', 
                 color_discrete_map={'Mexico + Tariff': '#60809c', 'USA': '#1A2A3A'})
    
    fig.update_layout(
        xaxis={'type': 'category', 'title': 'Number of Cylinders'},
        yaxis={'title': 'Average Cost'},
        xaxis_tickangle=0
    )
    
    return fig

# Línea del tiempo
def generate_timeline(df):
    if df.empty or 'Date' not in df.columns:
        return px.line(title="No timeline data available")
    
    timeline = df.copy()
    timeline['Date'] = pd.to_datetime(timeline['Date'])
    timeline = timeline.sort_values('Date')
    timeline['Month'] = timeline['Date'].dt.to_period('M').astype(str)
    grouped = timeline.groupby('Month').agg({'Total cost from Mexico (with tariff)': 'mean'}).reset_index()
    fig = px.line(grouped, x='Month', y='Total cost from Mexico (with tariff)', title='Timeline: Average Cost from Mexico')
    fig.update_layout(xaxis_title='X Axis', yaxis_title='Y Axis')
    return fig

# Cargar logos
with open("logo.png", "rb") as f:
    encoded_logo = base64.b64encode(f.read()).decode("utf-8")
logo_src = f"data:image/png;base64,{encoded_logo}"

with open("stellar.png", "rb") as f:
    encoded_stellar_logo = base64.b64encode(f.read()).decode("utf-8")
stellar_logo_src = f"data:image/png;base64,{encoded_stellar_logo}"

# Layout
app = dash.Dash(__name__)
app.title = "Dashboard Profesional Completo"

app.layout = html.Div(style={"fontFamily": "Segoe UI", "backgroundColor": "#1A2A3A", "padding": "20px"}, children=[
    html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "20px"}, children=[
        html.Img(src=logo_src, style={"height": "200px"}),

        html.Div(style={"textAlign": "center", "flexGrow": "1"}, children=[
            html.H1("MX+tariff vs USA Strategic Analysis", style={"color": "white", "marginTop": "5px", 'fontSize': '40px'})
        ]),

        html.Img(src=stellar_logo_src, style={"height": "60px"})
    ]),

    html.Div(style={"display": "flex", "justifyContent": "center", "marginBottom": "20px"}, children=[
        html.Div(style={"width": "50%"}, children=[
            html.Label("Manufacturer", style={'textAlign': 'center', 'color': 'white', 'fontWeight': 'bold'}), 
            dcc.Dropdown(
                id='manufacturer-filter', 
                options=[],  # Se llenará dinámicamente
                multi=True,
                placeholder="Select Manufacturer(s)"
            )
        ])
    ]),

    html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "20px"}, children=[
        html.Div(style={"flex": 1}, children=[
            html.Label("Model", style={'textAlign': 'center', 'color': 'white', 'fontWeight': 'bold'}), 
            dcc.Dropdown(
                id='model-filter', 
                options=[],  # Se llenará dinámicamente
                multi=True,
                placeholder="Select Model(s)"
            )
        ]),
        html.Div(style={"flex": 1}, children=[
            html.Label("Category", style={'textAlign': 'center', 'color': 'white', 'fontWeight': 'bold'}), 
            dcc.Dropdown(
                id='category-filter', 
                options=[],  # Se llenará dinámicamente
                multi=True,
                placeholder="Select Category(s)"
            )
        ]),
        html.Div(style={"flex": 1}, children=[
            html.Label("Fuel Type", style={'textAlign': 'center', 'color': 'white', 'fontWeight': 'bold'}), 
            dcc.Dropdown(
                id='fuel-filter', 
                options=[],  # Se llenará dinámicamente
                multi=True,
                placeholder="Select Fuel Type(s)"
            )
        ]),
        html.Div(style={"flex": 1}, children=[
            html.Label("Cylinders", style={'textAlign': 'center', 'color': 'white', 'fontWeight': 'bold'}), 
            dcc.Dropdown(
                id='cylinders-filter', 
                options=[],  # Se llenará dinámicamente
                multi=True,
                placeholder="Select Cylinders"
            )
        ])
    ]),

    html.Div(id='kpi-cards', style={"display": "flex", "gap": "20px", "marginBottom": "30px"}),

    html.Div(style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-between", "gap": "20px"}, children=[
        html.Div(style={"width": "48%"}, children=[dcc.Graph(id='manufacturer-chart')]),
        html.Div(style={"width": "48%"}, children=[dcc.Graph(id='model-chart')]),
        html.Div(style={"width": "48%"}, children=[dcc.Graph(id='category-chart')]),
        html.Div(style={"width": "48%"}, children=[dcc.Graph(id='fuel-chart')]),
        html.Div(style={"width": "48%"}, children=[dcc.Graph(id='cylinders-chart')]),
        html.Div(style={"width": "48%"}, children=[dcc.Graph(id='gear-chart')]),
        html.Div(style={"width": "100%"}, children=[dcc.Graph(id='timeline-chart')])
    ]),

    html.H3("Tabla de Datos Filtrados", style={"marginTop": "30px", "color": "white"}),
    dcc.Graph(id='table')
])

# Callback para actualizar opciones de dropdowns
@app.callback(
    [Output('manufacturer-filter', 'options'),
     Output('model-filter', 'options'),
     Output('category-filter', 'options'),
     Output('fuel-filter', 'options'),
     Output('cylinders-filter', 'options')],
    [Input('manufacturer-filter', 'value'),
     Input('model-filter', 'value'),
     Input('category-filter', 'value'),
     Input('fuel-filter', 'value'),
     Input('cylinders-filter', 'value')]
)
def update_dropdown_options(manufacturers, models, categories, fuels, cylinders):
    # Construir filtros para la consulta
    filters = {}
    if manufacturers:
        filters['Manufacturer'] = manufacturers
    if models:
        filters['Model'] = models
    if categories:
        filters['Category'] = categories
    if fuels:
        filters['Fuel type'] = fuels
    if cylinders:
        filters['Cylinders'] = cylinders
    
    # Consultar datos con los filtros actuales
    df = query_data(filters)
    
    # Obtener valores únicos para cada dropdown
    manufacturer_options = [{'label': m, 'value': m} for m in sorted(df['Manufacturer'].dropna().unique())] if not df.empty else []
    model_options = [{'label': m, 'value': m} for m in sorted(df['Model'].dropna().unique())] if not df.empty else []
    category_options = [{'label': c, 'value': c} for c in sorted(df['Category'].dropna().unique())] if not df.empty else []
    fuel_options = [{'label': f, 'value': f} for f in sorted(df['Fuel type'].dropna().unique())] if not df.empty else []
    
    # Opciones especiales para cilindros (mostrar como enteros)
    if not df.empty and 'Cylinders' in df.columns:
        cylinders_options = [{'label': str(int(float(c))), 'value': str(int(float(c)))} 
                            for c in sorted(df['Cylinders'].dropna().unique())]
    else:
        cylinders_options = []
    
    return (
        manufacturer_options,
        model_options,
        category_options,
        fuel_options,
        cylinders_options
    )

# Callback principal para actualizar todo el dashboard
@app.callback(
    [Output('kpi-cards', 'children'),
     Output('manufacturer-chart', 'figure'),
     Output('model-chart', 'figure'),
     Output('category-chart', 'figure'),
     Output('fuel-chart', 'figure'),
     Output('cylinders-chart', 'figure'),
     Output('gear-chart', 'figure'),
     Output('timeline-chart', 'figure'),
     Output('table', 'figure')],
    [Input('manufacturer-filter', 'value'),
     Input('model-filter', 'value'),
     Input('category-filter', 'value'),
     Input('fuel-filter', 'value'),
     Input('cylinders-filter', 'value')]
)
def update_dashboard(manufacturers, models, categories, fuels, cylinders):
    # Construir filtros para la consulta
    filters = {}
    if manufacturers:
        filters['Manufacturer'] = manufacturers
    if models:
        filters['Model'] = models
    if categories:
        filters['Category'] = categories
    if fuels:
        filters['Fuel type'] = fuels
    if cylinders:
        filters['Cylinders'] = [int(c) if isinstance(c, str) and c.replace('.','',1).isdigit() else c for c in cylinders]
    
    # Consultar datos con los filtros actuales
    df = query_data(filters)
    
    # Calcular KPIs
    if not df.empty:
        avg_mexico = df['Total cost from Mexico (with tariff)'].mean()
        avg_usa = df['Production cost US'].mean()
        diff = avg_mexico - avg_usa
        models_count = df['Model'].nunique()
    else:
        avg_mexico = avg_usa = diff = models_count = 0

    kpis = [
        html.Div(style={"flex": 1, "padding": "15px", "backgroundColor": "#EAF4FF", "borderRadius": "10px", "textAlign": "center", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[
            html.H4("Average Cost Mexico"), html.H2(f"${avg_mexico:,.2f}" if not pd.isna(avg_mexico) else "-")
        ]),
        html.Div(style={"flex": 1, "padding": "15px", "backgroundColor": "#EAF4FF", "borderRadius": "10px", "textAlign": "center", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[
            html.H4("Average Cost USA"), html.H2(f"${avg_usa:,.2f}" if not pd.isna(avg_usa) else "-")
        ]),
        html.Div(style={"flex": 1, "padding": "15px", "backgroundColor": "#EAF4FF", "borderRadius": "10px", "textAlign": "center", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[
            html.H4("Difference"), html.H2(f"${diff:,.2f}" if not pd.isna(diff) else "-")
        ]),
        html.Div(style={"flex": 1, "padding": "15px", "backgroundColor": "#EAF4FF", "borderRadius": "10px", "textAlign": "center", "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}, children=[
            html.H4("Unique Models"), html.H2(str(models_count))
        ])
    ]

    # Generar gráficas
    manufacturer_fig = generate_chart(df, 'Manufacturer', 'Cost by Manufacturer')
    model_fig = generate_chart(df, 'Model', 'Cost by Model')
    category_fig = generate_chart(df, 'Category', 'Cost by Category')
    fuel_fig = generate_chart(df, 'Fuel type', 'Cost by Fuel type')
    cylinders_fig = generate_cylinders_chart(df)  # Usamos la función especial para cilindros
    gear_fig = generate_chart(df, 'Gear box type', 'Cost by Gear box type')
    timeline_fig = generate_timeline(df)

    # Generar tabla
    table_fig = {
        'data': [{
            'type': 'table',
            'header': {'values': list(df.columns), 'fill': {'color': '#1A2A3A'}, 'font': {'color': 'white'}},
            'cells': {'values': [df[col] for col in df.columns], 'fill': {'color': '#EAF4FF'}}
        }],
        'layout': {'margin': {'t': 10}}
    } if not df.empty else {
        'data': [{
            'type': 'table',
            'header': {'values': ['No data available'], 'fill': {'color': '#1A2A3A'}, 'font': {'color': 'white'}},
            'cells': {'values': [[]], 'fill': {'color': '#EAF4FF'}}
        }],
        'layout': {'margin': {'t': 10}}
    }

    return (
        kpis,
        manufacturer_fig,
        model_fig,
        category_fig,
        fuel_fig,
        cylinders_fig,
        gear_fig,
        timeline_fig,
        table_fig
    )

server = app.server  # <- Esto sigue siendo necesario para Render

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
