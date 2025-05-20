# Python Shiny CSV to SQLite Uploader

This Shiny application, built with Python, allows users to upload a CSV file, provide a name and description for the dataset, and then store the data into an SQLite database. The app also maintains a metadata table for the stored datasets.

## Features

- Upload CSV files.
- Preview the first 5 rows of uploaded data.
- Define a unique name and a description for each dataset.
- Store data in an SQLite database located at `data/datasets.sqlite`.
- Stores metadata (original dataset name, description, sanitized table name, timestamp) in a `_metadata` table within the SQLite database.
- Prevents duplicate dataset names.
- Sanitizes dataset names to create safe table names.
- User-friendly notifications for success, warnings, and errors.
- Simple, clean UI using a theme.

## Project Structure

-   `app.py`: Main application file containing both UI and server logic.
-   `data/`: Directory where the `datasets.sqlite` database file is stored. (This directory is created automatically if it doesn't exist when the app first tries to save data).
-   `requirements.txt`: Lists the Python dependencies for the project.

## Setup and Installation

1.  **Clone the repository (or download the files):**
    ```bash
    # If you have git installed
    # git clone <repository_url>
    # cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment:**
    -   On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```
    -   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run the Application

1.  Ensure you have completed the setup and installation steps above and that your virtual environment is activated.
2.  Navigate to the project's root directory (where `app.py` is located) in your terminal.
3.  Run the Shiny application using the command:
    ```bash
    shiny run --reload app.py
    ```
    -   The `--reload` flag enables auto-reloading if you make changes to the code.
4.  The application should open in your default web browser. If not, the terminal will usually provide a URL (e.g., `http://127.0.0.1:8000`) that you can open manually.

## Dependencies

The `requirements.txt` file lists the following core dependencies:

-   `shiny`: The Python Shiny framework.
-   `pandas`: For data manipulation and CSV reading.
-   `shinyswatch`: For theming the application.

(`sqlite3` is part of the Python standard library and does not need to be installed separately.)
