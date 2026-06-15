setup:
	pip install -r requirements.txt
	plotly_get_chrome

pipeline:
	python load_data.py
	python analysis.py

dashboard:
	streamlit run dashboard.py