from __future__ import annotations
import msgspec
from enum import Enum
import datetime
import uuid
from typing import final, Any, Literal, TypeAlias
from collections.abc import Mapping, Sequence

DepthQuery: TypeAlias = int

FixedPointCount: TypeAlias = str

FixedPointDollars: TypeAlias = str

OrderbookLevel: TypeAlias = Sequence[float]

PriceLevel: TypeAlias = Sequence[int]

PriceLevelDollars: TypeAlias = Sequence[Any]

PriceLevelDollarsCountFp: TypeAlias = Sequence[str]


@final
class AcceptQuoteRequest(msgspec.Struct, frozen=True):
    accepted_side: Literal["yes", "no"]


@final
class AmendOrderRequest(msgspec.Struct, frozen=True):
    action: Literal["buy", "sell"]
    client_order_id: str
    side: Literal["yes", "no"]
    ticker: str
    updated_client_order_id: str
    count: int | None = None
    count_fp: FixedPointCount | None = None
    no_price: int | None = None
    no_price_dollars: FixedPointDollars | None = None
    yes_price: int | None = None
    yes_price_dollars: FixedPointDollars | None = None


@final
class AmendOrderResponse(msgspec.Struct, frozen=True):
    old_order: Order
    order: Order


@final
class Announcement(msgspec.Struct, frozen=True):
    delivery_time: datetime.datetime
    message: str
    status: Literal["active", "inactive"]
    type: Literal["info", "warning", "error"]


@final
class ApiKey(msgspec.Struct, frozen=True):
    api_key_id: str
    name: str
    scopes: Sequence[str]


@final
class ApplySubaccountTransferRequest(msgspec.Struct, frozen=True):
    amount_cents: int
    client_transfer_id: uuid.UUID
    from_subaccount: int
    to_subaccount: int


@final
class ApplySubaccountTransferResponse(msgspec.Struct, frozen=True):
    """Empty response indicating successful transfer."""


@final
class AssociatedEvent(msgspec.Struct, frozen=True):
    active_quoters: Sequence[str]
    is_yes_only: bool
    ticker: str
    size_max: int | None = None
    size_min: int | None = None


@final
class BatchCancelOrdersIndividualResponse(msgspec.Struct, frozen=True):
    order_id: str
    reduced_by: int
    reduced_by_fp: FixedPointCount
    error: ErrorResponse | None = None
    order: Order | None = None


@final
class BatchCancelOrdersRequest(msgspec.Struct, frozen=True):
    ids: Sequence[str]


@final
class BatchCancelOrdersResponse(msgspec.Struct, frozen=True):
    orders: Sequence[BatchCancelOrdersIndividualResponse]


@final
class BatchCreateOrdersIndividualResponse(msgspec.Struct, frozen=True):
    client_order_id: str | None = None
    error: ErrorResponse | None = None
    order: Order | None = None


@final
class BatchCreateOrdersRequest(msgspec.Struct, frozen=True):
    orders: Sequence[CreateOrderRequest]


@final
class BatchCreateOrdersResponse(msgspec.Struct, frozen=True):
    orders: Sequence[BatchCreateOrdersIndividualResponse]


@final
class BatchGetMarketCandlesticksResponse(msgspec.Struct, frozen=True):
    markets: Sequence[MarketCandlesticksResponse]


@final
class BidAskDistribution(msgspec.Struct, frozen=True):
    close: int
    close_dollars: FixedPointDollars
    high: int
    high_dollars: FixedPointDollars
    low: int
    low_dollars: FixedPointDollars
    open: int
    open_dollars: FixedPointDollars


@final
class CancelOrderResponse(msgspec.Struct, frozen=True):
    order: Order
    reduced_by: int
    reduced_by_fp: FixedPointCount


@final
class CreateApiKeyRequest(msgspec.Struct, frozen=True):
    name: str
    public_key: str
    scopes: Sequence[str] | None = None


@final
class CreateApiKeyResponse(msgspec.Struct, frozen=True):
    api_key_id: str


@final
class CreateMarketInMultivariateEventCollectionRequest(msgspec.Struct, frozen=True):
    selected_markets: Sequence[TickerPair]
    with_market_payload: bool | None = None


@final
class CreateMarketInMultivariateEventCollectionResponse(msgspec.Struct, frozen=True):
    event_ticker: str
    market_ticker: str
    market: Market | None = None


@final
class CreateOrderGroupRequest(msgspec.Struct, frozen=True):
    contracts_limit: int | None = None
    contracts_limit_fp: FixedPointCount | None = None


@final
class CreateOrderGroupResponse(msgspec.Struct, frozen=True):
    order_group_id: str


@final
class CreateOrderRequest(msgspec.Struct, frozen=True):
    action: Literal["buy", "sell"]
    side: Literal["yes", "no"]
    ticker: str
    buy_max_cost: int | None = None
    cancel_order_on_pause: bool | None = None
    client_order_id: str | None = None
    count: int | None = None
    count_fp: FixedPointCount | None = None
    expiration_ts: int | None = None
    no_price: int | None = None
    no_price_dollars: FixedPointDollars | None = None
    order_group_id: str | None = None
    post_only: bool | None = None
    reduce_only: bool | None = None
    self_trade_prevention_type: SelfTradePreventionType | None = None
    sell_position_floor: int | None = None
    subaccount: int | None = None
    time_in_force: (
        Literal["fill_or_kill", "good_till_canceled", "immediate_or_cancel"] | None
    ) = None
    type: Literal["limit", "market"] | None = None
    yes_price: int | None = None
    yes_price_dollars: FixedPointDollars | None = None


@final
class CreateOrderResponse(msgspec.Struct, frozen=True):
    order: Order


@final
class CreateQuoteRequest(msgspec.Struct, frozen=True):
    no_bid: FixedPointDollars
    rest_remainder: bool
    rfq_id: str
    yes_bid: FixedPointDollars


@final
class CreateQuoteResponse(msgspec.Struct, frozen=True):
    id: str


@final
class CreateRfqRequest(msgspec.Struct, frozen=True):
    market_ticker: str
    rest_remainder: bool
    contracts: int | None = None
    contracts_fp: FixedPointCount | None = None
    replace_existing: bool | None = None
    subtrader_id: str | None = None
    target_cost_centi_cents: int | None = None


@final
class CreateRfqResponse(msgspec.Struct, frozen=True):
    id: str


@final
class CreateSubaccountResponse(msgspec.Struct, frozen=True):
    subaccount_number: int


@final
class DailySchedule(msgspec.Struct, frozen=True):
    close_time: str
    open_time: str


@final
class DecreaseOrderRequest(msgspec.Struct, frozen=True):
    reduce_by: int | None = None
    reduce_by_fp: FixedPointCount | None = None
    reduce_to: int | None = None
    reduce_to_fp: FixedPointCount | None = None


@final
class DecreaseOrderResponse(msgspec.Struct, frozen=True):
    order: Order


@final
class EmptyResponse(msgspec.Struct, frozen=True):
    """An empty response body"""


@final
class ErrorResponse(msgspec.Struct, frozen=True):
    code: str | None = None
    details: str | None = None
    message: str | None = None
    service: str | None = None


@final
class EventData(msgspec.Struct, frozen=True):
    available_on_brokers: bool
    category: str
    collateral_return_type: str
    event_ticker: str
    mutually_exclusive: bool
    product_metadata: Mapping[str, Any]
    series_ticker: str
    sub_title: str
    title: str
    markets: Sequence[Market] | None = None
    strike_date: datetime.datetime | None = None
    strike_period: str | None = None


@final
class EventPosition(msgspec.Struct, frozen=True):
    event_exposure: int
    event_exposure_dollars: FixedPointDollars
    event_ticker: str
    fees_paid: int
    fees_paid_dollars: FixedPointDollars
    realized_pnl: int
    realized_pnl_dollars: FixedPointDollars
    total_cost: int
    total_cost_dollars: FixedPointDollars
    total_cost_shares: int
    total_cost_shares_fp: FixedPointCount


class ExchangeInstance(str, Enum):
    EVENT_CONTRACT = "event_contract"
    MARGINED = "margined"


@final
class ExchangeStatus(msgspec.Struct, frozen=True):
    exchange_active: bool
    trading_active: bool
    exchange_estimated_resume_time: datetime.datetime | None = None


@final
class Fill(msgspec.Struct, frozen=True):
    action: Literal["buy", "sell"]
    count: int
    count_fp: FixedPointCount
    fill_id: str
    is_taker: bool
    market_ticker: str
    no_price: int
    no_price_fixed: str
    order_id: str
    price: float
    side: Literal["yes", "no"]
    ticker: str
    trade_id: str
    yes_price: int
    yes_price_fixed: str
    client_order_id: str | None = None
    created_time: datetime.datetime | None = None
    ts: int | None = None


@final
class ForecastPercentilesPoint(msgspec.Struct, frozen=True):
    end_period_ts: int
    event_ticker: str
    percentile_points: Sequence[PercentilePoint]
    period_interval: int


@final
class GenerateApiKeyRequest(msgspec.Struct, frozen=True):
    name: str
    scopes: Sequence[str] | None = None


@final
class GenerateApiKeyResponse(msgspec.Struct, frozen=True):
    api_key_id: str
    private_key: str


@final
class GetApiKeysResponse(msgspec.Struct, frozen=True):
    api_keys: Sequence[ApiKey]


@final
class GetBalanceResponse(msgspec.Struct, frozen=True):
    balance: int
    portfolio_value: int
    updated_ts: int


@final
class GetCommunicationsIdResponse(msgspec.Struct, frozen=True):
    communications_id: str


@final
class GetEventCandlesticksResponse(msgspec.Struct, frozen=True):
    adjusted_end_ts: int
    market_candlesticks: Sequence[Sequence[MarketCandlestick]]
    market_tickers: Sequence[str]


@final
class GetEventForecastPercentilesHistoryResponse(msgspec.Struct, frozen=True):
    forecast_history: Sequence[ForecastPercentilesPoint]


@final
class GetEventMetadataResponse(msgspec.Struct, frozen=True):
    image_url: str
    market_details: Sequence[MarketMetadata]
    settlement_sources: Sequence[SettlementSource]
    competition: str | None = None
    competition_scope: str | None = None
    featured_image_url: str | None = None


@final
class GetEventResponse(msgspec.Struct, frozen=True):
    event: EventData
    markets: Sequence[Market]


@final
class GetEventsResponse(msgspec.Struct, frozen=True):
    cursor: str
    events: Sequence[EventData]
    milestones: Sequence[Milestone] | None = None


@final
class GetExchangeAnnouncementsResponse(msgspec.Struct, frozen=True):
    announcements: Sequence[Announcement]


@final
class GetExchangeScheduleResponse(msgspec.Struct, frozen=True):
    schedule: Schedule


@final
class GetFillsResponse(msgspec.Struct, frozen=True):
    cursor: str
    fills: Sequence[Fill]


@final
class GetFiltersBySportsResponse(msgspec.Struct, frozen=True):
    filters_by_sports: Mapping[str, SportFilterDetails]
    sport_ordering: Sequence[str]


@final
class GetIncentiveProgramsResponse(msgspec.Struct, frozen=True):
    incentive_programs: Sequence[IncentiveProgram]
    next_cursor: str | None = None


@final
class GetLiveDataResponse(msgspec.Struct, frozen=True):
    live_data: LiveData


@final
class GetLiveDatasResponse(msgspec.Struct, frozen=True):
    live_datas: Sequence[LiveData]


@final
class GetMarketCandlesticksResponse(msgspec.Struct, frozen=True):
    candlesticks: Sequence[MarketCandlestick]
    ticker: str


@final
class GetMarketOrderbookResponse(msgspec.Struct, frozen=True):
    orderbook: Orderbook
    orderbook_fp: OrderbookCountFp


@final
class GetMarketResponse(msgspec.Struct, frozen=True):
    market: Market


@final
class GetMarketsResponse(msgspec.Struct, frozen=True):
    cursor: str
    markets: Sequence[Market]


@final
class GetMilestoneResponse(msgspec.Struct, frozen=True):
    milestone: Milestone


@final
class GetMilestonesResponse(msgspec.Struct, frozen=True):
    milestones: Sequence[Milestone]
    cursor: str | None = None


@final
class GetMultivariateEventCollectionLookupHistoryResponse(msgspec.Struct, frozen=True):
    lookup_points: Sequence[LookupPoint]


@final
class GetMultivariateEventCollectionResponse(msgspec.Struct, frozen=True):
    multivariate_contract: MultivariateEventCollection


@final
class GetMultivariateEventCollectionsResponse(msgspec.Struct, frozen=True):
    multivariate_contracts: Sequence[MultivariateEventCollection]
    cursor: str | None = None


@final
class GetMultivariateEventsResponse(msgspec.Struct, frozen=True):
    cursor: str
    events: Sequence[EventData]


@final
class GetOrderGroupResponse(msgspec.Struct, frozen=True):
    is_auto_cancel_enabled: bool
    orders: Sequence[str]


@final
class GetOrderGroupsResponse(msgspec.Struct, frozen=True):
    order_groups: Sequence[OrderGroup] | None = None


@final
class GetOrderQueuePositionResponse(msgspec.Struct, frozen=True):
    queue_position: int


@final
class GetOrderQueuePositionsResponse(msgspec.Struct, frozen=True):
    queue_positions: Sequence[OrderQueuePosition]


@final
class GetOrderResponse(msgspec.Struct, frozen=True):
    order: Order


@final
class GetOrdersResponse(msgspec.Struct, frozen=True):
    cursor: str
    orders: Sequence[Order]


@final
class GetPortfolioRestingOrderTotalValueResponse(msgspec.Struct, frozen=True):
    total_resting_order_value: int


@final
class GetPositionsResponse(msgspec.Struct, frozen=True):
    event_positions: Sequence[EventPosition]
    market_positions: Sequence[MarketPosition]
    cursor: str | None = None


@final
class GetQuoteResponse(msgspec.Struct, frozen=True):
    quote: Quote


@final
class GetQuotesResponse(msgspec.Struct, frozen=True):
    quotes: Sequence[Quote]
    cursor: str | None = None


@final
class GetRfQsResponse(msgspec.Struct, frozen=True):
    rfqs: Sequence[Rfq]
    cursor: str | None = None


@final
class GetRfqResponse(msgspec.Struct, frozen=True):
    rfq: Rfq


@final
class GetSeriesFeeChangesResponse(msgspec.Struct, frozen=True):
    series_fee_change_arr: Sequence[SeriesFeeChange]


@final
class GetSeriesListResponse(msgspec.Struct, frozen=True):
    series: Sequence[Series]


@final
class GetSeriesResponse(msgspec.Struct, frozen=True):
    series: Series


@final
class GetSettlementsResponse(msgspec.Struct, frozen=True):
    settlements: Sequence[Settlement]
    cursor: str | None = None


@final
class GetStructuredTargetResponse(msgspec.Struct, frozen=True):
    structured_target: StructuredTarget | None = None


@final
class GetStructuredTargetsResponse(msgspec.Struct, frozen=True):
    cursor: str | None = None
    structured_targets: Sequence[StructuredTarget] | None = None


@final
class GetSubaccountBalancesResponse(msgspec.Struct, frozen=True):
    subaccount_balances: Sequence[SubaccountBalance]


@final
class GetSubaccountTransfersResponse(msgspec.Struct, frozen=True):
    transfers: Sequence[SubaccountTransfer]
    cursor: str | None = None


@final
class GetTagsForSeriesCategoriesResponse(msgspec.Struct, frozen=True):
    tags_by_categories: Mapping[str, Sequence[str]]


@final
class GetTradesResponse(msgspec.Struct, frozen=True):
    cursor: str
    trades: Sequence[Trade]


@final
class GetUserDataTimestampResponse(msgspec.Struct, frozen=True):
    as_of_time: datetime.datetime


@final
class IncentiveProgram(msgspec.Struct, frozen=True):
    end_date: datetime.datetime
    id: str
    incentive_type: Literal["liquidity", "volume"]
    market_ticker: str
    paid_out: bool
    period_reward: int
    start_date: datetime.datetime
    discount_factor_bps: int | None = None
    target_size: int | None = None
    target_size_fp: FixedPointCount | None = None


@final
class IntraExchangeInstanceTransferRequest(msgspec.Struct, frozen=True):
    amount: int
    destination: ExchangeInstance
    source: ExchangeInstance


@final
class IntraExchangeInstanceTransferResponse(msgspec.Struct, frozen=True):
    transfer_id: str


@final
class LiveData(msgspec.Struct, frozen=True):
    details: Mapping[str, Any]
    milestone_id: str
    type: str


@final
class LookupPoint(msgspec.Struct, frozen=True):
    event_ticker: str
    last_queried_ts: datetime.datetime
    market_ticker: str
    selected_markets: Sequence[TickerPair]


@final
class LookupTickersForMarketInMultivariateEventCollectionRequest(
    msgspec.Struct, frozen=True
):
    selected_markets: Sequence[TickerPair]


@final
class LookupTickersForMarketInMultivariateEventCollectionResponse(
    msgspec.Struct, frozen=True
):
    event_ticker: str
    market_ticker: str


@final
class MaintenanceWindow(msgspec.Struct, frozen=True):
    end_datetime: datetime.datetime
    start_datetime: datetime.datetime


@final
class Market(msgspec.Struct, frozen=True):
    can_close_early: bool
    close_time: datetime.datetime
    created_time: datetime.datetime
    event_ticker: str
    expiration_time: datetime.datetime
    expiration_value: str
    last_price: float
    last_price_dollars: FixedPointDollars
    latest_expiration_time: datetime.datetime
    liquidity: int
    liquidity_dollars: FixedPointDollars
    market_type: Literal["binary", "scalar"]
    no_ask: float
    no_ask_dollars: FixedPointDollars
    no_bid: float
    no_bid_dollars: FixedPointDollars
    no_sub_title: str
    notional_value: int
    notional_value_dollars: FixedPointDollars
    open_interest: int
    open_interest_fp: FixedPointCount
    open_time: datetime.datetime
    previous_price: int
    previous_price_dollars: FixedPointDollars
    previous_yes_ask: int
    previous_yes_ask_dollars: FixedPointDollars
    previous_yes_bid: int
    previous_yes_bid_dollars: FixedPointDollars
    price_level_structure: str
    price_ranges: Sequence[PriceRange]
    response_price_units: Literal["usd_cent"]
    result: Literal["yes", "no", ""]
    rules_primary: str
    rules_secondary: str
    settlement_timer_seconds: int
    status: Literal[
        "initialized",
        "inactive",
        "active",
        "closed",
        "determined",
        "disputed",
        "amended",
        "finalized",
    ]
    subtitle: str
    tick_size: int
    ticker: str
    title: str
    volume: int
    volume_24h: int
    volume_24h_fp: FixedPointCount
    volume_fp: FixedPointCount
    yes_ask: float
    yes_ask_dollars: FixedPointDollars
    yes_bid: float
    yes_bid_dollars: FixedPointDollars
    yes_sub_title: str
    cap_strike: float | None = None
    custom_strike: Mapping[str, Any] | None = None
    early_close_condition: str | None = None
    expected_expiration_time: datetime.datetime | None = None
    fee_waiver_expiration_time: datetime.datetime | None = None
    floor_strike: float | None = None
    functional_strike: str | None = None
    is_provisional: bool | None = None
    mve_collection_ticker: str | None = None
    mve_selected_legs: Sequence[MveSelectedLeg] | None = None
    primary_participant_key: str | None = None
    settlement_ts: datetime.datetime | None = None
    settlement_value: int | None = None
    settlement_value_dollars: FixedPointDollars | None = None
    strike_type: (
        Literal[
            "greater",
            "greater_or_equal",
            "less",
            "less_or_equal",
            "between",
            "functional",
            "custom",
            "structured",
        ]
        | None
    ) = None


@final
class MarketCandlestick(msgspec.Struct, frozen=True):
    end_period_ts: int
    open_interest: int
    open_interest_fp: FixedPointCount
    price: PriceDistribution
    volume: int
    volume_fp: FixedPointCount
    yes_ask: BidAskDistribution
    yes_bid: BidAskDistribution


@final
class MarketCandlesticksResponse(msgspec.Struct, frozen=True):
    candlesticks: Sequence[MarketCandlestick]
    market_ticker: str


@final
class MarketMetadata(msgspec.Struct, frozen=True):
    color_code: str
    image_url: str
    market_ticker: str


@final
class MarketPosition(msgspec.Struct, frozen=True):
    fees_paid: int
    fees_paid_dollars: FixedPointDollars
    market_exposure: int
    market_exposure_dollars: FixedPointDollars
    position: int
    position_fp: FixedPointCount
    realized_pnl: int
    realized_pnl_dollars: FixedPointDollars
    resting_orders_count: int
    ticker: str
    total_traded: int
    total_traded_dollars: FixedPointDollars
    last_updated_ts: datetime.datetime | None = None


@final
class Milestone(msgspec.Struct, frozen=True):
    category: str
    details: Mapping[str, Any]
    id: str
    last_updated_ts: datetime.datetime
    notification_message: str
    primary_event_tickers: Sequence[str]
    related_event_tickers: Sequence[str]
    start_date: datetime.datetime
    title: str
    type: str
    end_date: datetime.datetime | None = None
    source_id: str | None = None


@final
class MultivariateEventCollection(msgspec.Struct, frozen=True):
    associated_event_tickers: Sequence[str]
    associated_events: Sequence[AssociatedEvent]
    close_date: datetime.datetime
    collection_ticker: str
    description: str
    functional_description: str
    is_all_yes: bool
    is_ordered: bool
    is_single_market_per_event: bool
    open_date: datetime.datetime
    series_ticker: str
    size_max: int
    size_min: int
    title: str


@final
class MveSelectedLeg(msgspec.Struct, frozen=True):
    event_ticker: str | None = None
    market_ticker: str | None = None
    side: str | None = None
    yes_settlement_value_dollars: FixedPointDollars | None = None


@final
class Order(msgspec.Struct, frozen=True):
    action: Literal["buy", "sell"]
    client_order_id: str
    fill_count: int
    fill_count_fp: FixedPointCount
    initial_count: int
    initial_count_fp: FixedPointCount
    maker_fees: int
    maker_fill_cost: int
    maker_fill_cost_dollars: FixedPointDollars
    no_price: int
    no_price_dollars: FixedPointDollars
    order_id: str
    queue_position: int
    remaining_count: int
    remaining_count_fp: FixedPointCount
    side: Literal["yes", "no"]
    status: OrderStatus
    taker_fees: int
    taker_fill_cost: int
    taker_fill_cost_dollars: FixedPointDollars
    ticker: str
    type: Literal["limit", "market"]
    user_id: str
    yes_price: int
    yes_price_dollars: FixedPointDollars
    cancel_order_on_pause: bool | None = None
    created_time: datetime.datetime | None = None
    expiration_time: datetime.datetime | None = None
    last_update_time: datetime.datetime | None = None
    maker_fees_dollars: FixedPointDollars | None = None
    order_group_id: str | None = None
    self_trade_prevention_type: SelfTradePreventionType | None = None
    taker_fees_dollars: FixedPointDollars | None = None


@final
class OrderGroup(msgspec.Struct, frozen=True):
    id: str
    is_auto_cancel_enabled: bool


@final
class OrderQueuePosition(msgspec.Struct, frozen=True):
    market_ticker: str
    order_id: str
    queue_position: int


class OrderStatus(str, Enum):
    RESTING = "resting"
    CANCELED = "canceled"
    EXECUTED = "executed"


@final
class Orderbook(msgspec.Struct, frozen=True):
    """Legacy integer-count orderbook (will be deprecated). Prefer OrderbookCountFp / orderbook_fp for fixed-point contract counts."""

    no_dollars: Sequence[PriceLevelDollars]
    yes_dollars: Sequence[PriceLevelDollars]
    no: Sequence[OrderbookLevel] | None = None
    yes: Sequence[OrderbookLevel] | None = None


@final
class OrderbookCountFp(msgspec.Struct, frozen=True):
    """Orderbook with fixed-point contract counts (fp) in all dollar price levels."""

    no_dollars: Sequence[PriceLevelDollarsCountFp]
    yes_dollars: Sequence[PriceLevelDollarsCountFp]


@final
class PercentilePoint(msgspec.Struct, frozen=True):
    formatted_forecast: str
    numerical_forecast: float
    percentile: int
    raw_numerical_forecast: float


@final
class PriceDistribution(msgspec.Struct, frozen=True):
    close: int | None = None
    close_dollars: FixedPointDollars | None = None
    high: int | None = None
    high_dollars: FixedPointDollars | None = None
    low: int | None = None
    low_dollars: FixedPointDollars | None = None
    max: int | None = None
    max_dollars: FixedPointDollars | None = None
    mean: int | None = None
    mean_dollars: FixedPointDollars | None = None
    min: int | None = None
    min_dollars: FixedPointDollars | None = None
    open: int | None = None
    open_dollars: FixedPointDollars | None = None
    previous: int | None = None
    previous_dollars: FixedPointDollars | None = None


@final
class PriceRange(msgspec.Struct, frozen=True):
    end: str
    start: str
    step: str


@final
class Quote(msgspec.Struct, frozen=True):
    contracts: int
    contracts_fp: FixedPointCount
    created_ts: datetime.datetime
    creator_id: str
    id: str
    market_ticker: str
    no_bid: int
    no_bid_dollars: FixedPointDollars
    rfq_creator_id: str
    rfq_id: str
    status: Literal["open", "accepted", "confirmed", "executed", "cancelled"]
    updated_ts: datetime.datetime
    yes_bid: int
    yes_bid_dollars: FixedPointDollars
    accepted_side: Literal["yes", "no"] | None = None
    accepted_ts: datetime.datetime | None = None
    cancellation_reason: str | None = None
    cancelled_ts: datetime.datetime | None = None
    confirmed_ts: datetime.datetime | None = None
    creator_order_id: str | None = None
    creator_user_id: str | None = None
    executed_ts: datetime.datetime | None = None
    rest_remainder: bool | None = None
    rfq_creator_order_id: str | None = None
    rfq_creator_user_id: str | None = None
    rfq_target_cost_centi_cents: int | None = None


@final
class Rfq(msgspec.Struct, frozen=True):
    contracts: int
    contracts_fp: FixedPointCount
    created_ts: datetime.datetime
    creator_id: str
    id: str
    market_ticker: str
    status: Literal["open", "closed"]
    cancellation_reason: str | None = None
    cancelled_ts: datetime.datetime | None = None
    creator_user_id: str | None = None
    mve_collection_ticker: str | None = None
    mve_selected_legs: Sequence[MveSelectedLeg] | None = None
    rest_remainder: bool | None = None
    target_cost_centi_cents: int | None = None
    updated_ts: datetime.datetime | None = None


@final
class Schedule(msgspec.Struct, frozen=True):
    maintenance_windows: Sequence[MaintenanceWindow]
    standard_hours: Sequence[WeeklySchedule]


@final
class ScopeList(msgspec.Struct, frozen=True):
    scopes: Sequence[str]


class SelfTradePreventionType(str, Enum):
    TAKER_AT_CROSS = "taker_at_cross"
    MAKER = "maker"


@final
class Series(msgspec.Struct, frozen=True):
    additional_prohibitions: Sequence[str]
    category: str
    contract_terms_url: str
    contract_url: str
    fee_multiplier: float
    fee_type: Literal["quadratic", "quadratic_with_maker_fees", "flat"]
    frequency: str
    settlement_sources: Sequence[SettlementSource]
    tags: Sequence[str]
    ticker: str
    title: str
    product_metadata: Mapping[str, Any] | None = None
    volume: int | None = None
    volume_fp: FixedPointCount | None = None


@final
class SeriesFeeChange(msgspec.Struct, frozen=True):
    fee_multiplier: float
    fee_type: Literal["quadratic", "quadratic_with_maker_fees", "flat"]
    id: str
    scheduled_ts: datetime.datetime
    series_ticker: str


@final
class Settlement(msgspec.Struct, frozen=True):
    event_ticker: str
    fee_cost: str
    market_result: Literal["yes", "no", "scalar", "void"]
    no_count: int
    no_count_fp: FixedPointCount
    no_total_cost: int
    revenue: int
    settled_time: datetime.datetime
    ticker: str
    yes_count: int
    yes_count_fp: FixedPointCount
    yes_total_cost: int
    value: int | None = None


@final
class SettlementSource(msgspec.Struct, frozen=True):
    name: str | None = None
    url: str | None = None


@final
class SportFilterDetails(msgspec.Struct, frozen=True):
    competitions: Mapping[str, ScopeList]
    scopes: Sequence[str]


@final
class StructuredTarget(msgspec.Struct, frozen=True):
    details: Mapping[str, Any] | None = None
    id: str | None = None
    last_updated_ts: datetime.datetime | None = None
    name: str | None = None
    source_id: str | None = None
    type: str | None = None


@final
class SubaccountBalance(msgspec.Struct, frozen=True):
    balance: int
    subaccount_number: int
    updated_ts: int


@final
class SubaccountTransfer(msgspec.Struct, frozen=True):
    amount: int
    created_ts: int
    from_subaccount: int
    to_subaccount: int
    transfer_id: str


@final
class TickerPair(msgspec.Struct, frozen=True):
    event_ticker: str
    market_ticker: str
    side: Literal["yes", "no"]


@final
class Trade(msgspec.Struct, frozen=True):
    count: int
    count_fp: FixedPointCount
    no_price: int
    no_price_dollars: FixedPointDollars
    price: float
    taker_side: Literal["yes", "no"]
    ticker: str
    trade_id: str
    yes_price: int
    yes_price_dollars: FixedPointDollars
    created_time: datetime.datetime | None = None


@final
class WeeklySchedule(msgspec.Struct, frozen=True):
    end_time: datetime.datetime
    friday: Sequence[DailySchedule]
    monday: Sequence[DailySchedule]
    saturday: Sequence[DailySchedule]
    start_time: datetime.datetime
    sunday: Sequence[DailySchedule]
    thursday: Sequence[DailySchedule]
    tuesday: Sequence[DailySchedule]
    wednesday: Sequence[DailySchedule]
