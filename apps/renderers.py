from rest_framework.renderers import JSONRenderer
from rest_framework import status


class ApiRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_dict = {
            'result': 1,
            'message': '',
            "errors": {},
            'data': {},
        }

        status_code = renderer_context["response"].status_code
        if not status.is_success(status_code):
            response_dict['result'] = 0
            response_dict['message'] = "errors"
            response_dict['errors'] = data.get('data')
        else:
            response_dict['data'] = data
        return super(ApiRenderer, self).render(response_dict, accepted_media_type, renderer_context)

