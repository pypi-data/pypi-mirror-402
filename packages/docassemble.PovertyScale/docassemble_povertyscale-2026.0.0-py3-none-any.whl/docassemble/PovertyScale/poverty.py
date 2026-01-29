import json
from typing import Union
from pathlib import Path
from docassemble.base.util import path_and_mimetype, log

__all__ = ['poverty_scale_income_qualifies',
           'get_poverty_scale_data',
           'poverty_scale_get_income_limit'
          ]

ps_poverty_scale_json_path = path_and_mimetype(f"{__package__}:data/sources/federal_poverty_scale.json")[0]

def get_poverty_scale_data():
  global ps_poverty_scale_json_path
  ps_data = {}
  try:
    if ps_poverty_scale_json_path is None:
      ps_poverty_scale_json_path = Path(__file__).parent / 'data' / 'sources' / 'federal_poverty_scale.json'
    with open(ps_poverty_scale_json_path) as f:
      ps_data = json.load(f)
  except FileNotFoundError:
    log(f"Cannot determine poverty scale: unable to locate file {ps_poverty_scale_json_path}")
  except json.JSONDecodeError as e:
    log(f"Cannot determine poverty scale: is {ps_poverty_scale_json_path} a valid JSON file? Error was {e}")
  
  return ps_data

def poverty_scale_get_income_limit(household_size:int=1, multiplier:float=1.0, state=None)->Union[int, None]:
  """
  Return the income limit matching the given household size.
  """
  ps_data = get_poverty_scale_data()
  if not ps_data:
    return None
  if state and state.lower() == 'hi':
    poverty_base = int(ps_data.get("poverty_base_hi"))
    poverty_increment = int(ps_data.get("poverty_increment_hi"))
  elif state and state.lower() == 'ak':
    poverty_base = int(ps_data.get("poverty_base_ak"))
    poverty_increment = int(ps_data.get("poverty_increment_ak"))
  else:
    poverty_base = int(ps_data.get("poverty_base"))
    poverty_increment = int(ps_data.get("poverty_increment"))
  additional_income_allowed = max(household_size - 1, 0) * poverty_increment
  household_income_limit = (poverty_base + additional_income_allowed) * multiplier
  
  return round(household_income_limit)

def poverty_scale_income_qualifies(total_monthly_income:float, household_size:int=1, multiplier:float=1.0, state=None)->Union[bool,None]:
  """
  Given monthly income, household size, and an optional multiplier, return whether an individual
  is at or below the federal poverty level.
  
  Returns None if the poverty level data JSON could not be loaded.
  """
  # Globals: poverty_increment and poverty_base
  household_income_limit = poverty_scale_get_income_limit(household_size=household_size, multiplier=multiplier, state=state)
  
  if not household_income_limit:
    return None
  
  return round((household_income_limit)/12) >=  int(total_monthly_income)
