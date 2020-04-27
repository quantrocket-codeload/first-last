# first-last

Intraday momentum strategy that buys (sells) the S&P 500 when the first half hour return and penultimate half hour return are both positive (negative). Uses VIX filter to restrict strategy to high volatility regimes. Uses 1-minute SPY data from QuantRocket and 30-minute VIX data from Interactive Brokers. Runs in Moonshot.

## Clone in QuantRocket

CLI:

```shell
quantrocket codeload clone 'first-last'
```

Python:

```python
from quantrocket.codeload import clone
clone("first-last")
```

## Browse in GitHub

Start here: [first_last/Introduction.ipynb](first_last/Introduction.ipynb)

***

Find more code in QuantRocket's [Codeload Library](https://www.quantrocket.com/code/)
