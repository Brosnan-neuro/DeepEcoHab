"""Tunnel speed calculations, configuration and plotting integration."""

import datetime as dt
from types import SimpleNamespace

import polars as pl
import pytest
from pydantic import ValidationError

from deepecohab.core.data_model import Tunnel
from deepecohab.plotting import prepare
from deepecohab.plotting.context import PlotContext
from deepecohab.plotting.registry import PlotRegistry


@pytest.fixture
def context():
	return PlotContext(
		animal_ids=["a", "b"],
		cages=["cage"],
		positions=["cage", "t1", "t2", "undefined"],
		phases={"light_phase": 0, "dark_phase": 12},
		days_range=(1, 3),
		phase_range=(1, 6),
		tunnels_map={"forward": "t1", "reverse": "t1", "other": "t2"},
		tunnel_lengths_cm={"t1": 30, "t2": 60},
		_loaded={"animals": pl.DataFrame({"animal_id": ["a", "b"]})},
	)


def crossings(context, durations, positions=None, days=None, hours=None, phases=None):
	n = len(durations)
	days = days or [1] * n
	context._loaded["main_df"] = pl.DataFrame(
		{
			"animal_id": ["a"] * n,
			"position": positions or ["forward"] * n,
			"time_spent": [dt.timedelta(seconds=s) if s is not None else None for s in durations],
			"day": days,
			"hour": hours or [2] * n,
			"phase_count": [2 * day - 1 for day in days],
			"phase": phases or ["light_phase"] * n,
		}
	)


def test_crossings_use_each_tunnels_length_in_both_directions(context):
	crossings(context, [0.5, 2, 2], ["forward", "reverse", "other"])
	frame = prepare.prep_animal_speed(context, (1, 3), ["light_phase"])
	assert frame["speed_cm_s"].to_list() == [15, 30, 60]
	assert frame["position"].to_list() == ["t1", "t2", "t1"]


def test_duration_cutoff_is_inclusive_and_excludes_invalid_crossings(context):
	crossings(context, [0, -1, None, 10, 10.1, 1, 1], ["forward"] * 5 + ["cage", "undefined"])
	assert prepare.prep_animal_speed(context, (1, 3), ["light_phase"])["speed_cm_s"].to_list() == [
		3
	]
	assert prepare.prep_animal_speed(context, (1, 3), ["light_phase"], max_dwell=11).height == 2


@pytest.mark.parametrize("cutoff", [0, -1, float("nan"), float("inf")])
def test_invalid_cutoff_is_rejected(context, cutoff):
	with pytest.raises(ValueError, match="max_dwell"):
		prepare.prep_animal_speed(context, (1, 3), ["light_phase"], max_dwell=cutoff)


def test_missing_length_does_not_fall_back_to_twenty_cm(context):
	context.tunnel_lengths_cm = {}
	with pytest.raises(ValueError, match="crossing length"):
		prepare.prep_animal_speed(context, (1, 3), ["light_phase"])


def test_filters_select_phase_window_and_hours(context):
	crossings(
		context,
		[1, 2, 3, 4],
		days=[1, 2, 2, 3],
		hours=[2, 2, 3, 2],
		phases=["dark_phase", "light_phase", "light_phase", "light_phase"],
	)
	frame = prepare.prep_animal_speed(context, (3, 3), ["light_phase"], "phase_count", (2, 2))
	assert frame["speed_cm_s"].to_list() == [15]


@pytest.mark.parametrize("granularity", ["day", "phase_count"])
def test_boxes_contain_one_median_per_animal_tunnel_and_window_unit(context, granularity):
	crossings(context, [1, 2, 3, 1], ["forward", "reverse", "forward", "other"])
	frame = prepare.prep_speed_box(context, (1, 3), ["light_phase"], granularity)
	assert frame["speed_cm_s"].to_list() == [15, 60]
	assert frame["position"].to_list() == ["t1", "t2"]
	assert frame[granularity].to_list() == [1, 1]


def test_hourly_mean_weights_observed_day_cells_equally_and_has_sem(context):
	crossings(context, [1, 1, 3], days=[1, 1, 2])
	frame = prepare.prep_speed_line(context, (1, 3), ["light_phase"], "day", "hour")
	row = frame.filter((pl.col("animal_id") == "a") & (pl.col("hour") == 2)).row(0, named=True)
	assert row["mean"] == 20  # means 30 and 10, not a pooled crossing mean of 23.33
	assert row["sem"] == pytest.approx(10)
	assert row["lower"] == pytest.approx(10)
	assert row["upper"] == pytest.approx(30)
	assert frame.filter(pl.col("mean").is_not_null()).height == 1


def test_phase_axis_keeps_empty_bins_null(context):
	crossings(context, [1, 3], days=[1, 2])
	frame = prepare.prep_speed_line(context, (1, 3), ["light_phase"], "phase_count", "phase_count")
	a = frame.filter(pl.col("animal_id") == "a")
	assert a["mean"].to_list() == [30, None, 10]
	assert a["sem"].to_list() == [None, None, None]


def test_box_renderer_groups_by_tunnel(context):
	crossings(context, [1, 2, 3], ["forward", "reverse", "other"])
	figure = PlotRegistry.build("animal-speed", context)
	assert [trace.type for trace in figure.data] == ["box", "box"]
	assert [trace.name for trace in figure.data] == ["t1", "t2"]
	assert list(figure.data[0].y) == [22.5]


def test_mean_renderer_supplies_sem_side_panel_phase_axis_and_events(context):
	crossings(context, [1, 2], hours=[2, 3])
	context._loaded["event_bouts"] = pl.DataFrame(
		{
			"event": pl.Series(["stimulus"], dtype=pl.Enum(["stimulus"])),
			"position": ["t1"],
			"day": [1],
			"phase_count": [1],
			"hour": [2],
		}
	)
	figure = PlotRegistry.build(
		"animal-speed-daily", context, timescale="days", granularity="phase_count"
	)
	assert figure.layout.xaxis.title.text == "<b>Phase</b>"
	assert any(trace.fill == "toself" for trace in figure.data if trace.type == "scatter")
	assert any(trace.xaxis == "x2" for trace in figure.data)
	assert figure.layout.shapes


def test_group_mean_ignores_animals_without_crossings(context):
	crossings(context, [2])
	context.animal_ids.append("c")
	context._loaded["animals"] = pl.DataFrame(
		{"animal_id": ["a", "b", "c"], "sex": ["M", "M", "F"]}
	)
	figure = PlotRegistry.build("animal-speed-daily", context, color_by="sex", group_mean=True)
	line = next(
		trace
		for trace in figure.data
		if trace.type == "scatter" and trace.hoverinfo != "skip" and trace.name == "M"
	)
	assert [v for v in line.y if v is not None] == [15]


@pytest.mark.parametrize("name", ["animal-speed", "animal-speed-daily"])
def test_cutoff_is_exposed_as_plot_option(name):
	options = {option.name: option for option in PlotRegistry.spec(name).options}
	assert options["max_dwell"].default == 10


def tunnel(**extra):
	return Tunnel(
		name="t1", tunnel_no=1, start_cell_id="c1", end_cell_id="c2", antennas=["1", "2"], **extra
	)


def test_legacy_tunnel_has_no_assumed_length():
	assert tunnel().length_cm is None


def test_config_roundtrip_retains_distance():
	original = tunnel(length_cm=37.5)
	assert Tunnel.model_validate_json(original.model_dump_json()).length_cm == 37.5


@pytest.mark.parametrize("name", ["animal-speed", "animal-speed-daily"])
def test_empty_selection_has_no_zero_speed_values(context, name):
	crossings(context, [1])
	figure = PlotRegistry.build(name, context, hours_range=(4, 5))
	for trace in figure.data:
		values = trace.x if trace.type == "box" and trace.orientation == "h" else trace.y
		assert not [value for value in values if value is not None]


def test_dwell_control_uses_seconds_and_has_no_percentage_ceiling():
	from dash import Dash

	Dash(__name__, use_pages=True, pages_folder="")
	from deepecohab.app.pages.recording import _option_control

	option = next(o for o in PlotRegistry.spec("animal-speed").options if o.name == "max_dwell")
	control = _option_control("animal-speed", option).children[1]
	assert control.suffix == " s"
	assert control.min > 0
	assert control.max is None


@pytest.mark.parametrize("length", [0, -1, float("nan"), float("inf")])
def test_config_rejects_invalid_distance(length):
	with pytest.raises(ValidationError):
		tunnel(length_cm=length)


def test_context_reads_configured_tunnel_lengths():
	recording = SimpleNamespace(
		cohort=SimpleNamespace(animal_tags=["a"]),
		layout=SimpleNamespace(
			cage_names=[],
			positions_non_directional=["t1"],
			tunnels_map={"forward": "t1"},
			tunnels=[tunnel(length_cm=37.5)],
		),
		timeline=SimpleNamespace(
			phases={"light_phase": dt.time(6)},
			start_from="light_phase",
			days_range=(1, 2),
			phase_range=(1, 4),
		),
	)
	assert PlotContext.from_recording(recording).tunnel_lengths_cm == {"t1": 37.5}
