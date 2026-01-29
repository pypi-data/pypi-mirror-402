"""
Custom exceptions for bulk operations.

These exceptions provide domain-specific error handling for bulk operations,
with structured error information for better API responses.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class BulkOperationError(APIException):
    """Base exception for all bulk operation errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A bulk operation error occurred."
    default_code = "bulk_operation_error"


class DuplicateKeyError(BulkOperationError):
    """
    Raised when duplicate unique_field combinations found in request.

    Attributes:
        duplicates: List of duplicate unique_field combinations
    """

    default_detail = "Duplicate unique field combinations found in request."
    default_code = "duplicate_key"

    def __init__(self, duplicates, detail=None, code=None):
        """
        Initialize with list of duplicates.

        Args:
            duplicates: List of dicts containing duplicate unique field values
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.duplicates = duplicates
        if detail is None:
            detail = f"{self.default_detail} Found {len(duplicates)} duplicate(s)."
        super().__init__(detail, code)


class MissingUniqueFieldError(BulkOperationError):
    """
    Raised when required unique_field missing from data.

    Attributes:
        field: Name of missing field
        index: Position in data where field is missing
        indices: List of all positions where field is missing
    """

    default_detail = "Required unique field is missing from data."
    default_code = "missing_unique_field"

    def __init__(self, field, index=None, indices=None, detail=None, code=None):
        """
        Initialize with missing field information.

        Args:
            field: Name of the missing field
            index: Single index where field is missing (optional)
            indices: List of indices where field is missing (optional)
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.field = field
        self.index = index
        self.indices = indices or ([index] if index is not None else [])

        if detail is None:
            if self.indices:
                detail = f'Field "{field}" is missing at indices: {self.indices}'
            else:
                detail = f'Field "{field}" is required for this operation.'
        super().__init__(detail, code)


class BatchSizeExceededError(BulkOperationError):
    """
    Raised when request exceeds MAX_BATCH_SIZE.

    Attributes:
        size: Actual size of request
        max_size: Maximum allowed size
    """

    default_detail = "Request batch size exceeds maximum allowed."
    default_code = "batch_size_exceeded"

    def __init__(self, size, max_size, detail=None, code=None):
        """
        Initialize with size information.

        Args:
            size: Actual batch size
            max_size: Maximum allowed batch size
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.size = size
        self.max_size = max_size

        if detail is None:
            detail = f"Batch size {size} exceeds maximum allowed size of {max_size}."
        super().__init__(detail, code)


class BulkValidationError(BulkOperationError):
    """
    Raised when bulk data fails validation.

    Attributes:
        errors: Dict of {index: error_details}
    """

    default_detail = "Bulk data validation failed."
    default_code = "bulk_validation_error"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, errors, detail=None, code=None):
        """
        Initialize with validation errors.

        Args:
            errors: Dictionary mapping indices to error details
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.errors = errors

        if detail is None:
            error_count = len(errors)
            detail = f"Validation failed for {error_count} item(s)."
        super().__init__(detail, code)

    def get_full_details(self):
        """
        Get full error details including per-item errors.

        Returns:
            Dict with overall message and per-index errors
        """
        return {"message": str(self.detail), "code": self.default_code, "errors": self.errors}


class PartialBulkError(BulkOperationError):
    """
    Raised when some operations succeed but others fail.

    This exception is used when the failure strategy allows partial success.

    Attributes:
        successful: List of successful instances
        failed: List of failed items
        errors: Dict of {index: error}
    """

    default_detail = "Bulk operation completed with partial failures."
    default_code = "partial_bulk_error"
    status_code = status.HTTP_207_MULTI_STATUS

    def __init__(self, successful, failed, errors, detail=None, code=None):
        """
        Initialize with success and failure information.

        Args:
            successful: List of successfully processed instances
            failed: List of items that failed processing
            errors: Dictionary mapping indices to error details
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.successful = successful
        self.failed = failed
        self.errors = errors

        if detail is None:
            success_count = len(successful)
            fail_count = len(failed)
            detail = f"{success_count} succeeded, {fail_count} failed."
        super().__init__(detail, code)

    def to_response_data(self):
        """
        Convert to structured response data.

        Returns:
            Dict suitable for HTTP response
        """
        return {
            "message": str(self.detail),
            "code": self.default_code,
            "successful": len(self.successful),
            "failed": len(self.failed),
            "errors": self.errors,
        }


class UnsupportedBulkOperation(BulkOperationError):
    """
    Raised when operation not supported for this model/viewset.
    """

    default_detail = "This bulk operation is not supported."
    default_code = "unsupported_operation"
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED

    def __init__(self, operation=None, detail=None, code=None):
        """
        Initialize with operation information.

        Args:
            operation: Name of the unsupported operation
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.operation = operation

        if detail is None and operation:
            detail = f"Bulk {operation} operation is not supported."
        super().__init__(detail, code)


class ObjectNotFoundError(BulkOperationError):
    """
    Raised when objects required for update are not found.

    This is used specifically for bulk update operations where
    all objects must exist.
    """

    default_detail = "One or more objects not found."
    default_code = "object_not_found"
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, missing_keys, detail=None, code=None):
        """
        Initialize with missing key information.

        Args:
            missing_keys: List of unique field combinations that weren't found
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.missing_keys = missing_keys

        if detail is None:
            detail = f"{len(missing_keys)} object(s) not found for update."
        super().__init__(detail, code)


class ForeignKeyNotFoundError(BulkOperationError):
    """
    Raised when foreign key references cannot be resolved to existing objects.

    This occurs when foreign key IDs in the request data do not correspond
    to existing records in the related model.
    """

    default_detail = "One or more foreign key references not found."
    default_code = "foreign_key_not_found"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, missing_references, detail=None, code=None):
        """
        Initialize with missing foreign key reference information.

        Args:
            missing_references: Dict mapping field names to lists of missing IDs
                Example: {"financial_account": [1, 5], "category": [10]}
            detail: Optional custom error message
            code: Optional custom error code
        """
        self.missing_references = missing_references

        if detail is None:
            field_messages = []
            for field_name, missing_ids in missing_references.items():
                field_messages.append(f"{field_name}: IDs {missing_ids}")
            detail = f"Foreign key references not found - {', '.join(field_messages)}"
        super().__init__(detail, code)