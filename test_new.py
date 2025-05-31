import dash
import dash_leaflet as dl
from dash import html  # updated import
import rasterio
import numpy as np
from rasterio.warp import transform_bounds
from io import BytesIO
import base64
from PIL import Image
import matplotlib.pyplot as plt

# === Load GeoTIFF ===
tif_path = r"C:\Users\Jeevan.Somanna\Downloads\swi_combined_offset_005_norm.tif"
with rasterio.open(tif_path) as src:
    img = src.read(1)
    img = np.where(img == src.nodata, np.nan, img)
    bounds = src.bounds
    crs = src.crs
    bbox = transform_bounds(crs, 'EPSG:4326', *bounds)

# === Prepare Image for Overlay ===
# Flip image vertically to match Leaflet's top-down orientation
img = np.flipud(img)

# Normalize image to 0–255
img_norm = (img - np.nanmin(img)) / (np.nanmax(img) - np.nanmin(img))
img_uint8 = np.uint8(255 * img_norm)

# Apply colormap
rgba_img = plt.cm.viridis(img_uint8, bytes=True)

# Make transparent where data is missing
alpha_mask = ~np.isnan(img)
rgba_img[..., 3] = np.uint8(255 * alpha_mask)

# Convert to PNG
img_pil = Image.fromarray(rgba_img)
buf = BytesIO()
img_pil.save(buf, format="PNG")
encoded = base64.b64encode(buf.getvalue()).decode()

# === Dash App ===
app = dash.Dash(__name__)
center_lat = (bbox[1] + bbox[3]) / 2
center_lon = (bbox[0] + bbox[2]) / 2

app.layout = html.Div([
    html.H3("GeoTIFF on Leaflet Map"),
    dl.Map(center=[center_lat, center_lon],
           zoom=8,
           children=[
               dl.TileLayer(),  # Base map
               dl.ImageOverlay(
                   url="data:image/png;base64," + encoded,
                   bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
                   opacity=0.6
               )
           ],
           style={'width': '100%', 'height': '80vh'}
    )
])

if __name__ == '__main__':
    app.run(debug=True)
