from .response import json_response


def json_controller(func):
    ' controller that always return json '
    def response_as_json(request):
        response_data = func(request)
        return json_response(response_data)

    return response_as_json
