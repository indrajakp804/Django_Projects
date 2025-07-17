from flask import Flask, render_template, request, redirect, url_for
import subprocess
import os
from sqlalchemy import create_engine, text
import json

app = Flask(__name__)

from config import DATABASE_CONFIG

username = DATABASE_CONFIG['username']
password = DATABASE_CONFIG['password']
host = DATABASE_CONFIG['host']
port = DATABASE_CONFIG['port']
dbname = DATABASE_CONFIG['dbname']

engine = create_engine(f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}')

# Define the categories
categories = {
    "Smart Home": "https://www.amazon.in/s?i=specialty-aps&srs=13773797031&s=popularity-rank&fs=true&ref=lp_13773797031_sar",
    "DSLR Cameras":"https://www.amazon.in/s?i=electronics&rh=n%3A1389177031&s=popularity-rank&fs=true&ref=lp_1389177031_sar",
    "Refrigerators": "https://www.amazon.in/s?i=kitchen&rh=n%3A1380365031&s=popularity-rank&fs=true&ref=lp_1380365031_sar",
    "Laptops": "https://www.amazon.in/s?i=computers&rh=n%3A1375424031&s=popularity-rank&fs=true&ref=lp_1375424031_sar",
    "Power Banks": "https://www.amazon.in/s?i=electronics&rh=n%3A6612025031&s=popularity-rank&fs=true&ref=lp_6612025031_sar",
    "Televisions": "https://www.amazon.in/s?i=electronics&rh=n%3A1389396031&s=popularity-rank&fs=true&ref=lp_1389396031_sar",
    "Air Conditioners": "https://www.amazon.in/s?i=kitchen&rh=n%3A3474656031&s=popularity-rank&fs=true&ref=lp_3474656031_sar",
}

def fetch_analyzed_categories():
    """Fetch previously analyzed categories from the database."""
    query = "SELECT DISTINCT category FROM amazon_reviews_analysis"
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return [row[0] for row in result]  # Access by index (assuming 'category' is the first column)

@app.route('/')
def home_page():
    return render_template('index.html', categories=categories)

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Start the analysis when the button is pressed."""
    category = request.form['category']
    if category in categories:
        url = categories[category]
        result = subprocess.run(['python3', 'analyzer.py', category, url], capture_output=True, text=True)

        # Assuming plots are saved in the static/plots directory
        return redirect(url_for('dashboard', result=result.stdout))
    return redirect(url_for('home_page'))

@app.route('/dashboard')
def dashboard():
    """Display the analysis results and plots."""
    with open(f'static/summary.json', 'r') as f:
        summary = json.load(f)
    total_reviews = summary.get('total_reviews', 0)
    total_products = summary.get('total_products', 0)
    total_positive_reviews = summary.get('total_positive_reviews', 0)
    total_negative_reviews = summary.get('total_negative_reviews', 0)
    total_neutral_reviews = summary.get('total_neutral_reviews', 0)

    plot_files = os.listdir('static/plots') if os.path.exists('static/plots') else []
    analyzed_categories = fetch_analyzed_categories()

    result = request.args.get('result', '')
    return render_template('dashboard.html', result=result, plots=plot_files, analyzed_categories=analyzed_categories,
    total_reviews = total_reviews,
    total_products = total_products,
    total_positive_reviews = total_positive_reviews,
    total_negative_reviews = total_negative_reviews,
    total_neutral_reviews = total_neutral_reviews
    )

if __name__ == '__main__':
    app.run(debug=True)
