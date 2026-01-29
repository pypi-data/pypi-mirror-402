"""
Response formatting for bulk operations.

Provides structured result objects and response formatters for consistent API responses.
"""

from rest_framework.response import Response
from rest_framework import status


class BulkOperationResult:
    """
    Structured result object for bulk operations.

    Tracks created, updated, deleted instances and any failures.
    """

    def __init__(self):
        """Initialize empty result."""
        self.created = []  # List of created instances
        self.updated = []  # List of updated instances
        self.deleted = 0  # Count of deleted records
        self.failed = []  # List of failed items
        self.errors = {}  # {index: error_detail}
        self.metadata = {}  # Additional metadata (timing, etc.)

    def add_created(self, instance):
        """
        Add successfully created instance.

        Args:
            instance: Created model instance
        """
        self.created.append(instance)

    def add_updated(self, instance):
        """
        Add successfully updated instance.

        Args:
            instance: Updated model instance
        """
        self.updated.append(instance)

    def set_deleted_count(self, count):
        """
        Set count of deleted records.

        Args:
            count: Number of deleted records
        """
        self.deleted = count

    def add_failed(self, index, data, error):
        """
        Record failed operation.

        Args:
            index: Position in original request
            data: Original data that failed
            error: Error message/details
        """
        self.failed.append({"index": index, "data": data, "error": error})
        self.errors[str(index)] = error

    def add_error(self, index, error):
        """
        Add error for a specific index.

        Args:
            index: Position in original request
            error: Error details (dict or string)
        """
        self.errors[str(index)] = error

    def has_errors(self):
        """
        Check if any operations failed.

        Returns:
            True if there are errors, False otherwise
        """
        return len(self.errors) > 0

    def has_successes(self):
        """
        Check if any operations succeeded.

        Returns:
            True if there are successful operations
        """
        return len(self.created) > 0 or len(self.updated) > 0 or self.deleted > 0

    def get_all_instances(self):
        """
        Get all successful instances.

        Returns:
            Combined list of created and updated instances
        """
        instances = self.created + self.updated
        return instances

    def merge(self, other):
        """
        Merge another result into this one.

        Args:
            other: Another BulkOperationResult to merge
        """
        self.created.extend(other.created)
        self.updated.extend(other.updated)
        self.deleted += other.deleted
        self.failed.extend(other.failed)
        self.errors.update(other.errors)
        self.metadata.update(other.metadata)

    def to_dict(self):
        """
        Convert to dictionary for response.

        Returns:
            Dict with counts and error information
        """
        return {
            "created": len(self.created),
            "updated": len(self.updated),
            "deleted": self.deleted,
            "failed": len(self.failed),
            "errors": self.errors if self.errors else None,
        }

    def to_response(self, serializer=None, prefer_minimal=False):
        """
        Convert to DRF Response object.
        Auto-determines status code based on errors.

        Args:
            serializer: Optional serializer to format instance data
            prefer_minimal: If True, return minimal response

        Returns:
            rest_framework.response.Response
        """
        # Determine status code
        if not self.has_successes() and self.has_errors():
            # Complete failure
            response_status = status.HTTP_400_BAD_REQUEST
        elif self.has_errors():
            # Partial success
            response_status = status.HTTP_207_MULTI_STATUS
        else:
            # Complete success
            response_status = status.HTTP_200_OK

        # Format response data
        if prefer_minimal:
            data = BulkResponseFormatter.format_minimal(self)
        else:
            data = BulkResponseFormatter.format_full(self, serializer)

        return Response(data, status=response_status)


class BulkResponseFormatter:
    """
    Utility methods for formatting bulk responses.
    """

    @staticmethod
    def format_full(result, serializer=None, optimized_instances=None):
        """
        Format full bulk operation response.

        Args:
            result: BulkOperationResult instance
            serializer: Optional serializer for formatting instances
            optimized_instances: Optional pre-optimized instances (prevents N+1 queries)

        Returns:
            Dict with full response data
        """
        response_data = {
            "created": len(result.created),
            "updated": len(result.updated),
            "deleted": result.deleted,
            "failed": len(result.failed),
        }

        # Add instance data if serializer provided
        if serializer:
            # Use optimized instances if provided and non-empty, otherwise get from result
            all_instances = optimized_instances if optimized_instances else result.get_all_instances()

            if all_instances:
                # Support passing either a serializer class or an instance factory
                if isinstance(serializer, type):
                    ser = serializer(instance=all_instances, many=True)
                else:
                    # serializer is a callable (like self.get_serializer)
                    try:
                        ser = serializer(instance=all_instances, many=True)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Serializer call failed: {e}", exc_info=True)
                        raise

                response_data["data"] = ser.data
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("all_instances is empty/falsy, skipping data serialization")
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("serializer is falsy, skipping data serialization")

        # Add errors if any
        if result.errors:
            response_data["errors"] = result.errors

        # Add metadata if present
        if result.metadata:
            response_data["metadata"] = result.metadata

        return response_data

    @staticmethod
    def format_minimal(result):
        """
        Format minimal bulk operation response.

        Args:
            result: BulkOperationResult instance

        Returns:
            Dict with minimal response data (counts only)
        """
        return {
            "created": len(result.created),
            "updated": len(result.updated),
            "deleted": result.deleted,
            "failed": len(result.failed),
        }

    @staticmethod
    def format_success(result, serializer=None, prefer_minimal=False, optimized_instances=None):
        """
        Format successful bulk operation response.

        Args:
            result: BulkOperationResult instance
            serializer: Optional serializer for formatting instances
            prefer_minimal: If True, return minimal format
            optimized_instances: Optional pre-optimized instances (prevents N+1 queries)

        Returns:
            Dict with success response data
        """
        if prefer_minimal:
            return BulkResponseFormatter.format_minimal(result)
        return BulkResponseFormatter.format_full(result, serializer, optimized_instances)

    @staticmethod
    def format_partial_success(result, serializer=None, prefer_minimal=False, optimized_instances=None):
        """
        Format response when some operations failed.

        Args:
            result: BulkOperationResult instance
            serializer: Optional serializer for formatting instances
            prefer_minimal: If True, return minimal format without per-index errors
            optimized_instances: Optional pre-optimized instances (prevents N+1 queries)

        Returns:
            Dict with partial success response data
        """
        if prefer_minimal:
            # Minimal format: just counts, no detailed errors
            return BulkResponseFormatter.format_minimal(result)

        # Full format: includes errors and details
        return BulkResponseFormatter.format_full(result, serializer, optimized_instances)

    @staticmethod
    def format_error(errors, message=None):
        """
        Format complete failure response.

        Args:
            errors: Dict of {index: error_detail}
            message: Optional error message

        Returns:
            Dict with error response data
        """
        response_data = {"created": 0, "updated": 0, "deleted": 0, "failed": len(errors), "errors": errors}

        if message:
            response_data["message"] = message

        return response_data

    @staticmethod
    def format_validation_errors(validation_errors):
        """
        Format DRF validation errors for bulk response.

        Args:
            validation_errors: List or dict of DRF validation errors

        Returns:
            Dict mapping indices to error details
        """
        if isinstance(validation_errors, list):
            # List of errors per item
            return {str(idx): error for idx, error in enumerate(validation_errors) if error}
        elif isinstance(validation_errors, dict):
            # Dict already in correct format
            return validation_errors
        else:
            # Single error
            return {"0": validation_errors}
