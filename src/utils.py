import shutil
import csv
import sys
import time
import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ExifTags


def image_paths(directory):
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


def image_date_location(image_path):
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
            altitude = "N/A"
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
        return None, None, None


def identify_images_api(pne):
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Select Image Directory")
    if not directory:
        print("No directory selected.")
        sys.exit(1)
    image_files = image_paths(directory)
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
                response = pne.identify_post(images=[image])
                predicted_organ, predicted_organ_score, sci_name, species_score, genus, family, common_names = extract_data(
                    response)
                date_time, location, altitude = image_date_location(image)
            except Exception as e:
                error_message = f"Error: {e}"
                predicted_organ = predicted_organ_score = sci_name = species_score = genus = family = common_names = error_message
                date_time, location, altitude = "N/A", "N/A", "N/A"
            writer.writerow([os.path.basename(image), genus, family, sci_name, common_names, predicted_organ,
                             predicted_organ_score, species_score, date_time, location, altitude])

            time.sleep(1)
    print(f"Results have been saved to {output_file}")


def rename_to_species(csv_file, directory, suffix: str = ""):
    counters = {}
    with open(csv_file, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_file = row["Image File"]
            species_name = row["Species Name"].replace(" ", "_")
            predicted_organ = row["Predicted Organ"].replace(" ", "_")
            key = f"{species_name}_{predicted_organ}"
            counters[key] = counters.get(key, 0) + 1
            new_file_name = f"{species_name}_{predicted_organ}_{counters[key]}"
            if suffix:
                new_file_name += f"_{suffix}"
            file_ext = os.path.splitext(original_file)[1]
            original_path = os.path.join(directory, original_file)
            new_path = os.path.join(directory, new_file_name + file_ext)
            try:
                os.rename(original_path, new_path)
                print(f"Renamed {original_file} to {new_file_name + file_ext}")
            except Exception as e:
                print(f"Error renaming {original_file}: {e}")


def group_by_species(directory):
    image_extensions = ('.jpg', '.jpeg', '.png')
    for filename in os.listdir(directory):
        if not os.path.isfile(os.path.join(directory, filename)):
            continue
        if not filename.lower().endswith(image_extensions):
            continue
        parts = filename.rsplit('_', 3)
        if len(parts) < 4:
            print(f"Skipping file with unexpected name format: {filename}")
            continue
        species_name = '_'.join(parts[:-3])  # Join all parts except the last three
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


def get_first_english_common_name(common_names_str):
    if not common_names_str:
        return ""
    for name in common_names_str.split(','):
        candidate = name.strip()
        try:
            candidate.encode('ascii')
            return candidate
        except UnicodeEncodeError:
            continue
    return common_names_str.split(',')[0].strip()


def refactor_results(input_file):
    base, ext = os.path.splitext(input_file)
    output_file = base + "_refactored" + ext
    species_dict = {}
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            species_name = row['Species Name']
            predicted_organ = row['Predicted Organ'].strip().lower()
            if species_name not in species_dict:
                species_dict[species_name] = {
                    'Genus': row['Genus'],
                    'Family': row['Family'],
                    'Common Names': get_first_english_common_name(row['Common Names']),
                    'Date': row['Date'],
                    'Location': row['Location'],
                    'Altitude': row['Altitude'],
                    'organs': set()
                }
            species_dict[species_name]['organs'].add(predicted_organ)
    all_organs = sorted({organ for sp in species_dict.values() for organ in sp['organs']})
    fieldnames = ['Genus', 'Family', 'Species Name', 'Common Names', "Turkish Name", "Type", "Clade"] + all_organs + [
        'Date', 'Location', 'Altitude']
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for species_name, data in species_dict.items():
            row_dict = {
                'Genus': data['Genus'],
                'Family': data['Family'],
                'Species Name': species_name,
                'Common Names': data['Common Names'],
                'Date': data['Date'],
                'Location': data['Location'],
                'Altitude': data['Altitude']
            }
            for organ in all_organs:
                row_dict[organ] = '+' if organ in data['organs'] else ''
            writer.writerow(row_dict)
    print(f"Output saved at: {os.path.abspath(output_file)}")
