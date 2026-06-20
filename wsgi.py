from gevent import monkey
monkey.patch_all()


import os
from app import create_app, socketio

env = os.environ.get('FLASK_ENV', 'development')   # default to dev, not prod
app = create_app(env)

# ProxyFix — required when running behind Nginx reverse proxy
# Makes Flask see real client IP and correct HTTPS scheme
# Without this: url_for(_external=True) generates http:// instead of https://
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

if __name__ == '__main__':
    debug = (env == 'development')
    print(f"\n  iJodidar starting in [{env}] mode")
    print(f"  Open http://localhost:5000\n")
    socketio.run(
        app,
        host     = '127.0.0.1',
        port     = 5000,
        debug    = debug,
        use_reloader = debug,
        log_output   = True,
    )
