# payhere-python/response.py
from typing import Literal
from pydantic import BaseModel, Field


class BaseConfigModel(BaseModel):
    class Config:
        extra = "ignore"
        populate_by_name = True


class PayHereTokenResponse(BaseConfigModel):
    access_token: str
    token_type: str
    expires_in: int


class PayHereResponse(BaseConfigModel):
    status: int
    msg: str
    data: str | None


class PayHereRefundResponse(PayHereResponse):
    data: int | None


class PayHereErrorResponse(PayHereResponse):
    status: int
    msg: str
    data: None


class PayHereTokenErrorResponse(BaseConfigModel):
    error: str
    error_description: str


class PayHereCustomerDeliveryDetails(BaseConfigModel):
    address: str | None
    city: str | None
    country: str | None


class PayHereCustomer(BaseConfigModel):
    first_name: str | None = Field(alias="fist_name")
    last_name: str | None
    email: str | None
    phone: str | None
    delivery_details: PayHereCustomerDeliveryDetails | None


class PayHereAmountDetail(BaseConfigModel):
    currency: Literal["LKR", "USD", "EUR"]
    gross: float
    fee: float
    net: float
    exchange_rate: float
    exchange_from: Literal["LKR", "USD", "EUR"]
    exchange_to: Literal["LKR", "USD", "EUR"]


class PayHerePaymentMethod(BaseConfigModel):
    method: Literal["VISA", "MASTER", "AMEX", "EZCASH", "MCASH", "GENIE", "VISHWA", "PAYAPP", "HNB", "FRIMI"]
    card_customer_name: str | None
    card_no: str | None


class PaymentRequestData(BaseConfigModel):
    custom1: str | None
    custom2: str | None


class PaymentRetrievalItemData(BaseConfigModel):
    name: str
    quantity: int
    currency: Literal["LKR", "USD", "EUR"]
    unit_price: float
    total_price: float


class PaymentRetrievalData(BaseConfigModel):
    payment_id: int
    order_id: str
    date: str
    description: str
    status: Literal["RECEIVED", "REFUND REQUESTED", "REFUND PROCESSING", "REFUNDED", "CHARGEBACKED"]
    currency: Literal["LKR", "USD", "EUR"]
    amount: float
    customer: PayHereCustomer | None
    amount_detail: PayHereAmountDetail | None
    payment_method: PayHerePaymentMethod | None
    items: list[PaymentRetrievalItemData] | None
    request: PaymentRequestData | None


class PaymentRetrievalResponse(PayHereResponse):
    data: list[PaymentRetrievalData] | None


__all__ = [
    "PayHereTokenResponse",
    "PayHereResponse",
    "PayHereRefundResponse",
    "PayHereErrorResponse",
    "PayHereTokenErrorResponse",
    "PaymentRetrievalResponse",
]


# data getting from retrieval payment details
{
    "status": 1,
    "msg": "Payments with order_id:f0bc4487-4805-480e-b561-7839abb83e9b",
    "data": [
        {
            "payment_id": 320032557392,
            "order_id": "f0bc4487-4805-480e-b561-7839abb83e9b",
            "date": "2026-01-14 17:13:07",
            "description": "Chess for Intermidiet Level",
            "status": "RECEIVED",
            "currency": "LKR",
            "amount": 1000.0,
            "customer": {
                "fist_name": "imalsha",
                "last_name": "gamage",
                "email": "imalsha.gamage2005@gmail.com",
                "phone": "0760661605",
                "delivery_details": {
                    "address": "NO.70A, Saragama, Kurunegala",
                    "city": "Kurunegala",
                    "country": "Sri Lanka"
                }
            },
            "amount_detail": {
                "currency": "LKR",
                "gross": 1000.0,
                "fee": 33.0,
                "net": 967.0,
                "exchange_rate": 1.0,
                "exchange_from": "LKR",
                "exchange_to": "LKR"
            },
            "payment_method": {
                "method": "VISA",
                "card_customer_name": "kavi harshitha",
                "card_no": "************1292"
            },
            "items": [
                {
                    "name": "Chess for Intermidiet Level",
                    "quantity": 1,
                    "currency": "LKR",
                    "unit_price": 1000.0,
                    "total_price": 1000.0
                }
            ],
            "request": {
                "custom1": None,
                "custom2": None
            }
        },
        {
            "payment_id": 320032557390,
            "order_id": "f0bc4487-4805-480e-b561-7839abb83e9b",
            "date": "2026-01-14 17:11:01",
            "description": "Chess for Intermidiet Level",
            "status": "RECEIVED",
            "currency": "LKR",
            "amount": 1000.0,
            "customer": {
                "fist_name": "imalsha",
                "last_name": "gamage",
                "email": "imalsha.gamage2005@gmail.com",
                "phone": "0760661605",
                "delivery_details": {
                    "address": "NO.70A, Saragama, Kurunegala",
                    "city": "Kurunegala",
                    "country": "Sri Lanka"
                }
            },
            "amount_detail": {
                "currency": "LKR",
                "gross": 1000.0,
                "fee": 33.0,
                "net": 967.0,
                "exchange_rate": 1.0,
                "exchange_from": "LKR",
                "exchange_to": "LKR"
            },
            "payment_method": {
                "method": "VISA",
                "card_customer_name": "harshitha",
                "card_no": "************1292"
            },
            "items": [
                {
                    "name": "Chess for Intermidiet Level",
                    "quantity": 1,
                    "currency": "LKR",
                    "unit_price": 1000.0,
                    "total_price": 1000.0
                }
            ],
            "request": {
                "custom1": None,
                "custom2": None
            }
        },
        {
            "payment_id": 320032557388,
            "order_id": "f0bc4487-4805-480e-b561-7839abb83e9b",
            "date": "2026-01-14 17:09:50",
            "description": "Chess for Intermidiet Level",
            "status": "RECEIVED",
            "currency": "LKR",
            "amount": 1000.0,
            "customer": {
                "fist_name": "imalsha",
                "last_name": "gamage",
                "email": "imalsha.gamage2005@gmail.com",
                "phone": "0760661605",
                "delivery_details": {
                    "address": "NO.70A, Saragama, Kurunegala",
                    "city": "Kurunegala",
                    "country": "Sri Lanka"
                }
            },
            "amount_detail": {
                "currency": "LKR",
                "gross": 1000.0,
                "fee": 33.0,
                "net": 967.0,
                "exchange_rate": 1.0,
                "exchange_from": "LKR",
                "exchange_to": "LKR"
            },
            "payment_method": {
                "method": "VISA",
                "card_customer_name": "harshitha",
                "card_no": "************1292"
            },
            "items": [
                {
                    "name": "Chess for Intermidiet Level",
                    "quantity": 1,
                    "currency": "LKR",
                    "unit_price": 1000.0,
                    "total_price": 1000.0
                }
            ],
            "request": {
                "custom1": None,
                "custom2": None
            }
        },
        {
            "payment_id": 320032557387,
            "order_id": "f0bc4487-4805-480e-b561-7839abb83e9b",
            "date": "2026-01-14 17:05:44",
            "description": "Chess for Intermidiet Level",
            "status": "RECEIVED",
            "currency": "LKR",
            "amount": 1000.0,
            "customer": {
                "fist_name": "imalsha",
                "last_name": "gamage",
                "email": "imalsha.gamage2005@gmail.com",
                "phone": "0760661605",
                "delivery_details": {
                    "address": "NO.70A, Saragama, Kurunegala",
                    "city": "Kurunegala",
                    "country": "Sri Lanka"
                }
            },
            "amount_detail": {
                "currency": "LKR",
                "gross": 1000.0,
                "fee": 33.0,
                "net": 967.0,
                "exchange_rate": 1.0,
                "exchange_from": "LKR",
                "exchange_to": "LKR"
            },
            "payment_method": {
                "method": "VISA",
                "card_customer_name": "kavindu",
                "card_no": "************1292"
            },
            "items": [
                {
                    "name": "Chess for Intermidiet Level",
                    "quantity": 1,
                    "currency": "LKR",
                    "unit_price": 1000.0,
                    "total_price": 1000.0
                }
            ],
            "request": {
                "custom1": None,
                "custom2": None
            }
        },
        {
            "payment_id": 320032557385,
            "order_id": "f0bc4487-4805-480e-b561-7839abb83e9b",
            "date": "2026-01-14 17:04:31",
            "description": "Chess for Intermidiet Level",
            "status": "RECEIVED",
            "currency": "LKR",
            "amount": 1000.0,
            "customer": {
                "fist_name": "imalsha",
                "last_name": "gamage",
                "email": "imalsha.gamage2005@gmail.com",
                "phone": "0760661605",
                "delivery_details": {
                    "address": "NO.70A, Saragama, Kurunegala",
                    "city": "Kurunegala",
                    "country": "Sri Lanka"
                }
            },
            "amount_detail": {
                "currency": "LKR",
                "gross": 1000.0,
                "fee": 33.0,
                "net": 967.0,
                "exchange_rate": 1.0,
                "exchange_from": "LKR",
                "exchange_to": "LKR"
            },
            "payment_method": {
                "method": "VISA",
                "card_customer_name": "kavindu",
                "card_no": "************1292"
            },
            "items": [
                {
                    "name": "Chess for Intermidiet Level",
                    "quantity": 1,
                    "currency": "LKR",
                    "unit_price": 1000.0,
                    "total_price": 1000.0
                }
            ],
            "request": {
                "custom1": None,
                "custom2": None
            }
        },
        {
            "payment_id": 320032557378,
            "order_id": "f0bc4487-4805-480e-b561-7839abb83e9b",
            "date": "2026-01-14 16:46:58",
            "description": "Chess for Intermidiet Level",
            "status": "RECEIVED",
            "currency": "LKR",
            "amount": 1000.0,
            "customer": {
                "fist_name": "imalsha",
                "last_name": "gamage",
                "email": "imalsha.gamage2005@gmail.com",
                "phone": "0760661605",
                "delivery_details": {
                    "address": "NO.70A, Saragama, Kurunegala",
                    "city": "Kurunegala",
                    "country": "Sri Lanka"
                }
            },
            "amount_detail": {
                "currency": "LKR",
                "gross": 1000.0,
                "fee": 33.0,
                "net": 967.0,
                "exchange_rate": 1.0,
                "exchange_from": "LKR",
                "exchange_to": "LKR"
            },
            "payment_method": {
                "method": "VISA",
                "card_customer_name": "kavindu",
                "card_no": "************1292"
            },
            "items": [
                {
                    "name": "Chess for Intermidiet Level",
                    "quantity": 1,
                    "currency": "LKR",
                    "unit_price": 1000.0,
                    "total_price": 1000.0
                }
            ],
            "request": {
                "custom1": None,
                "custom2": None
            }
        }
    ]
}