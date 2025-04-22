import shutil
import tkinter as tk
from tkinter import filedialog
import csv
import sys
import time
import os
import json
import re
import pandas as pd
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

def replace_initials(directory, old_initials, new_initials):
    for root, _, files in os.walk(directory):
        for file in files:
            base, ext = os.path.splitext(file)
            # Check if the filename (without extension) ends with the old initials.
            if base.endswith(old_initials):
                # Create a new base name by replacing the ending initials.
                new_base = base[:-len(old_initials)] + new_initials
                new_file = new_base + ext
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_file)
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} --> {new_path}")
                except Exception as e:
                    print(f"Error renaming {old_path}: {e}")

def merge_csv_files(root_dir, output_file=None):
    # Save merged CSV file in the top directory if no output_file is provided
    if output_file is None:
        output_file = os.path.join(root_dir, "merged_results.csv")
    header_saved = False
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = None
        for dirpath, _, filenames in os.walk(root_dir):
            if 'results.csv' in filenames:
                file_path = os.path.join(dirpath, 'results.csv')
                with open(file_path, 'r', newline='', encoding='utf-8') as infile:
                    reader = csv.reader(infile)
                    header = next(reader)
                    if not header_saved:
                        writer = csv.writer(outfile)
                        writer.writerow(header)
                        header_saved = True
                    for row in reader:
                        writer.writerow(row)
                print(f"Merged: {file_path}")
    print(f"Merged CSV saved as: {os.path.abspath(output_file)}")

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

def organs_transposed(input_file, output_file):
    species_dict = {}

    # Read the input file and build a dictionary where each species collects its details.
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            species_name = row['Species Name']
            predicted_organ = row['Predicted Organ'].strip().lower()
            if species_name not in species_dict:
                # Store first occurrence values including Date, Location, and Altitude.
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

    # Get a sorted list of unique organ names.
    all_organs = sorted({organ for sp in species_dict.values() for organ in sp['organs']})

    # Define fieldnames with organ columns placed between Common Names and Date.
    # (Note: if "Turkish Name" is not needed, remove it.)
    fieldnames = ['Genus', 'Family', 'Species Name', 'Common Names', "Turkish Name", "Type", "Clade"] + all_organs + ['Date', 'Location', 'Altitude']

    # Write the transposed output.
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

def merge_excel_mapping(main_csv, mapping_xlsx, output_excel):
    # Define column names for the main file
    main_cols = ['Genus', 'Family', 'Species Name', 'Common Names', 'Turkish Name', 'Type', 'Clade',
                 'bark', 'flower', 'fruit', 'habit', 'leaf', 'Date', 'Location', 'Altitude']
    # Load main CSV file
    main_df = pd.read_csv(main_csv, encoding='utf-8')

    # Ensure the main file contains all expected columns. Missing ones are created as empty.
    for col in main_cols:
        if col not in main_df.columns:
            main_df[col] = ""

    # Load mapping Excel file
    mapping_df = pd.read_excel(mapping_xlsx)

    # Standardize keys: trim and lower-case for matching
    main_df['species_key'] = main_df['Species Name'].astype(str).str.strip().str.lower()
    main_df['common_key'] = main_df['Common Names'].astype(str).str.strip().str.lower()
    mapping_df['species_key'] = mapping_df['LATIN NAME'].astype(str).str.strip().str.lower()
    mapping_df['common_key'] = mapping_df['ENGLISH NAME'].astype(str).str.strip().str.lower()

    # Create a mapping index by the key pair for easy lookup
    mapping_keys = mapping_df.set_index(['species_key', 'common_key'])

    # Update Turkish Name, Type, Clade for matching rows in the main DataFrame
    def update_row(row):
        key = (row['species_key'], row['common_key'])
        if key in mapping_keys.index:
            row['Turkish Name'] = mapping_keys.loc[key, 'TURKISH NAME']
            row['Type'] = mapping_keys.loc[key, 'Type']
            row['Clade'] = mapping_keys.loc[key, 'clade']
        return row

    main_df = main_df.apply(update_row, axis=1)

    # Find new rows from mapping that are not in main_df
    main_keys = set(zip(main_df['species_key'], main_df['common_key']))
    new_entries = mapping_df[~mapping_df.apply(lambda r: (r['species_key'], r['common_key']) in main_keys, axis=1)]

    # Create DataFrame for new species with empty values for columns not provided by mapping
    new_rows = pd.DataFrame(columns=main_cols)
    for _, r in new_entries.iterrows():
        new_row = {
            'Genus': "",
            'Family': "",
            'Species Name': r['LATIN NAME'],
            'Common Names': r['ENGLISH NAME'],
            'Turkish Name': r['TURKISH NAME'],
            'Type': r['Type'],
            'Clade': r['clade'],
            'bark': "",
            'flower': "",
            'fruit': "",
            'habit': "",
            'leaf': "",
            'Date': "",
            'Location': "",
            'Altitude': ""
        }
        new_rows = new_rows._append(new_row, ignore_index=True)

    # Append new rows to main DataFrame
    combined_df = pd.concat([main_df[main_cols], new_rows], ignore_index=True)

    # Save result to an Excel file
    combined_df.to_excel(output_excel, index=False)
    print(f"Output saved at: {output_excel}")

if __name__ == "__main__":
    load_dotenv("api.env")
    api_key = os.environ.get("Plant_Net_API")
    pne = PlantNetEndpoints(api_key)
    main(pne)
    # result_file = r"C:\Users\fatih\Desktop\flora_project_2025\test\results.csv"
    # directory = r"C:\Users\fatih\Desktop\flora_project_2025\test"
    # rename_images_from_csv(result_file, directory, "fk")
    # move_images_by_species_from_filenames(directory)
