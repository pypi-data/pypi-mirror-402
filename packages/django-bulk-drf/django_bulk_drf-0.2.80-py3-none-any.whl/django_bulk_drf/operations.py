"""
Core bulk operation logic.

Provides operation classes for:
- Bulk create
- Bulk update
- Bulk upsert
- Bulk delete

Pure Django ORM, no DRF dependencies.
"""

import logging

from .results import BulkOperationResult
from .queries import BulkQueryBuilder
from .utils import M2MHandler, build_unique_key
from .exceptions import ObjectNotFoundError, ForeignKeyNotFoundError
from .monitoring import get_monitor
from .settings import bulk_settings


logger = logging.getLogger(__name__)


def _find_problematic_records(model, instances, error):
    """
    Attempt to identify which records caused a database error.
    
    This is a best-effort function that tries to identify problematic records
    by testing them individually when a bulk operation fails.
    
    Args:
        model: The Django model class
        instances: List of model instances that were being processed
        error: The original exception
        
    Returns:
        Dict with 'error', 'problematic_indices', and 'problematic_data' keys
    """
    result = {
        'error': str(error),
        'error_type': type(error).__name__,
        'total_records': len(instances),
        'problematic_indices': [],
        'problematic_data': [],
    }
    
    # Try to identify which records are problematic by checking individual model validation
    for idx, instance in enumerate(instances):
        try:
            # Run Django model validation (doesn't hit database)
            instance.full_clean()
        except Exception as e:
            result['problematic_indices'].append(idx)
            # Capture the data that caused the issue
            data_snapshot = {}
            for field in model._meta.get_fields():
                if hasattr(field, 'attname') and hasattr(instance, field.attname):
                    try:
                        value = getattr(instance, field.attname)
                        # Convert to string for logging (handles various types)
                        data_snapshot[field.attname] = repr(value)
                    except Exception:
                        data_snapshot[field.attname] = '<unable to read>'
            
            result['problematic_data'].append({
                'index': idx,
                'error': str(e),
                'data': data_snapshot
            })
    
    return result


def _log_bulk_operation_error(operation_name, model, instances, error):
    """
    Log detailed information about a bulk operation error.
    
    Args:
        operation_name: Name of the operation (create, update, upsert)
        model: Django model class
        instances: List of model instances
        error: The exception that occurred
    """
    error_info = _find_problematic_records(model, instances, error)
    
    lines = [
        f"Bulk {operation_name} operation failed for model {model.__name__}",
        f"  Error Type: {error_info['error_type']}",
        f"  Error: {error_info['error']}",
        f"  Total Records: {error_info['total_records']}",
    ]
    
    if error_info['problematic_indices']:
        lines.append(f"  Problematic Indices: {error_info['problematic_indices']}")
        lines.append("  Problematic Records:")
        for record in error_info['problematic_data']:
            lines.append(f"    [{record['index']}] Error: {record['error']}")
            lines.append(f"        Data: {record['data']}")
    else:
        lines.append("  Could not identify specific problematic records via model validation.")
        lines.append("  First few instances for context:")
        for idx, instance in enumerate(instances[:3]):
            data_snapshot = {
                f.attname: repr(getattr(instance, f.attname, None))
                for f in model._meta.get_fields()
                if hasattr(f, 'attname') and hasattr(instance, f.attname)
            }
            lines.append(f"    [{idx}]: {data_snapshot}")
    
    logger.error("\n".join(lines))


class BulkOperation:
    """
    Abstract base for all bulk operations.
    Encapsulates common setup and result handling.
    """

    def __init__(self, model, unique_fields=None, batch_size=None, context=None):
        """
        Initialize operation with configuration.

        Args:
            model: Django model class
            unique_fields: List of fields for matching (upsert/update)
            batch_size: Records per batch
            context: Additional context (user, request, etc.)
        """
        self.model = model
        self.unique_fields = unique_fields or ["id"]
        self.batch_size = batch_size or bulk_settings.default_batch_size
        self.context = context or {}

        self.result = BulkOperationResult()
        self.query_builder = BulkQueryBuilder(model, self.unique_fields)
        self.m2m_handler = M2MHandler(model)

        # Get monitor from settings
        self.monitor = get_monitor()

    def execute(self, validated_data, m2m_data=None):
        """
        Execute the operation.
        Must be implemented by subclasses.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional M2M data list

        Returns:
            BulkOperationResult
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def get_result(self):
        """
        Get operation result object.

        Returns:
            BulkOperationResult instance
        """
        return self.result
    
    def _resolve_foreign_keys(self, validated_data):
        """
        Convert foreign key IDs to model instances efficiently.

        For fields that are ForeignKey relations, if the validated_data contains
        integer IDs (from PrimaryKeyRelatedField), we need to convert them to
        actual model instances before creating/updating Django model objects.

        This method does this in a single query per FK field (no N+1 queries).

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of validated data dicts with FK IDs replaced by instances

        Raises:
            ForeignKeyNotFoundError: If any foreign key IDs cannot be resolved
        """
        if not validated_data:
            return validated_data

        # Identify foreign key fields in the model
        fk_fields = {}
        for field in self.model._meta.get_fields():
            if field.many_to_one and field.concrete:  # ForeignKey
                fk_fields[field.name] = field

        if not fk_fields:
            # No foreign keys to resolve
            return validated_data

        # Collect all FK IDs that need to be fetched (grouped by field)
        fk_ids_to_fetch = {field_name: set() for field_name in fk_fields.keys()}

        for data in validated_data:
            for field_name, field in fk_fields.items():
                if field_name in data:
                    value = data[field_name]
                    # Check if it's an integer ID (not already a model instance)
                    if isinstance(value, int):
                        fk_ids_to_fetch[field_name].add(value)

        # Fetch all FK instances in a single query per field
        fk_instances = {}
        for field_name, ids in fk_ids_to_fetch.items():
            if ids:
                field = fk_fields[field_name]
                related_model = field.related_model
                # Single query to fetch all instances for this FK field
                instances = related_model.objects.filter(pk__in=ids)
                fk_instances[field_name] = {instance.pk: instance for instance in instances}

        # Check for missing foreign key references
        missing_references = {}
        for field_name, requested_ids in fk_ids_to_fetch.items():
            if field_name in fk_instances:
                found_ids = set(fk_instances[field_name].keys())
                missing_ids = requested_ids - found_ids
                if missing_ids:
                    missing_references[field_name] = sorted(list(missing_ids))

        # If any foreign keys are missing, raise an error with details
        if missing_references:
            raise ForeignKeyNotFoundError(missing_references)

        # Replace integer IDs with actual instances in validated_data (in-place)
        for data in validated_data:
            for field_name, field in fk_fields.items():
                if field_name in data:
                    value = data[field_name]
                    # Replace integer ID with instance
                    if isinstance(value, int) and field_name in fk_instances:
                        instance = fk_instances[field_name].get(value)
                        if instance is not None:
                            data[field_name] = instance

        return validated_data


class BulkCreateOperation(BulkOperation):
    """
    Bulk create operation using Model.objects.bulk_create().
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute bulk create.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional list of M2M data per item

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("create", len(validated_data)):
            # Prepare instances
            instances = self._prepare_instances(validated_data)

            try:
                # Batch create
                created_instances = self._batch_create(instances)
            except Exception as e:
                _log_bulk_operation_error("create", self.model, instances, e)
                raise

            # Set M2M relations if provided
            if m2m_data and bulk_settings.enable_m2m_handling:
                self.m2m_handler.set_m2m_relations(created_instances, m2m_data)

            # Add to result
            for instance in created_instances:
                self.result.add_created(instance)

        return self.result

    def _prepare_instances(self, validated_data):
        """
        Convert validated dicts to unsaved model instances.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of unsaved model instances
        """
        # Resolve foreign key IDs to instances (no N+1 queries)
        resolved_data = self._resolve_foreign_keys(validated_data)
        
        instances = []
        for data in resolved_data:
            instance = self.model(**data)
            instances.append(instance)
        return instances

    def _batch_create(self, instances):
        """
        Execute bulk_create, letting Django handle batching internally.

        Args:
            instances: List of model instances

        Returns:
            List of created instances with IDs
        """
        return self.model.objects.bulk_create(instances, batch_size=self.batch_size)


class BulkUpdateOperation(BulkOperation):
    """
    Bulk update operation using Model.objects.bulk_update().
    Requires all objects to exist.
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute bulk update.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional list of M2M data per item

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("update", len(validated_data)):
            # Fetch existing objects
            existing = self._fetch_existing(validated_data)

            # Validate all exist
            self._validate_all_exist(validated_data, existing)

            # Apply updates
            instances, update_fields = self._apply_updates(existing, validated_data)

            try:
                # Batch update
                self._batch_update(instances, update_fields)
            except Exception as e:
                _log_bulk_operation_error("update", self.model, instances, e)
                raise

            # Set M2M relations if provided
            if m2m_data and bulk_settings.enable_m2m_handling:
                self.m2m_handler.set_m2m_relations(instances, m2m_data)

            # Add to result
            for instance in instances:
                self.result.add_updated(instance)

        return self.result

    def _fetch_existing(self, validated_data):
        """
        Single query to fetch all existing objects.

        Args:
            validated_data: List of validated data dicts

        Returns:
            Dict mapping unique_key → instance
        """
        queryset = self.model.objects.all()
        return self.query_builder.fetch_by_unique_fields(queryset, validated_data)

    def _validate_all_exist(self, validated_data, existing):
        """
        Ensure all items in validated_data match existing objects.

        Args:
            validated_data: List of validated data dicts
            existing: Dict of existing instances by unique key

        Raises:
            ObjectNotFoundError: If any objects missing
        """
        missing_keys = []

        for data in validated_data:
            key = build_unique_key(data, self.unique_fields)
            if key not in existing:
                missing_keys.append(dict(zip(self.unique_fields, key)))

        if missing_keys:
            raise ObjectNotFoundError(missing_keys)

    def _apply_updates(self, existing, validated_data):
        """
        Apply validated_data updates to existing instances.

        Args:
            existing: Dict of existing instances by unique key
            validated_data: List of validated data dicts

        Returns:
            Tuple of (instances, update_fields)
        """
        # Resolve foreign key IDs to instances (no N+1 queries)
        resolved_data = self._resolve_foreign_keys(validated_data)
        
        instances = []
        all_fields = set()

        for data in resolved_data:
            key = build_unique_key(data, self.unique_fields)
            instance = existing[key]

            # Apply updates
            for field, value in data.items():
                if field not in self.unique_fields:  # Don't update unique fields
                    setattr(instance, field, value)
                    all_fields.add(field)

            instances.append(instance)

        # Return union of all fields being updated
        update_fields = list(all_fields)
        return instances, update_fields

    def _batch_update(self, instances, update_fields):
        """
        Execute bulk_update, letting Django handle batching internally.

        Args:
            instances: List of instances to update
            update_fields: List of fields to update
        """
        if not update_fields:
            return

        # Normalize field names: convert _id fields to standard Django field names
        from .utils import FieldConverter
        normalized_fields = FieldConverter.normalize_update_fields(update_fields, self.model)

        self.model.objects.bulk_update(instances, normalized_fields, batch_size=self.batch_size)


class BulkUpsertOperation(BulkOperation):
    """
    Bulk upsert (create or update) operation.
    Uses Django's bulk_create with update_conflicts=True for true upsert.
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute bulk upsert using bulk_create with update_conflicts=True.

        Args:
            validated_data: List of validated data dicts
            m2m_data: Optional list of M2M data per item

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("upsert", len(validated_data)):
            # Prepare instances
            instances = self._prepare_instances(validated_data)

            # Determine update_fields (all fields except unique_fields and auto-generated)
            update_fields = self._determine_update_fields(validated_data)

            # Normalize field names: convert _id fields to standard Django field names
            from .utils import FieldConverter
            normalized_unique_fields = FieldConverter.normalize_update_fields(self.unique_fields, self.model)
            normalized_update_fields = FieldConverter.normalize_update_fields(update_fields, self.model)

            try:
                # Batch upsert using bulk_create with update_conflicts
                upserted_instances = self._batch_upsert(
                    instances, 
                    normalized_unique_fields, 
                    normalized_update_fields
                )
            except Exception as e:
                _log_bulk_operation_error("upsert", self.model, instances, e)
                raise

            # Set M2M relations if provided
            if m2m_data and bulk_settings.enable_m2m_handling:
                self.m2m_handler.set_m2m_relations(upserted_instances, m2m_data)

            # Add to result - mark all as updated since we can't distinguish created vs updated
            # without an additional query (which defeats the purpose of true upsert)
            for instance in upserted_instances:
                self.result.add_updated(instance)

        return self.result

    def _prepare_instances(self, validated_data):
        """
        Convert validated dicts to unsaved model instances.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of unsaved model instances
        """
        # Resolve foreign key IDs to instances (no N+1 queries)
        resolved_data = self._resolve_foreign_keys(validated_data)
        
        instances = []
        for data in resolved_data:
            instance = self.model(**data)
            instances.append(instance)
        return instances

    def _determine_update_fields(self, validated_data):
        """
        Determine which fields should be updated during conflict resolution.
        Includes all fields present in the data except unique_fields.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of field names to update
        """
        all_fields = set()
        
        # Collect all fields from all records
        for data in validated_data:
            all_fields.update(data.keys())
        
        # Remove unique fields (they're used for matching, not updating)
        update_fields = [f for f in all_fields if f not in self.unique_fields]
        
        return update_fields

    def _batch_upsert(self, instances, unique_fields, update_fields):
        """
        Execute bulk_create with update_conflicts=True, letting Django handle batching internally.

        Args:
            instances: List of model instances
            unique_fields: List of normalized field names for uniqueness constraint
            update_fields: List of normalized field names to update on conflict

        Returns:
            List of upserted instances with IDs
        """
        return self.model.objects.bulk_create(
            instances,
            update_conflicts=True,
            unique_fields=unique_fields,
            update_fields=update_fields,
            batch_size=self.batch_size
        )


class BulkDeleteOperation(BulkOperation):
    """
    Bulk delete operation using QuerySet.delete().
    """

    def execute(self, validated_data, m2m_data=None):
        """
        Execute bulk delete.

        Args:
            validated_data: List of validated data dicts with unique field values
            m2m_data: Not used for delete operations

        Returns:
            BulkOperationResult
        """
        if not validated_data:
            return self.result

        with self.monitor.monitor_operation("delete", len(validated_data)):
            # Build queryset
            queryset = self._build_queryset(validated_data)

            # Execute delete
            count = self._batch_delete(queryset)

            # Set result
            self.result.set_deleted_count(count)

        return self.result

    def _build_queryset(self, validated_data):
        """
        Build queryset matching unique_fields in validated_data.

        Args:
            validated_data: List of validated data dicts

        Returns:
            Filtered queryset
        """
        q_filter = self.query_builder.build_lookup_filter(validated_data)
        return self.model.objects.filter(q_filter)

    def _batch_delete(self, queryset):
        """
        Execute delete.

        Args:
            queryset: Queryset to delete

        Returns:
            Total deleted count
        """
        deleted_count, _ = queryset.delete()
        return deleted_count
