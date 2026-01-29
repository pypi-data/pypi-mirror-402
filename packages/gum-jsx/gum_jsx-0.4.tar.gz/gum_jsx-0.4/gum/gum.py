# terminal tools

import os
import json
import base64
import threading
import subprocess

##
## chafa interface
##

def snake_case(s):
    return s.replace('_', '-')

def readtext(path):
    with open(path, 'r') as fid:
        return fid.read()

def readbin(path):
    with open(path, 'rb') as fid:
        return fid.read()

def chafa(data, **kwargs):
    data = readbin(data) if isinstance(data, str) else data
    sargs = sum([
        [ f'--{snake_case(k)}', f'{v}' ] for k, v in kwargs.items() if v is not None
    ], [])
    subprocess.run([ 'chafa', *sargs, '-' ], input=data, stderr=subprocess.DEVNULL)

##
## error handling
##

class GumErrorType:
    PARSE = 'PARSE'
    NOCODE = 'NOCODE'
    NORETURN = 'NORETURN'
    NOELEMENT = 'NOELEMENT'

class GumError(Exception):
    def __init__(self, error_type, error_message):
        self.error_type = error_type
        self.error_message = error_message
        super().__init__(self.error_message)

##
## server interface
##

LIB_PATH = os.path.dirname(__file__)
GUM_PATH = os.path.join(LIB_PATH, 'gum-jsx/gum.js')

class GumUnixPipe:
    def __init__(self):
        self.proc = None
        self.debug = False
        self._pump_thread = None
        self.init()

    def __del__(self):
        self.close()

    def init(self):
        self.proc = subprocess.Popen(
            [ 'node', GUM_PATH ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # pump stderr to stdout
        self._start_pump_loop()

    def _start_pump_loop(self):
        def pump_loop():
            for line in self.proc.stderr:
                if self.debug:
                    print(f'[gum server] {line}')
        self._pump_thread = threading.Thread(target=pump_loop, daemon=True)
        self._pump_thread.start()

    def post(self, **request):
        # ensure server
        if self.proc is None:
            self.init()

        # send request
        request1 = { k: v for k, v in request.items() if v is not None }
        self.proc.stdin.write(json.dumps(request1) + '\n')
        self.proc.stdin.flush()

        # get reply
        reply = self.proc.stdout.readline()
        if reply == '':
            raise ValueError('[gum server] connection closed')

        # read response
        response = json.loads(reply)
        ok, result = response['ok'], response['result']

        # check for errors
        if not ok:
            etype = result['error']
            emsg = result['message']
            raise GumError(etype, emsg)

        # return response
        return result

    def close(self):
        if self.proc is not None:
            self.proc.stdin.close()
            self.proc.wait(timeout=1)
            self.proc = None
        self._pump_thread = None

    def restart(self):
        self.close()
        self.init()

    def evaluate(self, code, pixels=None, **kwargs):
        return self.post(code=code, size=pixels, **kwargs)

##
## server instance
##

# singleton server instance
server = GumUnixPipe()

def restart():
    server.restart()

def set_debug(debug=True):
    server.debug = debug

def evaluate(code, pixels=500, **kwargs):
    return server.evaluate(str(code), pixels=pixels, **kwargs)

def display(code, size='80x25', theme='dark', format=None, **kwargs):
    data = evaluate(str(code), theme=theme, **kwargs).encode()
    chafa(data, size=size, format=format)

def display_file(path, **kwargs):
    code = readtext(path)
    display(code, **kwargs)
