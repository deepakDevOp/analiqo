import requests
import json

# Define the API endpoint
url = "https://1.rome.api.flipkart.com/api/3/page/dynamic/product-sellers"

# Headers (based on the network request you provided)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Referer": "https://www.flipkart.com",
}

# Payload (modify this according to your needs)
payload = {
    "requestContext": {
        "productId": "ACCG6DS7WDJHGWSH"  # Replace with your desired product ID
    }
}

try:
    # Make the POST request
    response = requests.post(url, headers=headers, json=payload)

    # Check if the response is successful
    if response.status_code == 200:
        # Parse JSON response
        data = response.json()
        
        # Optional: Save the response to a file
        with open("response.json", "w") as f:
            json.dump(data, f, indent=4)
    else:
        # Failed request handling without print statements
        response_code = response.status_code
        response_text = response.text
        
except Exception as e:
    # Exception handling without print statements
    error = str(e)
