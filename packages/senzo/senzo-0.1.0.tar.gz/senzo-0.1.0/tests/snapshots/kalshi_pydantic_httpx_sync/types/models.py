from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
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
class AcceptQuoteRequest(BaseModel):
    accepted_side: Literal["yes", "no"]


@final
class AmendOrderRequest(BaseModel):
    action: Literal["buy", "sell"]
    client_order_id: str
    side: Literal["yes", "no"]
    ticker: str
    updated_client_order_id: str
    count: int | None = Field(default=None)
    count_fp: FixedPointCount | None = Field(default=None)
    no_price: int | None = Field(default=None)
    no_price_dollars: FixedPointDollars | None = Field(default=None)
    yes_price: int | None = Field(default=None)
    yes_price_dollars: FixedPointDollars | None = Field(default=None)


@final
class AmendOrderResponse(BaseModel):
    old_order: Order
    order: Order


@final
class Announcement(BaseModel):
    delivery_time: datetime.datetime
    message: str
    status: Literal["active", "inactive"]
    type: Literal["info", "warning", "error"]


@final
class ApiKey(BaseModel):
    api_key_id: str
    name: str
    scopes: Sequence[str]


@final
class ApplySubaccountTransferRequest(BaseModel):
    amount_cents: int
    client_transfer_id: uuid.UUID
    from_subaccount: int
    to_subaccount: int


@final
class ApplySubaccountTransferResponse(BaseModel):
    """Empty response indicating successful transfer."""


@final
class AssociatedEvent(BaseModel):
    active_quoters: Sequence[str]
    is_yes_only: bool
    ticker: str
    size_max: int | None = Field(default=None)
    size_min: int | None = Field(default=None)


@final
class BatchCancelOrdersIndividualResponse(BaseModel):
    order_id: str
    reduced_by: int
    reduced_by_fp: FixedPointCount
    error: ErrorResponse | None = Field(default=None)
    order: Order | None = Field(default=None)


@final
class BatchCancelOrdersRequest(BaseModel):
    ids: Sequence[str]


@final
class BatchCancelOrdersResponse(BaseModel):
    orders: Sequence[BatchCancelOrdersIndividualResponse]


@final
class BatchCreateOrdersIndividualResponse(BaseModel):
    client_order_id: str | None = Field(default=None)
    error: ErrorResponse | None = Field(default=None)
    order: Order | None = Field(default=None)


@final
class BatchCreateOrdersRequest(BaseModel):
    orders: Sequence[CreateOrderRequest]


@final
class BatchCreateOrdersResponse(BaseModel):
    orders: Sequence[BatchCreateOrdersIndividualResponse]


@final
class BatchGetMarketCandlesticksResponse(BaseModel):
    markets: Sequence[MarketCandlesticksResponse]


@final
class BidAskDistribution(BaseModel):
    close: int
    close_dollars: FixedPointDollars
    high: int
    high_dollars: FixedPointDollars
    low: int
    low_dollars: FixedPointDollars
    open: int
    open_dollars: FixedPointDollars


@final
class CancelOrderResponse(BaseModel):
    order: Order
    reduced_by: int
    reduced_by_fp: FixedPointCount


@final
class CreateApiKeyRequest(BaseModel):
    name: str
    public_key: str
    scopes: Sequence[str] | None = Field(default=None)


@final
class CreateApiKeyResponse(BaseModel):
    api_key_id: str


@final
class CreateMarketInMultivariateEventCollectionRequest(BaseModel):
    selected_markets: Sequence[TickerPair]
    with_market_payload: bool | None = Field(default=None)


@final
class CreateMarketInMultivariateEventCollectionResponse(BaseModel):
    event_ticker: str
    market_ticker: str
    market: Market | None = Field(default=None)


@final
class CreateOrderGroupRequest(BaseModel):
    contracts_limit: int | None = Field(default=None)
    contracts_limit_fp: FixedPointCount | None = Field(default=None)


@final
class CreateOrderGroupResponse(BaseModel):
    order_group_id: str


@final
class CreateOrderRequest(BaseModel):
    action: Literal["buy", "sell"]
    side: Literal["yes", "no"]
    ticker: str
    buy_max_cost: int | None = Field(default=None)
    cancel_order_on_pause: bool | None = Field(default=None)
    client_order_id: str | None = Field(default=None)
    count: int | None = Field(default=None)
    count_fp: FixedPointCount | None = Field(default=None)
    expiration_ts: int | None = Field(default=None)
    no_price: int | None = Field(default=None)
    no_price_dollars: FixedPointDollars | None = Field(default=None)
    order_group_id: str | None = Field(default=None)
    post_only: bool | None = Field(default=None)
    reduce_only: bool | None = Field(default=None)
    self_trade_prevention_type: SelfTradePreventionType | None = Field(default=None)
    sell_position_floor: int | None = Field(default=None)
    subaccount: int | None = Field(default=None)
    time_in_force: (
        Literal["fill_or_kill", "good_till_canceled", "immediate_or_cancel"] | None
    ) = Field(default=None)
    type: Literal["limit", "market"] | None = Field(default=None)
    yes_price: int | None = Field(default=None)
    yes_price_dollars: FixedPointDollars | None = Field(default=None)


@final
class CreateOrderResponse(BaseModel):
    order: Order


@final
class CreateQuoteRequest(BaseModel):
    no_bid: FixedPointDollars
    rest_remainder: bool
    rfq_id: str
    yes_bid: FixedPointDollars


@final
class CreateQuoteResponse(BaseModel):
    id: str


@final
class CreateRfqRequest(BaseModel):
    market_ticker: str
    rest_remainder: bool
    contracts: int | None = Field(default=None)
    contracts_fp: FixedPointCount | None = Field(default=None)
    replace_existing: bool | None = Field(default=None)
    subtrader_id: str | None = Field(default=None)
    target_cost_centi_cents: int | None = Field(default=None)


@final
class CreateRfqResponse(BaseModel):
    id: str


@final
class CreateSubaccountResponse(BaseModel):
    subaccount_number: int


@final
class DailySchedule(BaseModel):
    close_time: str
    open_time: str


@final
class DecreaseOrderRequest(BaseModel):
    reduce_by: int | None = Field(default=None)
    reduce_by_fp: FixedPointCount | None = Field(default=None)
    reduce_to: int | None = Field(default=None)
    reduce_to_fp: FixedPointCount | None = Field(default=None)


@final
class DecreaseOrderResponse(BaseModel):
    order: Order


@final
class EmptyResponse(BaseModel):
    """An empty response body"""


@final
class ErrorResponse(BaseModel):
    code: str | None = Field(default=None)
    details: str | None = Field(default=None)
    message: str | None = Field(default=None)
    service: str | None = Field(default=None)


@final
class EventData(BaseModel):
    available_on_brokers: bool
    category: str
    collateral_return_type: str
    event_ticker: str
    mutually_exclusive: bool
    product_metadata: Mapping[str, Any]
    series_ticker: str
    sub_title: str
    title: str
    markets: Sequence[Market] | None = Field(default=None)
    strike_date: datetime.datetime | None = Field(default=None)
    strike_period: str | None = Field(default=None)


@final
class EventPosition(BaseModel):
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
class ExchangeStatus(BaseModel):
    exchange_active: bool
    trading_active: bool
    exchange_estimated_resume_time: datetime.datetime | None = Field(default=None)


@final
class Fill(BaseModel):
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
    client_order_id: str | None = Field(default=None)
    created_time: datetime.datetime | None = Field(default=None)
    ts: int | None = Field(default=None)


@final
class ForecastPercentilesPoint(BaseModel):
    end_period_ts: int
    event_ticker: str
    percentile_points: Sequence[PercentilePoint]
    period_interval: int


@final
class GenerateApiKeyRequest(BaseModel):
    name: str
    scopes: Sequence[str] | None = Field(default=None)


@final
class GenerateApiKeyResponse(BaseModel):
    api_key_id: str
    private_key: str


@final
class GetApiKeysResponse(BaseModel):
    api_keys: Sequence[ApiKey]


@final
class GetBalanceResponse(BaseModel):
    balance: int
    portfolio_value: int
    updated_ts: int


@final
class GetCommunicationsIdResponse(BaseModel):
    communications_id: str


@final
class GetEventCandlesticksResponse(BaseModel):
    adjusted_end_ts: int
    market_candlesticks: Sequence[Sequence[MarketCandlestick]]
    market_tickers: Sequence[str]


@final
class GetEventForecastPercentilesHistoryResponse(BaseModel):
    forecast_history: Sequence[ForecastPercentilesPoint]


@final
class GetEventMetadataResponse(BaseModel):
    image_url: str
    market_details: Sequence[MarketMetadata]
    settlement_sources: Sequence[SettlementSource]
    competition: str | None = Field(default=None)
    competition_scope: str | None = Field(default=None)
    featured_image_url: str | None = Field(default=None)


@final
class GetEventResponse(BaseModel):
    event: EventData
    markets: Sequence[Market]


@final
class GetEventsResponse(BaseModel):
    cursor: str
    events: Sequence[EventData]
    milestones: Sequence[Milestone] | None = Field(default=None)


@final
class GetExchangeAnnouncementsResponse(BaseModel):
    announcements: Sequence[Announcement]


@final
class GetExchangeScheduleResponse(BaseModel):
    schedule: Schedule


@final
class GetFillsResponse(BaseModel):
    cursor: str
    fills: Sequence[Fill]


@final
class GetFiltersBySportsResponse(BaseModel):
    filters_by_sports: Mapping[str, SportFilterDetails]
    sport_ordering: Sequence[str]


@final
class GetIncentiveProgramsResponse(BaseModel):
    incentive_programs: Sequence[IncentiveProgram]
    next_cursor: str | None = Field(default=None)


@final
class GetLiveDataResponse(BaseModel):
    live_data: LiveData


@final
class GetLiveDatasResponse(BaseModel):
    live_datas: Sequence[LiveData]


@final
class GetMarketCandlesticksResponse(BaseModel):
    candlesticks: Sequence[MarketCandlestick]
    ticker: str


@final
class GetMarketOrderbookResponse(BaseModel):
    orderbook: Orderbook
    orderbook_fp: OrderbookCountFp


@final
class GetMarketResponse(BaseModel):
    market: Market


@final
class GetMarketsResponse(BaseModel):
    cursor: str
    markets: Sequence[Market]


@final
class GetMilestoneResponse(BaseModel):
    milestone: Milestone


@final
class GetMilestonesResponse(BaseModel):
    milestones: Sequence[Milestone]
    cursor: str | None = Field(default=None)


@final
class GetMultivariateEventCollectionLookupHistoryResponse(BaseModel):
    lookup_points: Sequence[LookupPoint]


@final
class GetMultivariateEventCollectionResponse(BaseModel):
    multivariate_contract: MultivariateEventCollection


@final
class GetMultivariateEventCollectionsResponse(BaseModel):
    multivariate_contracts: Sequence[MultivariateEventCollection]
    cursor: str | None = Field(default=None)


@final
class GetMultivariateEventsResponse(BaseModel):
    cursor: str
    events: Sequence[EventData]


@final
class GetOrderGroupResponse(BaseModel):
    is_auto_cancel_enabled: bool
    orders: Sequence[str]


@final
class GetOrderGroupsResponse(BaseModel):
    order_groups: Sequence[OrderGroup] | None = Field(default=None)


@final
class GetOrderQueuePositionResponse(BaseModel):
    queue_position: int


@final
class GetOrderQueuePositionsResponse(BaseModel):
    queue_positions: Sequence[OrderQueuePosition]


@final
class GetOrderResponse(BaseModel):
    order: Order


@final
class GetOrdersResponse(BaseModel):
    cursor: str
    orders: Sequence[Order]


@final
class GetPortfolioRestingOrderTotalValueResponse(BaseModel):
    total_resting_order_value: int


@final
class GetPositionsResponse(BaseModel):
    event_positions: Sequence[EventPosition]
    market_positions: Sequence[MarketPosition]
    cursor: str | None = Field(default=None)


@final
class GetQuoteResponse(BaseModel):
    quote: Quote


@final
class GetQuotesResponse(BaseModel):
    quotes: Sequence[Quote]
    cursor: str | None = Field(default=None)


@final
class GetRfQsResponse(BaseModel):
    rfqs: Sequence[Rfq]
    cursor: str | None = Field(default=None)


@final
class GetRfqResponse(BaseModel):
    rfq: Rfq


@final
class GetSeriesFeeChangesResponse(BaseModel):
    series_fee_change_arr: Sequence[SeriesFeeChange]


@final
class GetSeriesListResponse(BaseModel):
    series: Sequence[Series]


@final
class GetSeriesResponse(BaseModel):
    series: Series


@final
class GetSettlementsResponse(BaseModel):
    settlements: Sequence[Settlement]
    cursor: str | None = Field(default=None)


@final
class GetStructuredTargetResponse(BaseModel):
    structured_target: StructuredTarget | None = Field(default=None)


@final
class GetStructuredTargetsResponse(BaseModel):
    cursor: str | None = Field(default=None)
    structured_targets: Sequence[StructuredTarget] | None = Field(default=None)


@final
class GetSubaccountBalancesResponse(BaseModel):
    subaccount_balances: Sequence[SubaccountBalance]


@final
class GetSubaccountTransfersResponse(BaseModel):
    transfers: Sequence[SubaccountTransfer]
    cursor: str | None = Field(default=None)


@final
class GetTagsForSeriesCategoriesResponse(BaseModel):
    tags_by_categories: Mapping[str, Sequence[str]]


@final
class GetTradesResponse(BaseModel):
    cursor: str
    trades: Sequence[Trade]


@final
class GetUserDataTimestampResponse(BaseModel):
    as_of_time: datetime.datetime


@final
class IncentiveProgram(BaseModel):
    end_date: datetime.datetime
    id: str
    incentive_type: Literal["liquidity", "volume"]
    market_ticker: str
    paid_out: bool
    period_reward: int
    start_date: datetime.datetime
    discount_factor_bps: int | None = Field(default=None)
    target_size: int | None = Field(default=None)
    target_size_fp: FixedPointCount | None = Field(default=None)


@final
class IntraExchangeInstanceTransferRequest(BaseModel):
    amount: int
    destination: ExchangeInstance
    source: ExchangeInstance


@final
class IntraExchangeInstanceTransferResponse(BaseModel):
    transfer_id: str


@final
class LiveData(BaseModel):
    details: Mapping[str, Any]
    milestone_id: str
    type: str


@final
class LookupPoint(BaseModel):
    event_ticker: str
    last_queried_ts: datetime.datetime
    market_ticker: str
    selected_markets: Sequence[TickerPair]


@final
class LookupTickersForMarketInMultivariateEventCollectionRequest(BaseModel):
    selected_markets: Sequence[TickerPair]


@final
class LookupTickersForMarketInMultivariateEventCollectionResponse(BaseModel):
    event_ticker: str
    market_ticker: str


@final
class MaintenanceWindow(BaseModel):
    end_datetime: datetime.datetime
    start_datetime: datetime.datetime


@final
class Market(BaseModel):
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
    cap_strike: float | None = Field(default=None)
    custom_strike: Mapping[str, Any] | None = Field(default=None)
    early_close_condition: str | None = Field(default=None)
    expected_expiration_time: datetime.datetime | None = Field(default=None)
    fee_waiver_expiration_time: datetime.datetime | None = Field(default=None)
    floor_strike: float | None = Field(default=None)
    functional_strike: str | None = Field(default=None)
    is_provisional: bool | None = Field(default=None)
    mve_collection_ticker: str | None = Field(default=None)
    mve_selected_legs: Sequence[MveSelectedLeg] | None = Field(default=None)
    primary_participant_key: str | None = Field(default=None)
    settlement_ts: datetime.datetime | None = Field(default=None)
    settlement_value: int | None = Field(default=None)
    settlement_value_dollars: FixedPointDollars | None = Field(default=None)
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
    ) = Field(default=None)


@final
class MarketCandlestick(BaseModel):
    end_period_ts: int
    open_interest: int
    open_interest_fp: FixedPointCount
    price: PriceDistribution
    volume: int
    volume_fp: FixedPointCount
    yes_ask: BidAskDistribution
    yes_bid: BidAskDistribution


@final
class MarketCandlesticksResponse(BaseModel):
    candlesticks: Sequence[MarketCandlestick]
    market_ticker: str


@final
class MarketMetadata(BaseModel):
    color_code: str
    image_url: str
    market_ticker: str


@final
class MarketPosition(BaseModel):
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
    last_updated_ts: datetime.datetime | None = Field(default=None)


@final
class Milestone(BaseModel):
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
    end_date: datetime.datetime | None = Field(default=None)
    source_id: str | None = Field(default=None)


@final
class MultivariateEventCollection(BaseModel):
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
class MveSelectedLeg(BaseModel):
    event_ticker: str | None = Field(default=None)
    market_ticker: str | None = Field(default=None)
    side: str | None = Field(default=None)
    yes_settlement_value_dollars: FixedPointDollars | None = Field(default=None)


@final
class Order(BaseModel):
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
    cancel_order_on_pause: bool | None = Field(default=None)
    created_time: datetime.datetime | None = Field(default=None)
    expiration_time: datetime.datetime | None = Field(default=None)
    last_update_time: datetime.datetime | None = Field(default=None)
    maker_fees_dollars: FixedPointDollars | None = Field(default=None)
    order_group_id: str | None = Field(default=None)
    self_trade_prevention_type: SelfTradePreventionType | None = Field(default=None)
    taker_fees_dollars: FixedPointDollars | None = Field(default=None)


@final
class OrderGroup(BaseModel):
    id: str
    is_auto_cancel_enabled: bool


@final
class OrderQueuePosition(BaseModel):
    market_ticker: str
    order_id: str
    queue_position: int


class OrderStatus(str, Enum):
    RESTING = "resting"
    CANCELED = "canceled"
    EXECUTED = "executed"


@final
class Orderbook(BaseModel):
    """Legacy integer-count orderbook (will be deprecated). Prefer OrderbookCountFp / orderbook_fp for fixed-point contract counts."""

    no_dollars: Sequence[PriceLevelDollars]
    yes_dollars: Sequence[PriceLevelDollars]
    no: Sequence[OrderbookLevel] | None = Field(default=None)
    yes: Sequence[OrderbookLevel] | None = Field(default=None)


@final
class OrderbookCountFp(BaseModel):
    """Orderbook with fixed-point contract counts (fp) in all dollar price levels."""

    no_dollars: Sequence[PriceLevelDollarsCountFp]
    yes_dollars: Sequence[PriceLevelDollarsCountFp]


@final
class PercentilePoint(BaseModel):
    formatted_forecast: str
    numerical_forecast: float
    percentile: int
    raw_numerical_forecast: float


@final
class PriceDistribution(BaseModel):
    close: int | None = Field(default=None)
    close_dollars: FixedPointDollars | None = Field(default=None)
    high: int | None = Field(default=None)
    high_dollars: FixedPointDollars | None = Field(default=None)
    low: int | None = Field(default=None)
    low_dollars: FixedPointDollars | None = Field(default=None)
    max: int | None = Field(default=None)
    max_dollars: FixedPointDollars | None = Field(default=None)
    mean: int | None = Field(default=None)
    mean_dollars: FixedPointDollars | None = Field(default=None)
    min: int | None = Field(default=None)
    min_dollars: FixedPointDollars | None = Field(default=None)
    open: int | None = Field(default=None)
    open_dollars: FixedPointDollars | None = Field(default=None)
    previous: int | None = Field(default=None)
    previous_dollars: FixedPointDollars | None = Field(default=None)


@final
class PriceRange(BaseModel):
    end: str
    start: str
    step: str


@final
class Quote(BaseModel):
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
    accepted_side: Literal["yes", "no"] | None = Field(default=None)
    accepted_ts: datetime.datetime | None = Field(default=None)
    cancellation_reason: str | None = Field(default=None)
    cancelled_ts: datetime.datetime | None = Field(default=None)
    confirmed_ts: datetime.datetime | None = Field(default=None)
    creator_order_id: str | None = Field(default=None)
    creator_user_id: str | None = Field(default=None)
    executed_ts: datetime.datetime | None = Field(default=None)
    rest_remainder: bool | None = Field(default=None)
    rfq_creator_order_id: str | None = Field(default=None)
    rfq_creator_user_id: str | None = Field(default=None)
    rfq_target_cost_centi_cents: int | None = Field(default=None)


@final
class Rfq(BaseModel):
    contracts: int
    contracts_fp: FixedPointCount
    created_ts: datetime.datetime
    creator_id: str
    id: str
    market_ticker: str
    status: Literal["open", "closed"]
    cancellation_reason: str | None = Field(default=None)
    cancelled_ts: datetime.datetime | None = Field(default=None)
    creator_user_id: str | None = Field(default=None)
    mve_collection_ticker: str | None = Field(default=None)
    mve_selected_legs: Sequence[MveSelectedLeg] | None = Field(default=None)
    rest_remainder: bool | None = Field(default=None)
    target_cost_centi_cents: int | None = Field(default=None)
    updated_ts: datetime.datetime | None = Field(default=None)


@final
class Schedule(BaseModel):
    maintenance_windows: Sequence[MaintenanceWindow]
    standard_hours: Sequence[WeeklySchedule]


@final
class ScopeList(BaseModel):
    scopes: Sequence[str]


class SelfTradePreventionType(str, Enum):
    TAKER_AT_CROSS = "taker_at_cross"
    MAKER = "maker"


@final
class Series(BaseModel):
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
    product_metadata: Mapping[str, Any] | None = Field(default=None)
    volume: int | None = Field(default=None)
    volume_fp: FixedPointCount | None = Field(default=None)


@final
class SeriesFeeChange(BaseModel):
    fee_multiplier: float
    fee_type: Literal["quadratic", "quadratic_with_maker_fees", "flat"]
    id: str
    scheduled_ts: datetime.datetime
    series_ticker: str


@final
class Settlement(BaseModel):
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
    value: int | None = Field(default=None)


@final
class SettlementSource(BaseModel):
    name: str | None = Field(default=None)
    url: str | None = Field(default=None)


@final
class SportFilterDetails(BaseModel):
    competitions: Mapping[str, ScopeList]
    scopes: Sequence[str]


@final
class StructuredTarget(BaseModel):
    details: Mapping[str, Any] | None = Field(default=None)
    id: str | None = Field(default=None)
    last_updated_ts: datetime.datetime | None = Field(default=None)
    name: str | None = Field(default=None)
    source_id: str | None = Field(default=None)
    type: str | None = Field(default=None)


@final
class SubaccountBalance(BaseModel):
    balance: int
    subaccount_number: int
    updated_ts: int


@final
class SubaccountTransfer(BaseModel):
    amount: int
    created_ts: int
    from_subaccount: int
    to_subaccount: int
    transfer_id: str


@final
class TickerPair(BaseModel):
    event_ticker: str
    market_ticker: str
    side: Literal["yes", "no"]


@final
class Trade(BaseModel):
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
    created_time: datetime.datetime | None = Field(default=None)


@final
class WeeklySchedule(BaseModel):
    end_time: datetime.datetime
    friday: Sequence[DailySchedule]
    monday: Sequence[DailySchedule]
    saturday: Sequence[DailySchedule]
    start_time: datetime.datetime
    sunday: Sequence[DailySchedule]
    thursday: Sequence[DailySchedule]
    tuesday: Sequence[DailySchedule]
    wednesday: Sequence[DailySchedule]
