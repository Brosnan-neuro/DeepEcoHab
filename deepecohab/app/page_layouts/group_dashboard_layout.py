import dash_bootstrap_components as dbc
from dash import dcc, html


def generate_layout(fig):
	html.Div(
		[
			dbc.Row(
				[
					dbc.Col(
						[
							html.H4("Analysis Filters"),
							html.Hr(),
							dbc.Label("Select Metric:"),
							dcc.Dropdown(
								options=["Performance", "Latency", "Accuracy"],
								value="Performance",
								className="mb-3",
							),
							dbc.Label("Grouping Variable:"),
							dbc.RadioItems(
								options=[
									{"label": "Treatment", "value": 1},
									{"label": "Genotype", "value": 2},
									{"label": "Age", "value": 3},
								],
								value=1,
								id="grouping-input",
								className="mb-3",
							),
							dbc.Button(
								"Download Report", color="secondary", size="sm", className="w-100"
							),
						],
						width=3,
						style={"borderRadius": "10px", "minHeight": "70vh"},
					),
					dbc.Col(
						[
							dbc.Card(
								[
									dbc.CardHeader(html.H5("Group Comparisons", className="mb-0")),
									dbc.CardBody([dcc.Graph(figure=fig, id="box-plot-main")]),
								]
							),
							dbc.Row(
								[
									dbc.Col(
										dbc.Card(
											dbc.CardBody(
												[
													html.H6("Mean Delta", className="text-muted"),
													html.H3("+12.4%"),
												]
											)
										),
										width=6,
									),
									dbc.Col(
										dbc.Card(
											dbc.CardBody(
												[
													html.H6("P-Value", className="text-muted"),
													html.H3("0.0042"),
												]
											)
										),
										width=6,
									),
								]
							),
						],
						width=9,
					),
				]
			)
		]
	)
