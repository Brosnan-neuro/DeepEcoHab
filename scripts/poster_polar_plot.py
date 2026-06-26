"""Create a poster-ready polar/radar plot from DeepEcoHab feature data.

Examples:
    python scripts/poster_polar_plot.py path/to/config.toml --html --svg
    python scripts/poster_polar_plot.py path/to/feature_df.parquet --phase dark_phase --png

Dependencies:
    pip install plotly polars toml kaleido
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px
import polars as pl
import toml


POSTER_TEMPLATE = "plotly_white"
METRIC_LABELS = {
	"time_alone": "Time Alone",
	"n_chasing": "Chasing Initiated",
	"n_chased": "Chasing Received",
	"n_wins": "Tube-test Wins",
	"n_loses": "Tube-test Losses",
	"activity": "Activity",
	"time_together": "Time Together",
	"pairwise_encounters": "Pairwise Encounters",
}


def color_sampling(values: list[str], cmap: str = "Phase") -> list[str]:
	"""Sample stable Plotly colors without importing the DeepEcoHab package."""
	x = [i / len(values) for i in range(len(values) + 1)]
	return px.colors.sample_colorscale(cmap, x)


def resolve_feature_df(input_path: Path) -> tuple[pl.DataFrame, dict]:
	"""Resolve a project config or feature_df parquet into data plus config metadata."""
	if input_path.suffix == ".parquet":
		return pl.read_parquet(input_path), {}

	cfg = toml.load(input_path)
	feature_path = Path(cfg["project_location"]) / "results" / "feature_df.parquet"
	if not feature_path.exists():
		raise FileNotFoundError(
			f"Could not find {feature_path}. Run the analysis pipeline first."
		)
	return pl.read_parquet(feature_path), cfg


def default_day_range(feature_df: pl.DataFrame, first_day: int | None, last_day: int | None):
	"""Use requested day bounds, falling back to the available feature data."""
	first = first_day if first_day is not None else int(feature_df["day"].min())
	last = last_day if last_day is not None else int(feature_df["day"].max())
	return [first, last]


def prepare_polar_df(
	feature_df: pl.DataFrame,
	days_range: list[int],
	phases: list[str],
	animal_order: list[str] | None = None,
) -> pl.DataFrame:
	"""Prepare mean z-score and SEM values for each animal and metric."""
	n_days = 1 if days_range[0] == days_range[1] else days_range[1] - days_range[0] + 1

	df = (
		feature_df.lazy()
		.filter(
			pl.col("phase").is_in(phases),
			pl.col("day").is_between(days_range[0], days_range[1]),
		)
		.group_by("animal_id", "metric", "day")
		.agg(pl.mean("z-score"))
		.group_by("animal_id", "metric")
		.agg(
			pl.mean("z-score").alias("mean"),
			(pl.std("z-score") / math.sqrt(n_days)).alias("sem"),
		)
		.with_columns(
			(pl.col("mean") - pl.col("sem")).alias("lower"),
			(pl.col("mean") + pl.col("sem")).alias("upper"),
		)
		.fill_null(0)
		.with_columns(
			pl.col("animal_id").cast(pl.String),
		)
	)

	if animal_order:
		order_map = {animal: idx for idx, animal in enumerate(animal_order)}
		df = df.with_columns(
			pl.col("animal_id")
			.replace(order_map, default=len(order_map))
			.cast(pl.Int64)
			.alias("_animal_order")
		)
		df = df.sort("_animal_order", "metric").drop("_animal_order").collect(engine="in-memory")
	else:
		df = df.sort("animal_id", "metric").collect(engine="in-memory")

	return df.with_columns(
		pl.col("metric")
		.replace(METRIC_LABELS)
		.str.to_titlecase()
		.str.replace("_", " ")
		.alias("metric")
	)


def poster_polar_plot(
	df: pl.DataFrame,
	animals: list[str],
	title: str,
	width: int,
	height: int,
) -> go.Figure:
	"""Build a poster-formatted polar plot with large labels and clean export styling."""
	colors = color_sampling(animals)
	color_map = dict(zip(animals, colors, strict=False))

	fig = go.Figure()
	for animal, group in df.partition_by("animal_id", as_dict=True).items():
		animal_id = str(animal[0] if isinstance(animal, tuple) else animal)
		group_closed = pl.concat([group, group.head(1)])
		color = color_map.get(animal_id, "#2F5597")
		shade_color = color.replace("rgb", "rgba").replace(")", ", 0.16)")

		fig.add_trace(
			go.Scatterpolar(
				r=group_closed["lower"],
				theta=group_closed["metric"],
				mode="lines",
				line={"width": 0, "color": color},
				legendgroup=animal_id,
				showlegend=False,
				hoverinfo="skip",
				name=f"{animal_id} lower",
			)
		)
		fig.add_trace(
			go.Scatterpolar(
				r=group_closed["upper"],
				theta=group_closed["metric"],
				mode="lines",
				fill="tonext",
				fillcolor=shade_color,
				line={"width": 0, "color": color},
				legendgroup=animal_id,
				showlegend=False,
				hoverinfo="skip",
				name=f"{animal_id} SEM",
			)
		)
		fig.add_trace(
			go.Scatterpolar(
				r=group_closed["mean"],
				theta=group_closed["metric"],
				mode="lines+markers",
				line={"color": color, "width": 5},
				marker={"size": 10, "color": color, "line": {"color": "white", "width": 1.5}},
				legendgroup=animal_id,
				name=animal_id,
				hovertemplate=(
					"Animal: %{fullData.name}<br>"
					"Metric: %{theta}<br>"
					"Z-score: %{r:.2f}<extra></extra>"
				),
			)
		)

	r_min = float(df["lower"].min()) - 0.35
	r_max = float(df["upper"].max()) + 0.35
	fig.update_layout(
		template=POSTER_TEMPLATE,
		title={"text": f"<b>{title}</b>", "x": 0.5, "xanchor": "center", "font": {"size": 38}},
		width=width,
		height=height,
		font={"family": "Arial", "size": 24, "color": "#1A1A1A"},
		paper_bgcolor="white",
		plot_bgcolor="white",
		legend={
			"title": {"text": "<b>Animal ID</b>", "font": {"size": 25}},
			"font": {"size": 20},
			"orientation": "v",
			"x": 1.04,
			"y": 0.5,
			"xanchor": "left",
			"yanchor": "middle",
			"itemsizing": "constant",
			"tracegroupgap": 4,
		},
		margin={"l": 95, "r": 260, "t": 115, "b": 90},
		polar={
			"bgcolor": "white",
			"radialaxis": {
				"visible": True,
				"range": [r_min, r_max],
				"gridcolor": "rgba(0,0,0,0.16)",
				"gridwidth": 2,
				"linecolor": "rgba(0,0,0,0.35)",
				"linewidth": 2,
				"tickfont": {"size": 19},
			},
			"angularaxis": {
				"gridcolor": "rgba(0,0,0,0.13)",
				"gridwidth": 2,
				"linecolor": "rgba(0,0,0,0.35)",
				"linewidth": 2,
				"tickfont": {"size": 22},
				"rotation": 90,
				"direction": "clockwise",
			},
		},
	)
	return fig


def write_outputs(fig: go.Figure, output_prefix: Path, formats: list[str], scale: int) -> None:
	"""Write selected plot outputs."""
	output_prefix.parent.mkdir(parents=True, exist_ok=True)

	for fmt in formats:
		output = output_prefix.with_suffix(f".{fmt}")
		if fmt == "html":
			fig.write_html(output)
		else:
			fig.write_image(output, scale=scale)
		print(f"Saved {fmt.upper()}: {output}")


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("input", type=Path, help="Path to config.toml or feature_df.parquet")
	parser.add_argument("--phase", action="append", help="Phase to include. Repeat for both phases.")
	parser.add_argument("--first-day", type=int)
	parser.add_argument("--last-day", type=int)
	parser.add_argument("--title", default="Animal Feature Overview")
	parser.add_argument("--output", type=Path, default=Path("poster_polar_plot"))
	parser.add_argument("--width", type=int, default=1500)
	parser.add_argument("--height", type=int, default=1200)
	parser.add_argument("--scale", type=int, default=3, help="Static image scale for PNG/SVG/PDF export.")
	parser.add_argument("--html", action="store_true", help="Write interactive HTML output.")
	parser.add_argument("--svg", action="store_true", help="Write SVG output.")
	parser.add_argument("--png", action="store_true", help="Write high-resolution PNG output.")
	parser.add_argument("--pdf", action="store_true", help="Write PDF output.")
	parser.add_argument("--show", action="store_true", help="Open an interactive local Plotly window.")
	args = parser.parse_args()

	feature_df, cfg = resolve_feature_df(args.input)
	phases = args.phase or ["dark_phase", "light_phase"]
	days_range = default_day_range(feature_df, args.first_day, args.last_day)
	animals = [str(animal) for animal in cfg.get("animal_ids", [])]
	if not animals:
		animals = feature_df["animal_id"].cast(pl.String).unique().sort().to_list()

	polar_df = prepare_polar_df(feature_df, days_range, phases, animals)
	fig = poster_polar_plot(polar_df, animals, args.title, args.width, args.height)

	formats = []
	if args.html or not any([args.svg, args.png, args.pdf]):
		formats.append("html")
	if args.svg:
		formats.append("svg")
	if args.png:
		formats.append("png")
	if args.pdf:
		formats.append("pdf")

	write_outputs(fig, args.output, formats, args.scale)
	if args.show:
		fig.show()


if __name__ == "__main__":
	main()
