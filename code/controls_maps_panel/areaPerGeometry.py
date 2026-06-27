#vamos a usar geopandas para unir absolutamente todos 
import geopandas as gpd
import pandas as pd
import sys
from esda.smoothing import Empirical_Bayes
import numpy as np

# --- 1. Charge shapefiles ---
zat_gdf = gpd.read_file("../../data/panel/zat/ZAT.shp")
localidad_gdf = gpd.read_file("../../data/panel/localidades/poligonos-localidades.shp")
upz_gdf = gpd.read_file("../../data/panel/upz-bogota/upz-bogota.shp")

def obtain_area_per_geometry(final_geometry="upz"):
    #obtain the area of each geometry in square meters
    if final_geometry == "zat":
        geometry_gdf = zat_gdf[['ZAT','geometry']].copy()
    elif final_geometry == "upz":
        geometry_gdf = upz_gdf[['codigo_upz','geometry']].copy()
    elif final_geometry == "localidad":
        geometry_gdf = localidad_gdf[['codigo_localidad','geometry']].copy()
    
    #reproject to a metric CRS
    geometry_gdf = geometry_gdf.to_crs(epsg=3116)
    
    #create a new column with the area in square kilometers
    geometry_gdf['area_m2'] = geometry_gdf['geometry'].area
    
    #drop geometry_gdf['geometry']
    geometry_gdf = geometry_gdf.drop(columns=['geometry'])
    
    #save to csv
    geometry_gdf.to_csv(f"../../data/panel/preliminary_panel_datasets/{final_geometry}_area.csv", index=False)
    
    return geometry_gdf
    
    
#pedir por consola si mapa o panel
# <nombre_del_script>.py map
if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Uso: python script.py [upz | localidad | zat]")
        sys.exit(1)

    final_geometry = sys.argv[1].lower()
    
    geometry_gdf =obtain_area_per_geometry(final_geometry)
    
    #open this cvs "data/panel/panel_final_clean_new_upz_trimestral.csv" and merge it with geometry_gdf
    panel_gdf = pd.read_csv("../../data/panel/panel_final_all_upz_trimestral.csv")
    
    #look at the type of the column "codigo_upz" in both dataframes
    print(f"Type of 'codigo_upz' in panel_gdf: {panel_gdf['codigo_upz'].dtype}")
    print(f"Type of 'codigo_upz' in geometry_gdf: {geometry_gdf['codigo_upz'].dtype}")
    
    #convert geometry_gdf['codigo_upz'] to the same type as panel_gdf['codigo_upz']
    geometry_gdf['codigo_upz'] = geometry_gdf['codigo_upz'].astype(panel_gdf['codigo_upz'].dtype)
    
    merged_gdf = pd.merge(panel_gdf, geometry_gdf, left_on="codigo_upz", right_on="codigo_upz", how="left")
    
    print(f"Panel merged with {final_geometry} area:")
    print(merged_gdf.head())
    
    #save to csv
    merged_gdf.to_csv("../../data/panel/panel_final_all_upz_trimestral.csv", index=False)  
    
    

