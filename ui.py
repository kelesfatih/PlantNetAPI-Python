import tkinter as tk
from tkinter import filedialog
import csv
import sys
import time
import os
import json
import re
from plant_net_endpoints import PlantNetEndpoints

def get_image_files(directory):
    return [os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and f.lower().endswith(('.jpg', '.jpeg', '.png'))]

def extract_data(response_data):
    predicted_orgs = response_data.get("predictedOrgans", [])
    if predicted_orgs:
        organ_names = []
        organ_scores = []
        for org in predicted_orgs:
            organ_names.append(org.get("organ", "N/A"))
            organ_scores.append(str(org.get("score", "N/A")))
        predicted_organ = ", ".join(organ_names)
        predicted_organ_score = ", ".join(organ_scores)
    else:
        predicted_organ = predicted_organ_score = "N/A"

    results = response_data.get("results", [])
    if results:
        first_result = results[0]
        species = first_result.get("species", {})
        species_name = species.get("scientificNameWithoutAuthor", "N/A")
        species_score = first_result.get("score", "N/A")
        genus = species.get("genus", {}).get("scientificNameWithoutAuthor", "N/A")
        family = species.get("family", {}).get("scientificNameWithoutAuthor", "N/A")
        common_names = ", ".join(species.get("commonNames", []))
    else:
        species_name = species_score = genus = family = common_names = "N/A"

    return predicted_organ, predicted_organ_score, species_name, species_score, genus, family, common_names


def save_raw_response(response, base_directory, file_name):
    safe_file_name = os.path.basename(file_name)
    safe_file_name = re.sub(r'[^A-Za-z0-9\-_]', '_', safe_file_name)
    raw_folder = os.path.join(base_directory, "raw_response")
    if not os.path.exists(raw_folder):
        os.makedirs(raw_folder)
    json_file_path = os.path.join(raw_folder, f"{safe_file_name}.json")
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(response, json_file, indent=4)

def main():
    root = tk.Tk()
    root.withdraw()
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
        writer.writerow(["Image File", "Genus", "Family", "Species Name", "Common Names",
                         "Predicted Organ", "Predicted Organ Score", "Species Score"])

        for image in image_files:
            print(f"Processing: {image}")
            try:
                response = pne.identify_by_images([image])
                base_file_name = os.path.splitext(os.path.basename(image))[0]
                save_raw_response(response, directory, base_file_name)
                predicted_organ, predicted_organ_score, sci_name, species_score, genus, family, common_names = extract_data(response)
            except Exception as e:
                predicted_organ = predicted_organ_score = sci_name = species_score = genus = family = common_names = f"Error: {e}"
            writer.writerow([os.path.basename(image), genus, family, sci_name, common_names, predicted_organ, predicted_organ_score, species_score])

            time.sleep(1)

    print(f"Results have been saved to {output_file}")


if __name__ == "__main__":
    main()