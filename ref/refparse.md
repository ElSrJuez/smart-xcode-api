
# Xtream Codes API Reference
This document is based on experimentation/discovery, if you find a formal API reference please open a Discussion.

## Authentication
All endpoints require authentication via `username` and `password` query parameters. These must be valid credentials provisioned by the IPTV provider.

**Example:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>
```


## Get Live Stream Categories
Returns a list of available live TV categories.

**Endpoint:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_live_categories
```
**Response:** JSON array of objects with fields:
- `category_id` (string)
- `category_name` (string)
- `parent_id` (integer)


## Get VOD Stream Categories
Returns a list of available Video On Demand (VOD) categories.

**Endpoint:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_vod_categories
```
**Response:** JSON array of objects with fields:
- `category_id` (string)
- `category_name` (string)
- `parent_id` (integer)


## Get Series Categories
Returns a list of available series categories.

**Endpoint:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_series_categories
```
**Response:** JSON array of objects with fields:
- `category_id` (string)
- `category_name` (string)
- `parent_id` (integer)


## Get Live Streams
Returns a list of live streams. Optionally filter by category.

**Endpoints:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_live_streams
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_live_streams&category_id=<CATEGORY_ID>
```
**Parameters:**
- `category_id` (optional, string): Filter streams by category.

**Response:** JSON array of objects with fields:
- `num` (integer)
- `name` (string)
- `stream_type` (string)
- `stream_id` (integer)
- `stream_icon` (string, URL)
- `epg_channel_id` (string or null)
- `added` (string, timestamp)
- `category_id` (string)
- `custom_sid` (string)
- `tv_archive` (integer)
- `direct_source` (string)
- `tv_archive_duration` (integer)


## Get VOD Streams
Returns a list of Video On Demand streams. Optionally filter by category.

**Endpoints:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_vod_streams
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_vod_streams&category_id=<CATEGORY_ID>
```
**Parameters:**
- `category_id` (optional, string): Filter streams by category.


## Get Series Streams
Returns a list of series streams. Optionally filter by category.

**Endpoints:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_series
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_series&category_id=<CATEGORY_ID>
```
**Parameters:**
- `category_id` (optional, string): Filter series by category.


## Get Series Info
Returns detailed information for a specific series.

**Endpoint:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_series_info&series_id=<SERIES_ID>
```
**Parameters:**
- `series_id` (string): Series identifier.


## Get VOD Info
Returns detailed information for a specific VOD item.

**Endpoint:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_vod_info&vod_id=<VOD_ID>
```
**Parameters:**
- `vod_id` (string): VOD identifier.


## Get Short EPG for Live Streams
Returns a limited set of Electronic Program Guide (EPG) entries for a specific live stream. This endpoint is optimized for quick lookups and returns only a small number of upcoming or current events.

**Endpoints:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_short_epg&stream_id=<STREAM_ID>
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_short_epg&stream_id=<STREAM_ID>&limit=<LIMIT>
```
**Parameters:**
- `stream_id` (string): Stream identifier.
- `limit` (optional, integer): Maximum number of EPG entries to return.

**Response:** JSON object with field:
- `epg_listings`: array of objects with fields:
	- `id` (integer)
	- `epg_id` (integer)
	- `title` (string, base64-encoded)
	- `lang` (string)
	- `start` (string, datetime)
	- `end` (string, datetime)
	- `description` (string, base64-encoded)
	- `channel_id` (string)
	- `start_timestamp` (integer)
	- `stop_timestamp` (integer)


## Get All EPG for Live Streams
Returns the complete Electronic Program Guide (EPG) for a specific live stream.

**Endpoint:**
```
player_api.php?username=<USERNAME>&password=<PASSWORD>&action=get_simple_data_table&stream_id=<STREAM_ID>
```
**Parameters:**
- `stream_id` (string): Stream identifier.


## Get Full EPG List for All Streams
Returns the full EPG for all streams in XMLTV format.

**Endpoint:**
```
xmltv.php?username=<USERNAME>&password=<PASSWORD>
```