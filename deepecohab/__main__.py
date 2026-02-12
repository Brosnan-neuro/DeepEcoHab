import webbrowser
from deepecohab.app.app import app

if __name__ == "__main__":
	webbrowser.open_new("http://127.0.0.1:8050/")
	app.run(debug=True, port=8050)
