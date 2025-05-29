import os
import re
import shutil

pattern = re.compile(r'^(?P<base>[A-Za-z0-9]+_[A-Za-z0-9]+_[A-Za-z0-9]+)_(?P<number>\d+)_(?P<suffix>.+)$')

def get_unique_filename(dest_dir, filename):
    name, ext = os.path.splitext(filename)
    match = pattern.match(name)
    if not match:
        counter = 1
        new_name = f"{name}_{counter}{ext}"
        while os.path.exists(os.path.join(dest_dir, new_name)):
            counter += 1
            new_name = f"{name}_{counter}{ext}"
        return new_name
    base = match.group('base')
    number = int(match.group('number'))
    suffix = match.group('suffix')
    new_filename = filename
    while os.path.exists(os.path.join(dest_dir, new_filename)):
        number += 1
        new_filename = f"{base}_{number}_{suffix}{ext}"
    return new_filename

def merge_images(src_main_folders, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        print(f"Created destination folder: {dest_folder}")
    for main_folder in src_main_folders:
        if not os.path.exists(main_folder):
            print(f"Main folder does not exist: {main_folder}")
            continue
        print(f"Processing main folder: {main_folder}")
        for species_folder in os.listdir(main_folder):
            species_path = os.path.join(main_folder, species_folder)
            if not os.path.isdir(species_path):
                continue
            print(f"Found species folder: {species_path}")
            # Process images directly in the species folder
            for file in os.listdir(species_path):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    src_file = os.path.join(species_path, file)
                    new_filename = get_unique_filename(dest_folder, file)
                    dest_file = os.path.join(dest_folder, new_filename)
                    shutil.copy2(src_file, dest_file)
                    print(f"Copied {src_file} to {dest_file}")
                else:
                    print(f"Skipped non-image file: {file}")

