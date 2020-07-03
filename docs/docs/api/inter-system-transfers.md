
# Transfers config


More information

## List all transfers configs

`GET /admin/transfers-config`


List all of the transfers configs that are installed.

## Preview a transfers config

`POST /admin/transfers-config/preview`


This endpoint returns a preview of the transfers that would be created
using a specific config.

URL parameter | type | description
--------------|------|------------
`system_id`   | multiple string values | The system IDs to create transfers between
`distance`    | float | the maximum distance, in meters, between two stops in order for a transfer to be created between them

## Create a transfers config

`POST /admin/transfers-config`


This endpoint is identical to the preview endpoint, except that the resulting
transfers are persisted and a new transfer config is created.

## Get a transfers config

`GET /admin/transfers-config/<int:config_id>`



## Update a transfers config

`PUT /admin/transfers-config/<int:config_id>`


This endpoint is identical to the preview endpoint, except that the resulting
transfers are persisted and a new transfer config is created.

## Delete a transfers config

`DELETE /admin/transfers-config/<int:config_id>`


This endpoint deletes the config as well as all transfers associated to the config.
