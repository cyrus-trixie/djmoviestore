require("dotenv").config();
const axios = require("axios");

const getAccessToken = async () => {
    const auth = Buffer.from(`${process.env.CONSUMER_KEY}:${process.env.CONSUMER_SECRET}`).toString("base64");
    
    try {
        const response = await axios.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials", {
            headers: { Authorization: `Basic ${auth}` }
        });

        return response.data.access_token;
    } catch (error) {
        console.error("Error getting access token:", error.response.data);
    }
};

const stkPush = async (phoneNumber, amount) => {
    const accessToken = await getAccessToken();
    if (!accessToken) return;

    const timestamp = new Date().toISOString().replace(/[-T:]/g, "").split(".")[0]; // Format timestamp
    const password = Buffer.from(process.env.BUSINESS_SHORTCODE + process.env.PASSKEY + timestamp).toString("base64");

    const data = {
        BusinessShortCode: process.env.BUSINESS_SHORTCODE,
        Password: password,
        Timestamp: timestamp,
        TransactionType: "CustomerPayBillOnline",
        Amount: amount,
        PartyA: phoneNumber,
        PartyB: process.env.BUSINESS_SHORTCODE,
        PhoneNumber: phoneNumber,
        CallBackURL: process.env.CALLBACK_URL,
        AccountReference: "MoviePayment",
        TransactionDesc: "Payment for movie access"
    };

    try {
        const response = await axios.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", data, {
            headers: { Authorization: `Bearer ${accessToken}` }
        });

        console.log("STK Push Response:", response.data);
    } catch (error) {
        console.error("Error sending STK Push:", error.response.data);
    }
};

// Test STK Push
stkPush("254742918991", 100); // Change to your phone number
