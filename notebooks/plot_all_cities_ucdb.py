import os
import geopandas as gpd
import papermill as pm

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
notebook_input = "UHI_Annual.ipynb"  # notebook template
notebook_output_dir = "./notebooks_output"
os.makedirs(notebook_output_dir, exist_ok=True)

variable = "hurs"  # change to the variable you want to analyze

# LOAD UCDB DATA AND FILTER EUROPEAN CITIES
print("Loading UCDB data...")

root_aux_data = "/mnt/CORDEX_CMIP6_tmp/aux_data/"
ucdb_path = f"{root_aux_data}GHS_FUA_UCD/GHS_UCDB_GLOBE_R2024A.gpkg"

# Load UCDB layers
gdf_centroids = gpd.read_file(ucdb_path, layer="UC_centroids")
gdf_char = gpd.read_file(ucdb_path, layer="GHS_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A")

# Clean column names
gdf_centroids.columns = gdf_centroids.columns.str.strip().str.replace("﻿", "", regex=True)
gdf_char.columns = gdf_char.columns.str.strip().str.replace("﻿", "", regex=True)

# Reproject to WGS84
gdf_centroids = gdf_centroids.to_crs(epsg=4326)

# Merge centroid geometry with characteristics
gdf_merged = gdf_char.merge(
    gdf_centroids[["ID_UC_G0", "geometry"]],
    on="ID_UC_G0",
    suffixes=("_char", "_centroid")
)

# Set the geometry to the centroid geometry
gdf_merged = gdf_merged.set_geometry("geometry_centroid")

# Extract lon/lat for filtering
lon_tmp = gdf_merged.geometry.x
lat_tmp = gdf_merged.geometry.y

# Filter cities by area and Europe bounding box
gdf_filtered = gdf_merged[gdf_merged["GC_UCA_KM2_2025"] >= 12.5 * 12.5].copy()
gdf_europe = gdf_filtered[
    (lat_tmp >= 34) & (lat_tmp <= 72) &
    (lon_tmp >= -25) & (lon_tmp <= 45)
].copy()

print(f"Filtered European cities (≥144 km²): {len(gdf_europe)}")

# PREPARE CITY-COUNTRY LIST
def clean_string(s):
    if isinstance(s, str):
        return s.strip().replace("\ufeff", "")
    return s

gdf_europe["GC_UCN_MAI_2025"] = gdf_europe["GC_UCN_MAI_2025"].apply(clean_string)
gdf_europe["GC_CNT_GAD_2025"] = gdf_europe["GC_CNT_GAD_2025"].apply(clean_string)

city_country_list = list(zip(gdf_europe["GC_UCN_MAI_2025"], gdf_europe["GC_CNT_GAD_2025"]))

# RUN NOTEBOOK FOR EACH CITY
for city, country in reversed(city_country_list):
    print(f"\nRunning notebook for {city}, {country} — variable: {variable}")

    output_tmp = os.path.join(
        notebook_output_dir,
        f"{os.path.splitext(notebook_input)[0]}_tmp_{variable}_{city}.ipynb"
    )

    try:
        pm.execute_notebook(
            input_path=notebook_input,
            output_path=output_tmp,
            parameters=dict(city=city, country=country, variable=variable),
            log_output=False
        )
        os.remove(output_tmp)
    except Exception as e:
        error_notebook = os.path.join(
            notebook_output_dir,
            f"{os.path.splitext(notebook_input)[0]}_error_{variable}_{city}.ipynb"
        )
        os.rename(output_tmp, error_notebook)
        print(f"Error running {city} ({country}): {e}")
        print(f"Saved error notebook as: {error_notebook}")
        continue  

print("\nExecution finished — only error notebooks were saved.")
