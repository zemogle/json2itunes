import logging
from datetime import datetime
import os

from jinja2 import Environment, FileSystemLoader, Undefined
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

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
        logger.error("PHYSX Blog timed out")
        return False

    if r.status_code in [200,201]:
        logger.info('Downloaded latest podcast json')
        return r.json()
    else:
        logger.error("Could not send request: {}".format(r.content))
        return False



def extract_data(data):
    episodes = []
    posts = data['posts']
    for post in posts:
        podcast = dict()
        if not post['custom_fields'].get('enclosure', None):
            print(post['title'])
            continue
        podcast['file_url'] = post['custom_fields']['enclosure'][0].split('\n')[0]
        podcast['title'] = post['title']
        podcast['description'] =  BeautifulSoup(post['content'], "html.parser").text
        podcast['excerpt'] = BeautifulSoup(post['excerpt'], "html.parser").text
        datestamp = datetime.strptime(post['date'],'%Y-%m-%d %H:%M:%S')
        podcast['datestamp'] = datestamp.strftime("%a, %d %b %Y %H:%M:%S -0000")
        podcast['duration'] = "00:30:00"
        episodes.append(podcast)
    return episodes

def render_xml_data(indata, filename):
    data = dict()
    env = Environment(loader=TEMPLATE_LOADER)
    template = env.get_template('podcast.xml')
    data['items'] = indata

    output_from_parsed_template = template.render(**data)
    output_from_parsed_template.replace("–", " ")

    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    with open(os.path.join(OUTPUT_DIR, filename), "w") as fh:
        logger.debug('Writing out', fh.name)
        fh.write(output_from_parsed_template)

    return

if __name__ == '__main__':
    runner()
