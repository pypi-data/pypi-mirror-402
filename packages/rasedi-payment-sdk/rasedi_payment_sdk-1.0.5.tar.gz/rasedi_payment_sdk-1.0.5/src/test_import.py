from RasediPaymentSDK import PaymentClient,GATEWAY,ICreatePayment

# live_laisxVjnNnoY1w5mwWP6YwzfPg_zmu2BnWnJH1uCOzOGcAflAYShdjVPuDAG10DLSEpTOlsOopiyTJHJjO4fbqqU
#     private_key = """-----BEGIN PRIVATE KEY-----
# MC4CAQAwBQYDK2VwBCIEID2nK2pCcGSbtS+U9jc2SCYxHWOo1eA4IR97bdif4+rx
# -----END PRIVATE KEY-----"""
async def main():
    secret_key = "live_laisxVjnNnoY1w5mwWP6YwzfPg_zmu2BnWnJH1uCOzOGcAflAYShdjVPuDAG10DLSEpTOlsOopiyTJHJjO4fbqqU"
    private_key = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEID2nK2pCcGSbtS+U9jc2SCYxHWOo1eA4IR97bdif4+rx
-----END PRIVATE KEY-----"""
    
    client = PaymentClient(private_key=private_key, secret_key=secret_key)
    print("INSTALLED_OK", type(client).__name__)

    try:
        response =  await client.create_payment(payload=ICreatePayment(
            amount="300",title="Test Payment",description="This is a test payment",gateways=[GATEWAY.FIB,GATEWAY.ZAIN,GATEWAY.ASIA_PAY,GATEWAY.FAST_PAY,GATEWAY.NASS_WALLET,GATEWAY.CREDIT_CARD],redirectUrl="https://google.com", collectFeeFromCustomer=True,collectCustomerEmail=True,collectCustomerPhoneNumber=False,callbackUrl="https://webhook.site/fa1ce58d-d917-47d2-b93d-624ea78c66aa"),)
        print("PUBLIC_KEYS_RESPONSE", response)
    except Exception as e:
        print("PUBLIC_KEYS_ERROR", str(e))

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())