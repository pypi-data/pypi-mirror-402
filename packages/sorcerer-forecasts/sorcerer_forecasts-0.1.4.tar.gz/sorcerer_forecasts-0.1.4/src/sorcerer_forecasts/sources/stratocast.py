import xarray
import s3fs
import jwt
import logging
import numpy as np
from datetime import datetime, timedelta, timezone

from sorcerer_forecasts.sources import ForecastSource
from sorcerer_forecasts.utils.region import get_region
from sorcerer_forecasts.entity.forecast import ForecastData
from sorcerer_forecasts.entity.geo import Point4

NUM_LEVELS = 80
RESOLUTION = 0.25
BUCKET = 'sorcerer-forecasts'

REGION_DIR_MAP = {
    'conus': 'oper'
}


class StratocastData(ForecastData):
  pres: float
  u: float
  v: float
  h: float


class Stratocast(ForecastSource[StratocastData]):
  _logger = logging.getLogger(__name__)

  def __init__(self, api_key: str):
    payload = jwt.decode(api_key, options={"verify_signature": False})

    aws_access_key_id = payload['aws_access_key_id']
    aws_secret_access_key = payload['aws_secret_access_key']

    if aws_access_key_id is None or aws_secret_access_key is None:
      raise ValueError("Invalid API key")

    self.demo_user: str | None = payload.get('demo_user')
    self.s3 = s3fs.S3FileSystem(client_kwargs={'aws_access_key_id': aws_access_key_id, 'aws_secret_access_key': aws_secret_access_key})

  def fetch(self, location: Point4):
    forecast_time = location['time'].replace(minute=0, second=0, microsecond=0)
    region = get_region(location)
    region_dir = self.demo_user or REGION_DIR_MAP.get(region.name, region.name)
    forecast_id = self.forecast_id(location)

    self._logger.debug(f"{forecast_id} - FETCH START")

    # Calculate the expected reference time
    expected_ref_time = forecast_time.replace(hour=(forecast_time.hour // 6) * 6)
    expected_path = self._build_forecast_path(region_dir, region.name, expected_ref_time, forecast_time)

    ref_time = expected_ref_time
    forecast_path = expected_path

    if not self.s3.exists(expected_path):
      # Find the latest available reference time

      self._logger.debug(f"{forecast_id} - Expected reftime not found, searching for latest")
      ref_time = self._find_latest_ref_time(region_dir)

      if ref_time is None:
        raise RuntimeError(f"No reference times available for region {region.name}")

      forecast_path = self._build_forecast_path(region_dir, region.name, ref_time, forecast_time)

      if not self.s3.exists(forecast_path):
        raise RuntimeError(f"Forecast not available for {forecast_time} under latest reftime {ref_time}")

    try:
      file = self.s3.open(forecast_path)
      contents = xarray.open_dataset(file, engine='h5netcdf')

      # Rename Time dimension to time
      contents = contents.rename({'Time': 'time'})

      # Add time coordinates with explicit dtype; ensure tz-naive UTC to avoid warnings
      base_time = forecast_time.astimezone(timezone.utc).replace(tzinfo=None) if forecast_time.tzinfo is not None else forecast_time
      times = [base_time + timedelta(minutes=15 * i) for i in range(len(contents.time.values))]
      contents = contents.assign_coords(time=np.array(times, dtype='datetime64[ns]'))

      # Set resolution attribute
      contents.attrs['ref_time'] = ref_time.isoformat()
      contents.attrs['resolution'] = RESOLUTION

      self._logger.debug(f"{forecast_id} - FETCH SUCCESS (reftime: {ref_time})")
      return contents

    except Exception as error:
      self._logger.error(f"{forecast_id} - FETCH FAILED: {error}")
      raise RuntimeError(f"Failed to fetch forecast: {error}")

  def forecast_id(self, location: Point4) -> str:
    forecast_time = location['time'].replace(minute=0, second=0, microsecond=0)
    region = get_region(location)
    return f'{forecast_time.strftime("%Y%m%d")}.t{forecast_time.strftime("%H")}z.stratocast.{str(RESOLUTION).replace(".", "p")}.ml{NUM_LEVELS}.wind.{region.name}'

  def _build_forecast_path(self, region_dir: str, region_name: str, ref_time: datetime, forecast_time: datetime) -> str:
    """Builds the full S3 path for a forecast file."""
    ref_path = f'{BUCKET}/stratocast/{region_dir}/{ref_time.strftime("%Y%m%d")}/{ref_time.strftime("%H")}'
    forecast_file = f'{forecast_time.strftime("%Y%m%d")}.t{forecast_time.strftime("%H")}z.stratocast.{str(RESOLUTION).replace(".", "p")}.ml{NUM_LEVELS}.wind.{region_name}.nc'
    return f's3://{ref_path}/{forecast_file}'

  def _find_latest_ref_time(self, region_dir: str) -> datetime | None:
    """Find the latest available reference time by listing S3 directories."""
    base_path = f's3://{BUCKET}/stratocast/{region_dir}'

    # List all date/hour directories in one request
    ref_times = self.s3.glob(f'{base_path}/*/*')
    if not ref_times:
      return None

    # Parse and return the latest: {bucket}/stratocast/{region_dir}/{YYYYMMDD}/{HH}
    latest = str(sorted(ref_times)[-1])
    parts = latest.split('/')
    return datetime.strptime(f'{parts[-2]}{parts[-1]}', '%Y%m%d%H')
