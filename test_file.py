import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import networkx as nx
import json
import random
import socket
from contextlib import closing
import math
from dash.exceptions import PreventUpdate

# Load grid station data
file_path = r"C:\Users\Jeevan.Somanna\Downloads\grid_data_with_regions.json"
with open(file_path, encoding='utf-8') as f:
    data = json.load(f)
    stations = data['stations']

positions = {s['id']: (s['x'], s['y']) for s in stations}
types = {s['id']: s['type'] for s in stations}
names = {s['id']: s['name'] for s in stations}

# Create graph
def dist(a, b):
    ax, ay = positions[a]
    bx, by = positions[b]
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

# Hotspots and utility functions
HOTSPOT_RADIUS = 0.1
hotspots=[]

def point_to_segment_distance(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    if dx == dy == 0:
        return math.hypot(px - x0, py - y0)
    t = ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    proj_x = x0 + t * dx
    proj_y = y0 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

def is_near_hotspot(x0, y0, x1, y1, hotspots, radius=HOTSPOT_RADIUS):
    for hx, hy in hotspots:
        if point_to_segment_distance(hx, hy, x0, y0, x1, y1) <= radius:
            return True
    return False

def is_node_in_hotspot(x, y, hotspots, radius=HOTSPOT_RADIUS):
    for hx, hy in hotspots:
        if math.hypot(hx - x, hy - y) <= radius:
            return True
    return False

def add_secondary_edges(base_tree, original_graph, max_extra=15, threshold=200):
    added = 0
    for u, v, d in sorted(original_graph.edges(data=True), key=lambda x: x[2]['weight']):
        if added >= max_extra:
            break
        if base_tree.has_edge(u, v) or d['weight'] >= threshold:
            continue
        x0, y0 = positions[u]
        x1, y1 = positions[v]
        if is_near_hotspot(x0, y0, x1, y1, hotspots):
            continue
        base_tree.add_edge(u, v, weight=d['weight'])
        added += 1
    return base_tree

def greedy_path(graph, start, end):
    path = [start]
    current = start
    visited = {start}
    while current != end:
        neighbors = sorted((n for n in graph.nodes if n not in visited), key=lambda n: dist(current, n))
        if not neighbors:
            return path
        next_node = neighbors[0]
        path.append(next_node)
        visited.add(next_node)
        current = next_node
    return path

def greedy_tree_model(graph, start):
    tree = nx.DiGraph()
    tree.add_node(start)
    children_count = {n: 0 for n in graph.nodes}
    parents = {}
    unvisited = set(graph.nodes) - {start}
    queue = [start]
    while queue and unvisited:
        current = queue.pop(0)
        neighbors = sorted(unvisited, key=lambda n: dist(current, n))
        for n in neighbors:
            if children_count[current] < 2 and n not in parents:
                tree.add_edge(current, n, weight=dist(current, n))
                parents[n] = current
                children_count[current] += 1
                queue.append(n)
                unvisited.remove(n)
                break
    return tree.to_undirected()

type_color = {"400kv": "red", "220kv": "blue", "mixed": "green"}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

app.layout = dbc.Container([
    html.H1("⚡ Czech Grid Monitoring Dashboard", className="text-center fw-bold", style={
        "color": "#28a745", "fontSize": "3rem", "textShadow": "1px 1px 2px rgba(0,0,0,0.2)", "marginBottom": "0.2rem"
    }),
    html.H5("Real-time Optimization • CEPS Internal Monitoring", className="text-center text-muted", style={
        "marginBottom": "1rem", "fontStyle": "italic"
    }),
    html.Hr(style={"borderTop": "2px solid #28a745", "width": "60%", "margin": "auto"}),

    dcc.Tabs(id='tabs', value='tab-main', children=[
        dcc.Tab(label='Grid Visualization', value='tab-main', children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Hotspot Configuration"),
                        dbc.CardBody([
                            dbc.InputGroup([
                                dbc.Input(id='hotspot-lat', type='number', placeholder='Latitude'),
                                dbc.Input(id='hotspot-lon', type='number', placeholder='Longitude'),
                                dbc.Button("Add", id='add-hotspot', color="success", n_clicks=0),
                                dbc.Button("Clear", id='clear-hotspots', color="danger", className="ms-2", n_clicks=0)
                            ], className="mb-3"),
                            html.Div(id='current-hotspots')
                        ])
                    ], className="mb-4"),

                    dbc.Card([
                        dbc.CardHeader("Model Selection"),
                        dbc.CardBody([
                            dcc.Dropdown(
                                id='model',
                                value='slime',
                                options=[{'label': 'Slime Mold-Inspired', 'value': 'slime'}]
                            ),
                            dbc.Button("Generate Layout", id='run', color='primary', className='mt-3'),
                            html.Footer("© 2025 CEPS Monitoring — Internal Use Only",
                                        className="text-center mt-4 text-muted")
                        ])
                    ])
                ], md=4),

                dbc.Col([
                    dcc.Graph(
                        id='graph',
                        config={
                            'scrollZoom': True,
                            'displayModeBar': True,
                            'modeBarButtonsToAdd': ['zoomInMapbox', 'zoomOutMapbox']
                        }
                    )
                ], md=8)
            ])
        ]),

        # dcc.Tab(label='Analytics', value='tab-analytics', children=[
        #     html.Br(),
        #     html.H4("📊 Future Analytics Dashboard", className="text-center"),
        #     html.P("This space can be used for load forecasts, regional metrics, simulation results, etc.",
        #            className="text-center text-muted")
        # ])
        dcc.Tab(label='Analytics', value='tab-analytics', children=[
            html.Br(),
            html.H4("📊 Future Analytics Dashboard", className="text-center"),
            # html.P("This space can be used for load forecasts, regional metrics, simulation results, etc.",className="text-center text-muted"),

            html.Hr(),

            dbc.Row([
                dbc.Col([
                    html.H5("🖼️ Current Grid", className="text-center"),
                    html.Img(src='/assets/grid-image.jpeg', style={'width': '100%', 'border': '2px solid #444'}),
                ], md=6),

                dbc.Col([
                    html.H5("🗺️ Model Prediction", className="text-center"),
                    html.Img(src='/assets/green_model_image.jpeg', style={'width': '100%', 'border': '2px solid #444'}),
                ], md=6)
            ])
        ])
    ]),

# Hidden store
    dcc.Store(id='hotspots-store', data={'hotspots': hotspots}),
    dcc.Store(id='positions-store', data={'positions': positions})
], fluid=True)


@app.callback(
    Output('hotspots-store', 'data'),
    Output('current-hotspots', 'children'),
    Input('add-hotspot', 'n_clicks'),
    Input('clear-hotspots', 'n_clicks'),
    State('hotspot-lat', 'value'),
    State('hotspot-lon', 'value'),
    State('hotspots-store', 'data'),
    State('positions-store', 'data'),
    prevent_initial_call=True
)
def manage_hotspots(add_clicks, clear_clicks, lat, lon, data, pos):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    if ctx.triggered[0]['prop_id'] == 'clear-hotspots.n_clicks':
        return {'hotspots': []}, dbc.Alert("No hotspots defined.", color="info")

    if ctx.triggered[0]['prop_id'] == 'add-hotspot.n_clicks':
        if lat is None or lon is None:
            raise PreventUpdate
        new_hotspot = {
            "id": f"hotspot_{len(data['hotspots'])}",
            "x": float(lon),
            "y": float(lat),
            "type": "hotspot",
            "name": f"User Hotspot {len(data['hotspots'])}"
        }
        data['hotspots'].append(new_hotspot)

    badges = [
        dbc.Badge(f"{h['name']} ({h['x']:.2f}, {h['y']:.2f})", color="danger", className="me-1")
        for h in data['hotspots']
    ]
    return data, html.Div([html.Span("Current hotspots: ", className="fw-bold"), *badges])

@app.callback(
    Output('graph', 'figure'),
    Input('run', 'n_clicks'),
    State('model', 'value'),
    State('hotspots-store', 'data')
)
def update_graph(n, model, hotspots_data):
    if not n:
        return go.Figure()

    all_nodes = stations + hotspots_data['hotspots']
    G = nx.Graph()
    current_hotspots = hotspots_data['hotspots'];
    xy_hotspots = [(h['x'], h['y']) for h in current_hotspots]
    for s in all_nodes:
        node_id = s['id']
        x, y = s['x'], s['y']
        if is_node_in_hotspot(x, y,xy_hotspots):
            continue
        G.add_node(node_id, pos=(x, y), type=s['type'], name=s['name'])

    for i in G.nodes:
        for j in G.nodes:
            if i != j:
                ax, ay = G.nodes[i]['pos']
                bx, by = G.nodes[j]['pos']
                G.add_edge(i, j, weight=math.hypot(ax - bx, ay - by))

    if model == 'slime':
        base_tree = nx.minimum_spanning_tree(G.copy())
        graph_to_draw = add_secondary_edges(base_tree, G, max_extra=0)
        model_name = "Slime Mold-Inspired Model"
    else:
        graph_to_draw = G.copy()
        model_name = "Full Network"

    fig = go.Figure()

    for u, v in graph_to_draw.edges():
        lon0, lat0 = G.nodes[u]['pos']
        lon1, lat1 = G.nodes[v]['pos']
        fig.add_trace(go.Scattermapbox(
            lat=[lat0, lat1],
            lon=[lon0, lon1],
            mode="lines",
            line=dict(color="gray", width=2),
            hoverinfo="none",
        ))

    for node in G.nodes():
        lon, lat = G.nodes[node]['pos']
        color = type_color.get(G.nodes[node]['type'], "orange")
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode="markers+text",
            marker=dict(size=10, color=type_color[types[node]]),
                        text=[names[node]],
                        textposition="top center",
                        name=types[node]
                    ))
    for lon, lat in xy_hotspots:
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode="markers",
            marker=dict(size=30, color='rgba(255,0,0,0.3)', symbol='circle'),
            hoverinfo='skip',
            showlegend=True,
            name="Hotspot"
        ))

    fig.update_layout(
        mapbox=dict(
            accesstoken="pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw",
            style="open-street-map",
            center=dict(lat=49.75, lon=15.5),
            zoom=6.5
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        height=700,
        title=f"Electric Grid Layout: {model_name} (Hotspots: {len(hotspots_data['hotspots'])})"
    )

    return fig

app.layout.children.append(dcc.Store(id='hotspots-store', data={'hotspots': hotspots}))

def find_free_port(min_port=8050, max_port=9000, max_tries=100):
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
    port = find_free_port()
    app.run(debug=True, port=port)
