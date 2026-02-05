import time

import dash
from dash import Input, Output, State, callback, no_update

from deepecohab.app.page_layouts import analysis_layout
from deepecohab.utils.auxfun import df_registry
from deepecohab.utils.cache_config import get_project_data, launch_cache

ANALYSIS_STEPS = [
	(df_registry.get_function("activity_df"), "activity_df"),
	(df_registry.get_function("cage_occupancy"), "cage_occupancy"),
	(df_registry.get_function("chasings_df"), "chasings_df"),
	(df_registry.get_function("ranking"), "ranking"),
	(df_registry.get_function("pairwise_meetings"), "pairwise_meetings"),
	(df_registry.get_function("incohort_sociability"), "incohort_sociability"),
	(df_registry.get_function("time_alone"), "time_alone"),
	(df_registry.get_function("pairwise_meetings"), "pairwise_meetings"),
]

dash.register_page(__name__, path="/analysis", name="Analysis")

layout = analysis_layout.generate_layout()


@callback(
	Output("antenna-button", "disabled", allow_duplicate=True),
	Input("project-config-store", "data"),
	prevent_initial_call="initial_duplicate",
)
def update_analysis_page(config):
	if not config:
		return "No project loaded.", True

	return False


@callback(
	[
		Output("progress-interval", "disabled"),
		Output("antenna-button", "disabled", allow_duplicate=True),
	],
	Input("antenna-button", "n_clicks"),
	State("project-config-store", "data"),
	State("styled-numeric-input", "value"),
	State("chasing_window", "value"),
	prevent_initial_call=True,
)
def start_analysis(n_clicks, config, min_time, chasing_window):
	if not n_clicks or not config:
		return no_update, no_update

	launch_cache.set("analysis_status", {"percent": 0, "msg": "Starting..."})
	total_steps = len(ANALYSIS_STEPS)

	for i, (func, name) in enumerate(ANALYSIS_STEPS):
		launch_cache.set(
			"analysis_status",
			{"percent": int((i / total_steps) * 100), "msg": f"Running {name}..."},
		)

		if name == "pairwise_meetings":
			func(config, minimum_time=min_time if min_time else 2)
		elif name == "chasings_df":
			func(config, chasing_time_window=chasing_window)
		else:
			func(config)

		new_percent = int(((i + 1) / total_steps) * 100)
		launch_cache.set("analysis_status", {"percent": new_percent, "msg": f"Finished {name}"})

	time.sleep(0.5)
	get_project_data(config)

	return True, True


@callback(
	[
		Output("analysis-progress", "value"),
		Output("analysis-progress", "label"),
		Output("analysis-progress", "color"),
		Output("progress-text", "children"),
	],
	Input("progress-interval", "n_intervals"),
)
def update_progress_bar(n):
	status = launch_cache.get("analysis_status")
	if not status:
		return 0, "", "primary", ""

	percent = status.get("percent", 0)
	msg = status.get("msg", "")
	color = "success" if percent == 100 else "primary"

	return percent, f"{percent}%" if percent > 5 else "", color, msg


@callback(
	Output("progress-interval", "disabled", allow_duplicate=True),
	Input("antenna-button", "n_clicks"),
	prevent_initial_call=True,
)
def enable_interval(n):
	if n:
		return False
	return no_update
