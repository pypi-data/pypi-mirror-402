# PovertyScale

[![PyPI version](https://badge.fury.io/py/docassemble.PovertyScale.svg)](https://badge.fury.io/py/docassemble.PovertyScale)

Poverty scale, updated approximately on an annual basis, to use for calculating
income eligibility in the United States.

[Just get the JSON file](https://github.com/SuffolkLITLab/docassemble-PovertyScale/blob/main/docassemble/PovertyScale/data/sources/federal_poverty_scale.json)

## Justification

https://github.com/codeforamerica/fplapi exists but requires a dedicated
server, and hasn't been updated in recent years. At Suffolk we are already
maintaining and consuming this information in multiple apps; it's simple 
for us to maintain the API alongside it.

The intent is that you will run this on your own Docassemble server, but we may maintain a public endpoint
at some point. If you run your own Docassemble server, this allows you have one
source of truth for both use in Docassemble interviews (without the overhead of the REST call)
and for use in any non-Docassemble webapps you may have.

## Update frequency

The Federal Poverty Guidelines are updated annually, but not usually published in the federal register until a month or so into a new year.
We will try to closely track that update timeline. Pull requests with updated figures are welcome.

## Examples

See example and demo in demo_poverty_scale.yml

This package contains a JSON file, [federal_poverty_scale.json](https://github.com/SuffolkLITLab/docassemble-PovertyScale/blob/main/docassemble/PovertyScale/data/sources/federal_poverty_scale.json), which can be referenced directly,
as well as a module poverty.py which exports `poverty_scale_income_qualifies`

## REST API

Once this file is installed, you can access it as a REST API with
a JSON response. The following endpoints are created on your Docassemble
server:

* /poverty_guidelines (same as the JSON file)
* /poverty_guidelines/household_size/<n> (per-household size)
* /poverty_guidelines/household_size/<n>?state=ak|hi&multiplier=2
* /poverty_guidelines/qualifies/household_size/<household_size>?income=1000&state=AK&multiplier=1.5

You can just use the API endpoint to retrieve the contents of the JSON file,
or specify a household size and optional state and multiplier to get a tailored
response, with either the income limit for a given household size or a 
determination that someone's income is below the poverty guideline.

Income is expected to be provided on a monthly basis.

## Python function signatures

```python
def poverty_scale_income_qualifies(total_monthly_income:float, household_size:int=1, multiplier:int=1)->Union[bool,None]:
  """
  Given monthly income, household size, and an optional multiplier, return whether an individual
  is at or below the federal poverty level.
  
  Returns None if the poverty level data JSON could not be loaded.
  """
  
def poverty_scale_get_income_limit(household_size:int=1, multiplier:int=1)->Union[int, None]:
  """
  Return the income limit matching the given household size.
  """
  
```
