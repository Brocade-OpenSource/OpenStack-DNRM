import webob


class HTTPRequest(webob.Request):

    @classmethod
    def blank(cls, *args, **kwargs):
        kwargs['base_url'] = 'http://localhost'
        out = webob.Request.blank(*args, **kwargs)
        return out
