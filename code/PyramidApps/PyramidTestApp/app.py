from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response

def Pyramid_Test(request):
    return Response('Pyramid is Running!')

if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('running', '/')
        config.add_view(Pyramid_Test, route_name='running')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
