# WeatherUtil
This module includes methods to get data from a table and parse statistical values from it.

## Methods
### get_data()
`get_data()` returns a pandas DataFrame object. It takes one optional string parameter specifying the location of a csv file for it to pull data from, but otherwise it will default to `weather_data.csv`.

### mean(), median(), mode(), range()
These methods each take two arguments. First is a weather DataFrame object, second is a column to extract the data from. The column options are: 'temperature', 'humidity', 'precipitation', and 'windspeed'.