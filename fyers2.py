from fyers_apiv3 import fyersModel
import webbrowser
import os
import socketserver
from dotenv import load_dotenv

DEFAULT_PORT = 80
DEFAULT_PATH = "/callback"
FYERS_BASE = os.environ.get("FYERS_API_BASE", "https://api.fyers.in")

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "FyersAuth/0.1"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        code = q.get("code", [None])[0]
        state = q.get("state", [None])[0]
        self.server.auth_code = code
        # Respond to browser
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if code:
            self.wfile.write(b"<html><body><h1>Authorization received</h1><p>You can close this window.</p></body></html>")
        else:
            self.wfile.write(b"<html><body><h1>Missing code</h1><p>Check the query parameters.</p></body></html>")

    def log_message(self, format, *args):
        # Silence default logging
        return


def run_local_server(port: int) -> socketserver.TCPServer:
    handler = CallbackHandler
    httpd = socketserver.TCPServer(("", port), handler)
    # attach a place to store the code
    httpd.auth_code = None
    return httpd

def main() -> None:
    """
    1. Input parameters (loaded from .env)
    """
    load_dotenv()
    redirect_uri = os.getenv("FYERS_REDIRECT_URI")
    client_id = os.getenv("FYERS_CLIENT_ID")
    secret_key = os.getenv("FYERS_CLIENT_SECRET")
    if not client_id or not secret_key:
        raise SystemExit("Please set FYERS_CLIENT_ID and FYERS_CLIENT_SECRET in your .env or environment")
    grant_type = "authorization_code"                  ## The grant_type always has to be "authorization_code"
    response_type = "code"                             ## The response_type always has to be "code"
    state = "sample"                                   ##  The state field here acts as a session manager. you will be sent with the state field after successfull generation of auth_code 


    ### Connect to the sessionModel object here with the required input parameters
    appSession = fyersModel.SessionModel(client_id = client_id, redirect_uri = redirect_uri,response_type=response_type,state=state,secret_key=secret_key,grant_type=grant_type)

    auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiJQNkhEMVQ5WEdaIiwidXVpZCI6IjU1Y2NjNTBmZGYxNjRkOWZhZGFhYTUyMTMyOGVhYjEzIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IkZBSjc5MjQzIiwib21zIjoiSzEiLCJoc21fa2V5IjoiMGQyN2ExYTVlODM2ZmI3ZDMzODgwYTVjYzljM2I1MTFjYzJmNWZlMTdlMGJiNzlmNmQ1OGNjZGEiLCJpc0RkcGlFbmFibGVkIjoiTiIsImlzTXRmRW5hYmxlZCI6Ik4iLCJhdWQiOiJbXCJkOjFcIixcImQ6MlwiLFwieDowXCIsXCJ4OjFcIl0iLCJleHAiOjE3ODY4MjI5OTQsImlhdCI6MTc4Njc5Mjk5NCwiaXNzIjoiYXBpLmxvZ2luLmZ5ZXJzLmluIiwibmJmIjoxNzg2NzkyOTk0LCJzdWIiOiJhdXRoX2NvZGUifQ.zqBhpfGcKkr6R_ulK0JNRTmuBam7z0dTF8F4JRgxN6Q"
    appSession.set_token(auth_code)
    response = appSession.generate_token()

    ## There can be two cases over here you can successfully get the acccessToken over the request or you might get some error over here. so to avoid that have this in try except block
    try: 
        #print("Response:", response)
        access_token = response["access_token"]
        refresh_token = response["refresh_token"]
        print("Access Token:", access_token)
        print("Refresh Token:", refresh_token)
    except Exception as e:
        print(e,response)  ## This will help you in debugging then and there itself like what was the error and also you would be able to see the value you got in response variable. instead of getting key_error for unsuccessfull response.


if __name__ == "__main__":
	main()