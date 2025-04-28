const axios = require('axios');
require('dotenv').config(); // For loading env variables

const getAccessToken = async () => {
  try {
    const credentials = Buffer.from(
      `${process.env.PAYPAL_CLIENT_ID}:${process.env.PAYPAL_SECRET}`
    ).toString('base64');

    const response = await axios.post(
      'https://api.sandbox.paypal.com/v1/oauth2/token',
      'grant_type=client_credentials', // Send as data, not params
      {
        headers: {
          Authorization: `Basic ${credentials}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    return response.data.access_token;
  } catch (error) {
    console.error('Error getting access token:', error.response?.data || error.message);
  }
};

const createPayment = async () => {
  try {
    const accessToken = await getAccessToken();
    if (!accessToken) {
      throw new Error('Failed to obtain access token');
    }

    const paymentData = {
      intent: 'sale',
      payer: {
        payment_method: 'paypal',
      },
      transactions: [
        {
          amount: {
            total: '10.00',
            currency: 'USD',
          },
          description: 'Payment for Movie Tickets',
        },
      ],
      redirect_urls: {
        return_url: 'http://localhost:5173/',
        cancel_url: 'http://localhost:5173/',
      },
    };

    const response = await axios.post(
      'https://api.sandbox.paypal.com/v1/payments/payment',
      paymentData,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    console.log('Payment created:', response.data);
  } catch (error) {
    console.error('Error creating payment:', error.response?.data || error.message);
  }
};

// Call the function properly
(async () => {
  await createPayment();
})();
