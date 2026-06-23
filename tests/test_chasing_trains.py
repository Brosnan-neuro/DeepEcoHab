import datetime as dt

import numpy as np
import polars as pl

from deepecohab.utils import auxfun_plots


def test_prep_chasing_trains_groups_only_uninterrupted_same_pair_events():
	start = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
	match_df = pl.DataFrame(
		{
			"winner": ["A", "A", "A", "A", "A", "A", "A"],
			"loser": ["B", "B", "B", "B", "C", "C", "B"],
			"datetime": [
				start + dt.timedelta(seconds=seconds) for seconds in [0, 3, 7, 20, 25, 30, 32]
			],
			"day": [1] * 7,
			"phase": ["light_phase"] * 7,
			"position": ["c2_c1"] * 7,
		}
	)

	result = auxfun_plots.prep_chasing_trains(
		{"match_df": match_df}, [1, 1], ["light_phase"], max_pause_seconds=10
	)

	assert result.to_dicts() == [
		{
			"chaser": "A",
			"chased": "B",
			"trains": 1,
			"events_in_trains": 3,
			"mean_train_length": 3.0,
			"max_train_length": 3,
		},
		{
			"chaser": "A",
			"chased": "C",
			"trains": 1,
			"events_in_trains": 2,
			"mean_train_length": 2.0,
			"max_train_length": 2,
		},
	]


def test_prep_chasing_trains_can_filter_food_cage_direction():
	start = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
	match_df = pl.DataFrame(
		{
			"winner": ["A", "A", "A", "A"],
			"loser": ["B", "B", "B", "B"],
			"datetime": [start + dt.timedelta(seconds=seconds) for seconds in [0, 3, 20, 23]],
			"day": [1] * 4,
			"phase": ["light_phase"] * 4,
			"position": ["c2_c1", "c2_c1", "c1_c2", "c1_c2"],
		}
	)

	toward_food = auxfun_plots.prep_chasing_trains(
		{"match_df": match_df},
		[1, 1],
		["light_phase"],
		max_pause_seconds=10,
		positions=["c2_c1"],
	)
	away_from_food = auxfun_plots.prep_chasing_trains(
		{"match_df": match_df},
		[1, 1],
		["light_phase"],
		max_pause_seconds=10,
		positions=["c1_c2"],
	)

	assert toward_food["events_in_trains"].to_list() == [2]
	assert away_from_food["events_in_trains"].to_list() == [2]


def test_prep_chasings_daily_returns_chaser_totals_and_retains_zero_count_days():
	match_df = pl.DataFrame(
		{
			"winner": ["A", "A", "B", "A"],
			"day": [1, 1, 2, 3],
			"phase": ["light_phase", "light_phase", "light_phase", "dark_phase"],
			"position": ["c2_c1", "c1_c2", "c2_c1", "c2_c1"],
		}
	)

	result = auxfun_plots.prep_chasings_daily(
		{"match_df": match_df}, [1, 3], ["light_phase"]
	)

	assert result.to_dicts() == [
		{"day": 1, "chaser": "A", "chasing_events": 2},
		{"day": 1, "chaser": "B", "chasing_events": 0},
		{"day": 2, "chaser": "A", "chasing_events": 0},
		{"day": 2, "chaser": "B", "chasing_events": 1},
		{"day": 3, "chaser": "A", "chasing_events": 0},
		{"day": 3, "chaser": "B", "chasing_events": 0},
	]


def test_prep_chasings_daily_can_filter_food_cage_direction():
	match_df = pl.DataFrame(
		{
			"winner": ["A", "A", "B"],
			"day": [1, 1, 1],
			"phase": ["light_phase"] * 3,
			"position": ["c2_c1", "c1_c2", "c2_c1"],
		}
	)

	result = auxfun_plots.prep_chasings_daily(
		{"match_df": match_df},
		[1, 1],
		["light_phase"],
		positions=["c2_c1"],
	)

	assert result.to_dicts() == [
		{"day": 1, "chaser": "A", "chasing_events": 1},
		{"day": 1, "chaser": "B", "chasing_events": 1},
	]


def test_prep_initiated_vs_received_chasings_keeps_negative_net_values():
	chasings_df = pl.DataFrame(
		{
			"chaser": ["A", "B", "B"],
			"chased": ["B", "A", "A"],
			"day": [1, 1, 2],
			"phase": ["light_phase", "light_phase", "light_phase"],
			"position": ["c2_c1", "c1_c2", "c2_c1"],
			"chasings": [2, 5, 7],
		}
	)

	result = auxfun_plots.prep_initiated_vs_received_chasings(
		{"chasings_df": chasings_df},
		animals=["A", "B", "C"],
		days_range=[1, 2],
		phase_type=["light_phase"],
	)

	assert result.sort("animal_id").to_dicts() == [
		{"animal_id": "A", "initiated": 2, "received": 12, "net_chasing": -10},
		{"animal_id": "B", "initiated": 12, "received": 2, "net_chasing": 10},
		{"animal_id": "C", "initiated": 0, "received": 0, "net_chasing": 0},
	]


def test_prep_initiated_vs_received_chasings_can_filter_food_cage_direction():
	chasings_df = pl.DataFrame(
		{
			"chaser": ["A", "A", "B"],
			"chased": ["B", "B", "A"],
			"day": [1, 1, 1],
			"phase": ["light_phase"] * 3,
			"position": ["c2_c1", "c1_c2", "c2_c1"],
			"chasings": [2, 3, 5],
		}
	)

	result = auxfun_plots.prep_initiated_vs_received_chasings(
		{"chasings_df": chasings_df},
		animals=["A", "B"],
		days_range=[1, 1],
		phase_type=["light_phase"],
		positions=["c2_c1"],
	)

	assert result.sort("animal_id").to_dicts() == [
		{"animal_id": "A", "initiated": 2, "received": 5, "net_chasing": -3},
		{"animal_id": "B", "initiated": 5, "received": 2, "net_chasing": 3},
	]


def test_prep_chasings_heatmap_can_filter_food_cage_direction():
	chasings_df = pl.DataFrame(
		{
			"chaser": ["A", "A", "B", "B"],
			"chased": ["B", "B", "A", "A"],
			"day": [1, 1, 1, 1],
			"phase": ["light_phase"] * 4,
			"position": ["c2_c1", "c1_c2", "c4_c3", "c3_c4"],
			"chasings": [2, 3, 5, 7],
		}
	)
	store = {"chasings_df": chasings_df}
	animals = ["A", "B"]

	toward_food = auxfun_plots.prep_chasings_heatmap(
		store,
		animals,
		[1, 1],
		["light_phase"],
		"sum",
		positions=["c2_c1", "c4_c3"],
	)
	away_from_food = auxfun_plots.prep_chasings_heatmap(
		store,
		animals,
		[1, 1],
		["light_phase"],
		"sum",
		positions=["c1_c2", "c3_c4"],
	)

	np.testing.assert_array_equal(toward_food, np.array([[0, 5], [2, 0]]))
	np.testing.assert_array_equal(away_from_food, np.array([[0, 7], [3, 0]]))


def test_prep_chasings_line_can_filter_food_cage_direction():
	chasings_df = pl.DataFrame(
		{
			"chaser": ["A", "A", "B", "B"],
			"chased": ["B", "B", "A", "A"],
			"day": [1, 1, 1, 1],
			"hour": [5, 5, 5, 5],
			"position": ["c2_c1", "c1_c2", "c4_c3", "c3_c4"],
			"chasings": [2, 3, 5, 7],
		}
	)
	store = {"chasings_df": chasings_df}
	animals = ["A", "B"]

	toward_food = auxfun_plots.prep_chasings_line(
		store,
		animals,
		[1, 1],
		positions=["c2_c1", "c4_c3"],
	)
	away_from_food = auxfun_plots.prep_chasings_line(
		store,
		animals,
		[1, 1],
		positions=["c1_c2", "c3_c4"],
	)

	toward_hour = toward_food.filter(pl.col("hour") == 5).sort("chaser")
	away_hour = away_from_food.filter(pl.col("hour") == 5).sort("chaser")

	assert toward_hour.select("chaser", "total").to_dicts() == [
		{"chaser": "A", "total": 2},
		{"chaser": "B", "total": 5},
	]
	assert away_hour.select("chaser", "total").to_dicts() == [
		{"chaser": "A", "total": 3},
		{"chaser": "B", "total": 7},
	]


def test_prep_tube_test_heatmap_can_filter_food_cage_direction():
	tube_test_df = pl.DataFrame(
		{
			"winner": ["A", "A", "B", "B"],
			"loser": ["B", "B", "A", "A"],
			"day": [1, 1, 1, 1],
			"phase": ["light_phase"] * 4,
			"position": ["c2_c1", "c1_c2", "c4_c3", "c3_c4"],
			"tube_test": [2, 3, 5, 7],
		}
	)
	store = {"tube_test_df": tube_test_df}
	animals = ["A", "B"]

	toward_food = auxfun_plots.prep_tube_test_heatmap(
		store,
		animals,
		[1, 1],
		["light_phase"],
		"sum",
		positions=["c2_c1", "c4_c3"],
	)
	away_from_food = auxfun_plots.prep_tube_test_heatmap(
		store,
		animals,
		[1, 1],
		["light_phase"],
		"sum",
		positions=["c1_c2", "c3_c4"],
	)

	np.testing.assert_array_equal(toward_food, np.array([[0, 5], [2, 0]]))
	np.testing.assert_array_equal(away_from_food, np.array([[0, 7], [3, 0]]))


def test_prep_tube_test_heatmap_without_position_does_not_fake_direction_filter():
	tube_test_df = pl.DataFrame(
		{
			"winner": ["A", "B"],
			"loser": ["B", "A"],
			"day": [1, 1],
			"phase": ["light_phase", "light_phase"],
			"tube_test": [2, 5],
		}
	)

	result = auxfun_plots.prep_tube_test_heatmap(
		{"tube_test_df": tube_test_df},
		["A", "B"],
		[1, 1],
		["light_phase"],
		"sum",
		positions=["c2_c1", "c4_c3"],
	)

	np.testing.assert_array_equal(result, np.zeros((2, 2)))
