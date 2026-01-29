import requests
import os
import polars as pl
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('rhofred')
except PackageNotFoundError:
    __version__ = 'unknown'

__doc__ = '''Data from FRED
- catchidren(): categorical children
- catseries(): series in a category
- getdata(): data for a series
'''

HDR = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
}
HOST = 'https://api.stlouisfed.org'

class FRED:
    def __init__(self, key: str = None):
        if key is None:
            apikey = os.getenv('FREDKEY')
            if apikey is None:
                apikey = input('enter your FRED api key: ')
            self.apikey = apikey
        else:
            self.apikey = key
    def catchildren(self, id: int = 0) -> pl.DataFrame:
        '''
        Get category children, root category id = 0
        Ref: <https://fred.stlouisfed.org/categories>
        **Parameters**
        - id: category id
        **Returns**: DataFrame
        **Example**
        from freddata import FRED
        fred = FRED()
        fred.catchildren(0)
        '''        
        url = f'{HOST}/fred/category/children'
        params = {
            'category_id': id,
            'api_key': self.apikey,
            'file_type': 'json'
        }
        r = requests.get(url, params, headers = HDR)
        r.raise_for_status()   # if r.status_code not in range(200, 300), raise HTTPError
        try:
            df = pl.DataFrame(r.json()['categories'])
            return df
        except Exception as e:
            print(e)
    def catseries(self, id: int) -> pl.DataFrame:
        '''
        Get series in a category
        **Parameters**
        - id: category id (leaf category which has NO children)
        **Returns**: DataFrame
        **Example**
        from freddata import FRED
        fred = FRED()
        fred.catseries(32261)   # house price index
        '''
        url = f'{HOST}/fred/category/series'
        params = {
            'category_id': id,
            'api_key': self.apikey,
            'file_type': 'json'
        }
        r = requests.get(url, params, headers = HDR)
        r.raise_for_status()
        try:
            df = pl.DataFrame(r.json()['seriess'])
            return df
        except Exception as e:
            print(e)
    def getdata(self, series_id: str) -> pl.DataFrame:
        '''
        Observations or data for a series
        **Parameters**
        - series_id: series id
        **Returns**: DataFrame
        **Example**
        from freddata import FRED
        fred = FRED()
        fred.freddata('M2')
        '''
        url = f'{HOST}/fred/series/observations'
        params = {
            'series_id': series_id,
            'api_key': self.apikey,
            'file_type': 'json'
        }
        r = requests.get(url, params, headers = HDR)
        r.raise_for_status()
        try:
            df = pl.DataFrame(r.json()['observations'])
            df = df.with_columns(
                pl.col('value').map_elements(
                    lambda x: None if x == '.' else float(x),
                    return_dtype = pl.Float64
                )                
            )
            return df
        except Exception as e:
            print(e)
