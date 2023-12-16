# get stock price data for analysis using Yahoo Finance
import datetime as dt
# import pandas
# import calendar
import yfinance as yf

import requests as _requests
from yfinance.const import _BASE_URL_

try:
    import ujson as _json
except ImportError:
    import json as _json

user_agent_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


def get_all_by_isin(isin, proxy=None, session=None):
    #
    session = session or _requests
    url = f"{_BASE_URL_}/v1/finance/search?q={isin}"
    try:
        data = session.get(url=url, proxies=proxy, headers=user_agent_headers)
        # data.raise_for_status()
    except Exception as error:
        print('get error: ',
              type(error).__name__)
        return (isin + '-unable to get name')
    #
    data = data.json()
    # print(data)
    for ix in range(0, data.get('count')):
        ticker = data.get('quotes', [{}])[ix]
        if isin == ticker['symbol']:
            break
    #
    return ticker['longname']


class PxData:

    def __init__(self):
        super().__init__()
    def GetPxData(self, stkData, strtDte, endDte, interVal='1d'):
        # if interVal == None:
        #     intv = '1d'
        # else:
        intv = interVal
        #
        try:
            tkr = yf.Ticker(stkData)
        except Exception as error:
            print('yfinance error-Ticker ',
                type(error).__name__)
            return -1
        else:
            try:
                pxDataDF = tkr.history(start=strtDte,
                                       end=(dt.datetime.combine(endDte, dt.time(19,0))),
                                       interval=intv,
                                       prepost=True,
                                       actions=False)
            except Exception as error:
                print('Error in get history-{} , {} , {} , {} error:'.format(stkData,strtDte, endDte, intv),
                      type(error).__name__)
                raise Exception('YFinance-GetHistoryError')
                # pxDataDF = tkr.history(start=strtDte,end=dt.datetime.today(),prepost=False, actions=False)
            pxDataDF.index = pxDataDF.index.tz_localize(None)
            pxDataDF['Ticker'] = stkData
            pxDataDF['Trade Date'] = pxDataDF.index
            try:
                stkNme = get_all_by_isin(stkData)
                # stkNme = data['longname']
            except Exception as error:
                print('yfinance error-Info ',
                    type(error).__name__)
                stkNme = stkData + '-unable to get name'
            #
            pxDataDF['Name'] = stkNme
            return pxDataDF, stkNme
    #
