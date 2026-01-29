"""
thermadex.thermal_comfort
=================


"""
# Standard imports

# Outside imports
import numpy as np
from atmoflux import temperature as tp, humidity as hmd

# imports from within thermadex

def heat_index(temp: float, rh: float, unit: str = "F") -> float:
    """
    Calculate heat index using the Rothfusz regression equation.
    
    The Rothfusz regression is valid for temperatures >= 80°F and 
    relative humidity >= 40%. This is a US National Weather Service
    equation calibrated specifically for Fahrenheit temperatures.
    
    Parameters
    ----------
    temp : Air temperature.
    rh : Relative humidity (%).
    unit : Unit of input temperature: "C", "F", or "K" (default is "F").
    
    Returns
    -------
    Heat index in Fahrenheit
    
    Examples
    --------
    >>> heat_index(90, 60)
    100.47...
    """
    # Convert temperature to Fahrenheit if needed
    unit = unit.upper()
    if unit != "F":
        T = tp.convert_temperature(temp, unit, "F")
    else:
        T = temp
    
    # Calculate heat index using Rothfusz regression
    h_idx = (-42.379 
          + 2.04901523 * T 
          + 10.14333127 * rh 
          - 0.22475541 * T * rh 
          - 0.00683783 * T**2 
          - 0.05481717 * rh**2 
          + 0.00122874 * T**2 * rh 
          + 0.00085282 * T * rh**2 
          - 0.00000199 * T**2 * rh**2)
    
    return h_idx

def apparent_temperature(temp: float, rh: float, wind_speed: float, unit: str = "C", wind_unit: str = "m/s") -> float:
    """
    Calculate apparent temperature using the Australian Bureau of Meteorology formula.
    
    Parameters
    ----------
    temp : Temperature value.
    rh : Relative humidity (%).
    wind_speed : Wind speed at 10m height.
    unit : Unit of input/output temperature: "C", "F", or "K" (default is "C").
    wind_unit : Unit of wind speed: "m/s", "km/h", "mph", or "knots" (default is "m/s").
    
    Returns
    -------
    Apparent temperature in the same unit as input temperature.
    
    Notes
    -----
    Formula: AT = Ta + 0.33*e - 0.70*ws - 4.00
    where:
        Ta = dry bulb temperature (°C)
        e = water vapour pressure (hPa)
        ws = wind speed (m/s) at an elevation of 10 meters
    
    The formula is calibrated for temperatures in Celsius and is most 
    accurate for typical outdoor conditions.

    Examples
    --------
    >>> apparent_temperature(30, 60, 5)
    29.8...
    >>> apparent_temperature(86, 60, 11.18, unit="F", wind_unit="mph")
    85.6...
    """
    # Validate inputs
    if not 0 < rh <= 100:
        raise ValueError("Relative humidity must be between 0 and 100%")
    if wind_speed < 0:
        raise ValueError("Wind speed must be non-negative")
    
    # Convert temperature to Celsius for calculation
    unit = unit.upper()
    if unit != "C":
        temp_C = tp.convert_temperature(temp, unit, "C")
    else:
        temp_C = temp
    
    # Convert wind speed to m/s for calculation
    wind_unit = wind_unit.lower()
    if wind_unit == "m/s":
        ws = wind_speed
    elif wind_unit == "km/h":
        ws = wind_speed / 3.6
    elif wind_unit == "mph":
        ws = wind_speed * 0.44704
    elif wind_unit == "knots" or wind_unit == "kt":
        ws = wind_speed * 0.514444
    else:
        raise ValueError("Wind unit must be 'm/s', 'km/h', 'mph', or 'knots'")
    
    # Calculate water vapour pressure (e) in hPa
    # Using simplified formula: e = (rh/100) * 6.105 * exp(17.27*T/(237.7+T))
    e = (rh / 100.0) * 6.105 * np.exp((17.27 * temp_C) / (237.7 + temp_C))
    
    # Calculate apparent temperature in Celsius
    AT_C = temp_C + 0.33 * e - 0.70 * ws - 4.00
    
    # Convert back to original unit if needed
    if unit != "C":
        return tp.convert_temperature(AT_C, "C", unit)
    else:
        return AT_C
    
def humidex(temp: float, rh: float = None, dewpoint: float = None, unit: str = "C") -> float:
    """
    Calculate Humidex (humidity index) as used by Environment Canada.
    
    Parameters
    ----------
    temp : Air temperature.
    rh : Relative humidity (%). Either rh or dewpoint must be provided.
    dewpoint : Dew point temperature in same units as temp. Either rh or dewpoint must be provided.
    unit : Unit of temperature: "C", "F", or "K" (default: "C").
    
    Returns
    -------
    Humidex value in degrees Celsius.
    
    Raises
    ------
    ValueError
        If neither rh nor dewpoint is provided.
        If both rh and dewpoint are provided.
        If rh is not between 0 and 100%.
    
    Notes
    -----
    Formula: Humidex = T + 0.5555 * (e - 10)
    where:
        T = air temperature (°C)
        e = vapor pressure (hPa)
    
    Humidex values and comfort levels:
        20-29: Little to no discomfort
        30-39: Some discomfort
        40-45: Great discomfort; avoid exertion
        46+: Dangerous; heat stroke possible
    
    Examples
    --------
    >>> humidex(30, rh=70)
    41.9...
    >>> humidex(86, rh=70, unit="F")
    41.9...
    """
    # Validate inputs
    if rh is None and dewpoint is None:
        raise ValueError("Either rh or dewpoint must be provided")
    if rh is not None and dewpoint is not None:
        raise ValueError("Provide either rh or dewpoint, not both")
    if rh is not None and not 0 < rh <= 100:
        raise ValueError("Relative humidity must be between 0 and 100%")
    
    # Convert temperature to Celsius for calculation
    unit = unit.upper()
    if unit != "C":
        temp_C = tp.convert_temperature(temp, unit, "C")
        if dewpoint is not None:
            Td_C = tp.convert_temperature(dewpoint, unit, "C")
    else:
        temp_C = temp
        if dewpoint is not None:
            Td_C = dewpoint
    
    # Calculate dewpoint if not provided
    if dewpoint is None:
        Td_C = tp.dewpoint_temperature(temp_C, rh, unit="C")
    
    # Calculate actual vapor pressure and convert kPa to hPa 
    e = hmd.actual_vp(Td_C, "C") * 10
    
    # Calculate Humidex
    humidex = temp_C + 0.5555 * (e - 10.0)
    
    return humidex


def wgbt(temp: float, rh: float, wind_speed: float = None, 
         solar_radiation: float = None, unit: str = "C", wind_unit: str = "m/s") -> float:
    """
    Calculate estimated Wet Bulb Globe Temperature (WBGT) for outdoor conditions.
    
    Parameters
    ----------
    temp : Air temperature (dry bulb).
    rh : Relative humidity (%).
    wind_speed : Wind speed at 10m height. If None, assumes 1 m/s.
    solar_radiation : Solar radiation (W/m²). If None, assumes full sun (~800 W/m²).
    unit : Unit of temperature: "C", "F", or "K" (default: "C").
    wind_unit : Unit of wind speed: "m/s", "km/h", "mph", or "knots" (default: "m/s").
    
    Returns
    -------
    WBGT value in in the same unit as input temperature.
    
    Raises
    ------
    ValueError
        If rh is not between 0 and 100%
        If wind_speed is negative
        If wind_unit is invalid
    
    Notes
    -----
    This is a simplified estimation. The actual measured WBGT requires specialized 
    instruments (natural wet bulb thermometer and black globe thermometer).
    
    WBGT ≈ 0.567*Ta + 0.393*e + 3.94
    where:
      Ta = air temp (°C)
      e = vapor pressure (hPa)
    
    WBGT thresholds (for reference):
        <27°C: Low risk
        27-29°C: Moderate risk
        29-31°C: High risk
        >31°C: Extreme risk (modify or cancel activities)
    
    Examples
    --------
    >>> wet_bulb_globe_temperature(35, 60, 3)
    29.8...
    >>> wet_bulb_globe_temperature(95, 60, 6.7, unit="F", wind_unit="mph")
    29.8...
    """
    # Validate inputs
    if not 0 < rh <= 100:
        raise ValueError("Relative humidity must be between 0 and 100%")
    if wind_speed is not None and wind_speed < 0:
        raise ValueError("Wind speed must be non-negative")
    
    # Set defaults
    if wind_speed is None:
        wind_speed = 1.0
        wind_unit = "m/s"
    if solar_radiation is None:
        solar_radiation = 800.0  # Assume full sun
    
    # Convert temperature to Celsius for calculation
    unit = unit.upper()
    if unit != "C":
        temp_C = tp.convert_temperature(temp, unit, "C")
    else:
        temp_C = temp
    
    # Convert wind speed to m/s for calculation
    wind_unit = wind_unit.lower()
    if wind_unit == "m/s":
        ws = wind_speed
    elif wind_unit == "km/h":
        ws = wind_speed / 3.6
    elif wind_unit == "mph":
        ws = wind_speed * 0.44704
    elif wind_unit == "knots" or wind_unit == "kt":
        ws = wind_speed * 0.514444
    else:
        raise ValueError("Wind unit must be 'm/s', 'km/h', 'mph', or 'knots'")
    
    # Calculate vapor pressure and convert kPa to hPa
    e = hmd.saturation_vp(temp_C, "C") * (rh / 100.0) * 10
    
    # Base calculation
    wbgt = 0.567 * temp_C + 0.393 * e + 3.94
    
    # Adjustment for wind (higher wind slightly decreases WBGT)
    wind_factor = -0.5 * (ws - 1.0) if ws > 1.0 else 0
    
    # Adjustment for solar radiation (normalized to 800 W/m²)
    solar_factor = 2.0 * (solar_radiation / 800.0 - 1.0) if solar_radiation != 800 else 0
    
    wbgt = wbgt + wind_factor + solar_factor
    
    # Convert to original unit if needed
    if unit != "C":
        wbgt = tp.convert_temperature(wbgt, "C", unit)

    return wbgt