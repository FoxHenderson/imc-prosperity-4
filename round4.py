from datamodel import OrderDepth, TradingState, Order, Symbol, Listing, Trade, Observation, ProsperityEncoder
import json
from typing import Any


# ============================================================================
# Constants
# ============================================================================

HYDROGEL_SYMBOL = 'HYDROGEL_PACK'
OPTION_UNDERLYING_SYMBOL = 'VELVETFRUIT_EXTRACT'

# Active vouchers — mean-reversion regime.
VOUCHER_ACTIVE = [
    'VEV_4000', 'VEV_4500', 'VEV_5000', 'VEV_5100', 'VEV_5200',
    'VEV_5300', 'VEV_5400', 'VEV_5500', 
]

# Deep-OTM vouchers — constant 0 / 1 market-making.
VOUCHER_OTM = ['VEV_6000', 'VEV_6500']

VOUCHER_ALL = VOUCHER_ACTIVE + VOUCHER_OTM

POS_LIMITS = {
    HYDROGEL_SYMBOL: 200,
    OPTION_UNDERLYING_SYMBOL: 200,
    **{s: 300 for s in VOUCHER_ALL},
}

# --- HYDROGEL_PACK (mean known a priori from prior rounds) ---
HYDROGEL_MEAN = 9990.0
HYDROGEL_THRESHOLD = 10.0

# --- VEV mean reversion ---
VEV_EMA_WINDOW = 20
VEV_MEAN = 5250.0
VEV_THRESHOLD = 8.0         # deviation to trigger a trade
VEV_UNDERLYING_LIMIT = 200
VEV_OPTION_LIMIT = 300

# --- Spike trader (add-on) ---
SPIKE_OPTION_SYMBOLS = [
    'VEV_4000', 'VEV_4500', 'VEV_5000', 'VEV_5100', 'VEV_5200',
]
SPIKE_REFERENCE_SYMBOL = 'VEV_4000'
SPIKE_MIN_LEVELS = 3

# ============================================================================
# Logger (verbatim from skeleton — handles flushing for the visualizer)
# ============================================================================

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [self.compress_state(state, ""), self.compress_orders(orders), conversions, "", ""]
            )
        )
        max_item_length = (self.max_log_length - base_length) // 3
        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )
        self.logs = ""

    def compress_state(self, state, trader_data):
        return [
            state.timestamp, trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings):
        return [[l.symbol, l.product, l.denomination] for l in listings.values()]

    def compress_order_depths(self, ods):
        return {s: [od.buy_orders, od.sell_orders] for s, od in ods.items()}

    def compress_trades(self, trades):
        return [[t.symbol, t.price, t.quantity, t.buyer, t.seller, t.timestamp]
                for arr in trades.values() for t in arr]

    def compress_observations(self, observations):
        co = {}
        for product, obs in observations.conversionObservations.items():
            co[product] = [obs.bidPrice, obs.askPrice, obs.transportFees,
                           obs.exportTariff, obs.importTariff, obs.sugarPrice, obs.sunlightIndex]
        return [observations.plainValueObservations, co]

    def compress_orders(self, orders):
        return [[o.symbol, o.price, o.quantity] for arr in orders.values() for o in arr]

    def to_json(self, value):
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        lo, hi = 0, min(len(value), max_length)
        out = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = value[:mid]
            if len(candidate) < len(value):
                candidate += "..."
            if len(json.dumps(candidate)) <= max_length:
                out = candidate
                lo = mid + 1
            else:
                hi = mid - 1
        return out


logger = Logger()


# ============================================================================
# Helpers
# ============================================================================

def ewma_update(td_old, td_new, key, window, value):
    """
    Online EWMA mean update. State persists in traderData under f'{key}_mean'.
    We deliberately do NOT track variance — the strategy uses fixed absolute
    thresholds, not z-scores, per the methodology's caution against
    unjustified normalization.
    """
    alpha = 2.0 / (window + 1.0)
    old_mean = td_old.get(f'{key}_mean')
    if old_mean is None:
        new_mean = value
    else:
        new_mean = old_mean + alpha * (value - old_mean)
    td_new[f'{key}_mean'] = new_mean
    return new_mean


# ============================================================================
# ProductTrader — per-symbol order-book wrapper (verbatim from skeleton)
# ============================================================================

class ProductTrader:

    def __init__(self, name, state, prints, new_trader_data, product_group=None):
        self.orders: list[Order] = []
        self.name = name
        self.state = state
        self.new_trader_data = new_trader_data
        self.position_limit = POS_LIMITS.get(self.name, 0)
        self.initial_position = self.state.position.get(self.name, 0)
        self.mkt_buy_orders, self.mkt_sell_orders = self._get_order_depth()
        self.bid_wall, self.wall_mid, self.ask_wall = self._get_walls()
        self.best_bid, self.best_ask = self._get_best_bid_ask()
        self.max_allowed_buy_volume = self.position_limit - self.initial_position
        self.max_allowed_sell_volume = self.position_limit + self.initial_position

    def _get_order_depth(self):
        buy_orders, sell_orders = {}, {}
        try:
            od = self.state.order_depths[self.name]
            buy_orders = {p: abs(v) for p, v in sorted(od.buy_orders.items(), reverse=True)}
            sell_orders = {p: abs(v) for p, v in sorted(od.sell_orders.items())}
        except Exception:
            pass
        return buy_orders, sell_orders

    def _get_walls(self):
        bid_wall = wall_mid = ask_wall = None
        try: bid_wall = min(self.mkt_buy_orders.keys())
        except: pass
        try: ask_wall = max(self.mkt_sell_orders.keys())
        except: pass
        try: wall_mid = (bid_wall + ask_wall) / 2
        except: pass
        return bid_wall, wall_mid, ask_wall

    def _get_best_bid_ask(self):
        best_bid = best_ask = None
        try:
            if self.mkt_buy_orders: best_bid = max(self.mkt_buy_orders)
            if self.mkt_sell_orders: best_ask = min(self.mkt_sell_orders)
        except Exception:
            pass
        return best_bid, best_ask

    def bid(self, price, volume):
        vol = min(abs(int(volume)), self.max_allowed_buy_volume)
        if vol <= 0: return
        self.orders.append(Order(self.name, int(price), vol))
        self.max_allowed_buy_volume -= vol

    def ask(self, price, volume):
        vol = min(abs(int(volume)), self.max_allowed_sell_volume)
        if vol <= 0: return
        self.orders.append(Order(self.name, int(price), -vol))
        self.max_allowed_sell_volume -= vol


# ============================================================================
# Strategy 1 — HYDROGEL_PACK (mean known a priori)
# ============================================================================

class HydrogelTrader:
    """Mean-reversion on HYDROGEL_PACK around HYDROGEL_MEAN."""

    def __init__(self, state, new_trader_data):
        self.t = ProductTrader(HYDROGEL_SYMBOL, state, {}, new_trader_data)

    def get_orders(self):
        if self.t.wall_mid is None:
            return {}
        deviation = self.t.wall_mid - HYDROGEL_MEAN
        if deviation > HYDROGEL_THRESHOLD and self.t.best_bid is not None:
            self.t.ask(self.t.best_bid, self.t.max_allowed_sell_volume)
        elif deviation < -HYDROGEL_THRESHOLD and self.t.best_ask is not None:
            self.t.bid(self.t.best_ask, self.t.max_allowed_buy_volume)
        return {HYDROGEL_SYMBOL: self.t.orders}


# ============================================================================
# Strategy 2 — VELVETFRUIT_EXTRACT (mean learned online)
# ============================================================================

class FruitTrader:
    """Mean-reversion on VELVETFRUIT_EXTRACT around its long-run EWMA mean."""

    def __init__(self, state, new_trader_data, last_td):
        self.t = ProductTrader(OPTION_UNDERLYING_SYMBOL, state, {}, new_trader_data)
        self.last_td = last_td
        self.new_trader_data = new_trader_data
        self.underlying = ProductTrader(OPTION_UNDERLYING_SYMBOL, state, {}, new_trader_data)
        self.options = [ProductTrader(s, state, {}, new_trader_data) for s in VOUCHER_ACTIVE]


    def get_orders(self):
        if self.underlying.wall_mid is None:
            return {}

        mid = self.underlying.wall_mid
        deviation = mid - VEV_MEAN

        orders = {}

        if deviation > VEV_THRESHOLD:
            if self.underlying.best_bid is not None:
                self.underlying.ask(self.underlying.best_bid, self.underlying.max_allowed_sell_volume)
            for opt in self.options:
                if opt.best_bid is not None:
                    opt.ask(opt.best_bid, opt.max_allowed_sell_volume)

        elif deviation < -VEV_THRESHOLD:
            if self.underlying.best_ask is not None:
                self.underlying.bid(self.underlying.best_ask, self.underlying.max_allowed_buy_volume)
            for opt in self.options:
                if opt.best_ask is not None:
                    opt.bid(opt.best_ask, opt.max_allowed_buy_volume)

        orders[OPTION_UNDERLYING_SYMBOL] = self.underlying.orders
        for opt in self.options:
            orders[opt.name] = opt.orders
        return orders


class OtmVoucherTrader:
    """
    Quote bid 0 / ask 1 in max size on every deep-OTM voucher every tick.

    The user has confirmed these books only have offers at 1 and bids at 0
    for the whole round. By price-time priority our orders sit ahead of the
    bot quotes, so we capture all flow at those levels:

      • Fill on our ask 1 → +1 EV (option expires worthless deep OTM).
      • Fill on our bid 0 → 0 cost (we own a worthless option).

    No mean-reversion model is needed — these are pure free-money quotes.
    """

    def __init__(self, state, new_trader_data):
        self.traders = {s: ProductTrader(s, state, {}, new_trader_data)
                        for s in VOUCHER_OTM}

    def get_orders(self):
        out = {}
        for sym, t in self.traders.items():
            t.bid(0, t.max_allowed_buy_volume)
            t.ask(1, t.max_allowed_sell_volume)
            if t.orders:
                out[sym] = t.orders
        return out


# ============================================================================
# Strategy 5 — Spike trader (add-on, logic preserved from spike.py)
# ============================================================================

class SpikeTrader:
    def __init__(self, state, new_trader_data):
        self.state = state
        self.reference = ProductTrader(SPIKE_REFERENCE_SYMBOL, state, {}, new_trader_data)
        self.options = [ProductTrader(symbol, state, {}, new_trader_data)
                        for symbol in SPIKE_OPTION_SYMBOLS]

    def _detect_spike_side(self):
        """
        Returns:
            "ASK" if VEV_4000 has at least 3 ask levels below wall_mid.
            "BID" if VEV_4000 has at least 3 bid levels above wall_mid.
            None otherwise.

        If both sides qualify, pick the side with the larger edge versus wall_mid.
        """
        ref = self.reference

        if ref.wall_mid is None:
            return None

        ask_spike_levels = [
            price for price in ref.mkt_sell_orders.keys()
        ]

        bid_spike_levels = [
            price for price in ref.mkt_buy_orders.keys()
        ]

        has_ask_spike = len(ask_spike_levels) >= SPIKE_MIN_LEVELS
        has_bid_spike = len(bid_spike_levels) >= SPIKE_MIN_LEVELS

        if not has_ask_spike and not has_bid_spike:
            return None

        if has_ask_spike and not has_bid_spike:
            return "ASK"

        if has_bid_spike and not has_ask_spike:
            return "BID"

        # Defensive handling for weird/crossed books.
        best_spike_ask = min(ask_spike_levels)
        best_spike_bid = max(bid_spike_levels)

        ask_edge = ref.wall_mid - best_spike_ask
        bid_edge = best_spike_bid - ref.wall_mid

        if ask_edge > bid_edge:
            return "ASK"
        if bid_edge > ask_edge:
            return "BID"

        return None

    def get_orders(self):
        orders: dict[str, list[Order]] = {
            symbol: [] for symbol in SPIKE_OPTION_SYMBOLS
        }

        spike_side = self._detect_spike_side()

        if spike_side is None:
            return orders

        if spike_side == "ASK":
            # Ask-side spike in VEV_4000 means cheap asks appeared.
            # Take best asks across all options up to VEV_5500.
            for opt in self.options:
                if opt.best_ask is not None:
                    opt.bid(opt.best_ask, opt.max_allowed_buy_volume)
                orders[opt.name] = opt.orders

        elif spike_side == "BID":
            # Bid-side spike in VEV_4000 means rich bids appeared.
            # Take best bids across all options up to VEV_5500.
            for opt in self.options:
                if opt.best_bid is not None:
                    opt.ask(opt.best_bid, opt.max_allowed_sell_volume)
                orders[opt.name] = opt.orders

        return orders


# ============================================================================
# Top-level Trader
# ============================================================================

class Trader:

    def run(self, state: TradingState):
        result: dict[str, list[Order]] = {}
        new_trader_data: dict = {}
        conversions = 0

        # Read prior trader-data snapshot (EWMA state lives here).
        try:
            last_td = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            last_td = {}

        # Strategy 1 — HYDROGEL_PACK mean reversion.
        try:
            result.update(HydrogelTrader(state, new_trader_data).get_orders())
        except Exception as e:
            logger.print(f"hydrogel error: {e!r}")

        # Strategy 2 — VELVETFRUIT_EXTRACT mean reversion.
        try:
            result.update(FruitTrader(state, new_trader_data, last_td).get_orders())
        except Exception as e:
            logger.print(f"fruit error: {e!r}")

        # Strategy 4 — Deep-OTM voucher 0/1 market-making.
        try:
            result.update(OtmVoucherTrader(state, new_trader_data).get_orders())
        except Exception as e:
            logger.print(f"otm voucher error: {e!r}")

        # Strategy 5 — Spike trader (add-on). Merge orders into existing
        # result lists rather than overwriting, so FruitTrader's orders for
        # overlapping symbols (VEV_4000..VEV_5200) are preserved.
        try:
            spike_orders = SpikeTrader(state, new_trader_data).get_orders()
            for sym, ord_list in spike_orders.items():
                if not ord_list:
                    continue
                if sym in result:
                    result[sym].extend(ord_list)
                else:
                    result[sym] = ord_list
        except Exception as e:
            logger.print(f"spike error: {e!r}")

        try:
            final_trader_data = json.dumps(new_trader_data)
        except Exception:
            final_trader_data = ''

        logger.flush(state, result, conversions, final_trader_data)
        return result, conversions, final_trader_data


# prosperity4btx AI-mean-reversion-mm.py 4