# Python Interface for Pl@nt Net API (v2) Endpoints

- You need to have private API key to use this API. You can get it from [here](https://my.plantnet.org/account/settings).
- Save your API key as Plant_Net_API to api.env file in the root directory of the project.
- Here is an example Plant_Net_API=123456789abcdef0123456789abcdef0

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