import string
import secrets
import logging
import asyncio

from httpx import AsyncClient, HTTPError, HTTPStatusError
from .models import Receipt
from .errors import TaxError, ApiResponseError, AuthError


class Client:
    def __init__(
        self,
        *,
        taxpayer_id: str,
        password: str,
        base_url: str = "https://lknpd.nalog.ru/api/v1",
        timeout: float = 5.0,
        verify_tls: bool = True,
    ):
        self._taxpayer_id = taxpayer_id
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._token = None
        self._refresh_token = None
        self._device_id = self._generate_device_id()
        self._headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.2 Safari/605.1.15",
        }
        self._client = AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers=self._headers,
            verify=verify_tls,
        )
        self._logging = logging.getLogger(__name__)
        self._auth_lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()

    async def _authenticate(self) -> None:
        payload = {
            "username": self._taxpayer_id,
            "password": self._password,
            "deviceInfo": {
                "sourceDeviceId": self._device_id,
                "sourceType":"WEB",
                "appVersion":"1.0.0",
                "metaDetails":{
                    "userAgent": self._headers["User-Agent"]
                }
            }
        }
        headers = {
            **self._headers,
            "Origin": "https://lknpd.nalog.ru",
            "Referer": f"{self._base_url}/auth/login",
        }
        
        try:
            response = await self._client.post(
                url="/auth/lkfl", 
                json=payload,
                headers=headers
            )
            response.raise_for_status()
        except HTTPStatusError as e:
            raise AuthError(f"auth failed: HTTP {e.response.status_code}") from e
        except HTTPError as e:
            raise AuthError("auth failed: network error") from e
        
        try:
            data = response.json()
        except ValueError as e:
            raise ApiResponseError("auth failed: invalid JSON") from e

        token = data.get("token")
        
        if not token:
            raise ApiResponseError("auth failed: 'token' отсутствует в ответе")

        self._token = token
        self._refresh_token = data.get("refreshToken", None)
    
    async def _check_auth(self) -> None:
        if self._token:
            return

        async with self._auth_lock:
            if self._token:
                return
            await self._authenticate()
            
        if not self._token:
            raise AuthError("auth failed: token was not set")
    
    def _generate_device_id(self, prefix: str = "i_") -> str:
        chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
        remaining_length = 21 - len(prefix)

        if remaining_length < 0:
            raise ValueError("Длина prefix не может превышать 21 символ")

        random_part = ''.join(secrets.choice(chars) for _ in range(remaining_length))
        return prefix + random_part

    def receipt_to_dict(self, receipt: Receipt) -> dict:
        return {
            "operationTime": receipt.operation_time,
            "requestTime": receipt.request_time,
            "services": [
                {
                    "name": s.name,
                    "amount": s.amount,
                    "quantity": s.quantity,
                }
                for s in receipt.services
            ],
            "totalAmount": receipt.total_amount,
            "client": {
                "contactPhone": receipt.client.contact_phone,
                "displayName": receipt.client.display_name,
                "inn": receipt.client.inn,
                "incomeType": receipt.client.income_type,
            },
            "paymentType": receipt.payment_type,
            "ignoreMaxTotalIncomeRestriction": receipt.ignore_max_total_income_restriction,
        }
    
    async def send_receipt(self, receipt: Receipt) -> str:
        await self._check_auth()

        headers = {
            **self._headers,
            "Origin": "https://lknpd.nalog.ru",
            "Referer": "https://lknpd.nalog.ru/sales/create",
            "Authorization": f"Bearer {self._token}",
        }
        
        payload = self.receipt_to_dict(receipt)
        
        try:
            response = await self._client.post(
                url="/income",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                self._token = None
                raise AuthError(f"send_receipt failed: HTTP {e.response.status_code}") from e
            raise TaxError(f"send_receipt failed: HTTP {e.response.status_code}") from e
        except HTTPError as e:
            raise TaxError("send_receipt failed: network error") from e
        
        try:
            data = response.json()
        except ValueError as e:
            raise ApiResponseError("send_receipt failed: invalid JSON") from e
        
        approved_uuid = data.get("approvedReceiptUuid")
        
        if not approved_uuid:
            raise ApiResponseError("send_receipt: отсутствует 'approvedReceiptUuid' в ответе")

        return str(approved_uuid)