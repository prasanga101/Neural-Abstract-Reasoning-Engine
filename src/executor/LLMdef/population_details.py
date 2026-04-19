import rasterio

def get_population_from_worldpop(lat, lon):
    with rasterio.open("./data/nepal_population.tif") as src:
        row, col = src.index(lon, lat)  # FIXED
        population = src.read(1)[row, col]
        return population

if __name__ == "__main__":
    lat = 27.8667
    lon = 84.9167
    population = get_population_from_worldpop(lat, lon)
    print(f"Estimated population at ({lat}, {lon}): {population}")