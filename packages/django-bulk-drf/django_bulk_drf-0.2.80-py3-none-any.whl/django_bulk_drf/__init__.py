"""
Django Bulk DRF - High-performance bulk operations for Django REST Framework.

Provides bulk create, update, upsert, and delete operations with:
- Single-query fetches and batch processing
- Automatic FK and M2M handling
- Transaction safety with configurable failure strategies
- Performance monitoring
- Clean RESTful API design

Example usage:
    from django_bulk_drf import BulkModelViewSet, BulkModelSerializer

    class ProductSerializer(BulkModelSerializer):
        class Meta:
            model = Product
            fields = '__all__'

    class ProductViewSet(BulkModelViewSet):
        queryset = Product.objects.all()
        serializer_class = ProductSerializer
        unique_fields = ['sku']
"""

__version__ = "0.2.34"
__author__ = "Django Bulk DRF Contributors"

# Setup logging to be disabled by default unless explicitly configured
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Serializers
from .serializers import (
    BulkSerializerMixin,
    BulkListSerializer,
    BulkModelSerializer,
)

# Bulk-safe field classes (no DB queries during validation)
from .relations import (
    BulkPrimaryKeyRelatedField,
    BulkSlugRelatedField,
)

# ViewSets
from .viewsets import (
    BulkOperationMixin,
    BulkModelViewSet,
)

# Routers
from .routers import (
    BulkRouter,
    BulkSimpleRouter,
)

# Mixins (for granular control)
from .mixins import (
    BulkCreateMixin,
    BulkUpdateMixin,
    BulkUpsertMixin,
    BulkDestroyMixin,
)

# Operations (for advanced usage)
from .operations import (
    BulkOperation,
    BulkCreateOperation,
    BulkUpdateOperation,
    BulkUpsertOperation,
    BulkDeleteOperation,
)

# Results
from .results import (
    BulkOperationResult,
    BulkResponseFormatter,
)

# Exceptions
from .exceptions import (
    BulkOperationError,
    DuplicateKeyError,
    MissingUniqueFieldError,
    BatchSizeExceededError,
    BulkValidationError,
    PartialBulkError,
    UnsupportedBulkOperation,
    ObjectNotFoundError,
)

# Settings
from .settings import (
    BulkSettings,
    PartialFailureStrategy,
    bulk_settings,
)


# Monitoring
from .monitoring import (
    BulkPerformanceMonitor,
    BulkMetrics,
)

# Utilities (for advanced usage)
from .utils import (
    FieldConverter,
    M2MHandler,
    BatchProcessor,
)

# Query builders (for advanced usage)
from .queries import (
    BulkQueryBuilder,
    QueryOptimizer,
)

# Validators (for advanced usage)
from .validators import (
    BulkValidationMixin,
    BulkDataValidator,
    validate_bulk_request,
)

# Transactions (for advanced usage)
from .transactions import (
    BulkTransactionManager,
    bulk_atomic,
)

# Define public API
__all__ = [
    # Version
    "__version__",
    # Core classes (most commonly used)
    "BulkModelSerializer",
    "BulkModelViewSet",
    # Serializers
    "BulkSerializerMixin",
    "BulkListSerializer",
    "BulkPrimaryKeyRelatedField",
    "BulkSlugRelatedField",
    # ViewSets
    "BulkOperationMixin",
    # Routers
    "BulkRouter",
    "BulkSimpleRouter",
    # Mixins
    "BulkCreateMixin",
    "BulkUpdateMixin",
    "BulkUpsertMixin",
    "BulkDestroyMixin",
    # Operations
    "BulkOperation",
    "BulkCreateOperation",
    "BulkUpdateOperation",
    "BulkUpsertOperation",
    "BulkDeleteOperation",
    # Results
    "BulkOperationResult",
    "BulkResponseFormatter",
    # Exceptions
    "BulkOperationError",
    "DuplicateKeyError",
    "MissingUniqueFieldError",
    "BatchSizeExceededError",
    "BulkValidationError",
    "PartialBulkError",
    "UnsupportedBulkOperation",
    "ObjectNotFoundError",
    # Settings
    "BulkSettings",
    "PartialFailureStrategy",
    "bulk_settings",
    # Monitoring
    "BulkPerformanceMonitor",
    "BulkMetrics",
    # Utilities
    "FieldConverter",
    "M2MHandler",
    "BatchProcessor",
    "BulkQueryBuilder",
    "QueryOptimizer",
    "BulkValidationMixin",
    "BulkDataValidator",
    "validate_bulk_request",
    "BulkTransactionManager",
    "bulk_atomic",
]
