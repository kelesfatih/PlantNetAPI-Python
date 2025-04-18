import utils
import os
from dotenv import load_dotenv
from plant_net_endpoints import PlantNetEndpoints

load_dotenv("api.env")
api_key = os.environ.get("Plant_Net_API")
pne = PlantNetEndpoints(api_key)
utils.main(pne)