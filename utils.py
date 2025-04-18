import shutil
import tkinter as tk
from tkinter import filedialog
import csv
import sys
import time
import os
import json
import re
from PIL import Image, ExifTags
from dotenv import load_dotenv
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

def get_exif_data(image_path):
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return "N/A", "N/A", "N/A"
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return "N/A", "N/A", "N/A"
            exif = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif_data.items()}
            date_time = exif.get("DateTimeOriginal", "N/A")
            gps_info = exif.get("GPSInfo", None)
            location = "N/A"
            altitude = "N/A"  # Define altitude before conditional statements.
            if gps_info:
                def convert_value_to_dms(value):
                    d = float(value[0])
                    m = float(value[1])
                    s = float(value[2])
                    return f"{int(d)}:{int(m)}:{repr(s)}"

                lat_dms = None
                lon_dms = None
                if 2 in gps_info and 1 in gps_info:
                    lat_dms = convert_value_to_dms(gps_info[2])
                    if gps_info[1] == "S":
                        lat_dms = f"-{lat_dms}"
                if 4 in gps_info and 3 in gps_info:
                    lon_dms = convert_value_to_dms(gps_info[4])
                    if gps_info[3] == "W":
                        lon_dms = f"-{lon_dms}"
                if 6 in gps_info:
                    altitude_value = float(gps_info[6])
                    altitude = f"{altitude_value}"
                if lat_dms and lon_dms:
                    location = f"{lat_dms}, {lon_dms}"
            return date_time, location, altitude
    except Exception as e:
        print(f"Exception occurred: {e}")
        return "Error", "Error", None

def main(pne):
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

    output_file = os.path.join(directory, "results.csv")

    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Image File", "Genus", "Family", "Species Name", "Common Names",
                         "Predicted Organ", "Predicted Organ Score", "Species Score", "Date", "Location", "Altitude"])

        for image in image_files:
            print(f"Processing: {image}")
            try:
                response = pne.identify_by_images([image])
                base_file_name = os.path.splitext(os.path.basename(image))[0]
                save_raw_response(response, directory, base_file_name)
                predicted_organ, predicted_organ_score, sci_name, species_score, genus, family, common_names = extract_data(response)
                date_time, location, altitude = get_exif_data(image)
            except Exception as e:
                predicted_organ = predicted_organ_score = sci_name = species_score = genus = family = common_names = f"Error: {e}"
            writer.writerow([os.path.basename(image), genus, family, sci_name, common_names, predicted_organ,
                             predicted_organ_score, species_score, date_time, location, altitude])

            time.sleep(1)

    print(f"Results have been saved to {output_file}")

def rename_images_from_csv(csv_file, directory, suffix: str = ""):
    counters = {}  # to keep count for each species_organ key
    with open(csv_file, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_file = row["Image File"]
            species_name = row["Species Name"].replace(" ", "_")
            predicted_organ = row["Predicted Organ"].replace(" ", "_")
            key = f"{species_name}_{predicted_organ}"
            counters[key] = counters.get(key, 0) + 1
            new_file_name = f"{species_name}_{predicted_organ}_{counters[key]}"
            if suffix:  # Add suffix only if it's not an empty string
                new_file_name += f"_{suffix}"
            file_ext = os.path.splitext(original_file)[1]
            original_path = os.path.join(directory, original_file)
            new_path = os.path.join(directory, new_file_name + file_ext)
            try:
                os.rename(original_path, new_path)
                print(f"Renamed {original_file} to {new_file_name + file_ext}")
            except Exception as e:
                print(f"Error renaming {original_file}: {e}")

def move_images_by_species_from_filenames(directory):
    # List files that are in the given directory and are image files
    image_extensions = ('.jpg', '.jpeg', '.png')
    for filename in os.listdir(directory):
        if not os.path.isfile(os.path.join(directory, filename)):
            continue
        if not filename.lower().endswith(image_extensions):
            continue

        # Assume file name is formatted as: SpeciesName_PredictedOrgan_Number
        # Use rsplit to extract the species name (could contain underscores if original species contained spaces)
        parts = filename.rsplit('_', 3)
        if len(parts) < 4:
            print(f"Skipping file with unexpected name format: {filename}")
            continue
        species_name = '_'.join(parts[:-3])  # Join all parts except the last three

        # Create the destination folder if it doesn't exist
        species_folder = os.path.join(directory, species_name)
        if not os.path.exists(species_folder):
            os.makedirs(species_folder)

        src_path = os.path.join(directory, filename)
        dest_path = os.path.join(species_folder, filename)
        try:
            shutil.move(src_path, dest_path)
            print(f"Moved {filename} to {species_name}")
        except Exception as e:
            print(f"Error moving {filename}: {e}")

if __name__ == "__main__":
    load_dotenv("api.env")
    api_key = os.environ.get("Plant_Net_API")
    pne = PlantNetEndpoints(api_key)
    main(pne)
    # result_file = r"C:\Users\fatih\Desktop\flora_project_2025\test\results.csv"
    # directory = r"C:\Users\fatih\Desktop\flora_project_2025\test"
    # rename_images_from_csv(result_file, directory, "fk")
    # move_images_by_species_from_filenames(directory)