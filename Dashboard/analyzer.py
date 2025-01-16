from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import re
import emoji
from nltk.sentiment import SentimentIntensityAnalyzer
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Date, Text, text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt
import urllib
from better_profanity import profanity
from sqlalchemy import inspect
import seaborn as sns
from nltk.stem import WordNetLemmatizer
import plotly.express as px
from selenium.common.exceptions import NoSuchElementException
import nltk
import os
import sys
import mplcursors
import time
from wordcloud import WordCloud
import plotly.express as px
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

if not os.path.exists('static/plots'):
    os.makedirs('static/plots')

if not os.path.exists('results'):
    os.makedirs('results')

from config import DATABASE_CONFIG
def setup_database():
    username = DATABASE_CONFIG['username']
    password = DATABASE_CONFIG['password']
    host = DATABASE_CONFIG['host']
    port = DATABASE_CONFIG['port']
    dbname = DATABASE_CONFIG['dbname']

    engine = create_engine(f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}')

    metadata = MetaData()
    inspector = inspect(engine)
    if 'amazon_reviews_analysis' not in inspector.get_table_names():
        reviews_table = Table('amazon_reviews_analysis', metadata,
                              Column('ids', Integer, primary_key=True, autoincrement=True),
                              Column('category', String(255)),
                              Column('product_id', String(255)),
                              Column('product_name', String(255)),
                              Column('brand', String(255)),
                              Column('price', Float),
                              Column('amazon_customer_id', String(255)),
                              Column('customer_name', String(255)),
                              Column('rating', Integer),
                              Column('short_review', Text),
                              Column('converted_short_review', Text),
                              Column('date', Date),
                              Column('details', String(255)),
                              Column('review', Text),
                              Column('converted_review', Text),
                              Column('helpful_count', Integer),
                              Column('sentiment_score', Float),
                              Column('sentiment', String(20)),
                              Column('source_collected_date', Date)
                              )

        metadata.create_all(engine)
        print("Table 'amazon_reviews_anaalysis' created.")
    else:
        print("Table 'amazon_reviews_analysis' already exists.")

    return engine

def category_exists_in_db(category, engine):
    category = category.replace("'", "''")
    query = f"SELECT COUNT(*) FROM amazon_reviews_analysis WHERE category = '{category}'"
    with engine.connect() as connection:
        result = connection.execute(text(query))
        count = result.scalar()
    return count > 0

def get_last_review_id(engine):
    # Query to get the maximum id from the entire table
    query = "SELECT MAX(ids) FROM amazon_reviews_analysis"
    with engine.connect() as connection:
        result = connection.execute(text(query))
        last_id = result.scalar()
    return last_id if last_id else 0

def is_valid_customer_name(name):
    # Patterns for invalid names:
    placeholder_pattern = r"(?i)(amazon customer|placeholder|guest|reviewer|good|Reviews)"
    sentence_like_pattern = r"[,!?]"           # Sentence-like names with punctuation
    emoji_pattern = r"[^\w\s.,'-]"

    # Basic length validation
    if len(name) < 3 or len(name) > 20:
        return False

    # Check against invalid patterns
    if re.search(placeholder_pattern, name):  # Exclude placeholders
        return False
    if re.search(emoji_pattern, name):  # Exclude emojis or special characters
        return False
    if re.search(sentence_like_pattern, name):  # Exclude review-like text
        return False
    return True

lemmatizer = WordNetLemmatizer()
def lemmatize_review(text):
    # Tokenize the text and lemmatize each word
    words = text.split()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]
    return ' '.join(lemmatized_words)

engine = setup_database()

category_name = sys.argv[1]  # This is the category name (e.g., "Smart Home")
url = sys.argv[2]
category = sys.argv[1]  # This is the category name (e.g., "Smart Home")
url = sys.argv[2]

print(f"Selected Category: {category}")
print(f"Navigating to URL: {url}")
driver = webdriver.Chrome()

# Start scraping process
options = Options()
options.page_load_strategy = 'normal'
driver = webdriver.Chrome(options=options)
driver.maximize_window()
driver.get(url)

# Proceed with scraping logic
if category_exists_in_db(category, engine):
    print(f"Category '{category}' already reviewed.")
    driver.quit()
    exit()

# Initialize data structures
href_product_links = set()
product_brand_count = 0
pages = 0
# count = 0  # Initialize count to fix the reference error

# Scrape links across pages
while True:
    product_brand_count += 1
    print("product_brand_count:", product_brand_count)

    try:
        product_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[@class="a-link-normal s-no-outline"]')))
        product_url = [product_link.get_attribute('href') for product_link in product_links]
        # href_product_links.extend(product_url)
        href_product_links.update(product_url)

        # Navigate to the next page
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                            '//a[@class="s-pagination-item s-pagination-next s-pagination-button s-pagination-button-accessibility s-pagination-separator"]'))).click()
            sleep(4)
            pages += 1
            print("Clicked next page:", pages)
        except:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                            '//a[@class="s-pagination-item s-pagination-next s-pagination-button s-pagination-button-accessibility s-pagination-separator"]'))).click()
            sleep(2)
            print("Clicked in the exception")
    except Exception as e:
        print("next page error:", e)
        break
    print("url scrapped")

# Save links to CSV
href_product_links = list(href_product_links)  # Convert set to list to proceed with the DataFrame
df_a = pd.DataFrame(href_product_links)
print('df_a:', df_a)
df_a.to_csv('results/href_product_links.csv', sep='|', index=False, encoding='utf-8')
df_a
# df_a.to_csv('href_laptop_links.csv',sep='|',index=False,encoding='utf-8')
df_b=pd.read_csv('results/href_product_links.csv',sep='|')
df_b
href_product_links=df_b['0']
print(href_product_links)

last_id_in_db = get_last_review_id(engine)
ids = last_id_in_db
# ids = 0
count = 0
data_list = []

# Go through all the links collected
for href_product_link in href_product_links:
    count += 1
    print("count:", count)

    driver.get(href_product_link)
    print(href_product_link)
    sleep(2)

    if "sspa/click" in href_product_link:
        href_product_link = urllib.parse.parse_qs(urllib.parse.urlparse(href_product_link).query).get('url', [None])[0]
    parsed_link = urllib.parse.urlparse(href_product_link)
    path_parts = parsed_link.path.split('/')
    product_id = path_parts[-2]
    product_name = path_parts[-4].replace('-', ' ')
    try:

        brand = driver.find_element(By.XPATH, '//tr[@class="a-spacing-small po-brand"]/td[2]/span').text
    except:
        brand = ''
    try:
        # Extracting the price (value only, excluding the rupee symbol and commas)
        price_element = driver.find_element(By.XPATH, "//span[@class='a-price-whole']")
        price = price_element.text.replace(",", "")  # Remove commas
        price = float(price)
    except:
        price = 0

    print(f"Brand: {brand}")
    print(f"Price: {price}")

    try:
        more_reviews = driver.find_element(By.XPATH, '//a[@data-hook="see-all-reviews-link-foot"]')
        more_reviews.click()
        sleep(2)
    except:
        pass
    try:

        enter_login = driver.find_element(By.XPATH, '//label[@class="a-form-label"]').text
        if enter_login == 'Email or mobile phone number':
            phone_number = "phone_number"
            driver.find_element(By.ID, "ap_email").send_keys(phone_number)

            driver.find_element(By.ID, "continue").click()
            time.sleep(2)

            password = "your_passwod"
            driver.find_element(By.ID, "ap_password").send_keys(password)

            driver.find_element(By.ID, "signInSubmit").click()

            time.sleep(3)
            # input("Login manually and press 'Enter' to continue..")
    except:
        pass

    # input("Please complete the login manually continue....")

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    sleep(2)
    while True:

        try:

            card_reviews = driver.find_elements(By.XPATH, '//li[contains(@class, "review")]')
            print(f"Number of reviews found: {len(card_reviews)}")
            for card_review in card_reviews:

                ids += 1
                print("ids:", ids)

                customer_id_element = card_review.find_element(By.XPATH, './/div[@data-hook="genome-widget"]/a')
                amazon_customer_id = customer_id_element.get_attribute("href").split('/')[-2].replace('amzn1.account.',
                                                                                                      '') if customer_id_element else None
                print(amazon_customer_id)
                customer_name = card_review.find_element(By.XPATH, './/span[@class="a-profile-name"]').text
                if not is_valid_customer_name(customer_name):
                    print(f"Invalid customer name skipped: {customer_name}")
                    continue
                print(customer_name)
                date_element = card_review.find_element(By.XPATH, './/span[@class="a-icon-alt"]')
                rating = driver.execute_script("return arguments[0].textContent;", date_element).replace(
                    ' out of 5 stars', '').strip()
                rating = int(float(rating))
                print(rating)
                # short_review = card_review.find_element(By.XPATH, './/div[@class="a-row"]/a/span[2]').text
                # print(short_review)
                date = pd.to_datetime(
                    card_review.find_element(By.XPATH, './/span[@data-hook="review-date"]').text.replace(
                        'Reviewed in India on ',
                        '').strip(),
                    format='%d %B %Y').strftime('%d-%m-%Y')
                print(date)
                details = card_review.find_element(By.XPATH,
                                                   './/div[@class="a-row a-spacing-mini review-data review-format-strip"]').text.replace(
                    'Verified Purchase', '').strip()
                formatted_details = re.sub(r'\s+', ' ', ' '.join(re.split(r'(?=[A-Z])', details))).strip()
                details = formatted_details
                print(details)

                try:
                    translate_link = card_review.find_element(By.XPATH,
                                                              './/a[@data-hook="cr-translate-this-review-link"]')
                    translate_link.click()
                    sleep(2)

                    short_review = card_review.find_element(By.XPATH, './/div[@class="a-row"]/h5/a/span[2]').text
                    print("Translated Short Review:", short_review)

                    # Extract the translated review text
                    review = card_review.find_element(By.XPATH, './/span[@data-hook="review-body"]').text.replace('\n',
                                                                                                                  '').replace(
                        '\r', '')
                    print("Translated Review:", review)

                    # Restore the page to show the original review if needed
                    see_original = card_review.find_element(By.XPATH, './/a[@data-hook="cr-see-original-review-link"]')
                    see_original.click()
                    sleep(1)
                except:
                    # If translation not available, use the original review text
                    short_review = card_review.find_element(By.XPATH, './/div[@class="a-row"]/h5/a/span[2]').text
                    print("Original Short Review:", short_review)

                    review = card_review.find_element(By.XPATH, './/span[@data-hook="review-body"]').text.replace('\n',
                                                                                                                  '').replace(
                        '\r', '')
                    print("Original Review:", review)

                try:
                    helpful_count = card_review.find_element(By.XPATH,
                                                             './/span[@data-hook="helpful-vote-statement"]').text.replace(
                        '\n',
                        '').replace(
                        '\r', '').replace(' people found this helpful', '').replace('One person found this helpful',
                                                                                    '1')
                    print(helpful_count)
                except:
                    helpful_count = 0


                def clean_review(text):
                    text = re.sub(r'\(.*?\)', '', text)  # Remove anything inside parentheses
                    text = re.sub(r'\[.*?\]', '', text)  # Remove square brackets
                    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # Remove URLs
                    text = re.sub(r'<.*?>+', '', text)  # Remove HTML tags
                    text = re.sub('\n', '', text)  # Remove new lines
                    text = re.sub(r'\.\.+', '', text)  # Remove ellipses
                    text = re.sub(r'\(\)', '', text)  # Remove empty parentheses
                    text = re.sub(r'\*', '', text)  # Remove asterisks
                    text = re.sub(r'(.)\1{2,}', r'\1\1',
                                  text)  # Remove repeated letters (e.g., superrrrr becomes super)
                    text = re.sub(r'\b(\w+)\s+\1+\b', r'\1',
                                  text)  # Remove repeated words (e.g., wow wow wow becomes wow)
                    text = profanity.censor(text)
                    text = lemmatize_review(text)
                    return text


                converted_short_review = emoji.demojize(short_review).replace(":", " ").replace("_", " ")
                converted_short_review = clean_review(converted_short_review)
                print('converted_short_review:', converted_short_review)
                converted_review = emoji.demojize(review).replace(":", " ").replace("_", " ")
                converted_review = clean_review(converted_review)
                print('converted_review:', converted_review)

                timestamp = datetime.now()
                formatted_timestamp = timestamp.strftime("%d-%m-%Y %H:%M:%S")
                source_collected_date = formatted_timestamp

                data = [ids, category, product_id, product_name, brand, price, amazon_customer_id, customer_name,
                        rating, short_review, converted_short_review, date, details, review, converted_review,
                        helpful_count, source_collected_date]
                # list of differnt attributes

                data_list.append(data)
                print()
        except:
            pass

        try:
            next_page = driver.find_element(By.XPATH, '//li[@class="a-last"]')
            next_page.click()
            sleep(2)
        except:
            print("No more pages to navigate.")
            break

# columns = ['ids', 'category', 'product_id','product_name', 'amazon_customer_id', 'customer_name', 'rating', 'short_review','converted_short_review', 'date','details', 'review','converted_review', 'helpful_count',
#            'source_collected_date']
df = pd.DataFrame(data_list,
                  columns=['ids', 'category', 'product_id', 'product_name', 'brand', 'price', 'amazon_customer_id',
                           'customer_name', 'rating', 'short_review', 'converted_short_review', 'date', 'details',
                           'review', 'converted_review', 'helpful_count', 'source_collected_date'])
df.drop_duplicates(subset=['customer_name', 'product_id'], keep="first", inplace=True)
df['helpful_count'] = df['helpful_count'].replace(',', '', regex=True)  # Remove commas
df['helpful_count'] = pd.to_numeric(df['helpful_count'], errors='coerce').fillna(0).astype(int)
df['price'] = df['price'].replace(',', '', regex=True)  # Remove commas
print(f"Scraped data count: {len(df)}")

nltk.download('vader_lexicon')
def get_sentiment_and_score(row):
    sia = SentimentIntensityAnalyzer()
    combined_text = f"short_review: {row['converted_short_review']} review: {row['converted_review']}"
    score = sia.polarity_scores(combined_text)['compound']
    if score >= 0.05:
        sentiment = 'positive'
    elif score <= -0.05:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    return sentiment, score

def analyze_sentiment(df):
    df[['sentiment', 'sentiment_score']] = df.apply(lambda row: pd.Series(get_sentiment_and_score(row)), axis=1)
    return df

def save_to_database(df, engine, amazon_reviews_analysis):
    df.drop_duplicates(subset=['customer_name', 'product_id'], keep="first", inplace=True)
    with engine.connect() as connection:
        latest_id_query = f"SELECT MAX(product_id) FROM {amazon_reviews_analysis}"
        result = connection.execute(text(latest_id_query)).fetchone()
        last_aws_id = result[0] if result[0] else 0  # Start from 0 if table is empty

    df.to_sql('amazon_reviews_analysis', engine, if_exists='append', index=False)

    print("Data successfully inserted into table!")

def download_csv(df, category):
    file_name = f"results/{category}_sentiment_analysis.csv"
    df.to_csv(file_name, index=False)
    print(f"CSV file '{file_name}' has been saved!")

def plot_wordcloud_dropdown(df, plot_filepath):
    sentiments = ['positive', 'negative', 'neutral']
    wordclouds = {}
    for sentiment in sentiments:
        # Filter reviews by sentiment
        sentiment_reviews = ' '.join(df[df['sentiment'] == sentiment]['converted_short_review'].fillna('') + ' ' +
                                     df[df['sentiment'] == sentiment]['converted_review'].fillna(''))

        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(sentiment_reviews)
        wordclouds[sentiment] = wordcloud

    # Create figure with interactive dropdown
    fig = go.Figure()

    for sentiment in sentiments:
        fig.add_trace(go.Image(z=wordclouds[sentiment].to_array(), visible=(sentiment == 'positive')))

    # Add dropdown for selecting sentiment
    fig.update_layout(
        title='Word Cloud for Sentiments',
        updatemenus=[dict(
            buttons=[
                {'label': 'Positive', 'method': 'update',
                 'args': [{'visible': [True, False, False]}, {'title': 'Positive Word Cloud'}]},
                {'label': 'Negative', 'method': 'update',
                 'args': [{'visible': [False, True, False]}, {'title': 'Negative Word Cloud'}]},
                {'label': 'Neutral', 'method': 'update',
                 'args': [{'visible': [False, False, True]}, {'title': 'Neutral Word Cloud'}]},
            ],
            direction='down',
            showactive=True,
            x=0.17,
            xanchor='left',
            y=1.15,
            yanchor='top'
        )]
    )
    wordcloud_plot_filepath = os.path.join(os.path.dirname(plot_filepath), f'{df["category"][0]}_wordcloud_plot.html')
    fig.write_html(wordcloud_plot_filepath)

    return wordcloud_plot_filepath

def plot_sentiment_distribution(df, plot_filepath):
    sentiment_counts = df['sentiment'].value_counts().reset_index()
    sentiment_counts.columns = ['sentiment', 'count']

    # Create first plot for sentiment distribution
    fig_sentiment = px.bar(sentiment_counts, x='sentiment', y='count', title='Sentiment Distribution',
                           labels={'sentiment': 'Sentiment', 'count': 'Count'})

    # Update the text to show total counts on the bars
    fig_sentiment.update_traces(texttemplate='%{y}', textposition='outside', showlegend=False)
    fig_sentiment.update_traces(marker=dict(color='lightgrey'))

    # Add dropdown for product selection using product_name
    products = df['product_name'].unique()
    product_dropdown = []
    for product in products:
        filtered_df = df[df['product_name'] == product]
        product_count = filtered_df['sentiment'].value_counts().reset_index()
        product_count.columns = ['sentiment', 'count']

        fig_sentiment.add_trace(
            go.Bar(
                x=product_count['sentiment'],
                y=product_count['count'],
                name=f'{product}',
                visible=False,
                marker = dict(color='lightgrey')
            )
        )
        product_dropdown.append(
            {'label': f'{product}', 'value': f'{product}'}
        )

    # Show all product sentiment distribution in the dropdown
    fig_sentiment.update_layout(
        updatemenus=[dict(
            buttons=[{
                'label': 'All Products',
                'method': 'update',
                'args': [{'visible': [True] + [False] * len(products)}, {'title': 'Sentiment Distribution'}]
            }] + [
                        {
                            'label': product,
                            'method': 'update',
                            'args': [{'visible': [i == idx for i in range(len(products) + 1)]},
                                     {'title': f'Sentiment Distribution for {product}'}]
                        } for idx, product in enumerate(products, start=1)
                    ],
            direction='down',
            showactive=True,
            x=0.17,
            xanchor='left',
            y=1.15,
            yanchor='top'
        )]
    )

    sentiment_plot_filepath = os.path.join(os.path.dirname(plot_filepath), f'{df["category"][0]}_sentiment_distribution.html')
    fig_sentiment.write_html(sentiment_plot_filepath)

    # Create second plot for sentiment distribution by brand
    brand_sentiment_counts = df.groupby(['brand', 'sentiment']).size().reset_index(name='count')
    fig_brandwise = px.bar(brand_sentiment_counts, x='sentiment', y='count', color='brand', barmode='group',
                           title='Sentiment Distribution by Brand', labels={'sentiment': 'Sentiment', 'count': 'Count'})

    # Add total counts on each bar
    fig_brandwise.update_traces(texttemplate='%{y}', textposition='outside')

    # Add interactivity: clickable legend for brands
    fig_brandwise.update_layout(
        legend_title="Brand",
        legend=dict(
            x=1.02, y=1, traceorder='normal', orientation='v',
            font=dict(family="Arial", size=10, color="black"),
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)',
            borderwidth=1
        )
    )
    brandwise_plot_filepath = os.path.join(os.path.dirname(plot_filepath),
                                           f'{df["category"][0]}_brandwise_sentiment_distribution.html')
    fig_brandwise.write_html(brandwise_plot_filepath)
    return sentiment_plot_filepath, brandwise_plot_filepath

def year_wise_plot(df, plot_filepath):
    df = df.assign(year=pd.to_datetime(df['date'], format='%d-%m-%Y').dt.year)

    sentiment_year_brand = df.groupby(['year', 'sentiment', 'brand']).size().reset_index(name='count')

    fig = go.Figure()

    # Add traces for each brand, each year, and sentiment type
    brands = sentiment_year_brand['brand'].dropna().unique()
    for brand in brands:
        brand_data = sentiment_year_brand[sentiment_year_brand['brand'] == brand]
        for sentiment in ['positive', 'negative', 'neutral']:  # Sentiments you want to plot
            sentiment_data = brand_data[brand_data['sentiment'] == sentiment]
            fig.add_trace(go.Scatter(
                x=sentiment_data['year'],
                y=sentiment_data['count'],
                mode='lines+markers',
                name=f'{brand} - {sentiment}',
                legendgroup=brand,
                visible=True if sentiment == 'positive' else 'legendonly'  # Make non-positive lines hidden by default
            ))

    fig.update_layout(
        title='Sentiment Distribution vs Year for Different Brands',
        xaxis_title='Year',
        yaxis_title='Count',
        legend_title="Brand and Sentiment",
        legend=dict(
            title="Brand and Sentiment",
            x=1.05,
            y=1,
            traceorder='normal',
            orientation='v',
            font=dict(family="Arial", size=10, color="black"),
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)',
            borderwidth=1
        ),
        updatemenus=[dict(
            buttons=[
                {'label': 'Show All',
                 'method': 'update',
                 'args': [{'visible': [True] * len(fig.data)}, {'title': 'Sentiment Distribution vs Year for Different Brands'}]},
                {'label': 'Show Positive Sentiment Only',
                 'method': 'update',
                 'args': [{'visible': [True if 'positive' in trace.name else False for trace in fig.data]}, {'title': 'Positive Sentiment Distribution'}]},
                {'label': 'Show Negative Sentiment Only',
                 'method': 'update',
                 'args': [{'visible': [True if 'negative' in trace.name else False for trace in fig.data]}, {'title': 'Negative Sentiment Distribution'}]},
                {'label': 'Show Neutral Sentiment Only',
                 'method': 'update',
                 'args': [{'visible': [True if 'neutral' in trace.name else False for trace in fig.data]}, {'title': 'Neutral Sentiment Distribution'}]}
            ],
            direction='down',
            showactive=True,
            x=0.17,
            xanchor='left',
            y=1.15,
            yanchor='top'
        )]
    )

    fig.write_html(plot_filepath)

def plot_price_vs_sentiment(df, plot_filepath):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='price', y='sentiment_score', hue='sentiment', palette='coolwarm', alpha=0.7)
    plt.title('Price vs Sentiment Score')
    plt.xlabel('Price')
    plt.ylabel('Sentiment Score')
    plt.legend(title='Sentiment', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(plot_filepath)
    plt.close()


def plot_rating_distribution(ratings, plot_filepath, df):
    import matplotlib.pyplot as plt
    import pandas as pd

    rating_buckets = {'1-2': (1, 2), '2-3': (2, 3), '3-4': (3, 4), '4-5': (4, 5)}
    rating_colors = {'1-2': 'red', '2-3': 'orange', '3-4': 'yellow', '4-5': 'green'}

    # Count ratings in each bucket
    rating_counts = {'1-2': 0, '2-3': 0, '3-4': 0, '4-5': 0}

    for rating in ratings:
        for bucket, (lower, upper) in rating_buckets.items():
            if lower <= rating < upper:
                rating_counts[bucket] += 1

    # Ensure valid ratings for analysis
    df = df.dropna(subset=['rating'])
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    valid_df = df[df['rating'] > 0]  # Exclude ratings <= 0

    if valid_df.empty:
        print("No valid ratings found.")
        return

    # Identify the product with highest and lowest average rating
    product_stats = valid_df.groupby(['product_name', 'brand']).agg(
        average_rating=('rating', 'mean'),
        rating_count=('rating', 'size')
    ).reset_index()

    # Ensure there are products to compare
    if product_stats.empty:
        print("No products found for rating analysis.")
        return

    highest_rated = product_stats.loc[product_stats['average_rating'].idxmax()]
    lowest_rated = product_stats.loc[product_stats['average_rating'].idxmin()]

    labels = [f'Rating: {bucket}\nCount: {count}' for bucket, count in rating_counts.items()]
    sizes = list(rating_counts.values())
    colors = [rating_colors[bucket] for bucket in rating_counts.keys()]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      wedgeprops={'width': 0.3}, colors=colors)
    ax.set_title(f'Total Ratings Distribution\nTotal: {sum(rating_counts.values())}')

    ax.annotate(
        f"Highest Rated: {highest_rated['product_name']} ({highest_rated['brand']}) - "
        f"Avg Rating: {highest_rated['average_rating']:.2f}",
        xy=(0, -1.1), ha='center', fontsize=12, color='black')

    ax.annotate(
        f"Lowest Rated: {lowest_rated['product_name']} ({lowest_rated['brand']}) - "
        f"Avg Rating: {lowest_rated['average_rating']:.2f}",
        xy=(0, -1.2), ha='center', fontsize=12, color='black')

    plt.tight_layout()
    plt.savefig(plot_filepath)
    plt.close()

def get_review_summary(df):
    total_reviews = len(df)
    total_products = df['product_id'].nunique()
    total_positive_reviews = len(df[df['sentiment'] == 'positive'])
    total_negative_reviews = len(df[df['sentiment'] == 'negative'])
    total_neutral_reviews = len(df[df['sentiment'] == 'neutral'])

    return {
        'total_reviews': total_reviews,
        'total_products': total_products,
        'total_positive_reviews': total_positive_reviews,
        'total_negative_reviews': total_negative_reviews,
        'total_neutral_reviews': total_neutral_reviews
    }

if __name__ == "__main__":
    engine = setup_database()
    df = analyze_sentiment(df)
    save_to_database(df, engine, 'amazon_reviews_analysis')
    download_csv(df, df['category'][0])
    summary = get_review_summary(df)
    with open('static/summary.json', 'w') as f:
        json.dump(summary, f)
    sentiment_plot_filepath, brandwise_plot_filepath = plot_sentiment_distribution(df,
                                                                           f"static/plots/{df['category'][0]}_plots.html")
    year_wise_plot(df, f"static/plots/{df['category'][0]}_year_wise_plot.html")
    plot_price_vs_sentiment(df, f"static/plots/{df['category'][0]}_price_vs_sentiment.png")
    plot_rating_distribution(df['rating'], f"static/plots/{df['category'][0]}_rating_plot.png", df)
    wordcloud_plot_filepath = plot_wordcloud_dropdown(df, f"static/plots/{df['category'][0]}_wordcloud_plot.html")
