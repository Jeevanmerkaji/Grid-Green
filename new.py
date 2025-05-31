# import streamlit as st
# import cv2
# import time
# import numpy as np
# from ultralytics import YOLO
# from PIL import Image

# # -----------------------------
# # Energy Estimator (heuristic)
# # -----------------------------
# def estimate_energy(model_name, inference_time, resolution):
#     base_energy = {"YOLOv8n": 0.3, "YOLOv8s": 0.6, "YOLOv8m": 1.0}
#     res_factor = resolution[0] * resolution[1] / (640 * 640)
#     return round(inference_time * base_energy.get(model_name, 0.5) * res_factor, 3)

# # -----------------------------
# # Streamlit App
# # -----------------------------
# st.set_page_config(layout="wide")
# st.title("📹 Live Sustainable AI Object Detection Monitor")

# model_name = st.sidebar.selectbox("Model", ["yolov8n.pt", "yolov8s.pt"])
# resolution = st.sidebar.selectbox("Resolution", ["320x320", "640x640", "1280x1280"])
# res_tuple = tuple(map(int, resolution.split("x")))

# run = st.sidebar.toggle("Run Detection", value=False)

# # Load YOLOv8 model
# model = YOLO(model_name)

# FRAME_WINDOW = st.image([])

# # OpenCV webcam
# cap = cv2.VideoCapture(0)

# while run:
#     ret, frame = cap.read()
#     if not ret:
#         st.error("Failed to access camera.")
#         break

#     # Resize and convert BGR to RGB
#     frame = cv2.resize(frame, res_tuple)
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#     # Run inference
#     start_time = time.time()
#     results = model(rgb_frame, verbose=False)
#     end_time = time.time()

#     # Plot results on frame
#     annotated_frame = results[0].plot()

#     # Metrics
#     inference_time = round(end_time - start_time, 3)
#     energy = estimate_energy(model_name.replace(".pt", ""), inference_time, res_tuple)

#     col1, col2 = st.columns(2)
#     with col1:
#         st.metric("⏱ Inference Time", f"{inference_time}s")
#     with col2:
#         st.metric("⚡ Energy Estimate", f"{energy} J")

#     FRAME_WINDOW.image(annotated_frame)

# cap.release()



# import dash
# from dash import dcc, html, Input, Output, State
# import cv2
# import time
# import numpy as np
# from ultralytics import YOLO
# import base64
# import plotly.graph_objects as go
# from PIL import Image
# import io

# # Initialize Dash app
# app = dash.Dash(__name__, title="Green AI Object Detector")

# # Load model
# model = YOLO("yolov8n.pt")  # Default model

# # Energy estimator (same as Streamlit)
# def estimate_energy(model_name, inference_time, resolution):
#     base_energy = {"yolov8n": 0.3, "yolov8s": 0.6}
#     res_factor = resolution[0] * resolution[1] / (640 * 640)
#     return round(inference_time * base_energy.get(model_name, 0.5) * res_factor, 3)

# # Carbon estimator (grams CO2e)
# def estimate_carbon(energy_joules, region="global"):
#     carbon_intensity = {"global": 475, "europe": 300, "us": 400}  # gCO2/kWh (IEA)
#     kwh = energy_joules / 3.6e6
#     return round(kwh * carbon_intensity[region], 5)

# # App layout
# app.layout = html.Div([
#     html.H1("🌿 Green AI Object Detection", style={'textAlign': 'center'}),
    
#     html.Div([
#         dcc.Dropdown(
#             id='model-dropdown',
#             options=[{'label': 'YOLOv8 Nano', 'value': 'yolov8n'},
#                      {'label': 'YOLOv8 Small', 'value': 'yolov8s'}],
#             value='yolov8n',
#             style={'width': '50%'}
#         ),
#         dcc.Dropdown(
#             id='res-dropdown',
#             options=[{'label': '320x320', 'value': '320x320'},
#                      {'label': '640x640', 'value': '640x640'}],
#             value='640x640',
#             style={'width': '50%'}
#         ),
#         html.Button('Start/Stop', id='toggle-button', n_clicks=0),
#     ], style={'padding': '20px'}),
    
#     html.Div([
#         html.Img(id='live-feed', src='', style={'width': '60%'}),
#         dcc.Graph(id='energy-gauge', style={'width': '40%'})
#     ], style={'display': 'flex'}),
    
#     dcc.Interval(id='interval', interval=1000, disabled=True),
#     dcc.Store(id='carbon-total', data=0)  # Cumulative CO2 storage
# ])

# # Callbacks
# @app.callback(
#     [Output('live-feed', 'src'),
#      Output('energy-gauge', 'figure'),
#      Output('carbon-total', 'data'),
#      Output('interval', 'disabled')],
#     [Input('interval', 'n_intervals'),
#      Input('toggle-button', 'n_clicks')],
#     [State('model-dropdown', 'value'),
#      State('res-dropdown', 'value'),
#      State('carbon-total', 'data')]
# )
# def update_feed(n, clicks, model_name, resolution, co2_total):
#     ctx = dash.callback_context
#     if not ctx.triggered or 'toggle-button' in ctx.triggered[0]['prop_id']:
#         if clicks % 2 == 1:  # Start/Stop logic
#             return "", go.Figure(), co2_total, False
#         else:
#             return "", go.Figure(), co2_total, True
    
#     # Capture frame
#     cap = cv2.VideoCapture(0)
#     ret, frame = cap.read()
#     cap.release()
#     if not ret:
#         return "", go.Figure(), co2_total, True
    
#     # Process frame
#     res_tuple = tuple(map(int, resolution.split('x')))
#     frame = cv2.resize(frame, res_tuple)
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
#     # Inference
#     start_time = time.time()
#     results = model(rgb_frame, verbose=False)
#     inference_time = time.time() - start_time
    
#     # Annotate
#     annotated_frame = results[0].plot()
#     _, buffer = cv2.imencode('.jpg', annotated_frame)
#     img_src = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
    
#     # Energy/CO2 metrics
#     energy = estimate_energy(model_name, inference_time, res_tuple)
#     co2 = estimate_carbon(energy)
#     co2_total += co2
    
#     # Gauge chart
#     fig = go.Figure(go.Indicator(
#         mode = "gauge+number",
#         value = energy,
#         title = {'text': f"Energy (J) | CO2: {co2}g (Total: {round(co2_total, 3)}g)"},
#         gauge = {'axis': {'range': [0, 2]}}
#     ))
    
#     return img_src, fig, co2_total, False

# if __name__ == '__main__':
#     app.run_server(debug=True)





import streamlit as st
import cv2
import time
import numpy as np
from ultralytics import YOLO
import torch
from codecarbon import EmissionsTracker
tracker = EmissionsTracker()

# -----------------------------
# Estimate brightness from frame
# -----------------------------
def is_bright(image, threshold=100):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    return brightness > threshold, brightness

# -----------------------------
# Estimate energy based on model and time
# -----------------------------
# def estimate_energy(model_name, inference_time, resolution):
#     base_energy = {"yolov8n": 0.3, "yolov8s": 0.6, "yolov8m": 1.0}
#     res_factor = resolution[0] * resolution[1] / (640 * 640)
#     return round(inference_time * base_energy.get(model_name, 0.5) * res_factor, 3)

# -----------------------------
# Streamlit UI Setup
# -----------------------------
st.set_page_config(layout="wide")
st.title("🌱 Sustainable AI: Live Object Detection & Energy Monitor")

model_name = st.sidebar.selectbox("YOLOv8 Model", ["yolov8n.pt", "yolov8s.pt"])
resolution = st.sidebar.selectbox("Image Resolution", ["320x320", "640x640", "1280x1280"])
res_tuple = tuple(map(int, resolution.split("x")))
run_detection = st.sidebar.toggle("▶️ Run Detection", value=False)
auto_skip_dark = st.sidebar.checkbox("💡 Skip detection when dark", value=True)
brightness_threshold = st.sidebar.slider("Brightness Threshold", 0, 255, 100)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
# Load model
model = YOLO(model_name).to(device)
FRAME_WINDOW = st.image([])
cap = cv2.VideoCapture(0)

# Store previous inference info
if "prev_metrics" not in st.session_state:
    st.session_state.prev_metrics = {"inference_time": None, "energy": None}

while run_detection:
    ret, frame = cap.read()
    if not ret:
        st.error("Failed to access webcam.")
        break

    frame = cv2.resize(frame, res_tuple)
    bright, brightness_value = is_bright(frame, brightness_threshold)

    col1, col2, col3 = st.columns(3)
    col1.metric("💡 Brightness", f"{brightness_value:.1f}")
    col2.markdown(f"**Room is {'Bright' if bright else 'Dark'}**")

    # Skip if too dark
    if not bright and auto_skip_dark:
        col3.warning("🚫 Detection skipped due to low light")
        annotated = cv2.putText(
            frame.copy(), "Room too dark — detection skipped", (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
        )
        FRAME_WINDOW.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))

        # Show previous inference comparison
        st.subheader("📊 Last Inference Comparison")
        # if st.session_state.prev_metrics["inference_time"] is not None:
        #     st.markdown(f"- ⏱ **Inference Time**: {st.session_state.prev_metrics['inference_time']}s")
        #     st.markdown(f"- ⚡ **Energy Used**: {st.session_state.prev_metrics['energy']} J")
        # else:
        #     st.info("No previous inference data yet.")
        # continue

    # Run detection
    start_time = time.time()
    tracker.start()
    results = model(frame, verbose=False)
    end_time = time.time()

    energy_used = tracker.stop()
   
    # Inference metrics
    inference_time = round(end_time - start_time, 3)
    # energy_used = estimate_energy(model_name.replace(".pt", ""), inference_time, res_tuple)

    # Store current as previous for next loop
    st.session_state.prev_metrics = {
        "inference_time": inference_time,
        "energy": energy_used
    }

    col1.metric("⏱ Inference Time", f"{inference_time}s")
    col2.metric("⚡ Energy Used", f"{energy_used} J")

    # Show annotated result
    annotated = results[0].plot()
    FRAME_WINDOW.image(annotated, channels="BGR")

cap.release()