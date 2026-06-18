from app.cv.density import classify_density
from app.models.schemas import DensityLevel
from app.services.prediction import CrowdPredictor


def test_density_thresholds():
    assert classify_density(0.2) == DensityLevel.safe
    assert classify_density(0.5) == DensityLevel.warning
    assert classify_density(0.7) == DensityLevel.danger
    assert classify_density(0.95) == DensityLevel.critical


def test_predictor_detects_growth():
    predictor = CrowdPredictor()
    for count in [20, 25, 30, 42, 55, 70]:
        predictor.add_observation("cam-1", count)
    predicted, level, growth_rate = predictor.predict("cam-1", capacity=100)
    assert predicted > 70
    assert level in {DensityLevel.danger, DensityLevel.critical}
    assert growth_rate > 0

