# import sys
# import os
import datetime as dt
from dateutil.relativedelta import relativedelta
import dash
from dash import Dash, dcc, html  # , callback
from dash.dash_table import DataTable
from dash.dash_table.Format import Format, Scheme  # , Trim
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
#
import StkPxGetData as PxAPI
import SA_Const as Const


def get_RSI(df, period=14, oBought=70, oSold=30):
    delta = df['Close'].diff()
    gain = delta.where(delta>0, 0)
    loss = delta.where(delta<0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    RS = avg_gain / abs(avg_loss)
    RSI = (100 - (100/(1+abs(RS))))
    df['RSI'] = RSI
    df['RSIOB'] = np.NAN
    df['RSIOS'] = np.NAN
    for ix in range(1, len(df)):
        if df['RSI'].iloc[ix] >= oBought and df['RSI'].iloc[ix - 1] < oBought:
            df['RSIOB'].iloc[ix] = df['Close'].iloc[ix]
        if df['RSI'].iloc[ix] <= oSold and df['RSI'].iloc[ix - 1] > oSold:
            df['RSIOS'].iloc[ix] = df['Close'].iloc[ix]
    #
    return df

pxdf = pd.DataFrame()
#
app = Dash(__name__, external_stylesheets=Const.external_stylesheets)
server = app.server  #  For deployment to on render
#
ticker1_input = html.Div(dbc.Row(
    [
        dbc.Col(children=[
            dbc.Label('Ticker:', html_for='ticker1-input',
                      className='fw-bold pt-5'
                      )],
            width=4
        ),
        dbc.Col(
            children=[
                dbc.Input(
                    type='text', id='ticker1-input',
                    placeholder='Ticker - ex. AAPL', required=True, debounce=True,
                    class_name='fw-bold'
                )
            ],
                 className='pt-5',
            width=8
            )
    ]
))
ticker2_input = html.Div(
    dbc.Row(children=
        [
            dbc.Col(children=[
                dbc.Label('2nd Ticker:', html_for='ticker2-input',
                          className='bg-lightblue fw-bold'
                          )],
                width=4
            ),
            dbc.Col(children=[
                dbc.Input(type='text', id='ticker2-input',
                          placeholder='Ticker - ex. MSFT', debounce=True,
                          class_name='fw-bold')
            ],
                width=8
        ),
    ], className='pt-3'))
#
EODPrice_input = html.Div(dbc.Row(children=[
        dbc.Col(children=[
            dbc.Label('EOD/Hourly Price:', html_for='EODPx-input',
                      className='fw-bold'
                      )],
                width=4
                ),
        dbc.Col(children=[
            dcc.Dropdown({'1d': 'End-Of-Day Price',
                          '1h': 'Hourly Price',
                          '15m': '15 minute interval Price',
                          '5m': '5 minute interval Price'
                          },
                         '1d',
                         id='EODPx-input',
                         clearable=False,
                         className='fw-bold')],
                width=8
                ),
    ],
    className='me-2 pt-3'
))
#
index_selection = html.Div(dbc.Row(
    children=[
        dbc.Col(
            children=[
                dbc.Label('Index for Comparison:', html_for='index-selection',
                          className='fw-bold'
                          )],
            width=4
        ),
        dbc.Col(
            children=[
                dcc.Dropdown({'': 'No Index',
                                    '^DJI': 'Dow Jones Industrials',
                                    '^GSPC': 'S&P 500',
                                    '^IXIC': 'NASDAQ Composite',
                                    '^RUT': 'Russell 1000'},
                               '',
                               id='index-selection',
                               clearable=False,
                               className='fw-bold')],
            width=8)],
    className='me-2 pt-3'
))
#
strtEnd_Dte_Input = html.Div(dbc.Row(children=[
    dbc.Label('Price dates', html_for='strtEndDte-date',
              class_name='fw-bold'),
    dbc.Col(children=[
        dcc.DatePickerRange(
            start_date=(dt.datetime.today() - relativedelta(days=Const.dfltstrt)),
            end_date=dt.datetime.today(),
            min_date_allowed=(dt.datetime.today() - relativedelta(years=Const.nbryears)),
            max_date_allowed=dt.datetime.today(),
            updatemode='singledate',
            day_size=33,
            clearable=False,
            display_format='D MMM Y',
            minimum_nights=Const.minNights,
            className='fw-bold fst-italic',
            # style={'font-weight': 'bold',
            #        'fontSize': '8'},
            id='strtend-date'
        )], width=12
    )],
    className='me-3 pt-3',
))
#
mainInfo = html.Div([
        dbc.Button('', id="mainInfoBtn",
             size='sm',
             className='bi bi-info-lg fw-bold mx-auto',
             style={'border-radius': '15px'}),
])
#
mainsubmbtn = html.Div(
    dbc.Row(
        children=[
            dbc.Col(width=4),
            dbc.Col(
                children=[
                    dbc.Button("Generate Analysis", id="mainbtn",
                               size='sm',
                               className='mb-2 br-lightblue fw-bold me-2',
                               style={'border-radius': '5px'})],
                width=8
            )
        ], className='pt-5', justify='center',
    ))
#
selcard = dbc.Card([
                mainInfo,
                ticker1_input,
                ticker2_input,
                strtEnd_Dte_Input,
                index_selection,
                EODPrice_input,
                mainsubmbtn,
                dbc.Alert(Const.mainSelErrAlert,
                          id='selAlert',
                          color='danger',
                          dismissable=True,
                          is_open=False,),
                dbc.Alert(Const.mainInstrAlert,
                          id='mainInfo',
                          color='primary',
                          dismissable=True,
                          is_open=False,)
            ], body=True,)
#
stkpxtbl = DataTable(
    id='pxdtbl',
    columns=[
       dict(id='Trade Date', name='Trade Date'),
       dict(id='Ticker', name='Ticker'),
       dict(id='Name', name='Name'),
       dict(id='Close', name='Close', type='numeric',
            format=Format(precision=2, scheme=Scheme.fixed, group=True, groups=[3])),
       dict(id='Open', name='Open', type='numeric',
            format=Format(precision=2, scheme=Scheme.fixed, group=True, groups=[3])),
       dict(id='High', name='High', type='numeric',
            format=Format(precision=2, scheme=Scheme.fixed, group=True, groups=[3])),
       dict(id='Low', name='Low', type='numeric',
            format=Format(precision=2, scheme=Scheme.fixed, group=True, groups=[3])),
       dict(id='Volume', name='Volume', type='numeric',
            format=Format(precision=0, scheme=Scheme.fixed, group=True, groups=[3])
            )
    ],
    filter_action='native',
    sort_action='native',
    sort_mode='multi',
    page_action='native',
    page_current=0,
    page_size=20,
    style_data={'border': '1px solid grey',
                'color': 'black',
                'backgroundColor': 'lightgrey'
                },
    style_header={'border': '1px solid white',
                  'color': 'white',
                  'fontweight': 'bold',
                  'backgroundColor': 'black',
                  'textAlign': 'center'
                  },
    style_cell={
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': 0,
    },
    style_header_conditional=[
        {'if': {'column_id': 'Trade Date',
            }, 'textAlign': 'center'
        },
        {'if': {'column_id': 'Ticker',
            }, 'textAlign': 'center',
            'width': '5%'
        },
        {'if': {'column_id': 'Name',
            }, 'textAlign': 'center'
        }
    ],
    style_data_conditional=[
        {'if': {'column_id': 'Trade Date',
            }, 'textAlign': 'center'
        },
        {'if': {'column_id': 'Ticker',
            }, 'textAlign': 'center',
            'width': '5%'
        },
        {'if': {'column_id': 'Name',
            }, 'textAlign': 'center'
        }
    ],
    tooltip_duration=None
)
# Grid table filter layout
gridtblfilter = html.Div([
    dbc.Stack([
        dbc.Label('Date Range:', class_name='fw-bold'),
        html.Div([
            dcc.Dropdown(options={'test1': 'All dates', 'test2': 'Most recent only'},
                value='test2', id='gridDteRngSel', multi=False, clearable=False,
                className='fw-bold')], style={'width': '170px'},),
        dbc.Label('Ticker(s):', class_name='fw-bold'),
        dcc.Dropdown(options={},
                     value=[], id='gridTickerSel', multi=True, className='fw-bold'),
        dbc.Button('', id="gridBtn",
             size='sm',
             className='bi bi-info-lg fw-bold mx-auto',
             style={'border-radius': '15px'}),
    ],
        direction="horizontal",
        gap=3,),
    dbc.Alert(
        Const.gridAlertConst,
        id='gridAlert', color='light', dismissable=True,
        is_open=False, className='pt-5, cols=8'
    )
])
# Price/Volume filter layout
pxvolfilter = html.Div([
    dbc.Stack([
        dbc.Label('Ticker(s):', class_name='fw-bold'),
        dcc.Dropdown(options={},
                     value=[], id='pxvolTickerSel', multi=True, className='fw-bold'),
    ],
        direction="horizontal",
        gap=3,),
    dbc.Stack([
        dbc.Label('Moving Average Short - nbr periods:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='pxvolSMAShrtSel',
                      value=30, debounce=True, min=10, max=100, step=10,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('Moving Average long - nbr periods:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='pxvolSMAlongSel',
                      value=100, debounce=True, min=50, max=200, step=10,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('MA Type:', class_name='fw-bold'),
        html.Div([
            dcc.Dropdown(options={
                'SMA': 'Simple Moving Average',
                'EMA': 'Exponential Moving Average'
            },
                 value='EMA', id='pxvolMASel', multi=False, clearable=False, className='fw-bold w-100'),
            ],
            style={'width': '230px'},),
        dbc.Button('', id="pxvolBtn",
                   size='sm',
                   className='bi bi-info-lg fw-bold mx-auto',
                   style={'border-radius': '15px'}),
    ],
        direction="horizontal",
        className='pt-2',
        gap=3,),
    dbc.Alert(
        Const.pxvolAlertConst,
        id='pxvolAlert', color='light', dismissable=True,
        is_open=False, className='pt-5, cols=8'
    )
])
# Candlestick filter layout
csfilter = html.Div([
    dbc.Stack([
        dbc.Label('Moving Average - Nbr Periods:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='csSMAShrtSel',
                      value=30, debounce=True, min=10, max=500, step=10,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('Ticker(s):', class_name='fw-bold'),
        html.Div([
            dcc.Dropdown(options={},
                         value=[], id='csTickerSel', multi=False,
                         clearable=False,
                         className='fw-bold'),
            ],
            style={'width': '300px'},),
        dbc.Label('MA Type:', class_name='fw-bold'),
        html.Div([
            dcc.Dropdown(options={
                'SMA': 'Simple Moving Average',
                'EMA': 'Exponential Moving Average'
            },
                 value='EMA', id='csMASel', multi=False, clearable=False, className='fw-bold w-100'),
            ],
            style={'width': '230px'},),
        dbc.Button('', id="csBtn",
                   size='sm',
                   className='bi bi-info-lg fw-bold mx-auto',
                   style={'border-radius': '15px'}),
    ],
        direction="horizontal",
        className='pb-2',
        gap=3,),
    dbc.Stack([
        dbc.Label('RSI Number of Periods:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='csRSIPdSel',
                      value=14, debounce=True, min=2, max=30, step=1,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('RSI Overbought Indicator:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='csRSIOBSel',
                      value=70, debounce=True, min=30, max=90, step=1,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('RSI Oversold Indicator:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='csRSIOSSel',
                      value=30, debounce=True, min=5, max=70, step=1,
                      className='fw-bold')], style={'width': '75px'},),
    ],
        direction="horizontal",
        gap=3,),
    dbc.Alert(
        Const.csAlertConst,
        id='csAlert', color='light', dismissable=True,
        is_open=False, className='pt-5, cols=8'
    )
])
# Bollinger Band filter layout
bbfilter = html.Div([
    dbc.Stack([
        dbc.Label('Ticker:', class_name='fw-bold'),
        html.Div([
            dcc.Dropdown(options={},
                         value=[], id='bbTickerSel',
                         clearable=False,
                         className='fw-bold'),
            ],
            style={'width': '300px'},)
    ],
        direction="horizontal",
        gap=3,),
    dbc.Stack([
        dbc.Label('Moving Average - Nbr Periods:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='bbSMASel',
                      value=20, debounce=True, min=10, max=500, step=10,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('Std Deviation from SMA:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='bbSDSel',
                      value=2, debounce=True, min=.5, max=4, step=.1,
                      className='fw-bold')],
                 style={'width': '75px'},),
        dbc.Label('MA Type:', class_name='fw-bold'),
        html.Div([
            dcc.Dropdown(options={
                'SMA': 'Simple Moving Average',
                'EMA': 'Exponential Moving Average'
            },
                 value='SMA', id='bbMASel', multi=False, clearable=False, className='fw-bold w-100'),
            ],
            style={'width': '230px'},),
        dbc.Label('Close/Candlestick:', class_name='fw-bold'),
        html.Div([
            dcc.Dropdown(options={
                'Close': 'Closing Price',
                'CS': 'Candlestick Price'
            },
                 value='CS', id='bbPxSel', multi=False, clearable=False, className='fw-bold w-100'),
            ],
            style={'width': '230px'},),
        dbc.Button('', id='bbBtn',
                   size='sm',
                   className='bi bi-info-lg fw-bold mx-auto',
                   style={'border-radius': '15px'}),
    ],
        direction="horizontal",
        gap=3,),
    dbc.Stack([
        dbc.Label('RSI Number of Periods:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='bbRSIPdSel',
                      value=14, debounce=True, min=2, max=30, step=1,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('RSI Overbought Indicator:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='bbRSIOBSel',
                      value=70, debounce=True, min=30, max=90, step=1,
                      className='fw-bold')], style={'width': '75px'},),
        dbc.Label('RSI Oversold Indicator:', class_name='fw-bold'),
        html.Div([
            dbc.Input(type='number', id='bbRSIOSSel',
                      value=30, debounce=True, min=5, max=70, step=1,
                      className='fw-bold')], style={'width': '75px'},),
    ],
        direction="horizontal",
        gap=3,),
    dbc.Alert(
        Const.bbAlertConst,
        id='bbAlert', color='light', dismissable=True,
        is_open=False, className='pt-5, cols=8'
    )
])
#
tblcard = dbc.Card(
    html.Div([
        dbc.Row(
            dbc.Col(
                children=[
                    dbc.Accordion(
                        [dbc.AccordionItem(
                            [gridtblfilter],
                            title='Data Grid Parameters'
                        )], start_collapsed=True
                    ),
                    stkpxtbl
                ],
                width=12
            ), className='g-0',
        )
    ]), body=True,)
#
app.layout = dbc.Container(html.Div([
    dcc.Store(id='PxXtrStore', storage_type='memory'),
    dcc.Store(id='SelParamStoreGT', storage_type='memory'),
    dcc.Store(id='SelParamStorePV', storage_type='memory'),
    dcc.Store(id='SelParamStoreCS', storage_type='memory'),
    dcc.Store(id='SelParamStoreBB', storage_type='memory'),
    html.H4(children='Stock Price Trend Analysis', id='pgHdr',style={'textAlign': 'center'}),
    dcc.Tabs([
        dcc.Tab(label='Main', id='mainTab', style=Const.tab_style, selected_style=Const.tab_selected_style,
                children=[
                    dbc.Row([
                        dbc.Col([
                            selcard
                        ],
                            width=3, className='g-0'),
                        dbc.Col([
                            tblcard
                        ],
                            width=True),
                    ], className='g-0')
                ]),
        dcc.Tab(label='Price/Volume Chart', id='pxVolTab', style=Const.tab_style, selected_style=Const.tab_selected_style,
                children=[dbc.Row(html.H5('Price/Volume Chart'),
                                  style={'text-align': 'center'},
                                  justify='center'),
                          dbc.Accordion(
                                [dbc.AccordionItem(
                                    [pxvolfilter],
                                    title='Price/Volume Chart Parameters',
                                )], start_collapsed=True
                          ),
                          dcc.Graph(id='pxvolumechart',
                                    className='ms-1 me-2 mh-100')
                          ]),
        dcc.Tab(label='Candlestick Chart', id='candleTab', style=Const.tab_style, selected_style=Const.tab_selected_style,
                children=[dbc.Row(html.H5('Candlestick Chart'),
                                  style={'text-align': 'center'},
                                  justify='center'),
                          dbc.Accordion(
                                [dbc.AccordionItem(
                                    [csfilter],
                                    title='Candlestick Chart Parameters',
                                )], start_collapsed=True
                          ),
                          dcc.Graph(id='candlechart', className='ms-1 me-2 mh-100')
                      ]),
        dcc.Tab(label='Bollinger Band® Chart', id='bollBTab', style=Const.tab_style, selected_style=Const.tab_selected_style,
                children=[dbc.Row(html.H5('Bollinger Band® Chart'),
                                  style={'text-align': 'center'},
                                  justify='center'),
                          dbc.Accordion(
                            [dbc.AccordionItem(
                            [bbfilter],
                                title='Bollinger Band® Parameters',
                            )], start_collapsed=True
                          ),
                          dcc.Graph(id='bollingerchart', className='ms-1 me-2 mh-100')
                      ]),

    ], className='ms-1 me-2')
]), className='ms-1 me-2, mh-100', fluid=True, style={'height': 850})
#
app.title = 'Stock Analysis'


# Data stored - initiate callbacks for grid, and charts
@app.callback(
    Output('PxXtrStore', 'data'),
    Output('SelParamStoreGT', 'data'),
    Output('SelParamStorePV', 'data'),
    Output('SelParamStoreCS', 'data'),
    Output('SelParamStoreBB', 'data'),
    Output('selAlert', 'is_open'),
    Input('mainbtn', 'n_clicks'),
    Input('ticker1-input', 'value'),
    Input('ticker2-input', 'value'),
    Input('strtend-date', 'start_date'),
    Input('strtend-date', 'end_date'),
    Input('index-selection', 'value'),
    Input('EODPx-input', 'value'),
    prevent_initial_call=True
)
# Main selection callback
def mainselection(n_clicks, tkr1value, tkr2value, start_date_str, end_date_str, idxsel, eodpxvalue):
    #
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - mainselection')
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    # triggered on button click and ticker not blank
    if (tkr1value is None or tkr1value == '' or
        changed_id != 'mainbtn.n_clicks'):
        raise PreventUpdate
    #
    tkrlist = [tkr1value.strip().upper()]
    #
    if tkr2value != '' and tkr2value is not None:
        tkrlist.append(tkr2value.strip().upper())
    #
    if idxsel != '':
        tkrlist.append(idxsel)
    #
    stkPx = PxAPI.PxData()
    IdxSelected = False
    start_date = dt.date.fromisoformat(start_date_str[:10])
    end_date = dt.date.fromisoformat(end_date_str[:10])
    SelTkrOptions = {}
    for ix in range(0, len(tkrlist)):
        try:
            pxDF, stkNme = stkPx.GetPxData(tkrlist[ix],
                                           start_date,
                                           end_date,
                                           eodpxvalue)
        except Exception as error:
            # error Ticker is invalid
            print('GetPxData error-Ticker ',
                  tkrlist[ix], ' ',
                type(error).__name__)
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
        if ix == 0:
            pxDataDF = pxDF
        else:
            pxDataDF = pd.concat([pxDataDF, pxDF], ignore_index=False)
        #
        if len(pxDF) <= 1:
            # error Ticker/date range is invalid
            return dash.no_update, dash.no_update, True
        # create dictionary of ticker and stock name for use in subsequent filters
        SelTkrOptions.update({tkrlist[ix]: stkNme})
        if tkrlist[ix] in Const.idxList:
            IdxSelected = True
    #
    selData = {'SelTkrOption': SelTkrOptions,
               'SelTkrList': tkrlist,
               'IdxSelected': IdxSelected,
               'PxFreq': eodpxvalue}
    #
    return pxDataDF.to_dict('records'), selData, selData, selData, selData, dash.no_update
#
# Callback to initiate callback for grid
@app.callback(
    Output('gridTickerSel', 'options'),
    Output('gridTickerSel', 'value'),
    Output('gridDteRngSel', 'options'),
    Output('gridDteRngSel', 'value'),
    Input('PxXtrStore', 'data'),
    Input('SelParamStoreGT', 'data'),
    Input('SelParamStoreGT', 'modified_timestamp'),
    prevent_initial_call=True
)
# Initiate callbacks for grid
def triggerGT(PxXtrData, SelParamData, SelParamTS):
    #
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - triggerGT')
    if SelParamTS is None or SelParamData is None or PxXtrData is None:
        raise PreventUpdate
    #
    pxDataDF = pd.DataFrame.from_dict(PxXtrData)
    #
    SelTkrOption = SelParamData['SelTkrOption']
    SelTkrList = SelParamData['SelTkrList']
    # IdxSelected = SelParamData['IdxSelected']
    minTD = pxDataDF['Trade Date'].unique().min()[:10]
    maxTD = pxDataDF['Trade Date'].unique().max() # [:10]
    gridtbloptions = {minTD: 'All dates', maxTD: 'Most recent only'}
    #
    return SelTkrOption, SelTkrList, gridtbloptions, maxTD
#
# Callback to generate grid table based on filter
@app.callback(
    Output('pxdtbl', 'data'),
    Output('pxdtbl', 'tooltip_data'),
    # Input('gridBtn', 'n_clicks'),
    Input('gridDteRngSel', 'value'),
    Input('gridTickerSel', 'value'),
    State('PxXtrStore', 'data'),
    State('SelParamStoreGT', 'data'),
    prevent_initial_call=True
)
# Generate grid table based on filter
def showtbl(gridDteRngSel, gridTickerSel, PxXtrData, SelParam):
    #
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - showtbl')
    if (gridDteRngSel is None or gridDteRngSel == '' or
        gridTickerSel is None or gridTickerSel == ''):
        raise PreventUpdate
    #
    pxDataDF = pd.DataFrame.from_dict(PxXtrData)
    #
    pxDataDF['Trade Dte'] = pd.to_datetime(pxDataDF['Trade Date'])
    #
    gridTBDF1 = pxDataDF[pxDataDF['Ticker'].isin(gridTickerSel)]
    gridTBDF = gridTBDF1[gridTBDF1['Trade Dte'] >= pd.to_datetime(gridDteRngSel)]
    gridTBDF['Trade Date'] = gridTBDF['Trade Date'].replace('T', ' ')
    #
    ttData = [
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in gridTBDF.to_dict('records')
    ]
    #
    return gridTBDF.to_dict('records'), ttData
#
# Data stored - initiate callbacks for price/volume chart
@app.callback(
    Output('pxvolTickerSel', 'options'),
    Output('pxvolTickerSel', 'value'),
    Input('SelParamStorePV', 'data'),
    Input('SelParamStorePV', 'modified_timestamp'),
    prevent_initial_call=True
)
# Initiate callbacks for price/volume chart
def triggerPV(SelParamData, SelParamTS):
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - triggerPV')
    #
    if SelParamTS is None or SelParamData is None:
        raise PreventUpdate
    #
    SelTkrOption = SelParamData['SelTkrOption']
    SelTkrList = SelParamData['SelTkrList']
    #
    return SelTkrOption, SelTkrList
#
# Price/Volume Chart filter - callbacks to generate Price Volume Chart based on filter
@app.callback(
    Output('pxvolumechart', 'figure'),
    Input('pxvolTickerSel', 'value'),
    Input('pxvolSMAShrtSel', 'value'),
    Input('pxvolSMAlongSel', 'value'),
    Input('pxvolMASel', 'value'),
    State('PxXtrStore', 'data'),
    State('SelParamStorePV', 'data'),
    prevent_initial_call=True
)
# generate price/volume chart base on filter
def showPVChart(pxvolTickerSel, pxvolSMAShrtSel, pxvolSMAlongSel, pxvolMASel, PxXtrData, SelParamStorePV):
    #
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - show pvchart')
    if (pxvolTickerSel is None or pxvolTickerSel == '' or
        pxvolSMAShrtSel is None or pxvolSMAShrtSel == '' or int(pxvolSMAShrtSel) == 0 or
        pxvolSMAlongSel is None or pxvolSMAlongSel == '' or int(pxvolSMAlongSel) == 0):
        raise PreventUpdate
    #
    pxDataDF = pd.DataFrame.from_dict(PxXtrData)
    pxDataDF['Trade Dte'] = pd.to_datetime(pxDataDF['Trade Date'])
    pxDataDF.set_index('Trade Dte',drop=True, inplace=True)
    #
    chartTitle = ''
    pxvolfig = make_subplots(specs=[[{"secondary_y": True}]])
    for ix in range(0, len(pxvolTickerSel)):
        pvDF = pxDataDF[pxDataDF['Ticker'] == pxvolTickerSel[ix]]
        stknme = pvDF['Name'].unique()[0]
        if ix > 0:
            chartTitle = chartTitle + ' / '
        chartTitle = chartTitle + stknme
        #
        if pxvolTickerSel[ix] in Const.idxList and ix > 0:
            sec_Y=True
        else:
            sec_Y=False
        #
        if pxvolMASel == 'SMA':
            pvDF['smaShrt'] = pvDF['Close'].rolling(window=pxvolSMAShrtSel).mean().dropna()
            pvDF['smaLong'] = pvDF['Close'].rolling(window=pxvolSMAlongSel).mean().dropna()
        else:
            pvDF['smaShrt'] = pvDF['Close'].ewm(span=pxvolSMAShrtSel).mean().dropna()
            pvDF['smaLong'] = pvDF['Close'].ewm(span=pxvolSMAlongSel).mean().dropna()
        # Trend Line (Linear Regression Line)
        par = np.polyfit(range(len(pvDF.index.values)), pvDF['Close'].values, 1, full=True)
        slope = par[0][0]
        intercept = par[0][1]
        Uy_pred = [slope * i + intercept for i in range(len(pvDF.index))]
        # Volume plot - only when there are no index ticker selected and not mutual fund
        if not SelParamStorePV['IdxSelected'] and pvDF['Volume'].max() > 0:
            pxvolfig.add_trace(go.Bar(x=pvDF.index,
                              y=pvDF['Volume'],
                              opacity=0.3,
                              text=stknme,
                              name=(pxvolTickerSel[ix] + ' Volume')
                              ), secondary_y=True)
        # SMA short plot
        pxvolfig.add_trace(go.Scatter(x=pvDF.index,
                          y=pvDF['smaShrt'],
                          text=stknme,
                          name=(pxvolTickerSel[ix] + ' ' + str(pxvolSMAShrtSel) + ' Period ' + pxvolMASel)
                         ), secondary_y=sec_Y)
        # SMA Long plot
        pxvolfig.add_trace(go.Scatter(x=pvDF.index,
                          y=pvDF['smaLong'],
                          text=stknme,
                          name=(pxvolTickerSel[ix] + ' ' + str(pxvolSMAlongSel) + ' Period ' + pxvolMASel)
                         ), secondary_y=sec_Y)
        # Trend Line plot
        pxvolfig.add_trace(go.Scatter(x=[pvDF.index[0], pvDF.index[-1]],
                          y=[Uy_pred[0], Uy_pred[-1]],
                          mode='lines+markers',
                          text=stknme,
                          name=(pxvolTickerSel[ix] + ' Trend Line')
                         ), secondary_y=sec_Y)
        # Close plot
        pxvolfig.add_trace(go.Scatter(x=pvDF.index,
                          y=pvDF['Close'],
                          mode='lines+markers',
                          name=(pxvolTickerSel[ix] + ' Close'),
                          text=stknme
                         ), secondary_y=sec_Y)
        #
    pxvolfig.update_layout(dict(title=('<b>' + chartTitle + ' - Price & Volume</b>'),
                                xaxis_title='<b>Trade Date</b>',
                                yaxis_title='<b>Price</b>',
                                height=750,
                                paper_bgcolor='lightblue',
                                legend=(dict(entrywidth=0, bgcolor='white'))
                            ))
    #
    if SelParamStorePV['IdxSelected']:
        pxvolfig.update_yaxes(title_text="<b>Index Price</b>", secondary_y=True)
    else:
        pxvolfig.update_yaxes(title_text="<b>Volume</b>", secondary_y=True)
    pxvolfig.update_xaxes(showspikes=True)
    pxvolfig.update_yaxes(showspikes=True)
    #
    return pxvolfig
#
# Data stored - initiate callbacks for Candlestick chart
@app.callback(
    Output('csTickerSel', 'options'),
    Output('csTickerSel', 'value'),
    Input('SelParamStoreCS', 'data'),
    Input('SelParamStoreCS', 'modified_timestamp'),
    prevent_initial_call=True
)
# trigger callback for Candlestick chart
def triggerCS(SelParamData, SelParamTS):
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - triggercs')
    #
    if SelParamTS is None or SelParamData is None:
        raise PreventUpdate
    #
    SelTkrOption = SelParamData['SelTkrOption']
    SelTkrList = SelParamData['SelTkrList'][0]
    #
    return SelTkrOption, SelTkrList
#
# Candlestick Chart filter - callbacks to generate Candlestick Chart based on filter
@app.callback(
    Output('candlechart', 'figure'),
    Input('csTickerSel', 'value'),
    Input('csSMAShrtSel', 'value'),
    Input('csMASel', 'value'),
    Input('csRSIPdSel', 'value'),
    Input('csRSIOBSel', 'value'),
    Input('csRSIOSSel', 'value'),
    State('PxXtrStore', 'data'),
    prevent_initial_call=True
)
# Generate Candlestick chart
def showCSChart(csTickerSel, csSMAShrtSel, csMASel, csRSIPdSel, csRSIOBSel, csRSIOSSel, PxXtrData):
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - showcschart')
    #
    if csTickerSel is None or csTickerSel == '':
        raise PreventUpdate
    #
    pxDataDF = pd.DataFrame.from_dict(PxXtrData)
    pxDataDF['Trade Dte'] = pd.to_datetime(pxDataDF['Trade Date'])
    pxDataDF.set_index('Trade Dte',drop=True, inplace=True)
    #
    chartTitle = ''
    oBought = csRSIOBSel
    oSold = csRSIOSSel
    csfig = make_subplots(rows=2, cols=1,
                          vertical_spacing=0.05,
                          row_heights=[0.75, 0.25],
                          subplot_titles=(
                              None,
                              '<b>Relative Strength Index</b>',
                          ),
                          shared_xaxes=True)
    # for ix in range(0, len(csTickerSel)):
    csDF = pxDataDF[pxDataDF['Ticker'] == csTickerSel]
    stknme = csDF['Name'].unique()[0]
    RSIdf = get_RSI(csDF, csRSIPdSel, csRSIOBSel, csRSIOSSel)
    # if ix > 0:
    #     chartTitle = chartTitle + ' / '
    chartTitle = stknme
    #
    if csMASel == 'SMA':
        csDF['smaShrt'] = csDF['Close'].rolling(window=csSMAShrtSel).mean().dropna()
    else:
        csDF['smaShrt'] = csDF['Close'].ewm(span=csSMAShrtSel).mean().dropna()
    #
    downcrossover = (
        csDF[((csDF['Close'] <= csDF['smaShrt']) *
                   (csDF['Close'].shift(-1) <= csDF['smaShrt'].shift(-1)) *
                   (csDF['Close'].shift(1) >= csDF['smaShrt'].shift(1)))])
    upcrossover = (
        csDF[((csDF['Close'] >= csDF['smaShrt']) *
                   (csDF['Close'].shift(-1) >= csDF['smaShrt'].shift(-1)) *
                   (csDF['Close'].shift(1) <= csDF['smaShrt'].shift(1)))])
    # candlestick plot
    csplot = go.Candlestick(dict(x=csDF.index,
                            close=csDF['Close'],
                            open=csDF['Open'],
                            high=csDF['High'],
                            low=csDF['Low'],
                            text=stknme,
                            name=(csTickerSel + ' - Candlestick')))
    # SMA plot
    csSMAplot = go.Scatter(dict(x=csDF.index,
                           y=csDF['smaShrt'],
                           text=stknme,
                           opacity=0.5,
                           name=(csTickerSel + ' ' + str(csSMAShrtSel) + ' Periods ' + csMASel)
                                ))
    # upside cross over plot
    csUpXo = go.Scatter(dict(x=upcrossover.index,
                        y=upcrossover['Close'],
                        mode='markers',
                        marker=dict(size=8, symbol="triangle-up-open", color='black',
                                    line=dict(width=3, color="black")),
                        name=(csTickerSel + ' Up-Cosssover'),
                        text=stknme
                             ))
    # downside cross over plot
    csDwnXo = go.Scatter(dict(x=downcrossover.index,
                         y=downcrossover['Close'],
                         mode='markers',
                         marker=dict(size=8, symbol="triangle-down-open", color='blue',
                                     line=dict(width=3, color="yellow")),
                         name=(csTickerSel + ' Down-Crossover'),
                         text=stknme
                              ))
    #  RSI - Over bought plot
    csRSIOb = go.Scatter(dict(x=RSIdf.index,
                         y=RSIdf['RSIOB'],
                         text=stknme,
                         mode='markers',
                         marker=dict(size=8),
                         # marker=dict(size=8, color='red'), symbol="triangle-down-open"),
                         name=(csTickerSel + ' RSI Over Bought')
                              ))
    #  RSI - Over sold plot
    csRSIOs = go.Scatter(dict(x=RSIdf.index,
                         y=RSIdf['RSIOS'],
                         text=stknme,
                         mode='markers',
                         marker=dict(size=8),
                         # marker=dict(size=8, color='green'), symbol="triangle-up-open"),
                         name=(csTickerSel + ' RSI Over Sold')
                              ))
    csfig.add_trace(csplot, row=1, col=1)
    csfig.add_trace(csSMAplot, row=1, col=1)
    csfig.add_trace(csUpXo, row=1, col=1)
    csfig.add_trace(csDwnXo, row=1, col=1)
    csfig.add_trace(csRSIOb, row=1, col=1)
    csfig.add_trace(csRSIOs, row=1, col=1)
    #  RSI plot
    csRSI = go.Scatter(dict(x=RSIdf.index,
                       y=RSIdf['RSI'],
                       text=stknme,
                       name=(csTickerSel + ' RSI')
                      ))
    # RSI overbought line
    csRSIOBl = go.Scatter(dict(x=[RSIdf.index[0], RSIdf.index[-1]],
                          y=[oBought, oBought],
                          text=stknme,
                          line={'color': 'green'},
                          opacity=0.4,
                          name='RSI Over Bought Line'
                         ))
    # RSI overbought line
    csRSIOSl = go.Scatter(dict(x=[RSIdf.index[0], RSIdf.index[-1]],
                          y=[oSold, oSold],
                          text=stknme,
                          line={'color': 'red'},
                          opacity=0.4,
                          name='RSI Over Sold Line'
                         ))
    csfig.add_trace(csRSI, row=2, col=1)
    csfig.add_trace(csRSIOBl, row=2, col=1)
    csfig.add_trace(csRSIOSl, row=2, col=1)
    #
    csfig.update_layout(dict(title=('<b>'+chartTitle + ' - Candlestick Chart</b>'),
                             yaxis_title='<b>Price</b>',
                             height=750,
                             paper_bgcolor='lightblue',
                             xaxis_rangeslider_visible=False,
                             legend=(dict(entrywidth=0, bgcolor='white'))
                          ))
    #
    csfig.update_yaxes(showspikes=True)
    csfig.update_xaxes(showspikes=True)
    csfig.update_xaxes(title='<b>Trade Date</b>', row=2, col=1)
    #
    return csfig
#
# Data stored - initiate callbacks for Candlestick chart
@app.callback(
    Output('bbTickerSel', 'options'),
    Output('bbTickerSel', 'value'),
    Input('SelParamStoreBB', 'data'),
    Input('SelParamStoreBB', 'modified_timestamp'),
    prevent_initial_call=True
)
# trigger callback for Bollinger Band chart
def triggerBB(SelParamData, SelParamTS):
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - triggerBB')
    #
    if SelParamTS is None or SelParamData is None:
        raise PreventUpdate
    #
    SelTkrOption = SelParamData['SelTkrOption']
    SelTkrList = SelParamData['SelTkrList']
    #
    return SelTkrOption, SelTkrList[0]
#
# Bollinger Band Chart
@app.callback(
    Output('bollingerchart', 'figure'),
    Input('bbTickerSel', 'value'),
    Input('bbSMASel', 'value'),
    Input('bbSDSel', 'value'),
    Input('bbMASel', 'value'),
    Input('bbPxSel', 'value'),
    Input('bbRSIPdSel', 'value'),
    Input('bbRSIOBSel', 'value'),
    Input('bbRSIOSSel', 'value'),
    State('PxXtrStore', 'data'),
    prevent_initial_call=True
)
# Generate Bollinger Band chart based on filter
def showBBChart(bbTickerSel, bbSMASel, bbSDSel, bbMASel, bbPxSel, bbRSIPdSel, bbRSIOBSel, bbRSIOSSel, PxXtrData):
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - showBBchart')
    #
    if bbTickerSel is None or bbTickerSel == '':
        raise PreventUpdate
    #
    oBought = bbRSIOBSel
    oSold = bbRSIOSSel
    #
    pxDataDF = pd.DataFrame.from_dict(PxXtrData)
    pxDataDF['Trade Dte'] = pd.to_datetime(pxDataDF['Trade Date'])
    #
    bbDF = pxDataDF[pxDataDF['Ticker'] == bbTickerSel]
    bbDF.set_index('Trade Dte',drop=True, inplace=True)
    stknme = bbDF['Name'].unique()[0]
    chartTitle = stknme
    RSIdf = get_RSI(bbDF, bbRSIPdSel, oBought, oSold)
    #
    df = bbDF['Close'].to_frame()
    # Bollinger Band calculations
    # Calculate SMA
    # Calculate standard deviation
    if bbMASel == 'SMA':
        sma = df.rolling(window=bbSMASel).mean().dropna()
        rstd = df.rolling(window=bbSMASel).std().dropna()
    else:
        sma = df.ewm(span=bbSMASel).mean().dropna()
        rstd = df.ewm(span=bbSMASel).std().dropna()
    # Calculate upper band (range) - sma + 'n' times standard deviation
    upper_band = sma + (bbSDSel * rstd)
    # Calculate lower band (range) - sma - 'n' times standard deviation
    lower_band = sma - (bbSDSel * rstd)
    #
    upper_band = upper_band.rename(columns={'Close': 'upper'})
    upper_band = upper_band.dropna()
    lower_band = lower_band.rename(columns={'Close': 'lower'})
    lower_band = lower_band.dropna()
    # combine dataframes
    bb = bbDF.join(upper_band).join(lower_band)
    # bb = bb.dropna()
    #
    buyers = bb[bb['Close'] <= bb['lower']]
    sellers = bb[bb['Close'] >= bb['upper']]
    #
    # bbfig = go.Figure()
    bbfig = make_subplots(rows=2, cols=1,
                          vertical_spacing=0.05,
                          row_heights=[0.75, 0.25],
                          subplot_titles=(
                              None,
                              '<b>Relative Strength Index</b>',
                          ),
                          shared_xaxes=True)
    #
    bbLowerB = go.Scatter(dict(x=lower_band.index,
                               y=lower_band['lower'],
                               name='Lower Band',
                               line={'color': 'black'}
                               ))
    #
    bbUpperB = go.Scatter(dict(x=upper_band.index,
                               y=upper_band['upper'],
                               name='Upper Band',
                               fill='tonexty',
                               fillcolor='rgba(173,204,255,0.2)',
                               line={'color': 'black'}
                               ))
    #
    if bbPxSel == 'Close':
        bbClose = go.Scatter(dict(x=bbDF.index,
                                  y=bbDF['Close'],
                                  name='Close',
                                 opacity=0.5,
                                  # line={'color': '#636EFA'}
                                  ))
    else:
    # candlestick plot
        bbClose = go.Candlestick(dict(x=bbDF.index,
                                 close=bbDF['Close'],
                                 open=bbDF['Open'],
                                 high=bbDF['High'],
                                 low=bbDF['Low'],
                                 text=stknme,
                                 opacity=0.6,
                                 name=(bbTickerSel + ' - Candlestick')))
    #
    bbMA = go.Scatter(dict(x=sma.index,
                           y=sma['Close'],
                           name=('{} Period {}'.format(str(bbSMASel), bbMASel)),
                           # line={'color': '#FECB52'}
                           ))
    #
    bbBuyer = go.Scatter(dict(x=buyers.index,
                              y=buyers['Close'],
                              name='Buyers',
                              mode='markers',
                              marker=dict(
                                 color='#00CC96',
                                 size=10,
                                 )
                              ))
    #
    bbSeller = go.Scatter(dict(x=sellers.index,
                               y=sellers['Close'],
                               name='Sellers',
                               mode='markers',
                               marker=dict(
                                    color='#EF553B',
                                    size=10,
                                     )
                                ))
    #
    bbfig.add_trace(bbLowerB, row=1, col=1)
    bbfig.add_trace(bbUpperB, row=1, col=1)
    bbfig.add_trace(bbClose, row=1, col=1)
    bbfig.add_trace(bbMA, row=1, col=1)
    bbfig.add_trace(bbBuyer, row=1, col=1)
    bbfig.add_trace(bbSeller, row=1, col=1)
    #  RSI plot
    bbRSI = go.Scatter(dict(x=RSIdf.index,
                       y=RSIdf['RSI'],
                       text=chartTitle,
                       # yaxis='y2',
                       name=(bbTickerSel + ' RSI')
                       ))
    # RSI overbought line
    bbRSIOBl = go.Scatter(dict(x=[RSIdf.index[0], RSIdf.index[-1]],
                          y=[oBought, oBought],
                          text=chartTitle,
                          line={'color': 'green'},
                          opacity=0.4,
                          # yaxis='y2',
                          name='RSI Over Bought'
                          ))
    # RSI overbought line
    bbRSIOSl = go.Scatter(dict(x=[RSIdf.index[0], RSIdf.index[-1]],
                          y=[oSold, oSold],
                          text=chartTitle,
                          line={'color': 'red'},
                          opacity=0.4,
                          # yaxis='y2',
                          name='RSI Over Sold'
                          ))
    bbfig.add_trace(bbRSI, row=2, col=1)
    bbfig.add_trace(bbRSIOBl, row=2, col=1)
    bbfig.add_trace(bbRSIOSl, row=2, col=1)
    #
    bbfig.update_layout(
        dict(title=('<b>{} - Bollinger Band® Chart (Std Deviation - {}x)</b>'.format(chartTitle,str(bbSDSel))),
             # xaxis_title='<b>Trade Date</b>',
             yaxis_title='<b>Price</b>',
             height=750,
             paper_bgcolor='lightblue',
             xaxis_rangeslider_visible=False,
             legend=(dict(entrywidth=0, bgcolor='white'))
             ))
    bbfig.update_xaxes(showspikes=True)
    bbfig.update_yaxes(showspikes=True)
    bbfig.update_xaxes(title='<b>Trade Date</b>', row=2, col=1)
    #
    return bbfig
#
# Callback to display alert
@app.callback(
    Output('mainInfo', 'is_open'),
    Output('gridAlert', 'is_open'),
    Output('pxvolAlert', 'is_open'),
    Output('csAlert', 'is_open'),
    Output('bbAlert', 'is_open'),
    Input('mainInfoBtn', 'n_clicks'),
    Input('gridBtn', 'n_clicks'),
    Input('pxvolBtn', 'n_clicks'),
    Input('csBtn', 'n_clicks'),
    Input('bbBtn', 'n_clicks'),
    prevent_initial_call=True
)
# Callback to display the requested info alert
def triggerAlert(mainInfoBtn, gridBtn, pxvoklBtn, csBtn, bbBtn):
    print(dt.datetime.now().strftime('%d%b%Y-%H:%M:%S.%f') + ' - trigger Alert')
    #
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    #
    # match changed_id:
    if changed_id == 'mainInfoBtn.n_clicks':
        return True, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    elif changed_id == 'gridBtn.n_clicks':
        return dash.no_update, True, dash.no_update, dash.no_update, dash.no_update
    elif changed_id == 'pxvolBtn.n_clicks':
        return dash.no_update, dash.no_update, True, dash.no_update, dash.no_update
    elif changed_id == 'csBtn.n_clicks':
        return dash.no_update, dash.no_update, dash.no_update, True, dash.no_update
    elif changed_id == 'bbBtn.n_clicks':
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, True
    else:
        raise PreventUpdate
#

if __name__ == "__main__":
    app.run_server(debug=True)
