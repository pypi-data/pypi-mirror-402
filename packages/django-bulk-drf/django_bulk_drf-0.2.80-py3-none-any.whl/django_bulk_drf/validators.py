"""
Bulk-specific validation utilities.

Provides validation for:
- Unique field presence
- Duplicate detection
- Batch size limits
- Permission checks
"""

from .exceptions import MissingUniqueFieldError, DuplicateKeyError, BatchSizeExceededError, BulkValidationError
from .utils import build_unique_key


class BulkValidationMixin:
    """
    Validation utilities for bulk operations.
    Mixin for use in serializers or operations.
    """

    def validate_unique_fields_present(self, data, unique_fields):
        """
        Ensure all unique_fields exist in each data item.

        Args:
            data: List of data dicts
            unique_fields: List of required unique field names

        Raises:
            MissingUniqueFieldError: If any unique fields are missing
        """
        missing_indices = []
        missing_fields = set()

        for idx, item in enumerate(data):
            for field in unique_fields:
                if field not in item or item[field] is None:
                    missing_indices.append(idx)
                    missing_fields.add(field)

        if missing_indices:
            raise MissingUniqueFieldError(
                field=", ".join(missing_fields),
                indices=missing_indices,
                detail=f"Unique fields {missing_fields} missing at indices: {missing_indices}",
            )

    def validate_no_duplicate_keys(self, validated_data, unique_fields):
        """
        Check for duplicate unique_field combinations in request.

        Args:
            validated_data: List of validated data dicts
            unique_fields: List of unique field names

        Raises:
            DuplicateKeyError: If duplicates found
        """
        seen_keys = {}
        duplicates = []

        for idx, item in enumerate(validated_data):
            key = build_unique_key(item, unique_fields)

            if key in seen_keys:
                duplicates.append({"key": dict(zip(unique_fields, key)), "indices": [seen_keys[key], idx]})
            else:
                seen_keys[key] = idx

        if duplicates:
            raise DuplicateKeyError(duplicates)

    def validate_batch_size(self, data, max_size):
        """
        Ensure request doesn't exceed MAX_BATCH_SIZE.

        Args:
            data: List of data items
            max_size: Maximum allowed batch size

        Raises:
            BatchSizeExceededError: If batch is too large
        """
        actual_size = len(data) if isinstance(data, list) else 1

        if actual_size > max_size:
            raise BatchSizeExceededError(size=actual_size, max_size=max_size)

    def validate_update_permissions(self, user, instances):
        """
        Check user has permission to update all instances.

        This is a hook for custom permission logic.
        Override in subclasses to implement specific permission checks.

        Args:
            user: User making the request
            instances: List of instances to update

        Returns:
            True if user has permission, False otherwise
        """
        # Default: allow all (override in subclasses for custom logic)
        return True


class BulkDataValidator:
    """
    Validates bulk request data structure and constraints.
    """

    def __init__(self, unique_fields, max_batch_size):
        """
        Initialize with validation configuration.

        Args:
            unique_fields: List of unique field names
            max_batch_size: Maximum allowed batch size
        """
        self.unique_fields = unique_fields
        self.max_batch_size = max_batch_size
        self.errors = {}

    def validate_structure(self, data):
        """
        Validate data is list and each item is dict.

        Args:
            data: Request data

        Returns:
            Cleaned data

        Raises:
            BulkValidationError: If structure is invalid
        """
        if not isinstance(data, list):
            raise BulkValidationError(errors={"_": "Data must be a list for bulk operations"}, detail="Invalid data structure")

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                self.errors[str(idx)] = "Each item must be a dictionary"

        if self.errors:
            raise BulkValidationError(errors=self.errors)

        return data

    def validate_unique_constraints(self, validated_data):
        """
        Check unique_field constraints across all items.

        Args:
            validated_data: List of validated data dicts

        Raises:
            MissingUniqueFieldError: If required fields missing
            DuplicateKeyError: If duplicate keys found
        """
        # Check for missing unique fields
        self._check_missing_unique_fields(validated_data)

        # Check for duplicates
        self._check_duplicates(validated_data)

    def _check_missing_unique_fields(self, validated_data):
        """
        Check for missing unique fields.

        Args:
            validated_data: List of validated data dicts
        """
        missing_map = {}  # field -> [indices]

        for idx, item in enumerate(validated_data):
            for field in self.unique_fields:
                if field not in item or item[field] is None:
                    if field not in missing_map:
                        missing_map[field] = []
                    missing_map[field].append(idx)

        if missing_map:
            # Report first missing field
            field, indices = next(iter(missing_map.items()))
            raise MissingUniqueFieldError(field=field, indices=indices)

    def _check_duplicates(self, validated_data):
        """
        Check for duplicate unique keys.

        Args:
            validated_data: List of validated data dicts
        """
        seen_keys = {}
        duplicates = []

        for idx, item in enumerate(validated_data):
            key = build_unique_key(item, self.unique_fields)

            if key in seen_keys:
                duplicates.append({"key": dict(zip(self.unique_fields, key)), "indices": [seen_keys[key], idx]})
            else:
                seen_keys[key] = idx

        if duplicates:
            raise DuplicateKeyError(duplicates)

    def collect_errors(self):
        """
        Aggregate all validation errors.

        Returns:
            Dict of {index: errors}
        """
        return self.errors


def validate_bulk_request(data, unique_fields, max_batch_size):
    """
    Convenience function for validating bulk requests.

    Performs:
    - Structure validation
    - Batch size check
    - Unique field presence
    - Duplicate detection

    Args:
        data: Request data
        unique_fields: List of unique field names
        max_batch_size: Maximum allowed batch size

    Returns:
        Validated data

    Raises:
        BulkValidationError: If validation fails
        BatchSizeExceededError: If batch too large
        MissingUniqueFieldError: If unique fields missing
        DuplicateKeyError: If duplicates found
    """
    validator = BulkDataValidator(unique_fields, max_batch_size)

    # Validate structure
    data = validator.validate_structure(data)

    # Validate batch size
    if len(data) > max_batch_size:
        raise BatchSizeExceededError(size=len(data), max_size=max_batch_size)

    # Validate unique constraints
    validator.validate_unique_constraints(data)

    return data


def validate_for_update(data, unique_fields):
    """
    Validate data for update operation.

    Update requires all unique fields to be present.

    Args:
        data: List of data dicts
        unique_fields: List of unique field names

    Raises:
        MissingUniqueFieldError: If unique fields missing
    """
    missing_map = {}

    for idx, item in enumerate(data):
        for field in unique_fields:
            if field not in item:
                if field not in missing_map:
                    missing_map[field] = []
                missing_map[field].append(idx)

    if missing_map:
        field, indices = next(iter(missing_map.items()))
        raise MissingUniqueFieldError(
            field=field, indices=indices, detail=f'Update operation requires field "{field}" at indices: {indices}'
        )


def validate_for_delete(data, unique_fields):
    """
    Validate data for delete operation.

    Delete requires at least one unique field per item.

    Args:
        data: List of data dicts
        unique_fields: List of unique field names

    Raises:
        BulkValidationError: If no unique fields present
    """
    errors = {}

    for idx, item in enumerate(data):
        has_any_unique = any(field in item and item[field] is not None for field in unique_fields)
        if not has_any_unique:
            errors[str(idx)] = f"At least one unique field required: {unique_fields}"

    if errors:
        raise BulkValidationError(errors=errors, detail="Delete operation requires unique field identifiers")
