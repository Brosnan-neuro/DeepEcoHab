import dash_bootstrap_components as dbc
from dash import dcc, html


def generate_layout():
	return [
		dbc.Row(
			[
				dbc.Col(
					[
						html.H2("Experiment analysis", className="h2 text-center"),
					]
				),
			]
		),
		dbc.Row(
			[
				dbc.Col(
					[
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Antenna analysis", className="h3"),
										dbc.Row(
											[
												dbc.Col(
													[
														dbc.Label(
															"Minimum time together",
															class_name="mb-3",
														),
														dbc.Input(
															id="styled-numeric-input",
															type="number",
															min=2,
															placeholder="2",
															class_name="filled-input",
														),
													],
													width=6,
												),
											],
											class_name="mb-4",
										),
										dbc.Row(
											[
												dbc.Col(
													[
														dbc.Label(
															"Chasing time window", class_name="mb-3"
														),
														dcc.RangeSlider(
															id="chasing_window",
															min=0,
															max=5,
															step=0.1,
															count=1,
															value=[0.1, 1.2],
															marks={i: str(i) for i in [0, 5]},
															tooltip={
																"placement": "bottom",
																"always_visible": False,
																"style": {
																	"color": "LightSteelBlue",
																	"fontSize": "12px",
																},
															},
															className="dash-slider",
														),
													],
													width=6,
												),
											],
											class_name="mb-4",
										),
										dbc.Row(
											[
												dbc.Col(
													[
														dbc.Button(
															"Analyze",
															id="antenna-button",
															color="primary",
															n_clicks=0,
															size="md",
															disabled=True,
															class_name="w-100",
														),
														html.Div(
															[
																dbc.Progress(
																	id="analysis-progress",
																	value=0,
																	striped=True,
																	animated=True,
																	className="mb-3",
																	style={"height": "30px"},
																),
																html.P(
																	id="progress-text",
																	className="progress-print",
																),
																dcc.Interval(
																	id="progress-interval",
																	interval=200,
																	n_intervals=0,
																	disabled=True,
																),
															],
															className="mt-3",
														),
													],
													width=12,
												),
											]
										),
									]
								),
							]
						),
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Group analysis", className="h3"),
										dbc.Row(
											[html.H4("PLACEHOLDER", className="h4")],
											class_name="mb-4",
										),
										dbc.Row(
											[html.H4("PLACEHOLDER", className="h4")],
											class_name="mb-4",
										),
										dbc.Row(
											[
												dbc.Col(
													[
														dbc.Button(
															"PLACEHOLDER",
															id="placeholder-button",
															color="primary",
															n_clicks=0,
															size="md",
															class_name="w-100",
														),
													],
													width=12,
												),
											]
										),
									]
								),
							]
						),
					],
					width=6,
				),
				dbc.Col(
					[
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H3("Pose analysis", className="h3"),
										dbc.Row(
											[html.H4("PLACEHOLDER", className="h4")],
											class_name="mb-4",
										),
										dbc.Row(
											[html.H4("PLACEHOLDER", className="h4")],
											class_name="mb-4",
										),
										dbc.Row(
											[
												dbc.Col(
													[
														dbc.Button(
															"PLACEHOLDER",
															id="placeholder-button2",
															color="primary",
															n_clicks=0,
															size="mg",
															class_name="w-100",
														),
													],
													width=12,
												),
											]
										),
									]
								),
							]
						),
					],
					width=6,
				),
			]
		),
	]
