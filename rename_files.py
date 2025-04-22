import utils
your_initials = "fk"
result_file = r"C:\Users\fatih\Desktop\flora_project_2025\20250416_reviewed_images_fatih_keles\results.csv"
directory = r"C:\Users\fatih\Desktop\flora_project_2025\20250416_reviewed_images_fatih_keles"
utils.rename_images_from_csv(result_file, directory, your_initials)
utils.move_images_by_species_from_filenames(directory)
