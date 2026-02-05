import dash
import numpy as np
import plotly.express as px
import polars as pl

from deepecohab.app.page_layouts import group_dashboard_layout

dash.register_page(__name__, path="/group_dashboard", name="Group Dashboard")


# --- Generate Fake Data ---
def generate_fake_data():
	groups = ["Control", "Treatment A", "Treatment B", "Treatment C"]
	data = []
	for group in groups:
		# Create 50 random data points per group with different means
		mu = np.random.randint(40, 80)
		values = np.random.normal(mu, 10, 50)
		for val in values:
			data.append({"Group": group, "Score": val, "Metric": "Performance"})
	return pl.DataFrame(data)


df = generate_fake_data()

# Create the Box Plot
fig = px.box(
	df,
	x="Group",
	y="Score",
	color="Group",
	points="all",  # Show individual data points
	template="simple_white",
	title="Inter-Group Distribution Analysis",
)
fig.update_layout(showlegend=False)

# --- Page Layout ---

layout = group_dashboard_layout.generate_layout(fig)
