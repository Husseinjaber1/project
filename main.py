import json
import re
import unicodedata
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from bson import json_util
from bson.json_util import dumps
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import xml.etree.ElementTree as ET

client = MongoClient('mongodb://localhost:27017/')
db = client['mayadeen']
collection = db['news']


url = 'https://www.aljazeera.com/news/'

response = requests.get(url)
html_text = response.content

soup = BeautifulSoup(html_text, 'lxml')
data = []

for title_element in soup.find_all('a', class_='u-clickable-card__link'):
    span_element = title_element.find('span')
    if span_element:
        title = span_element.text.strip()
        cleaned_title = re.sub(r'[^\x00-\x7F]', '', title)
        cleaned_title = unicodedata.normalize("NFKD", cleaned_title)

        div_element = title_element.find_next('div', class_='gc__excerpt')
        if div_element:
            paragraph = div_element.get_text(strip=True)

        date_div = title_element.find_next('div', class_='date-simple')
        if date_div:
            date_span = date_div.find('span', class_='screen-reader-text')
            if date_span:
                date = date_span.get_text(strip=True)
            else:
                date = 'Date not found'

        data.append({'title': cleaned_title, 'paragraph': paragraph, 'date': date})

root = ET.Element("data")
for item in data:
    entry = ET.SubElement(root, "entry")
    title = ET.SubElement(entry, "title")
    title.text = item['title']
    paragraph = ET.SubElement(entry, "paragraph")
    paragraph.text = item['paragraph']
    date = ET.SubElement(entry, "date")
    date.text = item['date']

tree = ET.ElementTree(root)
tree.write("savedata.xml")


result = collection.insert_many(data)
app = Flask(__name__)
cors = CORS(app)

@app.route('/chartt')
def index():
    tree = ET.parse('savedata.xml')
    root = tree.getroot()

    chart_data = []

    for entry in root.findall('entry'):
        title = entry.find('title').text
        paragraph = entry.find('paragraph').text
        date = entry.find('date').text

        chart_data.append({'title': title, 'paragraph': paragraph, 'date': date})

    return render_template('chart.html', chart_data=chart_data)

if __name__ == '__main__':
    app.run(debug=True)