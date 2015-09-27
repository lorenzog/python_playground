"""
A simple url-sharing app across a network.

Use: from a browser, paste an URL in the form. The URL will be saved
in-memory. Then from another browser access the same page and retrieve the
URL.

Alternative use: perform a HTTP POST from a command-line tool like curl
invoked e.g. from a terminal mail client like mutt, and open the URL on
another computer.
"""

from flask import Flask, request, render_template
app = Flask(__name__)


def store_url(req):
    global urls
    _url_data = req.args
    _post_data = req.form
    if _post_data:
        # sent from curl
        for item in _post_data.keys():
            urls.add(item)
    if _url_data:
        _url = _url_data.get('url')
        urls.add(_url)


@app.route('/', methods=['GET', 'POST'])
def share_url():
    if request.method == 'POST':
        store_url(request)
    return render_template('shared_urls.html', urls=urls)


@app.route('/clean', methods=['POST'])
def cleanup():
    global urls
    urls.clear()
    return render_template('shared_urls.html', urls=urls)


if __name__ == '__main__':
    global urls
    urls = set()
    # app.debug = True
    app.run()
