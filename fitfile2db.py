#v0.5

import os
import fitparse
import pandas as pd
import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
import sqlite3
import numpy as np
import psycopg2

today = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
fit_path = os.path.join(os.getcwd(), 'testdata')
csv_path = os.path.join(os.getcwd(), 'testdata')
sqlite_db = os.path.join(os.getcwd(), 'fitfile_test.db')
use_db = True # If True, all data were written into database and no CSV would be generated
db_type = "SQLITE" # Possible types are 'PGSQL' for PostgreSQL and 'SQLITE' for SQLite3.

def find_fit_files(directory):
    fit_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if is_fit_file(file):
                fit_files.append(os.path.join(root, file))
    return fit_files

def is_fit_file(filename):
    return filename.lower().endswith('.fit')

def semicircles_to_degree(semicircles):
    return semicircles * (180 / 2 ** 31)

def mph_to_kph(speeds):
    if speeds is None:
        return None
    # Convert a single speed value to a list
    if isinstance(speeds, (int, float)):
        speeds = [speeds]
    # Filtering the list to retain only valid speed values
    speeds = [s for s in speeds if s is not None and not np.isnan(s)]
    # Convert speeds to kph
    speeds = [s * 1.609344 for s in speeds]
    # Return the first value if it was originally a single value, otherwise return the list
    return speeds[0] if len(speeds) == 1 else speeds

def load_env_variables():
    # check if .env-Datei available
    if not os.path.isfile('.env'):
        raise FileNotFoundError("Die .env-Datei wurde nicht gefunden")

    # load env-data from .env
    load_dotenv()
    host = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('USER_PASSWD')

    # check if all variables are available
    if not all([server, database, username, password]):
        raise ValueError("One or more environment variables are missing!")

    return host, database, user, password

def write_to_database(df, table_name):
    # Establish database connection
    if db_type == "PGSQL":
        host, database, user, password = load_env_variables()
        conn = psycopg2.connect(host, database, user, password)
    elif db_type == "SQLITE":
        conn = sqlite3.connect(sqlite_db)
    else:
            return
    
    cursor = conn.cursor()

    # Get the columns of the table
    cursor.execute(f"PRAGMA table_info({table_name})")
    table_info = cursor.fetchall()
    table_columns = [tup[1] for tup in table_info]
    
    # Add missing columns to the table
    for col in df.columns:
        if col not in table_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} TEXT")
            conn.commit()
            table_columns.append(col)
            
    # Write DataFrame to database
    for row in df.itertuples(index=False):
        # Create a dictionary mapping column names to their values for the current row
        row_dict = {col: getattr(row, col) for col in df.columns}
        # Create a list of values in the same order as the columns in the table
        values = [row_dict.get(col, '') for col in table_columns]
        cursor.execute(f"INSERT INTO {table_name} ({','.join(table_columns)}) VALUES ({','.join(['?']*len(table_columns))})", tuple(values))
        conn.commit()

    # Close database connection
    conn.close()

    print(f"Data successfully written to table {table_name} in database.")

def read_from_database(query):
    # Establish database connection
    if db_type == "PGSQL":
        host, database, user, password = load_env_variables()
        conn = psycopg2.connect(host, database, user, password)
    elif db_type == "SQLITE":
        conn = sqlite3.connect(sqlite_db)
    else:
            return
    
    cursor = conn.cursor()
    requested_data = pd.read_sql_query(query, conn)

    # Close connection and cursor
    cursor.close()
    conn.close()

    # Return requested data as a Pandas DataFrame
    return requested_data

def get_activity_type(fit_file):
    activity_type = None

    # open the file
    with fitparse.FitFile(fit_file) as fitfile:

        # look for all records with type "activity"
        for record in fitfile.get_messages("activity"):

            # read data field "sport" to get activity type
            sport_field = record.get("sport")
            if sport_field:
                activity_type = sport_field.value

    return activity_type

def get_totals(filename):
    # Open the fit file
    fitfile = fitparse.FitFile(filename)
    
    # Create an empty list to hold the totals data
    totals_data = []

    # Loop over all the messages in the FIT file
    for record in fitfile.get_messages():
        # Check if this is a "session" message
        if record.name == "session":
            # Get the activity type
            activity_type = record.get_value("sport")

            # Create an empty dictionary to hold the totals fields for this message
            totals_fields = {"activity_type": activity_type}

            # Loop over all the fields in this message
            for field in record:
                # Check if this field is a "totals" field
                if field.name.startswith("total_"):
                    # If so, add it to the dictionary
                    totals_fields[field.name] = field.value

            # Add the totals fields for this message to the list
            totals_data.append(totals_fields)

    # Create a pandas dataframe from the totals data
    df_totals = pd.DataFrame(totals_data)

    # Get the base filename without path
    filename = os.path.basename(filename)
    # Extract the first part of the filename before the first underscore
    name_part = filename.split('_')[0]
    # Add a new column with the name part of the file name
    df_totals.insert(0, "activity_number", name_part)

    return df_totals

def read_fit_file(file_path):
    fitfile = fitparse.FitFile(file_path)

    data = []
    for record in fitfile.get_messages('record'):
        # Create an empty dictionary to hold the data for this record
        record_data = {}
        for data_point in record:
            # Convert Garmin-Semicircles to Degree
            if data_point.name == 'position_lat' or data_point.name == 'position_long':
                record_data[data_point.name] = semicircles_to_degree(data_point.value)
            elif data_point.name == 'radar_speeds':
                record_data[data_point.name] = mph_to_kph(data_point.value)
            elif data_point.name == 'passing_speedabs':
                # Include the passing speed in kph directly in the record_data dictionary
                record_data['passing_speed_kph'] = mph_to_kph(data_point.value)
            else:
                record_data[data_point.name] = data_point.value

        data.append(record_data)

    # Convert the list of data to a Pandas DataFrame
    df = pd.DataFrame(data)
    # Give the longitude a proper field name
    df = df.rename(columns={'position_long': 'position_lon'})

    return df

def run_fitfile2db():
    # Set the directory to search for .fit files
    if fit_path:
        directory = fit_path
    else:
        directory = os.getcwd()

    # Find all .fit files in the directory
    fit_files = find_fit_files(directory)

    # Store filenames in dataframe
    df_fn = pd.DataFrame({'filename': fit_files})
    fieldname = df_fn.columns[0]
    df_fn =df_fn.rename(columns={fieldname: 'filename'})

    # Only if db flag is given:
    if use_db:
        # Check, if filename are known and build a dataframe with new files only
        querystring = 'select * from known_fitfiles'
        df_known = read_from_database(querystring)
        df_fn = df_fn[~df_fn['filename'].isin(df_known['filename'])]
        # Exit, if there is no new file
        if df_fn.empty:
            print('No new files to proceed!')
            return
    
    # Read the data from each (new) .fit file and combine it into a single DataFrame
    dfs = []
    for fit_file in df_fn['filename']:
        df = read_fit_file(fit_file)
        dfs.append(df)
    combined_df = pd.concat(dfs)

    # Convert all fields, except position data, to text
    combined_df = combined_df.astype({col: str for col in combined_df.columns if col not in ['position_lat', 'position_lon']})

    # Convert position fields to real
    if 'position_lat' in combined_df.columns:
        combined_df['position_lat'] = pd.to_numeric(combined_df['position_lat'], errors='coerce')
    if 'position_lon' in combined_df.columns:
        combined_df['position_lon'] = pd.to_numeric(combined_df['position_lon'], errors='coerce')
    if 'passing_speed_kph' in combined_df.columns:
        combined_df['passing_speed_kph'] = pd.to_numeric(combined_df['passing_speed_kph'], errors='coerce')

    # Read the totals from each (new) .fit file and combine it into a single DataFrame
    dftotals = []
    for fit_file in df_fn['filename']:
        dft = get_totals(fit_file)
        dftotals.append(dft)
    combined_df_totals = pd.concat(dftotals)

    # Write the combined DataFrames into database or to a CSV file
    if use_db:
        write_to_database(combined_df, 'fitfile_data')
        write_to_database(combined_df_totals, 'fitfile_totals')
        write_to_database(df_fn, 'known_fitfiles')
    elif csv_path:
        combined_df.to_csv(f'{csv_path}/{today}_output.csv', index=False)
        combined_df_totals.to_csv(f'{csv_path}/{today}_output_totals.csv', index=False)
    else:
        combined_df.to_csv('output.csv', index=False)
        combined_df_totals.to_csv('output_totals.csv', index=False)

run_fitfile2db()