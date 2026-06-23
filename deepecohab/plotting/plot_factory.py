from itertools import product
from typing import Literal

import networkx as nx
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl

from deepecohab.utils import auxfun_plots


def plot_activity(
	df: pl.DataFrame,
	positions: list[str],
	colors: list[str],
	type_switch: Literal["visits", "time"],
	agg_switch: Literal["sum", "mean"],
) -> go.Figure:
	"""Plots bar graph of sum of cage and tunnel visits or time spent."""
	match type_switch:
		case "visits":
			position_title = "<b>Visits to each position</b>"
			position_y_title = "<b>Number of visits</b>"
		case "time":
			position_title = "<b>Time spent in each position</b>"
			position_y_title = "<b>Time spent [s]</b>"

	match agg_switch:
		case "sum":
			# TODO: Investigate inconsistent px.histogram behavior (if position and animal_id swaped it works as expected)
			# Currently needs this group_by to present as necessary and px.bar
			df = df.group_by("animal_id", "position", maintain_order=True).agg(pl.sum(type_switch))
			fig = px.bar(
				df,
				x="position",
				y=type_switch,
				color="animal_id",
				color_discrete_sequence=colors,
				hover_data=["animal_id", "position", type_switch],
				title=position_title,
				barmode="group",
			)
			fig.update_layout(barcornerradius=10)
			fig.update_traces(marker_line_width=0)
		case "mean":
			fig = px.box(
				df,
				x="position",
				y=type_switch,
				color="animal_id",
				color_discrete_sequence=colors,
				hover_data=["animal_id", "position", "day", type_switch],
				title=position_title,
				boxmode="group",
				points="outliers",
			)
			fig.update_traces(boxmean=True)

	fig.update_layout(legend={"title": "<b>Animal ID</b>"})
	fig.update_xaxes(
		title_text="<b>Position</b>",
		tickvals=[i for i, pos in enumerate(positions)],
		ticktext=[position.capitalize().replace("_", " ") for position in positions],
	)
	fig.update_yaxes(title_text=position_y_title)

	return fig


def plot_animal_speed(
	df: pl.DataFrame, animals: list[str], colors: list[str]
) -> go.Figure:
	"""Plot the distribution of valid tunnel-crossing speeds per animal."""
	fig = px.violin(
		df,
		x="animal_id",
		y="speed_cm_s",
		color="animal_id",
		color_discrete_map=dict(zip(animals, colors, strict=False)),
		category_orders={"animal_id": animals},
		hover_data=["day", "phase", "position", "time_spent", "crossings"],
		title="<b>Tunnel-crossing speed</b>",
		points="outliers",
		box=True,
	)
	fig.update_layout(showlegend=False)
	fig.update_xaxes(title_text="<b>Animal ID</b>")
	fig.update_yaxes(title_text="<b>Speed [cm/s]</b>")

	return fig


def plot_animal_speed_daily(
	df: pl.DataFrame, animals: list[str], colors: list[str]
) -> go.Figure:
	"""Plot mean valid tunnel-crossing speed per animal and day."""
	fig = px.line(
		df,
		x="day",
		y="mean_speed_cm_s",
		color="animal_id",
		markers=True,
		color_discrete_map=dict(zip(animals, colors, strict=False)),
		category_orders={"animal_id": animals},
		title="<b>Mean tunnel-crossing speed over days</b>",
	)
	fig.update_layout(legend_title_text="<b>Animal ID</b>")
	fig.update_xaxes(title_text="<b>Day</b>", dtick=1)
	fig.update_yaxes(title_text="<b>Mean speed [cm/s]</b>")

	return fig


def plot_slow_crossings(
	df: pl.DataFrame, animals: list[str], colors: list[str]
) -> go.Figure:
	"""Plot the percentage of tunnel crossings taking over 10 seconds."""
	fig = px.bar(
		df,
		x="animal_id",
		y="slow_percentage",
		color="animal_id",
		color_discrete_map=dict(zip(animals, colors, strict=False)),
		category_orders={"animal_id": animals},
		hover_data=["crossings", "slow_crossings"],
		text_auto=".1f",
		title="<b>Slow tunnel crossings (&gt;10 s)</b>",
	)
	fig.update_layout(showlegend=False)
	fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
	fig.update_xaxes(title_text="<b>Animal ID</b>")
	fig.update_yaxes(title_text="<b>Crossings over 10 s [%]</b>", range=[0, 100])

	return fig


def plot_time_alone(
	df: pl.DataFrame, cages: list[str], colors: list[str], agg_switch: Literal["mean", "sum"]
) -> go.Figure:
	"""Plot time alone as a relative bar plot."""
	match agg_switch:
		case "sum":
			fig = px.histogram(
				df,
				x="cage",
				y="time_alone",
				color="animal_id",
				color_discrete_sequence=colors,
				hover_data=["animal_id", "cage", "day", "time_alone"],
				title="<b>Time spent alone</b>",
				barmode="group",
			)
		case "mean":
			fig = px.box(
				df,
				x="cage",
				y="time_alone",
				color="animal_id",
				color_discrete_sequence=colors,
				hover_data=["animal_id", "cage", "day", "time_alone"],
				title="<b>Time spent alone</b>",
				boxmode="group",
				points="outliers",
			)
			fig.update_traces(boxmean=True)

	fig.update_xaxes(
		title_text="<b>Cage</b>",
		tickvals=[i for i, cage in enumerate(cages)],
		ticktext=[cage.capitalize().replace("_", " ") for cage in cages],
	)
	fig.update_yaxes(title_text="<b>Time alone [s]</b>")
	fig.update_layout(
		barcornerradius=10,
		legend_title_text="<b>Animal ID</b>",
	)

	return fig


def plot_sum_line_per_hour(
	df: pl.DataFrame,
	animals: list[str],
	colors: list[str],
	input_type: Literal["activity", "chasings"],
	light_dark: dict[str, float],
	title_suffix: str | None = None,
) -> go.Figure:
	"""Plots line graph for activity or chasings."""
	match input_type:
		case "activity":
			title = "<b>Activity over time</b>"
			y_axes_label = "<b>Antenna detections</b>"
			color_col = "animal_id"
			legend_title = "<b>Animal ID</b>"
		case "chasings":
			title = "<b>Chasing over time</b>"
			y_axes_label = "<b># of chasing events</b>"
			color_col = "chaser"
			legend_title = "<b>Chaser</b>"
	if title_suffix is not None:
		title = f"{title}<br><sup>{title_suffix}</sup>"

	fig = px.line(
		df,
		x="hour",
		y="total",
		color=color_col,
		color_discrete_map=dict(zip(animals, colors, strict=False)),
		category_orders={color_col: animals},
		line_shape="spline",
		title=title,
	)

	fig.update_layout(legend={"title": legend_title})
	fig.update_yaxes(title=y_axes_label)
	fig.update_xaxes(title="<b>Hour of day</b>", range=[0, 23])

	light_onset = light_dark["light_phase"]
	dark_onset = light_dark["dark_phase"]

	fig.add_vline(x=light_onset, line_color="#C85C39", line_dash="dash", line_width=4)
	fig.add_vline(x=dark_onset, line_color="#637DE5", line_dash="dash", line_width=4)

	fig.add_annotation(
		x=(light_onset + 6) % 24,
		y=1.15,
		xref="x",
		yref="paper",
		text="☀️",
		showarrow=False,
		font={"size": 25},
	)

	fig.add_annotation(
		x=(dark_onset + 6) % 24,
		y=1.15,
		xref="x",
		yref="paper",
		text="🌙",
		showarrow=False,
		font={"size": 25},
	)

	fig.update_layout(
		xaxis={"dtick": 1},
		margin={"t": 80},
	)

	return fig


def plot_chasing_trains(df: pl.DataFrame, animals: list[str]) -> go.Figure:
	"""Plot repeated chasing-train frequency for each ordered animal pair."""
	grid = (
		pl.DataFrame(
			product(animals, animals),
			schema=[("chased", pl.String), ("chaser", pl.String)],
			orient="row",
		)
		.join(df, on=["chaser", "chased"], how="left")
		.fill_null(0)
	)
	n_animals = len(animals)
	trains = grid["trains"].to_numpy().reshape(n_animals, n_animals)
	customdata = np.stack(
		[
			grid["events_in_trains"].to_numpy().reshape(n_animals, n_animals),
			grid["mean_train_length"].to_numpy().reshape(n_animals, n_animals),
			grid["max_train_length"].to_numpy().reshape(n_animals, n_animals),
		],
		axis=-1,
	)

	fig = go.Figure(
		go.Heatmap(
			z=trains,
			x=animals,
			y=animals,
			customdata=customdata,
			colorscale="Viridis",
			colorbar={"title": "Trains"},
			hovertemplate=(
				"Chaser: %{x}<br>Chased: %{y}<br>Trains: %{z}"
				"<br>Events in trains: %{customdata[0]}"
				"<br>Mean events/train: %{customdata[1]:.2f}"
				"<br>Longest train: %{customdata[2]}<extra></extra>"
			),
		)
	)
	fig.update_layout(title="<b>Chasing trains (≤10 s pause)</b>")
	fig.update_xaxes(title="<b>Chaser</b>")
	fig.update_yaxes(title="<b>Chased</b>", autorange="reversed")

	return fig


def plot_chasings_daily(
	df: pl.DataFrame, animals: list[str], colors: list[str]
) -> go.Figure:
	"""Plot total cohort chasing events per day, stacked by chaser."""
	fig = px.bar(
		df,
		x="day",
		y="chasing_events",
		color="chaser",
		color_discrete_map=dict(zip(animals, colors, strict=False)),
		category_orders={"chaser": animals},
		title="<b>Total chasing events per day by chaser</b>",
	)
	fig.update_traces(marker_line_width=0)
	fig.update_layout(barcornerradius=10, barmode="stack", legend_title_text="<b>Chaser</b>")
	fig.update_xaxes(title="<b>Day</b>", dtick=1)
	fig.update_yaxes(title="<b>Number of chasing events</b>", rangemode="tozero")

	return fig


def plot_initiated_vs_received_chasings(
	df: pl.DataFrame, animals: list[str], colors: list[str]
) -> go.Figure:
	"""Plot each animal's initiated versus received chasing events."""
	color_map = dict(zip(animals, colors, strict=False))
	maximum = max(df["initiated"].max(), df["received"].max()) or 0
	axis_max = maximum * 1.08 if maximum > 0 else 1

	fig = go.Figure()
	for animal in animals:
		animal_df = df.filter(pl.col("animal_id") == animal)
		if animal_df.is_empty():
			continue
		fig.add_trace(
			go.Scatter(
				x=animal_df["initiated"].to_list(),
				y=animal_df["received"].to_list(),
				mode="markers",
				name=animal,
				text=animal_df["animal_id"].to_list(),
				customdata=animal_df["net_chasing"].to_list(),
				marker={
					"size": 13,
					"color": color_map.get(animal, colors[0]),
					"line": {"color": "rgba(255,255,255,0.35)", "width": 1},
				},
				hovertemplate=(
					"Animal: %{text}<br>"
					"Initiated: %{x:,}<br>"
					"Received: %{y:,}<br>"
					"Net chasing: %{customdata:,}<extra></extra>"
				),
			)
		)
	fig.add_shape(
		type="line",
		x0=0,
		y0=0,
		x1=axis_max,
		y1=axis_max,
		line={"dash": "dash", "color": "rgba(224,230,240,0.55)", "width": 2},
	)
	fig.add_annotation(
		x=axis_max,
		y=axis_max,
		text="equal initiated/received",
		showarrow=False,
		xanchor="right",
		yanchor="bottom",
		font={"size": 11, "color": "rgba(224,230,240,0.75)"},
	)
	fig.update_layout(
		title="<b>Initiated vs received chasing</b>",
		legend_title_text="<b>Animal ID</b>",
		margin={"t": 80},
	)
	fig.update_xaxes(title="<b>Chasing events initiated</b>", range=[0, axis_max])
	fig.update_yaxes(
		title="<b>Chasing events received</b>",
		range=[0, axis_max],
		scaleanchor="x",
		scaleratio=1,
	)

	return fig


def plot_mean_line_per_hour(
	df: pl.DataFrame,
	animals: list[str],
	colors: list[str],
	input_type: Literal["activity", "chasings"],
	light_dark: dict[str, float],
	title_suffix: str | None = None,
) -> go.Figure:
	"""Plots line graph for activity or chasings with SEM shading."""
	match input_type:
		case "activity":
			title = "<b>Activity over time</b>"
			y_axes_label = "<b>Antenna detections</b>"
			animal_col = "animal_id"
		case "chasings":
			title = "<b>Chasing over time</b>"
			y_axes_label = "<b># of chasing events</b>"
			animal_col = "chaser"
	if title_suffix is not None:
		title = f"{title}<br><sup>{title_suffix}</sup>"

	fig = go.Figure()

	for animal, color in zip(animals, colors, strict=False):
		animal_df = df.filter(pl.col(animal_col) == animal)

		x = animal_df["hour"].to_list()
		x_rev = x[::-1]
		y = animal_df["mean"].to_list()
		y_upper = animal_df["upper"].to_list()
		y_lower = animal_df["lower"].to_list()[::-1]

		shade_color = color.replace("rgb", "rgba").replace(")", ", 0.2)")  # shaded region is SEM

		fig.add_trace(
			go.Scatter(
				x=x + x_rev,
				y=y_upper + y_lower,
				fill="toself",
				fillcolor=shade_color,
				line_color="rgba(255,255,255,0)",
				showlegend=False,
				name=animal,
				legendgroup=animal,
				line={"shape": "spline"},
			)
		)

		fig.add_trace(
			go.Scatter(
				x=x,
				y=y,
				line_color=color,
				name=animal,
				legendgroup=animal,
				line={"shape": "spline"},
			)
		)

	fig.update_layout(
		title=title,
		legend={
			"title": "<b>Animal ID</b>",
			"tracegroupgap": 0,
		},
	)
	fig.update_yaxes(title=y_axes_label)
	fig.update_xaxes(title="<b>Hour of day</b>")

	light_onset = light_dark["light_phase"]
	dark_onset = light_dark["dark_phase"]

	fig.add_vline(x=light_onset, line_color="#C85C39", line_dash="dash", line_width=4)
	fig.add_vline(x=dark_onset, line_color="#637DE5", line_dash="dash", line_width=4)

	fig.add_annotation(
		x=(light_onset + 6) % 24,
		y=1.15,
		xref="x",
		yref="paper",
		text="☀️",
		showarrow=False,
		font={"size": 25},
	)

	fig.add_annotation(
		x=(dark_onset + 6) % 24,
		y=1.15,
		xref="x",
		yref="paper",
		text="🌙",
		showarrow=False,
		font={"size": 25},
	)

	fig.update_layout(
		xaxis={"dtick": 1},
		margin={"t": 80},
	)

	return fig


def plot_ranking_line(
	df: pl.DataFrame,
	animals: list[str],
	colors: list[str],
) -> go.Figure:
	"""Plots line graph of ranking over time."""
	fig = px.line(
		df,
		x="datetime",
		y="ordinal",
		color="animal_id",
		color_discrete_map=dict(zip(animals, colors, strict=False)),
	)

	fig.update_layout(
		title="<b>Social dominance ranking in time</b>",
		legend={
			"title": "<b>Animal ID</b>",
			"tracegroupgap": 0,
		},
		xaxis={"title": "<b>Timeline</b>"},
		yaxis={
			"title": "<b>Ranking</b>",
		},
	)

	return fig


def plot_ranking_distribution(
	df: pl.DataFrame,
	animals: list[str],
	colors: list[str],
) -> go.Figure:
	"""Plots line graph of ranking distribution with shaded area."""
	fig = px.line(
		df,
		x="ranking",
		y="probability_density",
		color="animal_id",
		color_discrete_map=dict(zip(animals, colors, strict=False)),
		hover_data=["animal_id", "ranking", "probability_density"],
	)
	fig.update_traces(fill="tozeroy")

	fig.update_layout(
		title="<b>Ranking probability distribution</b>",
		xaxis={
			"title": "<b>Ranking</b>",
		},
		yaxis={
			"title": "<b>Probability density</b>",
		},
		legend={
			"title": "<b>Animal ID</b>",
			"tracegroupgap": 0,
		},
	)

	return fig


def plot_ranking_stability(
	df: pl.DataFrame,
	animals: list[str],
	colors: list[str],
) -> go.Figure:
	"""Plots animal rank on a per day basis."""
	color_map = dict(zip(animals, colors, strict=False))

	fig = go.Figure(
		layout={
			"title_x": 0.5,
			"title": "<b>Daily dominance rank trajectories</b>",
			"legend_title_text": "<b>Animal ID</b>",
			"yaxis": {
				"title": "<b>Rank</b>",
				"autorange": "reversed",
				"type": "category",
				"categoryorder": "array",
				"categoryarray": df["rank"].unique().sort(),
			},
			"xaxis": {
				"title": "<b>Day</b>",
			},
		}
	)
	for animal in animals:
		temp = df.filter(pl.col("animal_id") == animal).sort("day")
		fig.add_trace(
			go.Scatter(
				x=temp["day"],
				y=temp["rank"],
				mode="lines+markers",
				name=animal,
				line={"color": color_map[animal]},
				marker={"color": color_map[animal]},
			)
		)

	return fig


def time_spent_per_cage(df: pl.DataFrame, type: Literal["hourly", "daily"]) -> go.Figure:
	"""Plots N-cages of heatmaps with per hour time spent for each animal."""
	match type:  # TODO: improve column naming consistency to avoid this mess
		case "hourly":
			title = "<b>Time spent per cage</b>"
			x_col = "hour"
			facet_col = "position"
			z_col = "time_in_position"
			x = "Hour: %{x}"
			x_title = "Hour of day"
			z = "Time [min]: %{z}"
			legend_title = "<b>Minutes</b>"
			nbins = 24
		case "daily":
			title = "<b>Cage preference over time</b>"
			x_col = "day"
			facet_col = "position"
			z_col = "time_in_position"
			x = "Day: %{x}"
			x_title = "Day"
			z = "Time [h]: %{z}"
			nbins = None
			legend_title = "<b>Hours</b>"

	fig = px.density_heatmap(
		df,
		x=x_col,
		y="animal_id",
		z=z_col,
		facet_col=facet_col,
		facet_col_wrap=2,
		color_continuous_scale="Viridis",
		nbinsx=nbins,
		title=title,
	)

	for annotation in fig.layout.annotations:
		annotation["text"] = f"<b>Cage {annotation['text'].split('_')[1]}</b>"

	fig.update_layout(
		xaxis={"title": x_title},
		xaxis2={"title": x_title},
		yaxis={"automargin": True, "title": "Animal ID"},
		yaxis3={"automargin": True, "title": "Animal ID"},
		coloraxis_colorbar={"title": {"text": legend_title}},
	)

	fig.update_traces(hovertemplate="<br>".join([x, "Animal ID: %{y}", z]))

	return fig


def plot_heatmap(
	img: np.ndarray,
	animals: list[str],
	input_type: Literal["chasings", "tube_test"],
	title: str | None = None,
	direction_label: str | None = None,
	agg_label: str | None = None,
	train_hover: np.ndarray | None = None,
) -> go.Figure:
	"""Plots heatmap for number of chasings."""
	match input_type:
		case "chasings":
			title = title or "<b>Chasings</b>"
			hover_x = "Chaser: %{x}"
			hover_y = "Chased: %{y}"
			value_label = "Chasing events"
		case "tube_test":
			title = title or "<b>Spontaneous tube-test</b>"
			hover_x = "Winner: %{x}"
			hover_y = "Loser: %{y}"
			value_label = "Tube-test events"

	agg_label = agg_label or "Value"
	direction_label = direction_label or "All tunnel directions"
	z_label = f"{value_label}: %{{z}}"

	fig = px.imshow(
		img,
		x=animals,
		y=animals,
		zmin=0,
		color_continuous_scale="Viridis",
		title=title,
	)
	if train_hover is not None:
		fig.update_traces(customdata=train_hover)
		train_lines = [
			"Chasing trains: %{customdata[0]}",
			"Events in trains: %{customdata[1]}",
			"Mean events/train: %{customdata[2]:.2f}",
			"Longest train: %{customdata[3]}",
		]
	else:
		train_lines = []

	fig.update_traces(
		hovertemplate="<br>".join(
			[
				hover_x,
				hover_y,
				f"View: {direction_label}",
				f"Aggregation: {agg_label}",
				z_label,
				*train_lines,
				"<extra></extra>",
			]
		)
	)

	fig.update_layout(yaxis={"automargin": True}, xaxis={"automargin": True})

	return fig


def plot_sociability_heatmap(
	img: np.ndarray,
	type_switch: Literal["pairwise_encounters", "time_together"],
	animals: list[str],
) -> go.Figure:
	"""Plots heatmaps for pairwise encounters or time spent together."""
	match type_switch:
		case "pairwise_encounters":
			pairwise_title = "<b>Number of pairwise encounters</b>"
			pairwise_z_label = "<b>Number: %{z}</b>"
		case "time_together":
			pairwise_title = "<b>Time spent together</b>"
			pairwise_z_label = "<b>Time [s]: %{z}</b>"

	fig = px.imshow(
		img,
		zmin=0,
		x=animals,
		y=animals,
		facet_col=0,
		facet_col_wrap=2,
		color_continuous_scale="Viridis",
		title=pairwise_title,
	)

	for annotation in fig.layout.annotations:
		annotation["text"] = f"<b>Cage {int(annotation['text'].split('=')[1]) + 1}</b>"

	fig.update_traces(
		hovertemplate="<br>".join(
			[
				"X: %{x}",
				"Y: %{y}",
				pairwise_z_label,
			]
		)
	)

	fig.update_layout(yaxis={"automargin": True}, xaxis={"automargin": True})

	return fig


def plot_within_cohort_heatmap(
	img: np.ndarray,
	animals: list[str],
	sociability_switch: Literal["proportion_together", "sociability"],
) -> go.Figure:
	"""Plots heatmap for within-cohort sociability."""
	match sociability_switch:
		case "proportion_together":
			title = "<b>Proportional time spent together</b>"
		case "sociability":
			title = "<b>Within-cohort sociability</b>"

	fig = px.imshow(
		img,
		zmin=0,
		x=animals,
		y=animals,
		color_continuous_scale="Viridis",
		title=title,
	)

	fig.update_traces(
		hovertemplate="<br>".join(
			[
				"X: %{x}",
				"Y: %{y}",
				"Sociability: %{z}",
			]
		)
	)

	fig.update_layout(yaxis={"automargin": True}, xaxis={"automargin": True})

	return fig


def plot_metrics_polar(df: pl.DataFrame, colors: list[str]):
	"""Plots mean z-scores (across animals) of metrics with shading showing SEM as polar plot."""
	fig = go.Figure()

	for i, (name, group) in enumerate(df.partition_by("animal_id", as_dict=True).items()):
		group_closed = pl.concat([group, group.head(1)])
		theta = group_closed["metric"]
		mean = group_closed["mean"]
		upper = group_closed["upper"]
		lower = group_closed["lower"]

		color = colors[i]
		shade_color = color.replace("rgb", "rgba").replace(")", ", 0.2)")
		leg_group = f"group_{name}"

		fig.add_trace(
			go.Scatterpolar(
				r=lower,
				theta=theta,
				mode="lines",
				line={"width": 0, "color": color},
				line_shape="spline",
				legendgroup=leg_group,
				showlegend=False,
				hoverinfo="skip",
				name=f"{name}_lower",
			)
		)

		fig.add_trace(
			go.Scatterpolar(
				r=upper,
				theta=theta,
				mode="lines",
				fill="tonext",
				fillcolor=shade_color,
				line={"width": 0, "color": color},
				line_shape="spline",
				legendgroup=leg_group,
				showlegend=False,
				hoverinfo="skip",
				name=f"{name}_upper",
			)
		)

		fig.add_trace(
			go.Scatterpolar(
				r=mean,
				theta=theta,
				mode="lines",
				line={"color": color, "width": 2},
				line_shape="spline",
				legendgroup=leg_group,
				marker={"size": 6},
				name=f"{name[0]}",
			)
		)

	fig.update_layout(
		title="<b>Animal feature overview</b>",
		title_y=0.95,
		legend_title_text="<b>Animal ID</b>",
		title_x=0.45,
		polar={
			"radialaxis": {
				"visible": True,
				# Series.min/max is typed as a broad union; arithmetic is valid for this numeric column.
				"range": [df["mean"].min() - 0.5, df["mean"].max() + 0.5],  # ty: ignore[unsupported-operator]
			}
		},
		legend={"tracegroupgap": 0},
		showlegend=True,
	)
	fig.update_polars(bgcolor="rgba(0,0,0,0)")

	return fig


def plot_network_graph(
	connections: pl.DataFrame,
	nodes: pl.DataFrame | None,
	animals: list[str],
	colors: list[str],
	graph_type: Literal["chasings", "proportion_together"],
) -> go.Figure:
	"""Plots network graph of social structure."""
	match graph_type:
		case "chasings":
			edge_weight = "chasings"
			graph = nx.DiGraph
			title = "<b>Dominance network graph</b>"
			include_ranking = True
		case "proportion_together":
			edge_weight = "proportion_together"
			graph = nx.Graph
			title = "<b>Sociability network graph</b>"
			include_ranking = False

	G = nx.from_pandas_edgelist(connections, create_using=graph, edge_attr=edge_weight)
	pos = nx.spring_layout(G, k=0.1, iterations=50, seed=42, weight=edge_weight, method="energy")

	for animal in animals:
		match graph_type:
			case "chasings":
				assert nodes is not None, "Ranking nodes are required for a chasings network graph."
				ordinal = nodes.filter(pl.col("animal_id") == animal).select("ordinal").item()
			case "proportion_together":
				ordinal = 30
		pos[animal] = np.append(pos[animal], ordinal)

	edge_trace = auxfun_plots.create_edges_trace(G, pos, edge_weight=edge_weight)
	node_trace = auxfun_plots.create_node_trace(pos, colors, animals, include_ranking)

	fig = go.Figure(
		data=[*edge_trace, node_trace],
		layout=go.Layout(
			showlegend=False,
			hovermode="closest",
			title={"text": title, "x": 0.5, "y": 0.95},
		),
	)

	fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, automargin=True)
	fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, automargin=True)

	return fig


def plot_social_stability(
	df: pl.DataFrame | None,
	animals: list[str],
	colors: list[str],
) -> go.Figure:
	"""Plots the stability of a social relationship based on time spent together."""
	fig = px.scatter(
		df,
		x="stability",
		y="proportion_together",
		color="animal_id",
		color_discrete_map=dict(zip(animals, colors, strict=False)),
		hover_data={"animal_id_2"},
		range_x=[0, 1],
		range_y=[0, 1],
		range_color=[0, 1],
		title="<b>Relationship stability</b>",
	)

	fig.update_layout(
		xaxis={"title": "<b>Relationship stability</b>"},
		yaxis={"title": "<b>Median proportion together</b>"},
		legend_title_text="<b>Animal ID</b>",
	)
	fig.update_traces(marker_size=12)

	return fig


def plot_cage_preference(
	df: pl.DataFrame | None,
	cages: list[str],
	colors: list[str],
) -> go.Figure:
	"""Plots cage preference on a per cage basis (cohort preference summary)."""
	fig = px.box(
		df,
		x="position",
		y="time_in_position",
		color="position",
		points="outliers",
		hover_data={"animal_id", "day"},
		color_discrete_map=dict(zip(cages, colors, strict=False)),
		title="<b>Cage preference</b>",
	)

	fig.update_traces(boxmean=True)
	fig.update_yaxes(title_text="<b>Avg time per day [h]</b>")
	fig.update_xaxes(
		title_text="<b>Cages</b>",
		tickvals=[i for i, cage in enumerate(cages)],
		ticktext=[cage.capitalize().replace("_", " ") for cage in cages],
	)
	fig.update_layout(legend={"title": ""})

	return fig
