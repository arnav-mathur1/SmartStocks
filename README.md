# SmartStocks
CMU 15-112 Final Project

SmartStocks is a stock application where users can improve their portfolio with the information provided in the app. \
The user can add and remove stocks in their portfolio and view the performance of each of their stocks over multiple time periods. \
Additionally, the user can observe their portfolio performance in comparison to a common index like the S&P 500 and can analyze the diversity of their portfolio by sector categories and the individual stocks themselves. \ 
Lastly, the user is given a recommendation on whether to sell, hold, or buy a particular stock in their portfolio and is provided a future prediction of the stock performances in their portfolio.

How to Run
Install Python 3.12 and download the “test.py” file \
Open the folder containing the file in an editor such as VSCode, then open a terminal in that folder \
Create a virtual environment by running “python3 -m venv .venv” and activate it by running “source .venv/bin/activate” on macOS or Linux, or “.venv\Scripts\activate” on Windows \
Install the required libraries by running “python -m pip install yfinance pandas pygame-ce cmu-graphics==1.1.48 cmu-graphics-helpers==0.1.3” \
Finally, run the application with “python test.py” \
If CMU Graphics does not install normally, follow the operating-system instructions at https://academy.cs.cmu.edu/desktop.
