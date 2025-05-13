# Python Interface for Pl@nt Net API (v2) Endpoints

- You need to have private API key from PlantNet to initiate API. You can get it from [here](https://my.plantnet.org/account/settings).

# Install
```
git clone https://github.com/kelesfatih/PlantNetAPI-Python.git
```
# Navigate to project directory
```
cd PlantNetAPI-Python
```
# Install Requirements
```
pip install -r requirements.txt
```
# Windows Users: Convert to executable (.exe) file
For Windows users it is recommended to convert this repository to executable using PyInstaller. 
You can do this by running the following command in the terminal:
```
pip install pyinstaller
pyinstaller --onefile --windowed src/gui.py
```
# CLI Users
If you want to use this repository with CLI, you need to initiate endpoints class with your API key.
```
from src.endpoints import PlantNetEndpoints
pne = PlantNetEndpoints("your_api_key_here")
```
Then you can use the functions as follows:
```
from src.utils import *
identify_images_api(pne)
```
# Endpoints
- GET
  * Status
  * Languages
  * Projects
  * Species
  * Subscription
  * Identify/{project}
  * Quota/daily
  * Quota/history
  * Projects/{project}/species
- POST
  * Identify/{project}
