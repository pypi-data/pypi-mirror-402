# from gevent import monkey
#
# monkey.patch_all()


# UNCOMMENT THIS IN CASE YOU'RE TESTING GEVENT WORKERS WITH SOCKET.IO

import os

if int(os.environ.get('PROFILE_MEM', '0')):
    from ul_api_utils.debug.malloc import trace_malloc

    with trace_malloc(show_all=True):
        from example.conf import sdk, db_config

        flask_app = sdk.init_with_flask(__name__, db_config=db_config)
else:
    from example.conf import sdk, db_config

    flask_app = sdk.init_with_flask(__name__, db_config=db_config)

__all__ = (
    'flask_app',
)
