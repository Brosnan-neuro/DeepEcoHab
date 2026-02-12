import dash_bootstrap_components as dbc
from dash import dcc, html


def generate_input_block(
	label_name: str,
	id: str | dict[str, str],
	placeholder: str,
	required: bool,
	value: str | None = None,
) -> list[dbc.Label, dbc.Input]:

	return [
		dbc.Label(label_name, className="home-label"),
		dbc.Input(
			id=id,
			placeholder=placeholder,
			required=required,
			value=value,
			className="filled-input",
		),
	]


modal = dbc.Modal(
	[
		dbc.ModalHeader([dbc.ModalTitle("Downloads")]),
		dbc.ModalBody(
			[
				dcc.Upload(
					id="upload-data",
					children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
					style={
						"width": "100%",
						"height": "60px",
						"lineHeight": "60px",
						"borderWidth": "1px",
						"borderStyle": "dashed",
						"borderRadius": "5px",
						"textAlign": "center",
						"margin": "10px",
					},
				),
				html.Div(id="output-data-upload"),
			]
		),
	],
	id="load-project-modal",
	is_open=False,
)


def generate_layout():
	return dbc.Row(
		[
			dbc.Col(
				[
					html.H2("Project Configuration", className="h2"),
					dbc.Card(
						[
							dbc.CardBody(
								[
									*generate_input_block(
										"Project Name:",
										{"type": "required-input", "index": "proj-name"},
										"test_project",
										True,
									),
									*generate_input_block(
										"Project Location:",
										{"type": "required-input", "index": "proj-loc"},
										"/etc/home/Documents/projects",
										True,
									),
									*generate_input_block(
										"Location of Raw Data:",
										{"type": "required-input", "index": "data-loc"},
										"/etc/home/Documents/data",
										True,
									),
									dbc.Row(
										[
											dbc.Col(
												generate_input_block(
													"Start Light Phase:",
													{
														"type": "required-input",
														"index": "light-start",
													},
													"00:00:00",
													True,
												),
												width=6,
											),
											dbc.Col(
												generate_input_block(
													"Start Dark Phase:",
													{
														"type": "required-input",
														"index": "dark-start",
													},
													"12:00:00",
													True,
												),
												width=6,
											),
										],
										className="mb-3",
									),
									dbc.Button(
										"Optional Settings",
										id="opt-btn",
										color="link",
										size="sm",
										className="p-0 mb-2",
									),
									dbc.Collapse(
										html.Div(
											[
												dbc.Row(
													[
														dbc.Col(
															generate_input_block(
																"Start datetime:",
																"experiment-start",
																"2024-11-05 00:00:00",
																False,
															),
															width=6,
														),
														dbc.Col(
															generate_input_block(
																"End datetime:",
																"experiment-end",
																"2024-11-29 12:00:00",
																False,
															),
															width=6,
														),
													],
													className="mb-3",
												),
												dbc.Row(
													[
														dbc.Col(
															generate_input_block(
																"Data extension",
																"file_ext",
																"txt",
																False,
																"txt",
															),
														),
														dbc.Col(
															generate_input_block(
																"Data prefix",
																"file_prefix",
																"COM",
																False,
																"COM",
															),
														),
														dbc.Col(
															generate_input_block(
																"Timezone",
																"timezone",
																"Europe/Warsaw",
																False,
																"Europe/Warsaw",
															),
														),
													]
												),
												dbc.Row(
													[
														dbc.Col(
															generate_input_block(
																"Animal IDs:",
																"animal-ids",
																"ID_01, ID_02, etc.",
																False,
															),
															width=7,
														),
														dbc.Col(
															[
																dbc.Label(
																	"Sanitize IDs:",
																	class_name="home-label",
																),
																dbc.Label(
																	"Min antenna crossings:",
																	class_name="home-label",
																),
															]
														),
														dbc.Col(
															[
																dbc.Checkbox(
																	id="sanitize-check",
																	value=True,
																	class_name="checkbox",
																),
																dbc.Input(
																	id="min-cross",
																	placeholder=100,
																	value=100,
																	type="number",
																	step=1,
																	class_name="filled-input mb-0",
																),
															]
														),
													],
													align="end",
												),
												dbc.Row(
													[
														dbc.Col(
															[
																dbc.Label(
																	"Layout settings:",
																	className="home-label",
																),
																dbc.Checklist(
																	options=[
																		{
																			"label": " Field layout",
																			"value": "field",
																		},
																	],
																	value=[],
																	id="layout-checks",
																	inline=True,
																	className="mb-3",
																),
															]
														),
													]
												),
											]
										),
										id="opt-collapse",
										is_open=False,
									),
									dbc.Row(
										[
											dbc.Col(
												dbc.Button(
													"Create Project",
													id="create-project-btn",
													color="primary",
													disabled=True,
													className="w-100 mt-3",
													n_clicks=0,
												),
												width=4,
											),
											dbc.Col(
												dbc.Container(
													[
														dbc.Button(
															"Load project",
															id="load-project",
															color="primary",
															className="w-100 mt-3",
															n_clicks=0,
														),
														modal,
													]
												),
												width=4,
											),
											dbc.Col(
												dbc.Button(
													"Clear Session",
													id="clear-session-btn",
													disabled=True,
													className="w-100 mt-3",
													n_clicks=0,
												)
											),
										]
									),
								]
							)
						],
						className="shadow",
					),
					html.Div(
						id="toast-container",
      					className="toast-container",
					),
				],
				xs=12,
				sm=12,
				md=8,
				lg=6,
			),
			dbc.Col(
				html.Img(src="assets/logo_test.png", width=500, height=500),
				className="d-flex justify-content-center align-items-center",
				style={"height": "100vh"},
			),
		],
		justify="left",
		align="center",
	)
