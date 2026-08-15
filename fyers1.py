from fyers_apiv3 import fyersModel
import webbrowser
import os
from dotenv import load_dotenv

"""
In order to get started with Fyers API we would like you to do the following things first.
1. Checkout our API docs :   https://myapi.fyers.in/docsv3
2. Create an APP using our API dashboard :   https://myapi.fyers.in/dashboard/

Once you have created an APP you can start using the below SDK 
"""


def main() -> None:
	"""Generate an authcode URL and open it in the browser.

	Reads credentials from environment variables (or `.env` via python-dotenv):
	  - FYERS_CLIENT_ID
	  - FYERS_CLIENT_SECRET
	  - FYERS_REDIRECT_URI
	"""
	load_dotenv()

	# Read credentials from environment
	redirect_uri = os.getenv("FYERS_REDIRECT_URI", "https://localhost")
	client_id = os.getenv("FYERS_CLIENT_ID")
	secret_key = os.getenv("FYERS_CLIENT_SECRET")

	if not client_id or not secret_key:
		print("Please set FYERS_CLIENT_ID and FYERS_CLIENT_SECRET in your .env or environment.")
		return

	grant_type = "authorization_code"
	response_type = "code"
	state = "sample"

	# Connect to the sessionModel object here with the required input parameters
	appSession = fyersModel.SessionModel(
		client_id=client_id,
		redirect_uri=redirect_uri,
		response_type=response_type,
		state=state,
		secret_key=secret_key,
		grant_type=grant_type,
	)

	# Make a request to generate_authcode object; this will return a login url
	generateTokenUrl = appSession.generate_authcode()

	# Print and open the URL in the default browser
	print(generateTokenUrl)
	try:
		webbrowser.open(generateTokenUrl, new=1)
	except Exception:
		print("Failed to open browser automatically. Paste the URL into your browser to continue.")


if __name__ == "__main__":
	main()
