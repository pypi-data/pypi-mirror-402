
import pandera as pa
import pandas as pd
from pandera.typing import Series
from datetime import date as date_type
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class WeatherForecastDayTimeBlockGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Weather Forecast Time Block GET data.
    """
    time_from: Series[pd.StringDtype] = pa.Field(coerce=True, description="Start time for weather forecast time block")
    time_till: Series[pd.StringDtype] = pa.Field(coerce=True, description="End time for weather forecast time block")
    temp_celcius: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Average temperature in celsius")
    temp_min_celcius: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Minimum temperature in celsius")
    temp_max_celcius: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Maximum temperature in celsius")
    rain_mm: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Rain forecast in mm")
    weather_type: Series[pd.StringDtype] = pa.Field(coerce=True, description="Weather type of the weather forecast")
    department_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Department ID for reference")
    date: Series[pd.StringDtype] = pa.Field(coerce=True, description="Date for reference")

    @pa.check("time_from", "time_till")
    def check_time_format(cls, series: Series[pd.StringDtype]) -> Series[bool]:
        """Validate time is in HH:MM format."""
        valid = series.str.match(r"^\d{2}:\d{2}$") | series.isna()
        return valid

    class _Annotation:
        primary_key = "department_id"
        foreign_keys = {}

class WeatherForecastDayGet(BrynQPanderaDataFrameModel):
    """
    Pandera schema for validating Weather Forecast Day GET data.
    """
    id: Series[pd.StringDtype] = pa.Field(coerce=True, description="The id is a combination of department_id and date")
    department_id: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="ID of the department")
    date: Series[pd.StringDtype] = pa.Field(coerce=True, description="Date of the weather forecast")
    temp_celcius: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Average temperature in celsius")
    temp_min_celcius: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Minimum temperature in celsius")
    temp_max_celcius: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Maximum temperature in celsius")
    rain_mm: Series[pd.Int64Dtype] = pa.Field(coerce=True, description="Rain forecast in mm")
    weather_type: Series[pd.StringDtype] = pa.Field(coerce=True, description="Weather type of the weather forecast")

    class _Annotation:
        primary_key = "id"
        foreign_keys = {}

    class Config:
        coerce = True
        strict = False
