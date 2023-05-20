from http.server import *
import re
import os

class RequestException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message   

class ResponseHandler(BaseHTTPRequestHandler):
    def __init__(self, args, directory, kwargs):
        self.path_function_registry = {
            'test' : test
        }
        super().__init__(args, directory, kwargs)

    def _validate_path(self):
        if self.path.count('/') != 2:
            raise RequestException(400, 'request path should be /command/')
        path = re.findall('(?<=\/).*(?=\/)', self.path)
        if len(path) == 0:
            raise RequestException(400, 'path is too short')
        elif len(path) > 1:
            raise RequestException(400, 'path is too long')
        else:
            path = path[0]
            if not self.path_function_registry.get(path):
                raise RequestException(400, 'command not supported')
        return path

    def _validate_params(self, query_param_string):
        if query_param_string[1] != '?':
            raise RequestException(400, "? not in query parameter string")
        terminator  = '$' if '&' not in query_param_string else '&'
        pattern     = '(?<=\?).*(?=%s)' % terminator
        param_list  = re.findall(pattern, query_param_string)
        if not param_list:
            raise RequestException(400, "no query parameters found that match \
                                    regex pattern %s" % pattern)
        query_params = {}
        for kv_string in param_list:
            if '=' not in kv_string:
                raise RequestException(400, "= not in query parameter string")
            split = kv_string.split('=')
            k = split[0]
            v = split[1]
            if not len(k) or not len(v):
                raise RequestException(400, "key or value is empty")
            else:
                query_params[k] = v
        return query_params
    
    def do_GET(self):
        try:
            path = self._validate_path()
            query_param_string = self.path.split(path)[1]
            query_params  = self._validate_params(query_param_string)
            func = self.path_function_registry.get(path)
            headers, response = func(query_params)
            self.send_response(200)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(response.encode())
        except RequestException as e:
            self.send_error(e.status_code, e.message)
            return
        except Exception as e:
            self.send_error(500, 'python api internal server error')

def test(query_params):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    test_file = os.path.join(this_dir, 'test.txt')
    headers = {
        'content-type': 'text/html'
    }
    with open(test_file, 'r') as f:
        response = "\r\n".join(f.readlines())
    return (headers, response)
    
server = HTTPServer(('', 5555), ResponseHandler)
server.serve_forever()