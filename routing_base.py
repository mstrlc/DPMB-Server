import geopandas as gpd
import json
import requests


def query_osm(area_name: str):
    request = f"""
    [out:json][timeout:25];
    area[name="{area_name}"]->.searchArea;
    (
        way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street"]["access"!~"private"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """
    return requests.get(
        f"https://overpass-api.de/api/interpreter?data={request}"
    ).json()


def get_routing_base(area_name: str = "Brno") -> gpd.GeoDataFrame:
    """_summary_

    Args:
        area_name (str): OSM area name, e.g. "Brno"

    Returns:
        gpd.GeoDataFrame: GeoDataFrame with routing base for the area
    """
    # transform json to expected format
    orig_json = query_osm(area_name)
    new_json = {"type": "FeatureCollection", "features": []}

    for feat in orig_json["features"]:
        # get properties useful for routing
        try:
            nazev = feat["properties"]["name"]
        except:
            nazev = ""
        try:
            oneway = feat["properties"]["oneway"]
        except:
            oneway = "no"
        try:
            type = feat["properties"]["highway"]
        except:
            type = ""
        try:
            maxspeed = feat["properties"]["maxspeed"]
        except:
            maxspeed = "0"
        # split current feat with multiple coords into multiple feats with one coord to match the original routing base
        coordinates = feat["geometry"]["coordinates"]
        # take the list of coordinates and transform it to tuples of coordinates [start,end]
        coord_touples = []
        for i in range(len(coordinates) - 1):
            coord_touples.append([coordinates[i], coordinates[i + 1]])
        # create individual features for each coordinate touple
        for i in range(len(coord_touples)):
            new_feat = {
                "type": "Feature",
                "properties": {
                    "nazev": nazev,
                    "oneway": oneway,
                    "type": type,
                    "maxspeed": maxspeed,
                },
                "geometry": {"type": "LineString", "coordinates": coord_touples[i]},
            }
            new_json["features"].append(new_feat)
    # save new json
    with open("./datasets/osm_routing_base.geojson", "w") as outfile:
        json.dump(
            new_json, outfile, ensure_ascii=False
        )  # ensure non-ascii characters are non-escaped as that's not expected
    print("Converting JSON done")
    # load new json
    return gpd.read_file("./datasets/osm_routing_base.geojson")
