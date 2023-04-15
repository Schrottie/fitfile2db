# Collect all totals from all fit files in a directory
def combined_totals(fit_dir):
    all_data = []
    totals_data = pd.DataFrame()
    for filename in os.listdir(fit_dir):
        if filename.endswith('.fit'):
            filepath = os.path.join(fit_dir, filename)
            fitfile = FitFile(filepath)
            sport = get_activity_type(fitfile)
            df = pd.DataFrame([get_activity_data(fitfile, sport)])
            df['filename'] = filename
            all_data.append(df)
            
            totals = get_totals(fitfile)
            totals['filename'] = filename
            
            # Check if all columns exist in totals_data
            missing_columns = set(totals.columns) - set(totals_data.columns)
            if missing_columns:
                for column in missing_columns:
                    totals_data[column] = pd.Series(dtype=totals[column].dtype)
            
            # Append missing values for columns that don't exist in current dataframe
            for column in totals_data.columns:
                if column not in totals.columns:
                    totals[column] = pd.NA
            
            totals_data = pd.concat([totals_data, totals], ignore_index=True, sort=False)
    
    # Reorder columns and drop duplicates
    totals_data = totals_data[['filename', 'activity_type', 'timestamp', 'total_distance', 'total_elapsed_time', 'total_timer_time', 'total_moving_time', 'total_calories', 'total_ascent', 'total_descent', 'avg_speed', 'max_speed', 'avg_heart_rate', 'max_heart_rate']]
    totals_data.drop_duplicates(subset=['filename'], keep='first', inplace=True)
    
    # Merge all_data and totals_data on filename
    df_all = pd.concat(all_data, ignore_index=True, sort=False)
    df_all = pd.merge(df_all, totals_data, on='filename', how='left')
    
    return df_all
