# import dash
# from dash import html, Output, Input
# import dash_leaflet as dl
# import dash_core_components as dcc

# # Initialize the Dash app
# app = dash.Dash(__name__)

# # Approximate coordinates of electric grid stations
# stations = [
#     {"name": "Čechy Střed", "coords": [50.117, 14.400]},
#     {"name": "Hradec", "coords": [50.210, 15.831]},
#     {"name": "Chodov", "coords": [49.939, 15.535]},
#     {"name": "Tábor", "coords": [49.414, 14.658]},
#     {"name": "Dasný", "coords": [48.980, 14.423]},
#     {"name": "Slavětice", "coords": [49.123, 15.837]},
#     {"name": "Sokolnice", "coords": [49.111, 16.738]},
#     {"name": "Otrokovice", "coords": [49.209, 17.528]},
#     {"name": "Prosenice", "coords": [49.469, 17.462]},
#     {"name": "Nošovice", "coords": [49.660, 18.460]},
#     {"name": "Krasíkov", "coords": [49.966, 16.016]},

# ]

# # Map center
# map_center = [49.8175, 15.4730]

# # App layout
# app.layout = html.Div([
#     html.H1("Electricity Grid connection", style={"textAlign": "center"}),

#     # Interval that ticks every 1 second
#     dcc.Interval(id="interval", interval=1000, n_intervals=0, max_intervals=len(stations)),

#     # Store intermediate state (current polyline path)
#     dcc.Store(id="polyline-coords", data=[]),

#     # Map
#     dl.Map(id="map", center=map_center, zoom=7, children=[
#         dl.TileLayer(),
#         dl.LayerGroup(id="lines"),  # Dynamic polyline layer
#         dl.LayerGroup([  # Static station markers
#             dl.Marker(position=station["coords"], children=[
#                 dl.Tooltip(station["name"]),
#                 dl.Popup(html.Div([
#                     html.H4(station["name"]),
#                     html.P(f"Coordinates: {station['coords'][0]}, {station['coords'][1]}")
#                 ]))
#             ]) for station in stations
#         ])
#     ], style={'width': '100%', 'height': '80vh'}),
# ])


# # Callback to update the polyline animation
# @app.callback(
#     Output("polyline-coords", "data"),
#     Input("interval", "n_intervals"),
#     prevent_initial_call=True
# )
# def update_path(n):
#     if n > 0 and n <= len(stations):
#         return [station["coords"] for station in stations[:n]]
#     return dash.no_update


# # Callback to draw updated polyline on map
# @app.callback(
#     Output("lines", "children"),
#     Input("polyline-coords", "data")
# )
# def draw_polyline(data):
#     if data:
#         return [dl.Polyline(positions=data, color="red", weight=4)]
#     return []

# # Run the Dash app
# if __name__ == '__main__':
#     app.run(debug=True)

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import random 
from contextlib import closing
import time
import socket


import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd

# Initialize the Dash app
app = dash.Dash(__name__)

# Power grid station data
grid_stations = [
    # Northern Region
    {"name": "Bezděčín", "lat": 50.7, "lon": 14.2, "type": "400kV", "region": "Northern"},
    {"name": "Babylon", "lat": 50.8, "lon": 15.0, "type": "400kV", "region": "Northern"},
    {"name": "Chotějovice", "lat": 50.4, "lon": 14.0, "type": "400kV", "region": "Northern"},
    {"name": "Vernéřov", "lat": 50.4, "lon": 12.6, "type": "400kV", "region": "Northern"},
    {"name": "Vítkov", "lat": 50.1, "lon": 12.4, "type": "400kV", "region": "Northern"},
    
    # Western Region
    {"name": "Chrást", "lat": 49.9, "lon": 13.3, "type": "400kV", "region": "Western"},
    {"name": "Prestice", "lat": 49.6, "lon": 13.3, "type": "400kV", "region": "Western"},
    {"name": "Výškov", "lat": 50.0, "lon": 13.7, "type": "220kV", "region": "Western"},
    {"name": "Hradec (West)", "lat": 50.2, "lon": 13.8, "type": "220kV", "region": "Western"},
    
    # Central Region
    {"name": "Mělník", "lat": 50.35, "lon": 14.47, "type": "400kV", "region": "Central"},
    {"name": "Míru", "lat": 50.1, "lon": 14.4, "type": "220kV", "region": "Central"},
    {"name": "Řeporyje", "lat": 50.0, "lon": 14.3, "type": "400kV", "region": "Central"},
    {"name": "Čechy", "lat": 50.2, "lon": 14.8, "type": "mixed", "region": "Central"},
    {"name": "Litoměřice", "lat": 50.5, "lon": 14.1, "type": "220kV", "region": "Central"},
    {"name": "Kralupy", "lat": 50.2, "lon": 14.3, "type": "220kV", "region": "Central"},
    
    # Eastern Region
    {"name": "Hradec Králové", "lat": 50.2, "lon": 15.8, "type": "400kV", "region": "Eastern"},
    {"name": "Týnec", "lat": 50.1, "lon": 15.9, "type": "220kV", "region": "Eastern"},
    {"name": "Nošovice", "lat": 49.7, "lon": 18.4, "type": "400kV", "region": "Eastern"},
    {"name": "Kletné", "lat": 49.8, "lon": 17.8, "type": "220kV", "region": "Eastern"},
    {"name": "Horní Životice", "lat": 49.8, "lon": 18.2, "type": "400kV", "region": "Eastern"},
    {"name": "Albrechtice", "lat": 49.9, "lon": 18.3, "type": "220kV", "region": "Eastern"},
    {"name": "Prosenice", "lat": 49.5, "lon": 17.2, "type": "400kV", "region": "Eastern"},
    {"name": "Opatovice", "lat": 50.0, "lon": 15.9, "type": "220kV", "region": "Eastern"},
    
    # Southern Region
    {"name": "Temelín", "lat": 49.181, "lon": 14.375, "type": "nuclear", "region": "Southern"},
    {"name": "Kočín", "lat": 49.0, "lon": 14.1, "type": "400kV", "region": "Southern"},
    {"name": "Dasný", "lat": 48.9, "lon": 14.0, "type": "400kV", "region": "Southern"},
    {"name": "Tábor", "lat": 49.4, "lon": 14.7, "type": "220kV", "region": "Southern"},
    
    # Southeastern Region
    {"name": "Dukovany/Slavětice", "lat": 49.1042, "lon": 16.1194, "type": "nuclear", "region": "Southeastern"},
    {"name": "Sokolnice", "lat": 49.1, "lon": 16.6, "type": "400kV", "region": "Southeastern"},
    {"name": "Čebín", "lat": 49.3, "lon": 16.4, "type": "400kV", "region": "Southeastern"},
    {"name": "Mírovka", "lat": 49.2, "lon": 15.8, "type": "400kV", "region": "Southeastern"},
    {"name": "Lískovec", "lat": 49.2, "lon": 16.5, "type": "220kV", "region": "Southeastern"},
]

# Convert to DataFrame
df = pd.DataFrame(grid_stations)

# Define constraint/hotspot areas that limit transmission line routing
constraint_areas = [
    # Protected Areas - National Parks & Landscape Areas
    {"name": "Šumava National Park", "lat": 48.9, "lon": 13.7, "type": "protected", "severity": "high", 
     "description": "Large national park, transmission lines prohibited"},
    {"name": "Krkonoše National Park", "lat": 50.6, "lon": 15.7, "type": "protected", "severity": "high",
     "description": "Mountain national park, extreme terrain constraints"},
    {"name": "České Švýcarsko NP", "lat": 50.9, "lon": 14.4, "type": "protected", "severity": "high",
     "description": "Bohemian Switzerland, rocky terrain and protection"},
    {"name": "Podyjí National Park", "lat": 48.8, "lon": 15.9, "type": "protected", "severity": "medium",
     "description": "River valley protection zone"},
    
    # High Urban Density Areas
    {"name": "Prague Metro Area", "lat": 50.08, "lon": 14.42, "type": "urban", "severity": "high",
     "description": "Capital city, 1.4M population, dense infrastructure"},
    {"name": "Brno Urban Area", "lat": 49.2, "lon": 16.6, "type": "urban", "severity": "medium",
     "description": "Second largest city, 400K population"},
    {"name": "Ostrava Industrial", "lat": 49.83, "lon": 18.28, "type": "urban", "severity": "medium",
     "description": "Heavy industry and mining region"},
    {"name": "Plzeň Urban", "lat": 49.75, "lon": 13.38, "type": "urban", "severity": "medium",
     "description": "Industrial city, Škoda works"},
    
    # Soil Erosion Hotspots
    {"name": "Central Bohemian Erosion", "lat": 49.8, "lon": 14.8, "type": "erosion", "severity": "medium",
     "description": "High water erosion susceptibility"},
    {"name": "South Moravian Erosion", "lat": 49.0, "lon": 16.8, "type": "erosion", "severity": "medium",
     "description": "Wind and water erosion prone area"},
    {"name": "Elbe Lowlands Erosion", "lat": 50.3, "lon": 15.2, "type": "erosion", "severity": "low",
     "description": "Agricultural erosion concerns"},
    
    # Steep Terrain / Geological Constraints
    {"name": "Bohemian Massif", "lat": 49.5, "lon": 14.0, "type": "terrain", "severity": "medium",
     "description": "Steep slopes and rocky terrain"},
    {"name": "Moravian-Silesian Highlands", "lat": 49.6, "lon": 16.0, "type": "terrain", "severity": "medium",
     "description": "Mountainous terrain, construction challenges"},
    {"name": "Sudetes Foothills", "lat": 50.4, "lon": 16.8, "type": "terrain", "severity": "high",
     "description": "Mountain slopes, avalanche risk"},
    
    # Mining Areas
    {"name": "North Bohemian Coal", "lat": 50.6, "lon": 13.8, "type": "mining", "severity": "medium",
     "description": "Active and former mining, ground instability"},
    {"name": "Ostrava Coal Basin", "lat": 49.9, "lon": 18.4, "type": "mining", "severity": "medium",
     "description": "Mining subsidence areas"},
    
    # Water Bodies / Wetlands
    {"name": "Třeboň Wetlands", "lat": 49.0, "lon": 14.8, "type": "wetland", "severity": "medium",
     "description": "Protected wetland ecosystem"},
    {"name": "Danube Floodplain", "lat": 48.7, "lon": 16.9, "type": "wetland", "severity": "low",
     "description": "Seasonal flooding constraints"},
]

# Convert constraint areas to DataFrame
constraints_df = pd.DataFrame(constraint_areas)

# Define colors and symbols for different station types
def get_station_style(station_type):
    styles = {
        "400kV": {"color": "red", "symbol": "circle", "size": 12},
        "220kV": {"color": "green", "symbol": "circle", "size": 10},
        "mixed": {"color": "orange", "symbol": "diamond", "size": 14},
        "nuclear": {"color": "purple", "symbol": "star", "size": 16}
    }
    return styles.get(station_type, {"color": "blue", "symbol": "circle", "size": 8})

# Define colors and symbols for constraint areas
def get_constraint_style(constraint_type, severity):
    base_styles = {
        "protected": {"color": "darkgreen", "symbol": "square"},
        "urban": {"color": "darkred", "symbol": "circle"},
        "erosion": {"color": "brown", "symbol": "triangle-up"},
        "terrain": {"color": "gray", "symbol": "diamond"},
        "mining": {"color": "black", "symbol": "hexagon"},
        "wetland": {"color": "blue", "symbol": "cross"}
    }
    
    # Adjust size based on severity
    size_map = {"high": 18, "medium": 14, "low": 10}
    
    style = base_styles.get(constraint_type, {"color": "orange", "symbol": "x"})
    style["size"] = size_map.get(severity, 12)
    return style

# App layout
app.layout = html.Div([
    html.H1("Czech Republic Power Grid Network", 
            style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),
    
    html.Div([
        html.Div([
            html.H3("Legend", style={'color': '#34495e'}),
            html.Div([
                html.H4("Power Stations", style={'color': '#2c3e50', 'fontSize': '14px', 'marginBottom': '5px'}),
                html.Div([
                    html.Span("●", style={'color': 'red', 'fontSize': '20px', 'marginRight': '10px'}),
                    html.Span("400kV Stations")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("●", style={'color': 'green', 'fontSize': '20px', 'marginRight': '10px'}),
                    html.Span("220kV Stations")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("◆", style={'color': 'orange', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Span("Mixed 400kV/220kV")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("★", style={'color': 'purple', 'fontSize': '20px', 'marginRight': '10px'}),
                    html.Span("Nuclear Plants")
                ], style={'marginBottom': '15px'}),
                
                html.H4("Transmission Constraints", style={'color': '#2c3e50', 'fontSize': '14px', 'marginBottom': '5px'}),
                html.Div([
                    html.Span("■", style={'color': 'darkgreen', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Span("Protected Areas")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("●", style={'color': 'darkred', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Span("Urban Dense Areas")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("▲", style={'color': 'brown', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Span("Soil Erosion Zones")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("◆", style={'color': 'gray', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Span("Difficult Terrain")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("⬢", style={'color': 'black', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Span("Mining Areas")
                ], style={'marginBottom': '5px'}),
                html.Div([
                    html.Span("✚", style={'color': 'blue', 'fontSize': '16px', 'marginRight': '10px'}),
                    html.Span("Wetlands")
                ], style={'marginBottom': '5px'}),
            ])
        ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 
                  'padding': '20px', 'backgroundColor': '#ecf0f1', 'borderRadius': '10px'}),
        
        html.Div([
            dcc.Graph(id='power-grid-map', style={'height': '700px'})
        ], style={'width': '78%', 'display': 'inline-block', 'marginLeft': '2%'})
    ]),
    
    html.Div([
        html.H3("Station Information", style={'color': '#34495e', 'marginTop': '30px'}),
        html.Div(id='station-info', style={'padding': '20px', 'backgroundColor': '#f8f9fa', 
                                          'borderRadius': '10px', 'marginTop': '10px'})
    ])
])

# Callback to create the map
@app.callback(
    Output('power-grid-map', 'figure'),
    Input('power-grid-map', 'id')
)
def create_map(_):
    fig = go.Figure()
    
    # Add power stations
    station_types = df['type'].unique()
    
    for station_type in station_types:
        stations = df[df['type'] == station_type]
        style = get_station_style(station_type)
        
        # Create label for legend
        if station_type == "nuclear":
            label = "Nuclear Power Plants"
        elif station_type == "mixed":
            label = "Mixed 400kV/220kV"
        else:
            label = f"{station_type} Stations"
        
        fig.add_trace(go.Scattermapbox(
            lat=stations['lat'],
            lon=stations['lon'],
            mode='markers',
            marker=dict(
                size=style['size'],
                color=style['color'],
                symbol=style['symbol'],
            ),
            text=stations['name'],
            hovertemplate='<b>%{text}</b><br>' +
                         'Type: ' + station_type + '<br>' +
                         'Coordinates: %{lat:.3f}°N, %{lon:.3f}°E<br>' +
                         '<extra></extra>',
            name=label,
            legendgroup="stations"
        ))
    
    # Add constraint areas
    constraint_types = constraints_df['type'].unique()
    
    for constraint_type in constraint_types:
        constraints = constraints_df[constraints_df['type'] == constraint_type]
        
        # Create label for legend
        type_labels = {
            "protected": "Protected Areas",
            "urban": "Urban Dense Areas", 
            "erosion": "Soil Erosion Zones",
            "terrain": "Difficult Terrain",
            "mining": "Mining Areas",
            "wetland": "Wetlands"
        }
        label = type_labels.get(constraint_type, constraint_type.title())
        
        for _, constraint in constraints.iterrows():
            style = get_constraint_style(constraint['type'], constraint['severity'])
            
            fig.add_trace(go.Scattermapbox(
                lat=[constraint['lat']],
                lon=[constraint['lon']],
                mode='markers',
                marker=dict(
                    size=style['size'],
                    color=style['color'],
                    symbol=style['symbol'],
                    opacity=0.7,
                    # line=dict(width=1, color='white')
                ),
                text=[constraint['name']],
                hovertemplate='<b>%{text}</b><br>' +
                             'Type: ' + constraint_type + '<br>' +
                             'Severity: ' + constraint['severity'] + '<br>' +
                             'Impact: ' + constraint['description'] + '<br>' +
                             'Coordinates: %{lat:.3f}°N, %{lon:.3f}°E<br>' +
                             '<extra></extra>',
                name=label,
                legendgroup="constraints",
                showlegend=(constraint['name'] == constraints.iloc[0]['name'])  # Show legend only once per type
            ))
    
    # Update layout for the map
    fig.update_layout(
        mapbox=dict(
            accesstoken='pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw',  # Free Mapbox token
            style='open-street-map',  # Use OpenStreetMap instead
            center=dict(lat=49.75, lon=15.5),  # Center of Czech Republic
            zoom=6.5
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        title=dict(
            text="Czech Republic Power Grid & Transmission Constraints",
            x=0.5,
            font=dict(size=16, color='#2c3e50')
        )
    )
    
    return fig

# Combined callback for station information display
@app.callback(
    Output('station-info', 'children'),
    [Input('power-grid-map', 'clickData'),
     Input('power-grid-map', 'hoverData')]
)
def display_station_info(clickData, hoverData):
    ctx = dash.callback_context
    
    # Check which input triggered the callback
    if not ctx.triggered:
        # Initial load - show statistics
        station_stats = {
            "Total Power Stations": len(df),
            "400kV Stations": len(df[df['type'] == '400kV']),
            "220kV Stations": len(df[df['type'] == '220kV']),
            "Mixed Stations": len(df[df['type'] == 'mixed']),
            "Nuclear Plants": len(df[df['type'] == 'nuclear'])
        }
        
        constraint_stats = {
            "Protected Areas": len(constraints_df[constraints_df['type'] == 'protected']),
            "Urban Constraints": len(constraints_df[constraints_df['type'] == 'urban']),
            "Erosion Zones": len(constraints_df[constraints_df['type'] == 'erosion']),
            "Terrain Challenges": len(constraints_df[constraints_df['type'] == 'terrain']),
            "Mining Areas": len(constraints_df[constraints_df['type'] == 'mining']),
            "Wetland Areas": len(constraints_df[constraints_df['type'] == 'wetland'])
        }
        
        return html.Div([
            html.H4("Network Overview", style={'color': '#2c3e50'}),
            html.Div([
                html.H5("Power Infrastructure:", style={'color': '#34495e', 'marginTop': '10px'}),
                html.Div([
                    html.P(f"{key}: {value}", style={'margin': '3px 0'}) 
                    for key, value in station_stats.items()
                ]),
                html.H5("Transmission Constraints:", style={'color': '#34495e', 'marginTop': '15px'}),
                html.Div([
                    html.P(f"{key}: {value}", style={'margin': '3px 0'}) 
                    for key, value in constraint_stats.items()
                ]),
            ]),
            html.Hr(),
            html.P("Click on markers for detailed information.", 
                   style={'fontStyle': 'italic', 'color': '#7f8c8d'})
        ])
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # If clicked, show detailed info (priority over hover)
    if clickData is not None and 'clickData' in ctx.triggered[0]['prop_id']:
        point = clickData['points'][0]
        marker_name = point['text']
        lat = point['lat']
        lon = point['lon']
        
        # Check if it's a power station
        if marker_name in df['name'].values:
            station = df[df['name'] == marker_name].iloc[0]
            
            return html.Div([
                html.H4(f"⚡ {station['name']}", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                html.P(f"Type: {station['type']}", style={'margin': '5px 0'}),
                html.P(f"Region: {station['region']}", style={'margin': '5px 0'}),
                html.P(f"Coordinates: {lat:.4f}°N, {lon:.4f}°E", style={'margin': '5px 0'}),
                html.P(f"Grid Connection: High voltage transmission network", style={'margin': '5px 0'}),
                html.Hr(),
                html.P("Power station - transmission hub", 
                       style={'fontStyle': 'italic', 'color': '#27ae60', 'fontSize': '12px'})
            ])
        
        # Check if it's a constraint area
        elif marker_name in constraints_df['name'].values:
            constraint = constraints_df[constraints_df['name'] == marker_name].iloc[0]
            
            severity_colors = {'high': '#e74c3c', 'medium': '#f39c12', 'low': '#f1c40f'}
            severity_color = severity_colors.get(constraint['severity'], '#95a5a6')
            
            return html.Div([
                html.H4(f"⚠️ {constraint['name']}", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                html.P(f"Constraint Type: {constraint['type'].title()}", style={'margin': '5px 0'}),
                html.P(f"Severity: {constraint['severity'].title()}", 
                       style={'margin': '5px 0', 'color': severity_color, 'fontWeight': 'bold'}),
                html.P(f"Impact: {constraint['description']}", style={'margin': '5px 0'}),
                html.P(f"Coordinates: {lat:.4f}°N, {lon:.4f}°E", style={'margin': '5px 0'}),
                html.Hr(),
                html.P("Transmission constraint - limits grid expansion", 
                       style={'fontStyle': 'italic', 'color': '#e74c3c', 'fontSize': '12px'})
            ])
    
    # If no click but hover, show brief hover info
    elif hoverData is not None:
        point = hoverData['points'][0]
        marker_name = point['text']
        
        if marker_name in df['name'].values:
            station = df[df['name'] == marker_name].iloc[0]
            return html.Div([
                html.H4("Power Station", style={'color': '#2c3e50'}),
                html.P(f"Hovering: {station['name']}", style={'margin': '5px 0', 'fontWeight': 'bold'}),
                html.P(f"Type: {station['type']}", style={'margin': '5px 0'}),
            ])
        elif marker_name in constraints_df['name'].values:
            constraint = constraints_df[constraints_df['name'] == marker_name].iloc[0]
            return html.Div([
                html.H4("Transmission Constraint", style={'color': '#2c3e50'}),
                html.P(f"Hovering: {constraint['name']}", style={'margin': '5px 0', 'fontWeight': 'bold'}),
                html.P(f"Type: {constraint['type'].title()}", style={'margin': '5px 0'}),
                html.P(f"Severity: {constraint['severity'].title()}", style={'margin': '5px 0'}),
            ])
    
    # Default case
    return dash.no_updat



def find_free_port(min_port=8050, max_port=9000, max_tries=100):
    """Find a free port using random sampling"""
    for _ in range(max_tries):
        port = random.randint(min_port, max_port)
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(('', port))
                sock.listen(1)
                return port
            except socket.error:
                continue
    raise ValueError(f"No free ports found after {max_tries} attempts")

if __name__ == '__main__':
    free_port = find_free_port()
    url = f"http://localhost:{free_port}"
    app.run(debug=True, port=free_port)