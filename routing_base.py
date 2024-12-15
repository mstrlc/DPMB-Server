import geopandas as gpd
import json
import requests
import osm2geojson


def query_osm(area_name: str) -> dict:
    """
    Queries OpenStreetMap (OSM) Overpass API for highway data in a given area.

    Args:
        area_name (str): Name of the area to query, e.g., "Brno".

    Returns:
        dict: Response data from the Overpass API in JSON format.
    """
    query = f"""
    [out:json][timeout:25];
    area[name="{area_name}"]->.searchArea;
    (
        way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street"]["access"!~"private"]["motor_vehicle"!~"no"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """
    url = "https://overpass-api.de/api/interpreter"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(url, data=query, headers=headers)
    response.raise_for_status()  # ensure HTTP request was successful
    json = response.json()

    return osm2geojson.json2geojson(json)


def transform_osm_data(orig_data: dict) -> dict:
    """
    Transforms raw OSM data into a GeoJSON format suitable for routing.

    Args:
        orig_data (dict): Raw OSM data in JSON format.

    Returns:
        dict: Transformed GeoJSON data.
    """
    transformed_data = {"type": "FeatureCollection", "features": []}

    for element in orig_data.get("features", []):
        # extract feature properties with defaults
        name = element["properties"]["tags"].get("name", "")
        oneway = element["properties"]["tags"].get("oneway", "no")
        road_type = element["properties"]["tags"].get("highway", "")
        maxspeed = element["properties"]["tags"].get("maxspeed", "0")

        # assign weight based on road type
        road_weights = {
            "motorway": 1,
            "trunk": 1.2,
            "primary": 1.5,
            "secondary": 2,
            "tertiary": 2.5,
            "unclassified": 3,
            "residential": 4,
            "living_street": 5
        }
        weight = road_weights.get(road_type, 5)
        
        # split coordinates into line segments
        coordinates = element["geometry"]["coordinates"]
        line_segments = [
            [coordinates[i], coordinates[i + 1]] for i in range(len(coordinates) - 1)
        ]

        # create a new feature for each line segment
        for segment in line_segments:
            transformed_data["features"].append(
                {
                    "type": "Feature",
                    "properties": {
                        "nazev": name,
                        "oneway": oneway,
                        "weight": weight,
                        "maxspeed": maxspeed,
                    },
                    "geometry": {"type": "LineString", "coordinates": segment},
                }
            )

    return transformed_data


def save_geojson(data: dict, filepath: str) -> None:
    """
    Saves GeoJSON data to a file.

    Args:
        data (dict): GeoJSON data to save.
        filepath (str): Path to the output file.
    """
    with open(filepath, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, ensure_ascii=False)
    print(f"GeoJSON saved to {filepath}")


def get_routing_base(area_name: str = "Brno") -> gpd.GeoDataFrame:
    """
    Generates a routing base for the specified area using OSM data.

    Args:
        area_name (str): OSM area name, e.g., "Brno".

    Returns:
        gpd.GeoDataFrame: GeoDataFrame with routing base for the area.
    """
    output_path = "./datasets/osm_routing_base.geojson"

    # query OSM data
    raw_data = query_osm(area_name)

    # transform raw OSM data
    transformed_data = transform_osm_data(raw_data)

    # save transformed data to GeoJSON and update the cached hash
    save_geojson(transformed_data, output_path)

    # load GeoJSON into GeoDataFrame
    return gpd.read_file(output_path)
