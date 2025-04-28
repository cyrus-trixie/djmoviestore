const axios = require("axios");
const consumerKey = "MWUqfn1Q5Przs5zpcrv6o2clzir0SjocvR1w8S6AGCaSGIGr";
const consumerSecret = "09tLGgqHMdAIeXhFdbCI0rBTzY4DE7ZCdxDKNTycTTVKTjdTzKTtAx50l8uXeg35";

const getAccessToken = async () => {
    const auth = Buffer.from(`${consumerKey}:${consumerSecret}`).toString("base64");
    
    try {
        const response = await axios.get("https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials", {
            headers: { Authorization: `Basic ${auth}` }
        });

        console.log("Access Token:", response.data.access_token);
        return response.data.access_token;
    } catch (error) {
        console.error("Error getting access token:", error.response.data);
    }
};

getAccessToken();
