from flask import jsonify

def detail_response(detail: str, status_code: int):
    response = jsonify({"detail": detail})
    response.status_code = status_code
    return response
