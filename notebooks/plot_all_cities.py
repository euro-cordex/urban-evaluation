import os
import yaml
import papermill as pm

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------
notebook_input = "UHI-Copy1.ipynb"  # notebook template
notebook_output_dir = "./notebooks_output"
os.makedirs(notebook_output_dir, exist_ok=True)

variable = "sfcWind"  # change to the variable you want to analyze

# ----------------------------------------------------------------------
# LOAD CITIES FROM YAML
# ----------------------------------------------------------------------
with open("cities.yaml", "r") as f:
    cities_data = yaml.safe_load(f)

# Skip any "default" city
cities = [c for c in cities_data if c not in ("default", "Paris")]

# ----------------------------------------------------------------------
# RUN NOTEBOOK FOR EACH CITY
# ----------------------------------------------------------------------
for city in cities:
    print(f"Running notebook for city: {city}, variable: {variable}")
    try:
        # Run without saving if successful
        pm.execute_notebook(
            input_path=notebook_input,
            output_path="/dev/null",  # discard output if OK
            parameters=dict(city=city, variable=variable),
            log_output=False
        )
    except Exception as e:
        # If there is an error, save it with the papermill_ name
        error_notebook = os.path.join(
            notebook_output_dir,
            f"{os.path.splitext(notebook_input)[0]}_papermill_{variable}_{city}.ipynb"
        )
        print(f"Error running {city}: {e}")
        print(f"Saving error notebook as: {error_notebook}")

        # Save the error state notebook
        pm.execute_notebook(
            input_path=notebook_input,
            output_path=error_notebook,
            parameters=dict(city=city, variable=variable),
            report_mode=False,
            log_output=True
        )

print("Execution finished — only error notebooks were saved.")