const axios = require('axios');

const generateAccessToken = async () => {
  const credentials = Buffer.from('your_shortcode' + ':' + 'your_passkey').toString('base64');
  const response = await axios({
    method: 'get',
    url: 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',  // Live URL
    headers: {
      'Authorization': `Basic ${credentials}`,
    },
  });
  return response.data.access_token;
};

const initiatePayment = async () => {
  const accessToken = await generateAccessToken();
  
  const headers = {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };

  const payload = {
    "BusinessShortcode": "3416056",  // Your Till Number
    "LipaNaMpesaOnlineShortcode": "3416056",  // Same Till Number
    "LipaNaMpesaOnlineShortcodePasskey": "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919",  // Your Passkey
    "Amount": 10,  // Payment amount
    "PhoneNumber": "+254742918991",  // Customer phone number
    "AccountReference": "MOVIE12345",  // Unique reference for the transaction
    "TransactionReference": "MOVIE12345TX",  // Unique transaction reference
    "Password": "MTc0Mzc5eW91cl9wYXNza2V5X2hlcmUyMDI1MDQwNDEzMzAwMw==",  // The base64 encoded password
    "TimeStamp": "20250404133003",  // Your timestamp (this should be the exact value you generated)
  };

  try {
    const response = await axios.post('https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest', payload, { headers });
    console.log(response.data);  // The response data will indicate whether the payment request was successful
  } catch (error) {
    console.error('Error making payment request:', error);
  }
};

initiatePayment();
