from typing import Literal

import numpy as np
import plotly.graph_objects as go
import polars as pl

from deepecohab.core.registries import plot_registry
from deepecohab.plotting import plot_factory
from deepecohab.utils import auxfun_plots
from deepecohab.utils.auxfun_plots import PlotConfig

__all__ = ["PlotConfig", "plot_registry"]


@plot_registry.register("cage-preference")
def cage_preference(
	store: dict,
	phase_type: list[str],
	days_range: list[int],
	cages: list[str],
	position_colors: list[str],
) -> go.Figure:
	"""Generates a cage preference box plot."""
	df = auxfun_plots.prep_cage_preference(store, phase_type, days_range)

	return plot_factory.plot_cage_preference(df, cages, position_colors)


@plot_registry.register("cage-preference-evolution")
def cage_preference_evolution(
	store: dict,
	animals: list[str],
	days_range: list[int],
	agg_switch: Literal["sum", "mean"],
	cages: list[str],
) -> go.Figure:
	"""Generates a cage preference box plot."""
	img = auxfun_plots.prep_cage_preference_evolution(store, animals, days_range, agg_switch, cages)

	return plot_factory.time_spent_per_cage(img, type="daily")


@plot_registry.register("metrics-polar-line")
def polar_metrics(
	store: dict,
	days_range: list[int],
	phase_type: list[str],
	animal_colors: list[str],
) -> go.Figure:
	"""Generates a polar (radar) plot comparing various social dominance metrics.

	Visualizes z-scored values for chasing behavior, activity levels, and social
	proximity (time alone vs. together) for each animal on a unified circular scale.
	"""
	df = auxfun_plots.prep_polar_df(store, days_range, phase_type)

	return plot_factory.plot_metrics_polar(df, animal_colors)


@plot_registry.register("ranking-line")
def ranking_over_time(
	store: dict,
	days_range: list[int],
	animals: list[str],
	animal_colors: list[str],
	ranking_switch: Literal["intime", "stability"],
) -> go.Figure:
	"""Generates ranking plots either over time or as day-to-day stability."""
	match ranking_switch:
		case "intime":
			df = auxfun_plots.prep_ranking_over_time(store, days_range)
			return plot_factory.plot_ranking_line(df, animals, animal_colors)

		case "stability":
			df = auxfun_plots.prep_ranking_day_stability(store, days_range)
			return plot_factory.plot_ranking_stability(df, animals, animal_colors)


@plot_registry.register("ranking-distribution-line")
def ranking_distribution(
	store: dict,
	days_range: list[int],
	animals: list[str],
	animal_colors: list[str],
) -> go.Figure:
	"""Generates a line plot of the ranking probability distributions.

	Fits and displays the probability density functions (PDF) for each animal's
	ranking based on Mu and Sigma values for the final day in the selected range.
	"""
	df = auxfun_plots.prep_ranking_distribution(store, days_range)

	return plot_factory.plot_ranking_distribution(df, animals, animal_colors)


@plot_registry.register("network-dominance")
def network_dominance(
	store: dict,
	animals: list[str],
	days_range: list[int],
	animal_colors: list[str],
) -> go.Figure:
	"""Generates a social dominance network graph of animal interactions.

	Visualizes hierarchy and aggression where node size represents ranking
	and edges represent the sum of chasing events in a directional fashion.
	"""
	connections, nodes = auxfun_plots.prep_network_dominance(store, animals, days_range)

	return plot_factory.plot_network_graph(connections, nodes, animals, animal_colors, "chasings")


@plot_registry.register("tube-test-heatmap")
def tube_test_heatmap(
	store: dict,
	animals: list[str],
	days_range: list[int],
	phase_type: list[str],
	agg_switch: Literal["sum", "mean"],
	food_cage_direction_switch: Literal["overall", "toward_food", "away_food"],
) -> go.Figure:
	"""Generates a chaser-vs-chased interaction heatmap.

	Displays a matrix of agonistic interactions, where rows and columns represent
	individual animals and cells show the sum or mean of chasing events. Columns
	represent Chasers and rows represent Chased.
	"""
	match food_cage_direction_switch:
		case "toward_food":
			positions = ["c2_c1", "c4_c1", "c2_c3", "c4_c3"]
			title = "<b>Spontaneous tube-test toward food cages</b>"
			direction_label = "Toward food cages 1 and 3"
		case "away_food":
			positions = ["c1_c2", "c3_c2", "c1_c4", "c3_c4"]
			title = "<b>Spontaneous tube-test away from food cages</b>"
			direction_label = "Away from food cages 1 and 3"
		case _:
			positions = None
			title = "<b>Spontaneous tube-test</b>"
			direction_label = "All tunnel directions"

	if positions is not None and "position" not in store["tube_test_df"].columns:
		title = "<b>Spontaneous tube-test direction unavailable</b>"
		direction_label = "All tunnel directions; cached tube_test_df has no position column"

	img = auxfun_plots.prep_tube_test_heatmap(
		store,
		animals,
		days_range,
		phase_type,
		agg_switch,
		positions=positions,
	)

	return plot_factory.plot_heatmap(
		img,
		animals,
		input_type="tube_test",
		title=title,
		direction_label=direction_label,
		agg_label=agg_switch.title(),
	)


@plot_registry.register("chasings-heatmap")
def chasings_heatmap(
	store: dict,
	animals: list[str],
	days_range: list[int],
	phase_type: list[str],
	agg_switch: Literal["sum", "mean"],
	food_cage_direction_switch: Literal["overall", "toward_food", "away_food"],
) -> go.Figure:
	"""Generates a chaser-vs-chased interaction heatmap.

	Displays a matrix of agonistic interactions, where rows and columns represent
	individual animals and cells show the sum or mean of chasing events. Columns
	represent Chasers and rows represent Chased.
	"""
	match food_cage_direction_switch:
		case "toward_food":
			positions = ["c2_c1", "c4_c1", "c2_c3", "c4_c3"]
			title = "<b>Chasings toward food cages</b>"
			direction_label = "Toward food cages 1 and 3"
		case "away_food":
			positions = ["c1_c2", "c3_c2", "c1_c4", "c3_c4"]
			title = "<b>Chasings away from food cages</b>"
			direction_label = "Away from food cages 1 and 3"
		case _:
			positions = None
			title = "<b>Chasings</b>"
			direction_label = "All tunnel directions"

	img = auxfun_plots.prep_chasings_heatmap(
		store,
		animals,
		days_range,
		phase_type,
		agg_switch,
		positions=positions,
	)
	trains = auxfun_plots.prep_chasing_trains(
		store, days_range, phase_type, positions=positions
	)
	train_grid = (
		pl.DataFrame(
			[(chased, chaser) for chased in animals for chaser in animals],
			schema=[("chased", pl.String), ("chaser", pl.String)],
			orient="row",
		)
		.join(trains, on=["chaser", "chased"], how="left")
		.fill_null(0)
	)
	train_hover = np.stack(
		[
			train_grid["trains"].to_numpy().reshape(len(animals), len(animals)),
			train_grid["events_in_trains"].to_numpy().reshape(len(animals), len(animals)),
			train_grid["mean_train_length"].to_numpy().reshape(len(animals), len(animals)),
			train_grid["max_train_length"].to_numpy().reshape(len(animals), len(animals)),
		],
		axis=-1,
	)

	return plot_factory.plot_heatmap(
		img,
		animals,
		input_type="chasings",
		title=title,
		direction_label=direction_label,
		agg_label=agg_switch.title(),
		train_hover=train_hover,
	)


@plot_registry.register("chasings-line")
def chasings_line(
	store: dict,
	animals: list[str],
	days_range: list[int],
	animal_colors: list[str],
	agg_switch: Literal["sum", "mean"],
	light_dark_onset: dict[str, float],
	food_cage_direction_switch: Literal["overall", "toward_food", "away_food"],
) -> go.Figure:
	"""Generates a line plot of chasing frequency per hour.

	Shows the diurnal rhythm of aggression. For mean includes a shaded area representing
	the Standard Error of the Mean (SEM) across the selected days.
	"""
	match food_cage_direction_switch:
		case "toward_food":
			positions = ["c2_c1", "c4_c1", "c2_c3", "c4_c3"]
			title_suffix = "Toward food cages 1 and 3"
		case "away_food":
			positions = ["c1_c2", "c3_c2", "c1_c4", "c3_c4"]
			title_suffix = "Away from food cages 1 and 3"
		case _:
			positions = None
			title_suffix = "All tunnel directions"

	df = auxfun_plots.prep_chasings_line(store, animals, days_range, positions=positions)

	match agg_switch:
		case "sum":
			return plot_factory.plot_sum_line_per_hour(
				df,
				animals,
				animal_colors,
				"chasings",
				light_dark_onset,
				title_suffix=title_suffix,
			)
		case "mean":
			return plot_factory.plot_mean_line_per_hour(
				df,
				animals,
				animal_colors,
				"chasings",
				light_dark_onset,
				title_suffix=title_suffix,
			)


@plot_registry.register("chasings-daily")
def chasings_daily(
	store: dict,
	animals: list[str],
	days_range: list[int],
	phase_type: list[str],
	animal_colors: list[str],
	food_cage_direction_switch: Literal["overall", "toward_food", "away_food"],
) -> go.Figure:
	"""Show total cohort chasing events per day, stacked by chaser."""
	match food_cage_direction_switch:
		case "toward_food":
			positions = ["c2_c1", "c4_c1", "c2_c3", "c4_c3"]
		case "away_food":
			positions = ["c1_c2", "c3_c2", "c1_c4", "c3_c4"]
		case _:
			positions = None

	df = auxfun_plots.prep_chasings_daily(store, days_range, phase_type, positions=positions)

	return plot_factory.plot_chasings_daily(df, animals, animal_colors)


@plot_registry.register("initiated-vs-received-chasings")
def initiated_vs_received_chasings(
	store: dict,
	animals: list[str],
	days_range: list[int],
	phase_type: list[str],
	animal_colors: list[str],
	food_cage_direction_switch: Literal["overall", "toward_food", "away_food"],
) -> go.Figure:
	"""Show each animal's chasing events initiated versus received."""
	match food_cage_direction_switch:
		case "toward_food":
			positions = ["c2_c1", "c4_c1", "c2_c3", "c4_c3"]
		case "away_food":
			positions = ["c1_c2", "c3_c2", "c1_c4", "c3_c4"]
		case _:
			positions = None

	df = auxfun_plots.prep_initiated_vs_received_chasings(
		store, animals, days_range, phase_type, positions=positions
	)

	return plot_factory.plot_initiated_vs_received_chasings(df, animals, animal_colors)


@plot_registry.register("activity-bar")
def activity(
	store: dict,
	days_range: list[int],
	phase_type: list[str],
	positions: list[str],
	position_switch: Literal["visits", "time"],
	agg_switch: Literal["sum", "mean"],
	animal_colors: list[str],
) -> go.Figure:
	"""Generates a bar or box plot of animal activity levels by position.

	Quantifies behavior either by the number of visits to specific locations
	or the total time spent in those locations.
	"""
	df = auxfun_plots.prep_activity(store, days_range, phase_type)

	return plot_factory.plot_activity(df, positions, animal_colors, position_switch, agg_switch)


@plot_registry.register("activity-line")
def activity_line(
	store: dict,
	animals: list[str],
	days_range: list[int],
	animal_colors: list[str],
	agg_switch: Literal["sum", "mean"],
	light_dark_onset: dict[str, float],
) -> go.Figure:
	"""Generates a line plot of diurnal activity based on antenna crossings.

	Plots the number of antenna detections per hour, allowing for
	comparison of circadian rhythms between animals. For mean includes a shaded area
	representing the Standard Error of the Mean (SEM) across the selected days.
	"""
	df = auxfun_plots.prep_activity_line(store, animals, days_range)

	match agg_switch:
		case "sum":
			return plot_factory.plot_sum_line_per_hour(
				df, animals, animal_colors, "activity", light_dark_onset
			)
		case "mean":
			return plot_factory.plot_mean_line_per_hour(
				df, animals, animal_colors, "activity", light_dark_onset
			)


@plot_registry.register("animal-speed")
def animal_speed(
	store: dict,
	animals: list[str],
	days_range: list[int],
	phase_type: list[str],
	animal_colors: list[str],
	tunnel_positions: list[str],
) -> go.Figure:
	"""Show the distribution of tunnel-crossing speeds per animal."""
	df = auxfun_plots.prep_animal_speed(store, days_range, phase_type, tunnel_positions)

	return plot_factory.plot_animal_speed(df, animals, animal_colors)


@plot_registry.register("animal-speed-daily")
def animal_speed_daily(
	store: dict,
	animals: list[str],
	days_range: list[int],
	phase_type: list[str],
	animal_colors: list[str],
	tunnel_positions: list[str],
) -> go.Figure:
	"""Show mean valid tunnel-crossing speed per day."""
	df = auxfun_plots.prep_animal_speed_daily(
		store, days_range, phase_type, tunnel_positions
	)

	return plot_factory.plot_animal_speed_daily(df, animals, animal_colors)


@plot_registry.register("slow-crossings")
def slow_crossings(
	store: dict,
	animals: list[str],
	days_range: list[int],
	phase_type: list[str],
	animal_colors: list[str],
	tunnel_positions: list[str],
) -> go.Figure:
	"""Show the share of tunnel crossings that exceed 10 seconds."""
	df = auxfun_plots.prep_slow_crossings(store, days_range, phase_type, tunnel_positions)

	return plot_factory.plot_slow_crossings(df, animals, animal_colors)


@plot_registry.register("time-per-cage-heatmap")
def time_per_cage(
	store: dict,
	animals: list[str],
	days_range: list[int],
	cages: list[str],
	agg_switch: Literal["sum", "mean"],
) -> go.Figure:
	"""Generates a grid of heatmaps showing cage occupancy over 24 hours.

	Creates a subplot for each cage, visualizing when and for how long specific animals
	occupy that space throughout the day.
	"""
	img = auxfun_plots.prep_time_per_cage(store, animals, days_range, agg_switch, cages)

	return plot_factory.time_spent_per_cage(img, type="hourly")


@plot_registry.register("sociability-heatmap")
def pairwise_sociability(
	store: dict,
	animals: list[str],
	phase_type: list[str],
	days_range: list[int],
	cages: list[str],
	agg_switch: Literal["sum", "mean"],
	pairwise_switch: Literal["time_together", "pairwise_encounters"],
) -> go.Figure:
	"""Generates heatmaps of pairwise sociability per cage.

	Visualizes how often pairs of animals meet or spend time together,
	broken down by physical location (cages).
	"""
	img = auxfun_plots.prep_pairwise_sociability(
		store, phase_type, animals, days_range, agg_switch, pairwise_switch, cages
	)

	return plot_factory.plot_sociability_heatmap(img, pairwise_switch, animals)


@plot_registry.register("cohort-heatmap")
def within_cohort_sociability(
	store: dict,
	animals: list[str],
	phase_type: list[str],
	days_range: list[int],
	sociability_switch: Literal["proportion_together", "sociability"],
) -> go.Figure:
	"""Generates a normalized heatmap of sociability within the entire cohort.

	Provides a high-level view of social bonds by calculating the mean
	sociability index between all animal pairs across the specified range.
	"""
	img = auxfun_plots.prep_within_cohort_sociability(
		store, phase_type, animals, days_range, sociability_switch
	)

	return plot_factory.plot_within_cohort_heatmap(img, animals, sociability_switch)


@plot_registry.register("time-alone-bar")
def time_alone(
	store: dict,
	phase_type: list[str],
	days_range: list[int],
	agg_switch: Literal["sum", "mean"],
	animal_colors: list[str],
	cages: list[str],
) -> go.Figure:
	"""Generates a stacked bar plot of time spent alone.

	Shows the duration each animal spent without any other animals present,
	segmented by the specific cages where this behavior occurred.
	"""
	df = auxfun_plots.prep_time_alone(store, phase_type, days_range)

	return plot_factory.plot_time_alone(df, cages, animal_colors, agg_switch)


@plot_registry.register("network-sociability")
def network_sociability(
	store: dict,
	animals: list[str],
	animal_colors: list[str],
	days_range: list[int],
) -> go.Figure:
	"""Generates a social dominance network graph of animal interactions.

	Visualizes hierarchy and aggression where node size represents ranking
	and edges represent the sum of chasing events in a directional fashion.
	"""
	connections = auxfun_plots.prep_network_sociability(store, animals, days_range)

	return plot_factory.plot_network_graph(
		connections, None, animals, animal_colors, "proportion_together"
	)


@plot_registry.register("social-stability")
def social_stability(
	store: dict,
	animals: list[str],
	animal_colors: list[str],
	phase_type: list[str],
	days_range: list[int],
) -> go.Figure:
	"""Generates a social stability scatter plot.

	Visualizes stability of a relationship of every pair across chosen days
	based on proportional time spent together and coefficient of variation like metric
	calculated through median absolute deviation.
	"""
	df = auxfun_plots.prep_social_stability(store, phase_type, days_range)

	return plot_factory.plot_social_stability(df, animals, animal_colors)
