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
# Convert to executable
```
pip install pyinstaller
pyinstaller --onefile --windowed src/gui.py
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
