const crypto = require("crypto");

const businessShortCode = "174379"; // Your Shortcode
const passkey = "your_passkey_here";
const timestamp = new Date().toISOString().replace(/[-T:.Z]/g, "").slice(0, 14); // YYYYMMDDHHMMSS

const password = Buffer.from(businessShortCode + passkey + timestamp).toString("base64");

console.log("Generated Password:", password);
console.log("Timestamp:", timestamp);
