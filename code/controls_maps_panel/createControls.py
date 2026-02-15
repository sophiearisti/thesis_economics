# Extends pandas with support for geospatial data (GeoDataFrames, spatial operations)
import geopandas as gpd  
 
# Core library for data manipulation and analysis using DataFrames
import pandas as pd  

# Removes accents and diacritics from Unicode strings (useful for text standardization)
from unidecode import unidecode  

# Creates and manipulates geometric objects such as points, lines, and polygons
from shapely.geometry import Point  

# Library for creating interactive web maps based on Leaflet.js
import folium             

# Adds interactive tooltips to GeoJSON layers in Folium maps
from folium.features import GeoJsonTooltip  

# Creates color maps and legends for visualizing data in Folium
import branca.colormap as cm  

import sys

# CRS for Bogotá
crs_metros = "EPSG:3116"  

####################################################
# First step:
# Create geographic controls: join UPZ with Locality and then join ZAT with Locality–UPZ
# The good thing is that the UPZ fits exactly within a locality
# and the ZAT fits exactly within a UPZ
# So there is no ambiguity in the spatial joins
####################################################


# --- 1. Charge shapefiles ---
zat_gdf = gpd.read_file("../../data/panel/zat/ZAT.shp")
localidad_gdf = gpd.read_file("../../data/panel/localidades/poligonos-localidades.shp")
upz_gdf = gpd.read_file("../../data/panel/upz-bogota/upz-bogota.shp")


# --- 2. Ensure same CRS ---
zat_gdf = zat_gdf.to_crs(crs_metros)
upz_gdf = upz_gdf.to_crs(crs_metros)
localidad_gdf = localidad_gdf.to_crs(crs_metros)


def merge_upz_localidad_zat(save_csv=False):

    # --- 3. associates UPZ with Localidad based on maximum spatial overlap ---
    
    #Creates a new GeoDataFrame with geometries representing the overlapping areas between upz and locality
    upz_loc_intersections = gpd.overlay(upz_gdf, localidad_gdf, how="intersection")
    
    #Calculates the area of each intersection polygon
    upz_loc_intersections["area_intersection"] = upz_loc_intersections.geometry.area

    """ Groups intersections by codigo_upz
    For each UPZ, finds the index of the row where the intersection area is largest
    This identifies the Localidad that contains most of that UPZ """
    # For each group, return the index of the row with the largest area
    idx = upz_loc_intersections.groupby("codigo_upz")["area_intersection"].idxmax()

    #Give me ONLY the rows whose index is in idx, ans return the specified columns
    gdf_upz_loc = upz_loc_intersections.loc[idx, [
        "codigo_upz", "nombre", "Identificad", "Nombre_de_l", "geometry"
    ]].rename(columns={
        "nombre": "nombre_upz",
        "Identificad": "codigo_localidad",
        "Nombre_de_l": "nombre_localidad"
    })

    # SAVE geometries of UPZ and Localidad separately
    gdf_upz_loc["geometry_upz"] = upz_gdf.geometry
    gdf_upz_loc["geometry_localidad"] = localidad_gdf.geometry


    # --- 4. associates UPZ with ZAT based on maximum spatial overlap ---
    #same as before, but now between zat and upz
    zat_upz_intersections = gpd.overlay(zat_gdf, gdf_upz_loc, how="intersection")
    zat_upz_intersections["area_intersection"] = zat_upz_intersections.geometry.area

    idx2 = zat_upz_intersections.groupby("ZAT")["area_intersection"].idxmax()
    
    gdf_zat_upz = zat_upz_intersections.loc[idx2, [
        "ZAT", "codigo_upz", "nombre_upz", "codigo_localidad", "nombre_localidad", "geometry"
    ]]
    
    # --- 3. Start from ZAT ---
    # rename geometry column to geometry_zat
    gdf_zat_upz_localidad = gpd.GeoDataFrame(
        zat_gdf[["ZAT", "geometry"]]
            .copy()
            .rename(columns={"geometry": "geometry_zat"}),
        geometry="geometry_zat",
        crs=zat_gdf.crs
    )

    # --- 4. Attach UPZ ---
    # from gdf_zat_upz select 'codigo_upz', 'nombre_upz', 'codigo_localidad', 'nombre_localidad'
    # from gdf_zat_upzgdf_zat_upz_localidad select 'ZAT', 'geometry'
    gdf_zat_upz_localidad = gdf_zat_upz_localidad.merge(
        gdf_zat_upz[[
            "ZAT",
            "codigo_upz",
            "nombre_upz",
            "codigo_localidad",
            "nombre_localidad"
        ]],
        on="ZAT",
        how="left"
    )

    
    # --- 5. Attach Localidad ---
    gdf_zat_upz_localidad = gdf_zat_upz_localidad.merge(
        gdf_upz_loc[[
            "codigo_upz", 
            "geometry_upz", 
            "geometry_localidad"
        ]], 
        on="codigo_upz", 
        how="left"
    )
    
    print("Final merge zat upz localidad :")
    print(gdf_zat_upz_localidad.columns)
    
    # --- 6. Export ---
    if save_csv:
        gdf_zat_upz_localidad.drop(columns=["geometry_zat", "geometry_upz", "geometry_localidad"]).to_csv(
            "../../data/panel/res_merges/zat_upz_localidad.csv",
            index=False
        )

    return gdf_zat_upz_localidad


####################################################
# Second step:
# Obtain the average stratum per ZAT
####################################################


def mean_estrato_per_zat(save_csv=False):

    estrato_gdf = gpd.read_file(
        "../../data/panel/estratos_por_manzana/ManzanaEstratificacion.shp"
    )

    estrato_gdf = estrato_gdf.to_crs(localidad_gdf.crs)

    # Unique values in the ESTRATO column
    print("Unique values in ESTRATO:")
    print(estrato_gdf["ESTRATO"].unique())

    # --- 1. Spatial join: blocks (manzanas) ↔ ZAT ---
    """estrato is defined per block (manzana).
    We want to aggregate this information at the ZAT level.
    First, we need to associate each block with the ZAT it belongs to."""
    intersections = gpd.overlay(estrato_gdf, zat_gdf, how="intersection")

    # Compute intersection area
    intersections["area_intersection"] = intersections.geometry.area

    # --- 2. For each block, keep the ZAT with the largest overlap ---
    idx = intersections.groupby("CODIGO_MAN")["area_intersection"].idxmax()
    manzana_zat = intersections.loc[idx, ["CODIGO_MAN", "ESTRATO", "ZAT"]]

    """for each block (manzana), we now have the ZAT it mostly belongs to.
    Next, we will group by ZAT and compute the average estrato."""
    estrato_por_zat = (
        manzana_zat.groupby("ZAT")["ESTRATO"]
        .agg(estrato_mean_custom)
        .reset_index()
        .rename(columns={"ESTRATO": "estrato_mean"})
    )

    # --- 5. Keep ZATs without estrato information as well ---

    # Merge: ZAT + attributes from estrato_por_zat
    gdf_final_estrato = zat_gdf[["ZAT"]].merge(
        estrato_por_zat,
        on="ZAT",
        how="left"
    )

    # --- 6. Check results ---
    print(gdf_final_estrato.head())
    print("Number of ZATs with average stratum calculated:", len(gdf_final_estrato))

    # --- 7. Export to CSV ---
    if save_csv := True:
        gdf_final_estrato.to_csv(
            "../../data/panel/res_merges/estrato_mean_por_zat.csv",
            index=False
        )

    return gdf_final_estrato

# --- 3. Group by ZAT and compute average stratum ---
def estrato_mean_custom(values):
    # If all blocks have stratum 0 → return 0
    if (values == 0).all():
        return None
    # If there is a mix, ignore zeros and compute the mean of the rest
    mean_val = values[values != 0].mean()
    return round(mean_val, 2)  # round to 2 decimal places


#########################################################################
# Third step:
# Obtain baseline covariates prior to the arrival of OXXO
#########################################################################


#########################################################################
# TOTAL POPULATION BY UPZ
# Merge population data from 2005 and 2009 by UPZ
#########################################################################


def merge_poblacion_baselines():

    # --- 1. Read 2005 CSV ---
    poblacion_2005 = pd.read_csv(
        "../../data/panel/baselines/poblacion_por_upz_2005.csv",
        sep=';', 
        engine='python'
    )

    # Rename columns
    poblacion_2005.columns = ['codigo_upz', 'poblacion_2005']

    # --- 2. Read 2009 CSV ---
    poblacion_2009 = pd.read_csv(
        "../../data/panel/baselines/poblacion_por_upz_2009.csv",
        sep=';',
        engine='python'
    )

    # Clean column names
    poblacion_2009.columns = [
        unidecode(c.replace('"', '').replace(' ', '_').lower()) 
        for c in poblacion_2009.columns
    ]
    
    # Rename specific columns by adding the _2009 suffix
    cols_to_rename = ['area_urbana', 'poblacion_urbana', 'densidad_urbana']
    rename_dict = {c: c + '_2009' for c in cols_to_rename}
    poblacion_2009 = poblacion_2009.rename(columns=rename_dict)

    # Ensure integer type for codigo_upz
    poblacion_2009['codigo_upz'] = poblacion_2009['codigo_upz'].astype(int)

    # --- 3. Merge with 2005 population ---
    poblacion_2009_2005 = pd.merge(
        poblacion_2005,
        poblacion_2009,
        on='codigo_upz',
        how='outer'  # keep all UPZs
    )
    
    return poblacion_2009_2005


#########################################################################
# The following CSV contains this information:
# AVERAGE HOUSEHOLD SIZE BY LOCALITY (2007)
# QUALITY OF LIFE INDEX BY LOCALITY (2007)
# It will be merged by locality
#########################################################################


def merge_baselines(poblacion_2009_2005, save_csv=False):
    baselines = pd.read_csv(
        "../../data/panel/baselines/baselines_2007_localidad.csv",
        sep=';',
        engine='python'
    )

    print(baselines.head())
    print(baselines.columns)

    # --- 2. Merge with 2007 baselines ---
    merge_baselines = pd.merge(
        poblacion_2009_2005,
        baselines,
        on='codigo_localidad',
        how='left'  # keeps all UPZs
    )

    # --- 4. Save final result ---
    if save_csv := True:
        merge_baselines.to_csv(
            "../../data/panel/res_merges/poblacion_baselines_merge.csv",
            index=False,
            sep=';',
            encoding='utf-8'
        )
        
    return merge_baselines


#########################################################################
# Fourth step:
# miscellaneous controls that may affect d or y
#########################################################################


#########################################################################
# Control for access to public transportation (TransMilenio)
# at the ZAT level
#########################################################################

# take each TransMilenio station
# check for each spatial unit whether it is within XXX meters of,
# or intersects with, a ZAT
# create a dummy variable for access to TransMilenio by ZAT
# create a count variable for the number of TransMilenio stations
# inside or intersecting each ZAT
# use gdf_zat_upz_localidad

def transmilenio_access(gdf_zat_upz_localidad, buffer=800, save_csv=False):

    # --- 1. Load TransMilenio stations shapefile ---
    datos_transmi = gpd.read_file(
        "../../data/panel/estaciones_transmilenio/Estaciones_Troncales_de_TRANSMILENIO.shp"
    )


    # --- 2. Reproject to a CRS in meters ---
    datos_transmi = datos_transmi.to_crs(crs_metros)


    # --- 3. Create a XXX-meter buffer around each station ---
    # THIS MAY BE ADJUSTED AS NEEDED FOR A ROBUSTNESS CHECK
    # each stated is represented as a point
    datos_transmi['geometry_buffer'] = datos_transmi.geometry.buffer(buffer)


    # --- 4. Prepare GeoDataFrame with the buffer as the active geometry ---
    datos_transmi_buffer = datos_transmi.set_geometry('geometry_buffer')


    # --- 5. Select required columns for the overlay ---
    transmi_gdf_sel = datos_transmi_buffer[['num_est', 'geometry_buffer']].copy()
    transmi_gdf_sel = transmi_gdf_sel.set_geometry('geometry_buffer')


    # --- 6. Reproject both datasets to a CRS in meters ---
    zat_gdf_sel = gdf_zat_upz_localidad.to_crs(crs_metros)
    transmi_gdf_sel = transmi_gdf_sel.to_crs(crs_metros)


    # --- 7. Overlay / intersection ---
    intersections = gpd.overlay(
        zat_gdf_sel,
        transmi_gdf_sel,
        how='intersection',
        keep_geom_type=False  # keep all geometry types
    )


    # --- 9. Count stations per ZAT ---
    stations_per_zat = intersections.groupby('ZAT')['num_est'].nunique().reset_index()
    stations_per_zat = stations_per_zat.rename(columns={'num_est': 'num_est_transmi'})


    # --- 10. Merge back to the original ZAT GeoDataFrame ---
    gdf_zat_upz_localidad = gdf_zat_upz_localidad.merge(
        stations_per_zat,
        on='ZAT',
        how='left'
    )


    # --- 11. Create a dummy variable for TransMilenio access ---
    gdf_zat_upz_localidad['acceso_transmi'] = (gdf_zat_upz_localidad['num_est_transmi'] > 0).astype(int)

    # fill NaN with 0 (ZATs with no nearby stations)
    gdf_zat_upz_localidad['num_est_transmi'] = gdf_zat_upz_localidad['num_est_transmi'].fillna(0)

    # --- 12. Check results ---
    print("check TransMilenio access by ZAT results:")
    print(gdf_zat_upz_localidad[['ZAT', 'num_est_transmi', 'acceso_transmi']].head())

    print(gdf_zat_upz_localidad.columns)
    
    # --- 13. Save results ---
    if save_csv := True:
        gdf_zat_upz_localidad.drop(columns=["geometry_zat", "geometry_upz", "geometry_localidad"]).to_csv(
            "../../data/panel/res_merges/zat_transmi_access.csv",
            index=False
        )
        
    return gdf_zat_upz_localidad


#########################################################################
# Arterial road access control
# by ZAT
#########################################################################


# see how many arterial roads are inside or bordering the ZAT
# we will treat this as exposure measured in number of arterial roads that touch each ZAT

def arterial_access(gdf_zat_upz_localidad, save_csv=False):
    
    datos_arterias = gpd.read_file(
        "../../data/panel/vias_principales/RedInfraestructuraVialArterial.shp"
    )


    # --- 1. Ensure the same CRS projected in meters ---
    datos_arterias = datos_arterias.to_crs(crs_metros)


    # --- 2. Intersection of arterial roads with ZAT ---
    intersections = gpd.overlay(
        gdf_zat_upz_localidad[['ZAT', 'geometry_zat']],   # ZAT
        datos_arterias[['Shape_Leng', 'geometry']],   # Roads
        how='intersection'
    )


    # --- 3. COUNT HOW MANY ROAD SEGMENTS TOUCH EACH ZAT ---
    accesos_por_zat = intersections.groupby("ZAT").size().reset_index(name="accesibilidad_arterial")

    # merge into the main GeoDataFrame
    gdf_zat_upz_localidad = gdf_zat_upz_localidad.merge(accesos_por_zat, on="ZAT", how="left")

    # replace NaN with 0
    gdf_zat_upz_localidad["accesibilidad_arterial"] = gdf_zat_upz_localidad["accesibilidad_arterial"].fillna(0)

    print(gdf_zat_upz_localidad.head())
   
    
    # --- 4. Save results ---
    if save_csv := True:
        gdf_zat_upz_localidad.drop(columns=["geometry_zat", "geometry_upz", "geometry_localidad"]).to_csv(
            "../../data/panel/res_merges/zat_arterial_access.csv",
            index=False
        )
        
    return gdf_zat_upz_localidad


####################################################
# CREATE MAP TO VERIFY THAT EVERYTHING IS CORRECT
####################################################

def create_map_for_verification(gdf_final, final_geometry="zat"):
    
    #depending on the final_geometry
    # if the user wants to visualize the data by zat, 
    # nothing needs to be done, just drop the other geometries a priori

    """if the user wants to visualize the data by upz or localidad, 
    we need to change the geometry of the gdf_final accordingly
    also the data must be aggregated accordingly 
    (mean for numeric variables, first for categorical variables)"""
    if final_geometry == "upz":

        # unir el final geometry con la geometría de upz


        # 1. Set UPZ geometry
        gdf_final = gdf_final.drop(columns=["geometry_zat", "geometry_localidad", "ZAT"]).set_geometry("geometry_upz")

        gdf_final = aggregation_function(by="codigo_upz", gdf_final=gdf_final)
        
    elif final_geometry == "localidad":
        
        # unir el final geometry con la geometría de localidad
        
        
        # 1. Set Localidad geometry
        gdf_final = gdf_final.drop(columns=["geometry_zat", "geometry_upz", "ZAT", "codigo_upz"]).set_geometry("geometry_localidad")

        gdf_final = aggregation_function(by="codigo_localidad", gdf_final=gdf_final)
        
    else:
        # keep ZAT geometry
        gdf_final = gdf_final.drop(columns=["geometry_upz", "geometry_localidad"])
       
        
    # --- Create base map ---
    map = folium.Map(location=[4.65, -74.1], zoom_start=11, tiles="cartodbpositron")

    # --- Convert to GeoJSON with dynamic tooltip ---
    # We use all columns except 'geometry'
    tooltip = GeoJsonTooltip(
        fields=[col for col in gdf_final.columns if col != f"geometry_{final_geometry}"], 
        aliases=[col for col in gdf_final.columns if col != f"geometry_{final_geometry}"], 
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: white;
            border: 1px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
        max_width=800,
    )

    # --- Add polygons ---
    folium.GeoJson(
        gdf_final,
        name="ZATs",
        tooltip=tooltip,
        style_function=lambda x: {
            "fillColor": "purple",
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.3,
        },
    ).add_to(map)

    # --- Save to HTML ---
    map.save(f"../../data/maps_data/mapa_{final_geometry}s_controles.html")

def aggregation_function(by, gdf_final):

    geom_col = gdf_final.geometry.name

    agg_dict = {}

    for col in gdf_final.columns:
        # nunca agregar el identificador ni la geometría
        if col in {by, geom_col}:
            continue

        # variables numéricas → mean
        if gdf_final[col].dtype.kind in "iuf":
            agg_dict[col] = "mean"

        # categóricas → first
        else:
            agg_dict[col] = "first"

    gdf_final = (
        gdf_final
        .dissolve(by=by, aggfunc=agg_dict)
        .reset_index()
    )

    print(f"After aggregating by {by}:")
    print(gdf_final[["codigo_localidad", "geometry_localidad"]])
    #list all data
    print(gdf_final.columns)
    
    return gdf_final


####################################################
# Fifth step:
# merge absolutely everything
####################################################
def save_final_results(gdf_final, final_geometry="zat"):
    gdf_final.drop(columns=["geometry_zat","geometry_localidad","geometry_upz"]).to_csv(
    "../../data/panel/preliminary_panel_datasets/zat_all_controls.csv",
    index=False
    )

    if final_geometry == "zat":
        gdf_final = gdf_final.drop(columns=["geometry_upz","geometry_localidad"]).set_geometry("geometry_zat")
        # save the complete shapefile
        gdf_final.to_file(
            f"../../data/panel/res_merges/final_shp/{final_geometry}_all_controls.shp"
        )
    elif final_geometry == "upz":
        gdf_final = gdf_final.drop(columns=["geometry_zat","geometry_localidad"]).set_geometry("geometry_upz")
        # save the complete shapefile
        gdf_final.to_file(
            f"../../data/panel/res_merges/final_shp/{final_geometry}_all_controls.shp"
        )
    elif final_geometry == "localidad":
        gdf_final = gdf_final.drop(columns=["geometry_zat","geometry_upz"]).set_geometry("geometry_localidad")
        # save the complete shapefile
        gdf_final.to_file(
            f"../../data/panel/res_merges/final_shp/{final_geometry}_all_controls.shp"
        )


def create_all_controls(final_geometry="zat"): 
    print("Starting the complete process of creating controls...")

    gdf_zat_upz_localidad = merge_upz_localidad_zat(save_csv=True)


    gdf_final_estrato = mean_estrato_per_zat(save_csv=True)


    poblacion_2009_2005 = merge_poblacion_baselines()
    print("Population 2005 and 2009 by UPZ merged:")


    gdf_merge_baselines = merge_baselines(poblacion_2009_2005, save_csv=True)


    gdf_acceso_transmi = transmilenio_access(gdf_zat_upz_localidad, buffer=800, save_csv=True)


    gdf_arterial_access = arterial_access(gdf_zat_upz_localidad, save_csv=True)


    # merge everything into a single CSV
    # ---- 1. Merge gdf_zat_upz_localidad with gdf_final_estrato ---
    gdf_final = gdf_zat_upz_localidad.merge(gdf_final_estrato, on="ZAT", how="left")


    # ---- 2. Merge with gdf_merge_baselines (by codigo_upz) ---
    gdf_final["codigo_upz"] = gdf_final["codigo_upz"].astype("Int64")
    gdf_merge_baselines["codigo_upz"] = gdf_merge_baselines["codigo_upz"].astype("Int64")

    # drop repeated columns in gdf_merge_baselines
    gdf_merge_baselines.drop(columns=["codigo_localidad", "nombre_localidad", "nombre_upz"], inplace=True)


    # split into with and without UPZ
    with_upz = gdf_final.dropna(subset=["codigo_upz"])
    without_upz = gdf_final[gdf_final["codigo_upz"].isna()]

    # merge only for those with UPZ
    with_upz = with_upz.merge(gdf_merge_baselines, on="codigo_upz", how="left")

    # merge back together
    gdf_final = pd.concat([with_upz, without_upz], ignore_index=True)


    # --- 3. Merge with gdf_acceso_transmi (by ZAT) ---
    gdf_final = gdf_final.merge(
        gdf_acceso_transmi[['ZAT', 'num_est_transmi', 'acceso_transmi']],
        on="ZAT",
        how="left"
    )

    print("After merging with TransMilenio access:")
    print(gdf_final.head())
    print(gdf_final.columns)


    # --- 4. Merge with gdf_arterial_access (by ZAT) ---
    gdf_final = gdf_final.merge(
        gdf_arterial_access[['ZAT', 'accesibilidad_arterial']],
        on="ZAT",
        how="left"
    )
    print("After merging with arterial access:")
    print(gdf_final.head())
    print(gdf_final.columns)


    # --- 5. Save final result ---
    save_final_results(gdf_final, final_geometry=final_geometry)

    # create a map to verify that everything is correct
    create_map_for_verification(gdf_final, final_geometry=final_geometry)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        raise ValueError(
            "Usage: python createControls.py [zat|upz|localidad]"
        )

    final_geometry = sys.argv[1].lower()

    if final_geometry not in {"zat", "upz", "localidad"}:
        raise ValueError(
            "final_geometry must be 'zat', 'upz', or 'localidad'"
        )

    print(f"Running controls with final geometry: {final_geometry.upper()}")

    create_all_controls(final_geometry=final_geometry)

