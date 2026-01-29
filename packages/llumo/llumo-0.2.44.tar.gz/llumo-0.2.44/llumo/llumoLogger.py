import requests


class LlumoLogger:
    def __init__(self, apiKey: str, project: str):
        self.apiKey = apiKey
        # self.playground = playground
        self.playground = project
        self.workspaceID = None
        self.playgroundID = None
        self.userEmailID = None
        self.isLangchain = False
        self._authenticate()

    def _authenticate(self):
        url = "https://app.llumo.ai/api/get-playground-name"
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.apiKey}",
                    "Content-Type": "application/json",
                },
                json={"playgroundName": self.playground},
                timeout=10,
            )

            if response.status_code == 401:
                # Wrong API key
                print("❌ SDK integration failed! ")
                raise Exception("Your Llumo API key is Invalid. Try again.")


            response.raise_for_status()
            res_json = response.json()

            # Navigate into the nested "data" structure
            inner_data = res_json.get("data", {}).get("data", {})

            self.workspaceID = inner_data.get("workspaceID")
            self.playgroundID = inner_data.get("playgroundID")
            self.userEmailID = inner_data.get("createdBy")

            # if not self.workspaceID or not self.playgroundID:
            #     raise RuntimeError(
            #         f"Invalid response: workspaceID or playgroundID missing. Full response: {res_json}"
            #     )
            print("✅ SDK integration successful! ")
        except requests.exceptions.RequestException as req_err:
            raise RuntimeError(
                f"Network or HTTP error during authentication: {req_err}"
            )
        # except ValueError as json_err:
        #     raise RuntimeError(f"Invalid JSON in authentication response: {json_err}")
        # except Exception as e:
        #     raise RuntimeError(f"Authentication failed: {e}")

    def getWorkspaceID(self):
        return self.workspaceID

    def getUserEmailID(self):
        return self.userEmailID

    def getPlaygroundID(self):
        return self.playgroundID
