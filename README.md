Our team, DU Trading, placed 1st in the UK, 4th in Europe, and 10th globally. Rounds 1 and 2 were "qualifying" for phase 2, where the leaderboard started from scratch after the intermission.

| Round | Global Rank | 
|-------|-------------|
| 1 | 5 |
| 2 | 3 |
| Intermission | - |
| 3 | 47 |
| 4 | 89 |
| 5 | 10 |



## Notes

Please refer to the [Frankfurt Hedgehogs writeup](https://github.com/TimoDiehm/imc-prosperity-3) from last year, we used their ideas and methods significantly in our approach to this year's competition. This write-up will build on concepts introduced there, so please do read that first if you have not already. 

## Team
 
- **[Fox Henderson](https://www.linkedin.com/in/foxhenderson/)**
- **[Ankith Rangan](https://www.linkedin.com/in/ankith-rangan/)**
- **[Fred Bicknell](https://www.linkedin.com/in/fredbicknell/)**
- **[Tim Wolstenholme](https://www.linkedin.com/in/tim-wolstenholme/)**
- **[Harry Donohoe](https://www.linkedin.com/in/harry-donohoe-46055232b/)**


## Round 1

Round 1 introduced two products, both of which were broadly recognisable evolutions of last year's stable assets:
- **ASH_COATED_OSMIUM**: a noisy, mean-reverting product.
- **INTARIAN_PEPPER_ROOT**: a stable-fair-value product, but with a slow linear drift.

### Ash Coated Osmium

Following the hint on the wiki, we reasoned that osmium was mean-reverting, which was confirmed by further statistical testing (ADF). Our first version of the strategy was very simple:

1. Take any cheap asks below $\text{wall-mid} - 1$ and any rich bids above $\text{wall-mid} + 1$.
2. Quote passively at $\lceil \text{wall-mid} - 1 \rceil$ on the bid and $\lfloor \text{wall-mid} + 1 \rfloor$ on the ask, undercutting the existing best-of-book by a tick where possible.
3. Skew that quote with $\verb|target-pos|$, so we drift back to flat (or crucially, some other desired position, see our pepper root strategy) whenever the price is extended. 

|  |
| --- |
| **Figure 1: Ash Coated Osmium Orderbook over Time** |
| <img width="1297" height="325" alt="osmium dashboard" src="https://github.com/user-attachments/assets/6a5ed8e7-50c2-44af-b8c3-230777e789c1" /> |
| Snippet of the dashboard for ASH_COATED_OSMIUM. Bids and asks are shown in blue and red; our own fills are marked in orange. |

However, our most meaningful edge this round came from a second observation.

#### Wide-fills

Looking at the order book on any visualiser, it was easy to see that many timestamps had no resting quotes on either one or both sides. When market-making at these timestamps, we could deliberately quote far wider than the bid-ask spread quoted at other timestamps (e.g. we could cause a bot to buy 100 above wall-mid for osmium) and still get filled. Presumably, some taker bots were programmed to trade at fixed timestamps, hitting our quotes as the only available liquidity. We found that these bots would only cross the spread up to a predefined limit from the fair price, and so we quoted at this limit.

|  |
| --- |
| **Figure 2: A Wide Fill on a Missing-Side Timestamp** |
| <img width="1466" height="383" alt="wide fill example" src="https://github.com/user-attachments/assets/1e0923ed-48db-4eee-89bf-e0ff81302484" /> |
|An example timestamp where one side of the order book is empty. Our quote, placed at the bot's tolerance limit, gets filled at far better than wall-mid. |

### Intarian Pepper Root

This was this year's version of the stable asset, with a slight addition. Instead of having a constant fair value, it increased linearly according to the formula

$$P_{\text{fair}} = 12{,}000 + 0.1 \cdot \left\lfloor{\frac{t}{100} + 0.5}\right\rfloor$$

where $P_{\text{fair}}$ is our fair value and $t$ is the current timestamp. Note that this is a verbose way of saying the fair value increased by $0.1$ per tick.

Using this fair value, it's straightforward to take any bids/asks that are cheap. We also held an intentional long bias, a desired position of $+76$ rather than $0$. Since the fair value drifts up monotonically, holding inventory is clearly beneficial, particularly over a 10,000-tick day. Empirically, the bot wide-fill threshold was $\pm 120$ for pepper root (vs. $\pm 100$ for osmium), so our quote band on root was correspondingly wider when the opposite side of the book was missing. Note that we are not buying and holding the max position like many teams did, as this would cause us to be unable to take advantage of wide-fills as well as prices that were better than wall-mid in the market.

Overall, this resulted in a 5th place finish in Round 1. 

## Round 2

In this round, the assets traded stayed the same with the option to bid for additional liquidity on all of the assets. Participants could submit bids of any integer amount, with the top 50% receiving access to a 25% increase in liquidity for the round. After a message from one of the Prosperity admins in the Discord, we concluded that the missing sides of the order book observed in Round 1 were likely a consequence of the data generation process. According to the explanation provided, bot quotes were first generated using the usual undisclosed method, after which 20% of orders were randomly removed. Given this, we reasoned that purchasing additional liquidity would effectively “repair” the order book at the points where sides were missing, thereby reducing opportunities to capture wide-fills. Since wide-fills represented our most profitable edge, we compared the expected gains from the added liquidity against the profits we would forgo. Based on these calculations, we ultimately decided not to bid for additional liquidity at all.

What we missed this round were predictable trades. Certain traders, as seen in the trades csv, executed at the same timestamp each day. This created an opportunity whereby, at those specific times, one could wipe both sides of the order book and then apply the wide-fills strategy as usual. Although wiping the book would incur an immediate cost from crossing the spread, the subsequent wide-fills would more than offset these losses, resulting in a positive expected return.

|  |
| --- |
| **Figure 3: Predictable Bot Trade Timestamps** |
| <img width="892" height="596" alt="predictable trades" src="https://github.com/user-attachments/assets/813f28ba-3105-45d9-9097-9bb96474f74c" /> |
| Distribution of bot trade timestamps across the three days of Round 2 data, showing the recurring pattern that we did not exploit. |

Overall, this resulted in us **ranking 3rd in the world** at the end of Round 2.


## Round 3

Round 3 introduced three new asset classes, and the assets from round 1/2 were removed. In this round, we had

- **HYDROGEL_PACK** — a mean-reverting asset.
- **VELVETFRUIT_EXTRACT** — the underlying for a set of European-style call options (also mean-reverting).
- **VEV_xxxx vouchers** — ten call options on velvetfruit at strikes 4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000 and 6500.

### Hydrogel Pack

The natural first hypothesis was that hydrogel would be related to velvetfruit, however after testing this exhaustively (correlation, lead/lag, volatility coupling) we got nothing back, so we settled on treating it as a pure mean-reversion product around its long-run mean of $9{,}990$, maxing our position limits to bet on a reversion whenever wall-mid drifted too far.


### Velvetfruit (European) Options

We split the option chain into two groups based on what the order books actually looked like:

| Group | Strikes | Behaviour |
|-------|---------|-----------|
| **Active** | 4000–5500 | Two-sided liquidity, real spreads, bot-driven flow |
| **Deep OTM** | 6000, 6500 | Bids stuck at $0$, asks stuck at $1$|

#### The deep-OTM 0/1 strategy

The 6000 and 6500 strikes never traded in any meaningful sense as the order book on every tick was just a $0$ bid and a $1$ ask. We quoted bid 0 in maximum size on every tick. By price-time priority our quotes sat ahead of (some of the) bot quotes, so we captured all flow, effectively picking up free money. Note that any inventory held at the end of the round was automatically liquidated at the asset's internal fair value, which in this case was fixed at 1 unit (in reality, it was likely a float that was bouncing around between 0 and 1, but prices are always integers). As a result, carrying inventory into expiry was not risky in any way. We again attempted to implement the wide-fills strategy, but profitability proved difficult because we were unable to predict when trades would occur. Although there were several occasions each round where we could effectively wipe the book “for free” by buying out all asks at a cost of 1 each, these purchased assets also had a true value of 1, meaning there was no loss or risk. However, the challenge was subsequently unwinding the resulting inventory position, as we could not reliably generate offsetting sells, meaning we had limited book wipes per round and no way to predict incoming trades.

This only made us $\sim 150$ per round, but I thought I would include it anyway to illustrate our thought process.

#### IV-smile fitting and BS pricing

Following the advice in the Discord and the advisor on the website, we tried to construct a volatility smile by fitting a parabola to the implied volatilities of the active strikes against moneyness, then pricing each voucher off the fitted IV via Black-Scholes. Two issues stopped us from being able to use it consistently:

1. The IV of the 5X00 options were mean-reverting
2. The spreads on all of these assets were obscene, meaning even if we could detect an IV mispricing, it was difficult to take advantage. 

|  |
| --- |
| **Figure 4: Velvetfruit Volatility Smile** |
| <img width="1120" height="548" alt="VEV volatility smile" src="https://github.com/user-attachments/assets/b222f177-0c24-4183-b01b-50464b256d2c" /> |
| Implied volatility plotted against moneyness for the eight active VEV strikes, with our parabolic fit overlaid. |

Rather than rely on the IV smile, we ran a fixed-threshold mean-reversion strategy on the underlying and the vouchers: when the underlying moved more than 8 ticks away from $5{,}250$, we faded it on both fruit and every active voucher simultaneously (i.e all in mean-reversion lol).

Perhaps unsurprisingly, due to our lack of progress in this round, we finished just 47th. 

## Round 4

No new assets were introduced this round. However, we were now able to identify the parties involved in every transaction. The market-trade rows in the data now exposed the buyer and seller as `Mark XX` strings: `Mark 14`, `Mark 22`, `Mark 38`, `Mark 49`, `Mark 55`, `Mark 67`.

We spent essentially the full Friday and Saturday classifying each Mark by behaviour:

| Trader | Role |
|--------|------|
| **Mark 01** | Deep, wide market-maker. Quotes at the bid/ask wall. |
| **Mark 14** | Tighter market-maker than 01. By PnL, the only consistently profitable maker. |
| **Mark 22** | Places "spike" orders at the wall-mid on multiple options simultaneously. Hybrid maker/taker. |
| **Mark 38** | Trades against Mark 14 on hydrogel. After exhaustive testing, this flow looked statistically random and was probably benign. |
| **Mark 49** | Spike-placer like Mark 22, but only on velvetfruit. |
| **Mark 55** | Adversely-selected market maker on velvetfruit. Wide-fill threshold of $\sim 55$. We could not predict his trades, only note their adverse selection. |
| **Mark 67** | The directional informed trader on velvetfruit. When he bought, the underlying tended to lift by ~2 ticks within 100 timestamps. |

Following from what we missed in the previous round, we implemented the following. 

#### 1. VEV_4000 intrinsic arbitrage

The 4000-strike voucher tracked $\text{fruit-mid} - 4000$ with empirical standard deviation $\approx 0.84$. We treated any deviation greater than 2 ticks as a take, sweeping the relevant side of the book in maximum size.

#### 2. Mark 67 directional bias

When Mark 67 appeared as a buyer in the market-trades stream for velvetfruit, we set a "signal active" flag with a TTL of 500 timestamps. While the flag was active we:

- Lifted the best ask on velvetfruit aggressively (we expected ~$+2$ tick mid moves over the next 100 timestamps).
- *Refused* to sell fruit on the mean-reversion leg, even if our reversion model was suggesting a sell. 


#### Exploiting Mark 22

Mark 22 often placed resting orders at, or below, the wall-mid. Visually, you could see these through the spikes in the best bid/ask going below the wall-mid. Since we believed wall-mid to be a sufficiently accurate reading of the internal fair value, we took any bids/asks in their entirety at these levels, for a small expected profit each time. 

|  |
| --- |
| **Figure 5: Mark 22 Spike Orders below Wall-Mid** |
| <img width="1439" height="443" alt="mark 22 spikes" src="https://github.com/user-attachments/assets/1ca15c85-4bc1-49d8-91c6-977b2c34de3c" /> |
| Best bid and best ask deviating below wall-mid on multiple vouchers simultaneously, corresponding to Mark 22's resting orders. |

## Round 5

Round 5 introduced ten new product groups, each containing five variants:

- `GALAXY_SOUND_RECORDERS_*`, `VERTICAL_SLEEPING_PODS_*`, `DOMESTIC_ROBOTS_*`, `CONSTRUCTION_PANELS_*`, `SNACKPACK_*`, `PEBBLES_*`, `INSTANT_TRANSLATORS_*`, `OXYGEN_SHAKE_*`, `MICROCHIP_*`, `UV_VISOR_*`.


### Discretisation

Several of the products, most clearly those from the OXYGEN_SHAKE_ and DOMESTIC_ROBOTS_ groups, moved on a discrete grid: their prices jumped between fixed levels (multiples of 100) rather than drifting continuously at seemingly random points, for random durations. After every discrete jump there was a high probability that the price would *snap back* to the previous level within a small number of ticks. We believe the internal price was still a random walk, but some rounding function was applied. This means often the price would bounce around from 49 -> 50 and back again internally, resulting in frequent jumps of 100 in the actual price. 

We could exploit this due to the asymmetric payoff:

- If it snapped back: we made $\sim1,000$.
- If it didn't: we lost $\sim160$.

|  |
| --- |
| **Figure 6: Discrete Jumps** |
| <img width="1301" height="378" alt="discrete jump" src="https://github.com/user-attachments/assets/440f8ba8-71b0-4543-be9b-4a3b5164976b" /> |
| Discrete price pattern, with the snap-back to the prior level occurring within a small number of ticks. |

Crucially, we implemented this strategy to come into effect for any products, not just the ones that exhibited this in the sample data. Around 660,000 of our final-round PnL came from this strategy alone.

### Pebbles

It was quite clear that the pebbles had a fixed sum of 50,000. This meant that on any given timestamp, we could find the sum and trade any deviations from the fair value we calculated. In practice, we implemented this as a basket mean-reversion strategy. If the sum of best bids across the pebble products exceeded a threshold ($\sim 49,990$), we interpreted the basket as overpriced and sold all five products simultaneously at the bid. Conversely, if the sum of asks dropped below $\sim 50,010$, we aggressively bought the entire basket at the ask. This allowed us to enter both long and short basket positions depending on the direction of the deviation.

|  |
| --- |
| **Figure 7: Pebble Basket Sum over Time** |
| <img width="1496" height="400" alt="pebble basket sum" src="https://github.com/user-attachments/assets/a24d8023-8006-44c0-920f-8887efe75ce4" /> |
| Sum of best bids and asks across all five PEBBLES products, oscillating tightly around 50,000. |

### Snack Packs
The five snack pack flavours, chocolate, vanilla, pistachio, strawberry and raspberry, turned out to contain two separable mean-reverting structures within the group itself. The first relationship was between chocolate and vanilla. Their wall-mids were almost perfectly mirrored around 10,000. We treated this as pure spread reversion.

|  |
| --- |
| **Figure 8: Chocolate and Vanilla Snack Packs Mirrored Around 10,000** |
| <img width="1204" height="381" alt="choc vs vanilla" src="https://github.com/user-attachments/assets/71b51ce9-0ac0-49fd-9a6b-bc752786264c" /> |
| Wall-mids of SNACKPACK_CHOCOLATE and SNACKPACK_VANILLA plotted on the same axes, showing the near-perfect mirroring around 10,000. |

The second relationship was a three-way one between pistachio, strawberry and raspberry. Strawberry and raspberry were mirrored around 10,000 in the same way as chocolate and vanilla, but with a slow upward drift in both products on top. Pistachio's returns were a clean linear function of strawberry's, with a regression coefficient of approx 0.6. Rather than trying to disentangle these into individual fair values, we just treated the normalised combination as a synthetic basket and ran mean reversion on its deviations from zero. Together, the two snack pack legs earned us roughly 20,000 per round.

## Conclusion

Huge thanks to IMC for running the competition, we're looking forward to competing again next year. 

Thanks to Claude, Gemini, and ChatGPT lol. LLMs allowed us to rapidly test ideas and perform large-scale analysis. However, we found they still lack some trading intuition.
