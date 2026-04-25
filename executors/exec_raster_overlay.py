import streamlit as st
import rasterio
from pyproj import Transformer
import numpy as np
import base64
import io
import matplotlib.cm as cm
from PIL import Image
import rasterio.mask
import json
import geopandas as gpd

@st.cache_data(ttl=86400)
def fetch_roof_raster(tif_path, geojson_path):
    # load up the geojson of the hospital roofs. we only want the solar heat map to show up directly *on* the buildings.
    gdf = gpd.read_file(geojson_path)
    shapes = [geom for geom in gdf.geometry]
    
    with rasterio.open(tif_path) as src:
        # punch out the raster so everything outside the hospital shapes gets ignored
        img, out_transform = rasterio.mask.mask(src, shapes, crop=False, filled=True)
        img = img[0] # Take first band
        crs = src.crs
        
    # figure out exactly where this image sits in the real world
    bounds_left = out_transform[2]
    bounds_top = out_transform[5]
    bounds_right = bounds_left + (out_transform[0] * img.shape[1])
    bounds_bottom = bounds_top + (out_transform[4] * img.shape[0])
    
    # convert the british national grid coordinates into the standard gps lat/lon PyDeck expects
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    
    lon_min, lat_min = transformer.transform(bounds_left, bounds_bottom)
    lon_max, lat_max = transformer.transform(bounds_right, bounds_top)
    
    # Mask NoData, Zeros, AND values physically outside the clip boundary
    img_masked = np.ma.masked_where((img <= 0) | np.isnan(img), img)
    
    img_min = img_masked.min()
    img_max = img_masked.max()
    if img_max > img_min:
        norm_img = (img_masked - img_min) / (img_max - img_min)
    else:
        norm_img = img_masked
        
    # throw an 'inferno' color scheme over it so it looks like a hot and cold heat map
    cmap = cm.get_cmap('inferno')
    colored_img = cmap(norm_img)
    colored_img_8bit = (colored_img * 255).astype(np.uint8)
    
    # Make masked sections 100% transparent
    colored_img_8bit[..., 3] = np.where(img_masked.mask, 0, colored_img_8bit[..., 3])
    
    # flip the image upside down because web maps and numpy arrays disagree on which way 'up' is
    colored_img_8bit = np.flipud(colored_img_8bit)
    
    # instead of serving base64 strings which can choke the browser, we'll just save it as a local png
    import os
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    os.makedirs(static_dir, exist_ok=True)
    img_path = os.path.join(static_dir, "roof_raster.png")
    
    pil_img = Image.fromarray(colored_img_8bit, mode='RGBA')
    pil_img.save(img_path, format="PNG")
    
    # Serialize for PyDeck consumption via absolute path
    data_uri = img_path
    
    # remember we made the roofs 15 meters tall? we need to slide this image up by 15.5 meters so it sits right on top like a sticker
    z_height = 15.5
    # Deck.gl expects [[left, bottom], [left, top], [right, top], [right, bottom]]
    bounds_arr = [
        [lon_min, lat_min, z_height], # bottom-left
        [lon_min, lat_max, z_height], # top-left
        [lon_max, lat_max, z_height], # top-right
        [lon_max, lat_min, z_height]  # bottom-right
    ]
    
    return data_uri, bounds_arr
