import tornado.ioloop
import tornado.web
import json

options = {'port':8888}

wordlist = []
with open('sorted.txt') as f:
    wordlist = f.read().splitlines()
    wordlist = [word.lower() for word in wordlist]

max_suggestions = 10

class AutocompleteHandler(tornado.web.RequestHandler):
    def post(self):
        self.set_header("Content-Type", "application/javascript")
        prefix = self.get_body_argument('search_string');
        suggestions = [word for word in wordlist if word.startswith(prefix)]
        if len(suggestions) > max_suggestions:
            suggestions = suggestions[0:max_suggestions]
        self.write(json.dumps(suggestions))

def make_app():
    return tornado.web.Application([
        (r"/autocomplete", AutocompleteHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(options['port'])
    tornado.ioloop.IOLoop.current().start()
