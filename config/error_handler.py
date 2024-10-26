from flask import jsonify, request
import traceback
from time import strftime

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def exceptions(e):
        tb = traceback.format_exc()
        timestamp = strftime('[%Y-%b-%d %H:%M]')
        app.logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s', 
                         timestamp, request.remote_addr, request.method, 
                         request.scheme, request.full_path, tb)
        response = {
            "code": 500,
            "status": "Internal Server Error",
            "message": "An internal server error occurred. Please try again.",
            "data" : {}
        }
        return jsonify(response), 500

    @app.errorhandler(404)
    def not_found_error(e):
        timestamp = strftime('[%Y-%b-%d %H:%M]')
        app.logger.warning('%s %s %s %s %s 404 NOT FOUND', 
                           timestamp, request.remote_addr, request.method, 
                           request.scheme, request.full_path)
        response = {
            "code": 404,
            "status": "Not Found",
            "message": "The resource you are looking for could not be found.",
            "data" : {}
        }
        return jsonify(response), 404

    @app.errorhandler(405)
    def method_not_allowed_error(e):
        timestamp = strftime('[%Y-%b-%d %H:%M]')
        app.logger.warning('%s %s %s %s %s 405 METHOD NOT ALLOWED', 
                           timestamp, request.remote_addr, request.method, 
                           request.scheme, request.full_path)
        response = {
            "code": 405,
            "status": "Method Not Allowed",
            "message": "The method is not allowed for the requested URL.",
            "data" : {}
        }
        return jsonify(response), 405
