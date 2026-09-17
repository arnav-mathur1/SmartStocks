import os
os.environ.setdefault("CI", "1")  # Keep CMU Graphics open when stdin is unavailable.

import yfinance as yf
import pandas as pd
import math
from functools import lru_cache
from cmu_graphics import *


def onAppStart(app):
   app.width = 1200
   app.height = 800
   app.paused = True  # Redraw only for user input; this app has no animation loop.
  
   # Colors
   app.backgroundColor = 'aliceBlue' #'lightGray'
   app.buttonColor = 'royalBlue'
   app.hoverColor = 'darkBlue'
   app.textColor = 'white'
   app.errorColor = 'red'
  
   # Graph values
   app.graphX = 100
   app.graphY = 350
   app.graphWidth = 1000
   app.graphHeight = 300
   app.numYTicks = 10
   app.numXTicks = 8
  
   # Mouse tracking for graph
   app.mouseInGraph = False
   app.hoverX = None
   app.hoverY = None
   app.hoverPrice = None
   app.hoverDate = None
  
   app.currentStockData = None # Current data being displayed (changes w/ stock ticker and time interval)
  
   # Button dimensions
   app.buttonWidth = 250
   app.buttonHeight = 70
   app.buttonSpacing = 30
  
   # Button hover states, got the idea for making hovers from https://chatgpt.com/
   app.managePortfolioHover = False
   app.viewPerformanceHover = False
   app.runPredictionsHover = False
   app.comparisonHover = False
   app.diversityChartHover = False
   app.backButtonHover = False
   app.addStockHover = False
   app.removeStockHover = None
  
   app.currentPage = 'mainPage' # page I'm currently on
  
   app.portfolio = [] # portfolio
  
   # Stock input variables
   app.stockSymbol = ''
   app.stockShares = ''
   app.isTypingSymbol = False
   app.isTypingShares = False
   app.inputError = ''
  
   app.selectedStock = None
   app.performanceTimeframe = '1mo'
   # got time intervals from https://algotrading101.com/learn/yfinance-guide/
   app.timeOptions = ['5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'] # 'max' crashes sometimes
   app.comparisontimeOptions = ['5d', '1mo', '3mo', '6mo', '1y'] # '5y' and less crashes sometimes
  
   # Input (from the user) box dimensions
   app.inputFieldWidth = 250
   app.inputFieldHeight = 50
   app.inputFieldX = app.width/2 - app.inputFieldWidth/2
   app.symbolInputY = 250
   app.sharesInputY = 330
  
   # Back button dimensions
   app.backButtonWidth = 100
   app.backButtonHeight = 40
   app.backButtonX = 20
   app.backButtonY = 20


   # app.setMaxShapeCount(n) # potentially use this


@lru_cache(maxsize=128)
def getStockData(symbol, timeframe='1mo'):
   stock = yf.Ticker(symbol)
   data = stock.history(period=timeframe)
   if len(data) > 0:
       return data
   return None


def getPortfolioValue(portfolio):
   total = 0
   for stockIndex in range(len(portfolio)):
       symbol, shares = portfolio[stockIndex]
       data = getStockData(symbol, '1mo')
       if data is not None and len(data) > 0:
           price = data['Close'].iloc[-1]
           total += float(price) * int(shares)
   return total


def getPortfolioHistoricalValue(portfolio, historicalData, dateIndex):
   total = 0
   for stock, shares in portfolio:
       if stock in historicalData:
           stockData = historicalData[stock]
           if dateIndex < len(stockData['Close']):
               price = float(stockData['Close'].iloc[dateIndex])
               total += price * int(shares)
   return total


def getPortfolioPerformance(app, timeframe):
   if not app.portfolio: return None
  
   # Get S&P 500 data
   spyData = getStockData('^GSPC', timeframe)
   if spyData is None or len(spyData) == 0:
       return None
  
   # Get historical data for all stocks in portfolio
   historicalData = {}
   for stock, shares in app.portfolio:
       data = getStockData(stock, timeframe)
       if data is not None and len(data) > 0:
           historicalData[stock] = data
  
   # Calculate portfolio performance over time
   portfolioValues = []
   spyValues = []
   dates = []
  
   # Calculate initial values
   initialPortfolioValue = getPortfolioHistoricalValue(app.portfolio, historicalData, 0)
   initialSpyValue = float(spyData['Close'].iloc[0])
  
   # Calculate performance for each date
   for i in range(len(spyData)):
       date = spyData.index[i]
       spyPrice = float(spyData['Close'].iloc[i])
      
       # Calculate percentage changes
       spyChange = ((spyPrice - initialSpyValue) / initialSpyValue) * 100
      
       portfolioValue = getPortfolioHistoricalValue(app.portfolio, historicalData, i)
       portfolioChange = ((portfolioValue - initialPortfolioValue) / initialPortfolioValue) * 100
      
       portfolioValues.append(portfolioChange)
       spyValues.append(spyChange)
       dates.append(date)
  
   return {
       'dates': dates,
       'portfolio': portfolioValues,
       'spy': spyValues,
       'initialPortfolioValue': initialPortfolioValue,
       'currentPortfolioValue': portfolioValue,
       'initialSpyValue': initialSpyValue,
       'currentSpyValue': spyPrice
   }


@lru_cache(maxsize=128)
def getSectorInfo(symbol):
  # get the sector info for a particular stock ticker
   stock = yf.Ticker(symbol)
   info = stock.info
   # got info['sector'] from https://www.geeksforgeeks.org/getting-stock-symbols-with-yfinance-in-python/
   if 'sector' in info and info['sector'] is not None: return info['sector']
   else: return 'Unknown'


def getPortfolioDistributions(app):
   stockData = {}
   sectorData = {}
   totalValue = 0
  
   # get all the data first
   for symbol, shares in app.portfolio:
       data = getStockData(symbol, '1mo')
       if data is not None and len(data) > 0:
           price = float(data['Close'].iloc[-1])
           value = price * int(shares)
           sector = getSectorInfo(symbol)
          
           stockData[symbol] = {'symbol': symbol, 'value': value, 'shares': shares, 'sector': sector}
          
           if sector not in sectorData:
               sectorData[sector] = {'totalValue': 0, 'companies': []}
           sectorData[sector]['totalValue'] += value
           sectorData[sector]['companies'].append(symbol)
           totalValue += value
  
   # get the distribution data from the data above
   stockDistribution = []
   sectorDistribution = []
  
   if totalValue > 0:
       for symbol, data in stockData.items(): # data is the stockData above
           data['percentage'] = (data['value'] / totalValue) * 100
           stockDistribution.append(data) # add the percentage of each stock to the existing data
      
       for sector, data in sectorData.items():
           companies = []
           for symbol in data['companies']:
               companyData = stockData[symbol]
               companies.append(companyData)
          
           sectorDistribution.append({
               'sector': sector,
               'value': data['totalValue'],
               'percentage': (data['totalValue'] / totalValue) * 100,
               'companies': companies
           }) # adds all the data for each company in a particular sector
   return stockDistribution, sectorDistribution, totalValue


def drawPieSlice(centerX, centerY, radius, startAngle, endAngle, fill):
   # Convert angles from degrees to radians
   startRad = math.radians(startAngle)
   endRad = math.radians(endAngle)
  
   points = []
   points.append(centerX) # start at the center
   points.append(centerY)
  
   steps = 32  # more steps = smoother arc
   for i in range(steps + 1):
       theta = startRad + (i/steps) * (endRad - startRad) # used https://claude.ai/chat to get theta
       x = centerX + radius * math.cos(theta) # adapted from CS Academy, 6.3.4 Circular Motion
       y = centerY - radius * math.sin(theta)
       points.append(x)
       points.append(y)
  
   # Draw the filled slice
   drawPolygon(*points, fill=fill)


def isMouseInGraph(app, x, y):
   return (app.graphX <= x <= app.graphX + app.graphWidth and
           app.graphY <= y <= app.graphY + app.graphHeight)


def getStockInfoAtMouse(app, mouseX, mouseY):
   if app.currentStockData is None or len(app.currentStockData) == 0:
       return None, None
  
   # used https://claude.ai/chat to get relativeX and index
   relativeX = (mouseX - app.graphX) / app.graphWidth
   numPoints = len(app.currentStockData)
   index = int(relativeX * (numPoints - 1))
  
   if index < 0: index = 0
   if index >= numPoints: index = numPoints - 1
  
   date = str(app.currentStockData.index[index]).split()[0] # used https://claude.ai/chat to format/get date
   price = float(app.currentStockData['Close'].iloc[index])
   return date, price


def getPrediction(stockData, period='1mo'):
   if stockData is None or len(stockData) < 2: return None
   closingPrices = stockData['Close']
  
   # get recent data
   if period == '1mo': recentData = closingPrices.iloc[-20:]  # 20 trading days for 1 month
   elif period == '3mo': recentData = closingPrices.iloc[-60:]  # 60 trading days for 3 months
   elif period == '6mo': recentData = closingPrices.iloc[-120:]  # 120 trading days for 6 months
   else: return None


   # get the average of the daily percent changes
   # got pct_change, dropna, and mean from https://pandas.pydata.org/docs/reference/frame.html (pandas)
   changes = recentData.pct_change().dropna()
   avgDailyChange = changes.mean()
  
   lastPrice = float(recentData.iloc[-1]) # float to avoid crashing
   predictions = []
  
   for i in range(20):  # predict 20 trading days ahead (about 1 month)
       lastPrice = lastPrice * (1 + avgDailyChange) # basic future prediction based on last price
       predictions.append(lastPrice)
  
   return predictions


def getRecommendation(stockData, period='1mo'):
   if stockData is None or len(stockData) < 2: return "Not enough data for recommendation"
   closingPrices = stockData['Close']
  
   if period == '1mo': recentData = closingPrices.iloc[-20:] 
   elif period == '3mo': recentData = closingPrices.iloc[-60:] 
   elif period == '6mo': recentData = closingPrices.iloc[-120:]
  
   # calculate indicators
   startPrice = recentData.iloc[0]
   endPrice = recentData.iloc[-1]
   priceChange = ((endPrice - startPrice) / startPrice) * 100
   # got volatility formula from https://corporatefinanceinstitute.com/resources/career-map/sell-side/capital-markets/volatility-vol/
   volatility = recentData.pct_change().std() * 100  # standard deviation of percentage changes (std from pandas)
  
   # thresholds for recommendation (modified from https://chatgpt.com/)
   if period == '1mo':
       changeThreshold = 5
       volatilityThreshold = 2
   elif period == '3mo':
       changeThreshold = 10
       volatilityThreshold = 2.5
   else:
       changeThreshold = 15
       volatilityThreshold = 3
  
   # generate recommendation (from https://chatgpt.com/)
   if abs(priceChange) <= changeThreshold/2:
       return f"HOLD - Stable price movement ({priceChange:.1f}% change)"
  
   if volatility > volatilityThreshold * 2:
       return f"HOLD - High volatility suggests caution ({priceChange:.1f}% change)"
  
   if priceChange > changeThreshold:
       if volatility < volatilityThreshold:
           return f"SELL - Strong upward trend, consider taking profits ({priceChange:.1f}% change)"
       else:
           return f"HOLD - Positive but volatile trend ({priceChange:.1f}% change)"
  
   if priceChange < -changeThreshold:
       if volatility < volatilityThreshold:
           return f"BUY - Price dip with low volatility ({priceChange:.1f}% change)"
       else:
           return f"HOLD - Wait for price stabilization ({priceChange:.1f}% change)"
  
   return f"HOLD - No strong signals ({priceChange:.1f}% change)"
  
def drawGraph(app):
   if app.currentStockData is None or len(app.currentStockData) == 0:
       return
  
   drawRect(app.graphX, app.graphY, app.graphWidth, app.graphHeight, fill='white', border='black') # Draw graph background


   closingPrices = app.currentStockData['Close']
   minPrice = float(min(closingPrices))
   maxPrice = float(max(closingPrices))
   if maxPrice > minPrice: priceRange = maxPrice - minPrice
   else: priceRange = 1
  
   # Draw Y-axis grid and labels
   for tickIndex in range(app.numYTicks+1):
       y = app.graphY + app.graphHeight - (tickIndex * app.graphHeight / app.numYTicks)
       price = minPrice + (tickIndex * priceRange / app.numYTicks)
      
       drawLine(app.graphX, y, app.graphX + app.graphWidth, y, fill='lightGray', dashes=True)
       # got '.2f' from https://www.w3schools.com/python/python_string_formatting.asp
       drawLabel(f'${price:.2f}', app.graphX - 15, y, size=12, fill='darkBlue', align='right')
  
   # Draw X-axis grid and labels
   dates = app.currentStockData.index
   for tickIndex in range(app.numXTicks+1):
       x = app.graphX + (tickIndex * app.graphWidth / app.numXTicks)
       dateIndex = int((tickIndex * (len(dates) - 1)) / app.numXTicks)
       date = str(dates[dateIndex]).split()[0]
      
       drawLine(x, app.graphY, x, app.graphY + app.graphHeight, fill='lightGray', dashes=True)
       drawLabel(date, x, app.graphY + app.graphHeight + 20, size=12, fill='darkBlue', align='center')
  
   # Draw price line
   for priceIndex in range(1, len(closingPrices)):
       # modified ideas from https://chatgpt.com/ for scaling/getting the x and y values
       x1 = app.graphX + ((priceIndex-1) * app.graphWidth) / (len(closingPrices)-1)
       y1 = app.graphY + app.graphHeight - ((float(closingPrices.iloc[priceIndex-1]) - minPrice) / priceRange * app.graphHeight)
       x2 = app.graphX + (priceIndex * app.graphWidth) / (len(closingPrices)-1)
       y2 = app.graphY + app.graphHeight - ((float(closingPrices.iloc[priceIndex]) - minPrice) / priceRange * app.graphHeight)
      
       drawLine(x1, y1, x2, y2, fill='blue', lineWidth=2)
  
   # Draw hover line/box
   if app.mouseInGraph and app.hoverPrice is not None and app.hoverDate is not None:
       drawLine(app.hoverX, app.graphY, app.hoverX, app.graphY + app.graphHeight, fill='red', dashes=True)
      
       infoX = min(app.hoverX + 10, app.graphX + app.graphWidth - 150)
       infoY = max(app.hoverY - 50, app.graphY + 10)
      
       drawRect(infoX - 5, infoY - 5, 160, 60, fill='ghostWhite', border='gray') #opacity=90
       drawLabel(f'Date: {app.hoverDate}', infoX + 75, infoY + 15, size=14, fill='black')
       drawLabel(f'Price: ${app.hoverPrice:.2f}', infoX + 75, infoY + 35, size=14, fill='black')


def drawMainPage(app):
   drawRect(0, 0, app.width, app.height, fill=app.backgroundColor)
  
   drawLabel('SmartStocks', app.width/2, 200, size=54, bold=True, fill='darkBlue')
  
   # Manage Portfolio Button
   if app.managePortfolioHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.width/2 - app.buttonWidth/2, 400, app.buttonWidth, app.buttonHeight, fill=buttonFill, border='black')
   drawLabel('Manage Portfolio', app.width/2, 435, size=24, fill=app.textColor)
  
   # View Performance Button
   if app.viewPerformanceHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.width/2 - app.buttonWidth/2, 400 + app.buttonHeight + app.buttonSpacing,
            app.buttonWidth, app.buttonHeight, fill=buttonFill, border='black')
   drawLabel('View Performance', app.width/2, 435 + app.buttonHeight + app.buttonSpacing, size=24, fill=app.textColor)
  
   # Run Predictions Button
   if app.runPredictionsHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.width/2 - app.buttonWidth/2, 400 + 2*app.buttonHeight + 2*app.buttonSpacing,
            app.buttonWidth, app.buttonHeight, fill=buttonFill, border='black')
   drawLabel('Run Predictions', app.width/2, 435 + 2*app.buttonHeight + 2*app.buttonSpacing, size=24, fill=app.textColor)


   # Comparison with S&P500 Button
   if app.comparisonHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.width/2 - 3.5*app.buttonWidth/2, 400 + app.buttonHeight + app.buttonSpacing,
            app.buttonWidth, app.buttonHeight, fill=buttonFill, border='black')
   drawLabel('Comparison with S&P500', app.width/2 - 2.5*app.buttonWidth/2, 435 + app.buttonHeight + app.buttonSpacing,
             size=20, fill=app.textColor)
  
   # Diversity Chart Button
   if app.diversityChartHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.width/2 + 1.5*app.buttonWidth/2, 400 + app.buttonHeight + app.buttonSpacing,
            app.buttonWidth, app.buttonHeight, fill=buttonFill, border='black')
   drawLabel('Diversity Chart', app.width/2 + 2.5*app.buttonWidth/2, 435 + app.buttonHeight + app.buttonSpacing,
             size=24, fill=app.textColor)


def drawManagePortfolioPage(app):
   drawRect(0, 0, app.width, app.height, fill=app.backgroundColor)
  
   drawLabel('Manage Portfolio', app.width/2, 100, size=36, bold=True, fill='darkBlue')
  
   # Back Button
   if app.backButtonHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.backButtonX, app.backButtonY, app.backButtonWidth, app.backButtonHeight,
            fill=buttonFill, border='black')
   drawLabel('Back', app.backButtonX + app.backButtonWidth/2, app.backButtonY + app.backButtonHeight/2,
             size=18, fill=app.textColor)
  
   # Symbol input box
   drawRect(app.inputFieldX, app.symbolInputY, app.inputFieldWidth, app.inputFieldHeight, fill='white', border='black')
   if app.stockSymbol == '': placeholderText = 'Enter Stock Symbol'
   else: placeholderText = app.stockSymbol
   drawLabel(placeholderText, app.inputFieldX + 10, app.symbolInputY + app.inputFieldHeight/2,
             align='left', size=18)
  
   # Shares input box
   drawRect(app.inputFieldX, app.sharesInputY, app.inputFieldWidth, app.inputFieldHeight, fill='white', border='black')
   if app.stockShares == '': placeholderText = 'Number of Shares'
   else: placeholderText = app.stockShares
   drawLabel(placeholderText, app.inputFieldX + 10, app.sharesInputY + app.inputFieldHeight/2,
             align='left', size=18)
  
   # Add Stock Button
   if app.addStockHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.width/2 + 100, 400, 150, 40, fill=buttonFill, border='black')
   drawLabel('Add Stock', app.width/2 + 175, 420, size=18, fill=app.textColor)
  
   if app.inputError: drawLabel(app.inputError, app.width/2, 460, size=18, fill=app.errorColor) # Error Message
  
   # Portfolio List
   startY = 500
   for stockIndex in range(len(app.portfolio)):
       stock = app.portfolio[stockIndex]
       symbol = stock[0]
       shares = stock[1]
      
       # Stock Info
       drawLabel(f'{stockIndex + 1}. {symbol} - {shares} shares', app.width/2, startY + stockIndex*30,
                size=20, fill='darkBlue')
      
       # Remove Button
       if app.removeStockHover == stockIndex: buttonFill = 'darkRed'
       else: buttonFill = 'red'
       drawRect(app.width/2 - 250, startY + stockIndex*30 - 15, 150, 30, fill=buttonFill, border='black')
       drawLabel('Remove', app.width/2 - 175, startY + stockIndex*30, size=16, fill='white')
          
   # Portfolio Value
   value = getPortfolioValue(app.portfolio)
   drawLabel(f'Total Portfolio Value: ${value:.2f}', app.width/2, app.height - 50, size=24, bold=True, fill='darkBlue')


def drawViewPerformancePage(app):
   drawRect(0, 0, app.width, app.height, fill=app.backgroundColor)
  
   drawLabel('Stock Performance', app.width/2, 100, size=36, bold=True, fill='darkBlue')
  
   # Back Button
   if app.backButtonHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.backButtonX, app.backButtonY, app.backButtonWidth, app.backButtonHeight, fill=buttonFill, border='black')
   drawLabel('Back', app.backButtonX + app.backButtonWidth/2, app.backButtonY + app.backButtonHeight/2,
             size=18, fill=app.textColor)
  
   if len(app.portfolio) == 0:
       drawLabel('No stocks in portfolio', app.width/2, app.height/2, size=48, fill='darkBlue')
       return
  
   # Select first stock if there are none selected
   if app.selectedStock == None:
       app.selectedStock = app.portfolio[0][0]
       app.currentStockData = getStockData(app.selectedStock, app.performanceTimeframe)
  
   # Stock List
   startY = 150
   for stockIndex in range(len(app.portfolio)):
       stock = app.portfolio[stockIndex]
       symbol = stock[0]
       shares = stock[1]
       if symbol == app.selectedStock:  fillColor = 'lightBlue'
       else:  fillColor = 'white'
      
       drawRect(app.width/2 - 200, startY + stockIndex*40, 400, 40, fill=fillColor, border='black')
       drawLabel(f'{symbol} - {shares} shares', app.width/2, startY + stockIndex*40 + 20, size=20, fill='darkBlue')
          
   drawGraph(app) # Draw big graph
  
   # Timeframe Buttons
   totalButtons = len(app.timeOptions)
   startX = app.width/2 - (totalButtons * 100) / 2


   for timeframeIndex in range(len(app.timeOptions)):
       timeframe = app.timeOptions[timeframeIndex]
       if app.performanceTimeframe == timeframe: fillColor = app.hoverColor
       else: fillColor = app.buttonColor
      
       buttonX = startX + (timeframeIndex * 100)
      
       drawRect(buttonX, app.height - 50, 100, 50, fill=fillColor, border='black')
       drawLabel(timeframe, buttonX + 50, app.height - 25, size=18, fill=app.textColor)
          
   drawLabel(f'Selected Stock: {app.selectedStock}', app.width/2 + 400, 250, size=24, fill='darkBlue')
  
   # Current Price
   if app.currentStockData is not None and len(app.currentStockData) > 0:
       currentPrice = float(app.currentStockData['Close'].iloc[-1])
       drawLabel(f'Current Price: ${currentPrice:.2f}', app.width/2 + 400, 300, size=20, fill='darkBlue')
   else:
       drawLabel('Current Price: Unavailable', app.width/2 + 400, 300, size=20, fill='darkBlue')


def drawComparisonPage(app):
   drawRect(0, 0, app.width, app.height, fill=app.backgroundColor)
  
   drawLabel('Comparison with S&P 500', app.width/2, 100, size=36, bold=True, fill='darkBlue')


   # Back Button
   if app.backButtonHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.backButtonX, app.backButtonY, app.backButtonWidth, app.backButtonHeight, fill=buttonFill, border='black')
   drawLabel('Back', app.backButtonX + app.backButtonWidth/2, app.backButtonY + app.backButtonHeight/2,
             size=18, fill=app.textColor)
  
   if len(app.portfolio) == 0:
       drawLabel('No stocks in portfolio', app.width/2, app.height/2, size=48, fill='darkBlue')
       return
  
   performanceData = getPortfolioPerformance(app, app.performanceTimeframe)
   if performanceData is None:
       drawLabel('No comparison data', app.width/2, app.height/2, size=48, fill='darkBlue')
       return
  
   drawRect(app.graphX, app.graphY, app.graphWidth, app.graphHeight, fill='white', border='black') # background


   # (similar to viewPerformance/graph function)
  
   # Find min/max val for scaling
   allValues = performanceData['portfolio'] + performanceData['spy']
   minValue, maxValue  = min(allValues), max(allValues)
   valueRange = max(abs(maxValue - minValue), 0.01)  # got this idea from https://chatgpt.com/ to avoid division by 0
  
   # Draw y-axis
   for i in range(app.numYTicks + 1):
       y = app.graphY + app.graphHeight - (i * app.graphHeight / app.numYTicks)
       value = minValue + (i * valueRange / app.numYTicks)
       drawLine(app.graphX, y, app.graphX + app.graphWidth, y, fill='lightGray', dashes=True)
       drawLabel(f'{value:.1f}%', app.graphX - 15, y, size=12, fill='darkBlue', align='right')
  
   # Draw x-axis
   dates = performanceData['dates']
   for i in range(app.numXTicks + 1):
       x = app.graphX + (i * app.graphWidth / app.numXTicks)
       dateIndex = int((i * (len(dates) - 1)) / app.numXTicks)
       date = str(dates[dateIndex]).split()[0]
       drawLine(x, app.graphY, x, app.graphY + app.graphHeight, fill='lightGray', dashes=True)
       drawLabel(date, x, app.graphY + app.graphHeight + 20, size=12, fill='darkBlue', align='center')
  
   # Draw portfolio line
   for i in range(1, len(performanceData['portfolio'])):
       x1 = app.graphX + ((i-1) * app.graphWidth) / (len(dates)-1)
       y1 = app.graphY + app.graphHeight - ((performanceData['portfolio'][i-1] - minValue) / valueRange * app.graphHeight)
       x2 = app.graphX + (i * app.graphWidth) / (len(dates)-1)
       y2 = app.graphY + app.graphHeight - ((performanceData['portfolio'][i] - minValue) / valueRange * app.graphHeight)
       drawLine(x1, y1, x2, y2, fill='blue', lineWidth=2)
  
   # Draw S&P 500 line
   for i in range(1, len(performanceData['spy'])):
       x1 = app.graphX + ((i-1) * app.graphWidth) / (len(dates)-1)
       y1 = app.graphY + app.graphHeight - ((performanceData['spy'][i-1] - minValue) / valueRange * app.graphHeight)
       x2 = app.graphX + (i * app.graphWidth) / (len(dates)-1)
       y2 = app.graphY + app.graphHeight - ((performanceData['spy'][i] - minValue) / valueRange * app.graphHeight)
       drawLine(x1, y1, x2, y2, fill='red', lineWidth=2)
  
   legendY = 180
   # Portfolio metrics
   drawRect(app.width - 250, legendY, 20, 20, fill='blue')
   drawLabel('Your Portfolio', app.width - 210, legendY + 10, size=16, fill='darkBlue', align='left')
   portfolioChange = ((performanceData['currentPortfolioValue'] - performanceData['initialPortfolioValue'])
                      / performanceData['initialPortfolioValue'] * 100)
   drawLabel(f'Change: {portfolioChange:.1f}%', app.width - 210, legendY + 30, size=14, fill='darkBlue', align='left')
   drawLabel(f'Value: ${performanceData["currentPortfolioValue"]:.2f}',
             app.width - 210, legendY + 50, size=14, fill='darkBlue', align='left')
  
   # S&P 500 metrics
   drawRect(app.width - 250, legendY + 80, 20, 20, fill='red')
   drawLabel('S&P 500', app.width - 210, legendY + 90, size=16, fill='darkBlue', align='left')
   spyChange = ((performanceData['currentSpyValue'] - performanceData['initialSpyValue'])
                / performanceData['initialSpyValue'] * 100)
   drawLabel(f'Change: {spyChange:.1f}%', app.width - 210, legendY + 110, size=14, fill='darkBlue', align='left')
  
   # Tell the user if they're beating the S&P500 (purpose)
   difference = portfolioChange - spyChange
  
   if difference > 0:
       message = f"Outperforming S&P 500 by {abs(difference):.1f}%"
       color = 'green'
   else:
       message = f"Underperforming S&P 500 by {abs(difference):.1f}%"
       color = 'red'
  
   drawLabel(message, app.width/2, 225, size=28, fill=color, bold=True)
  
   # Draw timeframe buttons
   totalButtons = len(app.comparisontimeOptions)
   startX = app.width/2 - (totalButtons * 100) / 2
  
   for i in range(len(app.comparisontimeOptions)):
       timeframe = app.comparisontimeOptions[i]
       if app.performanceTimeframe == timeframe:
           fillColor = app.hoverColor
       else:
           fillColor = app.buttonColor
          
       buttonX = startX + (i * 100)
       drawRect(buttonX, app.height - 50, 100, 50, fill=fillColor, border='black')
       drawLabel(timeframe, buttonX + 50, app.height - 25, size=18, fill=app.textColor)


def drawDiversityChartPage(app):
   drawRect(0, 0, app.width, app.height, fill=app.backgroundColor)
  
   drawLabel('Portfolio Diversity Charts', app.width/2, 60, size=36, bold=True, fill='darkBlue')
  
   # Back Button
   if app.backButtonHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.backButtonX, app.backButtonY, app.backButtonWidth, app.backButtonHeight, fill=buttonFill, border='black')
   drawLabel('Back', app.backButtonX + app.backButtonWidth/2, app.backButtonY + app.backButtonHeight/2,
             size=18, fill=app.textColor)
  
   if len(app.portfolio) == 0:
       drawLabel('No stocks in portfolio', app.width/2, app.height/2, size=48, fill='darkBlue')
       return
  
   stockDistribution, sectorDistribution, totalValue = getPortfolioDistributions(app)
   drawLabel(f'Total Portfolio Value: ${totalValue:,.2f}', app.width/2, 100, size=24, bold=True, fill='darkBlue')
  
   # random colors generated by https://claude.ai/chat
   stockColors = ['royalBlue', 'crimson', 'forestGreen', 'orange', 'purple', 'teal', 'maroon', 'navy', 'olive', 'coral']
   sectorColors = ['dodgerBlue', 'mediumSeaGreen', 'salmon', 'darkOrchid', 'gold', 'crimson', 'teal', 'navy', 'olive', 'slateBlue']


   # Left side: stock charts
   stockCenterX = app.width/4
   stockCenterY = app.height/2 - 50
   stockRadius = 150
  
   drawLabel('Individual Stock Breakdown', stockCenterX, stockCenterY - stockRadius - 20, size=24, bold=True, fill='darkBlue')
  
   drawCircle(stockCenterX, stockCenterY, stockRadius, fill='white', border='black') # big circle
   currentAngle = 0
   # got enumerate from https://www.geeksforgeeks.org/enumerate-in-python/
   for i, stock in enumerate(stockDistribution):
       colorIndex = i % len(stockColors) # 'random' color almost
       sliceAngle = (stock['percentage'] / 100) * 360
       drawPieSlice(stockCenterX, stockCenterY, stockRadius, currentAngle, currentAngle + sliceAngle, stockColors[colorIndex])
       currentAngle += sliceAngle
  
   # Draw stock list below the chart
   stockListY = stockCenterY + stockRadius + 40
   drawLabel('Stock Holdings:', stockCenterX - 150, stockListY, size=18, bold=True, fill='darkBlue', align='left')
   colorSquareSize = 15
   for i, stock in enumerate(stockDistribution):
       # Draw color square
       drawRect(stockCenterX - 160, stockListY + 30 + (i * 25) - colorSquareSize/2,
                colorSquareSize, colorSquareSize, fill=stockColors[i % len(stockColors)])
      
       # add text to the right of the color square
       text = f"{stock['symbol']}: ${stock['value']:,.2f} ({stock['percentage']:.1f}%)"
       drawLabel(text, stockCenterX - 150 + colorSquareSize + 5, stockListY + 30 + (i * 25),
               size=14, fill='darkBlue', align='left')
  
   # Right side: sector chart
   sectorCenterX = 3*app.width/4
   sectorCenterY = app.height/2 - 50
   sectorRadius = 150
  
   drawLabel('Sector Breakdown', sectorCenterX, sectorCenterY - sectorRadius - 20, size=24, bold=True, fill='darkBlue')
  
   drawCircle(sectorCenterX, sectorCenterY, sectorRadius, fill='white', border='black') # big circle
   currentAngle = 0
   for i, sector in enumerate(sectorDistribution):
       colorIndex = i % len(sectorColors)
       sliceAngle = (sector['percentage'] / 100) * 360
       drawPieSlice(sectorCenterX, sectorCenterY, sectorRadius, currentAngle, currentAngle + sliceAngle, sectorColors[colorIndex])
       currentAngle += sliceAngle
  
   # Draw sector breakdown with companies below it
   sectorListY = sectorCenterY + sectorRadius + 40
   currentY = sectorListY
  
   drawLabel('Sector Details:', sectorCenterX - 150, currentY, size=18, bold=True, fill='darkBlue', align='left')
   currentY += 30
  
   for i, sector in enumerate(sectorDistribution):
       drawRect(sectorCenterX - 160, currentY - 5, 15, 15, fill=sectorColors[i % len(sectorColors)])
       sectorText = f"{sector['sector']}: ${sector['value']:,.2f} ({sector['percentage']:.1f}%)"
       drawLabel(sectorText, sectorCenterX - 130, currentY, size=14, fill='darkBlue', bold=True, align='left')
       currentY += 25
      
       # List companies in the sector
       for company in sector['companies']:
           # looks like a bulleted list
           drawLabel(f"   - {company['symbol']}", sectorCenterX - 130, currentY, size=14, fill='darkBlue', align='left')
           currentY += 20
      
       currentY += 10


def drawPredictionsPage(app):
   drawRect(0, 0, app.width, app.height, fill=app.backgroundColor)
  
   drawLabel('Stock Predictions', app.width/2, 100, size=36, bold=True, fill='darkBlue')
  
   # Back Button
   if app.backButtonHover: buttonFill = app.hoverColor
   else: buttonFill = app.buttonColor
   drawRect(app.backButtonX, app.backButtonY, app.backButtonWidth, app.backButtonHeight, fill=buttonFill, border='black')
   drawLabel('Back', app.backButtonX + app.backButtonWidth/2, app.backButtonY + app.backButtonHeight/2, size=18, fill=app.textColor)
  
   if len(app.portfolio) == 0:
       drawLabel('No stocks in portfolio', app.width/2, app.height/2, size=48, fill='darkBlue')
       return
  
   # Stock List (similar to view performance page)
   startY = 150
   for i in range(len(app.portfolio)):
       stock = app.portfolio[i]
       symbol = stock[0]
       shares = stock[1]
       if symbol == app.selectedStock: fillColor = 'lightBlue'
       else: fillColor = 'white'
      
       drawRect(app.width/2 - 200, startY + i*40, 400, 40, fill=fillColor, border='black')
       drawLabel(f'{symbol} - {shares} shares', app.width/2, startY + i*40 + 20, size=20, fill='darkBlue')
  
   # Draw stock data (70% of graph) and prediction (other 30%)
   if app.selectedStock is not None and app.currentStockData is not None and len(app.currentStockData) > 0:
       drawRect(app.graphX, app.graphY, app.graphWidth, app.graphHeight, fill='white', border='black')
      
       closingPrices = app.currentStockData['Close']
       predictions = getPrediction(app.currentStockData, app.performanceTimeframe)
      
       if predictions: # this part is also similar to the view performance page
           allPrices = list(closingPrices) + predictions
           minPrice = float(min(allPrices))
           maxPrice = float(max(allPrices))
           if maxPrice > minPrice: priceRange = maxPrice - minPrice
           else: priceRange = 1
          
           # Draw Y-axis grid and labels
           for i in range(app.numYTicks + 1):
               y = app.graphY + app.graphHeight - (i * app.graphHeight / app.numYTicks)
               price = minPrice + (i * priceRange / app.numYTicks)
               drawLine(app.graphX, y, app.graphX + app.graphWidth, y, fill='lightGray', dashes=True)
               drawLabel(f'${price:.2f}', app.graphX - 15, y, size=12, fill='darkBlue', align='right')
          
           # Draw historical price line
           historyWidth = int(app.graphWidth * 0.7)
           for i in range(1, len(closingPrices)):
               x1 = app.graphX + ((i-1) * historyWidth) / (len(closingPrices)-1)
               y1 = (app.graphY + app.graphHeight - ((float(closingPrices.iloc[i-1]) - minPrice) / priceRange * app.graphHeight))
               x2 = app.graphX + (i * historyWidth) / (len(closingPrices)-1)
               y2 = (app.graphY + app.graphHeight - ((float(closingPrices.iloc[i]) - minPrice) / priceRange * app.graphHeight))
               drawLine(x1, y1, x2, y2, fill='blue', lineWidth=2)
          
           # Draw prediction line
           predictionStart = float(closingPrices.iloc[-1])
           startX = app.graphX + historyWidth
           # used https://chatgpt.com/ to get startY variable
           startY = (app.graphY + app.graphHeight - ((predictionStart - minPrice) / priceRange * app.graphHeight))
           predictionWidth = app.graphWidth - historyWidth


           for i in range(1, len(predictions)):
               x1 = startX + ((i-1) * predictionWidth) / (len(predictions)-1)
               y1 = (app.graphY + app.graphHeight - ((predictions[i-1] - minPrice) / priceRange * app.graphHeight))
               x2 = startX + (i * predictionWidth) / (len(predictions)-1)
               y2 = (app.graphY + app.graphHeight - ((predictions[i] - minPrice) / priceRange * app.graphHeight))
               drawLine(x1, y1, x2, y2, fill='red', lineWidth=2, dashes=True)
          
           # draw legend, recommendation under graph, and predicted percent change
           legendY = 180
           drawRect(app.width - 250, legendY, 20, 20, fill='blue')
           drawLabel('Historical Data', app.width - 210, legendY + 10, size=16, fill='darkBlue', align='left')
           drawRect(app.width - 250, legendY + 40, 20, 20, fill='red')
           drawLabel('Prediction', app.width - 210, legendY + 50, size=16, fill='darkBlue', align='left')
          
           recommendation = getRecommendation(app.currentStockData, app.performanceTimeframe)
           drawLabel(f'Recommendation: ' + recommendation, app.width/2, 680, size=17, fill='darkBlue', bold=True, align='center')
          
           startPrice = predictionStart
           endPrice = predictions[-1]
           priceChange = ((endPrice - startPrice) / startPrice) * 100
           if priceChange > 0: changeColor = 'green'
           else: changeColor = 'red'
           # +.2f displays the sign too (+ or -)
           drawLabel(f'Predicted Change: {priceChange:+.2f}%', app.width - 250, legendY + 100, size=18, fill=changeColor, align='left')
  
   # Timeframe buttons (limited options)
   predictTimeOptions = ['1mo', '3mo', '6mo']
   totalButtons = len(predictTimeOptions)
   startX = app.width/2 - (totalButtons * 100) / 2
  
   for i in range(len(predictTimeOptions)):
       timeframe = predictTimeOptions[i]
       if app.performanceTimeframe == timeframe: fillColor = app.hoverColor
       else: fillColor = app.buttonColor
      
       buttonX = startX + (i * 100)
       drawRect(buttonX, app.height - 50, 100, 50, fill=fillColor, border='black')
       drawLabel(timeframe, buttonX + 50, app.height - 25, size=18, fill=app.textColor)


def onMouseMove(app, mouseX, mouseY):
   app.managePortfolioHover = False
   app.viewPerformanceHover = False
   app.runPredictionsHover = False
   app.comparisonHover = False
   app.diversityChartHover = False
   app.backButtonHover = False
   app.addStockHover = False
   app.removeStockHover = None
  
   # Main page button hovers
   if app.currentPage == 'mainPage':
       app.managePortfolioHover = (mouseX >= app.width/2 - app.buttonWidth/2 and
                                 mouseX <= app.width/2 + app.buttonWidth/2 and
                                 mouseY >= 400 and mouseY <= 400 + app.buttonHeight)
      
       app.viewPerformanceHover = (mouseX >= app.width/2 - app.buttonWidth/2 and
                                 mouseX <= app.width/2 + app.buttonWidth/2 and
                                 mouseY >= 400 + app.buttonHeight + app.buttonSpacing and
                                 mouseY <= 400 + 2*app.buttonHeight + app.buttonSpacing)
      
       app.runPredictionsHover = (mouseX >= app.width/2 - app.buttonWidth/2 and
                                mouseX <= app.width/2 + app.buttonWidth/2 and
                                mouseY >= 400 + 2*app.buttonHeight + 2*app.buttonSpacing and
                                mouseY <= 400 + 3*app.buttonHeight + 2*app.buttonSpacing)
      
       app.comparisonHover = (mouseX >= app.width/2 - 3.5*app.buttonWidth/2 and
                                 mouseX <= app.width/2 - 3.5*app.buttonWidth/2 + app.buttonWidth and
                                 mouseY >= 400 + app.buttonHeight + app.buttonSpacing and
                                 mouseY <= 400 + 2*app.buttonHeight + app.buttonSpacing)
      
       app.diversityChartHover = (mouseX >= app.width/2 + 1.5*app.buttonWidth/2 and
                                 mouseX <= app.width/2 + 1.5*app.buttonWidth/2  + app.buttonWidth and
                                 mouseY >= 400 + app.buttonHeight + app.buttonSpacing and
                                 mouseY <= 400 + 2*app.buttonHeight + app.buttonSpacing)
      
  
   # Portfolio page button hovers
   elif app.currentPage == 'managePortfolioPage':
       app.backButtonHover = (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
                           mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight)
      
       app.addStockHover = (mouseX >= app.width/2 + 100 and mouseX <= app.width/2 + 250 and
                         mouseY >= 400 and mouseY <= 440)
      
       # Remove button hovers
       app.removeStockHover = None
       startY = 500
       for stockIndex in range(len(app.portfolio)):
           if (mouseX >= app.width/2 - 250 and mouseX <= app.width/2 - 100 and
               mouseY >= startY + stockIndex*30 - 15 and mouseY <= startY + stockIndex*30 + 15):
               app.removeStockHover = stockIndex
               break
  
   # Graph hover updates/back button hover in view performance
   elif app.currentPage == 'viewPerformancePage':
       app.backButtonHover = (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
                           mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight)
      
       app.mouseInGraph = isMouseInGraph(app, mouseX, mouseY)
       if app.mouseInGraph:
           app.hoverX = mouseX
           app.hoverY = mouseY
           app.hoverDate, app.hoverPrice = getStockInfoAtMouse(app, mouseX, mouseY)
       else:
           app.hoverX = None
           app.hoverY = None
           app.hoverPrice = None
           app.hoverDate = None
  
   elif app.currentPage == 'comparisonPage':
       app.backButtonHover = (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
                           mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight)
  
   elif app.currentPage == 'diversityChartPage':
       app.backButtonHover = (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
                           mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight)
  
   elif app.currentPage == 'predictionsPage':
       app.backButtonHover = (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
                           mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight)


def handleMainPageClick(app, mouseX, mouseY):
   # Manage Portfolio button
   if (mouseX >= app.width/2 - app.buttonWidth/2 and mouseX <= app.width/2 + app.buttonWidth/2 and
       mouseY >= 400 and mouseY <= 400 + app.buttonHeight):
       app.currentPage = 'managePortfolioPage'
       app.inputError = ''
  
   # View Performance button
   elif (mouseX >= app.width/2 - app.buttonWidth/2 and mouseX <= app.width/2 + app.buttonWidth/2 and
         mouseY >= 400 + app.buttonHeight + app.buttonSpacing and mouseY <= 400 + 2*app.buttonHeight + app.buttonSpacing):
       if len(app.portfolio) > 0:
           app.selectedStock = app.portfolio[0][0]
           app.currentStockData = getStockData(app.selectedStock, app.performanceTimeframe)
           app.currentPage = 'viewPerformancePage'
  
   # Comparison Page
   elif (mouseX >= app.width/2 - 3.5*app.buttonWidth/2 and mouseX <= app.width/2 - 3.5*app.buttonWidth/2 + app.buttonWidth and
         mouseY >= 400 + app.buttonHeight + app.buttonSpacing and mouseY <= 400 + 2*app.buttonHeight + app.buttonSpacing):
         app.currentPage = 'comparisonPage'
         app.performanceTimeframe = '1mo'
  
   # Diversity Chart Page
   elif (mouseX >= app.width/2 + 1.5*app.buttonWidth/2 and mouseX <= app.width/2 + 1.5*app.buttonWidth/2 + app.buttonWidth and
         mouseY >= 400 + app.buttonHeight + app.buttonSpacing and mouseY <= 400 + 2*app.buttonHeight + app.buttonSpacing):
         app.currentPage = 'diversityChartPage'


   # Run Predictions Page
   elif (mouseX >= app.width/2 - app.buttonWidth/2 and mouseX <= app.width/2 + app.buttonWidth/2 and
         mouseY >= 400 + 2*app.buttonHeight + 2*app.buttonSpacing and mouseY <= 400 + 3*app.buttonHeight + 2*app.buttonSpacing):
         app.currentPage = 'predictionsPage'
         app.performanceTimeframe = '1mo'
         if len(app.portfolio) > 0:
         # Select first stock if none selected    
           if app.selectedStock == None:
               app.selectedStock = app.portfolio[0][0]
           app.currentStockData = getStockData(app.selectedStock, app.performanceTimeframe)


def handleManagePortfolioPageClick(app, mouseX, mouseY):
   # Back button
   if (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
       mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight):
       app.currentPage = 'mainPage'
       app.inputError = ''
  
   # Symbol input box
   elif (mouseX >= app.inputFieldX and mouseX <= app.inputFieldX + app.inputFieldWidth and
         mouseY >= app.symbolInputY and mouseY <= app.symbolInputY + app.inputFieldHeight):
       app.isTypingSymbol = True
       app.isTypingShares = False
  
   # Shares input box
   elif (mouseX >= app.inputFieldX and mouseX <= app.inputFieldX + app.inputFieldWidth and
         mouseY >= app.sharesInputY and mouseY <= app.sharesInputY + app.inputFieldHeight):
       app.isTypingShares = True
       app.isTypingSymbol = False
  
   # Add stock button
   elif (mouseX >= app.width/2 + 100 and mouseX <= app.width/2 + 250 and
         mouseY >= 400 and mouseY <= 440):
       if app.stockSymbol == '':
           app.inputError = 'Please enter a stock symbol'
       elif app.stockShares == '':
           app.inputError = 'Please enter number of shares'
       elif not app.stockShares.isdigit():
           app.inputError = 'Shares must be a number'
       else:
           # Try to get stock data to see if the symbol is valid
           data = getStockData(app.stockSymbol.upper(), '1mo')
           if data is not None and len(data) > 0:
               app.portfolio.append((app.stockSymbol.upper(), app.stockShares))
               app.stockSymbol = ''
               app.stockShares = ''
               app.isTypingSymbol = False
               app.isTypingShares = False
               app.inputError = ''
           else:
               app.inputError = 'Invalid stock symbol'
  
   # Remove stock buttons
   startY = 500
   for stockIndex in range(len(app.portfolio)):
       if (mouseX >= app.width/2 - 200 and mouseX <= app.width/2 - 50 and
           mouseY >= startY + stockIndex*30 - 15 and mouseY <= startY + stockIndex*30 + 15):
           app.portfolio.pop(stockIndex) # Remove the stock
           break


def handleViewPerformancePageClick(app, mouseX, mouseY):
   # Back button
   if (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
       mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight):
       app.currentPage = 'mainPage'
  
   # Timeframe selection
   totalButtons = len(app.timeOptions)
   startX = app.width/2 - (totalButtons * 100) / 2


   for timeframeIndex in range(len(app.timeOptions)):
       buttonX = startX + (timeframeIndex * 100)
       if (mouseX >= buttonX and mouseX <= buttonX + 100 and
           mouseY >= app.height - 50 and mouseY <= app.height):
           app.performanceTimeframe = app.timeOptions[timeframeIndex]
           app.currentStockData = getStockData(app.selectedStock, app.performanceTimeframe)
  
   # Stock selection
   startY = 150
   for stockIndex in range(len(app.portfolio)):
       if (mouseX >= app.width/2 - 200 and mouseX <= app.width/2 + 200 and
           mouseY >= startY + stockIndex*40 and mouseY <= startY + stockIndex*40 + 40):
           app.selectedStock = app.portfolio[stockIndex][0]
           app.currentStockData = getStockData(app.selectedStock, app.performanceTimeframe)


def handleComparisonPageClick(app, mouseX, mouseY):
   # Back button
   if (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
       mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight):
       app.currentPage = 'mainPage'
  
   # Timeframe selection
   totalButtons = len(app.comparisontimeOptions)
   startX = app.width/2 - (totalButtons * 100) / 2


   for timeframeIndex in range(len(app.comparisontimeOptions)):
       buttonX = startX + (timeframeIndex * 100)
       if (mouseX >= buttonX and mouseX <= buttonX + 100 and
           mouseY >= app.height - 50 and mouseY <= app.height):
           app.performanceTimeframe = app.comparisontimeOptions[timeframeIndex]
           if len(app.portfolio) > 0:
               app.currentStockData = getStockData(app.portfolio[0][0], app.performanceTimeframe)


def handleDiversityChartPageClick(app, mouseX, mouseY):
   # Back button
   if (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
       mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight):
       app.currentPage = 'mainPage'


def handlePredictionsPageClick(app, mouseX, mouseY):
   # Back button
   if (mouseX >= app.backButtonX and mouseX <= app.backButtonX + app.backButtonWidth and
       mouseY >= app.backButtonY and mouseY <= app.backButtonY + app.backButtonHeight):
       app.currentPage = 'mainPage'
  
   # Timeframe selection
   predictTimeOptions = ['1mo', '3mo', '6mo']
   totalButtons = len(predictTimeOptions)
   startX = app.width/2 - (totalButtons * 100) / 2
  
   for i in range(len(predictTimeOptions)):
       buttonX = startX + (i * 100)
       if (mouseX >= buttonX and mouseX <= buttonX + 100 and
           mouseY >= app.height - 50 and mouseY <= app.height):
           app.performanceTimeframe = predictTimeOptions[i]
           app.currentStockData = getStockData(app.selectedStock, app.performanceTimeframe)
  
   # Stock selection
   startY = 150
   for i in range(len(app.portfolio)):
       if (mouseX >= app.width/2 - 200 and mouseX <= app.width/2 + 200 and
           mouseY >= startY + i*40 and mouseY <= startY + i*40 + 40):
           app.selectedStock = app.portfolio[i][0]
           app.currentStockData = getStockData(app.selectedStock, app.performanceTimeframe)


def onMousePress(app, mouseX, mouseY):
   if app.currentPage == 'mainPage':
       handleMainPageClick(app, mouseX, mouseY)
   elif app.currentPage == 'managePortfolioPage':
       handleManagePortfolioPageClick(app, mouseX, mouseY)
   elif app.currentPage == 'viewPerformancePage':
       handleViewPerformancePageClick(app, mouseX, mouseY)
   elif app.currentPage == 'comparisonPage':
       handleComparisonPageClick(app, mouseX, mouseY)
   elif app.currentPage == 'diversityChartPage':
       handleDiversityChartPageClick(app, mouseX, mouseY)
   elif app.currentPage == 'predictionsPage':
       handlePredictionsPageClick(app, mouseX, mouseY)


def handleSymbolInput(app, key):
   if key == 'backspace' and len(app.stockSymbol) > 0:
       app.stockSymbol = app.stockSymbol[:-1]
   # got isalnum() from https://www.programiz.com/python-programming/methods/string/isalnum
   elif key.isalnum() and len(app.stockSymbol) < 5 and key != 'backspace':
       app.stockSymbol += key.upper()


def handleSharesInput(app, key):
   if key == 'backspace' and len(app.stockShares) > 0:
       app.stockShares = app.stockShares[:-1]
   elif key.isdigit() and len(app.stockShares) < 5:
       app.stockShares += key


def onKeyPress(app, key):
   if app.currentPage == 'managePortfolioPage':
       if app.isTypingSymbol:
           handleSymbolInput(app, key)
       elif app.isTypingShares:
           handleSharesInput(app, key)


def redrawAll(app):
   if app.currentPage == 'mainPage':
       drawMainPage(app)
   elif app.currentPage == 'managePortfolioPage':
       drawManagePortfolioPage(app)
   elif app.currentPage == 'viewPerformancePage':
       drawViewPerformancePage(app)
   elif app.currentPage == 'comparisonPage':
       drawComparisonPage(app)
   elif app.currentPage == 'diversityChartPage':
      drawDiversityChartPage(app)
   elif app.currentPage == 'predictionsPage':
       drawPredictionsPage(app)


def main():
   runApp(width=1200, height=800)


if __name__ == "__main__":
   main()
