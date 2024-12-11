import requests
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns


def get_housing_data(borough: str, year: int):
    
    """
    Query NYC housing data from the NYC Open Data API for a given borough and year.

    Parameters:
        borough (str): The name of the borough (e.g., 'BRONX', 'MANHATTAN', 'STATEN ISLAND', 'BROOKLYN' or 'QUEENS').
        year (int): The year for which to query data (must be within 1980-2023). Can only query one year at a time.
        
    Returns:
        pd.DataFrame: A DataFrame containing the queried data.
    """
    
    # Base API endpoint
    api_url = "https://data.cityofnewyork.us/resource/wvxf-dwi5.json"
    
    # Validate borough
    valid_boroughs = {"BRONX", "MANHATTAN", "STATEN ISLAND", "BROOKLYN", "QUEENS"}
    borough = borough.upper()
    if borough not in valid_boroughs:
        raise ValueError(f"Borough must be one of NYC's 5 boroughs: {', '.join(valid_boroughs)}")
    
    # Validate year
    if not isinstance(year, int) or not (1980 <= year <= 2023):
        raise ValueError("Year must be an integer between 1980 and 2023.")
    
    # Inform the user about sampling if the limit is exceeded
    limit = 100000
    print(f"Note: The query has a limit of {limit} rows. If the data for {borough} in {year} exceeds this, only a sample will be returned.")
    
    # Format the date range
    start_date = f"{year}-01-01T00:00:00"
    end_date = f"{year}-12-31T23:59:59"
    
    # Parameters for the API request
    params = {
        "$limit": limit,
        "$where": f"inspectiondate BETWEEN '{start_date}' AND '{end_date}'",
        "boro": borough
    }
    
    # Send GET request
    response = requests.get(api_url, params=params)
    
    # Check response status and handle errors
    if response.status_code == 200:
        data = response.json()  # Parse JSON response
        if not data:
            print("No data found for the specified borough and year.")
            return pd.DataFrame()  # Return an empty DataFrame if no data found
        
        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame(data)
        print(f"This query has returned a dataframe with {len(df)} rows.")
        return df
    else:
        raise RuntimeError(f"Error: {response.status_code} - {response.text}")




def select_key_columns(df):
    """
    Filters the queried dataframe to only include important columns and/or those that this package will
    focus on. Results in a smaller df that is easier to work with and visualize, but this step is not necessary to
    remaining functions.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing all columns from original query

    Returns:
        pd.DataFrame:  A DataFrame containing only the specified columns.
    """
    columns_to_select = [
        "boro", "housenumber", "lowhousenumber", "highhousenumber", "streetname", 
        "zip", "apartment", "story", "block", "class", "inspectiondate", 
        "originalcorrectbydate", "novdescription", "novtype", "rentimpairing", 
        "councildistrict", "censustract", "nta"
    ]

    # Check if all columns exist in the DataFrame
    missing_columns = [col for col in columns_to_select if col not in df.columns]

    # Raise an error if any column names ended up in missing_columns
    if missing_columns:
        raise ValueError(f"Missing required columns in DataFrame: {', '.join(missing_columns)}")
    
    
    # Select the specified columns
    selected_df = df[columns_to_select]
    return selected_df




def clean_inspection_date(df):
    """
    Splits the 'inspectiondate' column into 'inspection_year', 'inspection_month', and 'inspection_day'
    and drops the original 'inspectiondate' column.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing the 'inspectiondate' column.

    Returns:
        pd.DataFrame: The mutated DataFrame with new columns and 'inspectiondate' removed.
    """

    # Check if 'inspectiondate' column is in the DataFrame, otherwise throw error
    if 'inspectiondate' not in df.columns:
        raise ValueError("'inspectiondate' column is missing in the DataFrame.")
        
    # Use loc to assign new columns
    df.loc[:, 'inspection_year'] = pd.to_numeric(df['inspectiondate'].str[:4])
    df.loc[:, 'inspection_month'] = pd.to_numeric(df['inspectiondate'].str[5:7])
    df.loc[:, 'inspection_day'] = pd.to_numeric(df['inspectiondate'].str[8:10])

    # Drop the original 'inspectiondate' column
    df = df.drop(columns=['inspectiondate'])

    return df




def drop_nas(df):
    """
    Removes rows with any NA values, and prints information on how many and what proportion
    of rows the function is removing

    Parameters:
        df (pd.DataFrame): The input DataFrame to be cleaned.

    Returns:
        pd.DataFrame: The cleaned DataFrame with no NA values
    """

    df_cleaned = df.dropna()

    original_length = len(df)
    new_length = len(df_cleaned)
    removed = original_length - new_length
    percent_removed = (removed / original_length)*100

    print(f"{removed} of the {original_length} original rows have been removed, leaving {new_length} remaining rows. {percent_removed} percent of the original rows were removed.")

    return df_cleaned




def count_key_issues(df):
    """
    Counts occurrences of fixed issue terms using regex 
    and calculates proportions relative to the total number of rows.

    Parameters:
        df (pd.DataFrame): The DataFrame to analyze

    Returns:
        pd.DataFrame: A DataFrame with counts and proportions for each issue term.
    """
    # setting up terms to search for using regex
    terms_patterns = {
        "mold": r"\bmold[ing]*\b",
        "heat": r"\bheat[ing]*\b",
        "leak": r"\bleak[s]*\b",
        "hot water": r"\bhot water\b",
        "ADA": r"\bADA\b" #Americans with Dissabilities Act
    }
    
    # Initialize a dictionary to store results
    results = {
        "term": [],
        "count": [],
        "proportion": []
    }
    
    # Total rows/number of violations
    total_rows = len(df)
    
    # Loop through each term and its regex pattern
    for term, pattern in terms_patterns.items():
        # Count the matches using regex (case-insensitive)
        count = df['novdescription'].str.contains(pattern, flags=re.IGNORECASE, na=False).sum()
        # Calculate proportion of all issues that mention that term
        proportion = count / total_rows if total_rows > 0 else 0
        
        # Appendint the results for each term we loop through
        results["term"].append(term)
        results["count"].append(count)
        results["proportion"].append(proportion)
    
    # Convert results to df
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by="count", ascending=False)
    return results_df




def plot_key_issues(df):
    """
    Plots a bar chart of key issues based on counts. 
    
    Parameters:
        df (pd.DataFrame): DataFrame with columns 'term', 'count'.
        Meant to be run with df output from count_key_issues function
    """

    # Check if required columns exist, otherwise throw error
    if 'term' not in df.columns or 'count' not in df.columns:
        raise ValueError("DataFrame must contain 'term' and 'count' columns.")
    
    # Create a bar chart for the count of issues
    plt.figure(figsize=(10, 6))
    plt.bar(df['term'], df['count'], color='skyblue')
    plt.xlabel('Term', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.title('Counts of Key Issues', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()  # Adjust layout to fit labels

    # Display the plot
    plt.show()



def count_by_month(df):
    """
    Counts the number of rows for each unique month in the dataset.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing 'inspection_year', 'inspection_month', and 'inspection_day'.
        This should only be run after running the clean_inspection_date function
        which outputs a df with the necessary columns for this function.
    
    Returns:
        pd.DataFrame: DataFrame with the counts of rows grouped by month or day.
    """

    # Check if required columns exist, otherwise throw error
    if 'inspection_month' not in df.columns:
        raise ValueError("DataFrame must contain a column called 'inspection_month'. Make sure you have run clean_inspection_date function!")
    
    # Group by inspection_month and count occurrences
    count_df = df.groupby('inspection_month').size().reset_index(name='count')
    count_df['month'] = count_df['inspection_month']  # Add a column for month
    count_df = count_df.drop('inspection_month', axis=1)  # Drop the original month column
    count_df = count_df.sort_values(by='month')  # Sort by month

    
    return count_df




def plot_time_series(df, start_month: int = 1, end_month: int = 12):
    """
    Plots a time series connected dot plot based on the given DataFrame. Allows the user to 
    select a range of months to visualize. 

    This is meant to be run after running count_by_month function.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing counts by month.
                           Must include a 'month' column and optionally a 'day' column.
                           This df should be the output of count_by_month function!!
        start_month (int): Start of the month range (inclusive, default is 1).
        end_month (int): End of the month range (inclusive, default is 12).
    """
    
    # Validate input for month range
    if not (1 <= start_month <= 12) or not (1 <= end_month <= 12):
        raise ValueError("Start and end months must be integers between 1 and 12.")
    
    if start_month > end_month:
        raise ValueError("Start month must be less than or equal to end month.")
    
    # Filter data for the specified month range
    filtered_df = df[(df['month'] >= start_month) & (df['month'] <= end_month)].copy()
    
    # Plot monthly counts with connected dots
    plt.figure(figsize=(10, 6))
    sns.lineplot(x='month', y='count', data=filtered_df, marker='o', color='orange', linewidth=2)
    plt.xticks(range(start_month, end_month + 1), 
                [pd.to_datetime(str(m), format='%m').strftime('%b') for m in range(start_month, end_month + 1)])
    plt.xlabel('Month')
    plt.ylabel('Count')
    plt.title(f'Monthly Count Time Series')
    
    # Show grid and plot
    plt.grid(True)
    plt.show()



def count_key_issues_by_month(df):
    """
    Groups the DataFrame by month and applies count_key_issues to each group.
    Concatenates results into a single DataFrame with an additional 'month' column.

    Parameters:
        df (pd.DataFrame): The DataFrame to analyze. Must include 'inspection_month' and 'novdescription' columns.

        
    Returns:
        pd.DataFrame: A DataFrame with counts and proportions for each term, grouped by month.
    """
    
    all_results = []  # List to hold dfs for each month

    # Ensure the 'inspection_month' column exists
    if 'inspection_month' not in df.columns:
        raise ValueError("The DataFrame must contain a 'inspection_month' column. Make sure you have run clean_inspection_date function!")

    # Group by month and apply count_key_issues
    for month, group in df.groupby('inspection_month'):
        # Apply count_key_issues to the group
        month_results = count_key_issues(group)
        
        # Add a 'month' column to indicate the current month
        month_results['month'] = month
        
        # Append to the list of results
        all_results.append(month_results)
    
    # Concatenate all results into a single DataFrame
    final_results = pd.concat(all_results, ignore_index=True)
    
    # Sort by month and term count (optional)
    final_results = final_results.sort_values(by=["month", "count"], ascending=[True, False])
    
    return final_results




def plot_issue_trends_by_range(df, start_month: int = 1, end_month: int = 12):
    """
    Plots a time series line plot for term counts grouped by month.
    Each line represents a different term or issue, filtered by a specified month range.

    This is meant to be run after running count_key_issues_by_month function.

    Parameters:
        df (pd.DataFrame): DataFrame containing 'term', 'count', and 'month' columns.
            - This df should be the output from the count_key_issues function!
        start_month (int): Start of the month range (inclusive, default is 1).
        end_month (int): End of the month range (inclusive, default is 12).
    """
    # Validate input for month range
    if not (1 <= start_month <= 12) or not (1 <= end_month <= 12):
        raise ValueError("Start and end months must be integers between 1 and 12.")
    
    if start_month > end_month:
        raise ValueError("Start month must be less than or equal to end month.")

    # Check if required columns exist, otherwise throw error
    if 'term' not in df.columns or 'count' not in df.columns or 'month' not in df.columns:
        raise ValueError("DataFrame must contain 'term' and 'count' columns.")
    
    
    # Filter the DataFrame for the specified month range
    filtered_df = df[(df['month'] >= start_month) & (df['month'] <= end_month)].copy()

    # Plotting
    plt.figure(figsize=(12, 8))
    sns.lineplot(data=filtered_df, x='month', y='count', hue='term', marker='o', linewidth=2)

    # Set plot aesthetics
    plt.title(f"Issue Trends from Month {start_month} to {end_month}")
    plt.xlabel("Month")
    plt.ylabel("Count")
    # converting from month numbers to string labels
    plt.xticks(ticks=range(1, 13), labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    plt.legend(title="Term", loc="upper left", bbox_to_anchor=(1, 1))
    plt.grid(True)
    plt.tight_layout()
    plt.show()



def count_by_tract(df):
    """
    Counts the number of rows for each unique month or day in the dataset.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing 'censustract'
    
    Returns:
        pd.DataFrame: DataFrame with the counts of rows grouped by censustract
    """
    # Group by census tract and count occurrences
    count_df = df.groupby('censustract').size().reset_index(name='count')
    count_df = count_df.sort_values(by='count', ascending = False)  # Sort by month

    return count_df