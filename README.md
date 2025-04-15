# Python Interface for Pl@nt Net API (v2) Endpoints
!!! API ENDPOINTS ARE NOT EXTENSIVELY TESTED. USE AT YOUR OWN RISK !!!
- You need to have private API key to use this API. You can get it from [here](https://my.plantnet.org/account/settings).
- Save your API key as Plant_Net_API to api.env file in the root directory of the project.
- Here is an example Plant_Net_API=123456789abcdef0123456789abcdef0

# Requirements
```
pip install -r requirements.txt
```

# Endpoints
Some endpoints are not added yet. You can use post requests to identify images.
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