import enum


class GATEWAY(enum.Enum):
    FIB = "FIB"
    ZAIN = "ZAIN"
    ASIA_PAY = "ASIA_PAY"
    FAST_PAY = "FAST_PAY"
    NASS_WALLET = "NASS_WALLET"
    CREDIT_CARD = "CREDIT_CARD"

class PAYMENT_STATUS(enum.Enum):
    TIMED_OUT = "TIMED_OUT"
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELED = "CANCELED"
    FAILED = "FAILED"