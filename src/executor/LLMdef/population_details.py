import rasterio
import rasterio.windows
import numpy as np

# Radius in raster cells for aggregation (~50 cells ≈ 5 km at 100 m/pixel)
_RADIUS = 50

def get_population_from_worldpop(lat, lon):
    with rasterio.open("./data/nepal_population.tif") as src:
        row, col = src.index(lon, lat)
        window = rasterio.windows.Window(
            col - _RADIUS, row - _RADIUS,
            2 * _RADIUS + 1, 2 * _RADIUS + 1
        )
        data = src.read(1, window=window, boundless=True, fill_value=0)
        nodata = src.nodata
        if nodata is not None:
            data = np.where(data == nodata, 0, data)
        population = float(np.sum(data[data > 0]))
        return population

if __name__ == "__main__":
    lat = 27.8667
    lon = 84.9167
    population = get_population_from_worldpop(lat, lon)
    print(f"Estimated population at ({lat}, {lon}): {population}")