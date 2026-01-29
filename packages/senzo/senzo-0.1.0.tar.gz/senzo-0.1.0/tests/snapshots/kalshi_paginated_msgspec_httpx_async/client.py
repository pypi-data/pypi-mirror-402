from __future__ import annotations
from typing import final, Literal
import datetime
import httpx
import msgspec
from typing import Any
from ._base import APIError, ResponseValue, encode_path, Paginator
from .types import (
    AcceptQuoteRequest,
    AmendOrderRequest,
    AmendOrderResponse,
    ApplySubaccountTransferRequest,
    ApplySubaccountTransferResponse,
    BatchCancelOrdersRequest,
    BatchCancelOrdersResponse,
    BatchCreateOrdersRequest,
    BatchCreateOrdersResponse,
    BatchGetMarketCandlesticksResponse,
    CancelOrderResponse,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    CreateMarketInMultivariateEventCollectionRequest,
    CreateMarketInMultivariateEventCollectionResponse,
    CreateOrderGroupRequest,
    CreateOrderGroupResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    CreateQuoteRequest,
    CreateQuoteResponse,
    CreateRfqRequest,
    CreateRfqResponse,
    CreateSubaccountResponse,
    DecreaseOrderRequest,
    DecreaseOrderResponse,
    EmptyResponse,
    ExchangeStatus,
    Fill,
    GenerateApiKeyRequest,
    GenerateApiKeyResponse,
    GetApiKeysResponse,
    GetBalanceResponse,
    GetCommunicationsIdResponse,
    GetEventCandlesticksResponse,
    GetEventForecastPercentilesHistoryResponse,
    GetEventMetadataResponse,
    GetEventResponse,
    GetEventsResponse,
    GetExchangeAnnouncementsResponse,
    GetExchangeScheduleResponse,
    GetFillsResponse,
    GetFiltersBySportsResponse,
    GetIncentiveProgramsResponse,
    GetLiveDataResponse,
    GetLiveDatasResponse,
    GetMarketCandlesticksResponse,
    GetMarketOrderbookResponse,
    GetMarketResponse,
    GetMarketsResponse,
    GetMilestoneResponse,
    GetMilestonesResponse,
    GetMultivariateEventCollectionLookupHistoryResponse,
    GetMultivariateEventCollectionResponse,
    GetMultivariateEventCollectionsResponse,
    GetMultivariateEventsResponse,
    GetOrderGroupResponse,
    GetOrderGroupsResponse,
    GetOrderQueuePositionResponse,
    GetOrderQueuePositionsResponse,
    GetOrderResponse,
    GetOrdersResponse,
    GetPortfolioRestingOrderTotalValueResponse,
    GetPositionsResponse,
    GetQuoteResponse,
    GetQuotesResponse,
    GetRfQsResponse,
    GetRfqResponse,
    GetSeriesFeeChangesResponse,
    GetSeriesListResponse,
    GetSeriesResponse,
    GetSettlementsResponse,
    GetStructuredTargetResponse,
    GetStructuredTargetsResponse,
    GetSubaccountBalancesResponse,
    GetSubaccountTransfersResponse,
    GetTagsForSeriesCategoriesResponse,
    GetTradesResponse,
    GetUserDataTimestampResponse,
    LookupTickersForMarketInMultivariateEventCollectionRequest,
    LookupTickersForMarketInMultivariateEventCollectionResponse,
    Order,
    Trade,
)


@final
class ApiKeysClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_api_keys(self) -> ResponseValue[GetApiKeysResponse]:
        """Get API Keys

        Endpoint for retrieving all API keys associated with the authenticated user.  API keys allow programmatic access to the platform without requiring username/password authentication. Each key has a unique identifier and name."""
        _path = "/api_keys"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetApiKeysResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def create_api_key(
        self, body: CreateApiKeyRequest
    ) -> ResponseValue[CreateApiKeyResponse]:
        """Create API Key

        Endpoint for creating a new API key with a user-provided public key.  This endpoint allows users with Premier or Market Maker API usage levels to create API keys by providing their own RSA public key. The platform will use this public key to verify signatures on API requests."""
        _path = "/api_keys"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=CreateApiKeyResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def generate_api_key(
        self, body: GenerateApiKeyRequest
    ) -> ResponseValue[GenerateApiKeyResponse]:
        """Generate API Key

        Endpoint for generating a new API key with an automatically created key pair.  This endpoint generates both a public and private RSA key pair. The public key is stored on the platform, while the private key is returned to the user and must be stored securely. The private key cannot be retrieved again."""
        _path = "/api_keys/generate"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GenerateApiKeyResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def delete_api_key(self, api_key: str) -> ResponseValue[None]:
        """Delete API Key

        Endpoint for deleting an existing API key.  This endpoint permanently deletes an API key. Once deleted, the key can no longer be used for authentication. This action cannot be undone."""
        _path = f"/api_keys/{encode_path(api_key)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="DELETE",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        return ResponseValue(
            value=None, status_code=_response.status_code, headers=_headers_dict
        )


@final
class CommunicationsClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_communications_id(self) -> ResponseValue[GetCommunicationsIdResponse]:
        """Get Communications ID

        Endpoint for getting the communications ID of the logged-in user."""
        _path = "/communications/id"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetCommunicationsIdResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_rf_qs(
        self,
        cursor: str | None = None,
        event_ticker: str | None = None,
        market_ticker: str | None = None,
        limit: int | None = None,
        status: str | None = None,
        creator_user_id: str | None = None,
    ) -> ResponseValue[GetRfQsResponse]:
        """Get RFQs

        Endpoint for getting RFQs"""
        _path = "/communications/rfqs"
        _params: dict[str, Any] = {
            "cursor": cursor,
            "event_ticker": event_ticker,
            "market_ticker": market_ticker,
            "limit": limit,
            "status": status,
            "creator_user_id": creator_user_id,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetRfQsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def create_rfq(
        self, body: CreateRfqRequest
    ) -> ResponseValue[CreateRfqResponse]:
        """Create RFQ

        Endpoint for creating a new RFQ. You can have a maximum of 100 open RFQs at a time."""
        _path = "/communications/rfqs"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=CreateRfqResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_rfq(self, rfq_id: str) -> ResponseValue[GetRfqResponse]:
        """Get RFQ

        Endpoint for getting a single RFQ by id"""
        _path = f"/communications/rfqs/{encode_path(rfq_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetRfqResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def delete_rfq(self, rfq_id: str) -> ResponseValue[None]:
        """Delete RFQ

        Endpoint for deleting an RFQ by ID"""
        _path = f"/communications/rfqs/{encode_path(rfq_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="DELETE",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        return ResponseValue(
            value=None, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_quotes(
        self,
        cursor: str | None = None,
        event_ticker: str | None = None,
        market_ticker: str | None = None,
        limit: int | None = None,
        status: str | None = None,
        quote_creator_user_id: str | None = None,
        rfq_creator_user_id: str | None = None,
        rfq_creator_subtrader_id: str | None = None,
        rfq_id: str | None = None,
    ) -> ResponseValue[GetQuotesResponse]:
        """Get Quotes

        Endpoint for getting quotes"""
        _path = "/communications/quotes"
        _params: dict[str, Any] = {
            "cursor": cursor,
            "event_ticker": event_ticker,
            "market_ticker": market_ticker,
            "limit": limit,
            "status": status,
            "quote_creator_user_id": quote_creator_user_id,
            "rfq_creator_user_id": rfq_creator_user_id,
            "rfq_creator_subtrader_id": rfq_creator_subtrader_id,
            "rfq_id": rfq_id,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetQuotesResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def create_quote(
        self, body: CreateQuoteRequest
    ) -> ResponseValue[CreateQuoteResponse]:
        """Create Quote

        Endpoint for creating a quote in response to an RFQ"""
        _path = "/communications/quotes"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=CreateQuoteResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_quote(self, quote_id: str) -> ResponseValue[GetQuoteResponse]:
        """Get Quote

        Endpoint for getting a particular quote"""
        _path = f"/communications/quotes/{encode_path(quote_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetQuoteResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def delete_quote(self, quote_id: str) -> ResponseValue[None]:
        """Delete Quote

        Endpoint for deleting a quote, which means it can no longer be accepted."""
        _path = f"/communications/quotes/{encode_path(quote_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="DELETE",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        return ResponseValue(
            value=None, status_code=_response.status_code, headers=_headers_dict
        )

    async def accept_quote(
        self, quote_id: str, body: AcceptQuoteRequest
    ) -> ResponseValue[None]:
        """Accept Quote

        Endpoint for accepting a quote. This will require the quoter to confirm"""
        _path = f"/communications/quotes/{encode_path(quote_id)}/accept"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="PUT",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        return ResponseValue(
            value=None, status_code=_response.status_code, headers=_headers_dict
        )

    async def confirm_quote(
        self, quote_id: str, body: EmptyResponse | None = None
    ) -> ResponseValue[None]:
        """Confirm Quote

        Endpoint for confirming a quote. This will start a timer for order execution"""
        _path = f"/communications/quotes/{encode_path(quote_id)}/confirm"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="PUT",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body) if body is not None else None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        return ResponseValue(
            value=None, status_code=_response.status_code, headers=_headers_dict
        )


@final
class EventsClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_market_candlesticks_by_event(
        self,
        ticker: str,
        series_ticker: str,
        start_ts: int,
        end_ts: int,
        period_interval: Literal[1, 60, 1440],
    ) -> ResponseValue[GetEventCandlesticksResponse]:
        """Get Event Candlesticks

        End-point for returning aggregated data across all markets corresponding to an event."""
        _path = f"/series/{encode_path(series_ticker)}/events/{encode_path(ticker)}/candlesticks"
        _params: dict[str, Any] = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetEventCandlesticksResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_events(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        with_nested_markets: bool | None = None,
        with_milestones: bool | None = None,
        status: Literal["open", "closed", "settled"] | None = None,
        series_ticker: str | None = None,
        min_close_ts: int | None = None,
    ) -> ResponseValue[GetEventsResponse]:
        """Get Events

        Get all events. This endpoint excludes multivariate events.
        To retrieve multivariate events, use the GET /events/multivariate endpoint.
        """
        _path = "/events"
        _params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "with_nested_markets": with_nested_markets,
            "with_milestones": with_milestones,
            "status": status,
            "series_ticker": series_ticker,
            "min_close_ts": min_close_ts,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetEventsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_multivariate_events(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        series_ticker: str | None = None,
        collection_ticker: str | None = None,
        with_nested_markets: bool | None = None,
    ) -> ResponseValue[GetMultivariateEventsResponse]:
        """Get Multivariate Events

        Retrieve multivariate (combo) events. These are dynamically created events from multivariate event collections. Supports filtering by series and collection ticker."""
        _path = "/events/multivariate"
        _params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "series_ticker": series_ticker,
            "collection_ticker": collection_ticker,
            "with_nested_markets": with_nested_markets,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetMultivariateEventsResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_event(
        self, event_ticker: str, with_nested_markets: bool | None = None
    ) -> ResponseValue[GetEventResponse]:
        """Get Event

        Endpoint for getting data about an event by its ticker.  An event represents a real-world occurrence that can be traded on, such as an election, sports game, or economic indicator release. Events contain one or more markets where users can place trades on different outcomes."""
        _path = f"/events/{encode_path(event_ticker)}"
        _params: dict[str, Any] = {"with_nested_markets": with_nested_markets}
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetEventResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_event_metadata(
        self, event_ticker: str
    ) -> ResponseValue[GetEventMetadataResponse]:
        """Get Event Metadata

        Endpoint for getting metadata about an event by its ticker.  Returns only the metadata information for an event."""
        _path = f"/events/{encode_path(event_ticker)}/metadata"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetEventMetadataResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_event_forecast_percentiles_history(
        self,
        ticker: str,
        series_ticker: str,
        percentiles: list[int],
        start_ts: int,
        end_ts: int,
        period_interval: Literal[0, 1, 60, 1440],
    ) -> ResponseValue[GetEventForecastPercentilesHistoryResponse]:
        """Get Event Forecast Percentile History

        Endpoint for getting the historical raw and formatted forecast numbers for an event at specific percentiles."""
        _path = f"/series/{encode_path(series_ticker)}/events/{encode_path(ticker)}/forecast_percentile_history"
        _params: dict[str, Any] = {
            "percentiles": percentiles,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetEventForecastPercentilesHistoryResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class ExchangeClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_exchange_status(self) -> ResponseValue[ExchangeStatus]:
        """Get Exchange Status

        Endpoint for getting the exchange status."""
        _path = "/exchange/status"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=ExchangeStatus)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_exchange_announcements(
        self,
    ) -> ResponseValue[GetExchangeAnnouncementsResponse]:
        """Get Exchange Announcements

        Endpoint for getting all exchange-wide announcements."""
        _path = "/exchange/announcements"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetExchangeAnnouncementsResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_series_fee_changes(
        self, series_ticker: str | None = None, show_historical: bool | None = None
    ) -> ResponseValue[GetSeriesFeeChangesResponse]:
        """Get Series Fee Changes"""
        _path = "/series/fee_changes"
        _params: dict[str, Any] = {
            "series_ticker": series_ticker,
            "show_historical": show_historical,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetSeriesFeeChangesResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_exchange_schedule(self) -> ResponseValue[GetExchangeScheduleResponse]:
        """Get Exchange Schedule

        Endpoint for getting the exchange schedule."""
        _path = "/exchange/schedule"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetExchangeScheduleResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_user_data_timestamp(
        self,
    ) -> ResponseValue[GetUserDataTimestampResponse]:
        """Get User Data Timestamp

        There is typically a short delay before exchange events are reflected in the API endpoints. Whenever possible, combine API responses to PUT/POST/DELETE requests with websocket data to obtain the most accurate view of the exchange state. This endpoint provides an approximate indication of when the data from the following endpoints was last validated: GetBalance, GetOrder(s), GetFills, GetPositions"""
        _path = "/exchange/user_data_timestamp"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetUserDataTimestampResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class FcmClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_fcm_orders(
        self,
        subtrader_id: str,
        cursor: str | None = None,
        event_ticker: str | None = None,
        ticker: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
        status: Literal["resting", "canceled", "executed"] | None = None,
        limit: int | None = None,
    ) -> ResponseValue[GetOrdersResponse]:
        """Get FCM Orders

        Endpoint for FCM members to get orders filtered by subtrader ID.
        This endpoint requires FCM member access level and allows filtering orders by subtrader ID.
        """
        _path = "/fcm/orders"
        _params: dict[str, Any] = {
            "subtrader_id": subtrader_id,
            "cursor": cursor,
            "event_ticker": event_ticker,
            "ticker": ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
            "status": status,
            "limit": limit,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetOrdersResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_fcm_positions(
        self,
        subtrader_id: str,
        ticker: str | None = None,
        event_ticker: str | None = None,
        count_filter: str | None = None,
        settlement_status: Literal["all", "unsettled", "settled"] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> ResponseValue[GetPositionsResponse]:
        """Get FCM Positions

        Endpoint for FCM members to get market positions filtered by subtrader ID.
        This endpoint requires FCM member access level and allows filtering positions by subtrader ID.
        """
        _path = "/fcm/positions"
        _params: dict[str, Any] = {
            "subtrader_id": subtrader_id,
            "ticker": ticker,
            "event_ticker": event_ticker,
            "count_filter": count_filter,
            "settlement_status": settlement_status,
            "limit": limit,
            "cursor": cursor,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetPositionsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class IncentiveProgramsClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_incentive_programs(
        self,
        status: Literal["all", "active", "upcoming", "closed", "paid_out"]
        | None = None,
        type: Literal["all", "liquidity", "volume"] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> ResponseValue[GetIncentiveProgramsResponse]:
        """Get Incentives

        List incentives with optional filters. Incentives are rewards programs for trading activity on specific markets."""
        _path = "/incentive_programs"
        _params: dict[str, Any] = {
            "status": status,
            "type": type,
            "limit": limit,
            "cursor": cursor,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetIncentiveProgramsResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class LiveDataClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_live_data(
        self, type: str, milestone_id: str
    ) -> ResponseValue[GetLiveDataResponse]:
        """Get Live Data

        Get live data for a specific milestone"""
        _path = f"/live_data/{encode_path(type)}/milestone/{encode_path(milestone_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetLiveDataResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_live_datas(
        self, milestone_ids: list[str]
    ) -> ResponseValue[GetLiveDatasResponse]:
        """Get Multiple Live Data

        Get live data for multiple milestones"""
        _path = "/live_data/batch"
        _params: dict[str, Any] = {"milestone_ids": milestone_ids}
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetLiveDatasResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class MarketClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_market_candlesticks(
        self,
        series_ticker: str,
        ticker: str,
        start_ts: int,
        end_ts: int,
        period_interval: Literal[1, 60, 1440],
        include_latest_before_start: bool | None = None,
    ) -> ResponseValue[GetMarketCandlesticksResponse]:
        """Get Market Candlesticks

        Time period length of each candlestick in minutes. Valid values: 1 (1 minute), 60 (1 hour), 1440 (1 day)."""
        _path = f"/series/{encode_path(series_ticker)}/markets/{encode_path(ticker)}/candlesticks"
        _params: dict[str, Any] = {
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval,
            "include_latest_before_start": include_latest_before_start,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetMarketCandlesticksResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_trades(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        ticker: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
    ) -> ResponseValue[GetTradesResponse]:
        """Get Trades

        Endpoint for getting all trades for all markets.  A trade represents a completed transaction between two users on a specific market. Each trade includes the market ticker, price, quantity, and timestamp information.  This endpoint returns a paginated response. Use the 'limit' parameter to control page size (1-1000, defaults to 100). The response includes a 'cursor' field - pass this value in the 'cursor' parameter of your next request to get the next page. An empty cursor indicates no more pages are available."""
        _path = "/markets/trades"
        _params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "ticker": ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetTradesResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_trades_iter(
        self,
        limit: int | None = None,
        ticker: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
    ) -> Paginator[Trade]:
        return Paginator(
            fetch_page=lambda _token: self.get_trades(
                limit=limit, ticker=ticker, min_ts=min_ts, max_ts=max_ts, cursor=_token
            ),
            get_items=lambda page: list(page.trades),
            get_next_token=lambda page: page.cursor or None,
        )

    async def get_market_orderbook(
        self, ticker: str, depth: int | None = None
    ) -> ResponseValue[GetMarketOrderbookResponse]:
        """Get Market Orderbook

        Endpoint for getting the current order book for a specific market.  The order book shows all active bid orders for both yes and no sides of a binary market. It returns yes bids and no bids only (no asks are returned). This is because in binary markets, a bid for yes at price X is equivalent to an ask for no at price (100-X). For example, a yes bid at 7¢ is the same as a no ask at 93¢, with identical contract sizes.  Each side shows price levels with their corresponding quantities and order counts, organized from best to worst prices."""
        _path = f"/markets/{encode_path(ticker)}/orderbook"
        _params: dict[str, Any] = {"depth": depth}
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetMarketOrderbookResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_series(
        self, series_ticker: str, include_volume: bool | None = None
    ) -> ResponseValue[GetSeriesResponse]:
        """Get Series

        Endpoint for getting data about a specific series by its ticker.  A series represents a template for recurring events that follow the same format and rules (e.g., "Monthly Jobs Report", "Weekly Initial Jobless Claims", "Daily Weather in NYC"). Series define the structure, settlement sources, and metadata that will be applied to each recurring event instance within that series."""
        _path = f"/series/{encode_path(series_ticker)}"
        _params: dict[str, Any] = {"include_volume": include_volume}
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetSeriesResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_series_list(
        self,
        category: str | None = None,
        tags: str | None = None,
        include_product_metadata: bool | None = None,
        include_volume: bool | None = None,
    ) -> ResponseValue[GetSeriesListResponse]:
        """Get Series List

        Endpoint for getting data about multiple series with specified filters.  A series represents a template for recurring events that follow the same format and rules (e.g., "Monthly Jobs Report", "Weekly Initial Jobless Claims", "Daily Weather in NYC"). This endpoint allows you to browse and discover available series templates by category."""
        _path = "/series"
        _params: dict[str, Any] = {
            "category": category,
            "tags": tags,
            "include_product_metadata": include_product_metadata,
            "include_volume": include_volume,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetSeriesListResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_markets(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        event_ticker: str | None = None,
        series_ticker: str | None = None,
        min_created_ts: int | None = None,
        max_created_ts: int | None = None,
        max_close_ts: int | None = None,
        min_close_ts: int | None = None,
        min_settled_ts: int | None = None,
        max_settled_ts: int | None = None,
        status: Literal["unopened", "open", "paused", "closed", "settled"]
        | None = None,
        tickers: str | None = None,
        mve_filter: Literal["only", "exclude"] | None = None,
    ) -> ResponseValue[GetMarketsResponse]:
        """Get Markets

        Filter by market status. Possible values: `unopened`, `open`, `closed`, `settled`. Leave empty to return markets with any status.
         - Only one `status` filter may be supplied at a time.
         - Timestamp filters will be mutually exclusive from other timestamp filters and certain status filters.

         | Compatible Timestamp Filters | Additional Status Filters|
         |------------------------------|--------------------------|
         | min_created_ts, max_created_ts | `unopened`, `open`, *empty* |
         | min_close_ts, max_close_ts | `closed`, *empty* |
         | min_settled_ts, max_settled_ts | `settled`, *empty* |
        """
        _path = "/markets"
        _params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "event_ticker": event_ticker,
            "series_ticker": series_ticker,
            "min_created_ts": min_created_ts,
            "max_created_ts": max_created_ts,
            "max_close_ts": max_close_ts,
            "min_close_ts": min_close_ts,
            "min_settled_ts": min_settled_ts,
            "max_settled_ts": max_settled_ts,
            "status": status,
            "tickers": tickers,
            "mve_filter": mve_filter,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetMarketsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_market(self, ticker: str) -> ResponseValue[GetMarketResponse]:
        """Get Market

        Endpoint for getting data about a specific market by its ticker. A market represents a specific binary outcome within an event that users can trade on (e.g., "Will candidate X win?"). Markets have yes/no positions, current prices, volume, and settlement rules."""
        _path = f"/markets/{encode_path(ticker)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetMarketResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def batch_get_market_candlesticks(
        self,
        market_tickers: str,
        start_ts: int,
        end_ts: int,
        period_interval: int,
        include_latest_before_start: bool | None = None,
    ) -> ResponseValue[BatchGetMarketCandlesticksResponse]:
        """Batch Get Market Candlesticks

        Endpoint for retrieving candlestick data for multiple markets.

        - Accepts up to 100 market tickers per request
        - Returns up to 10,000 candlesticks total across all markets
        - Returns candlesticks grouped by market_id
        - Optionally includes a synthetic initial candlestick for price continuity (see `include_latest_before_start` parameter)
        """
        _path = "/markets/candlesticks"
        _params: dict[str, Any] = {
            "market_tickers": market_tickers,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "period_interval": period_interval,
            "include_latest_before_start": include_latest_before_start,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=BatchGetMarketCandlesticksResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class MilestoneClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_milestone(
        self, milestone_id: str
    ) -> ResponseValue[GetMilestoneResponse]:
        """Get Milestone

        Endpoint for getting data about a specific milestone by its ID."""
        _path = f"/milestones/{encode_path(milestone_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetMilestoneResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_milestones(
        self,
        limit: int,
        minimum_start_date: datetime.datetime | None = None,
        category: str | None = None,
        competition: str | None = None,
        source_id: str | None = None,
        type: str | None = None,
        related_event_ticker: str | None = None,
        cursor: str | None = None,
    ) -> ResponseValue[GetMilestonesResponse]:
        """Get Milestones

        Minimum start date to filter milestones. Format: RFC3339 timestamp"""
        _path = "/milestones"
        _params: dict[str, Any] = {
            "limit": limit,
            "minimum_start_date": minimum_start_date,
            "category": category,
            "competition": competition,
            "source_id": source_id,
            "type": type,
            "related_event_ticker": related_event_ticker,
            "cursor": cursor,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetMilestonesResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class MultivariateClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_multivariate_event_collection(
        self, collection_ticker: str
    ) -> ResponseValue[GetMultivariateEventCollectionResponse]:
        """Get Multivariate Event Collection

        Endpoint for getting data about a multivariate event collection by its ticker."""
        _path = f"/multivariate_event_collections/{encode_path(collection_ticker)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetMultivariateEventCollectionResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def create_market_in_multivariate_event_collection(
        self,
        collection_ticker: str,
        body: CreateMarketInMultivariateEventCollectionRequest,
    ) -> ResponseValue[CreateMarketInMultivariateEventCollectionResponse]:
        """Create Market In Multivariate Event Collection

        Endpoint for creating an individual market in a multivariate event collection. This endpoint must be hit at least once before trading or looking up a market."""
        _path = f"/multivariate_event_collections/{encode_path(collection_ticker)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=CreateMarketInMultivariateEventCollectionResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_multivariate_event_collections(
        self,
        status: Literal["unopened", "open", "closed"] | None = None,
        associated_event_ticker: str | None = None,
        series_ticker: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> ResponseValue[GetMultivariateEventCollectionsResponse]:
        """Get Multivariate Event Collections

        Endpoint for getting data about multivariate event collections."""
        _path = "/multivariate_event_collections"
        _params: dict[str, Any] = {
            "status": status,
            "associated_event_ticker": associated_event_ticker,
            "series_ticker": series_ticker,
            "limit": limit,
            "cursor": cursor,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetMultivariateEventCollectionsResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_multivariate_event_collection_lookup_history(
        self, collection_ticker: str, lookback_seconds: Literal[10, 60, 300, 3600]
    ) -> ResponseValue[GetMultivariateEventCollectionLookupHistoryResponse]:
        """Get Multivariate Event Collection Lookup History

        Endpoint for retrieving which markets in an event collection were recently looked up."""
        _path = (
            f"/multivariate_event_collections/{encode_path(collection_ticker)}/lookup"
        )
        _params: dict[str, Any] = {"lookback_seconds": lookback_seconds}
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetMultivariateEventCollectionLookupHistoryResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def lookup_tickers_for_market_in_multivariate_event_collection(
        self,
        collection_ticker: str,
        body: LookupTickersForMarketInMultivariateEventCollectionRequest,
    ) -> ResponseValue[LookupTickersForMarketInMultivariateEventCollectionResponse]:
        """Lookup Tickers For Market In Multivariate Event Collection

        Endpoint for looking up an individual market in a multivariate event collection. If CreateMarketInMultivariateEventCollection has never been hit with that variable combination before, this will return a 404."""
        _path = (
            f"/multivariate_event_collections/{encode_path(collection_ticker)}/lookup"
        )
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="PUT",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content,
            type=LookupTickersForMarketInMultivariateEventCollectionResponse,
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class OrderGroupsClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_order_groups(self) -> ResponseValue[GetOrderGroupsResponse]:
        """Get Order Groups

        Retrieves all order groups for the authenticated user."""
        _path = "/portfolio/order_groups"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetOrderGroupsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def create_order_group(
        self, body: CreateOrderGroupRequest
    ) -> ResponseValue[CreateOrderGroupResponse]:
        """Create Order Group

        Creates a new order group with a contracts limit. When the limit is hit, all orders in the group are cancelled and no new orders can be placed until reset."""
        _path = "/portfolio/order_groups/create"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=CreateOrderGroupResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_order_group(
        self, order_group_id: str
    ) -> ResponseValue[GetOrderGroupResponse]:
        """Get Order Group

        Retrieves details for a single order group including all order IDs and auto-cancel status."""
        _path = f"/portfolio/order_groups/{encode_path(order_group_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetOrderGroupResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def delete_order_group(
        self, order_group_id: str
    ) -> ResponseValue[EmptyResponse]:
        """Delete Order Group

        Deletes an order group and cancels all orders within it. This permanently removes the group."""
        _path = f"/portfolio/order_groups/{encode_path(order_group_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="DELETE",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=EmptyResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def reset_order_group(
        self, order_group_id: str, body: EmptyResponse | None = None
    ) -> ResponseValue[EmptyResponse]:
        """Reset Order Group

        Resets the order group's matched contracts counter to zero, allowing new orders to be placed again after the limit was hit."""
        _path = f"/portfolio/order_groups/{encode_path(order_group_id)}/reset"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="PUT",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body) if body is not None else None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=EmptyResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class OrdersClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_orders(
        self,
        ticker: str | None = None,
        event_ticker: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
        status: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        subaccount: int | None = None,
    ) -> ResponseValue[GetOrdersResponse]:
        """Get Orders

        Restricts the response to orders that have a certain status: resting, canceled, or executed."""
        _path = "/portfolio/orders"
        _params: dict[str, Any] = {
            "ticker": ticker,
            "event_ticker": event_ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
            "status": status,
            "limit": limit,
            "cursor": cursor,
            "subaccount": subaccount,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetOrdersResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_orders_iter(
        self,
        ticker: str | None = None,
        event_ticker: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
        status: str | None = None,
        limit: int | None = None,
        subaccount: int | None = None,
    ) -> Paginator[Order]:
        return Paginator(
            fetch_page=lambda _token: self.get_orders(
                ticker=ticker,
                event_ticker=event_ticker,
                min_ts=min_ts,
                max_ts=max_ts,
                status=status,
                limit=limit,
                subaccount=subaccount,
                cursor=_token,
            ),
            get_items=lambda page: list(page.orders),
            get_next_token=lambda page: page.cursor or None,
        )

    async def create_order(
        self, body: CreateOrderRequest
    ) -> ResponseValue[CreateOrderResponse]:
        """Create Order

        Endpoint for submitting orders in a market. Each user is limited to 200 000 open orders at a time."""
        _path = "/portfolio/orders"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=CreateOrderResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_order(self, order_id: str) -> ResponseValue[GetOrderResponse]:
        """Get Order

        Endpoint for getting a single order."""
        _path = f"/portfolio/orders/{encode_path(order_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetOrderResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def cancel_order(self, order_id: str) -> ResponseValue[CancelOrderResponse]:
        """Cancel Order

        Endpoint for canceling orders. The value for the orderId should match the id field of the order you want to decrease. Commonly, DELETE-type endpoints return 204 status with no body content on success. But we can't completely delete the order, as it may be partially filled already. Instead, the DeleteOrder endpoint reduce the order completely, essentially zeroing the remaining resting contracts on it. The zeroed order is returned on the response payload as a form of validation for the client."""
        _path = f"/portfolio/orders/{encode_path(order_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="DELETE",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=CancelOrderResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def batch_create_orders(
        self, body: BatchCreateOrdersRequest
    ) -> ResponseValue[BatchCreateOrdersResponse]:
        """Batch Create Orders

        Endpoint for submitting a batch of orders. Each order in the batch is counted against the total rate limit for order operations. Consequently, the size of the batch is capped by the current per-second rate-limit configuration applicable to the user. At the moment of writing, the limit is 20 orders per batch."""
        _path = "/portfolio/orders/batched"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=BatchCreateOrdersResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def batch_cancel_orders(
        self, body: BatchCancelOrdersRequest
    ) -> ResponseValue[BatchCancelOrdersResponse]:
        """Batch Cancel Orders

        Endpoint for cancelling up to 20 orders at once."""
        _path = "/portfolio/orders/batched"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="DELETE",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=BatchCancelOrdersResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def amend_order(
        self, order_id: str, body: AmendOrderRequest
    ) -> ResponseValue[AmendOrderResponse]:
        """Amend Order

        Endpoint for amending the max number of fillable contracts and/or price in an existing order. Max fillable contracts is `remaining_count` + `fill_count`."""
        _path = f"/portfolio/orders/{encode_path(order_id)}/amend"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=AmendOrderResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def decrease_order(
        self, order_id: str, body: DecreaseOrderRequest
    ) -> ResponseValue[DecreaseOrderResponse]:
        """Decrease Order

        Endpoint for decreasing the number of contracts in an existing order. This is the only kind of edit available on order quantity. Cancelling an order is equivalent to decreasing an order amount to zero."""
        _path = f"/portfolio/orders/{encode_path(order_id)}/decrease"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=DecreaseOrderResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_order_queue_positions(
        self, market_tickers: str | None = None, event_ticker: str | None = None
    ) -> ResponseValue[GetOrderQueuePositionsResponse]:
        """Get Queue Positions for Orders

        Endpoint for getting queue positions for all resting orders. Queue position represents the number of contracts that need to be matched before an order receives a partial or full match, determined using price-time priority."""
        _path = "/portfolio/orders/queue_positions"
        _params: dict[str, Any] = {
            "market_tickers": market_tickers,
            "event_ticker": event_ticker,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetOrderQueuePositionsResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_order_queue_position(
        self, order_id: str
    ) -> ResponseValue[GetOrderQueuePositionResponse]:
        """Get Order Queue Position

        Endpoint for getting an order's queue position in the order book. This represents the amount of orders that need to be matched before this order receives a partial or full match. Queue position is determined using a price-time priority."""
        _path = f"/portfolio/orders/{encode_path(order_id)}/queue_position"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetOrderQueuePositionResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class PortfolioClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_balance(self) -> ResponseValue[GetBalanceResponse]:
        """Get Balance

        Endpoint for getting the balance and portfolio value of a member. Both values are returned in cents."""
        _path = "/portfolio/balance"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetBalanceResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def create_subaccount(self) -> ResponseValue[CreateSubaccountResponse]:
        """Create Subaccount

        Creates a new subaccount for the authenticated user. Subaccounts are numbered sequentially starting from 1. Maximum 32 subaccounts per user."""
        _path = "/portfolio/subaccounts"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=CreateSubaccountResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def apply_subaccount_transfer(
        self, body: ApplySubaccountTransferRequest
    ) -> ResponseValue[ApplySubaccountTransferResponse]:
        """Transfer Between Subaccounts

        Transfers funds between the authenticated user's subaccounts. Use 0 for the primary account, or 1-32 for numbered subaccounts."""
        _path = "/portfolio/subaccounts/transfer"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="POST",
            url=_url,
            headers={"Content-Type": "application/json"},
            params={},
            content=msgspec.json.encode(body),
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=ApplySubaccountTransferResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_subaccount_balances(
        self,
    ) -> ResponseValue[GetSubaccountBalancesResponse]:
        """Get All Subaccount Balances

        Gets balances for all subaccounts including the primary account."""
        _path = "/portfolio/subaccounts/balances"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetSubaccountBalancesResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_subaccount_transfers(
        self, limit: int | None = None, cursor: str | None = None
    ) -> ResponseValue[GetSubaccountTransfersResponse]:
        """Get Subaccount Transfers

        Gets a paginated list of all transfers between subaccounts for the authenticated user."""
        _path = "/portfolio/subaccounts/transfers"
        _params: dict[str, Any] = {"limit": limit, "cursor": cursor}
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetSubaccountTransfersResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_positions(
        self,
        cursor: str | None = None,
        limit: int | None = None,
        count_filter: str | None = None,
        ticker: str | None = None,
        event_ticker: str | None = None,
        subaccount: int | None = None,
    ) -> ResponseValue[GetPositionsResponse]:
        """Get Positions

        Restricts the positions to those with any of following fields with non-zero values, as a comma separated list. The following values are accepted: position, total_traded"""
        _path = "/portfolio/positions"
        _params: dict[str, Any] = {
            "cursor": cursor,
            "limit": limit,
            "count_filter": count_filter,
            "ticker": ticker,
            "event_ticker": event_ticker,
            "subaccount": subaccount,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetPositionsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_settlements(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        ticker: str | None = None,
        event_ticker: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
    ) -> ResponseValue[GetSettlementsResponse]:
        """Get Settlements

        Endpoint for getting the member's settlements historical track."""
        _path = "/portfolio/settlements"
        _params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "ticker": ticker,
            "event_ticker": event_ticker,
            "min_ts": min_ts,
            "max_ts": max_ts,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetSettlementsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_portfolio_resting_order_total_value(
        self,
    ) -> ResponseValue[GetPortfolioRestingOrderTotalValueResponse]:
        """Get Total Resting Order Value

        Endpoint for getting the total value, in cents, of resting orders. This endpoint is only intended for use by FCM members (rare). Note: If you're uncertain about this endpoint, it likely does not apply to you."""
        _path = "/portfolio/summary/total_resting_order_value"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetPortfolioRestingOrderTotalValueResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_fills(
        self,
        ticker: str | None = None,
        order_id: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        subaccount: int | None = None,
    ) -> ResponseValue[GetFillsResponse]:
        """Get Fills

        Endpoint for getting all fills for the member. A fill is when a trade you have is matched."""
        _path = "/portfolio/fills"
        _params: dict[str, Any] = {
            "ticker": ticker,
            "order_id": order_id,
            "min_ts": min_ts,
            "max_ts": max_ts,
            "limit": limit,
            "cursor": cursor,
            "subaccount": subaccount,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(_response.content, type=GetFillsResponse)
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    def get_fills_iter(
        self,
        ticker: str | None = None,
        order_id: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
        limit: int | None = None,
        subaccount: int | None = None,
    ) -> Paginator[Fill]:
        return Paginator(
            fetch_page=lambda _token: self.get_fills(
                ticker=ticker,
                order_id=order_id,
                min_ts=min_ts,
                max_ts=max_ts,
                limit=limit,
                subaccount=subaccount,
                cursor=_token,
            ),
            get_items=lambda page: list(page.fills),
            get_next_token=lambda page: page.cursor or None,
        )


@final
class SearchClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_tags_for_series_categories(
        self,
    ) -> ResponseValue[GetTagsForSeriesCategoriesResponse]:
        """Get Tags for Series Categories

        Retrieve tags organized by series categories.

        This endpoint returns a mapping of series categories to their associated tags, which can be used for filtering and search functionality.
        """
        _path = "/search/tags_by_categories"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetTagsForSeriesCategoriesResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_filters_for_sports(self) -> ResponseValue[GetFiltersBySportsResponse]:
        """Get Filters for Sports

        Retrieve available filters organized by sport.

        This endpoint returns filtering options available for each sport, including scopes and competitions. It also provides an ordered list of sports for display purposes.
        """
        _path = "/search/filters_by_sport"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetFiltersBySportsResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class StructuredTargetsClient:
    def __init__(self, client: httpx.AsyncClient, base_url: str) -> None:
        self._base_url = base_url
        self._client = client

    async def get_structured_targets(
        self,
        type: str | None = None,
        competition: str | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
    ) -> ResponseValue[GetStructuredTargetsResponse]:
        """Get Structured Targets

        Page size (min: 1, max: 2000)"""
        _path = "/structured_targets"
        _params: dict[str, Any] = {
            "type": type,
            "competition": competition,
            "page_size": page_size,
            "cursor": cursor,
        }
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={k: v for k, v in _params.items() if v is not None},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetStructuredTargetsResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )

    async def get_structured_target(
        self, structured_target_id: str
    ) -> ResponseValue[GetStructuredTargetResponse]:
        """Get Structured Target

        Endpoint for getting data about a specific structured target by its ID."""
        _path = f"/structured_targets/{encode_path(structured_target_id)}"
        _url = self._base_url.rstrip("/") + _path
        _response = await self._client.request(
            method="GET",
            url=_url,
            headers={},
            params={},
            content=None,
        )
        _headers_dict = dict(_response.headers)
        if _response.status_code >= 400:
            raise APIError(
                status_code=_response.status_code,
                body=_response.content,
                headers=_headers_dict,
            )
        _result = msgspec.json.decode(
            _response.content, type=GetStructuredTargetResponse
        )
        return ResponseValue(
            value=_result, status_code=_response.status_code, headers=_headers_dict
        )


@final
class Client:
    api_keys: "ApiKeysClient"
    communications: "CommunicationsClient"
    events: "EventsClient"
    exchange: "ExchangeClient"
    fcm: "FcmClient"
    incentive_programs: "IncentiveProgramsClient"
    live_data: "LiveDataClient"
    market: "MarketClient"
    milestone: "MilestoneClient"
    multivariate: "MultivariateClient"
    order_groups: "OrderGroupsClient"
    orders: "OrdersClient"
    portfolio: "PortfolioClient"
    search: "SearchClient"
    structured_targets: "StructuredTargetsClient"

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)
        self.api_keys = ApiKeysClient(client=self._client, base_url=self._base_url)
        self.communications = CommunicationsClient(
            client=self._client, base_url=self._base_url
        )
        self.events = EventsClient(client=self._client, base_url=self._base_url)
        self.exchange = ExchangeClient(client=self._client, base_url=self._base_url)
        self.fcm = FcmClient(client=self._client, base_url=self._base_url)
        self.incentive_programs = IncentiveProgramsClient(
            client=self._client, base_url=self._base_url
        )
        self.live_data = LiveDataClient(client=self._client, base_url=self._base_url)
        self.market = MarketClient(client=self._client, base_url=self._base_url)
        self.milestone = MilestoneClient(client=self._client, base_url=self._base_url)
        self.multivariate = MultivariateClient(
            client=self._client, base_url=self._base_url
        )
        self.order_groups = OrderGroupsClient(
            client=self._client, base_url=self._base_url
        )
        self.orders = OrdersClient(client=self._client, base_url=self._base_url)
        self.portfolio = PortfolioClient(client=self._client, base_url=self._base_url)
        self.search = SearchClient(client=self._client, base_url=self._base_url)
        self.structured_targets = StructuredTargetsClient(
            client=self._client, base_url=self._base_url
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.close()
