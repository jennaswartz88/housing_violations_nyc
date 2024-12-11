from housing_violations_nyc.housing_violations_nyc import get_housing_data, clean_inspection_date, count_by_month, count_by_tract
import pytest
import pandas as pd


def test_get_housing_data():
    # Test for valid input
    df = get_housing_data('MANHATTAN', 2020)
    assert isinstance(df, pd.DataFrame), "Output should be a DataFrame."
    assert not df.empty, "The DataFrame should not be empty."
    
    # Test for invalid borough
    with pytest.raises(ValueError, match="Borough must be one of NYC's 5 boroughs"):
        get_housing_data('California', 2020)
    
    # Test for invalid year
    with pytest.raises(ValueError, match="Year must be an integer between 1980 and 2023."):
        get_housing_data('MANHATTAN', 1800)



def test_clean_inspection_date():
    # Simple DataFrame with 'inspectiondate' column
    data = {"inspectiondate": ["2010-07-28T00:00:00.000", "2010-02-12T00:00:00.000", "2010-12-09T00:00:00.000"]}
    df = pd.DataFrame(data)
    
    cleaned_df = clean_inspection_date(df)
    
    # Check for the new columns
    assert 'inspection_year' in cleaned_df.columns, "The 'inspection_year' column is missing."
    assert 'inspection_month' in cleaned_df.columns, "The 'inspection_month' column is missing."
    assert 'inspection_day' in cleaned_df.columns, "The 'inspection_day' column is missing."



def test_count_by_month():
    # Create a sample DataFrame with inspection_month data
    data = {
        'inspection_year': [2020, 2020, 2020, 2020],
        'inspection_month': [1, 1, 2, 2],
        'inspection_day': [15, 16, 17, 18]
    }
    df = pd.DataFrame(data)
    
    # Run the count_by_month function
    result = count_by_month(df)
    
    # Check that the result is a DataFrame and contains the expected columns
    assert isinstance(result, pd.DataFrame), "Result should be a DataFrame."
    assert 'month' in result.columns, "The 'month' column should exist."
    assert 'count' in result.columns, "The 'count' column should exist."
    
    # Check that the counts are correct
    assert result.loc[result['month'] == 1, 'count'].values[0] == 2, "Month 1 should have a count of 2."
    assert result.loc[result['month'] == 2, 'count'].values[0] == 2, "Month 2 should have a count of 2."



def test_count_by_tract():
    # Create a sample DataFrame with 'censustract'
    data = {
        'censustract': ['001', '002', '002', '003']
    }
    df = pd.DataFrame(data)
    
    # Run the count_by_tract function
    result = count_by_tract(df)
    
    # Check that the result is a DataFrame and contains the expected columns
    assert isinstance(result, pd.DataFrame), "Result should be a DataFrame."
    assert 'censustract' in result.columns, "The 'censustract' column should exist."
    assert 'count' in result.columns, "The 'count' column should exist."
    
    # Check the counts are correct
    assert result.loc[result['censustract'] == '002', 'count'].values[0] == 2, "002 should have a count of 2."
    assert result.loc[result['censustract'] == '001', 'count'].values[0] == 1, "001 should have a count of 1."

