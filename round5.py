import json
import math
from datamodel import *
from typing import Any
import numpy as np


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(
        self,
        state: TradingState,
        orders: dict[Symbol, list[Order]],
        conversions: int,
        trader_data: str,
    ) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        max_item_length = max(0, (self.max_log_length - base_length) // 3)

        print(
            self.to_json(
                [
                    self.compress_state(
                        state,
                        self.truncate(state.traderData, max_item_length),
                    ),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []

        for listing in listings.values():
            try:
                compressed.append(
                    [listing.symbol, listing.product, listing.denomination]
                )
            except Exception:
                compressed.append(
                    [
                        listing["symbol"],
                        listing["product"],
                        listing["denomination"],
                    ]
                )

        return compressed

    def compress_order_depths(
        self,
        order_depths: dict[Symbol, OrderDepth],
    ) -> dict[Symbol, list[Any]]:
        return {
            symbol: [order_depth.buy_orders, order_depth.sell_orders]
            for symbol, order_depth in order_depths.items()
        }

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []

        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}

        try:
            items = observations.conversionObservations.items()
        except Exception:
            items = []

        for product, observation in items:
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        try:
            plain = observations.plainValueObservations
        except Exception:
            plain = {}

        return [plain, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []

        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if max_length <= 0:
            return ""

        lo, hi = 0, min(len(value), max_length)
        out = ""

        while lo <= hi:
            mid = (lo + hi) // 2

            candidate = value[:mid]
            if len(candidate) < len(value):
                candidate += "..."

            encoded_candidate = json.dumps(candidate)

            if len(encoded_candidate) <= max_length:
                out = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        return out


logger = Logger()

class Trader:
    HOLD_TICKS = 3

    GALAXY = [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ]

    SLEEP = [
        "SLEEP_POD_SUEDE",
        "SLEEP_POD_LAMB_WOOL",
        "SLEEP_POD_POLYESTER",
        "SLEEP_POD_NYLON",
        "SLEEP_POD_COTTON",
    ]

    ROBOTS = [
        "ROBOT_VACUUMING",
        "ROBOT_MOPPING",
        "ROBOT_DISHES",
        "ROBOT_LAUNDRY",
        "ROBOT_IRONING",
    ]

    PANELS = [
        "PANEL_1X2",
        "PANEL_2X2",
        "PANEL_1X4",
        "PANEL_2X4",
        "PANEL_4X4",
    ]

    SNACKS = [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_VANILLA",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY",
    ]

    PEBBLES = [
        "PEBBLES_XS",
        "PEBBLES_S",
        "PEBBLES_M",
        "PEBBLES_L",
        "PEBBLES_XL",
    ]

    TRANSLATORS = [
        "TRANSLATOR_SPACE_GRAY",
        "TRANSLATOR_ASTRO_BLACK",
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST",
        "TRANSLATOR_VOID_BLUE",
    ]

    OXYGEN = [
        "OXYGEN_SHAKE_MORNING_BREATH",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_CHOCOLATE",
        "OXYGEN_SHAKE_GARLIC",
    ]

    MICROCHIPS = [
        "MICROCHIP_CIRCLE",
        "MICROCHIP_OVAL",
        "MICROCHIP_SQUARE",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_TRIANGLE",
    ]

    UV_VISORS = [
        "UV_VISOR_YELLOW",
        "UV_VISOR_AMBER",
        "UV_VISOR_ORANGE",
        "UV_VISOR_RED",
        "UV_VISOR_MAGENTA",
    ]

    GROUPS = {
        "GALAXY": GALAXY,
        "SLEEP": SLEEP,
        "ROBOTS": ROBOTS,
        "PANELS": PANELS,
        "SNACKS": SNACKS,
        "PEBBLES": PEBBLES,
        "TRANSLATORS": TRANSLATORS,
        "OXYGEN": OXYGEN,
        "MICROCHIPS": MICROCHIPS,
        "UV_VISORS": UV_VISORS,
    }

    PRODUCTS = sorted(set(
        GALAXY
        + SLEEP
        + ROBOTS
        + PANELS
        + SNACKS
        + PEBBLES
        + TRANSLATORS
        + OXYGEN
        + MICROCHIPS
        + UV_VISORS
    ))

    POS_SIZE_LIMITS = {product: 10 for product in PRODUCTS}

    PAIRS = {
        # ----------------------------- #
        # Tier 1 mean-reversion pairs
        # ----------------------------- #
        "ROBOTS_minus_PANELS": {
            "group_a": "ROBOTS",
            "group_b": "PANELS",
            "spread_type": "difference",
            "entry_z": 2.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 1000,
            "base_size": 3,
            "max_size": 7,
        },

        "MICROCHIPS_minus_UV_VISORS": {
            "group_a": "MICROCHIPS",
            "group_b": "UV_VISORS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 5000,
            "base_size": 3,
            "max_size": 7,
        },

        "ROBOTS_minus_SNACKS": {
            "group_a": "ROBOTS",
            "group_b": "SNACKS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 5000,
            "base_size": 3,
            "max_size": 7,
        },

        "PEBBLES_minus_TRANSLATORS": {
            "group_a": "PEBBLES",
            "group_b": "TRANSLATORS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 5000,
            "base_size": 3,
            "max_size": 7,
        },

        "PEBBLES_plus_PANELS": {
            "group_a": "PEBBLES",
            "group_b": "PANELS",
            "spread_type": "sum",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 1000,
            "base_size": 2,
            "max_size": 6,
        },

        "GALAXY_minus_UV_VISORS": {
            "group_a": "GALAXY",
            "group_b": "UV_VISORS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 5000,
            "base_size": 2,
            "max_size": 6,
        },

        "GALAXY_plus_ROBOTS": {
            "group_a": "GALAXY",
            "group_b": "ROBOTS",
            "spread_type": "sum",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 1000,
            "base_size": 2,
            "max_size": 6,
        },

        "SLEEP_plus_ROBOTS": {
            "group_a": "SLEEP",
            "group_b": "ROBOTS",
            "spread_type": "sum",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 5000,
            "base_size": 2,
            "max_size": 6,
        },

        "SLEEP_minus_UV_VISORS": {
            "group_a": "SLEEP",
            "group_b": "UV_VISORS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 500,
            "base_size": 2,
            "max_size": 6,
        },

        "GALAXY_minus_SLEEP": {
            "group_a": "GALAXY",
            "group_b": "SLEEP",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 1001.0,
            "max_hold": 1000,
            "base_size": 2,
            "max_size": 6,
        },

        "TRANSLATORS_plus_PANELS": {
            "group_a": "TRANSLATORS",
            "group_b": "PANELS",
            "spread_type": "sum",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 1000,
            "base_size": 2,
            "max_size": 5,
        },

        "SLEEP_minus_TRANSLATORS": {
            "group_a": "SLEEP",
            "group_b": "TRANSLATORS",
            "spread_type": "difference",
            "entry_z": 2.0,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 1000,
            "base_size": 2,
            "max_size": 5,
        },

        "SLEEP_plus_OXYGEN": {
            "group_a": "SLEEP",
            "group_b": "OXYGEN",
            "spread_type": "sum",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 1000,
            "base_size": 2,
            "max_size": 5,
        },

        "PEBBLES_plus_ROBOTS": {
            "group_a": "PEBBLES",
            "group_b": "ROBOTS",
            "spread_type": "sum",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 501.0,
            "max_hold": 100,
            "base_size": 1,
            "max_size": 4,
        },
        # ----------------------------- #
        # Tier 2 mean-reversion pairs
        # ----------------------------- #
        "MICROCHIPS_minus_TRANSLATORS": {
            "group_a": "MICROCHIPS",
            "group_b": "TRANSLATORS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 2500,
            "base_size": 2,
            "max_size": 5,
        },

        "MICROCHIPS_minus_SNACKS": {
            "group_a": "MICROCHIPS",
            "group_b": "SNACKS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 2500,
            "base_size": 2,
            "max_size": 5,
        },

        "MICROCHIPS_minus_PEBBLES": {
            "group_a": "MICROCHIPS",
            "group_b": "PEBBLES",
            "spread_type": "difference",
            "entry_z": 2.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 2500,
            "base_size": 2,
            "max_size": 5,
        },

        "GALAXY_minus_MICROCHIPS": {
            "group_a": "GALAXY",
            "group_b": "MICROCHIPS",
            "spread_type": "difference",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 2500,
            "base_size": 2,
            "max_size": 5,
        },

        "MICROCHIPS_plus_OXYGEN": {
            "group_a": "MICROCHIPS",
            "group_b": "OXYGEN",
            "spread_type": "sum",
            "entry_z": 1.5,
            "exit_z": 0.75,
            "ew_alpha": 2.0 / 2501.0,
            "max_hold": 2500,
            "base_size": 2,
            "max_size": 5,
        },
    }

    # All ten baskets are now used by the Tier 1 + Tier 2 pair book.
    PAIR_PRODUCTS = PRODUCTS[:]

    # Bump this so old traderData does not reuse stale pair stats/signals.
    MEMORY_VERSION = 8


    MIN_OBS = 250
    MIN_STD = 1e-6

    TAKE_MARGIN = 1
    NEUTRALISE_MARGIN = 0

    # stop overtrading
    NEUTRALISE_HYSTERESIS_QTY = 1

    MM_MARGIN = 1
    SIGNAL_MM_MARGIN = 2
    MM_HALF_RANGE_CAP = 4
    BOT_HALF_SPREAD_THRESHOLD = 100

    PEBBLE_LONG_EXIT_BID_SUM = 49990
    PEBBLE_SHORT_EXIT_ASK_SUM = 50010
    PEBBLE_MM_IMPROVE = 1

    def __init__(self):
        pass

    # ------------------------------------------------------------------ #
    # Memory
    # ------------------------------------------------------------------ #

    def fresh_trader_data(self):
        return {
            "v": self.MEMORY_VERSION,
            "last_ts": None,
            "open": {},
            "last_wall_mid": {},
            "pair_stats": {
                pair_name: {"n": 0, "mean": 0.0, "var": 0.0}
                for pair_name in self.PAIRS
            },
            "signals": {
                pair_name: {"side": 0, "size": 0, "hold_ticks": 0}
                for pair_name in self.PAIRS
            },
            "discrete": {
                product: {"p1": None, "p2": None, "t": 0, "g": 0}
                for product in self.PRODUCTS
            },
        }

    def load_trader_data(self, raw):
        if not raw:
            return self.fresh_trader_data()

        try:
            data = json.loads(raw)
        except Exception:
            return self.fresh_trader_data()

        if not isinstance(data, dict) or data.get("v") != self.MEMORY_VERSION:
            return self.fresh_trader_data()

        data.setdefault("open", {})
        data.setdefault("last_wall_mid", {})
        data.setdefault("pair_stats", {})
        data.setdefault("signals", {})
        data.setdefault("discrete", {})

        for pair_name in self.PAIRS:
            data["pair_stats"].setdefault(pair_name, {"n": 0, "mean": 0.0, "var": 0.0})
            data["signals"].setdefault(pair_name, {"side": 0, "size": 0, "hold_ticks": 0})

        for product in self.PRODUCTS:
            data["discrete"].setdefault(product, {"p1": None, "p2": None, "t": 0, "g": 0})

        return data

    # ------------------------------------------------------------------ #
    # Book helpers
    # ------------------------------------------------------------------ #

    def get_pos_set_limits(self, state: TradingState):
        position_sizes = {
            product: state.position.get(product, 0)
            for product in self.POS_SIZE_LIMITS
        }

        self.initial_position_sizes = position_sizes.copy()
        self.implied_position_sizes = position_sizes.copy()

        self.remaining_bid_volume = {
            product: self.POS_SIZE_LIMITS[product] - position_sizes[product]
            for product in self.POS_SIZE_LIMITS
        }

        self.remaining_ask_volume = {
            product: self.POS_SIZE_LIMITS[product] + position_sizes[product]
            for product in self.POS_SIZE_LIMITS
        }

    def get_bids_asks(self, state: TradingState):
        self.bids = {}
        self.asks = {}

        for product in self.PRODUCTS:
            od = state.order_depths.get(product, None)

            if od is None:
                self.bids[product] = {}
                self.asks[product] = {}
                continue

            self.bids[product] = {
                int(price): abs(int(volume))
                for price, volume in sorted(
                    od.buy_orders.items(),
                    key=lambda x: x[0],
                    reverse=True,
                )
                if volume != 0
            }

            self.asks[product] = {
                int(price): abs(int(volume))
                for price, volume in sorted(
                    od.sell_orders.items(),
                    key=lambda x: x[0],
                )
                if volume != 0
            }

    def wall_mid(self, product):
        bids = self.bids.get(product, {})
        asks = self.asks.get(product, {})

        if bids and asks:
            bid_wall = min(bids)
            ask_wall = max(asks)
            wall_mid = (bid_wall + ask_wall) / 2
            self.trader_data["last_wall_mid"][product] = wall_mid
            return wall_mid

        return self.trader_data.get("last_wall_mid", {}).get(product, None)

    def best_bid(self, product):
        bids = self.bids.get(product, {})
        return max(bids.keys()) if bids else None

    def best_ask(self, product):
        asks = self.asks.get(product, {})
        return min(asks.keys()) if asks else None

    def bid_wall(self, product):
        bids = self.bids.get(product, {})
        return min(bids.keys()) if bids else None

    def ask_wall(self, product):
        asks = self.asks.get(product, {})
        return max(asks.keys()) if asks else None

    def place_bid(self, product, price, volume):
        volume = abs(max(0, int(volume)))
        volume = min(volume, self.remaining_bid_volume.get(product, 0))

        if volume <= 0:
            return None

        price = int(round(price))
        order = Order(product, price, volume)

        self.result[product].append(order)
        self.remaining_bid_volume[product] -= volume
        self.implied_position_sizes[product] += volume

        return order

    def place_ask(self, product, price, volume):
        volume = abs(max(0, int(volume)))
        volume = min(volume, self.remaining_ask_volume.get(product, 0))

        if volume <= 0:
            return None

        price = int(round(price))
        order = Order(product, price, -volume)

        self.result[product].append(order)
        self.remaining_ask_volume[product] -= volume
        self.implied_position_sizes[product] -= volume

        return order

    # ------------------------------------------------------------------ #
    # Discrete regime logic
    # ------------------------------------------------------------------ #

    def is_round_100(self, x):
        if x is None:
            return False
        try:
            return abs(x - round(x / 100) * 100) < 1e-9
        except Exception:
            return False

    def update_product_discrete_state(self, product, wm):
        d = self.trader_data["discrete"][product]

        prev1 = d.get("p1", None)
        prev2 = d.get("p2", None)
        ticks_left = int(d.get("t", 0))
        target = int(d.get("g", 0))

        is_discrete = (
            self.is_round_100(wm)
            and self.is_round_100(prev1)
            and self.is_round_100(prev2)
        )

        if wm is None:
            d["p1"] = wm
            d["p2"] = prev1
            d["t"] = ticks_left
            d["g"] = target
            return False, target

        if not is_discrete:
            target = 0
            ticks_left = 0
        else:
            move = wm - prev1

            if move != 0:
                target = -self.POS_SIZE_LIMITS[product] if move > 0 else self.POS_SIZE_LIMITS[product]
                ticks_left = self.HOLD_TICKS

            elif ticks_left > 0:
                ticks_left -= 1
                if ticks_left == 0:
                    target = 0

        d["p1"] = wm
        d["p2"] = prev1
        d["t"] = ticks_left
        d["g"] = target

        return is_discrete, target

    def group_is_discrete(self, group_name, group_discrete_flags):
        return bool(group_discrete_flags.get(group_name, False))

    def reset_pair_signal(self, pair_name):
        sig = self.trader_data["signals"][pair_name]
        sig["side"] = 0
        sig["size"] = 0
        sig["hold_ticks"] = 0

    def reach_target_aggressively(self, product, target_position):
        """
        Exact discrete execution style:
        target > current: buy at ask_wall.
        target < current: sell at bid_wall.
        """
        current = self.implied_position_sizes.get(product, 0)
        delta = int(target_position) - current

        if delta > 0:
            ask_wall = self.ask_wall(product)
            if ask_wall is not None:
                self.place_bid(product, ask_wall, delta)

        elif delta < 0:
            bid_wall = self.bid_wall(product)
            if bid_wall is not None:
                self.place_ask(product, bid_wall, -delta)

    # ------------------------------------------------------------------ #
    # Pair stats
    # ------------------------------------------------------------------ #

    def pair_z_before_update(self, pair_name, spread):
        stats = self.trader_data["pair_stats"][pair_name]

        n = int(stats.get("n", 0))
        mean = float(stats.get("mean", 0.0))
        var = max(float(stats.get("var", 0.0)), 0.0)

        if n < self.MIN_OBS:
            return None, mean, math.sqrt(max(var, self.MIN_STD ** 2))

        std = math.sqrt(max(var, self.MIN_STD ** 2))

        if not math.isfinite(std) or std <= 0:
            return None, mean, std

        return (spread - mean) / std, mean, std

    def update_pair_stats(self, pair_name, spread):
        if not math.isfinite(spread):
            return

        spec = self.PAIRS[pair_name]
        stats = self.trader_data["pair_stats"][pair_name]

        n = int(stats.get("n", 0))
        mean = float(stats.get("mean", 0.0))
        var = max(float(stats.get("var", 0.0)), 0.0)

        if n <= 0:
            stats["n"] = 1
            stats["mean"] = spread
            stats["var"] = 0.0
            return

        alpha = 1.0 / (n + 1) if n < self.MIN_OBS else float(spec["ew_alpha"])

        delta = spread - mean
        stats["mean"] = float(mean + alpha * delta)
        stats["var"] = float(max((1.0 - alpha) * (var + alpha * delta * delta), 0.0))
        stats["n"] = min(n + 1, 1_000_000)

    # ------------------------------------------------------------------ #
    # Pair signal logic
    # ------------------------------------------------------------------ #

    def target_size_from_z(self, z, spec):
        abs_z = abs(z)
        entry_z = float(spec["entry_z"])
        base_size = int(spec["base_size"])
        max_size = int(spec["max_size"])

        strength = min(
            1.0,
            max(0.0, (abs_z - entry_z) / max(1e-9, 4.0 - entry_z)),
        )

        return max(1, min(max_size, int(round(base_size + strength * (max_size - base_size)))))

    def update_pair_signal_state(self, pair_name, z):
        spec = self.PAIRS[pair_name]
        sig = self.trader_data["signals"][pair_name]

        prev_side = int(sig.get("side", 0))
        prev_size = int(sig.get("size", 0))
        prev_hold = int(sig.get("hold_ticks", 0))

        entry_z = float(spec["entry_z"])
        exit_z = float(spec["exit_z"])
        max_hold = int(spec["max_hold"])

        if z is None or not math.isfinite(z):
            sig["side"] = 0
            sig["size"] = 0
            sig["hold_ticks"] = 0
            return 0, 0, "warmup"

        abs_z = abs(z)

        if prev_side != 0 and prev_hold >= max_hold:
            sig["side"] = 0
            sig["size"] = 0
            sig["hold_ticks"] = 0
            return 0, 0, "max_hold_flat"

        if abs_z <= exit_z:
            sig["side"] = 0
            sig["size"] = 0
            sig["hold_ticks"] = 0
            return 0, 0, "exit_flat"

        if z >= entry_z:
            side = -1
            size = self.target_size_from_z(z, spec)
            sig["side"] = side
            sig["size"] = size
            sig["hold_ticks"] = 1 if prev_side != side else prev_hold + 1
            return side, size, "short_spread"

        if z <= -entry_z:
            side = 1
            size = self.target_size_from_z(z, spec)
            sig["side"] = side
            sig["size"] = size
            sig["hold_ticks"] = 1 if prev_side != side else prev_hold + 1
            return side, size, "long_spread"

        if prev_side != 0:
            sig["side"] = prev_side
            sig["size"] = prev_size
            sig["hold_ticks"] = prev_hold + 1
            return prev_side, prev_size, "hold_signal"

        sig["side"] = 0
        sig["size"] = 0
        sig["hold_ticks"] = 0
        return 0, 0, "neutral"

    def add_pair_desired_positions(self, desired_positions, spec, spread_side, target_size):
        if spread_side == 0 or target_size == 0:
            return

        products_a = self.GROUPS[spec["group_a"]]
        products_b = self.GROUPS[spec["group_b"]]
        spread_type = spec["spread_type"]

        if spread_type == "difference":
            for p in products_a:
                desired_positions[p] += spread_side * target_size
            for p in products_b:
                desired_positions[p] -= spread_side * target_size

        elif spread_type == "sum":
            for p in products_a:
                desired_positions[p] += spread_side * target_size
            for p in products_b:
                desired_positions[p] += spread_side * target_size

    def cap_desired_positions(self, desired_positions):
        out = {}
        for p, desired in desired_positions.items():
            limit = self.POS_SIZE_LIMITS[p]
            out[p] = int(max(-limit, min(limit, round(desired))))
        return out

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #

    def trade_pebbles_sum_mm(self):
        """
        Pebbles trade around a roughly-constant basket sum (~50000).
        Two regimes:
          * bid_sum > PEBBLE_LONG_EXIT_BID_SUM  -> basket too rich on the bid side
                -> SELL each pebble at its best bid (ENTRY into shorts and EXIT of longs).
          * ask_sum < PEBBLE_SHORT_EXIT_ASK_SUM -> basket too cheap on the ask side
                -> BUY each pebble at its best ask (ENTRY into longs and EXIT of shorts).
        Outside those regimes we just market-make tightly inside the book.

        When sell_signal is active we suppress new MM bids so we don't immediately
        re-buy what we just sold. Symmetric for buy_signal.
        """
        best_bids = {p: self.best_bid(p) for p in self.PEBBLES}
        best_asks = {p: self.best_ask(p) for p in self.PEBBLES}

        if any(best_bids[p] is None or best_asks[p] is None for p in self.PEBBLES):
            return False

        bid_sum = sum(best_bids[p] for p in self.PEBBLES)
        ask_sum = sum(best_asks[p] for p in self.PEBBLES)

        sell_signal = bid_sum > self.PEBBLE_LONG_EXIT_BID_SUM
        buy_signal = ask_sum < self.PEBBLE_SHORT_EXIT_ASK_SUM

        # ---- ENTRY + EXIT (sell side) ----
        # Lift the bid on every pebble. Bound by remaining_ask_volume only,
        # so we can run all the way to the short position limit (not just back to flat).
        if sell_signal:
            for product in self.PEBBLES:
                best_bid_p = self.best_bid(product)
                if best_bid_p is None:
                    continue

                available = self.bids[product].get(best_bid_p, 0)
                qty = min(available, self.remaining_ask_volume[product])

                if qty > 0:
                    self.place_ask(product, best_bid_p, qty)
                    self.bids[product][best_bid_p] -= qty
                    if self.bids[product][best_bid_p] <= 0:
                        self.bids[product].pop(best_bid_p, None)

        # ---- ENTRY + EXIT (buy side) ----
        # Hit the ask on every pebble. Bound by remaining_bid_volume only,
        # so we can run all the way to the long position limit.
        if buy_signal:
            for product in self.PEBBLES:
                best_ask_p = self.best_ask(product)
                if best_ask_p is None:
                    continue

                available = self.asks[product].get(best_ask_p, 0)
                qty = min(available, self.remaining_bid_volume[product])

                if qty > 0:
                    self.place_bid(product, best_ask_p, qty)
                    self.asks[product][best_ask_p] -= qty
                    if self.asks[product][best_ask_p] <= 0:
                        self.asks[product].pop(best_ask_p, None)

        # ---- Passive MM ----
        # Quote inside the inside book. Suppress bids when we're trying to short,
        # suppress asks when we're trying to long, so the MM layer doesn't fight
        # the entry layer.
        for product in self.PEBBLES:
            best_bid_p = self.best_bid(product)
            best_ask_p = self.best_ask(product)

            if best_bid_p is None or best_ask_p is None:
                continue

            bid_price = best_bid_p + self.PEBBLE_MM_IMPROVE
            ask_price = best_ask_p - self.PEBBLE_MM_IMPROVE

            if bid_price >= ask_price:
                continue

            bid_qty = 0 if sell_signal else self.remaining_bid_volume[product]
            ask_qty = 0 if buy_signal else self.remaining_ask_volume[product]

            if bid_qty > 0:
                self.place_bid(product, bid_price, bid_qty)

            if ask_qty > 0:
                self.place_ask(product, ask_price, ask_qty)

        return True

    def trade_product_to_desired(self, product, fair_value, desired_position, signal_active):
        bids = self.bids.get(product, {})
        asks = self.asks.get(product, {})

        if fair_value is None or not math.isfinite(fair_value) or fair_value <= 0:
            return

        desired_position_int = int(round(desired_position))

        take_margin = self.TAKE_MARGIN
        neutralise_margin = self.NEUTRALISE_MARGIN
        neutralise_hysteresis_qty = int(self.NEUTRALISE_HYSTERESIS_QTY)

        mm_margin = self.SIGNAL_MM_MARGIN if signal_active else self.MM_MARGIN

        # -------------------------------------------------------------- #
        # 1. TAKE PHASE
        #
        # No hysteresis here.
        #
        # These trades already require positive edge:
        #   buy only if ask < fair - TAKE_MARGIN
        #   sell only if bid > fair + TAKE_MARGIN
        #
        # Blocking these with hysteresis would reject genuinely good prices.
        # Humanity occasionally finds free money and then tries to refuse it.
        # We will not.
        # -------------------------------------------------------------- #

        levels_to_remove = []

        for price, volume in list(asks.items()):
            if (
                price < fair_value - take_margin
                and self.implied_position_sizes[product] < desired_position_int
            ):
                qty = min(
                    volume,
                    self.remaining_bid_volume[product],
                    max(0, desired_position_int - self.implied_position_sizes[product]),
                )

                if qty > 0:
                    self.place_bid(product, price, qty)
                    asks[price] -= qty

                    if asks[price] <= 0:
                        levels_to_remove.append(price)

        for price in levels_to_remove:
            asks.pop(price, None)

        levels_to_remove = []

        for price, volume in list(bids.items()):
            if (
                price > fair_value + take_margin
                and self.implied_position_sizes[product] > desired_position_int
            ):
                qty = min(
                    volume,
                    self.remaining_ask_volume[product],
                    max(0, self.implied_position_sizes[product] - desired_position_int),
                )

                if qty > 0:
                    self.place_ask(product, price, qty)
                    bids[price] -= qty

                    if bids[price] <= 0:
                        levels_to_remove.append(price)

        for price in levels_to_remove:
            bids.pop(price, None)

        # -------------------------------------------------------------- #
        # 2. NEUTRALISE PHASE WITH POSITION HYSTERESIS
        #
        # This is where spread-crossing churn usually comes from.
        #
        # Old behavior:
        #   buy if implied < desired
        #   sell if implied > desired
        #
        # New behavior:
        #   buy only if implied < desired - H
        #   sell only if implied > desired + H
        #
        # With H=1, the algo tolerates being one unit away from target and
        # lets the passive MM layer handle that final unit instead of paying
        # spread at zero edge.
        # -------------------------------------------------------------- #

        buy_neutralise_trigger_position = desired_position_int - neutralise_hysteresis_qty
        sell_neutralise_trigger_position = desired_position_int + neutralise_hysteresis_qty

        levels_to_remove = []

        for price, volume in list(asks.items()):
            if (
                price <= fair_value - neutralise_margin
                and self.implied_position_sizes[product] < buy_neutralise_trigger_position
            ):
                qty = min(
                    volume,
                    self.remaining_bid_volume[product],
                    max(0, desired_position_int - self.implied_position_sizes[product]),
                )

                if qty > 0:
                    self.place_bid(product, price, qty)
                    asks[price] -= qty

                    if asks[price] <= 0:
                        levels_to_remove.append(price)

        for price in levels_to_remove:
            asks.pop(price, None)

        levels_to_remove = []

        for price, volume in list(bids.items()):
            if (
                price >= fair_value + neutralise_margin
                and self.implied_position_sizes[product] > sell_neutralise_trigger_position
            ):
                qty = min(
                    volume,
                    self.remaining_ask_volume[product],
                    max(0, self.implied_position_sizes[product] - desired_position_int),
                )

                if qty > 0:
                    self.place_ask(product, price, qty)
                    bids[price] -= qty

                    if bids[price] <= 0:
                        levels_to_remove.append(price)

        for price in levels_to_remove:
            bids.pop(price, None)

        # -------------------------------------------------------------- #
        # 3. Clean consumed levels
        # -------------------------------------------------------------- #

        for price in list(bids.keys()):
            if bids[price] <= 0:
                bids.pop(price, None)

        for price in list(asks.keys()):
            if asks[price] <= 0:
                asks.pop(price, None)

        best_bid = max(bids.keys()) if bids else None
        best_ask = min(asks.keys()) if asks else None

        # -------------------------------------------------------------- #
        # 4. Passive market making
        #
        # No hysteresis here because we are not crossing the spread.
        # The MM layer is allowed to passively work small residual gaps left
        # by the neutralise deadband.
        # -------------------------------------------------------------- #

        bid_price = int(math.ceil(fair_value - 1)) - mm_margin
        ask_price = int(math.floor(fair_value + 1)) + mm_margin

        if best_bid is None:
            bid_price = int(round(fair_value - self.BOT_HALF_SPREAD_THRESHOLD))
        else:
            bid_price = min(bid_price, best_bid + 1)

        if best_ask is not None:
            bid_price = min(bid_price, best_ask - 1)

        if best_ask is None:
            ask_price = int(round(fair_value + self.BOT_HALF_SPREAD_THRESHOLD))
        else:
            ask_price = max(ask_price, best_ask - 1)

        if best_bid is not None:
            ask_price = max(ask_price, best_bid + 1)

        pos_upper = min(
            self.POS_SIZE_LIMITS[product],
            desired_position_int + self.MM_HALF_RANGE_CAP,
        )

        pos_lower = max(
            -self.POS_SIZE_LIMITS[product],
            desired_position_int - self.MM_HALF_RANGE_CAP,
        )

        bid_qty = max(
            0,
            min(
                pos_upper - self.implied_position_sizes[product],
                self.remaining_bid_volume[product],
            ),
        )

        ask_qty = max(
            0,
            min(
                self.implied_position_sizes[product] - pos_lower,
                self.remaining_ask_volume[product],
            ),
        )

        if best_bid is None:
            bid_qty = self.remaining_bid_volume[product]

        if best_ask is None:
            ask_qty = self.remaining_ask_volume[product]

        if bid_price > 0 and bid_qty > 0:
            self.place_bid(product, bid_price, bid_qty)

        if ask_price > 0 and ask_qty > 0:
            self.place_ask(product, ask_price, ask_qty)
        

    
    # ------------------------------------------------------------------ #
    # Combined strategy
    # ------------------------------------------------------------------ #

    def trade_combined(self):
        wall_mids = {}

        for product in self.PRODUCTS:
            mid = self.wall_mid(product)
            if mid is not None and mid > 0:
                wall_mids[product] = mid

        if not wall_mids:
            return

        discrete_flags = {}
        discrete_targets = {}

        for product in self.PRODUCTS:
            is_discrete, target = self.update_product_discrete_state(product, wall_mids.get(product, None))
            discrete_flags[product] = is_discrete
            discrete_targets[product] = target

        group_discrete_flags = {
            group_name: any(discrete_flags.get(p, False) for p in products)
            for group_name, products in self.GROUPS.items()
        }

        opens = self.trader_data["open"]

        for product, mid in wall_mids.items():
            if product not in opens:
                opens[product] = mid

        norms = {}

        for product, mid in wall_mids.items():
            open_price = float(opens.get(product, 0))
            if open_price > 0:
                norms[product] = math.log(mid / open_price)

        basket_norms = {}

        for group_name, products in self.GROUPS.items():
            vals = [norms[p] for p in products if p in norms]
            if len(vals) == len(products):
                basket_norms[group_name] = sum(vals) / len(vals)

        desired_positions = {p: 0 for p in self.PRODUCTS}
        active_product_signal_count = {p: 0 for p in self.PRODUCTS}
        pair_metrics = {}
        disabled_pairs = []

        for pair_name, spec in self.PAIRS.items():
            group_a = spec["group_a"]
            group_b = spec["group_b"]

            if self.group_is_discrete(group_a, group_discrete_flags) or self.group_is_discrete(group_b, group_discrete_flags):
                self.reset_pair_signal(pair_name)
                disabled_pairs.append(pair_name)

                pair_metrics[pair_name] = {
                    "mode": "disabled_group_discrete",
                    "group_a": group_a,
                    "group_b": group_b,
                    "group_a_discrete": group_discrete_flags.get(group_a, False),
                    "group_b_discrete": group_discrete_flags.get(group_b, False),
                }
                continue

            if group_a not in basket_norms or group_b not in basket_norms:
                self.reset_pair_signal(pair_name)
                pair_metrics[pair_name] = {"mode": "missing_basket"}
                continue

            basket_a = basket_norms[group_a]
            basket_b = basket_norms[group_b]

            if spec["spread_type"] == "difference":
                spread = basket_a - basket_b
            elif spec["spread_type"] == "sum":
                spread = basket_a + basket_b
            else:
                continue

            z, mean, std = self.pair_z_before_update(pair_name, spread)
            side, size, mode = self.update_pair_signal_state(pair_name, z)

            self.add_pair_desired_positions(desired_positions, spec, side, size)

            if side != 0:
                for p in self.GROUPS[group_a] + self.GROUPS[group_b]:
                    active_product_signal_count[p] += 1

            pair_metrics[pair_name] = {
                "mode": mode,
                "spread_type": spec["spread_type"],
                "group_a": group_a,
                "group_b": group_b,
                "spread": round(spread, 6),
                "mean": round(mean, 6),
                "std": round(std, 6),
                "z": None if z is None else round(z, 3),
                "side": side,
                "size": size,
                "hold": self.trader_data["signals"][pair_name].get("hold_ticks", 0),
            }

            self.update_pair_stats(pair_name, spread)

        discrete_group_products = set()

        for group_name, is_group_discrete in group_discrete_flags.items():
            if not is_group_discrete:
                continue

            for product in self.GROUPS[group_name]:
                discrete_group_products.add(product)
                desired_positions[product] = discrete_targets.get(product, 0)
                active_product_signal_count[product] += 1

        desired_positions = self.cap_desired_positions(desired_positions)

        pebble_signal_active = any(active_product_signal_count[p] > 0 for p in self.PEBBLES)
        pebble_group_discrete = group_discrete_flags.get("PEBBLES", False)

        used_pebble_sum_mm = False

        if not pebble_signal_active and not pebble_group_discrete:
            used_pebble_sum_mm = self.trade_pebbles_sum_mm()

        for product in self.PRODUCTS:
            if product not in wall_mids:
                continue

            if used_pebble_sum_mm and product in self.PEBBLES:
                continue

            # Hard switch: discrete group products do ONLY discrete reversion.
            if product in discrete_group_products:
                self.reach_target_aggressively(
                    product=product,
                    target_position=desired_positions.get(product, 0),
                )
                continue

            signal_active = active_product_signal_count[product] > 0

            self.trade_product_to_desired(
                product=product,
                fair_value=wall_mids[product],
                desired_position=desired_positions[product],
                signal_active=signal_active,
            )

        self.metrics_to_log = {
            "used_pebble_sum_mm": used_pebble_sum_mm,
            "disabled_pairs": disabled_pairs,
            "discrete_groups": {
                g: v for g, v in group_discrete_flags.items() if v
            },
            "discrete_products": [
                p for p, v in discrete_flags.items() if v
            ],
            "pairs": pair_metrics,
            "desired": desired_positions,
        }

    # ------------------------------------------------------------------ #
    # Run
    # ------------------------------------------------------------------ #

    def run(self, state: TradingState):
        self.timestamp = state.timestamp

        self.trader_data = self.load_trader_data(state.traderData)

        last_ts = self.trader_data.get("last_ts", None)

        if self.timestamp == 0 or (
            isinstance(last_ts, (int, float))
            and self.timestamp < last_ts
        ):
            self.trader_data = self.fresh_trader_data()

        self.trader_data["last_ts"] = self.timestamp

        self.result = {product: [] for product in self.PRODUCTS}
        self.conversions = 0
        self.metrics_to_log = {}

        try:
            self.get_pos_set_limits(state)
            self.get_bids_asks(state)
            self.trade_combined()
        except Exception as e:
            self.metrics_to_log = {"ERROR": repr(e)}

        trader_data_str = json.dumps(self.trader_data, separators=(",", ":"))

        try:
            logger.flush(state, self.result, self.conversions, trader_data_str)
        except Exception:
            pass

        return self.result, self.conversions, trader_data_str