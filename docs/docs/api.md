
# HTTP API reference


This page details the HTTP endpoints exposed by Transiter.

Endpoints mostly return JSON data; exceptions are specifically noted.
In order to avoid stale documentation,
the structure of the JSON data returned by each endpoint
 is not described here, but can be inspected on the
[demo site](https://demo.transiter.io) or
by clicking any of the example links below.


## Quick reference
Operation | API endpoint
----------|-------------
**Entrypoint endpoints**
**Transit system endpoints**
[List all systems](#list-all-systems) | `GET /systems`
[Configure system auto-update](#configure-system-auto-update) | `PUT /systems/<system_id>/auto-update`
[List all transfers in a system](#list-all-transfers-in-a-system) | `GET /systems/<system_id>/transfers`
[Get a specific system](#get-a-specific-system) | `GET /systems/<system_id>`
[Install a system](#install-a-system) | `PUT /systems/<system_id>`
[Uninstall a system](#uninstall-a-system) | `DELETE /systems/<system_id>`
**Stop endpoints**
[Search for stops](#search-for-stops) | `POST /stops`
[Get a stop in a system](#get-a-stop-in-a-system) | `GET /systems/<system_id>/stops/<stop_id>`
[List stops in a system](#list-stops-in-a-system) | `GET /systems/<system_id>/stops`
[Search for stops in a system](#search-for-stops-in-a-system) | `POST /systems/<system_id>/stops`
**Route endpoints**
[Get a route in a system](#get-a-route-in-a-system) | `GET /systems/<system_id>/routes/<route_id>`
[List routes in a system](#list-routes-in-a-system) | `GET /systems/<system_id>/routes`
**Trip endpoints**
[Get a trip in a route](#get-a-trip-in-a-route) | `GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`
[List trips in a route](#list-trips-in-a-route) | `GET /systems/<system_id>/routes/<route_id>/trips`
**Feed endpoints**
[List updates for a feed](#list-updates-for-a-feed) | `GET /systems/<system_id>/feeds/<feed_id>/updates`
[Perform a feed flush](#perform-a-feed-flush) | `POST /systems/<system_id>/feeds/<feed_id>/flush`
[Get a feed in a system](#get-a-feed-in-a-system) | `GET /systems/<system_id>/feeds/<feed_id>`
[Perform a feed update](#perform-a-feed-update) | `POST /systems/<system_id>/feeds/<feed_id>`
[List feeds in a system](#list-feeds-in-a-system) | `GET /systems/<system_id>/feeds`
**Transfer config endpoints**
[Preview a transfers config](#preview-a-transfers-config) | `POST /admin/transfers-config/preview`
[List all transfers configs](#list-all-transfers-configs) | `GET /admin/transfers-config`
[Create a transfers config](#create-a-transfers-config) | `POST /admin/transfers-config`
[Get a transfers config](#get-a-transfers-config) | `GET /admin/transfers-config/<int:config_id>`
[Update a transfers config](#update-a-transfers-config) | `PUT /admin/transfers-config/<int:config_id>`
[Delete a transfers config](#delete-a-transfers-config) | `DELETE /admin/transfers-config/<int:config_id>`
**Admin endpoints**
[List scheduler tasks](#list-scheduler-tasks) | `GET /admin/scheduler`
[Refresh scheduler tasks](#refresh-scheduler-tasks) | `POST /admin/scheduler`
[Upgrade database](#upgrade-database) | `POST /admin/upgrade`
[Transiter health status](#transiter-health-status) | `GET /admin/health`

## Entrypoint endpoints

## Transit system endpoints

### List all systems

`GET /systems`


List all transit systems that are installed in this Transiter instance.

### Configure system auto-update

`PUT /systems/<system_id>/auto-update`


Configure whether auto-update is enabled for
 auto-updatable feeds in a system.

The endpoint takes a single form parameter `enabled`
which can either be `true` or `false` (case insensitive).

Return code         | Description
--------------------|-------------
`204 NO CONTENT`    | The configuration was applied successfully.
`400 BAD REQUEST`   | Returned if the form parameter is not provided or is invalid.
`404 NOT FOUND`     | Returned if the system does not exist.

### List all transfers in a system

`GET /systems/<system_id>/transfers`


List all transfers in a system.

Return code | Description
------------|-------------
`200 OK` | A system with this ID exists.
`404 NOT FOUND` | No system with the provided ID is installed.

### Get a specific system

`GET /systems/<system_id>`


Get a system by its ID.

Return code | Description
------------|-------------
`200 OK` | A system with this ID exists.
`404 NOT FOUND` | No system with the provided ID is installed.

### Install a system

`PUT /systems/<system_id>`


This endpoint is used to install or update transit systems.
Installs can be performed asynchronously (recommended)
or synchronously (using the optional URL parameter `sync=true`; not recommended);
see below for more information.

The endpoint accepts `multipart/form-data` requests.
There is a single required parameter, `config_file`, which
specifies the YAML configuration file for the Transit system.
(There is a [dedicated documentation page](systems.md) concerned with creating transit system configuration files.)
The parameter can either be:

- A file upload of the configuration file, or
- A text string, which will be interpreted as a URL pointing to the configuration file.

In addition, depending on the configuration file, the endpoint will also accept extra text form data parameters.
These additional parameters are used for things like API keys, which are different
for each user installing the transit system.
The configuration file will customize certain information using the parameters -
    for example, it might include an API key as a GET parameter in a feed URL.
If you are installing a system using a YAML configuration provided by someone else, you
 should be advised of which additional parameters are needed.
If you attempt to install a system without the required parameters, the install will fail and
the response will detail which parameters you're missing.

#### Async versus sync

Often the install process is long because it often involves performing
large feed updates
of static feeds - for example, in the case of the New York City Subway,
an install takes close to two minutes.
If you perform a synchronous install, the install request is liable
to timeout - for example, Gunicorn by default terminates HTTP
requests that take over 60 seconds.
For this reason you should generally install asynchronously.

After triggering the install asynchronously, you can track its
progress by hitting the `GET` system endpoint repeatedly.

Synchronous installs are supported and useful when writing new
transit system configs, in which case getting feedback from a single request
is quicker.


Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system already exists, in which case this is a no-op.
`201 CREATED`       | For synchronous installs, returned if the transit system was successfully installed.
`202 ACCEPTED`      | For asynchronous installs, returned if the install is successfully triggered.
`400 BAD REQUEST`   | Returned if the YAML configuration file cannot be retrieved. For synchronous installs, this code is also returned if there is any kind of install error.

### Uninstall a system

`DELETE /systems/<system_id>`


The uninstall can be performed asynchronously or synchronously (using the
optional URL parameter `sync=true`).

You should almost always use the asynchronous version of this endpoint.
It works by changing the system ID to be a new "random" ID, and then performs
the delete asynchronously.
This means that at soon as the asynchronous request ends (within a few milliseconds)
the system ID is available.

The actual delete takes up to a few minutes for large transit systems like
the NYC Subway.

Return code         | Description
--------------------|-------------
`202 ACCEPTED`      | For asynchronous deletes, returned if the delete is successfully triggered.
`204 NO CONTENT`    | For synchronous deletes, returned if the system was successfully deleted.
`404 NOT FOUND`     | Returned if the system does not exist.

## Stop endpoints

### Search for stops

`POST /stops`


Search for stops in all systems based on their proximity to a geographic root location.
This endpoint can be used, for example, to list stops near a user given the user's location.

It takes three URL parameters:

- `latitude` - the latitude of the root location (required).
- `longitude` - the longitude of the root location (required).
- `distance` - the maximum distance, in meters, away from the root location that stops can be.
            This is optional and defaults to 1000 meters (i.e., 1 kilometer). 1 mile is about 1609 meters.

The result of this endpoint is a list of stops ordered by distance, starting with the stop
closest to the root location.

### Get a stop in a system

`GET /systems/<system_id>/stops/<stop_id>`


Describe a stop in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and stop exist.
`404 NOT FOUND`     | Returned if either the system or the stop does not exist.

### List stops in a system

`GET /systems/<system_id>/stops`


List all the stops in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists.
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

### Search for stops in a system

`POST /systems/<system_id>/stops`


Search for stops in a system based on their proximity to a geographic root location.
This endpoint can be used, for example, to list stops near a user given the user's location.

It takes three URL parameters:

- `latitude` - the latitude of the root location (required).
- `longitude` - the longitude of the root location (required).
- `distance` - the maximum distance, in meters, away from the root location that stops can be.
            This is optional and defaults to 1000 meters (i.e., 1 kilometer). 1 mile is about 1609 meters.

The result of this endpoint is a list of stops ordered by distance, starting with the stop
closest to the root location.

## Route endpoints

### Get a route in a system

`GET /systems/<system_id>/routes/<route_id>`


Describe a route in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and route exist.
`404 NOT FOUND`     | Returned if either the system or the route does not exist.

### List routes in a system

`GET /systems/<system_id>/routes`


List all the routes in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists.
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

## Trip endpoints

### Get a trip in a route

`GET /systems/<system_id>/routes/<route_id>/trips/<trip_id>`


Describe a trip in a route in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system, route and trip exist.
`404 NOT FOUND`     | Returned if the system, route or trip do not exist.

### List trips in a route

`GET /systems/<system_id>/routes/<route_id>/trips`


List all the realtime trips in a particular route.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system and route exist.
`404 NOT FOUND` | Returned if either the system or the route does not exist.

## Feed endpoints

### List updates for a feed

`GET /systems/<system_id>/feeds/<feed_id>/updates`


List the most recent updates for a feed.
Up to one hundred updates will be listed.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and feed exist.
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

### Perform a feed flush

`POST /systems/<system_id>/feeds/<feed_id>/flush`


The feed flush operation removes all entities from Transiter
that were added through updates for the given feed.
The operation is useful for removing stale data from the database.

Return code         | Description
--------------------|-------------
`201 CREATED`       | Returned if the system and feed exist, in which case the flush is _scheduled_ (and executed in the same thread, if sync).
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

### Get a feed in a system

`GET /systems/<system_id>/feeds/<feed_id>`


Describe a feed in a transit system.

Return code         | Description
--------------------|-------------
`200 OK`            | Returned if the system and feed exist.
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

### Perform a feed update

`POST /systems/<system_id>/feeds/<feed_id>`


Perform a feed update of the given feed.
The response is a description of the feed update.

This endpoint is provided for one-off feed updates and development work.
In general feed updates should instead be scheduled periodically using the transit system configuration;
see the [transit system documentation](systems.md) for more information.

Return code         | Description
--------------------|-------------
`201 CREATED`       | Returned if the system and feed exist, in which case the update is _scheduled_ (and executed in the same thread, if sync).
`404 NOT FOUND`     | Returned if either the system or the feed does not exist.

### List feeds in a system

`GET /systems/<system_id>/feeds`


List all the feeds in a transit system.

Return code     | Description
----------------|-------------
`200 OK`        | Returned if the system with this ID exists.
`404 NOT FOUND` | Returned if no system with the provided ID is installed.

## Transfer config endpoints

### Preview a transfers config

`POST /admin/transfers-config/preview`


This endpoint returns a preview of the transfers that would be created
using a specific config.

URL parameter | type | description
--------------|------|------------
`system_id`   | multiple string values | The system IDs to create transfers between
`distance`    | float | the maximum distance, in meters, between two stops in order for a transfer to be created between them

### List all transfers configs

`GET /admin/transfers-config`


List all of the transfers configs that are installed.

### Create a transfers config

`POST /admin/transfers-config`


This endpoint is identical to the preview endpoint, except that the resulting
transfers are persisted and a new transfer config is created.

### Get a transfers config

`GET /admin/transfers-config/<int:config_id>`



### Update a transfers config

`PUT /admin/transfers-config/<int:config_id>`


This endpoint is identical to the preview endpoint, except that the resulting
transfers are persisted and a new transfer config is created.

### Delete a transfers config

`DELETE /admin/transfers-config/<int:config_id>`


This endpoint deletes the config as well as all transfers associated to the config.

## Admin endpoints

### List scheduler tasks

`GET /admin/scheduler`


List all tasks that are currently being scheduled by the scheduler.

This contains the feed auto update tasks as well as the cron task that trims old feed updates.

### Refresh scheduler tasks

`POST /admin/scheduler`


When this endpoint is hit the scheduler inspects the database and ensures that the right tasks are being scheduled
and with the right periodicity, etc.
This process happens automatically when an event occurs that
potentially requires the tasks list to be changed, like a system install or delete.
This endpoint is designed for the case when an admin manually edits something in the database and
wants the scheduler to reflect that edit.

### Upgrade database

`POST /admin/upgrade`


Upgrades the Transiter database to the schema/version associated to
the Transiter version of the webservice.
This endpoint is used during Transiter updates: after first updating
the Python code (or Docker contains), this endpoint can be hit to
upgrade the database schema.
It has the same effect as the terminal command:

    transiterclt db upgrade

### Transiter health status

`GET /admin/health`


Return Transiter's health status.
This describes whether or not the scheduler and executor cluster are up.
