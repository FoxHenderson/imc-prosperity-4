import json
from datamodel import *
from typing import List,Any
import numpy as np

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
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

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
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
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

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
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
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

    # def bid(self):
    #     return 0

    def __init__(self):
        pass

    def get_pos_set_limits(self, trading_state: TradingState):
        self.POS_SIZE_LIMITS = {
            "ASH_COATED_OSMIUM": 80,
            "INTARIAN_PEPPER_ROOT": 80,
        }
        position_sizes = {product: trading_state.position.get(product, 0) for product in self.POS_SIZE_LIMITS}
        self.initial_position_sizes = position_sizes.copy()
        self.implied_position_sizes = position_sizes.copy()

        self.remaining_bid_volume = {product: self.POS_SIZE_LIMITS[product] - position_sizes[product] for product in
                                     self.POS_SIZE_LIMITS}
        self.remaining_ask_volume = {product: self.POS_SIZE_LIMITS[product] + position_sizes[product] for product in
                                     self.POS_SIZE_LIMITS}

    def get_bids_asks(self, trading_state: TradingState):
        bids = {}
        asks = {}
        for product in trading_state.order_depths:
            try:
                bids[product] = {price: abs(volume) for price, volume in
                                 sorted(trading_state.order_depths[product].buy_orders.items(), key=lambda x: x[0],
                                        reverse=True)}
            except:
                bids[product] = {}
            try:
                asks[product] = {price: abs(volume) for price, volume in
                                 sorted(trading_state.order_depths[product].sell_orders.items(), key=lambda x: x[0])}
            except:
                asks[product] = {}
        self.bids = bids
        self.asks = asks
        return bids, asks

    def place_bid(self, product, price, volume):
        volume = abs(max(0, volume))
        volume = int(min(volume, self.remaining_bid_volume[product]))
        price = int(price)
        order = Order(product, price, volume)
        self.result[product].append(order)
        self.remaining_bid_volume[product] -= volume
        self.implied_position_sizes[product] += volume
        return order

    def place_ask(self, product, price, volume):
        volume = abs(max(0, volume))
        volume = int(min(volume, self.remaining_ask_volume[product]))
        price = int(price)
        order = Order(product, price, -volume)
        self.result[product].append(order)
        self.remaining_ask_volume[product] -= volume
        self.implied_position_sizes[product] -= volume
        return order

    def bid(self):
        return 0

    ###############################################
    ################# OSMIUM ####################
    ###############################################

    def trade_osmium(self):
        try:
            osmium_bids_implied = self.bids["ASH_COATED_OSMIUM"]
        except:
            osmium_bids_implied = {}
        try:
            osmium_asks_implied = self.asks["ASH_COATED_OSMIUM"]
        except:
            osmium_asks_implied = {}

        ## Remove levels with 0 size, just in case
        levels_to_remove = []
        for price, size in osmium_bids_implied.items():
            if size == 0:
                levels_to_remove.append(price)
        for price in levels_to_remove:
            del osmium_bids_implied[price]
        levels_to_remove = []
        for price, size in osmium_asks_implied.items():
            if size == 0:
                levels_to_remove.append(price)
        for price in levels_to_remove:
            del osmium_asks_implied[price]

        ## Do the mid_wall_ff2 calculation
        bid_prices_current = sorted(osmium_bids_implied.keys(), reverse=True)
        ask_prices_current = sorted(osmium_asks_implied.keys())

        prev_bp1 = self.trader_data.get("last_osmium_bid_price_1", None)
        prev_bp2 = self.trader_data.get("last_osmium_bid_price_2", None)
        prev_ap1 = self.trader_data.get("last_osmium_ask_price_1", None)
        prev_ap2 = self.trader_data.get("last_osmium_ask_price_2", None)

        bp1_ff = bid_prices_current[0] if len(bid_prices_current) > 0 else prev_bp1
        bp2_ff = bid_prices_current[1] if len(bid_prices_current) > 1 else prev_bp2
        bp3_ff = bid_prices_current[2] if len(bid_prices_current) > 2 else None
        ap1_ff = ask_prices_current[0] if len(ask_prices_current) > 0 else prev_ap1
        ap2_ff = ask_prices_current[1] if len(ask_prices_current) > 1 else prev_ap2
        ap3_ff = ask_prices_current[2] if len(ask_prices_current) > 2 else None

        bid_price_candidates = [p for p in [bp1_ff, bp2_ff, bp3_ff] if p is not None]
        ask_price_candidates = [p for p in [ap1_ff, ap2_ff, ap3_ff] if p is not None]

        bid_wall_ff2 = min(bid_price_candidates) if len(bid_price_candidates) > 0 else None
        ask_wall_ff2 = max(ask_price_candidates) if len(ask_price_candidates) > 0 else None

        ## Save the levels in trader data
        self.trader_data["last_osmium_bid_price_1"] = bp1_ff
        self.trader_data["last_osmium_bid_price_2"] = bp2_ff
        self.trader_data["last_osmium_ask_price_1"] = ap1_ff
        self.trader_data["last_osmium_ask_price_2"] = ap2_ff

        ## Fall back on these if no information, unlikely
        if bid_wall_ff2 is None:
            bid_wall_ff2 = 9900
        if ask_wall_ff2 is None:
            ask_wall_ff2 = 10100

        wall_mid = (bid_wall_ff2 + ask_wall_ff2) / 2

        self.metrics_to_log["osmium_bid_wall"] = bid_wall_ff2
        self.metrics_to_log["osmium_ask_wall"] = ask_wall_ff2
        self.metrics_to_log["osmium_wall_mid"] = wall_mid

        ## TAKING ##
        ## Take any liquidity crossing wall mid calculated above (+-1)
        z_score = (wall_mid - 10_000)/ 5
        desired_position = -np.sign(z_score)*80*np.power(abs(z_score),1/2)
        if abs(desired_position) > 80:
            desired_position = np.sign(desired_position)*80
        ## BUYING
        levels_to_remove = []
        for price, volume in osmium_asks_implied.items():
            if price < wall_mid - self.OSMIUM_WALL_MID_MARGIN and self.implied_position_sizes["ASH_COATED_OSMIUM"] < desired_position:
                quantity = min(volume, self.remaining_bid_volume["ASH_COATED_OSMIUM"])
                self.place_bid("ASH_COATED_OSMIUM", price, quantity)
                osmium_asks_implied[price] -= quantity  ## If this is 0, can remove this level
                if volume == quantity:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del osmium_asks_implied[price]

        ## SELLING
        levels_to_remove = []
        for price, volume in osmium_bids_implied.items():
            if price > wall_mid + self.OSMIUM_WALL_MID_MARGIN and self.implied_position_sizes["ASH_COATED_OSMIUM"] > desired_position:
                quantity = min(volume, self.remaining_ask_volume["ASH_COATED_OSMIUM"])
                self.place_ask("ASH_COATED_OSMIUM", price, quantity)
                osmium_bids_implied[price] -= quantity  ## If this is 0, can remove this level
                if volume == quantity:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del osmium_bids_implied[price]

        ## POSITION NEUTRALISATION ##
        levels_to_remove = []

        for price, volume in osmium_asks_implied.items():
            if price <= wall_mid and self.implied_position_sizes["ASH_COATED_OSMIUM"] < desired_position:
                quantity = min(volume, -self.implied_position_sizes["ASH_COATED_OSMIUM"])
                self.place_bid("ASH_COATED_OSMIUM", price, quantity)
                osmium_asks_implied[price] -= quantity  ## If this is 0, can remove this level
                if quantity == volume:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del osmium_asks_implied[price]

        levels_to_remove = []
        for price, volume in osmium_bids_implied.items():
            if price >= wall_mid and self.implied_position_sizes["ASH_COATED_OSMIUM"] > desired_position:
                quantity = min(volume, self.implied_position_sizes["ASH_COATED_OSMIUM"])
                self.place_ask("ASH_COATED_OSMIUM", price, quantity)
                osmium_bids_implied[price] -= quantity  ## If this is 0, can remove this level
                if quantity == volume:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del osmium_bids_implied[price]

        ## Remove any levels with 0 volume
        levels_to_remove = []
        for price, size in osmium_bids_implied.items():
            if size == 0:
                levels_to_remove.append(price)
        for price in levels_to_remove:
            del osmium_bids_implied[price]
        levels_to_remove = []
        for price, size in osmium_asks_implied.items():
            if size == 0:
                levels_to_remove.append(price)
        for price in levels_to_remove:
            del osmium_asks_implied[price]

        ## MARKET MAKING ##
        ## Note: If there are no bids or no asks, make sure to quote WIDE

        ## Start either side of wall mid
        ## Should we really +- 1 ???
        bid_price = int(np.ceil(wall_mid - 1)) - self.OSMIUM_WALL_MID_MARGIN
        ask_price = int(np.floor(wall_mid + 1)) + self.OSMIUM_WALL_MID_MARGIN

        best_bid = max(osmium_bids_implied.keys()) if len(osmium_bids_implied) > 0 else None
        best_ask = min(osmium_asks_implied.keys()) if len(osmium_asks_implied) > 0 else None

        if best_bid is None:
            bid_price = wall_mid - self.OSMIUM_BOT_HALF_SPREAD_THRESHOLD  ## Wide if no bids
        else:
            bid_price = min(bid_price, best_bid + 1) if best_bid is not None else bid_price  ## Like normal

        if best_ask is None:
            ask_price = wall_mid + self.OSMIUM_BOT_HALF_SPREAD_THRESHOLD  ## Wide if no asks
        else:
            ask_price = max(ask_price, best_ask - 1) if best_ask is not None else ask_price  ## Like normal

        bid_quantity = self.remaining_bid_volume["ASH_COATED_OSMIUM"]
        ask_quantity = self.remaining_ask_volume["ASH_COATED_OSMIUM"]

        self.place_bid("ASH_COATED_OSMIUM", bid_price, bid_quantity)
        self.place_ask("ASH_COATED_OSMIUM", ask_price, ask_quantity)

    #############################################################
    ###################### PEPPER ROOT #############################
    #############################################################

    def trade_pepper_root(self):
        try:
            pepper_root_bids = self.bids["INTARIAN_PEPPER_ROOT"]
        except KeyError:
            pepper_root_bids = {}
        try:
            pepper_root_asks = self.asks["INTARIAN_PEPPER_ROOT"]
        except KeyError:
            pepper_root_asks = {}

        ## Logic to handle fair value calculation
        ## Detect an initial fair value and track it
        wall_mid = (min(pepper_root_bids) + max(
            pepper_root_asks)) / 2 if pepper_root_bids and pepper_root_asks else None

        try:
            pepper_root_initial_value = self.trader_data["pepper_root_initial_value"]
            pepper_root_initial_timestamp = self.trader_data["pepper_root_initial_timestamp"]
            self.trader_data["pepper_root_initial_value"] = pepper_root_initial_value
            self.trader_data["pepper_root_initial_timestamp"] = pepper_root_initial_timestamp
            fair_value = round(pepper_root_initial_value,-2) + 0.1 * (
                        int(self.timestamp / 100) - int(pepper_root_initial_timestamp / 100))
            self.metrics_to_log["pepper_root_fair_value"] = fair_value

        except KeyError:
            if wall_mid:
                base_fv = np.round(wall_mid, -2)  ## Could change to 100, especially if using lots of key errors
                fv = base_fv + 0.1 * (int(self.timestamp / 100))
                self.trader_data["pepper_root_initial_value"] = fv
                self.trader_data["pepper_root_initial_timestamp"] = self.timestamp
                fair_value = fv

                logger.print(f"Bids: {pepper_root_bids}")
                logger.print(f"Asks: {pepper_root_asks}")
                logger.print(f"Wall mid: {wall_mid}")
                logger.print(f"Base fair value: {base_fv}")
                logger.print(f"Timestamp: {self.timestamp}")
                logger.print(f"Initial fair value: {fair_value}")
                self.metrics_to_log["pepper_root_fair_value"] = fair_value
            else:
                fair_value = 14000 + 0.1 * (
                    int(self.timestamp / 100))   ## Best guess, update as soon as we have wall mid. TODO Update to 14,000 for real submission


        self.metrics_to_log["pepper_root_wall_mid"] = wall_mid

        POS_UPPER = self.PEPPER_ROOT_DESIRED_POSITION + self.PEPPER_ROOT_MAKE_TAKE__HALF_RANGE_CAP_UPPER
        POS_LOWER = self.PEPPER_ROOT_DESIRED_POSITION - self.PEPPER_ROOT_MAKE_TAKE_HALF_RANGE_CAP_LOWER
        ## TAKING ##
        levels_to_remove = []
        ## BUYING
        for price, volume in pepper_root_asks.items():
            if price < fair_value:
                quantity = max(0, min(
                    volume,
                    POS_UPPER - self.implied_position_sizes["INTARIAN_PEPPER_ROOT"],
                    self.remaining_bid_volume["INTARIAN_PEPPER_ROOT"]
                ))
                self.place_bid("INTARIAN_PEPPER_ROOT", price, quantity)
                if volume == quantity:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del pepper_root_asks[price]
        levels_to_remove = []

        ## SELLING
        for price, volume in pepper_root_bids.items():
            if price > fair_value +1:
                quantity = max(0, min(
                    volume,
                    self.implied_position_sizes["INTARIAN_PEPPER_ROOT"] - POS_LOWER,
                    self.remaining_ask_volume["INTARIAN_PEPPER_ROOT"]
                ))
                self.place_ask("INTARIAN_PEPPER_ROOT", price, quantity)
                if volume == quantity:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del pepper_root_bids[price]

        ## NEUTRALISATION
        levels_to_remove = []

        ## BUYING
        for price, volume in pepper_root_asks.items():
            if price <= fair_value and self.implied_position_sizes[
                "INTARIAN_PEPPER_ROOT"] < self.PEPPER_ROOT_DESIRED_POSITION:
                quantity = min(volume,
                               self.PEPPER_ROOT_DESIRED_POSITION - self.implied_position_sizes["INTARIAN_PEPPER_ROOT"])
                self.place_bid("INTARIAN_PEPPER_ROOT", price, quantity)
                if volume == quantity:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del pepper_root_asks[price]
        levels_to_remove = []

        ## SELLING
        for price, volume in pepper_root_bids.items():
            if price >= fair_value and self.implied_position_sizes[
                "INTARIAN_PEPPER_ROOT"] > self.PEPPER_ROOT_DESIRED_POSITION:
                quantity = min(volume,
                               self.implied_position_sizes["INTARIAN_PEPPER_ROOT"] - self.PEPPER_ROOT_DESIRED_POSITION)
                self.place_ask("INTARIAN_PEPPER_ROOT", price, quantity)
                if volume == quantity:
                    levels_to_remove.append(price)

        for price in levels_to_remove:
            del pepper_root_bids[price]

        ## ACCUMULATAION
        levels_to_remove = []
        if self.timestamp < 1000:
            for price, volume in pepper_root_asks.items():
                if self.implied_position_sizes["INTARIAN_PEPPER_ROOT"] < self.PEPPER_ROOT_DESIRED_POSITION:
                    quantity = min(volume, self.PEPPER_ROOT_DESIRED_POSITION - self.implied_position_sizes[
                        "INTARIAN_PEPPER_ROOT"])
                    self.place_bid("INTARIAN_PEPPER_ROOT", price, quantity)
                    if volume == quantity:
                        levels_to_remove.append(price)

        for price in levels_to_remove:
            del pepper_root_asks[price]

        ## Remove any levels with 0 volume
        levels_to_remove = []
        for price, size in pepper_root_bids.items():
            if size == 0:
                levels_to_remove.append(price)
        for price in levels_to_remove:
            del pepper_root_bids[price]
        levels_to_remove = []
        for price, size in pepper_root_asks.items():
            if size == 0:
                levels_to_remove.append(price)
        for price in levels_to_remove:
            del pepper_root_asks[price]

        ## MARKET MAKING
        bid_price = int(np.ceil(fair_value - 1))
        ask_price = int(np.floor(fair_value + 1))

        best_bid = max(pepper_root_bids.keys()) if len(pepper_root_bids) > 0 else None
        best_ask = min(pepper_root_asks.keys()) if len(pepper_root_asks) > 0 else None

        if best_bid is None:
            bid_price = fair_value - self.PEPPER_ROOT_BOT_HALF_SPREAD_THRESHOLD
            bid_quantity = self.remaining_bid_volume["INTARIAN_PEPPER_ROOT"]  ## ! DO NOT CAP FOR WIDE FILLS
        else:
            bid_price = min(bid_price, best_bid + 1) if best_bid is not None else bid_price
            bid_quantity = max(0, min(
                POS_UPPER - self.implied_position_sizes["INTARIAN_PEPPER_ROOT"],
                self.remaining_bid_volume["INTARIAN_PEPPER_ROOT"]
            ))

        if best_ask is None:
            ask_price = fair_value + self.PEPPER_ROOT_BOT_HALF_SPREAD_THRESHOLD
            ask_quantity = self.remaining_ask_volume["INTARIAN_PEPPER_ROOT"]  ## ! DO NOT CAP FOR WIDE FILLS
        else:
            ask_price = max(ask_price, best_ask - 1) if best_ask is not None else ask_price
            ask_quantity = max(0, min(
                self.implied_position_sizes["INTARIAN_PEPPER_ROOT"] - POS_LOWER,
                self.remaining_ask_volume["INTARIAN_PEPPER_ROOT"]
            ))

        self.place_bid("INTARIAN_PEPPER_ROOT", bid_price, bid_quantity)
        self.place_ask("INTARIAN_PEPPER_ROOT", ask_price, ask_quantity)

        ## If wall_mid deviates too much, assume regime change and use wall_mid instead TODO
        ## TODO if this happens then it could be wise to not bias long too

    ###############################################################
    ############################ RUN ##############################
    ###############################################################

    def run(self, state: TradingState):
        self.timestamp = state.timestamp
        PRODUCTS_ALGORITHMS = {
            "ASH_COATED_OSMIUM": self.trade_osmium,
           "INTARIAN_PEPPER_ROOT": self.trade_pepper_root
        }

        ## Spread for when no orders, at 97 rather than 100 in case fair_price is off
        self.OSMIUM_BOT_HALF_SPREAD_THRESHOLD = 98
        self.OSMIUM_WALL_MID_MARGIN = 1

        self.PEPPER_ROOT_BOT_HALF_SPREAD_THRESHOLD = 120
        self.PEPPER_ROOT_MAKE_TAKE__HALF_RANGE_CAP_UPPER = 4
        self.PEPPER_ROOT_MAKE_TAKE_HALF_RANGE_CAP_LOWER = 4
        self.PEPPER_ROOT_DESIRED_POSITION = 80 - self.PEPPER_ROOT_MAKE_TAKE__HALF_RANGE_CAP_UPPER

        self.trader_data = {}
        self.metrics_to_log = {}

        if state.traderData:
            self.trader_data = json.loads(state.traderData)

        self.result = {product: [] for product, _ in PRODUCTS_ALGORITHMS.items()}
        self.conversions = 0

        self.get_pos_set_limits(state)
        self.get_bids_asks(state)
        if state.timestamp == 0:
            logger.print(f"Market making at best bid/ask +- 1, position neutralisation at wall mid, taking")

        for product, algorithm in PRODUCTS_ALGORITHMS.items():
            algorithm()

        logger.print(f"METRICS: {json.dumps(self.metrics_to_log)}")
        logger.flush(state,self.result,0,"")
        return self.result, self.conversions, json.dumps(self.trader_data)

