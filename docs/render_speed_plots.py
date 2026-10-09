"""Render the speed-plot documentation illustration from deterministic synthetic data.

Run from the repository root with ``python -m docs.render_speed_plots``.
Requires the app's Plotly/Kaleido installation.
"""

import datetime as dt
from pathlib import Path

import polars as pl

from deepecohab.plotting.context import PlotContext
from deepecohab.plotting.registry import PlotRegistry


def main():
	"""Write two real plot renders, labelled as illustrative in the app docs."""
	rows = []
	for animal_index, animal in enumerate(["A", "B", "C"]):
		for day in range(1, 7):
			for hour in [2, 5, 14, 17]:
				for tunnel, length in [("tunnel_1", 25), ("tunnel_2", 35)]:
					for crossing in range(3):
						speed = 8 + animal_index * 3 + day + hour / 4 + crossing * 2
						rows.append(
							{
								"animal_id": animal,
								"position": tunnel + "_forward",
								"day": day,
								"hour": hour,
								"phase_count": day * 2 - (hour < 12),
								"phase": "light_phase" if hour < 12 else "dark_phase",
								"time_spent": dt.timedelta(seconds=length / speed),
							}
						)
	context = PlotContext(
		animal_ids=["A", "B", "C"],
		cages=[],
		positions=["tunnel_1", "tunnel_2"],
		phases={"light_phase": 0, "dark_phase": 12},
		days_range=(1, 6),
		phase_range=(1, 12),
		tunnels_map={"tunnel_1_forward": "tunnel_1", "tunnel_2_forward": "tunnel_2"},
		tunnel_lengths_cm={"tunnel_1": 25, "tunnel_2": 35},
		_loaded={
			"main_df": pl.DataFrame(rows),
			"animals": pl.DataFrame({"animal_id": ["A", "B", "C"]}),
			"event_bouts": pl.DataFrame(
				{
					"event": pl.Series(
						["Illustrative event"], dtype=pl.Enum(["Illustrative event"])
					),
					"position": ["tunnel_1"],
					"day": [3],
					"hour": [2],
					"phase_count": [5],
				}
			),
		},
	)
	for name, options in [("animal-speed", {}), ("animal-speed-daily", {"timescale": "days"})]:
		figure = PlotRegistry.build(name, context, **options)
		figure.update_layout(template="plotly_white", font={"size": 14}, margin={"t": 75, "b": 60})
		figure.write_image(
			Path(__file__).parent / "images" / "app" / f"{name}.png", width=1050, height=420
		)


if __name__ == "__main__":
	main()
