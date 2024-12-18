import geopandas as gpd


def prepare_stats_count(gdf_delay, gdf_route):
    joined_gdf = gpd.sjoin(gdf_route, gdf_delay, op='intersects', how='left')
    joined_gdf = joined_gdf.dropna(subset=['index_right'])
    joined_gdf = joined_gdf[joined_gdf['nazev'] == joined_gdf['street']]
    result_streets_df = joined_gdf.groupby(['nazev']).size().reset_index(name='count')
    return result_streets_df


def get_stats_on_street(gdf_delay, name):
    gdf = gdf_delay[gdf_delay['street'] == name]
    gdf = gdf.groupby(['street']).size().reset_index(name='count')
    return gdf
