import base64
import datetime as dt
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import toml
from dash import ALL, Input, Output, State, callback, ctx, no_update

from deepecohab.app.page_layouts import home_layout
from deepecohab.core import create_data_structure, create_project
from deepecohab.utils.cache_config import launch_cache


def is_valid_time(time_str):
	try:
		dt.time.strptime(str(time_str), "%H:%M:%S")
		return True
	except (ValueError, TypeError):
		return False


dash.register_page(__name__, path="/", name="Home")

layout = home_layout.generate_layout()


@callback(
	Output("load-project-modal", "is_open"),
	Input("load-project", "n_clicks"),
	State("load-project-modal", "is_open"),
	prevent_initial_call=True,
)
def toggle_modal(n_clicks, is_open):
	"""Opens and closes Downloads modal component"""
	if n_clicks:
		return not is_open
	return is_open


@callback(
	Output("opt-collapse", "is_open"),
	Input("opt-btn", "n_clicks"),
	State("opt-collapse", "is_open"),
	prevent_initial_call=True,
)
def toggle_opt(n, is_open):
	return not is_open


@callback(
	Output("layout-checks", "value"), Input("layout-checks", "value"), prevent_initial_call=True
)
def sync_checks(selected):
	if not selected:
		return no_update

	if "field" in selected and "custom" not in selected:
		return selected + ["custom"]

	return no_update


@callback(
	[
		Output("create-project-btn", "disabled"),
		Output({"type": "required-input", "index": ALL}, "valid"),
		Output({"type": "required-input", "index": ALL}, "invalid"),
	],
	Input({"type": "required-input", "index": ALL}, "value"),
	State({"type": "required-input", "index": ALL}, "valid"),
	State({"type": "required-input", "index": ALL}, "invalid"),
	prevent_initial_call=True,
)
def validate_and_highlight(values, current_valid_states, current_invalid_states):
	triggered_id = ctx.triggered_id
	if not triggered_id:
		return no_update

	inputs_info = ctx.inputs_list[0]

	new_valid_states = []
	new_invalid_states = []

	all_technically_valid = []

	for i, item in enumerate(inputs_info):
		idx = item["id"]["index"]
		val = values[i]

		is_empty = not (val and str(val).strip())

		if is_empty:
			is_valid = False
		elif idx in ["proj-loc", "data-loc"]:
			is_valid = Path(str(val)).is_dir()
		elif idx in ["light-start", "dark-start"]:
			is_valid = is_valid_time(val)
		else:
			is_valid = True

		all_technically_valid.append(is_valid)

		if item["id"] == triggered_id:
			new_valid_states.append(is_valid)
			new_invalid_states.append(not is_valid)
		else:
			new_valid_states.append(current_valid_states[i])
			new_invalid_states.append(current_invalid_states[i])

	button_disabled = not all(all_technically_valid)

	return button_disabled, new_valid_states, new_invalid_states


@callback(
	[
		Output("project-config-store", "data", allow_duplicate=True),
		Output("toast-container", "children", allow_duplicate=True),
	],
	Input("create-project-btn", "n_clicks"),
	[
		State({"type": "required-input", "index": "proj-name"}, "value"),
		State({"type": "required-input", "index": "proj-loc"}, "value"),
		State({"type": "required-input", "index": "data-loc"}, "value"),
		State({"type": "required-input", "index": "light-start"}, "value"),
		State({"type": "required-input", "index": "dark-start"}, "value"),
		State("file_ext", "value"),
		State("file_prefix", "value"),
		State("timezone", "value"),
		State("animal-ids", "value"),
		State("layout-checks", "value"),
		State("experiment-start", "value"),
		State("experiment-end", "value"),
		State("sanitize-check", "value"),
		State("min-cross", "value"),
	],
	prevent_initial_call=True,
)
def _create_project(
	n_clicks,
	name,
	loc,
	data,
	light,
	dark,
	ext,  # placeholder for now
	prefix,
	tz,
	animals,
	layouts,
	exp_start,
	exp_end,
	sanitize,
	min_cross,
):
	if n_clicks == 0:
		return no_update

	id_list = [i.strip() for i in animals.split(",")] if animals else None
	is_custom = "custom" in layouts
	is_field = "field" in layouts

	try:
		config_path = create_project.create_ecohab_project(
			project_location=loc,
			data_path=data,
			experiment_name=name,
			light_phase_start=light,
			dark_phase_start=dark,
			animal_ids=id_list,
			custom_layout=is_custom,
			field_ecohab=is_field,
			start_datetime=exp_start,
			finish_datetime=exp_end,
		)

		create_data_structure.get_ecohab_data_structure(
			config_path,
			sanitize_animal_ids=sanitize,
			min_antenna_crossings=int(min_cross),
			fname_prefix=prefix,
			custom_layout=is_custom,
			timezone=tz,
		)
		config_dict = toml.load(config_path)

		if isinstance(config_dict, dict):
			return (
				config_dict,
				dbc.Toast(
					f"Project created at: {config_path}",
					id="project-success-toast",
					header="Success",
					is_open=True,
					dismissable=True,
					icon="success",
					duration=5000,
					class_name="custom-toast",
					style={"width": 350},
				),
			)
		else:
			raise Exception("Couldn't create the EcoHab data structure!")

	except Exception as e:
		return [
			"",
			dbc.Toast(
				f"Error: {str(e)}",
				id="project-error-toast",
				header="Project Creation Failed",
				is_open=True,
				dismissable=True,
				icon="danger",
				style={"width": 350},
				class_name="custom-toast",
			),
		]


@callback(
	[
		Output("project-config-store", "data", allow_duplicate=True),
		Output("load-project-modal", "is_open", allow_duplicate=True),
		Output("toast-container", "children", allow_duplicate=True),
	],
	Input("upload-data", "contents"),
	State("upload-data", "filename"),
	prevent_initial_call=True,
)
def load_config_to_store(contents, filename):
	if not contents:
		return [no_update] * 3

	try:
		content_string = contents.split(",")[-1]
		decoded = base64.b64decode(content_string).decode("utf-8")
		config_dict = toml.loads(decoded)

		return [
			config_dict,
			False,
			dbc.Toast(
				f"Loaded {filename} into session",
				header="Success",
				icon="success",
				duration=3000,
				className="custom-toast",
			),
		]

	except Exception as e:
		error_toast = dbc.Toast(
			f"Error: {str(e)}", header="Load Error", icon="danger", className="custom-toast"
		)
		return [no_update, True, error_toast]


@callback(
	[
		Output("project-config-store", "data", allow_duplicate=True),
		Output("toast-container", "children", allow_duplicate=True),
	],
	Input("clear-session-btn", "n_clicks"),
	prevent_initial_call=True,
)
def clear_app_cache(n_clicks):
	if not n_clicks:
		return no_update, no_update

	launch_cache.clear()
	launch_cache.cull()

	return (
		None,
		dbc.Toast(
			"Session and cache cleared. You can now load a new project.",
			header="System Reset",
			icon="info",
			duration=4000,
			className="custom-toast",
		),
	)


@callback(
	Output("clear-session-btn", "disabled"),
	Input("project-config-store", "data"),
)
def toggle_clear_button(config_data):
	return config_data is None or not config_data
