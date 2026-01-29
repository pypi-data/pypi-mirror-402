import os
import sys
from setuptools import setup, find_namespace_packages
from fnmatch import fnmatchcase
from distutils.util import convert_path

standard_exclude = ('*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info')
def find_package_data(where='.', package='', exclude=standard_exclude, exclude_directories=standard_exclude_directories):
    out = {}
    stack = [(convert_path(where), '', package)]
    while stack:
        where, prefix, package = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                        stack.append((fn, '', new_package))
                else:
                    stack.append((fn, prefix + name + '/', package))
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out

setup(name='docassemble.PovertyScale',
      version='2026.0.0',
      description=('A docassemble extension.'),
      long_description='# PovertyScale\r\n\r\nPoverty scale, updated approximately on an annual basis, to use for calculating\r\nincome eligibility in the United States.\r\n\r\n[Just get the JSON file](https://github.com/SuffolkLITLab/docassemble-PovertyScale/blob/main/docassemble/PovertyScale/data/sources/federal_poverty_scale.json)\r\n\r\n## Justification\r\n\r\nhttps://github.com/codeforamerica/fplapi exists but requires a dedicated\r\nserver, and hasn\'t been updated in recent years. At Suffolk we are already\r\nmaintaining and consuming this information in multiple apps; it\'s simple \r\nfor us to maintain the API alongside it.\r\n\r\nThe intent is that you will run this on your own Docassemble server, but we may maintain a public endpoint\r\nat some point. If you run your own Docassemble server, this allows you have one\r\nsource of truth for both use in Docassemble interviews (without the overhead of the REST call)\r\nand for use in any non-Docassemble webapps you may have.\r\n\r\n## Update frequency\r\n\r\nThe Federal Poverty Guidelines are updated annually, but not usually published in the federal register until a month or so into a new year.\r\nWe will try to closely track that update timeline. Pull requests with updated figures are welcome.\r\n\r\n## Examples\r\n\r\nSee example and demo in demo_poverty_scale.yml\r\n\r\nThis package contains a JSON file, [federal_poverty_scale.json](https://github.com/SuffolkLITLab/docassemble-PovertyScale/blob/main/docassemble/PovertyScale/data/sources/federal_poverty_scale.json), which can be referenced directly,\r\nas well as a module poverty.py which exports `poverty_scale_income_qualifies`\r\n\r\n## REST API\r\n\r\nOnce this file is installed, you can access it as a REST API with\r\na JSON response. The following endpoints are created on your Docassemble\r\nserver:\r\n\r\n* /poverty_guidelines (same as the JSON file)\r\n* /poverty_guidelines/household_size/<n> (per-household size)\r\n* /poverty_guidelines/household_size/<n>?state=ak|hi&multiplier=2\r\n* /poverty_guidelines/qualifies/household_size/<household_size>?income=1000&state=AK&multiplier=1.5\r\n\r\nYou can just use the API endpoint to retrieve the contents of the JSON file,\r\nor specify a household size and optional state and multiplier to get a tailored\r\nresponse, with either the income limit for a given household size or a \r\ndetermination that someone\'s income is below the poverty guideline.\r\n\r\nIncome is expected to be provided on a monthly basis.\r\n\r\n## Python function signatures\r\n\r\n```python\r\ndef poverty_scale_income_qualifies(total_monthly_income:float, household_size:int=1, multiplier:int=1)->Union[bool,None]:\r\n  """\r\n  Given monthly income, household size, and an optional multiplier, return whether an individual\r\n  is at or below the federal poverty level.\r\n  \r\n  Returns None if the poverty level data JSON could not be loaded.\r\n  """\r\n  \r\ndef poverty_scale_get_income_limit(household_size:int=1, multiplier:int=1)->Union[int, None]:\r\n  """\r\n  Return the income limit matching the given household size.\r\n  """\r\n  \r\n```\r\n',
      long_description_content_type='text/markdown',
      author='Quinten Steenhuis',
      author_email='qsteenhuis@suffolk.edu',
      license='The MIT License (MIT)',
      url='https://github.com/SuffolkLITLab/docassemble-PovertyScale',
      packages=find_namespace_packages(),
      install_requires=[],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/PovertyScale/', package='docassemble.PovertyScale'),
     )
