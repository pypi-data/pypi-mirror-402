from RasediPaymentSDK import PaymentClient,GATEWAY,ICreatePayment

async def main():
    # secret_key = "live_laisEJqXbLSdUaitcEpPibB6LDINQ9RcmXp7HmYsR2zzX3_WTUNvh5mByZVMFdibvKWPH9HZks2RzxoD2TTjxEwk"
    # private_key = """-----BEGIN PRIVATE KEY-----
    # MC4CAQAwBQYDK2VwBCIEIH8fsaTsKrU8Iv3wW0ranPx/H9YfAyRB2nilI+OxaS0g
    # -----END PRIVATE KEY-----"""
    secret_key = "live_laisxVjnNnoY1w5mwWP6YwzfPg_zmu2BnWnJH1uCOzOGcAflAYShdjVPuDAG10DLSEpTOlsOopiyTJHJjO4fbqqU"
    private_key = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEID2nK2pCcGSbtS+U9jc2SCYxHWOo1eA4IR97bdif4+rx
-----END PRIVATE KEY-----"""
    
    client = PaymentClient(private_key=private_key, secret_key=secret_key)
    print("INSTALLED_OK", type(client).__name__)

    try:
        creation_res =  await client.create_payment(payload=ICreatePayment(
            amount="10200",title="Test Payment",description="This is a test payment",gateways=[GATEWAY.CREDIT_CARD],redirectUrl="https://google.com", collectFeeFromCustomer=True,collectCustomerEmail=True,collectCustomerPhoneNumber=False,callbackUrl="https://google.com"))
        print("PAYMENT_CREATION_RESPONSE", creation_res)
    except Exception as e:
        print("PAYMENT_CREATION_ERROR", str(e))

    try: 
        get_res = await client.get_payment_by_reference_code(reference_code="0b0a8bce-bf3c-4fc4-993e-6179d95e9ece")
        print("GET_PAYMENT_RESPONSE", get_res)
    except Exception as e:
        print("GET_PAYMENT_ERROR", e)

    try:
        cancel_res = await client.cancel_payment(reference_code=get_res.body.referenceCode)
        print("CANCEL_PAYMENT_RESPONSE", cancel_res)
    except Exception as e:
        print("CANCEL_PAYMENT_ERROR",e)

    try: 
        get_after_cancel = await client.get_payment_by_reference_code(reference_code=cancel_res.body.referenceCode)
        print("GET_AFTER_CANCEL", get_after_cancel)
    except Exception as e:
        print("GET_AFTER_CANCEL_ERROR", e)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())