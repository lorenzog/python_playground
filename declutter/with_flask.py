import logging

from flask import Flask, request
app = Flask('decl')

from decl import read_from_url, cleaners, DEFAULT_CLEANER


log = logging.getLogger('decl-wsgi')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)


_cleaners = cleaners.keys()

# let's use a template, shall we
form = b'''<html><body><form action="/" method="post">
<label form="your_name">URL:</label>
    <input id="url_id" type="text" name="url"><br>
    <input id="cleaner_id" type="radio" name="cleaner" value="{0}">{0}<br>
    <input id="cleaner_id" type="radio" name="cleaner" value="{1}">{1}<br>
    <input id="cleaner_id" type="radio" name="cleaner" value="{2}">{2}<br>
    <input id="cleaner_id" type="radio" name="cleaner" value="{3}">{3}<br>
    <input type="submit" value="Cleanup!">
</form></body></html>'''.format(_cleaners[0], _cleaners[1],
                                _cleaners[2], _cleaners[3])


@app.route('/', methods=['GET'])
def get():
    return form


@app.route('/', methods=['POST'])
def post():
    url = request.form['url']
    try:
        cleaner = request.form['cleaner']
    except KeyError as e:
        cleaner = DEFAULT_CLEANER
    out = read_from_url(url, cleaner)
    out_html = u'<html><head/><body><p><a href="{}">Original</a></p><p><pre>{}</pre></p></body></html>'.format(url, out)
    return out_html

if __name__ == '__main__':
    app.run()
