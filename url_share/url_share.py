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
    _form_data = req.form
    if _form_data:
        # as application/x-www-form-urlencoded
        for _k, _v in _form_data.items():
            if not _v:
                continue
            if _k == 'url':
                urls.append(_v)
            else:
                urls.append(_k)
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
    urls.clear()
    return return_all()


if __name__ == '__main__':
    global urls
    urls = list()
    app.debug = True
    app.run()
