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


url = 'https://www.aljazeera.com/opinion/'

response = requests.get(url)
html = response.content
soup = BeautifulSoup(html, 'lxml')
data = []

for info in soup.find_all('a', class_='u-clickable-card__link'):
    span = info.find('span')
    if span:
        title = span.text.strip()
        # erase the encryption
        cleaned_title = re.sub(r'[^\x00-\x7F]', '', title)
        # normalizes the text
        cleaned_title = unicodedata.normalize("NFKD", cleaned_title)
        # get the paragraph
        paragraph = info.find_next('div', class_='gc__excerpt').get_text(strip=True)
        # get the date published
        date_pub = info.find_next('div', class_='date-simple')
        if date_pub:
            date = date_pub.find('span', class_='screen-reader-text').get_text(strip=True)
        # get the author
        author = info.find_next('span', class_='meta-content-author-name').get_text(strip=True)
        data.append({'title': cleaned_title, 'paragraph': paragraph, 'date': date, 'author': author})

# store them in xml file
root = ET.Element("data")
for item in data:
    entry = ET.SubElement(root, "entry")
    title = ET.SubElement(entry, "title")
    title.text = item['title']
    paragraph = ET.SubElement(entry, "paragraph")
    paragraph.text = item['paragraph']
    date = ET.SubElement(entry, "date")
    date.text = item['date']
    author = ET.SubElement(entry, "author")
    author.text = item['author']

tree = ET.ElementTree(root)
tree.write("savedata.xml")


result = collection.insert_many(data)
app = Flask(__name__)
cors = CORS(app)

@app.route('/')
def index():
    tree = ET.parse('savedata.xml')
    root = tree.getroot()

    chart_data = []

    for entry in root.findall('entry'):
        title = entry.find('title').text
        paragraph = entry.find('paragraph').text
        date = entry.find('date').text
        author = entry.find('author').text

        chart_data.append({'title': cleaned_title, 'paragraph': paragraph, 'date': date, 'author': author})

    return render_template('chart.html', chart_data=chart_data)

if __name__ == '__main__':
    app.run(debug=True)
