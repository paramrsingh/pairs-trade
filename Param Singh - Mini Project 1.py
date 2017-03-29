import numpy as np
import pandas as pd
import datetime as dt
import statsmodels.tsa.stattools as ts
 
def initialize(context):
 
    context.stock_pairs = [(symbol('DIA'), symbol('QQQ')), 
                           (symbol('KO'), symbol('PEP'))]
    
    # Rebalance every day, 1 hour after market open.
    schedule_function(pairstrade, date_rules.every_day(), time_rules.market_open(hours=1))
    
def pairstrade(context, data):
    
    for i in range(len(context.stock_pairs)):
        #single pair
        (stock_x, stock_y) = context.stock_pairs[i]
        pricesx = data.history([stock_x], "price", 60, '1d')
        pricesy = data.history([stock_y], "price", 60, '1d')
        
        trade_signal = check_cointegrated(pricesx, pricesy)
        
        if trade_signal == True:
            trader(pricesx, pricesy, stock_x, stock_y, context, data)
        else:
            print "Not cointegrated, no trade"    
    
def check_stationary(X):
    X = X.ix[:,0]
    adfresult = ts.adfuller(X, regression='ctt')
    #Dickey–Fuller test tests the null hypothesis of whether a unit root is present in an autoregressive model.
    #The alternative hypothesis is stationarity or trend-stationarity
    #Note: No check for p-value significance
    #If the t-statistic is greater than the critical value reject the null hypothesis
    if adfresult[0] >= adfresult[4]['5%']:
        return True
    else:
        return False
    
def check_cointegrated(x, y):
    #check for stationary series in both series
    x_stationary_check = check_stationary(x)
    y_stationary_check = check_stationary(y)
    
    if x_stationary_check == True and y_stationary_check == True:
        # check for cointegration
        cointresult = ts.coint(x, y)
        if cointresult[0] >= cointresult[2][1]:
            return True
        else:
            return False        
    else:
        # series are not stationary and cannot be cointegrated
        return False
    
def trader(x, y, sidx, sidy, context, data):
    
    diff = []
    xs = x.ix[:,0]
    ys = y.ix[:,0]
    for i in range(0, len(xs)):
        diff.append(xs[i] - ys[i])
    
    #mean
    mean = np.average(diff)
    #standard deviation
    std_dev = np.std(diff)
    #current prices
    current_x = xs[-1]
    current_y = ys[-1]
    #spread
    spread = current_x - current_y
    
    #If spread(t) <= Mean Spread + 2*Std AND spread(t-1)> Mean Spread + 2*Std
    #If spread(t) >= Mean Spread – 2*Std AND spread(t-1)< Mean Spread – 2*Std
    if spread <= mean + 2*std_dev and spread > mean + 2*std_dev:
        #short
        order(sidx, 100)
        order(sidy, -10)
    if spread >= mean - 2*std_dev and spread < mean + 2*std_dev:
        #long
        order(sidx, -10)
        order(sidy, 100)
    else:
        print "No trade"