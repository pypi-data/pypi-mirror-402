"""
Custom middleware for CDCStream.
"""


class NoCacheMiddleware:
    """
    Add no-cache headers to all responses.
    This prevents browsers from showing stale content when the server is stopped.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add no-cache headers for HTML pages (not static assets)
        content_type = response.get('Content-Type', '')

        if 'text/html' in content_type:
            # Prevent caching of HTML pages
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        elif request.path.startswith('/api/'):
            # API responses should also not be cached
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        # Static assets (_next/, etc.) can be cached normally for performance

        return response




