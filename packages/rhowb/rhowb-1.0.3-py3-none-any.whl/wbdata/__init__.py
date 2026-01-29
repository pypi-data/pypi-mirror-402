import requests
import json
import polars as pl
from importlib.resources import files
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('rhowb')
except PackageNotFoundError:
    __version__ = 'unknown'
    
__doc__ = 'Data from world bank api'


HDR = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.36'
}
HOST = 'https://api.worldbank.org/v2'
PARAMS = {
    'format': 'json'
}

class WB:
    def __init__(self):
        # incomelevel: f'{HOST}/incomeLevel}'
        # lendingtype: f'{HOST}/lendingType}'
        income = [
            {'id': 'HIC', 'iso2code': 'XD', 'value': 'high income'},
            {'id': 'INX', 'iso2code': 'XY', 'value': 'not classified'},
            {'id': 'LIC', 'iso2code': 'XM', 'value': 'low income'},
            {'id': 'LMC', 'iso2code': 'XN', 'value': 'lower middle income'},
            {'id': 'LMY', 'iso2code': 'XO', 'value': 'low & middle income'},
            {'id': 'MIC', 'iso2code': 'XP', 'value': 'middle income'},
            {'id': 'UMC', 'iso2code': 'XT', 'value': 'upper middle income'}
        ]
        inc_df = pl.from_dicts(income)
        lend = [
            {'id': 'IBD', 'iso2code': 'XF', 'value': 'IBRD'},
            {'id': 'IDB', 'iso2code': 'XH', 'value': 'Blend'},
            {'id': 'IDX', 'iso2code': 'XI', 'value': 'IDA'},
            {'id': 'INX', 'iso2code': 'XX', 'value': 'Not classified'}
        ]
        lend_df = pl.from_dicts(lend)    
        self.incomelevels = inc_df
        self.lendingtypes = lend_df
    def getsources(self, fromcache: bool = True) -> pl.DataFrame:
        '''
        Source databases of wb api
        **Parameters**
        - fromcache: if True, read from local file
        **Returns**: DataFrame
        **Example**
        from wbdata import WB
        wb = WB()
        wb.getsources()
        '''
        if fromcache:
            with files('wbdata').joinpath('asset', 'sources.csv').open('rb') as f:
                df = pl.read_csv(f)
        else:
            url = f'{HOST}/source'
            PARAMS['per_page'] = 80   # till 2025-12-30, there are 71 sources
            r = requests.get(url, params = PARAMS, headers = HDR)
            r.raise_for_status()
            l = r.json()[1]
            df = pl.from_dicts(
                l,
                schema = ['id', 'code', 'name', 'lastupdated', 'concepts']
            )
        return df
    def getregions(self, fromcache: bool = True) -> pl.DataFrame:
        '''
        Regions in world bank, e.g. 'South Asia'
        **Parameters**
        - fromcache: if True, read from local file
        **Returns**: DataFrame
        **Example**
        from wbdata import WB
        wb = WB()
        wb.getregions()   
        '''
        if fromcache:
            with files('wbdata').joinpath('asset', 'regions.csv').open('rb') as f:
                df = pl.read_csv(f)
        else:
            url = f'{HOST}/region'
            r = requests.get(url, params = PARAMS, headers = HDR)
            r.raise_for_status()
            l = r.json()[1]
            df = pl.from_dicts(l)
        return df
    def gettopics(self, fromcache: bool = True) -> pl.DataFrame:
        '''
        List topics in world bank, e.g. 'Education'
        **Parameters**
        - fromcache: if True, read from local file
        **Returns**: DataFrame
        **Example**
        from wbdata import WB
        wb = WB()
        wb.gettopics()
        '''
        if fromcache:
            with files('wbdata').joinpath('asset', 'topics.json').open('rb') as f:
                df = pl.read_ndjson(f)
        else:
            url = f'{HOST}/topic'
            r = requests.get(url, params = PARAMS, headers = HDR)
            r.raise_for_status()
            df = pl.from_dicts(r.json()[1])
        return df
    def queryecons(self, *, name: str = None, region: str = None, incomelevel: str = None, lendtype: str = None, excludeaggs: bool = True, fromcache: bool = True) -> pl.DataFrame:
        '''
        Query information about wb's member economies
        **Parameters**
        - name: querying pattern on economy name, e.g. 'China'. NB: case-sensitive
        - region: querying on region id, e.g. 'EAS' (East Asia & Pacific)
        - incomelevel: querying on incomelevel id, e.g. 'UMC' (Upper middle income)
        - lendtype: querying on lendtype id, e.g. 'IBD' (IBRD)
          NB: At least one of the above four querying conditions are NOT None!
        - excludeaggs: if True, exclude aggregates
        - fromcache: if True, read from local file
        **Returns**: DataFrame
        **Example**
        from wbdata import WB
        wb = WB()
        wb.queryecons(name = 'China')
        wb.queryecons(region = 'EAS', incomelevel = 'HIC')
        '''
        assert (name is not None) or (region is not None) or (incomelevel is not None) or (lendtype is not None), 'specify at least one parameter'
        if fromcache:
            with files('wbdata').joinpath('asset', 'economies.json').open('rb') as f:
                df = pl.read_ndjson(f)
        else:
            url = f'{HOST}/country'
            PARAMS['per_page'] = 296   # till 2025-12-30, there are 296 economies (including regions)
            r = requests.get(url, params = PARAMS, headers = HDR)
            r.raise_for_status()
            ldict = r.json()[1]
            df = pl.from_dicts(ldict)
        lconds = []   # list of conditions
        if name is not None:
            lconds.append(pl.col('name').str.contains(f'(?i){name}'))   # case-insensitive
        if region is not None:
            lconds.append(pl.col('region').struct.field('id') == region)
        if incomelevel is not None:
            lconds.append(pl.col('incomeLevel').struct.field('id') == incomelevel)
        if lendtype is not None:
            lconds.append(pl.col('lendingType').struct.field('id') == lendtype)
        if excludeaggs:
            lconds.append(pl.col('region').struct.field('value') != 'Aggregates')
        # combine all conditions with AND
        conds = lconds[0]
        for cond in lconds[1:]:
            conds = conds & cond
        res = df.filter(conds)
        return res    
    def queryinds(self, *, name: str = None, source: str = None, topic: str = None, fromcache: bool = True) -> pl.DataFrame:
        '''
        Query wb indicators
        **Parameters**
        - name: querying pattern on indicator name, e.g. 'GDP'
        - source: querying on source id, e.g. '2' ('World Development Indicators)
        - topic: querying on topic id, e.g. '3' (Economy & Growth)
        NB: At least one of the above three querying conditions are NOT None!
        - fromcache: if True, read from local file
        **Returns**: dict
        **Example**
        from wbdata import WB
        wb = WB()
        wb.queryinds(name = 'GDP Per Capita')
        '''
        assert (name is not None) or (source is not None) or (topic is not None), 'specify at least one parameter'
        if fromcache:
            with files('wbdata').joinpath('asset', 'indicators.json').open('rb') as f:
                df = pl.read_ndjson(f)
        else:
            url = f'{HOST}/indicator'
            PARAMS['per_page'] = 30000   # till 2025-12-30, there are 29323 indicators
            r = requests.get(url, params = PARAMS, headers = HDR)
            r.raise_for_status()
            ldict = r.json()[1]
            df = pl.from_dicts(ldict)
        lconds = []   # list of conditions
        if name is not None:
            lconds.append(pl.col('name').str.contains(f'(?i){name}'))   # case-insensitive
        if source is not None:
            lconds.append(pl.col('source').struct.field('id') == source)
        if topic is not None:
            lconds.append(pl.col('topic').struct.field('id') == topic)
        # combine all conditions with AND
        conds = lconds[0]
        for cond in lconds[1:]:
            conds = conds & cond
        res = df.filter(conds)
        return res
    def getdata(self, indicator: str, economies: str = None, *, period: str = None, mrv: int = None, mrnev: int = None, per_page: int = 10000) -> pl.DataFrame:
        '''
        Retrieving series data
        **Parameters**
        - indicator: indicator id
        - economy: economy id, separated with semicolon if multiple economies. If None, all economies.
          e.g. 'CHN' (China), 'CHN;IND' (China & India)
        - period: e.g. '2018:2022', '2018Q1:2022Q4', '2018M01:2022M12', '2022', '2022M12', '2022Q1'
        - mrv: most recent values. e.g. `mrv=10` means 10 years for annual data, 10 quarters for quarterly data, etc.
        - mrnev: most recent non-empty values
        **NB**: period, mrv and mrnev are mutually exclusive
        - per_page: number of records per page
        **Returns**: DataFrame
        **Example**
        from wbdata import WB
        wb = WB()
        wb.getdata('NY.GDP.MKTP.KD', 'CHN', period = '2020:2024')
        '''
        assert (period is not None) ^ (mrv is not None) ^ (mrnev is not None), 'period, mrv, mrnev are exclusive'
        if economies is None:
            economies = 'all'
        url = f'{HOST}/country/{economies}/indicator/{indicator}'
        if period is not None:
            PARAMS['date'] = period
        if mrv is not None:
            PARAMS['mrv'] = mrv
        if mrnev is not None:
            PARAMS['mrnev'] = mrnev
        PARAMS['per_page'] = per_page
        r = requests.get(url, params = PARAMS, headers = HDR)
        r.raise_for_status()
        df = pl.from_dicts(r.json()[1])
        df = df.select(
            pl.col('countryiso3code').alias('economy'),
            pl.col('date', 'value')
        ).sort(['economy', 'date'])
        return df
