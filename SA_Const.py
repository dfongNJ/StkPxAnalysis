from dash import html
import dash_bootstrap_components as dbc

# Main instructions description
mainInstrAlert = html.Div([
            html.H5('Stock Trend Analysis', className='fw-bold text-black text-center'), html.Br(),
            'Purpose of this app is to allow the user to visualize potential trend(s) of security prices.', html.Br(),
            html.B('The analysis provides for:'), html.Br(), html.Br(),
            html.B('Grid Data Table:'), html.Br(),
            html.Ul([
                html.Li('Price extract for specified period (default/initial: most recent period)'),
            ]),
            html.B('Price/Volume Chart:'), html.Br(),
            html.Ul([
                html.Li('Closing price movement'),
                html.Li('Trading volume'),
                html.Li(['Moving average (',
                         html.Span('simple',id='ttSMA'),
                         '/',
                         html.Span('exponential',id='ttEWMA'),
                         ') movement (long and short range averages)']),
                html.Li('Trend line (predictive) analysis'),
            ]),
            html.B('Candlestick Chart:'), html.Br(),
            html.Ul([
                html.Li([html.Span('Candlestick', id='ttcs'),
                         ' (Open/High/Low/Close) price analysis.']),
                html.Li('Moving average (simple/exponential) movement (long and short range averages)'),
                html.Li('Relative Strength Index', id='ttRSI'),
                html.Li('Buy/Sell (over bought/over sold) vs. moving average analysis.'),
            ]),
            html.B('Bollinger Band® Chart:', id='ttBB'), html.Br(),
            html.Ul([
                html.Li(['Bollinger Band® chart provides an analysis of closing price vs. moving average ',
                         'price and +/- standard deviation (potential calculated trading range to indicate ',
                         'the potential over bought/over sold of the closing price.']),
                html.Li('Moving average (simple/exponential) movement'),
                html.Li('Relative Strength Index'),
                html.Li('Over bought/Over sold vs. Bollinger Band® analysis.'),
            ]),
            # Simple Moving Average tooltip
            dbc.Tooltip(
                [html.H6('Simple Moving Average', className='fw-bold text-black text-center'),
                 'The simple moving average is a calculated "rolling" moving average ',
                 '(mean) over the period specified.'], target="ttSMA",
            ),
            # Exponential Moving Average tooltip
            dbc.Tooltip(
                [html.H6('Exponential Moving Average', className='fw-bold text-black text-center'),
                    'The exponential moving average is a "rolling" ',
                    'moving average (mean) over the period specified ',
                    'that applies "weighting" to the "nearer" periods.'], target="ttEWMA",
            ),
            # Candlestick chart tooltip
            dbc.Tooltip(
                [html.H6('Candlestick Chart', className='fw-bold text-black text-center'),
                    'This chart plots the open/high/loc/close price for period.'], target="ttcs",
            ),
            # Relative Strength Index tooltip
            dbc.Tooltip(
                [html.H6('Relative Strength Index', className='fw-bold text-black text-center'),
                    'What is Relative Strength Index (RSI)?', html.Br(),
                    'The Relative Strength Index is one of the popular indexes that track the momentum of the ',
                    'price as it measures both the speed and the rate of change in the price movement. It was ',
                    'developed by J.Welles Wilder Jr in 1978. The RSI values range between 0 and 100, the RSI ',
                    'value below 30 indicates oversold, and greater than 70 indicates overbought. Although some ',
                    'traders and analysts change the range to 40–60, it is very subjective and comes with ',
                    'experience. The RSI is plotted just below the asset price trend on the same timeline.', html.Br(),
                    html.Br(),
                    'The relative strength index is calculated as:', html.Br(),
                    html.Ul([
                        html.Li('"Rolling" average gain and loss'),
                        html.Li('Average gain divided by the average loss to derive relative strength'),
                        html.Li('100 minus relative strength to derive relative strength index'),
            ]),
                 ], target="ttRSI",
            ),
            # Bollinger Band tooltip
            dbc.Tooltip([
                html.H6('Bollinger Band® chart', className='fw-bold text-black text-center'),
                'A Bollinger Band® is a technical analysis tool defined by a set of trendlines.', html.Br(),
                'They are plotted as two standard deviations, both positively and negatively, ',
                'away from a (20 day) simple (Exponential) moving average (SMA) of a security''s price.', html.Br(),
                'Bollinger Bands® gives traders an idea of where the market is moving based on prices.', html.Br(),
                'It involves the use of three bands—one for the upper level, another for the lower level, ',
                'and the third for the moving average.', html.Br(),
                'When prices (closing) move closer to the upper band, it indicates that the '
                'market may be overbought.', html.Br(), html.Br(),
                'This chart can be used as an indication of the price trends.', html.Br(),
                'The upper and lower price bands are boundaries that can be used to indicate an over bought/over sold ',
                'instance', html.Br()
            ], target="ttBB",
            ),
                    ])
# Selection error
mainSelErrAlert = 'Please check ticker(s) or date range, unable to retrieve prices'
# Alert description(instructions) for grid data table
gridAlertConst = [
            # html.Hr(),
            html.H5("Data Grid instructions.", className="alert-heading"),
            html.P([
                'Grid filter:', html.Br(), html.Br(),
                html.I('Date Range:'), html.Br(),
                'Most Recent Only - will only extract/display the most recent price', html.Br(),
                'All Dates - no filter on dates', html.Br(),
                html.I('Ticker(s):'), html.Br(),
                'Tickers can be added or removed from extract/display.', html.Br(), html.Br(),
                'This is a grid of the prices extracted based upon the filtering criteria specified.', html.Br(),
                'The grid allows for further filtering and sorting as desired.', html.Br()])
            ]
# Alert description(instructions) for Price/volume Chart
pxvolAlertConst = [
            html.H5("Price/Volume Chart instructions.", className="alert-heading"),
            html.P([
                'Price/Volume filter:', html.Br(), html.Br(),
                html.I('Ticker(s):'), html.Br(),
                'Tickers can be added or removed from extract/display.', html.Br(), html.Br(),
                html.I('SMA/EWMA Short/Long nbr periods: SMA/EWMA - Simple/Exponential '),
                html.I('Moving Average (short/long periods)'), html.Br(),
                'Used to generate moving average plots for the period(s) specified', html.Br(),
                'These averages can be used as indications of closing price relative to the average price.', html.Br(),
                'Default average 30 - short, 100 - long.  increments by 10', html.Br(), html.Br(),
                html.I('Simple moving average is the average of the prior n period closing price.'), html.Br(),
                html.I('Exponential moving average  is a type of moving average that gives more weight to recent '),
                html.I('observations, which means it’s able to capture recent trends more quickly.'), html.Br(), html.Br(),
                html.I('Trend Line (Linear Regression Line):'), html.Br(),
                'Trend line is a data analysis technique that predicts the value of unknown data by using another ',
                'related and known data value.', html.Br(),
                'It mathematically models the unknown or dependent variable and the known or independent variable ',
                'as a linear equation.', html.Br(), html.Br(),
                'This chart plots the closing prices, volume (optional except mutual funds and indexes)',
                ' short/long SMA and trend line.', html.Br(),
                'This chart can be used to indicate the direction of the price.', html.Br()])
            ]
# Alert description(instructions) for Candlestick chart
csAlertConst = [
            html.H5("Candlestick Chart instructions.", className="alert-heading"),
            html.P([
                'Candlestick filter:', html.Br(), html.Br(),
                html.I('Ticker(s):'), html.Br(),
                'Tickers can be added or removed from extract/display.', html.Br(), html.Br(),
                html.I('Simple moving average is the average of the prior n period closing price.'), html.Br(),
                html.I('Exponential moving average  is a type of moving average that gives more weight to recent '),
                html.I('observations, which means it’s able to capture recent trends more quickly.'), html.Br(), html.Br(),
                'This chart plots the closing prices, volume (optional except mutual funds and indexes)',
                ' short/long SMA/EWMA and trend line.', html.Br(),
                'This chart can be used to indicate the direction of the price.', html.Br()])
            ]
# Alert description(instructions) for Bollinger Bands chart
bbAlertConst = [
            html.H5("Bollinger Band® Chart instructions.", className="alert-heading"),
            html.P([
                'Bollinger Band® filter:', html.Br(), html.Br(),
                html.I('Ticker:'), html.Br(),
                'Ticker can be updated for display.  Only 1 ticker at a time.', html.Br(), html.Br(),
                html.I('SMA/EWMA:'), html.Br(),
                'The number of periods used to calculate the SMA/EWMA used in the ',
                'Bollinger Band® is configurable.', html.Br(),
                html.I('Simple moving average is the average of the prior n period closing price.'), html.Br(),
                html.I('Exponential moving average  is a type of moving average that gives more weight to recent '),
                html.I('observations, which means it’s able to capture recent trends more quickly.'), html.Br(),
                html.I('Number of Standard Deviation(s):'), html.Br(),
                'The number of standard deviations used to calculate the the ranges (upper/lower) used in the ',
                'Bollinger Band® is configurable.', html.Br(), html.Br(),
                html.I('Bollinger Band® chart:'), html.Br(),
                'A Bollinger Band® is a technical analysis tool defined by a set of trendlines.', html.Br(),
                'They are plotted as two standard deviations, both positively and negatively, ',
                'away from a (20 day) simple (Exponential) moving average (SMA) of a security''s price.', html.Br(),
                'Bollinger Bands® gives traders an idea of where the market is moving based on prices.', html.Br(),
                'It involves the use of three bands—one for the upper level, another for the lower level, ',
                'and the third for the moving average.', html.Br(),
                'When prices (closing) move closer to the upper band, it indicates that the '
                'market may be overbought.', html.Br(), html.Br(),
                'This chart can be used as an indication of the price trends.', html.Br(),
                'The upper and lower price bands are boundaries that can be used to indicate an over bought/over sold ',
                'instance', html.Br()])
            ]
