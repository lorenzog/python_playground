'''UWSGI front-end for the de-clutter

Usage::

    uwsgi --http :9090 --wsgi-file decl.py

'''
import logging
import urllib
import tempfile


from decl import read_from_url


log = logging.getLogger('decl-wsgi')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)


CONTENT_TYPE = ('Content-Type', 'text/html; charset="utf-8"')

form = b'''<html><body><form action="/" method="post">
<label for="your_name">URL:</label>
    <input id="url_id" type="text" name="url">
    <input type="submit" value="Cleanup!">
</form></body></html>'''


error_msg = b'''<html><body>No URL specified</body></html>'''


def get(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [form]


def post(env, start_response):
    _in = env['wsgi.input'].read()
    # log.debug("got: {}".format(_in))
    # remove after the =
    _split = _in.split('=')
    if len(_split) < 2 or not _split[1]:
        log.info("No url provided")
        start_response('400 Bad Request', [CONTENT_TYPE])
        return [error_msg]

    # TODO check there's something after the =..
    _url = urllib.unquote(_split[1])

    # core method
    out = read_from_url(_url)

    log.debug("len(out): {}".format(len(out)))

    if type(out) is unicode:
        # VERY important - must be binary string
        # if unicode, uwsgi has undefined behaviour
        out = out.encode('utf-8')
    log.debug('type: {}'.format(type(out)))
    out_html = b'<html><head/><body><p><a href="{}">Original</a></p><p><pre>{}</pre></p></body></html>'.format(_url, out)
    tmpfile = tempfile.NamedTemporaryFile()
    with open(tmpfile.name, 'w') as f:
        f.write(out_html)
        log.debug("output saved as {}".format(tmpfile.name))
    start_response(
        '200 OK', [
            ('Content-Type', 'text/html'),
        ]
    )
    return [out_html]


def application(env, start_response):
    '''UWSGI entry point'''
    # log.debug('\n{}\n'.format(dir(env['wsgi.input'])))
    if env['REQUEST_METHOD'] == 'GET':
        return get(env, start_response)
    elif env['REQUEST_METHOD'] == 'POST':
        return post(env, start_response)
    else:
        pass
