from http.server import *
import re

class ResponseHandler(BaseHTTPRequestHandler):

    def __init__(self, args, directory, kwargs):
        self.path_function_registry = {
            'test' : self.test
        }
        super().__init__(args, directory, kwargs)

    def test(self, value):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        self.wfile.write('test complete'.encode())

    def _validate_path(self):
        status_code = 200
        message = None

        if self.path[0] != '/':
            status_code = 500
            message = 'first character of request was not /'
        
        if self.path.count('/') > 2:
            status_code = 400
            message = 'too many /'
        
        pattern = '(?<=\/).*(?=\/)'
        path = re.findall(pattern, self.path)
        
        if len(path) == 0:
            status_code = 400
            message = 'path is too short'
        elif len(path) > 1:
            status_code = 400
            message = 'path is too long'
        else:
            path = path[0]
            print(path)
            print('registry = ', self.path_function_registry)
            if not self.path_function_registry.get(path):
                status_code = 400
                message = 'command not supported'
        
        return (status_code, message, path)

    def _validate_params(self, query_param_string):
        status_code = 200
        message     = None

        if query_param_string[1] != '?':
            status_code = 400
            message = "? not in query parameter string"
        
        terminator  = '$' if '&' not in query_param_string else '&'
        pattern     = '(?<=\?).*(?=%s)' % terminator
        param_list  = re.findall(pattern, query_param_string)

        if not param_list:
            status_code = 400
            message = "no query parameters found that match regex pattern %s" % pattern
        
        query_params = {}

        for kv_string in param_list:
            if '=' not in kv_string:
                status_code = 400
                message = "= not in query parameter string"
            split = kv_string.split('=')
            k = split[0]
            v = split[1]
            if not len(k) or not len(v):
                status_code = 400
                message = "key or value is empty"
            else:
                query_params[k] = v

        print(query_params)
        return (status_code, message, query_params)
              
    def do_GET(self):
        status_code, message, path = self._validate_path()
        if status_code != 200:
            self.send_error(status_code, message)
            return
        
        query_param_string = self.path.split(path)[1]
        status_code, message, query_params  = self._validate_params(query_param_string)

        if status_code != 200:
            self.send_error(status_code, message)
            return
        
        print('registry = ', self.path_function_registry)
        print('path = ', path)
        func = self.path_function_registry.get(path)
        func(query_params)

port = HTTPServer(('', 5555), ResponseHandler)
port.serve_forever()