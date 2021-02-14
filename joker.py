from datetime import datetime

import rutimeparser
import requests
from lxml.html import *


last_joke_time = datetime.now()

def get_new_joke():
    r = requests.get('https://vse-shutochki.ru/')
    if r.status_code != 200:
        return
    html = document_fromstring(r.text)
    posts = html.find_class('post')

    def actual_post(p):
        time_span = p.xpath('./div/span')
        if not time_span:
            return None
        post_time = rutimeparser.parse(time_span[0].text)
        return post_time > last_joke_time

    actual_posts = filter(actual_post, posts)
    post = next(actual_posts, None)
    if post is not None:
        return post.text


if __name__ == '__main__':
    from datetime import timedelta
    last_joke_time -= timedelta(days=1)
    print(get_new_joke())
