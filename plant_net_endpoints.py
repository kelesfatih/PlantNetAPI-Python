import os
import requests
import contextlib
from dotenv import load_dotenv

class PlantNetEndpoints:
    def __init__(self):
        load_dotenv("api.env")
        self.api_key = os.environ.get("Plant_Net_API")
        self.base_url = "https://my-api.plantnet.org/v2/"

    def status(self):
        url = self.base_url + "_status"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def languages(self):
        url = self.base_url + "languages"
        params = {"api-key": self.api_key}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def projects(self, lang="en", lat=None, lon=None, type="kt"):
        url = self.base_url + "projects"
        params = {
            "api-key": self.api_key,
            "lang":lang,
            "type":type
        }
        if lat is not None:
            params["lat"] = lat
        if lon is not None:
            params["lon"] = lon

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def species(self, lang="en", type="kt", pageSize=None, page=None, prefix=None):
        url = self.base_url + "species"
        params = {
            "api-key": self.api_key,
            "lang": lang,
            "type": type
        }
        if pageSize is not None:
            params["pageSize"] = pageSize
        if page is not None:
            params["page"] = page
        if prefix is not None:
            params["prefix"] = prefix

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def subscription(self):
        url = self.base_url + "subscription"
        params = {"api-key": self.api_key}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return "403 Forbidden: Check your API key and permissions. You may need to subscribe to a plan."
        else:
            response.raise_for_status()

    def identify_by_url(self, project="all", images=None, organs=None, include_related_images=False, no_reject=False,
                        nb_results=10, lang="en", type="kt", authenix_access_token=None):
        if images is None:
            raise ValueError("Both images and organs parameters must be provided.")

        url = self.base_url + "identify/" + project
        params = {
            "api-key": self.api_key,
            "images": images,
            "include-related-images": str(include_related_images).lower(),
            "no-reject": str(no_reject).lower(),
            "nb-results": nb_results,
            "lang": lang,
            "type": type
        }

        if organs is not None:
            params["organs"] = organs
        if authenix_access_token:
            params["authenix-access-token"] = authenix_access_token

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def identify_by_images(self, images):
        url = self.base_url + "identify/all"
        params = {"api-key": self.api_key}
        with contextlib.ExitStack() as stack:
            files = [
                ("images", (image, stack.enter_context(open(image, "rb"))))
                for image in images
            ]
            response = requests.post(url, params=params, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def quota_daily(self, day):
        url = self.base_url + "quota/daily"
        params = {"api-key": self.api_key, "day": day}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def quota_history(self, year):
        url = self.base_url + "quota/history"
        params = {"api-key": self.api_key, "year": year}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return "403 Forbidden: Check your API key and permissions. You may need to subscribe to a plan."
        else:
            response.raise_for_status()

    def projects_project_species(self, project, lang="en", pageSize=None, page=None, prefix=None):
        url = self.base_url + f"projects/{project}/species"
        params = {
            "lang": lang,
            "api-key": self.api_key
        }
        if pageSize is not None:
            params["pageSize"] = pageSize
        if page is not None:
            params["page"] = page
        if prefix is not None:
            params["prefix"] = prefix

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
