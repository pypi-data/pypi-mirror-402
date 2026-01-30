# import os.path
# from tempfile import NamedTemporaryFile
#
# from flask import Flask, send_file, after_this_request, Response
#
# app = Flask(__name__)
#
#
# files = []
#
#
# # def _clean_files():
# #     print('_clean_files')
# #
# #
# # @app.after_request
# # def _after(resp):
# #     print('_after', resp)
# #     return resp
# #
# #
# # def _after_this(resp):
# #     print('_after_this', resp)
# #     return resp
#
#
# @app.route('/test')
# def donwload_test():
#     resp = Response("some")
#
#     after_this_request(_after_this)
#     resp.call_on_close(_clean_files)
#
#     return resp, 200
#
#
# # @app.teardown_request
# # def _teardown(exc):
# #     print('_teardown', str(exc))
#
#
# @app.route('/test-file')
# def donwload_test_file():
#     f = NamedTemporaryFile()
#     for ff in files:
#         print(f'{ff} = {os.path.exists(ff)}')
#     files.append(str(f.name))
#     # f.seek(0)
#     f.write(b'test\n')
#     f.write(b'test\n')
#     f.write(b'test\n')
#     f.write(b'test\n')
#
#     with open(f.name, 'w+t') as ff:
#         ff.write('SOME\n')
#         ff.write('SOME\n')
#         ff.write('SOME\n')
#         ff.write('SOME\n')
#
#     resp = send_file(f, mimetype='application/javascript')
#
#     # after_this_request(_after_this)
#     # resp.call_on_close(_clean_files)
#
#     return resp
