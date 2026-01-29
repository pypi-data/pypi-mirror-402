# payments/main.py
import hashlib
import logging
from typing import Literal
import requests

from .utils import _try_pydantic_parse
from .exceptions import PayHereError
from .response import (
    PaymentRetrievalResponse,
    PayHereTokenResponse,
    PayHereTokenErrorResponse,
    PayHereErrorResponse,
    PayHereRefundResponse,   
)


__logger__ = logging.getLogger("payhere")

PAYHERE_VERSION = "v1"


class PayHere:
    """
    Main PayHere SDK client.

    This class handles:
    - OAuth token generation
    - Payment retrieval
    - Refund processing
    - API authentication
    - Request handling

    Example:
        client = PayHere(
            merchant_id="123",
            merchant_secret="abc",
            app_id="app123",
            app_secret="secret",
            sandbox_enabled=True
        )
    """

    def __init__(self, merchant_id:str="", merchant_secret:str="", app_id:str="", app_secret:str="", sandbox_enabled:bool=True, request_timeout:int=20) -> None:
        self.merchant_id = merchant_id
        self.merchant_secret = merchant_secret
        self.app_id = app_id
        self.app_secret = app_secret
        self._authorization_code: str = ""
        self._access_token: str = ""
        self._access_token_expires_at: int = 0
        self.sandbox_enabled = sandbox_enabled
        self.request_timeout = request_timeout
        self.session = requests.Session()

    def _base_url(self)->str:
        return "https://sandbox.payhere.lk" if self.sandbox_enabled else "https://www.payhere.lk"

    @property
    def gen_base64_encode(self)->str:
        self.__need_app_credentials__()

        if self._authorization_code:
            return self._authorization_code

        import base64

        auth_str = f"{self.app_id}:{self.app_secret}"
        b64_bytes = base64.b64encode(auth_str.encode("utf-8"))
        self._authorization_code = b64_bytes.decode("utf-8")
        __logger__.info("Generated Base64 encoded authorization code for PayHere.")
        return self._authorization_code
        
    @property
    def get_access_token(self)->str:
        url = f"{self._base_url()}/merchant/{PAYHERE_VERSION}/oauth/token"

        self.__need_app_credentials__()

        if self._access_token:
            import time
            if time.time() > self._access_token_expires_at:
                self._access_token = ""
                return self.get_access_token
            return self._access_token

        headers = {
            "Authorization": f"Basic {self.gen_base64_encode}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
        }

        try:
            response = self.session.post(url, headers=headers, data=data, timeout=self.request_timeout)

            if response.status_code == 200:
                data = response.json()
                resp_json = _try_pydantic_parse(PayHereTokenResponse, data)
                self._access_token = resp_json.access_token
                import time
                self._access_token_expires_at = resp_json.expires_in + int(time.time())
                __logger__.info("Successfully retrieved PayHere access token.")
                return self._access_token
            else:
                resp_json = _try_pydantic_parse(PayHereTokenErrorResponse, response.json())
                __logger__.error(f"Error retrieving access token: {resp_json.error_description}")
                raise PayHereError(f"Error retrieving access token: {resp_json.error_description}")
            
        except requests.RequestException as e:
            __logger__.error(f"Request exception while retrieving access token: {str(e)}")
            raise PayHereError(f"Request exception while retrieving access token: {str(e)}")

    def __need_merchant_credentials__(self):
        if not self.merchant_id or not self.merchant_secret:
            __logger__.error("PAYHERE_MERCHANT_ID and PAYHERE_SECRET must be set in settings.")
            raise PayHereError("PAYHERE_MERCHANT_ID and PAYHERE_SECRET must be set in settings.")
        
    def __need_app_credentials__(self):
        if not self.app_id or not self.app_secret:
            __logger__.error("PAYHERE_APP_ID and PAYHERE_APP_SECRET must be set in settings.")
            raise PayHereError("PAYHERE_APP_ID and PAYHERE_APP_SECRET must be set in settings.")
        
    def get_payment_details(self, order_id:str)->PaymentRetrievalResponse:
        """
        Retrieve payment details from PayHere using the order ID.

        Args:
            order_id (str): Your internal order ID used during payment.

        Returns:
            PaymentRetrievalResponse: Payment information including status, amount, and customer data.

        Raises:
            PayHereError: If the API request fails or PayHere returns an error.
        """
        self.__need_merchant_credentials__()

        url = f"{self._base_url()}/merchant/{PAYHERE_VERSION}/payment/search?order_id={order_id}"

        headers = {
            "Authorization": f"Bearer {self.get_access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = self.session.get(url, headers=headers, timeout=self.request_timeout)

            if response.status_code == 200:
                data = response.json()
                resp_json = _try_pydantic_parse(PaymentRetrievalResponse, data)
                __logger__.info("Successfully retrieved payment details from PayHere.")
                return resp_json
            else:
                resp_json = response.json()
                
                if "status" in resp_json:
                    res = _try_pydantic_parse(PayHereErrorResponse, resp_json)
                    __logger__.error(f"Error retrieving payment details: {res.msg}")
                    raise PayHereError(f"Error retrieving payment details: {res.msg}")
                
                elif "error" in resp_json:
                    res = _try_pydantic_parse(PayHereTokenErrorResponse, resp_json)

                    if "expired" in res.error_description:
                        self._access_token = ""
                        return self.retrieve_payment_details(order_id)
                    
                    __logger__.error(f"Error retrieving payment details: {res.error_description}")
                    raise PayHereError(f"Error retrieving payment details: {res.error_description}")
                
        except requests.RequestException as e:
            __logger__.error(f"Request exception while retrieving payment details: {str(e)}")
            raise PayHereError(f"Request exception while retrieving payment details: {str(e)}")
    
    def refund_payment(self, payment_id:int, reason:str, amount:float=0, refund_type:Literal["full", "partial"]="full")->PayHereRefundResponse:
        """
        Process a refund for a PayHere payment.

        Args:
            payment_id (int): PayHere payment ID.
            reason (str): Reason for the refund.
            amount (float, optional): Amount to refund (only for partial refunds).
            refund_type (str): "full" or "partial".

        Returns:
            PayHereRefundResponse: Refund confirmation response.

        Raises:
            PayHereError: If the refund fails or input is invalid.
        """
        self.__need_merchant_credentials__()

        url = f"{self._base_url()}/merchant/{PAYHERE_VERSION}/payment/refund"
        headers = {
            "Authorization": f"Bearer {self.get_access_token}",
            "Content-Type": "application/json",
        }
        data = {
            "payment_id": payment_id,
            "reason": reason,
        }

        if refund_type == "partial":
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                __logger__.error("Invalid amount for partial refund. Amount must be a number.")
                raise PayHereError("Invalid amount for partial refund. Amount must be a number.")
            
            if amount <= 0:
                __logger__.error("Amount for partial refund must be greater than zero.")
                raise PayHereError("Amount for partial refund must be greater than zero.")
            
            data["amount"] = f"{amount:.2f}"
        try:
            response = self.session.post(url, headers=headers, json=data, timeout=self.request_timeout)

            if response.status_code == 200:
                data = response.json()
                resp_json = _try_pydantic_parse(PayHereRefundResponse, data)
                __logger__.info(f"Successfully processed refund for payment ID {payment_id}.")
                return resp_json
            
            else:
                resp_json = response.json()

                if "status" in resp_json:
                    res = _try_pydantic_parse(PayHereErrorResponse, resp_json)
                    __logger__.error(f"Error processing refund: {res.msg}")
                    raise PayHereError(f"Error processing refund: {res.msg}")
                
                elif "error" in resp_json:
                    res = _try_pydantic_parse(PayHereTokenErrorResponse, resp_json)

                    if "expired" in res.error_description:
                        self._access_token = ""
                        return self.refund_payment(payment_id, reason, amount, refund_type)
                    
                    __logger__.error(f"Error processing refund: {res.error_description}")
                    raise PayHereError(f"Error processing refund: {res.error_description}")
                
        except requests.RequestException as e:
            __logger__.error(f"Request exception while processing refund: {str(e)}")
            raise PayHereError(f"Request exception while processing refund: {str(e)}")

    def generate_payment_hash(self, order_id: str, amount: str, currency:Literal["LKR", "USD", "EUR"]="LKR") -> str:
        return generate_payment_hash(order_id, amount, self.merchant_id, self.merchant_secret, currency)

    def verify_payment_signature(self, data:dict) -> bool:
        return verify_payment_signature(data, self.merchant_id, self.merchant_secret)


def generate_payment_hash(order_id: str, amount: str, merchant_id:str, merchant_secret:str, currency:Literal["LKR", "USD", "EUR"]="LKR") -> str:
    """
    Generate the PayHere payment hash required for frontend checkout.

    Args:
        order_id (str): Order ID.
        amount (str): Payment amount.
        merchant_id (str): PayHere merchant ID.
        merchant_secret (str): PayHere merchant secret.
        currency (str): Currency code (default: LKR).

    Returns:
        str: MD5 hash string for PayHere payment request.
    """
    if not all([merchant_id, merchant_secret]):
        __logger__.error("PAYHERE_MERCHANT_ID and PAYHERE_SECRET must be set in settings.")
        raise PayHereError("PAYHERE_MERCHANT_ID and PAYHERE_SECRET must be set in settings.")

    hashed_secret = hashlib.md5(merchant_secret.encode("utf-8")).hexdigest().upper()

    formatted_amount = f"{float(amount):.2f}"

    hash_string = f"{merchant_id}{order_id}{formatted_amount}{currency}{hashed_secret}"

    payment_hash = hashlib.md5(hash_string.encode("utf-8")).hexdigest().upper()

    return payment_hash


def verify_payment_signature(data:dict, merchant_id:str, merchant_secret:str) -> bool:
    """
    Verify PayHere webhook signature.

    Args:
        data (dict): Webhook payload from PayHere.
        merchant_id (str): Your PayHere merchant ID.
        merchant_secret (str): Your PayHere merchant secret.

    Returns:
        bool: True if signature is valid, False otherwise.
    """
    required_keys = ["order_id", "payhere_amount", "status_code", "md5sig", "payhere_currency"]

    if not all(key in data for key in required_keys):
        __logger__.error("Missing required keys in data for signature verification.")
        return False
    
    md5sig = str(data.get("md5sig", ""))
    order_id = str(data.get("order_id", ""))
    status_code = str(data.get("status_code", ""))
    payhere_amount = data.get("payhere_amount")
    payhere_currency = str(data.get("payhere_currency", ""))

    if not all([merchant_id, merchant_secret]):
        __logger__.error("PAYHERE_MERCHANT_ID and PAYHERE_SECRET must be set in settings.")
        raise PayHereError("PAYHERE_MERCHANT_ID and PAYHERE_SECRET must be set in settings.")

    hashed_secret = hashlib.md5(merchant_secret.encode("utf-8")).hexdigest().upper()

    try:
        formatted_amount = f"{float(payhere_amount):.2f}"  # format 1250.00
    except (ValueError, TypeError):
        __logger__.error("Invalid payhere_amount format for signature verification.")
        return False

    hash_string = f"{merchant_id}{order_id}{formatted_amount}{payhere_currency}{status_code}{hashed_secret}"

    payment_hash = hashlib.md5(hash_string.encode("utf-8")).hexdigest().upper()

    return payment_hash == md5sig



__all__ = [
    "PayHere",
    "generate_payment_hash",
    "verify_payment_signature",
]