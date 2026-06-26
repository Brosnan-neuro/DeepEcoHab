"""Plot total cohort chasing events per day.

Run with either a project config. By default this creates the recommended
two-panel plot: total daily chasing plus stacked animal/chaser contributions.

    python scripts/total_chasing_events_per_day.py path/to/config.toml --show

Or directly with a match_df parquet:
    python scripts/total_chasing_events_per_day.py path/to/match_df.parquet --show

To show only the stacked animal/chaser contribution:
    python scripts/total_chasing_events_per_day.py path/to/config.toml --stack-by-chaser --show
"""

from __future__ import annotations

import argparse
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl
import toml

from deepecohab.utils import auxfun_plots


PLOT_TEMPLATE = "plotly_white"


def match_df_path(input_path: Path) -> Path:
	"""Resolve config.toml or match_df.parquet to the parquet file path."""
	if input_path.suffix == ".parquet":
		return input_path

	cfg = toml.load(input_path)
	return Path(cfg["project_location"]) / "results" / "match_df.parquet"


def animal_order(input_path: Path, match_df: pl.DataFrame) -> list[str]:
	"""Return project animal order when available, otherwise infer from match_df."""
	if input_path.suffix != ".parquet":
		cfg = toml.load(input_path)
		return [str(animal) for animal in cfg["animal_ids"]]

	return (
		match_df.select(pl.col("winner").cast(pl.String).alias("animal_id"))
		.unique()
		.sort("animal_id")["animal_id"]
		.to_list()
	)


def animal_color_map(animals: list[str]) -> dict[str, str]:
	"""Use the same animal colour palette as the dashboard."""
	return dict(zip(animals, auxfun_plots.color_sampling(animals), strict=False))


def filter_match_df(
	match_df: pl.DataFrame,
	phases: list[str] | None = None,
	first_day: int | None = None,
	last_day: int | None = None,
) -> tuple[pl.DataFrame, int, int]:
	"""Apply the same phase/day filters used for both plot types."""
	df = match_df

	if phases:
		df = df.filter(pl.col("phase").is_in(phases))

	first_day = first_day if first_day is not None else int(df["day"].min())
	last_day = last_day if last_day is not None else int(df["day"].max())
	df = df.filter(pl.col("day").is_between(first_day, last_day))

	return df, first_day, last_day


def total_chasing_events_per_day(
	match_df: pl.DataFrame,
	phases: list[str] | None = None,
	first_day: int | None = None,
	last_day: int | None = None,
) -> pl.DataFrame:
	"""Count total chasing events per day, retaining zero-count days."""
	df, first_day, last_day = filter_match_df(match_df, phases, first_day, last_day)

	counts = (
		df.lazy()
		.group_by("day")
		.len(name="chasing_events")
		.with_columns(pl.col("day").cast(pl.Int64))
	)
	grid = pl.LazyFrame(
		{"day": range(first_day, last_day + 1)},
		schema={"day": pl.Int64},
	)

	return (
		grid.join(counts, on="day", how="left")
		.fill_null(0)
		.sort("day")
		.collect(engine="in-memory")
	)


def chasing_events_per_day_by_chaser(
	match_df: pl.DataFrame,
	phases: list[str] | None = None,
	first_day: int | None = None,
	last_day: int | None = None,
) -> pl.DataFrame:
	"""Count daily chasing events for each animal doing the chasing."""
	df, first_day, last_day = filter_match_df(match_df, phases, first_day, last_day)
	chasers = df.select(pl.col("winner").cast(pl.String)).unique().sort("winner")

	counts = (
		df.lazy()
		.with_columns(pl.col("winner").cast(pl.String))
		.group_by("day", "winner")
		.len(name="chasing_events")
		.rename({"winner": "chaser"})
	)
	grid = (
		pl.LazyFrame({"day": range(first_day, last_day + 1)}, schema={"day": pl.Int64})
		.join(chasers.lazy().rename({"winner": "chaser"}), how="cross")
	)

	return (
		grid.join(counts, on=["day", "chaser"], how="left")
		.fill_null(0)
		.sort("day", "chaser")
		.collect(engine="in-memory")
	)


def style_daily_chasing_figure(fig: go.Figure) -> go.Figure:
	"""Apply shared styling so the graph looks publication/report friendlier."""
	fig.update_layout(
		template=PLOT_TEMPLATE,
		font={"size": 14},
		title={"x": 0.02, "xanchor": "left"},
		bargap=0.18,
		hovermode="x unified",
		legend_title_text="<b>Chaser</b>",
		margin={"l": 70, "r": 30, "t": 70, "b": 60},
	)
	fig.update_traces(marker_line_width=0)
	fig.update_xaxes(
		title="<b>Day</b>",
		dtick=1,
		showgrid=False,
		tickmode="linear",
	)
	fig.update_yaxes(
		title="<b>Number of chasing events</b>",
		rangemode="tozero",
		gridcolor="rgba(0,0,0,0.08)",
	)
	return fig


def plot_daily_chasing(df: pl.DataFrame, rolling_window: int = 3) -> go.Figure:
	"""Plot total cohort chasing events per day with an optional rolling mean."""
	plot_df = df.with_columns(
		pl.col("chasing_events")
		.rolling_mean(window_size=rolling_window, min_samples=1)
		.round(2)
		.alias("rolling_mean")
	)
	fig = go.Figure()
	fig.add_trace(
		go.Bar(
			x=plot_df["day"],
			y=plot_df["chasing_events"],
			name="Total chasing events",
			marker={"color": "rgba(70, 130, 180, 0.72)", "line_width": 0},
			hovertemplate="Day %{x}<br>Total events: %{y:,}<extra></extra>",
		)
	)
	fig.add_trace(
		go.Scatter(
			x=plot_df["day"],
			y=plot_df["rolling_mean"],
			mode="lines+markers",
			name=f"{rolling_window}-day rolling mean",
			line={"color": "black", "width": 3},
			marker={"size": 6},
			hovertemplate="Rolling mean: %{y:.2f}<extra></extra>",
		)
	)
	fig.update_layout(title="<b>Total chasing events per day</b>")
	return style_daily_chasing_figure(fig)


def plot_daily_chasing_by_chaser(
	df: pl.DataFrame, animals: list[str] | None = None
) -> go.Figure:
	"""Plot total daily chasing events as stacked bars by chaser."""
	fig = go.Figure()
	observed_chasers = df["chaser"].unique().sort().to_list()
	chasers = (
		[chaser for chaser in animals if chaser in observed_chasers]
		if animals
		else observed_chasers
	)
	color_map = animal_color_map(animals if animals else chasers)

	add_manually_stacked_chaser_bars(fig, df, chasers, color_map)

	fig.update_layout(title="<b>Total chasing events per day, stacked by chaser</b>")
	fig.update_layout(barmode="overlay")
	return style_daily_chasing_figure(fig)


def add_manually_stacked_chaser_bars(
	fig: go.Figure,
	stacked_df: pl.DataFrame,
	chasers: list[str],
	color_map: dict[str, str],
	row: int | None = None,
	col: int | None = None,
) -> None:
	"""Add visibly stacked chaser bars using explicit bases instead of barmode."""
	days = stacked_df["day"].unique().sort().to_list()
	base_by_day = {day: 0 for day in days}

	for chaser in chasers:
		chaser_df = (
			stacked_df.filter(pl.col("chaser") == chaser)
			.select("day", "chasing_events")
			.sort("day")
		)
		x_values = chaser_df["day"].to_list()
		y_values = chaser_df["chasing_events"].to_list()
		base_values = [base_by_day[day] for day in x_values]

		trace = go.Bar(
			x=x_values,
			y=y_values,
			base=base_values,
			width=0.82,
			name=str(chaser),
			legendgroup=str(chaser),
			showlegend=True,
			marker={"color": color_map[chaser], "line_width": 0},
			hovertemplate=(
				"Day %{x}<br>Chaser: "
				+ str(chaser)
				+ "<br>Events: %{y:,}<extra></extra>"
			),
		)
		if row is None or col is None:
			fig.add_trace(trace)
		else:
			fig.add_trace(trace, row=row, col=col)

		for day, events in zip(x_values, y_values, strict=False):
			base_by_day[day] += events


def plot_daily_chasing_combo(
	total_df: pl.DataFrame,
	stacked_df: pl.DataFrame,
	animals: list[str] | None = None,
	rolling_window: int = 3,
) -> go.Figure:
	"""Plot total daily chasing and stacked-by-chaser contribution together."""
	total_plot_df = total_df.with_columns(
		pl.col("chasing_events")
		.rolling_mean(window_size=rolling_window, min_samples=1)
		.round(2)
		.alias("rolling_mean")
	)
	observed_chasers = stacked_df["chaser"].unique().sort().to_list()
	chasers = (
		[chaser for chaser in animals if chaser in observed_chasers]
		if animals
		else observed_chasers
	)
	color_map = animal_color_map(animals if animals else chasers)

	fig = make_subplots(
		rows=2,
		cols=1,
		shared_xaxes=True,
		vertical_spacing=0.12,
		row_heights=[0.38, 0.62],
		subplot_titles=(
			"Total cohort chasing intensity",
			"Which animal is doing the chasing?",
		),
	)
	fig.add_trace(
		go.Bar(
			x=total_plot_df["day"],
			y=total_plot_df["chasing_events"],
			name="Total chasing events",
			marker={"color": "rgba(70, 130, 180, 0.72)", "line_width": 0},
			hovertemplate="Day %{x}<br>Total events: %{y:,}<extra></extra>",
			showlegend=False,
		),
		row=1,
		col=1,
	)
	fig.add_trace(
		go.Scatter(
			x=total_plot_df["day"],
			y=total_plot_df["rolling_mean"],
			mode="lines+markers",
			name=f"{rolling_window}-day rolling mean",
			line={"color": "black", "width": 3},
			marker={"size": 6},
			hovertemplate="Day %{x}<br>Rolling mean: %{y:.2f}<extra></extra>",
			showlegend=False,
		),
		row=1,
		col=1,
	)

	add_manually_stacked_chaser_bars(fig, stacked_df, chasers, color_map, row=2, col=1)

	fig.update_layout(
		template=PLOT_TEMPLATE,
		title={
			"text": "<b>Daily chasing events and chaser contribution</b>",
			"x": 0.02,
			"xanchor": "left",
		},
		font={"size": 14},
		barmode="overlay",
		bargap=0.18,
		hovermode="x unified",
		legend={
			"title": {"text": "<b>Chaser</b>"},
			"x": 1.02,
			"y": 0.58,
			"xanchor": "left",
			"yanchor": "middle",
			"traceorder": "normal",
		},
		margin={"l": 75, "r": 190, "t": 95, "b": 65},
		height=860,
	)
	fig.update_xaxes(title="<b>Day</b>", dtick=1, showgrid=False, row=2, col=1)
	fig.update_xaxes(showgrid=False, row=1, col=1)
	fig.update_yaxes(
		title="<b>Total events</b>",
		rangemode="tozero",
		gridcolor="rgba(0,0,0,0.08)",
		row=1,
		col=1,
	)
	fig.update_yaxes(
		title="<b>Events by chaser</b>",
		rangemode="tozero",
		gridcolor="rgba(0,0,0,0.08)",
		row=2,
		col=1,
	)
	return fig


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("input", type=Path, help="Path to config.toml or match_df.parquet")
	parser.add_argument(
		"--phase",
		action="append",
		help="Phase to include, e.g. --phase light_phase. Repeat for multiple phases.",
	)
	parser.add_argument("--first-day", type=int)
	parser.add_argument("--last-day", type=int)
	parser.add_argument("--csv", type=Path, default=Path("total_chasing_events_per_day.csv"))
	parser.add_argument("--html", type=Path, default=Path("total_chasing_events_per_day.html"))
	parser.add_argument("--rolling-window", type=int, default=3)
	parser.add_argument(
		"--stack-by-chaser",
		action="store_true",
		help="Stack each daily bar by the animal doing the chasing.",
	)
	parser.add_argument(
		"--combo",
		action="store_true",
		help="Create the recommended two-panel plot: total + stacked by chaser. This is now the default.",
	)
	parser.add_argument(
		"--total-only",
		action="store_true",
		help="Create only the total chasing events per day plot.",
	)
	parser.add_argument("--show", action="store_true", help="Open the interactive plot window")
	args = parser.parse_args()

	match_df = pl.read_parquet(match_df_path(args.input))
	animals = animal_order(args.input, match_df)

	if args.combo or not args.stack_by_chaser and not args.total_only:
		daily = total_chasing_events_per_day(
			match_df,
			phases=args.phase,
			first_day=args.first_day,
			last_day=args.last_day,
		)
		stacked = chasing_events_per_day_by_chaser(
			match_df,
			phases=args.phase,
			first_day=args.first_day,
			last_day=args.last_day,
		)
		fig = plot_daily_chasing_combo(
			daily, stacked, animals=animals, rolling_window=args.rolling_window
		)
		stacked_csv = args.csv.with_name(f"{args.csv.stem}_by_chaser{args.csv.suffix}")
		stacked.write_csv(stacked_csv)
	elif args.stack_by_chaser:
		daily = chasing_events_per_day_by_chaser(
			match_df,
			phases=args.phase,
			first_day=args.first_day,
			last_day=args.last_day,
		)
		fig = plot_daily_chasing_by_chaser(daily, animals=animals)
	else:
		daily = total_chasing_events_per_day(
			match_df,
			phases=args.phase,
			first_day=args.first_day,
			last_day=args.last_day,
		)
		fig = plot_daily_chasing(daily, rolling_window=args.rolling_window)

	daily.write_csv(args.csv)
	fig.write_html(args.html)

	print(f"Rows: {daily.height}")
	print(f"Saved CSV: {args.csv}")
	if args.combo or not args.stack_by_chaser and not args.total_only:
		print(f"Saved stacked CSV: {stacked_csv}")
	print(f"Saved plot: {args.html}")

	if args.show:
		fig.show()


if __name__ == "__main__":
	main()
