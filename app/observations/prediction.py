from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


FEATURE_COLUMNS = (
    'Max_Temp_C',
    'Humidity_Pct',
    'Wind_Speed_kmh',
    'Rainfall_mm',
    'Slope_Angle_Deg',
    'Vegetation_Cover',
)
MODEL_PATH = (
    Path(settings.BASE_DIR).parent
    / 'notebooks'
    / 'landslide_logistic_pipeline.joblib'
)


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.is_file():
        raise ImproperlyConfigured(
            f'Landslide prediction model not found: {MODEL_PATH}'
        )

    model = joblib.load(MODEL_PATH)
    model_features = tuple(getattr(model, 'feature_names_in_', ()))
    if model_features != FEATURE_COLUMNS:
        raise ImproperlyConfigured(
            'Landslide prediction model features do not match the API inputs.'
        )
    return model


def predict_landslide(observation):
    model_input = pd.DataFrame(
        [
            {
                'Max_Temp_C': observation['max_temp_c'],
                'Humidity_Pct': observation['humidity_pct'],
                'Wind_Speed_kmh': observation['wind_speed_kmh'],
                'Rainfall_mm': observation['rainfall_mm'],
                'Slope_Angle_Deg': observation['slope_angle_deg'],
                'Vegetation_Cover': observation['vegetation_cover'],
            }
        ],
        columns=FEATURE_COLUMNS,
    )
    model = load_model()
    prediction = int(model.predict(model_input)[0])
    positive_class_index = list(model.classes_).index(1)
    probability = float(model.predict_proba(model_input)[0, positive_class_index])

    return {
        'landslide_prediction': 'Yes' if prediction == 1 else 'No',
        'landslide_probability': round(probability, 4),
    }
