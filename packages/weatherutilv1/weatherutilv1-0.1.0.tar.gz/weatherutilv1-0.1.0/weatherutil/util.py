"""
module2 - Parses data from a CSV file using pandas and stores it in an array
"""

import pandas
from typing import Tuple

INPUT_FILE = "weather_data.csv"

def get_data(input_file = INPUT_FILE) -> pandas.DataFrame:
    """Reads CSV data from a provided file
    
    Arguments:
        input_file (str): Path to a CSV file, default is INPUT_FILE
        
    Returns:
        DataFrame: 
        Tabular data in the CSV file"""
    weather_data = pandas.read_csv(input_file)
    weather_data.columns = ['location', 'date_time', 'temperature', 
                            'humidity', 'precipitation', 'wind_speed']
    return weather_data

def mean(weather_data: pandas.DataFrame, column: str) -> float:
    """
    Returns the mean from a column of a given dataset.
    
    Arguments:
        weather_data (pandas.DataFrame): Weather data.
        column ('temperature' | 'humidity' | 'precipitation' | 'wind_speed'): Column of data to find the range of.
    
    Returns:
        float: Mean of column.
        """
    return weather_data[column].mean()

def median(weather_data: pandas.DataFrame, column: str) -> float:
    """Returns the median from a column of a given dataset.
    
    Arguments:
        weather_data (pandas.DataFrame): Weather data.
        column ('temperature' | 'humidity' | 'precipitation' | 'wind_speed'): Column of data to find the range of.
        
    Returns:
        float: Median of column."""
    return weather_data[column].median()

def mode(weather_data: pandas.DataFrame, column: str) -> float:
    """Returns the mode of a column of a given dataset.
    
    Arguments:
        weather_data (pandas.DataFrame): Weather data.
        column ('temperature' | 'humidity' | 'precipitation' | 'wind_speed'): Column of data to find the range of.
        
    Returns:
        float: Mode of column."""
    return weather_data[column].mode().loc[0]

def range(weather_data: pandas.DataFrame, column: str) -> Tuple[float, float]:
    """Returns the range of a column of a given dataset
    
    Arguments:
        weather_data (pandas.DataFrame): Weather data.
        column ('temperature' | 'humidity' | 'precipitation' | 'wind_speed'): Column of data to find the range of.
        
    Returns:
        (float, float): Min and max of column."""
    return (float(weather_data[column].min()), float(weather_data[column].max()))

if __name__ == "__main__":
    weather_data_array = get_data()
    print(weather_data_array.loc[0])
    print("=== Humidity ===")
    print(f"Mean: {mean(weather_data_array, 'humidity')}")
    print(f"Median: {median(weather_data_array, 'humidity')}")
    print(f"Mode: {mode(weather_data_array, 'humidity')}")
    print(f"Range: {range(weather_data_array, 'humidity')}")