from pathlib import Path

import diskcache
import polars as pl
from dash import DiskcacheManager

from deepecohab.utils import auxfun

cache_dir = Path(r"\cache")
cache_dir.mkdir(exist_ok=True)

launch_cache = diskcache.Cache(cache_dir)
background_manager = DiskcacheManager(launch_cache)

def get_project_data(config: dict):
	results_path = Path(config["project_location"]) / "results"
	if not results_path.exists():
		return {}

	return {
		name: auxfun.load_ecohab_data(config, name, return_df=True)
		for name in auxfun.df_registry.list_available()
		if "binary" not in str(name)
	}
