import os
import fitparse
import pandas as pd
import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
import sqlite3
import numpy as np

# Set global variables
today = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
fit_path = os.path.join(os.getcwd(), 'testdata')
csv_path = os.path.join(os.getcwd(), 'testdata')
sqlite_db = os.path.join(os.getcwd(), 'fitfile.db')
use_db = True # If True, all data were written into database and no CSV would be generated

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

def is_fit_file(filename):
    return filename.lower().endswith('.fit')

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

def find_fit_files(directory):
    fit_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if is_fit_file(file):
                fit_files.append(os.path.join(root, file))
    return fit_files

def write_to_database(df, table_name):
    
   # Establish database connection
    conn = sqlite3.connect(sqlite_db)
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

def read_data_from_database(query):
    
    # Establish database connection
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()
    requested_data = pd.read_sql_query(query, conn)

    # Close connection and cursor
    cursor.close()
    conn.close()

    # Return requested data as a Pandas DataFrame
    return requested_data
    
def run_fitfile2db(fit_path, csv_path):
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
        df_known = read_data_from_database(querystring)
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

    # Write the combined DataFrame into database or to a CSV file
    if use_db:
        # First write data, if it fails, the list of known files would be ignored for a new try
        write_to_database(combined_df, 'fitfile_data')
        write_to_database(df_fn, 'known_fitfiles')
    elif csv_path:
        combined_df.to_csv(f'{csv_path}/{today}_output.csv', index=False)
    else:
        combined_df.to_csv('output.csv', index=False)

run_fitfile2db(fit_path, csv_path)


