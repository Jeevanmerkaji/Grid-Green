from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from opcua import Client
import pathlib
import pandas as pd
import datetime
import atexit
import random
import socket
from contextlib import closing
import time
import threading
from OPCUAServer import OPCUAClient
from triagelogic import Vitals, TriageSystem, SoldierRequest
import fpdf
import base64
import io
import webbrowser


triage_system = TriageSystem()


triage_results = {} 

# Initialize app with military dark theme
app = Dash(__name__,
           external_stylesheets=[
               dbc.themes.DARKLY,
               {
                   'href': 'https://fonts.googleapis.com/css2?family=Orbitron&display=swap',
                   'rel': 'stylesheet'
               }
           ],
           meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
           suppress_callback_exceptions=True)
app.title = "TACTICAL SOLDIER STATUS DASHBOARD"
server = app.server

history={}

# Create a global OPCUAClient object for the connection
opc_thread = OPCUAClient()
opc_thread.daemon = True
opc_thread.start()

# Military-style color scheme
COLORS = {
    'background': '#0a0a0a',
    'text': '#00FF41',  # Matrix green
    'panel': '#121212',
    'critical': '#FF0000',
    'warning': '#FFA500',
    'normal': '#00AA00'
}

# Dashboard Layout
app.layout = dbc.Container(fluid=True, children=[
    dcc.Store(id='selected-soldier-data'),
    dbc.Modal(
        id='soldier-detail-modal',
        is_open=False,
        size="lg",
        children=[
            dbc.ModalHeader(dbc.ModalTitle("SOLDIER DETAILS")),
            dbc.ModalBody(id='modal-body')
        ],
        backdrop='static',
        scrollable=True,
        centered=True
    ),
    # Header with military insignia
    dbc.Row([
        dbc.Col(html.Img(src=app.get_asset_url("military_logo.png"), height="20px"), width=2),
        dbc.Col(html.H1("TACTICAL SOLDIER MONITORING",
                       style={'color': COLORS['text'], 'font-family': 'Orbitron, sans-serif'}), width=8),
        dbc.Col(html.Div(id='live-clock',
                        style={'color': COLORS['text'], 'font-size': '24px'}),
                width=2)
    ], className="mb-4", style={'border-bottom': f"2px solid {COLORS['text']}"}),

    # Main content area
    dbc.Row([
        # Map Panel
        dbc.Col([
            html.Div("OPERATIONAL THEATER", className="panel-header"),
            dcc.Graph(id='health-map', config={'displayModeBar': False}),
            dcc.Interval(id='map-refresh', interval=10_000)
        ], width=8, className="map-panel"),

        # Status Panel
        dbc.Col([
            html.Div("UNIT STATUS", className="panel-header"),
            html.Div(id='soldier-status-table', className="status-table"),
            html.Div([
                html.Div("SYSTEM STATUS:", className="system-status-label"),
                html.Div(id='system-status', children="ALL SYSTEMS NOMINAL",
                         className="system-status-normal")
            ], className="system-status"),
            dcc.Interval(id='status-refresh', interval=5_000)
        ], width=4, className="status-panel")
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("TRIAGE SUMMARY", style={"color": COLORS['text'], "font-family": "Orbitron"}),
                dbc.CardBody(id="triage-summary-body", children="No data available."),
                dbc.CardFooter([
                    dbc.Button("Download PDF", id="download-btn", color="success", className="mt-2"),
                    dcc.Download(id="pdf-download")
                ])
            ], className="mt-4", style={"backgroundColor": COLORS["panel"], "borderColor": COLORS["text"]})
        ], width=12)
    ]),


    # Footer with comms status
    dbc.Row([
        dbc.Col([
            html.Div(id='comms-status', children="COMMS: STABLE",
                     className="comms-status"),
            html.Div(id='last-update', className="last-update")
        ], width=12)
    ], className="footer")
], style={'backgroundColor': COLORS['background'], 'height': '100vh'})

# Callbacks
@app.callback(
    [Output('health-map', 'figure'),
     Output('soldier-status-table', 'children'),
     Output('system-status', 'children'),
     Output('system-status', 'className'),
     Output('comms-status', 'children'),
     Output('last-update', 'children'),
     Output('live-clock', 'children')],
    [Input('map-refresh', 'n_intervals'),
     Input('status-refresh', 'n_intervals')]
)
def update_dashboard(map_intervals, status_intervals):
    try:
        # Check connection status
        if not opc_thread.is_connected:
            opc_thread.run()
            print("Reconnected to OPC UA server")

        # Get data from OPC UA
        objects = opc_thread.client.get_objects_node()
        soldiers = [node for node in objects.get_children()
                   if node.get_browse_name().Name.startswith("Soldier")]

        soldier_data = []
        status_rows = []
        critical_count = 0

        

        for soldier in soldiers:
            try:
                # Get soldier data with error handling for each field
                # name = soldier.get_browse_name().Name
                status = soldier.get_child("2:Status").get_value()
                if status == "CRITICAL":
                    critical_count += 1

                # hr= soldier.get_child("2:HeartRate").get_value()
                # bt =  soldier.get_child("2:BodyTemp").get_value()
                # spbp = soldier.get_child("2:SystolicBP").get_value()
                # dp = soldier.get_child("2:DiastolicBP").get_value()
                # rsp = soldier.get_child("2:RespiratoryRate").get_value()
                # spo2 =  soldier.get_child("2:SpO2").get_value()


                # if name not in history:
                #     history[name] = {
                #         "heart_rate": [],
                #         "body_temp":[],
                #         "spo2": [],
                #         "resp_rate": [],
                #         "systolic_bp" : [],
                #         "respiratory_rate" : [],
                #         "diastolic_bp" : [],
                #         "soldier_id" :[]

                #     }
                
                # soldier_id =  random.randint(1,5)
                # # Append new vitals
                # history[name]["heart_rate"].append(hr)
                # history[name]["body_temp"].append(bt)
                # history[name]["systolic_bp"].append(spbp)
                # history[name]["diastolic_bp"].append(dp)
                # # history[name]["blood_pressure"].append()
                # # history[name]["blood_pressure"].append((sbp, dbp))
                # history[name]["spo2"].append(spo2)
                # history[name]["respiratory_rate"].append(rsp)
                # history[name]["soldier_id"].append(soldier_id)

                # for key in history[name]:
                #     history[name][key] = history[name][key][-3:]
                
                # injury = "Gunshot wound"
                #     # Only run triage if we have 3 timepoints
                # if all(len(history[name][k]) == 3 for k in history[name]):
                #     vitals_obj = Vitals(
                #         heart_rate=history[name]["heart_rate"],
                #         bp = list(zip(history[name]["systolic_bp"], history[name]["diastolic_bp"])),
                #         spo2=history[name]["spo2"],
                #         resp_rate=history[name]["respiratory_rate"]
                #     )
                #     request = SoldierRequest(
                #         soldier_id=history[name][soldier_id],
                #         vitals=vitals_obj,
                #         injury_description=injury
                #     )
                #     triage = triage_system.determine_triage(request.vitals, request.injury_description)
                #     triage_results[name] = triage


                gps_value = soldier.get_child("2:GPS").get_value()
                if ',' in gps_value:
                    lat, lon = gps_value.split(',')
                else:
                    lat, lon = "0", "0"  # Default coordinates if format is wrong

                soldier_data.append({
                    "soldier_id": soldier.get_browse_name().Name,
                    "heart_rate": soldier.get_child("2:HeartRate").get_value(),
                    "body_temp": soldier.get_child("2:BodyTemp").get_value(),
                    "latitude": float(lat.strip()),
                    "longitude": float(lon.strip()),
                    "status": status
                })

                # Create status table row
                status_rows.append(
                    dbc.Row([
                        dbc.Col(soldier.get_browse_name().Name, width=3),
                        dbc.Col(f"{soldier.get_child('2:HeartRate').get_value():.2f} BPM", width=3),
                        dbc.Col(f"{soldier.get_child('2:BodyTemp').get_value():.1f}°C", width=3),
                        dbc.Col(status, width=3,className=f"status-{status.lower()}"),
                        # dbc.Col(triage_results.get(name, {}).get("treatment_plan", "Unknown"), width=6)
            
                    ], className="status-row")
                )
            except Exception as e:
                print(f"Error processing {soldier.get_browse_name().Name}: {e}")
                continue

        df = pd.DataFrame(soldier_data)

        # Create map
        fig = px.scatter_geo(
            df,
            lat="latitude",
            lon="longitude",
            color="status",
            hover_name="soldier_id",
            hover_data={
                "heart_rate": True,
                "body_temp": ":.1f",
                "latitude": False,
                "longitude": False,
                "status": False
            },
            projection="natural earth",
            color_discrete_map={
                "OK": COLORS['normal'],
                "INJURED": COLORS['warning'],
                "CRITICAL": COLORS['critical']
            }
        )

        # Military-style map customization
        fig.update_geos(
            showland=True,
            landcolor="#333333",
            showocean=True,
            oceancolor="#111122",
            showcountries=True,
            countrycolor="#555555"
        )

        fig.update_layout(
            plot_bgcolor=COLORS['panel'],
            paper_bgcolor=COLORS['panel'],
            font=dict(family="Orbitron, Courier New, monospace", color=COLORS['text']),
            margin={"r":0,"t":0,"l":0,"b":0},
            hoverlabel=dict(
                bgcolor=COLORS['panel'],
                font_size=16,
                font_family="Courier New"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # System status logic
        if critical_count > 0:
            system_status = f"WARNING: {critical_count} CRITICAL UNITS"
            status_class = "system-status-warning"
            comms_status = "COMMS: PRIORITY TRAFFIC"
        else:
            system_status = "ALL SYSTEMS NOMINAL"
            status_class = "system-status-normal"
            comms_status = "COMMS: STABLE"

        current_time = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")

        return (
            fig,
            status_rows,
            system_status,
            status_class,
            comms_status,
            f"LAST UPDATE: {current_time}",
            current_time.split()[0]  # Just the time for clock
        )

    except Exception as e:
        print(f"Dashboard error: {e}")
        return (
            go.Figure(),
            "STATUS UNAVAILABLE",
            "SYSTEM OFFLINE",
            "system-status-offline",
            "COMMS: OFFLINE",
            "LAST UPDATE: FAILED",
            datetime.datetime.now().strftime("%H:%M:%S")
        )

@app.callback(
    Output('soldier-detail-modal', 'is_open'),
    Output('modal-body', 'children'),
    Input('health-map', 'clickData'),
    prevent_initial_call=True
)
def display_soldier_details(clickData):
    if not clickData or 'points' not in clickData:
        return False, ""

    try:
        point = clickData['points'][0]
        soldier_id = point['hovertext']

        # Reconnect to get fresh data (or reuse if available)
        objects = opc_thread.client.get_objects_node()
        for node in objects.get_children():
            if node.get_browse_name().Name == soldier_id:
                # Extract data
                hr = node.get_child("2:HeartRate").get_value()
                temp = node.get_child("2:BodyTemp").get_value()
                status = node.get_child("2:Status").get_value()
                gps = node.get_child("2:GPS").get_value()

                bp = "120/80"
                spo2 = f"{random.randint(95, 100)}%"
                movement = "MOVING" if random.random() > 0.5 else "STATIC"

                triage = triage_results.get(soldier_id, {})
                print(triage)
                triage_plan = triage.get("treatment_plan", "Pending")
                triage_priority = triage.get("priority", "N/A")

                return True, dbc.Container([
                    html.H4(soldier_id, style={'color': COLORS['text']}),
                    html.Hr(),
                    html.P(f"Heart Rate: {hr:.1f} BPM"),
                    html.P(f"Body Temp: {temp:.1f}°C"),
                    html.P(f"Status: {status}", className=f"text-{status.lower()}"),
                    html.P(f"GPS: {gps}"),
                    html.P(f"Blood Pressure: {bp}"),
                    html.P(f"Oxygen Saturation: {spo2}"),
                    html.P(f"Movement: {movement}"),
                     html.Hr(),
                    html.H5("Triage Recommendation", style={'color': COLORS['text']}),
                    html.P(f"Priority: {triage_priority}", className="text-warning"),
                    html.P(f"Treatment Plan: {triage_plan}", className="text-info")
                ])
    except Exception as e:
        return True, html.Div(f"Error loading soldier info: {e}")

    return False, ""

#Update the Triage Summary body in the callback
@app.callback(
    Output("triage-summary-body", "children"),
    [Input("status-refresh", "n_intervals")]
)
def update_triage_summary(n):
    global triage_results
    try:
        # Get OPC UA object nodes
        objects = opc_thread.client.get_objects_node()
        soldiers = [node for node in objects.get_children()
                    if node.get_browse_name().Name.startswith("Soldier")]

        critical_count = 0

        for soldier in soldiers:
            try:
                name = soldier.get_browse_name().Name
                status = soldier.get_child("2:Status").get_value()

                if status == "CRITICAL":
                    critical_count += 1

                hr = soldier.get_child("2:HeartRate").get_value()
                bt = soldier.get_child("2:BodyTemp").get_value()
                spbp = soldier.get_child("2:SystolicBP").get_value()
                dp = soldier.get_child("2:DiastolicBP").get_value()
                rsp = soldier.get_child("2:RespiratoryRate").get_value()
                spo2 = soldier.get_child("2:SpO2").get_value()

                # Initialize history if not present
                if name not in history:
                    history[name] = {
                        "heart_rate": [],
                        "body_temp": [],
                        "spo2": [],
                        "systolic_bp": [],
                        "diastolic_bp": [],
                        "respiratory_rate": []
                    }

                # Append current vitals
                history[name]["heart_rate"].append(hr)
                history[name]["body_temp"].append(bt)
                history[name]["systolic_bp"].append(spbp)
                history[name]["diastolic_bp"].append(dp)
                history[name]["spo2"].append(spo2)
                history[name]["respiratory_rate"].append(rsp)

                
                # Keep only last 3 readings
                for key in history[name]:
                    history[name][key] = history[name][key][-3:]


                required_keys = ["heart_rate", "body_temp", "systolic_bp", "diastolic_bp", "spo2", "respiratory_rate"]
                

                # Run triage if enough data
                if all(len(history[name][k]) == 3 for k in required_keys):
                    vitals_obj = Vitals(
                        heart_rate=history[name]["heart_rate"],
                        blood_pressure=list(zip(history[name]["systolic_bp"], history[name]["diastolic_bp"])),
                        spo2=history[name]["spo2"],
                        resp_rate=history[name]["respiratory_rate"]
                    )
                    request = SoldierRequest(
                        soldier_id=name,
                        vitals=vitals_obj,
                        injury_description="Gunshot wound"  # Replace with dynamic input if available
                    )
                    triage = triage_system.determine_triage(request.vitals, request.injury_description)
                    triage_results[name] = triage

            except Exception as e:
                print(f"Error processing {soldier.get_browse_name().Name}: {e}")
                continue

        # Build UI summary list
        items = []
        for soldier_id, result in triage_results.items():
            items.append(html.Div([
                html.H5("Current Status",style={"color": COLORS['text']}),
                html.Div(children= f"Triage:{result['current_vitals']['category']} ({result['current_vitals']['priority']})"),
                html.H5(soldier_id, style={"color": COLORS['text']}),
                # html.P(f"Priority: {result.get('priority', 'N/A')}"),
                html.P(f"Plan: {result.get('treatment_plan', 'N/A')}"),
                html.P("This is a test entry.")
            ], className="mb-3", style={"borderBottom": "1px solid #555"}))
        
        print(f"items: {items}")
        return items

    except Exception as e:
        print(f"Unexpected error in update_triage_summary: {e}")
        return [html.P("Error fetching triage data.")]




@app.callback(
    Output("pdf-download", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_pdf(n_clicks):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Triage Summary", ln=True, align='C')

    for soldier_id, result in triage_results.items():
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Soldier: {soldier_id}", ln=True)
        pdf.cell(200, 10, txt=f"Priority: {result.get('priority', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Plan: {result.get('treatment_plan', 'N/A')}", ln=True)

    # Get the PDF as a bytes string
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return dcc.send_bytes(pdf_bytes, "triage_summary.pdf")


def clean_shutdown():
    try:
        opc_thread.disconnect()
        print("OPCUA client is disconnected")
    except Exception as e:
        print(f"Error disconnecting OPC Client {e}")

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
    timeout = 10
    waited = 0
    while not opc_thread.is_connected and waited < timeout:
        time.sleep(0.5)
        waited += 0.5

    try:
        free_port = find_free_port()
        url = f"http://localhost:{free_port}"
        webbrowser.open(url)
        app.run(port=free_port, debug=True)

    except KeyboardInterrupt:
        print("Server is stopped by the user")

    finally:
        clean_shutdown()
        print("Server is now stopped")