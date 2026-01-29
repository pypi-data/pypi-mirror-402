"""
Custom routers for bulk operations.

Provides routers that map PATCH, PUT, and DELETE to collection endpoints.
"""

from rest_framework.routers import DefaultRouter, SimpleRouter


class BulkRouter(DefaultRouter):
    """
    Router that enables bulk operations on collection endpoints.

    Extends DefaultRouter to add PATCH, PUT, and DELETE methods to collection endpoints:
    - PATCH /items/ -> partial_update (bulk upsert)
    - PUT /items/ -> update (bulk update)
    - DELETE /items/ -> destroy (bulk delete)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Modify the default routes to include bulk operations on collection endpoint
        self.routes[0].mapping.update(
            {
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        )


class BulkSimpleRouter(SimpleRouter):
    """
    Simple router that enables bulk operations on collection endpoints.

    Like BulkRouter but without the API root view.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Modify the default routes to include bulk operations on collection endpoint
        self.routes[0].mapping.update(
            {
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        )
