from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    sessionFactory = SignedCookieSessionFactory('WK;/cB3qDe6{txr')

    with Configurator(settings=settings, session_factory=sessionFactory) as config:
        config.include('.models')
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.scan()
    return config.make_wsgi_app()
