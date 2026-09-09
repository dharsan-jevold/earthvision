import numpy as np

from app.geospatial.indices import coverage_fraction, index_stats, ndbi, ndvi, ndwi


def test_ndvi_range_and_known_value():
    nir = np.array([[0.5]])
    red = np.array([[0.1]])
    result = ndvi(nir, red)
    assert np.isclose(result[0, 0], (0.5 - 0.1) / (0.5 + 0.1), atol=1e-6)


def test_ndvi_bare_soil_near_zero():
    # bare soil: red and nir roughly comparable -> NDVI near 0
    nir = np.array([[0.2]])
    red = np.array([[0.18]])
    result = ndvi(nir, red)
    assert -0.2 < result[0, 0] < 0.2


def test_ndwi_water_positive():
    green = np.array([[0.3]])
    nir = np.array([[0.05]])
    result = ndwi(green, nir)
    assert result[0, 0] > 0


def test_ndbi_urban_positive():
    swir1 = np.array([[0.4]])
    nir = np.array([[0.15]])
    result = ndbi(swir1, nir)
    assert result[0, 0] > 0


def test_coverage_fraction():
    arr = np.array([[0.5, 0.1], [0.6, 0.2]])
    frac = coverage_fraction(arr, threshold=0.3, above=True)
    assert frac == 0.5


def test_index_stats_keys():
    arr = np.array([[0.1, 0.9], [0.5, 0.3]])
    stats = index_stats(arr)
    assert set(stats.keys()) == {"mean", "min", "max", "std"}
    assert stats["min"] == 0.1
    assert stats["max"] == 0.9
