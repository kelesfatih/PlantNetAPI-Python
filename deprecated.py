# Functions below will be deprecated.
def save_raw_response(response, base_directory, file_name):
    safe_file_name = os.path.basename(file_name)
    safe_file_name = re.sub(r'[^A-Za-z0-9\-_]', '_', safe_file_name)
    raw_folder = os.path.join(base_directory, "raw_response")
    if not os.path.exists(raw_folder):
        os.makedirs(raw_folder)
    json_file_path = os.path.join(raw_folder, f"{safe_file_name}.json")
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(response, json_file, indent=4)

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
