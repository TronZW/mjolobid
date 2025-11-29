# Payment Gateway Setup Guide for MjoloBid

This guide explains how to set up payment gateways for subscriptions and payments in MjoloBid, with a focus on **EcoCash** (Zimbabwe's most popular mobile money service).

## Supported Payment Gateways

1. **EcoCash** - Direct EcoCash API integration
2. **Paynow** - Payment aggregator supporting EcoCash, OneMoney, TeleCash, ZimSwitch, Cards, PayPal
3. **Pesepay** - Payment gateway supporting EcoCash and VISA

---

## 1. EcoCash Setup (Recommended for Zimbabwe)

### Step 1: Register as EcoCash Merchant

1. Visit: https://www.ecocash.co.zw/merchants
2. Complete the merchant registration form
3. Provide required business documentation
4. Wait for approval (usually 2-5 business days)

### Step 2: Get API Credentials

After approval, you'll receive:
- **Client ID** - Your application client ID
- **Client Secret** - Your secret key for authentication
- **Merchant ID** - Your unique merchant identifier
- **API Documentation** - Integration guide

### Step 3: Configure Environment Variables

Add to your `.env` file (local) or Render environment variables:

```env
# EcoCash Configuration
ECOCASH_CLIENT_ID=your_client_id_here
ECOCASH_CLIENT_SECRET=your_client_secret_here
ECOCASH_MERCHANT_ID=your_merchant_id_here
ECOCASH_API_URL=https://api.ecocash.co.zw
ECOCASH_SANDBOX=False
```

**For Testing (Sandbox):**
```env
ECOCASH_API_URL=https://sandbox.ecocash.co.zw
ECOCASH_SANDBOX=True
```

### Step 4: How EcoCash Works

- User selects EcoCash as payment method
- System sends USSD push to user's phone
- User approves payment on their phone
- Payment is confirmed via webhook
- Subscription is automatically activated

---

## 2. Paynow Setup (Alternative - Supports Multiple Methods)

### Step 1: Sign Up

1. Visit: https://www.paynow.co.zw
2. Create a merchant account
3. Complete business verification

### Step 2: Get Integration Credentials

You'll receive:
- **Integration ID** - Your Paynow integration identifier
- **Integration Key** - Secret key for API authentication

### Step 3: Configure Environment Variables

```env
# Paynow Configuration
PAYNOW_INTEGRATION_ID=your_integration_id
PAYNOW_INTEGRATION_KEY=your_integration_key
PAYNOW_API_URL=https://www.paynow.co.zw/Interface/API
PAYNOW_SANDBOX=False
```

**For Testing:**
```env
PAYNOW_API_URL=https://sandbox.paynow.co.zw/Interface/API
PAYNOW_SANDBOX=True
```

### Step 4: How Paynow Works

- User selects Paynow
- Redirected to Paynow payment page
- User chooses payment method (EcoCash, OneMoney, Card, etc.)
- Payment processed through Paynow
- User redirected back with payment status

---

## 3. Pesepay Setup

### Step 1: Sign Up

1. Visit: https://www.pesepay.com
2. Register as a merchant
3. Complete verification process

### Step 2: Get API Credentials

You'll receive:
- **API Key** - Your API authentication key
- **Secret Key** - Secret for signature generation

### Step 3: Configure Environment Variables

```env
# Pesepay Configuration
PESEPAY_API_KEY=your_api_key
PESEPAY_SECRET_KEY=your_secret_key
PESEPAY_API_URL=https://api.pesepay.com
PESEPAY_SANDBOX=False
```

---

## 4. Webhook Configuration

Payment gateways send webhooks to confirm payments. Configure webhook URLs:

### EcoCash Webhook
```
https://mjolobid.onrender.com/payments/webhook/ecocash/
```

### Paynow Webhook
```
https://mjolobid.onrender.com/payments/webhook/paynow/
```

### Pesepay Webhook
```
https://mjolobid.onrender.com/payments/webhook/pesepay/
```

**Important:** Add these URLs in your payment gateway dashboard settings.

---

## 5. Testing Payment Flow

### Local Testing

1. Set `ECOCASH_SANDBOX=True` (or equivalent for other gateways)
2. Use sandbox/test credentials
3. Test with test phone numbers provided by gateway
4. Verify webhook callbacks are received

### Production Testing

1. Use real credentials
2. Test with small amounts first
3. Monitor transaction logs
4. Verify webhooks are working

---

## 6. Currency Support

All gateways support:
- **USD** (US Dollars) - Primary currency
- **ZWL** (Zimbabwean Dollar) - Secondary currency

Set currency in transaction:
```python
transaction.currency = 'USD'  # or 'ZWL'
```

---

## 7. Payment Flow Diagram

```
User clicks "Subscribe"
    ↓
Selects payment gateway (EcoCash/Paynow/Pesepay)
    ↓
Enters phone number
    ↓
System initiates payment via gateway API
    ↓
User approves payment (USSD push or redirect)
    ↓
Gateway sends webhook to our server
    ↓
Payment verified and subscription activated
    ↓
User redirected to success page
```

---

## 8. Troubleshooting

### Payment Not Processing

1. **Check API credentials** - Verify all credentials are correct
2. **Check webhook URLs** - Ensure webhooks are configured in gateway dashboard
3. **Check logs** - Review Django logs for API errors
4. **Verify phone number format** - Must be in format: +263771234567

### Webhook Not Received

1. **Check webhook URL** - Must be publicly accessible (not localhost)
2. **Check firewall** - Ensure Render allows incoming webhooks
3. **Check gateway dashboard** - Verify webhook is registered
4. **Test manually** - Use gateway's webhook testing tool

### Payment Status Stuck on "Processing"

1. **Run verification** - System auto-verifies, but you can manually verify
2. **Check gateway dashboard** - View payment status in gateway portal
3. **Contact gateway support** - If payment confirmed but not updating

---

## 9. Security Best Practices

1. **Never commit credentials** - Always use environment variables
2. **Use HTTPS** - All webhook URLs must use HTTPS
3. **Verify webhook signatures** - Gateways provide signatures for verification
4. **Log all transactions** - Keep audit trail of all payments
5. **Monitor for fraud** - Set up alerts for suspicious activity

---

## 10. Support Contacts

### EcoCash
- Website: https://www.ecocash.co.zw
- Support: merchant.support@ecocash.co.zw
- API Docs: Provided after merchant approval

### Paynow
- Website: https://www.paynow.co.zw
- Support: support@paynow.co.zw
- Documentation: Available in merchant dashboard

### Pesepay
- Website: https://www.pesepay.com
- Support: support@pesepay.com
- API Docs: Available after registration

---

## 11. Cost Considerations

### EcoCash
- Merchant registration: Usually free
- Transaction fees: ~2-3% per transaction
- Monthly fees: Varies by merchant tier

### Paynow
- Setup fee: Usually free
- Transaction fees: ~2.5-3.5% per transaction
- Monthly fees: May apply for high-volume merchants

### Pesepay
- Registration: Usually free
- Transaction fees: ~2-3% per transaction
- Monthly fees: Check with Pesepay

---

## 12. Recommended Setup for Zimbabwe

**Primary:** EcoCash (most popular, direct integration)
**Backup:** Paynow (supports multiple methods as fallback)

This gives users maximum flexibility while ensuring high success rates.

---

## Next Steps

1. Choose your primary payment gateway (recommend EcoCash)
2. Register and get credentials
3. Add credentials to environment variables
4. Test in sandbox mode
5. Configure webhooks
6. Test with real payment
7. Go live!

For questions or issues, check the gateway's support documentation or contact their support teams.

