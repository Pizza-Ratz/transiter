# The Transiter Tour

## Launch Transiter


To begin, we're going to launch Transiter.
The easiest way to do this is with Docker compose and the
    [standard Transiter compose config file](https://github.com/jamespfennell/transiter/blob/master/docker/docker-compose.yml).
Simply run,

    docker-compose up -f path/to/docker-compose.yml

It will take a minute for the images to download from Docker Hub and for the containers to be launched successfully.

When everything is launched, Transiter will be listening on port 8000.
If you navigate to `localhost:8000` in your web browser (or use `curl`), you will find the Transiter landing page,

```json
{
  "transiter": {
    "version": "0.4.5",
    "href": "https://github.com/jamespfennell/transiter",
    "docs": {
      "href": "https://demo.transiter.io/docs/"
    }
  },
  "systems": {
    "count": 0,
    "href": "https://demo.transiter.io/systems"
  }
}
```

As you can see, there are no (transit) systems installed, and the next step is to install one!

??? info "Running Transiter without Docker"
    It's possible to run Transiter on "bare metal" without Docker; 
    the [deployment](deployment.md) page details how.
    It's quite a bit more work though, so for getting started we recommend the Docker approach.

??? info "Building the Docker images locally"
    If you want to build the Docker images locally that's easy, too:
    just check out the [Transiter Git repository](https://github.com/jamespfennell/transiter)
    and in the root of repository run `make docker`.
   
## Install a system

Each deployment of Transiter can have multiple transit systems installed side-by-side.
A transit system is installed using a YAML configuration file that 
    contains basic metadata about the system (like its name),
    the URLs of the data feeds,
    and how to parse those data feeds (GTFS Static, GTFS Realtime, or a custom format).

For this tour, we're going to start by installing the BART system in San Francisco.
The YAML configuration file is stored in Github, you can [inspect it here](https://github.com/jamespfennell/transiter-sfbart/blob/master/Transiter-SF-BART-config.yaml).
The system in installed by sending a `PUT` HTTP request to the desired system ID.
In this case we'll install the system using ID `bart`,

```
curl -X PUT "localhost:8000/systems/bart?sync=true" \
     -F 'config_file=https://raw.githubusercontent.com/jamespfennell/transiter-sfbart/master/Transiter-SF-BART-config.yaml'
```

As you can see, we've provided a `config_file` form parameter that contains the URL of the config file.
It's also possible to provide the config as a file upload using the same `config_file` form parameter.

The request will take a few seconds to complete;
    most of the time is spent loading the BART's schedule into the database.
After it finishes, hit the Transiter landing page again to get,

```json
{
  "transiter": {
    "version": "0.4.5",
    "href": "https://github.com/jamespfennell/transiter",
    "docs": {
      "href": "https://demo.transiter.io/docs/"
    }
  },
  "systems": {
    "count": 1,
    "href": "http://localhost:8000/systems"
  }
}
```

It's installed! 
Next, navigate to the list systems endpoint.
The URL `http://localhost:8000/systems` is helpfully given in the JSON response.
We get,

```json
[
  {
    "id": "bart",
    "status": "ACTIVE",
    "name": "San Francisco BART",
    "href": "http://localhost:8000/systems/bart"
  }
]
```

Now navigating to the system itself, we get,


```json
{
  "id": "bart",
  "status": "ACTIVE",
  "name": "San Francisco BART",
  "agencies": {
    "count": 1,
    "href": "http://localhost:8000/systems/bart/agencies"
  },
  "feeds": {
    "count": 3,
    "href": "http://localhost:8000/systems/bart/feeds"
  },
  "routes": {
    "count": 14,
    "href": "http://localhost:8000/systems/bart/routes"
  },
  "stops": {
    "count": 177,
    "href": "http://localhost:8000/systems/bart/stops"
  },
  "transfers": {
    "count": 0,
    "href": "http://localhost:8000/systems/bart/transfers"
  }
}
```

This is an overview of the system, showing the number of various things like stops and routes,
as well as URLs for those.

## Explore route data

Let's dive into the routes data that Transiter exposes.
Navigating to the list routes endpoint (given above; `http://localhost:8000/systems/bart/routes`)
lists all the routes.
We'll focus on a specific route, the *Berryessa/North San José–Richmond line* or *Orange Line* 
([Wikipedia page](https://en.wikipedia.org/wiki/Berryessa/North_San_Jos%C3%A9%E2%80%93Richmond_line)).
The route ID for this system is `3`, so we can find it by navigating to,

```text
http://localhost:8000/systems/bart/routes/3
```

The start of response will look like this,

```json
{
  "id": "3",
  "color": "FF9933",
  "short_name": "OR-N",
  "long_name": "Berryessa/North San Jose to Richmond",
  "description": "",
  "url": "http://www.bart.gov/schedules/bylineresults?route=3",
  "type": "SUBWAY",
  "periodicity": 7.5,
  "agency": null,
  "alerts": [],
  "service_maps": // service map definitions in here
}
```

Most of the basic data here, such as [the color FF9933](https://www.color-hex.com/color/ff9933),
is taken from the GTFS Static feed.
The *alerts* are taken from the GTFS Realtime feed.
Depending on the current state of the system when you take the tour, this may be empty.
The *periodicity* is calculated by Transiter.
It is the current average time between realtime trips on this route.
If there is insufficient data to calculate the periodicity, it will be `null`.

Arguably the most useful data here, though, are the *service maps*.

### Service maps

When transit consumers think of a route, they often think of the list of stops the route usually calls at.
In our example above, "the Orange Line goes from Richmond to San José."
Even though it's so central to how people think about routes, 
    GTFS does not directly give this kind of information.
However, Transiter has a system for automatically 
    generating such lists of stops using the timetable and realtime data in the GTFS feeds.
They're called *service maps* in Transiter.

Each route can have multiple service maps.
In the BART example there are two maps presented in the routes endpoint: `all-times` and `realtime`:

```json
  "service_maps": [
    {
      "group_id": "all-times",
      "stops": [
        {
          "id": "place_RICH",
          "name": "Richmond",
          "href": "http://localhost:8000/systems/bart/stops/place_RICH"
        },
        {
          "id": "place_DELN",
          "name": "El Cerrito Del Norte",
          "href": "http://localhost:8000/systems/bart/stops/place_DELN"
        },
        // More stops ...
        {
          "id": "place_BERY",
          "name": "Berryessa",
          "href": "http://localhost:8000/systems/bart/stops/place_BERY"
        }
      ]
    },
    {
      "group_id": "realtime",
      "stops": [
        // List of stops ...
      ]
    }
  ]
```

Transiter enables generating service maps from two source:

1. The realtime trips in the GTFS Realtime feeds.
    The `realtime` service map was generated in this way.

1. The timetable in the GTFS Static feeds.
    Transiter can calculate the service maps using every trip in the timetable, like the `all-times` service map.
    Transiter can also calculate service maps for a subset of the timetable - for example, just using
        the weekend trips, or just using the weekday trips.
    (The weekday service map will make an appearance below.)

More information on configuring service maps can be found in the 
    [service maps section](systems.md#service-maps)
    of the transit system config documentation page.
    
## Explore stop data

Having looked at routes, let's look at some stops data.
The endpoint for the BART transit system (`http://localhost:8000/systems/bart`)


## Search for stops using GPS

## Add cross-system transfers


## Where to go next?
