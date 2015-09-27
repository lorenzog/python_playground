"""
A simple url-sharing app across a network.

Use: from a browser, paste an URL in the form. The URL will be saved
in-memory. Then from another browser access the same page and retrieve the
URL.

Alternative use: perform a HTTP POST from a command-line tool like curl
invoked e.g. from a terminal mail client like mutt, and open the URL on
another computer.
"""

import argparse

from flask import Flask, request, render_template
app = Flask(__name__)

urls = list()


def store_url(req):
    _url_data = req.args
    _form_data = req.form
    if _form_data:
        # as application/x-www-form-urlencoded
        for _k, _v in _form_data.items():
            if _k == 'url' and _v:
                urls.append(_v)
            elif _k != 'url' and not _v:
                urls.append(_k)
            else:
                # empty url
                continue
    if _url_data:
        _url = _url_data.get('url')
        if _url:
            urls.append(_url)


@app.route('/', methods=['GET', 'POST'])
def share_url():
    if request.method == 'POST':
        store_url(request)

    return return_all()


def return_all():
    # return the list, reversed
    return render_template('shared_urls.html', urls=urls[::-1])


@app.route('/clean', methods=['POST'])
def cleanup():
    global urls
    urls = []
    return return_all()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-d', '--debug', action='store_true')
    args = p.parse_args()
    if args.debug:
        app.debug = True
    app.run()
