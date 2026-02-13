import time

import dash
from dash import Input, Output, State, callback, no_update

from deepecohab.app.page_layouts import analysis_layout
from deepecohab.utils import (
	auxfun,
	cache_config,
)

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

    pipeline_generator = auxfun.df_registry.run_pipeline(
        config, 
        minimum_time=min_time,
        chasing_time_window=chasing_window,
    )

    for step_name, current, total in pipeline_generator:
        percent = int((current / total) * 100)
        
        cache_config.launch_cache.set(
            "analysis_status", 
            {"percent": percent, "msg": f"Running {step_name}..."}
        )

    cache_config.launch_cache.set("analysis_status", {"percent": 100, "msg": "Analysis Complete"})
    time.sleep(0.5)
    cache_config.get_project_data(config)
    
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
	status = cache_config.launch_cache.get("analysis_status")
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
