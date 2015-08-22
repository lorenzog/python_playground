import argparse
import subprocess
import urllib
import tempfile

import requests


# def index(request):
#     if request.method == 'POST':
#         form = MyForm(request.POST)
#         if form.is_valid():
#             # return HttpResponseRedirect("/thanks/")
#             out = _do_cleanup(request)
#             return HttpResponse(out)
#     else:
#         form = MyForm()
#
#     return render(request, 'd.html', {'form': form})

def do_cleanup(localfile):
    out = subprocess.check_output(['html2text', localfile])
    return out

# alternative:
# from subprocess import Popen, PIPE, STDOUT
# p = Popen(['myapp'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
# stdout_data = p.communicate(input='data_to_write')[0]


form = b'''<html><body><form action="/" method="post">
<label for="your_name">URL:</label>
    <input id="url_id" type="text" name="url">
    <input type="submit" value="Cleanup!">
</form></body></html>'''

# REQUEST_URI
# wsgi.input: wsgi._Input
# PATH_INFO
def application(env, start_response):
    # print '\n{}\n'.format(dir(env['wsgi.input']))
    if env['REQUEST_METHOD'] == 'GET':
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [form]
    elif env['REQUEST_METHOD'] == 'POST':
        start_response('200 OK', [('Content-Type', 'text/plain')])
        _in = env['wsgi.input'].read()
        print "got: {}".format(_in)
        # remove after the =
        _split = _in.split('=')
        # out = read_from_file('/tmp/foo.html')
        # TODO check there's something after the =..
        out = read_from_url(urllib.unquote(_split[1]))
        return [out]
    else:
        pass


def usage():
    print 'foo'


def read_from_file(where):
    return do_cleanup(where)


def read_from_url(url):
    print "reading from {}".format(url)
    tmpfile = tempfile.NamedTemporaryFile()
    try:
        with open(tmpfile.name, 'wb') as f:
            response = requests.get(url)
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print e
        return e.message
    # now read from file
    return do_cleanup(tmpfile.name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--localfile')
    parser.add_argument('-u', '--url')
    args = parser.parse_args()

    done_something = False

    out = list()
    if args.localfile:
        _out = read_from_file(args.localfile)
        out.append(_out)
        done_something = True

    if args.url:
        _out = read_from_url(args.url)
        out.append(_out)
        done_something = True

    if not done_something:
        usage()
    else:
        print '\n'.join(out)


if __name__ == '__main__':
    main()
