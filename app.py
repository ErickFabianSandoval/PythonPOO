import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from pymongo import MongoClient
from sklearn.linear_model import LinearRegression
import numpy as np
import base64
from pymongo.server_api import ServerApi

# URI con tu usuario y contraseña
uri = f"mongodb+srv://erickfabian845:kikini1@cluster0.v22gzsc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    # Conexión con API de servidor moderna
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['DataWareHouse_DB']
    dfs = {col: pd.DataFrame(list(db[col].find())) for col in ["museos", "zonas", "visitas"]}
    print(f"✅ Conexión exitosa a MongoDB.")

except Exception as e:
    print("❌ Error al conectar con MongoDB Atlas:")
    print(e)

museos = dfs["museos"]
zonas = dfs["zonas"]
visitas = dfs["visitas"]


# --- PREPROCESAMIENTO ---
visitas["Periodo"] = pd.to_datetime(visitas["Periodo"], errors="coerce")
visitas["Año"] = visitas["Periodo"].dt.year
visitas["Tipo de sitio"] = visitas["Tipo de sitio"].str.strip().str.title()
visitas["Centro de trabajo"] = visitas["Centro de trabajo"].str.strip()
visitas["Número de visitas"] = pd.to_numeric(visitas["Número de visitas"], errors="coerce").fillna(0)

# --- MAPA INTERACTIVO CON MENÚ ---
museos_df = museos.rename(columns={"gmaps_latitud": "latitud", "gmaps_longitud": "longitud"})
museos_df["tipo"] = "Museo"
zonas_df = zonas.copy()
zonas_df["tipo"] = "Zona Arqueológica"
lugares = pd.concat([museos_df, zonas_df], ignore_index=True)

fig_mapa = px.scatter_mapbox(
    lugares, lat="latitud", lon="longitud", color="tipo",
    zoom=4.2, height=600, mapbox_style="carto-positron",
    center={"lat": 24, "lon": -102},
    title="Museos y Zonas Arqueológicas en México"
)
fig_mapa.update_layout(
    title_x=0.5,
    margin={"r":0,"t":50,"l":0,"b":0},
    legend_title="Tipo de Lugar",
    updatemenus=[{
        "buttons": [
            {"label": "Museos y Zonas Arqueológicas", "method": "update", "args": [{"visible": [True]*len(lugares)}, {"title": "Todos"}]},
            {"label": "Museos", "method": "update", "args": [{"visible": lugares["tipo"] == "Museo"}, {"title": "Museos"}]},
            {"label": "Zonas Arqueológicas", "method": "update", "args": [{"visible": lugares["tipo"] == "Zona Arqueológica"}, {"title": "Zonas Arqueológicas"}]},
        ],
        "direction": "down",
        "showactive": True,
        "x": 1.005, "xanchor": "left", "y": 0.85, "yanchor": "top"
    }]
)

# --- TOP 5 MUSEOS POR ESTADO ---
museos["nom_ent"] = museos["nom_ent"].replace("Veracruz de Ignacio de la Llave", "Veracruz")
top_estados_museos = museos["nom_ent"].value_counts().nlargest(5).reset_index()
top_estados_museos.columns = ["Estado", "Cantidad de Museos"]
fig_museos = px.bar(top_estados_museos, x="Cantidad de Museos", y="Estado", orientation="h",
                    color_discrete_sequence=["#6D48E7"],
                    title="Top 5 Estados con Más Museos en México")
fig_museos.update_layout(title_x=0.5, yaxis_title=None)

# --- TOP 5 ZONAS POR ESTADO ---
zonas["nom_ent"] = zonas["nom_ent"].replace({"MÃ©xico": "Edo. de México", "YucatÃ¡n": "Yucatán"})
top_estados_zonas = zonas["nom_ent"].value_counts().nlargest(5).reset_index()
top_estados_zonas.columns = ["Estado", "Cantidad de Zonas"]
fig_zonas = px.bar(top_estados_zonas, x="Cantidad de Zonas", y="Estado", orientation="h",
                   color_discrete_sequence=["#DC5252"], text="Cantidad de Zonas",
                   title="Top 5 Estados con Más Zonas Arqueológicas en México")
fig_zonas.update_traces(textposition="outside")
fig_zonas.update_layout(title_x=0.5, yaxis_title=None)

# --- SERIE TEMPORAL DE SITIOS DISPONIBLES ---
conteo = visitas.groupby(["Año", "Tipo de sitio"])["Centro de trabajo"].nunique().reset_index(name="Cantidad de Sitios")
conteo = conteo[conteo["Tipo de sitio"].isin(["Museo", "Zona Arqueológica"])]
fig_tiempo = px.line(conteo, x="Año", y="Cantidad de Sitios", color="Tipo de sitio",
                     color_discrete_map={"Museo": "#6D48E7", "Zona Arqueológica": "#DC5252"},
                     markers=True,
                     title="Museos y Zonas Arqueológicas Disponibles por Año")
fig_tiempo.update_layout(title_x=0.5, xaxis=dict(dtick=1, range=[1996, 2024]), yaxis_title="Cantidad de Sitios")

# --- TOP 10 ZONAS MÁS VISITADAS (INTERACTIVO POR AÑO) ---
df_zonas = visitas[visitas["Tipo de sitio"] == "Zona Arqueológica"]
anios_z = sorted(df_zonas["Año"].dropna().unique())
fig_zonas_visita = go.Figure()
for i, anio in enumerate(anios_z):
    top = df_zonas[df_zonas["Año"] == anio].groupby("Centro de trabajo")["Número de visitas"].sum().nlargest(10).reset_index()
    fig_zonas_visita.add_trace(go.Bar(x=top["Número de visitas"], y=top["Centro de trabajo"],
        orientation="h", name=str(anio), visible=(i == 0), marker_color="#6D48E7"))
buttons2 = [dict(label=str(anio), method="update",
    args=[{"visible": [i == j for j in range(len(anios_z))]},
          {"title": f"Top 10 Zonas Arqueológicas Más Visitadas en {anio}"}])
    for i, anio in enumerate(anios_z)]
fig_zonas_visita.update_layout(title=f"Top 10 Zonas Arqueológicas Más Visitadas en {anios_z[0]}",
    title_x=0.5, yaxis_title=None, yaxis=dict(autorange="reversed"),
    updatemenus=[dict(buttons=buttons2, direction="down", showactive=True,
                      x=1.05, xanchor="left", y=1, yanchor="top")])

# --- TOP 10 MUSEOS MÁS VISITADOS (INTERACTIVO POR AÑO) ---
df_museos = visitas[visitas["Tipo de sitio"] == "Museo"]
anios_m = sorted(df_museos["Año"].dropna().unique())
fig_museos_visita = go.Figure()
for i, anio in enumerate(anios_m):
    top = df_museos[df_museos["Año"] == anio].groupby("Centro de trabajo")["Número de visitas"].sum().nlargest(10).reset_index()
    fig_museos_visita.add_trace(go.Bar(x=top["Número de visitas"], y=top["Centro de trabajo"],
        orientation="h", name=str(anio), visible=(i == 0), marker_color="#DC5252"))
buttons_m = [dict(label=str(anio), method="update",
    args=[{"visible": [i == j for j in range(len(anios_m))]},
          {"title": f"Top 10 Museos Más Visitados en {anio}"}])
    for i, anio in enumerate(anios_m)]
fig_museos_visita.update_layout(title=f"Top 10 Museos Más Visitados en {anios_m[0]}",
    title_x=0.5, yaxis_title=None, yaxis=dict(autorange="reversed"),
    updatemenus=[dict(buttons=buttons_m, direction="down", showactive=True,
                      x=1.05, xanchor="left", y=1, yanchor="top")])

# --- REGRESIÓN: ZONAS ARQUEOLÓGICAS ---
df_zonas_pred = visitas[visitas["Tipo de sitio"] == "Zona Arqueológica"]
nombres_zonas_all = sorted(df_zonas_pred["Centro de trabajo"].dropna().unique())
rango_zonas = {}
annotations_z = []
fig_pred_zonas = go.Figure()

# Filtrar nombres con datos suficientes para regresión
nombres_zonas = []

for i, nombre in enumerate(nombres_zonas_all):
    df_filtrado = df_zonas_pred[df_zonas_pred["Centro de trabajo"] == nombre]
    visitas_anio = df_filtrado.groupby("Año")["Número de visitas"].sum().reset_index()
    
    x = visitas_anio["Año"].values.reshape(-1, 1)
    y = visitas_anio["Número de visitas"].values
    if len(x) < 2:
        continue  # Saltar si no hay suficientes datos

    model = LinearRegression().fit(x, y)
    next_year = x.max() + 1
    y_pred = model.predict([[next_year]])[0]

    x_range = np.append(x.flatten(), next_year)
    y_fit = model.predict(x_range.reshape(-1, 1))
    rango_zonas[nombre] = (x.min(), next_year)

    # Guardar nombre válido
    nombres_zonas.append(nombre)

    fig_pred_zonas.add_trace(go.Scatter(
        x=visitas_anio["Año"], y=visitas_anio["Número de visitas"],
        mode='lines+markers', name=nombre,
        visible=False, line=dict(color="#6D48E7"), marker=dict(size=8)
    ))
    fig_pred_zonas.add_trace(go.Scatter(
        x=x_range, y=y_fit, mode="lines", name=f"Regresión - {nombre}",
        visible=False, line=dict(dash='dot', color="gray")
    ))
    annotations_z.append(dict(
        x=next_year, y=y_pred,
        text=f"Predicción {next_year}: {int(y_pred):,} visitas",
        showarrow=True, arrowhead=2, ax=-50, ay=-40,
        font=dict(size=12, color="blue"), bgcolor="white",
        bordercolor="blue", borderwidth=1, opacity=0.9, visible=False
    ))

# Si no hay nombres válidos, evitar error
if nombres_zonas:
    # Hacer visible solo la primera
    fig_pred_zonas.data[0].visible = True
    fig_pred_zonas.data[1].visible = True
    annotations_z[0]['visible'] = True

buttons_z = []
for i, nombre in enumerate(nombres_zonas):
    vis = [False] * len(fig_pred_zonas.data)
    vis[2 * i] = vis[2 * i + 1] = True
    annots = [dict(a, visible=(j == i)) for j, a in enumerate(annotations_z)]
    buttons_z.append(dict(
        label=nombre, method="update",
        args=[{"visible": vis},
              {"title": f"Visitantes por año en: {nombre}",
               "xaxis": {"range": rango_zonas[nombre]},
               "yaxis": {"range": [0, None]},
               "annotations": annots}]
    ))

fig_pred_zonas.update_layout(
    title=f"Visitantes por año en: {nombres_zonas[0] if nombres_zonas else 'N/A'}",
    title_x=0.5, xaxis_title="Año", yaxis_title="Número de visitas",
    margin=dict(t=100), xaxis_range=[*rango_zonas[nombres_zonas[0]]] if nombres_zonas else None,
    yaxis_range=[0, None], annotations=[annotations_z[0]] if annotations_z else None,
    updatemenus=[dict(
        buttons=buttons_z, direction="down", showactive=True,
        x=0.5, xanchor="center", y=1.15, yanchor="top"
    )] if nombres_zonas else []
)

# --- REGRESIÓN: MUSEOS ---
# --- REGRESIÓN: MUSEOS ---
df_museos_pred = visitas[visitas["Tipo de sitio"] == "Museo"]
nombres_museos_all = sorted(df_museos_pred["Centro de trabajo"].dropna().unique())
rango_museos = {}
annotations_m = []
fig_pred_museos = go.Figure()

# Filtrar nombres con datos suficientes para regresión
nombres_museos = []

for i, nombre in enumerate(nombres_museos_all):
    df_filtrado = df_museos_pred[df_museos_pred["Centro de trabajo"] == nombre]
    visitas_anio = df_filtrado.groupby("Año")["Número de visitas"].sum().reset_index()
    
    x = visitas_anio["Año"].values.reshape(-1, 1)
    y = visitas_anio["Número de visitas"].values
    if len(x) < 2:
        continue  # Saltar si no hay suficientes datos

    model = LinearRegression().fit(x, y)
    next_year = x.max() + 1
    y_pred = model.predict([[next_year]])[0]

    x_range = np.append(x.flatten(), next_year)
    y_fit = model.predict(x_range.reshape(-1, 1))
    rango_museos[nombre] = (x.min(), next_year)

    # Guardar nombre válido
    nombres_museos.append(nombre)

    fig_pred_museos.add_trace(go.Scatter(
        x=visitas_anio["Año"], y=visitas_anio["Número de visitas"],
        mode='lines+markers', name=nombre,
        visible=False, line=dict(color="#DC5252"), marker=dict(size=8)
    ))
    fig_pred_museos.add_trace(go.Scatter(
        x=x_range, y=y_fit, mode="lines", name=f"Regresión - {nombre}",
        visible=False, line=dict(dash='dot', color="gray")
    ))
    annotations_m.append(dict(
        x=next_year, y=y_pred,
        text=f"Predicción {next_year}: {int(y_pred):,} visitas",
        showarrow=True, arrowhead=2, ax=-50, ay=-40,
        font=dict(size=12, color="red"), bgcolor="white",
        bordercolor="red", borderwidth=1, opacity=0.9, visible=False
    ))

# Si no hay nombres válidos, evitar error
if nombres_museos:
    # Hacer visible solo la primera
    fig_pred_museos.data[0].visible = True
    fig_pred_museos.data[1].visible = True
    annotations_m[0]['visible'] = True

buttons_m = []
for i, nombre in enumerate(nombres_museos):
    vis = [False] * len(fig_pred_museos.data)
    vis[2 * i] = vis[2 * i + 1] = True
    annots = [dict(a, visible=(j == i)) for j, a in enumerate(annotations_m)]
    buttons_m.append(dict(
        label=nombre, method="update",
        args=[{"visible": vis},
              {"title": f"Visitantes por año en: {nombre}",
               "xaxis": {"range": rango_museos[nombre]},
               "yaxis": {"range": [0, None]},
               "annotations": annots}]
    ))

fig_pred_museos.update_layout(
    title=f"Visitantes por año en: {nombres_museos[0] if nombres_museos else 'N/A'}",
    title_x=0.5, xaxis_title="Año", yaxis_title="Número de visitas",
    margin=dict(t=100), xaxis_range=[*rango_museos[nombres_museos[0]]] if nombres_museos else None,
    yaxis_range=[0, None], annotations=[annotations_m[0]] if annotations_m else None,
    updatemenus=[dict(
        buttons=buttons_m, direction="down", showactive=True,
        x=0.5, xanchor="center", y=1.15, yanchor="top"
    )] if nombres_museos else []
)

# Cargar imágenes como base64
with open("inegi.png", "rb") as f:
    encoded_inegi_logo = base64.b64encode(f.read()).decode("utf-8")
inegi_logo_src = f"data:image/png;base64,{encoded_inegi_logo}"

with open("cultura.png", "rb") as f:
    encoded_cultura_logo = base64.b64encode(f.read()).decode("utf-8")
cultura_logo_src = f"data:image/png;base64,{encoded_cultura_logo}"

app = dash.Dash(__name__)
app.title = "Dashboard Museos y Zonas Arqueológicas"

app.layout = html.Div([
    # Encabezado con logos y título
    html.Div([
        html.Img(src=inegi_logo_src, style={
            "height": "140px",
            "width": "auto",
            "objectFit": "contain"
        }),
        html.H1("Museos y Zonas Arqueológicas de México", style={
            "flex": "1",
            "textAlign": "center",
            "color": "#2c3e50",
            "fontFamily": "'Montserrat', sans-serif",
            "fontWeight": "700",
            "fontSize": "2.5rem",
            "margin": "0"
        }),
        html.Img(src=cultura_logo_src, style={
            "height": "200px",
            "width": "auto",
            "objectFit": "contain"
        }),
    ], style={
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "padding": "10px 40px",
        "borderBottom": "3px solid #6D48E7",
        "backgroundColor": "#f9f9fc",
        "boxShadow": "0 3px 10px rgba(0,0,0,0.05)"
    }),

    # HIGHLIGHTS
    html.Div([
        html.Div([
            html.H4("Total Museos", style={"color": "#6D48E7", "marginBottom": "0"}),
            html.P(f"{len(museos):,}", style={"fontSize": "28px", "fontWeight": "bold", "marginTop": "5px"})
        ], style={
            "width": "22%", "padding": "15px", "backgroundColor": "#f9f9f9",
            "border": "2px solid #6D48E7", "borderRadius": "10px",
            "textAlign": "center", "boxShadow": "2px 2px 8px rgba(0,0,0,0.05)"
        }),

        html.Div([
            html.H4("Total Zonas", style={"color": "#800000", "marginBottom": "0"}),
            html.P(f"{len(zonas):,}", style={"fontSize": "28px", "fontWeight": "bold", "marginTop": "5px"})
        ], style={
            "width": "22%", "padding": "15px", "backgroundColor": "#fdf7f5",
            "border": "2px solid #800000", "borderRadius": "10px",
            "textAlign": "center", "boxShadow": "2px 2px 8px rgba(0,0,0,0.05)"
        }),

        html.Div([
            html.H4("Total Registros de Visitas", style={"color": "#444", "marginBottom": "0"}),
            html.P(f"{len(visitas):,}", style={"fontSize": "28px", "fontWeight": "bold", "marginTop": "5px"})
        ], style={
            "width": "22%", "padding": "15px", "backgroundColor": "#f3f3f3",
            "border": "2px solid #999", "borderRadius": "10px",
            "textAlign": "center", "boxShadow": "2px 2px 8px rgba(0,0,0,0.05)"
        }),

        html.Div([
            html.H4("Último Año Registrado", style={"color": "#CFAF5F", "marginBottom": "0"}),
            html.P(f"{int(visitas['Año'].max())}", style={"fontSize": "28px", "fontWeight": "bold", "marginTop": "5px"})
        ], style={
            "width": "22%", "padding": "15px", "backgroundColor": "#fffdf5",
            "border": "2px solid #CFAF5F", "borderRadius": "10px",
            "textAlign": "center", "boxShadow": "2px 2px 8px rgba(0,0,0,0.05)"
        }),
    ], style={
        "display": "flex", "justifyContent": "space-around", "margin": "30px 0",
        "fontFamily": "Segoe UI, Roboto, sans-serif"
    }),

    # GRÁFICOS
    dcc.Graph(id="mapa", figure=fig_mapa),

    html.Div([
        html.Div(dcc.Graph(figure=fig_museos), style={"width": "49%", "display": "inline-block", "verticalAlign": "top"}),
        html.Div(dcc.Graph(figure=fig_zonas), style={"width": "49%", "display": "inline-block", "verticalAlign": "top", "marginLeft": "2%"}),
    ], style={"width": "100%", "display": "flex", "justifyContent": "space-between"}),

    dcc.Graph(figure=fig_tiempo),

    html.Div([
        html.Div(dcc.Graph(figure=fig_zonas_visita), style={"width": "49%", "display": "inline-block", "verticalAlign": "top"}),
        html.Div(dcc.Graph(figure=fig_museos_visita), style={"width": "49%", "display": "inline-block", "verticalAlign": "top", "marginLeft": "2%"}),
    ], style={"width": "100%", "display": "flex", "justifyContent": "space-between"}),

    dcc.Graph(figure=fig_pred_zonas),
    dcc.Graph(figure=fig_pred_museos),

    html.Hr(),

    # INFORMACIÓN Y DROPDOWNS
    html.H3("Información de contacto del sitio seleccionado",
            style={"textAlign": "center", "color": "#333", "fontFamily": "Segoe UI, Roboto, sans-serif"}),

    html.Div([
        html.Label("Tipo de sitio:", style={"fontWeight": "bold", "color": "#444"}),
        dcc.Dropdown(
            id="tipo-dropdown",
            options=[
                {"label": "Museo", "value": "Museo"},
                {"label": "Zona Arqueológica", "value": "Zona Arqueológica"}
            ],
            value="Museo",
            clearable=False,
            style={"width": "300px", "marginBottom": "15px"}
        ),
    ], style={"margin": "10px"}),

    html.Div([
        html.Label("Nombre del sitio:", style={"fontWeight": "bold", "color": "#444"}),
        dcc.Dropdown(
            id="sitio-dropdown",
            options=[],  # Dinámico
            clearable=False,
            style={"width": "500px"}
        ),
    ], style={"margin": "10px"}),

    html.Div(id="info-sitio", style={
        "margin": "10px 20px", "whiteSpace": "pre-line", "fontSize": "16px",
        "backgroundColor": "#f5f5f5", "padding": "15px", "borderRadius": "8px",
        "border": "1px solid #ccc", "fontFamily": "Segoe UI, Roboto, sans-serif"
    })

], style={"backgroundColor": "#f1f4f9", "padding": "20px", "fontFamily": "Segoe UI, Roboto, sans-serif"})


# --- CALLBACKS ---
@app.callback(
    Output("sitio-dropdown", "options"),
    Output("sitio-dropdown", "value"),
    Input("tipo-dropdown", "value")
)
def actualizar_sitios(tipo):
    if tipo == "Museo":
        nombres = sorted(museos["museo_nombre"].dropna().unique())
    else:
        nombres = sorted(zonas["zona_arqueologica_nombre"].dropna().unique())
    opciones = [{"label": nombre, "value": nombre} for nombre in nombres]
    valor = nombres[0] if nombres else None
    return opciones, valor

@app.callback(
    Output("info-sitio", "children"),
    Input("tipo-dropdown", "value"),
    Input("sitio-dropdown", "value")
)
def mostrar_info(tipo, nombre):
    if not nombre:
        return "Selecciona un sitio válido."

    if tipo == "Museo":
        fila = museos[museos["museo_nombre"] == nombre]
        if fila.empty:
            return "Museo no encontrado."
        fila = fila.iloc[0]
        telefono = fila.get("museo_telefono1", "No disponible")
    else:
        fila = zonas[zonas["zona_arqueologica_nombre"] == nombre]
        if fila.empty:
            return "Zona no encontrada."
        fila = fila.iloc[0]
        telefono = fila.get("zona_arqueologica_telefono1", "No disponible")

    web = fila.get("pagina_web", "No disponible")
    email = fila.get("email", "No disponible")

    info_texto = (
        f"📞 Teléfono: {telefono}\n"
        f"🌐 Página web: {web}\n"
        f"✉️ Correo electrónico: {email}"
    )
    return info_texto

server = app.server  # <- Esto sigue siendo necesario para Render

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
