from shiny import App, ui, render, reactive, req
import shinyswatch
import pandas as pd
import sqlite3
from datetime import datetime
import os
import re

# Define the UI
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_file("file_upload", "Upload CSV File", accept=[".csv"], multiple=False),
        ui.input_text("dataset_name", "Dataset Name", placeholder="Enter a unique name"),
        ui.input_text_area("dataset_description", "Dataset Description", placeholder="Enter a brief description"),
        ui.input_action_button("save_button", "Save to Database", class_="btn btn-primary w-100"),
        title="Controls"
    ),
    ui.h4("Status Message:"),
    ui.output_text("message_output"), # Changed to output_text for simplicity with reactive.Value
    ui.hr(),
    ui.h4("Data Preview (First 5 rows):"),
    ui.output_data_frame("preview_output"),
    title="CSV to SQLite Uploader",
    theme=shinyswatch.theme.sandstone()
)


def server(input, output, session):
    db_path = os.path.join(os.path.dirname(__file__), "data", "datasets.sqlite")
    
    # Ensure data directory exists
    # Handled by the prior subtask, but good for robustness if running standalone
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    def initialize_db():
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS _metadata (
                    dataset_name TEXT PRIMARY KEY,
                    description TEXT,
                    table_name TEXT,
                    timestamp DATETIME
                )
            ''')
            conn.commit()
    
    initialize_db() # Run once when server starts

    current_message = reactive.Value("Please upload a CSV and provide dataset details.")

    @reactive.Calc
    def parsed_csv_data():
        file_infos = input.file_upload()
        if not file_infos:
            current_message.set("Awaiting CSV file upload.")
            return None
        
        file_path = file_infos[0]["datapath"]
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                # Check if it's just headers with no data rows
                if list(df.columns): # Has columns but no rows
                     current_message.set("Warning: Uploaded CSV has headers but no data rows.")
                     # Depending on requirements, this might still be "valid" for preview but not saving.
                     # For now, treat as empty for saving purposes.
                     return df # Return for preview, handle emptiness in save
                else: # Truly empty file or no columns
                    ui.notification_show("Uploaded CSV is empty.", type="warning", duration=5)
                    current_message.set("Warning: Uploaded CSV is empty or has no columns.")
                    return None
            current_message.set("CSV parsed successfully. Ready for preview or save.")
            return df
        except Exception as e:
            ui.notification_show(f"Error parsing CSV: {e}", type="error", duration=5)
            current_message.set(f"Error parsing CSV: {e}")
            return None

    @output
    @render.data_frame
    def preview_output():
        df = parsed_csv_data()
        if df is not None:
            # Even if df has only headers and no rows, .head(5) is fine.
            return render.DataGrid(df.head(5), height="250px")
        return None

    @reactive.Effect
    @reactive.event(input.save_button)
    def handle_save():
        # req ensures that these inputs are truthy (not None, not empty string, etc.)
        # For file_upload, it checks if a file has been uploaded.
        req(input.file_upload(), cancel_output=output.message_output, cancel_return="Error: No file uploaded. Please upload a CSV file.")
        
        dataset_name = input.dataset_name().strip()
        description = input.dataset_description().strip()
        
        # Ensure dataset_name is not empty
        if not dataset_name:
            msg = "Error: Dataset name cannot be empty."
            ui.notification_show(msg, type="error", duration=5)
            current_message.set(msg)
            return

        df = parsed_csv_data() # Get the parsed data

        # Ensure data is valid and not empty for saving
        if df is None:
            msg = "Error: No data to save. CSV parsing might have failed or file not uploaded."
            ui.notification_show(msg, type="error", duration=5)
            current_message.set(msg)
            return
        if df.empty and not list(df.columns): # Truly empty (no columns, no rows)
            msg = "Error: No data to save. The CSV file is completely empty."
            ui.notification_show(msg, type="error", duration=5)
            current_message.set(msg)
            return
        if df.empty and list(df.columns): # Headers only, no data rows
            msg = "Error: No data rows to save. The CSV file contains only headers."
            ui.notification_show(msg, type="error", duration=5)
            current_message.set(msg)
            return


        table_name_prefix = "data_"
        sanitized_base = re.sub(r'[^a-zA-Z0-9_]', '_', dataset_name)
        
        if not sanitized_base or all(c == '_' for c in sanitized_base):
             msg = "Error: Invalid dataset name. After sanitization, the name is empty or only underscores."
             ui.notification_show(msg, type="error", duration=5)
             current_message.set(msg)
             return
        
        table_name = table_name_prefix + sanitized_base
        # Ensure table_name is not excessively long if that's a concern
        # table_name = table_name[:MAX_TABLE_NAME_LENGTH] # Example if needed

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM _metadata WHERE dataset_name = ?", (dataset_name,))
                if cursor.fetchone()[0] > 0:
                    msg = f"Error: Dataset name '{dataset_name}' already exists."
                    ui.notification_show(msg, type="error", duration=5)
                    current_message.set(msg)
                    return
                
                # Check if the sanitized table_name itself would conflict (less likely if dataset_name is unique)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if cursor.fetchone() is not None:
                    msg = f"Error: Table name '{table_name}' (derived from dataset name) already exists in the database. Please choose a different dataset name."
                    ui.notification_show(msg, type="error", duration=10)
                    current_message.set(msg)
                    return

                df.to_sql(table_name, conn, if_exists='fail', index=False)
                
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO _metadata (dataset_name, description, table_name, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (dataset_name, description, table_name, ts))
                
                conn.commit()
                msg = f"Success: Dataset '{dataset_name}' saved as table '{table_name}'. Timestamp: {ts}"
                ui.notification_show(msg, type="success", duration=5)
                current_message.set(msg)

        except sqlite3.OperationalError as e:
            msg = f"Database operational error: {e}"
            # More specific check for "table ... already exists" from df.to_sql,
            # though metadata check should prevent this for dataset_name.
            # This could happen if table_name sanitation leads to a collision not caught by dataset_name check.
            if "already exists" in str(e).lower():
                 msg = f"Error: Table '{table_name}' (derived from dataset name '{dataset_name}') already exists in the database. This might be due to name sanitization. Please try a different dataset name."
            ui.notification_show(msg, type="error", duration=10)
            current_message.set(msg)

        except Exception as e:
            msg = f"An unexpected error occurred: {e}"
            ui.notification_show(msg, type="error", duration=5)
            current_message.set(msg)

    @output
    @render.text
    def message_output():
        return current_message.get()

# Create the Shiny app instance
app = App(app_ui, server)
