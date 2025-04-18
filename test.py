import os
import shutil

def merge_species_folders(main_folders, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    for main_folder in main_folders:
        for species_folder in os.listdir(main_folder):
            species_path = os.path.join(main_folder, species_folder)
            if not os.path.isdir(species_path):
                continue

            dest_species_path = os.path.join(destination_folder, species_folder)
            if not os.path.exists(dest_species_path):
                os.makedirs(dest_species_path)

            for image_file in os.listdir(species_path):
                src_image_path = os.path.join(species_path, image_file)
                if not os.path.isfile(src_image_path):
                    continue

                dest_image_path = os.path.join(dest_species_path, image_file)
                base_name, ext = os.path.splitext(image_file)
                counter = 1

                # Ensure unique file name in the destination folder
                while os.path.exists(dest_image_path):
                    dest_image_path = os.path.join(dest_species_path, f"{base_name}_{counter}{ext}")
                    counter += 1

                try:
                    shutil.copy(src_image_path, dest_image_path)
                    print(f"Copied {src_image_path} to {dest_image_path}")
                except Exception as e:
                    print(f"Error copying {src_image_path}: {e}")

# Example usage:
main_folders = [
    r"C:\Users\fatih\Desktop\flora_project_2025\folder_name_1",
    r"C:\Users\fatih\Desktop\flora_project_2025\folder_name_2"
]
destination_folder = r"C:\Users\fatih\Desktop\flora_project_2025\merged_folder"
merge_species_folders(main_folders, destination_folder)