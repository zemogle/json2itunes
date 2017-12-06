import logging
from datetime import datetime
import os

from jinja2 import Environment, FileSystemLoader, Undefined
import requests
from bs4 import BeautifulSoup

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

TEMPLATE_LOADER = FileSystemLoader('templates')
OUTPUT_DIR = 'xml'
FEED_URL = 'https://blogs.cardiff.ac.uk/physicsoutreach/category/media/pythagorean-astronomy/?json=1&count=50'

def runner():
    data = get_data()
    if data:
        episodes = extract_data(data)
        filename = datetime.now().strftime("feed-%Y-%m-%dT%H:%M:%S.xml")
        render_xml_data(episodes, filename)
    return

def get_data():
    try:
        r = requests.get(FEED_URL, timeout=20.0)
    except requests.exceptions.Timeout:
        logging.error("PHYSX Blog timed out")
        return False

    if r.status_code in [200,201]:
        logging.info('Downloaded latest podcast json')
        return r.json()
    else:
        logging.error("Could not send request: {}".format(r.content))
        return False



def extract_data(data):
    episodes = []
    posts = data['posts']
    for post in posts:
        podcast = dict()
        if not post['custom_fields'].get('enclosure', None):
            logging.error("No audio for: {}".format(post['title']))
            continue
        podcast['file_url'] = post['custom_fields']['enclosure'][0].split('\n')[0].strip()
        podcast['title'] = post['title']
        desc = BeautifulSoup(post['content'], "html.parser").text
        podcast['description'] =  desc.replace(podcast['file_url'],'').replace("& ", "&amp; ")
        podcast['excerpt'] = BeautifulSoup(post['excerpt'], "html.parser").text[0:255].replace("& ", "&amp; ")
        datestamp = datetime.strptime(post['date'],'%Y-%m-%d %H:%M:%S')
        podcast['datestamp'] = datestamp.strftime("%a, %d %b %Y %H:%M:%S -0000")
        podcast['duration'] = "00:30:00"
        podcast['length'] = "300000"
        episodes.append(podcast)
    return episodes

def render_xml_data(indata, filename):
    data = dict()
    env = Environment(loader=TEMPLATE_LOADER)
    template = env.get_template('podcast.xml')
    data['items'] = indata

    output_from_parsed_template = template.render(**data)
    output_from_parsed_template.replace("& ", "&amp; ")

    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, filename), "w") as fh:
        logging.debug('Writing out {}'.format(fh.name))
        fh.write(output_from_parsed_template)

    return

if __name__ == '__main__':
    runner()
