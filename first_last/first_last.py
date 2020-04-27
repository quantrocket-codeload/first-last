# Copyright 2020 QuantRocket LLC - All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from moonshot import Moonshot
from moonshot.commission import PerShareCommission
from quantrocket import get_prices

class USStockCommission(PerShareCommission):
    BROKER_COMMISSION_PER_SHARE = 0.005

class FirstHalfHourPredictsLastHalfHour(Moonshot):
    """
    Intraday strategy that buys (sells) if the market is up (down) during the first
    and penultimate half-hour.
    """

    CODE = 'first-last'
    DB = 'usstock-1min'
    DB_TIMES = ['10:00:00', '15:00:00', '15:30:00', '15:59:00']
    DB_FIELDS = ['Open','Close']
    SIDS = ["FIBBG000BDTBL9"]
    COMMISSION_CLASS = USStockCommission
    SLIPPAGE_BPS = 0.5
    MIN_VIX = None
    BENCHMARK = "FIBBG000BDTBL9"
    BENCHMARK_TIME = "15:59:00"

    def prices_to_signals(self, prices):

        closes = prices.loc["Close"]
        opens = prices.loc["Open"]

        # Calculate first half-hour returns (including overnight return)
        prior_closes = closes.xs('15:59:00', level="Time").shift()
        ten_oclock_prices = opens.xs('10:00:00', level="Time")
        first_half_hour_returns = (ten_oclock_prices - prior_closes) / prior_closes

        # Calculate penultimate half-hour returns
        fifteen_oclock_prices = opens.xs('15:00:00', level="Time")
        fifteen_thirty_prices = opens.xs('15:30:00', level="Time")
        penultimate_half_hour_returns = (fifteen_thirty_prices - fifteen_oclock_prices) / fifteen_oclock_prices

        # long when both are positive, short when both are negative
        long_signals = (first_half_hour_returns > 0) & (penultimate_half_hour_returns > 0)
        short_signals = (first_half_hour_returns < 0) & (penultimate_half_hour_returns < 0)

        # Combine long and short signals
        signals = long_signals.astype(int).where(long_signals, -short_signals.astype(int))

        # filter by VIX
        if self.MIN_VIX:
            # Query VIX at 15:30 NY time (= close of 14:00:00 bar because VIX is Chicago time)
            vix = get_prices("vix-30min",
                             fields="Close",
                             start_date=signals.index.min(),
                             end_date=signals.index.max(),
                             times="14:00:00")
            # extract VIX and squeeze single-column DataFrame to Series
            vix = vix.loc["Close"].xs("14:00:00", level="Time").squeeze()
            # reshape VIX like signals
            vix = signals.apply(lambda x: vix)
            signals = signals.where(vix >= self.MIN_VIX, 0)

        return signals

    def signals_to_target_weights(self, signals, prices):

        # only one instrument, so allocate all capital
        target_weights = signals.copy()
        return target_weights

    def target_weights_to_positions(self, target_weights, prices):

        # We enter on the same day as the signals/target_weights
        positions = target_weights.copy()
        return positions

    def positions_to_gross_returns(self, positions, prices):

        opens = prices.loc["Open"]
        closes = prices.loc["Close"]

        # Our signal came at 15:30 and we enter at 15:30
        entry_prices = opens.xs("15:30:00", level="Time")
        session_closes = closes.xs("15:59:00", level="Time")

        pct_changes = (session_closes - entry_prices) / entry_prices
        gross_returns = pct_changes * positions
        return gross_returns
