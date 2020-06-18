# Feed parser types reference
Feed parsers can return one of 9 types:

- [Agency](#agency)

- [Alert](#alert)

- [DirectionRule](#directionrule)

- [Route](#route)

- [ScheduledService](#scheduledservice)

- [Stop](#stop)

- [Transfer](#transfer)

- [Trip](#trip)

- [Vehicle](#vehicle)

## Agency

Represents a transit system agency.
This type corresponds closely to the GTFS Static `agency.txt` table.

As in GTFS Static, the timezone field is mandatory.
If the system this agency is imported into has no timezone, the system timezone
will be set to the agency timezone.

Name | Type
-----|-----
id* | String.
name* | String.
url* | String.
timezone* | String.
language | String.
phone | String.
fare_url | String.
email | String.

*required
## Alert

Represents an alert in the system.
This type closely corresponds to the GTFS Realtime `Alert` type.

Name | Type
-----|-----
id* | String.
cause | Enum constant of type `transiter.parse.Alert.Cause`; admissible values are: `UNKNOWN_CAUSE`, `OTHER_CAUSE`, `TECHNICAL_PROBLEM`, `STRIKE`, `DEMONSTRATION`, `ACCIDENT`, `HOLIDAY`, `WEATHER`, `MAINTENANCE`, `CONSTRUCTION`, `POLICE_ACTIVITY`, `MEDICAL_EMERGENCY`. Default is `UNKNOWN_CAUSE`.
effect | Enum constant of type `transiter.parse.Alert.Effect`; admissible values are: `NO_SERVICE`, `REDUCED_SERVICE`, `SIGNIFICANT_DELAYS`, `DETOUR`, `ADDITIONAL_SERVICE`, `MODIFIED_SERVICE`, `OTHER_EFFECT`, `UNKNOWN_EFFECT`, `STOP_MOVED`. Default is `UNKNOWN_EFFECT`.
created_at | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
updated_at | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
sort_order | Integer.
messages | List of objects of type `AlertMessage`
active_periods | List of objects of type `AlertActivePeriod`
agency_ids | List of string foreign key references to the `id` attribute of the `Agency` class.
route_ids | List of string foreign key references to the `id` attribute of the `Route` class.
route_types | List of enum constants of type `transiter.parse.Route.Type`; admissible values are: `LIGHT_RAIL`, `SUBWAY`, `RAIL`, `BUS`, `FERRY`, `CABLE_CAR`, `GONDOLA`, `FUNICULAR`, `TROLLEYBUS`, `MONORAIL`.
trip_ids | List of string foreign key references to the `id` attribute of the `Trip` class.
stop_ids | List of string foreign key references to the `id` attribute of the `Stop` class.

*required
### AlertMessage

Represents the message of an alert.

Name | Type
-----|-----
header* | String.
description* | String.
url | String.
language | String.

*required
### AlertActivePeriod

Represents the active period of an alert.
In general in Transiter, alerts are only returned if the curren time is
contained in one of the alert's active periods.

Name | Type
-----|-----
starts_at | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
ends_at | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.

*required
## DirectionRule

DirectionRule(name: str, id: str = None, priority: int = None, stop_id: str = None, direction_id: bool = None, track: str = None)

Name | Type
-----|-----
name* | String.
id | String.
priority | Integer.
stop_id | String.
direction_id | Boolean.
track | String.

*required
## Route

Represents a route in a transit system.
This type corresponds closely to the GTFS Static `routes.txt` table.

The sort_order field is used to order routes, with routes having lower sort_orders
coming first.

Name | Type
-----|-----
id* | String.
type* | Enum constant of type `transiter.parse.Route.Type`; admissible values are: `LIGHT_RAIL`, `SUBWAY`, `RAIL`, `BUS`, `FERRY`, `CABLE_CAR`, `GONDOLA`, `FUNICULAR`, `TROLLEYBUS`, `MONORAIL`.
agency_id | String foreign key reference to the `id` attribute of the `Agency` class.
short_name | String.
long_name | String.
description | String.
color | String.
text_color | String.
url | String.
sort_order | Integer.
continuous_pickup | Enum constant of type `transiter.parse.BoardingPolicy`; admissible values are: `ALLOWED`, `NOT_ALLOWED`, `COORDINATE_WITH_AGENCY`, `COORDINATE_WITH_DRIVER`. Default is `NOT_ALLOWED`.
continuous_drop_off | Enum constant of type `transiter.parse.BoardingPolicy`; admissible values are: `ALLOWED`, `NOT_ALLOWED`, `COORDINATE_WITH_AGENCY`, `COORDINATE_WITH_DRIVER`. Default is `NOT_ALLOWED`.

*required
## ScheduledService

A scheduled service relates a group of trips with the days those trips run.
The field corresponding to a day of the week is true if the trips run on that day,
and false otherwise. It can also specify additional dates
(`added_dates`) and skipped dates (`removed_dates`) that the trips do and don't
run on, respectively.

It is a combination of the GTFS Static tables `calender.txt` and
`calender_dates.txt`.

Name | Type
-----|-----
id* | String.
monday* | Boolean.
tuesday* | Boolean.
wednesday* | Boolean.
thursday* | Boolean.
friday* | Boolean.
saturday* | Boolean.
sunday* | Boolean.
start_date | Date object.
end_date | Date object.
trips | List of objects of type `ScheduledTrip`
added_dates | List of date objects.
removed_dates | List of date objects.

*required
### ScheduledTrip

Represents a trip in a scheduled service.
This type corresponds closely to the GTFS Static `trips.txt` table.

Name | Type
-----|-----
id* | String.
route_id* | String foreign key reference to the `id` attribute of the `Route` class.
direction_id* | Boolean.
headsign | String.
short_name | String.
block_id | String.
wheelchair_accessible | Enum constant of type `transiter.parse.ScheduledTrip.WheelchairAccessible`; admissible values are: `UNKNOWN`, `ACCESSIBLE`, `NOT_ACCESSIBLE`. Default is `UNKNOWN`.
bikes_allowed | Enum constant of type `transiter.parse.ScheduledTrip.BikesAllowed`; admissible values are: `UNKNOWN`, `ALLOWED`, `NOT_ALLOWED`. Default is `UNKNOWN`.
stop_times | List of objects of type `ScheduledTripStopTime`
frequencies | List of objects of type `ScheduledTripFrequency`

*required
### ScheduledTripStopTime

Contains data on when a specific trip calls at a specific stop.
Corresponds to the GTFS Static `stop_times.txt` table.

Name | Type
-----|-----
stop_id* | String foreign key reference to the `id` attribute of the `Stop` class.
arrival_time* | Time object.
departure_time* | Time object.
stop_sequence* | Integer.
headsign | String.
pickup_type | Enum constant of type `transiter.parse.BoardingPolicy`; admissible values are: `ALLOWED`, `NOT_ALLOWED`, `COORDINATE_WITH_AGENCY`, `COORDINATE_WITH_DRIVER`. Default is `ALLOWED`.
drop_off_type | Enum constant of type `transiter.parse.BoardingPolicy`; admissible values are: `ALLOWED`, `NOT_ALLOWED`, `COORDINATE_WITH_AGENCY`, `COORDINATE_WITH_DRIVER`. Default is `ALLOWED`.
continuous_pickup | Enum constant of type `transiter.parse.BoardingPolicy`; admissible values are: `ALLOWED`, `NOT_ALLOWED`, `COORDINATE_WITH_AGENCY`, `COORDINATE_WITH_DRIVER`. Default is `NOT_ALLOWED`.
continuous_drop_off | Enum constant of type `transiter.parse.BoardingPolicy`; admissible values are: `ALLOWED`, `NOT_ALLOWED`, `COORDINATE_WITH_AGENCY`, `COORDINATE_WITH_DRIVER`. Default is `NOT_ALLOWED`.
shape_distance_traveled | Float.
exact_times | Boolean.

*required
### ScheduledTripFrequency

This type corresponds to the GTFS Static `frequencies.txt` and is used to denote
the 'same' trip running multiple times at a fixed interval.

Name | Type
-----|-----
start_time* | Time object.
end_time* | Time object.
headway* | Integer.
frequency_based | Boolean.

*required
## Stop

Represents a stop in a transit system, like the GTFS Static `stops.txt` table.
A stop can mean different things depending on its type:

- A `BOARDING_AREA` is a physical location within a `PLATFORM` where passengers
    can board a vehicle. It must have a parent stop of type `PLATFORM`.

- A `PLATFORM` generally denotes a place where vehicles can stop.
    Its optional parent stop, if provided, must be a `STATION`.

- A `STATION` often refers to the physical idea of station, containing multiple
    platforms where vehicles can stop.
    In the GTFS Static spec stations can't have parent stops but in Transiter
    they can have a parent stop of type `STATION_GROUP`.

- A `STATION_GROUP` represents a collection of different stations.
    This type does not exist in the GTFS Static spec but is unique to Transiter.
    The station group type is useful when
    distinct "stations" in a feed are actually in the same physical structure,
    and linking them with `Transfer` types is not as meaningful.

- A `ENTRANCE_OR_EXIT` is what it says it is, and it must have a parent stop
    of type `STATION`.

- A `GENERIC_NODE` represent some other point in a station. It must have a parent
    stop of type `STATION`.

Note that none of the "must" statements here are enforced by Transiter.

Name | Type
-----|-----
id* | String.
name* | String.
longitude* | Float.
latitude* | Float.
type* | Enum constant of type `transiter.parse.Stop.Type`; admissible values are: `PLATFORM`, `STATION`, `ENTRANCE_OR_EXIT`, `GENERIC_NODE`, `BOARDING_AREA`, `GROUPED_STATION`.
parent_stop | Object of type `Stop`
code | String.
description | String.
zone_id | String.
url | String.
timezone | String.
wheelchair_boarding | Enum constant of type `transiter.parse.Stop.WheelchairBoarding`; admissible values are: `NOT_SPECIFIED`, `ACCESSIBLE`, `NOT_ACCESSIBLE`. Default is `NOT_SPECIFIED`.
platform_code | String.

*required
## Transfer

Represents an available transfer between two stops.
It is closely connected to the GTFS Static `transfers.txt` table.

Note that the parse and import process can only create transfers between two
stops in the same system. For creating cross-system transfers, see the docs here.

Name | Type
-----|-----
from_stop_id* | String foreign key reference to the `id` attribute of the `Stop` class.
to_stop_id* | String foreign key reference to the `id` attribute of the `Stop` class.
type | Enum constant of type `transiter.parse.Transfer.Type`; admissible values are: `RECOMMENDED`, `COORDINATED`, `POSSIBLE`, `NO_TRANSFER`, `GEOGRAPHIC`. Default is `RECOMMENDED`.
min_transfer_time | Integer.

*required
## Trip

Trip(id: str, route_id: Union[str, NoneType] = None, direction_id: Union[bool, NoneType] = None, schedule_relationship: Trip.ScheduleRelationship = <ScheduleRelationship.UNKNOWN: 10>, start_time: Union[datetime.datetime, NoneType] = None, updated_at: datetime.datetime = None, delay: int = None, stop_times: List[ForwardRef('TripStopTime')] = <factory>)

Name | Type
-----|-----
id* | String.
route_id | String.
direction_id | Boolean.
schedule_relationship | Enum constant of type `transiter.parse.Trip.ScheduleRelationship`; admissible values are: `SCHEDULED`, `ADDED`, `UNSCHEDULED`, `CANCELED`, `REPLACEMENT`, `UNKNOWN`. Default is `UNKNOWN`.
start_time | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
updated_at | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
delay | Integer.
stop_times | List of objects of type `TripStopTime`

*required
### TripStopTime

TripStopTime(stop_id: str, stop_sequence: int = None, schedule_relationship: TripStopTime.ScheduleRelationship = <ScheduleRelationship.SCHEDULED: 0>, arrival_time: datetime.datetime = None, arrival_delay: int = None, arrival_uncertainty: int = None, departure_time: datetime.datetime = None, departure_delay: int = None, departure_uncertainty: int = None, track: str = None)

Name | Type
-----|-----
stop_id* | String.
stop_sequence | Integer.
schedule_relationship | Enum constant of type `transiter.parse.TripStopTime.ScheduleRelationship`; admissible values are: `SCHEDULED`, `SKIPPED`, `NO_DATA`, `UNSCHEDULED`. Default is `SCHEDULED`.
arrival_time | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
arrival_delay | Integer.
arrival_uncertainty | Integer.
departure_time | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
departure_delay | Integer.
departure_uncertainty | Integer.
track | String.

*required
## Vehicle

Vehicle(id: Union[str, NoneType] = None, trip_id: Union[str, NoneType] = None, label: str = None, license_plate: str = None, current_stop_sequence: int = None, current_status: Vehicle.Status = <Status.IN_TRANSIT_TO: 2>, current_stop_id: str = None, latitude: float = None, longitude: float = None, bearing: float = None, odometer: float = None, speed: float = None, updated_at: datetime.datetime = None, congestion_level: Vehicle.CongestionLevel = <CongestionLevel.UNKNOWN_CONGESTION_LEVEL: 0>, occupancy_status: Vehicle.OccupancyStatus = <OccupancyStatus.UNKNOWN: 100>)

Name | Type
-----|-----
id | String.
trip_id | String.
label | String.
license_plate | String.
current_stop_sequence | Integer.
current_status | Enum constant of type `transiter.parse.Vehicle.Status`; admissible values are: `INCOMING_AT`, `STOPPED_AT`, `IN_TRANSIT_TO`. Default is `IN_TRANSIT_TO`.
current_stop_id | String.
latitude | Float.
longitude | Float.
bearing | Float.
odometer | Float.
speed | Float.
updated_at | Datetime object. If no timezone is provided, the importer will add the timezone of the system to it.
congestion_level | Enum constant of type `transiter.parse.Vehicle.CongestionLevel`; admissible values are: `UNKNOWN_CONGESTION_LEVEL`, `RUNNING_SMOOTHLY`, `STOP_AND_GO`, `CONGESTION`, `SEVERE_CONGESTION`. Default is `UNKNOWN_CONGESTION_LEVEL`.
occupancy_status | Enum constant of type `transiter.parse.Vehicle.OccupancyStatus`; admissible values are: `EMPTY`, `MANY_SEATS_AVAILABLE`, `FEW_SEATS_AVAILABLE`, `STANDING_ROOM_ONLY`, `CRUSHED_STANDING_ROOM_ONLY`, `FULL`, `NOT_ACCEPTING_PASSENGERS`, `UNKNOWN`. Default is `UNKNOWN`.

*required
