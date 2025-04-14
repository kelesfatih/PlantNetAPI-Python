import csv
import sys
import os
import time
import requests
import contextlib
import json
import tkinter as tk
from tkinter import filedialog
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

    def identify(self, images):
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


def get_image_files(directory):
    return [os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and f.lower().endswith(('.jpg', '.jpeg', '.png'))]


def extract_first_name_and_score(response_data):
    results = response_data.get("results", [])
    if not results:
        return "N/A", "N/A"
    first_result = results[0]
    sci_name = first_result.get("species", {}).get("scientificNameWithoutAuthor", "N/A")
    score = first_result.get("score", "N/A")
    return sci_name, score

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    directory = filedialog.askdirectory(title="Select Image Directory")
    if not directory:
        print("No directory selected.")
        sys.exit(1)

    image_files = get_image_files(directory)
    if not image_files:
        print("No image files found in directory.")
        sys.exit(1)

    pne = PlantNetEndpoints()
    output_file = os.path.join(directory, "results.csv")

    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Image File", "Scientific Name", "Score"])

        for image in image_files:
            print(f"Processing: {image}")
            try:
                response = pne.identify([image])
                sci_name, score = extract_first_name_and_score(response)
            except Exception as e:
                sci_name = f"Error: {e}"
                score = "Error"
            writer.writerow([os.path.basename(image), sci_name, score])
            time.sleep(1)

    print(f"Results have been saved to {output_file}")


if __name__ == "__main__":
    main()
