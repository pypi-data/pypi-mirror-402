"""
Field conversion and M2M handling utilities.

Provides utilities for:
- FK → FK_id field conversion with SlugField support
- M2M relationship extraction and bulk setting
- Batch processing helpers
"""

from django.db import models


class FieldConverter:
    """
    Converts between different field representations.
    Handles FK → FK_id conversion with SlugField support.
    """

    @staticmethod
    def fk_to_id(field_name):
        """
        Convert FK field name to _id field.

        Args:
            field_name: Foreign key field name (e.g., 'user')

        Returns:
            ID field name (e.g., 'user_id')
        """
        return f"{field_name}_id"

    @staticmethod
    def normalize_update_fields(field_names, model):
        """
        Convert _id field names to standard Django field names for bulk_update.
        
        Django's bulk_update expects field names (e.g., 'author') not database
        column names (e.g., 'author_id') for ForeignKey fields.
        
        Args:
            field_names: List or set of field names that may include _id suffixes
            model: Django model class
            
        Returns:
            List of normalized field names suitable for bulk_update
        """
        # Get all ForeignKey fields on the model
        fk_field_map = {}  # Maps 'field_name_id' -> 'field_name'
        for field in model._meta.get_fields():
            if field.many_to_one and field.concrete:  # ForeignKey
                fk_field_map[f"{field.name}_id"] = field.name
        
        # Convert _id fields to their standard field names
        normalized = []
        for field_name in field_names:
            if field_name in fk_field_map:
                # Convert author_id -> author
                normalized.append(fk_field_map[field_name])
            else:
                # Keep as-is for regular fields
                normalized.append(field_name)
        
        return normalized

    @staticmethod
    def get_model_fk_fields(model):
        """
        Get all ForeignKey field names from model.

        Args:
            model: Django model class

        Returns:
            List of FK field names
        """
        import logging
        logger = logging.getLogger(__name__)
        
        fk_fields = []
        all_fields = model._meta.get_fields()
        
        for field in all_fields:
            if isinstance(field, models.ForeignKey):
                fk_fields.append(field.name)
        
        return fk_fields

    @staticmethod
    def get_fk_field_info(model, fk_field_name):
        """
        Get detailed information about a FK field.

        Args:
            model: Django model class
            fk_field_name: Name of the FK field

        Returns:
            Dict with field info (related_model, to_field, etc.)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            field = model._meta.get_field(fk_field_name)
            
            if not isinstance(field, models.ForeignKey):
                logger.warning(f"Field {fk_field_name} on {model.__name__} is not a ForeignKey (type: {type(field).__name__})")
                return None

            # Handle different Django versions - to_field might be in different places
            to_field = None
            if hasattr(field, 'to_field'):
                to_field = field.to_field
            elif hasattr(field, 'remote_field') and hasattr(field.remote_field, 'field_name'):
                to_field = field.remote_field.field_name
            
            # Default to 'pk' if no specific to_field is set
            to_field = to_field or "pk"
            
            result = {
                "field": field,
                "related_model": field.related_model,
                "to_field": to_field,
                "db_column": field.db_column or f"{fk_field_name}_id",
            }
            return result
        except Exception as e:
            logger.error(f"Exception getting field info for {model.__name__}.{fk_field_name}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def is_slug_backed_fk(model, fk_field_name):
        """
        Return True if the fk_field targets a unique SlugField.

        Args:
            model: Django model class
            fk_field_name: Name of the FK field

        Returns:
            Boolean indicating if FK is slug-backed
        """
        field_info = FieldConverter.get_fk_field_info(model, fk_field_name)
        if not field_info:
            return False

        to_field = field_info["to_field"]
        if to_field == "pk":
            return False

        related_model = field_info["related_model"]
        try:
            related_field = related_model._meta.get_field(to_field)
            return isinstance(related_field, models.SlugField)
        except Exception:
            return False

    @staticmethod
    def collect_fk_identifiers(validated_data, model):
        """
        Scan the batch and collect identifiers for each FK field.

        Args:
            validated_data: List of validated data dicts
            model: Django model class

        Returns:
            Dict mapping fk_field_name to set of identifiers
        """
        import logging
        logger = logging.getLogger(__name__)
        
        fk_fields = FieldConverter.get_model_fk_fields(model)
        
        identifiers_map = {fk_field: set() for fk_field in fk_fields}

        for data in validated_data:
            for fk_field in fk_fields:
                if fk_field in data and data[fk_field] is not None:
                    identifiers_map[fk_field].add(data[fk_field])

        return {k: v for k, v in identifiers_map.items() if v}

    @staticmethod
    def resolve_fk_ids(model, fk_field_name, identifiers, slug_field=None):
        """
        Resolve identifiers to primary keys in a single query.

        Args:
            model: Django model class
            fk_field_name: Name of the FK field
            identifiers: Set/list of identifiers (ints or strings)
            slug_field: Optional slug field name to use for string identifiers (from serializer)

        Returns:
            Dict mapping identifier to pk
            
        Raises:
            ForeignKeyNotFoundError: If any identifiers cannot be resolved
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Import here to avoid circular dependency
        from .exceptions import ForeignKeyNotFoundError
        
        field_info = FieldConverter.get_fk_field_info(model, fk_field_name)
        if not field_info:
            logger.error(f"No field info found for {model.__name__}.{fk_field_name}")
            return {}

        related_model = field_info["related_model"]
        to_field = field_info["to_field"]


        # Check if all identifiers are integers (PKs)
        all_ints = all(isinstance(i, int) for i in identifiers)
        
        # Check if all identifiers are strings (slugs)
        all_strings = all(isinstance(i, str) for i in identifiers)

        # Determine which field to use for lookup
        lookup_field = to_field
        if slug_field:
            # Serializer specified a slug field - use that instead of model's to_field
            lookup_field = slug_field
        elif all_strings and to_field == "pk":
            # We have string identifiers but no slug_field specified - can't resolve
            raise ValueError(
                f"Cannot resolve string identifiers for FK field '{fk_field_name}' "
                f"without a slug_field. Please use BulkSlugRelatedField with slug_field parameter, "
                f"or set to_field on the model's ForeignKey."
            )

        # Query for resolution
        if lookup_field == "pk":
            queryset = related_model.objects.filter(pk__in=identifiers)
            results_list = list(queryset)
            result = {obj.pk: obj.pk for obj in results_list}
        else:
            # Lookup by slug/to_field
            lookup = {f"{lookup_field}__in": identifiers}
            queryset = related_model.objects.filter(**lookup)
            results_list = list(queryset)
            result = {getattr(obj, lookup_field): obj.pk for obj in results_list}
        
        # Check for missing identifiers and raise error if any are not found
        if len(result) < len(identifiers):
            missing = set(identifiers) - set(result.keys())
            logger.warning(f"Missing identifiers for {fk_field_name}: {missing}")
            # Raise ForeignKeyNotFoundError with proper format
            raise ForeignKeyNotFoundError({fk_field_name: sorted(list(missing))})
        
        return result

    @staticmethod
    def convert_related_fields_batch(validated_data, model, serializer=None):
        """
        Perform batched FK → _id conversion for the entire payload.
        No per-item database queries.

        Args:
            validated_data: List of validated data dicts
            model: Django model class
            serializer: Optional serializer instance to extract field metadata

        Returns:
            Updated validated_data with FK fields converted to _id fields
        """
        import logging
        logger = logging.getLogger(__name__)
        
        
        # Extract FK field metadata from serializer
        fk_metadata = {}
        if serializer:
            # Lazy import to avoid circular dependency
            from .relations import BulkSlugRelatedField
            for field_name, field in serializer.fields.items():
                if isinstance(field, BulkSlugRelatedField):
                    fk_metadata[field_name] = {
                        'slug_field': field.slug_field
                    }
        
        logger.debug(f"FK Metadata extracted: {fk_metadata}")
        
        # Collect all FK identifiers
        identifiers_map = FieldConverter.collect_fk_identifiers(validated_data, model)
        logger.debug(f"Identifiers collected: {identifiers_map}")

        # Resolve each FK field in a single query
        resolution_maps = {}
        for fk_field, identifiers in identifiers_map.items():
            if identifiers:
                slug_field = fk_metadata.get(fk_field, {}).get('slug_field')
                logger.debug(f"Resolving {fk_field}: identifiers={identifiers}, slug_field={slug_field}")
                resolution_maps[fk_field] = FieldConverter.resolve_fk_ids(
                    model, fk_field, identifiers, slug_field=slug_field
                )
                logger.debug(f"Resolution map for {fk_field}: {resolution_maps[fk_field]}")

        # Apply conversions to each data item
        for data in validated_data:
            for fk_field, resolution_map in resolution_maps.items():
                if fk_field in data and data[fk_field] is not None:
                    identifier = data[fk_field]
                    if identifier in resolution_map:
                        # Convert to _id field
                        id_field = FieldConverter.fk_to_id(fk_field)
                        data[id_field] = resolution_map[identifier]
                        logger.debug(f"Converted {fk_field}={identifier} -> {id_field}={resolution_map[identifier]}")
                        # Remove original FK field
                        del data[fk_field]
                    else:
                        logger.warning(f"Identifier {identifier} not found in resolution map for {fk_field}")

        logger.debug(f"Final data sample: {validated_data[0] if validated_data else 'empty'}")
        return validated_data

    @staticmethod
    def get_model_m2m_fields(model):
        """
        Get all ManyToMany field names from model.

        Args:
            model: Django model class

        Returns:
            List of M2M field names
        """
        m2m_fields = []
        for field in model._meta.get_fields():
            if isinstance(field, models.ManyToManyField):
                m2m_fields.append(field.name)
        return m2m_fields


class M2MHandler:
    """
    Handles ManyToMany relationships for bulk operations.
    M2M relations must be set after object creation.
    """

    def __init__(self, model):
        """
        Initialize with model class.

        Args:
            model: Django model class
        """
        self.model = model
        self.m2m_fields = FieldConverter.get_model_m2m_fields(model)

    def extract_m2m_data(self, validated_data):
        """
        Remove M2M fields from validated_data.

        Args:
            validated_data: List of validated data dicts

        Returns:
            Tuple of (cleaned_data, m2m_data_list)
            where m2m_data_list is a list of M2M data per item
        """
        m2m_data_list = []

        for data in validated_data:
            item_m2m = {}
            for field_name in self.m2m_fields:
                if field_name in data:
                    item_m2m[field_name] = data.pop(field_name)
            m2m_data_list.append(item_m2m)

        return validated_data, m2m_data_list

    def set_m2m_relations(self, instances, m2m_data_list):
        """
        Set M2M relations for bulk created/updated instances using batched writes.

        Must be called after objects have IDs.

        Args:
            instances: List of model instances
            m2m_data_list: List of M2M data dicts (one per instance)
        """
        # Early exit: no instances or no M2M fields on model
        if not instances or not self.m2m_fields:
            return
        
        if len(instances) != len(m2m_data_list):
            raise ValueError(f"Mismatch: {len(instances)} instances but {len(m2m_data_list)} M2M data items")

        # Early exit: check if any M2M data exists
        has_m2m_data = any(m2m_data for m2m_data in m2m_data_list)
        if not has_m2m_data:
            return

        # Aggregate all through-model rows to insert per field
        field_to_rows = {}
        field_to_clear = {}

        # Collect rows
        for instance, m2m_data in zip(instances, m2m_data_list):
            for field_name, values in m2m_data.items():
                if values is None:
                    continue
                # Clear existing relations for updates (replace semantics)
                field_to_clear.setdefault(field_name, []).append(instance.pk)

                # Normalize values to list of IDs
                if values and hasattr(values, "__iter__") and not isinstance(values, (str, bytes)):
                    ids = [getattr(v, "pk", v) for v in values]
                else:
                    ids = [getattr(values, "pk", values)] if values is not None else []

                # Prepare through rows later when we have the through model
                field_to_rows.setdefault(field_name, []).append((instance.pk, ids))

        # Execute clears and bulk inserts per field (only for fields with data)
        for field_name in field_to_clear.keys() | field_to_rows.keys():
            pk_list = field_to_clear.get(field_name, [])
            rows = field_to_rows.get(field_name, [])
            
            if not pk_list and not rows:
                continue

            rel = self.model._meta.get_field(field_name)
            through = rel.remote_field.through
            source_column = rel.m2m_column_name()
            target_column = rel.m2m_reverse_name()

            # Clear existing relations in a single delete per field
            if pk_list:
                through.objects.filter(**{f"{source_column}__in": pk_list}).delete()

            # Build through instances to insert
            to_create = []
            for instance_pk, target_ids in rows:
                for target_pk in target_ids:
                    row = through(**{source_column: instance_pk, target_column: target_pk})
                    to_create.append(row)

            if to_create:
                through.objects.bulk_create(to_create, batch_size=1000)

    def set_m2m_field(self, instance, field_name, values):
        """
        Set M2M field for a single instance.

        Args:
            instance: Model instance
            field_name: Name of M2M field
            values: List of related objects or IDs
        """
        m2m_manager = getattr(instance, field_name)
        m2m_manager.set(values)

    def clear_and_set(self, instance, field_name, values):
        """
        Clear existing M2M relations and set new ones.
        Used for update/upsert operations.

        Args:
            instance: Model instance
            field_name: Name of M2M field
            values: List of related objects or IDs
        """
        m2m_manager = getattr(instance, field_name)
        m2m_manager.clear()
        if values:
            m2m_manager.set(values)


class BatchProcessor:
    """
    Utility for processing large datasets in chunks.
    """

    def __init__(self, batch_size):
        """
        Initialize with batch size.

        Args:
            batch_size: Number of items per batch
        """
        self.batch_size = batch_size

    def process_in_batches(self, items, processor_func):
        """
        Process items in batches.

        Args:
            items: List of items to process
            processor_func: Function called for each batch

        Returns:
            Combined results from all batches
        """
        results = []
        for batch in self.chunk_list(items):
            batch_result = processor_func(batch)
            if batch_result:
                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)
        return results

    def chunk_list(self, items):
        """
        Split list into chunks of batch_size.
        Generator function for memory efficiency.

        Args:
            items: List of items to chunk

        Yields:
            Chunks of batch_size items
        """
        for i in range(0, len(items), self.batch_size):
            yield items[i : i + self.batch_size]


def normalize_unique_fields(model, unique_fields):
    """
    Normalize unique_fields to use _id suffix for ForeignKey fields.
    
    This ensures consistency when FK fields are converted to _id in validated_data.
    
    Args:
        model: Django model class
        unique_fields: List of field names (may include FK field names)
    
    Returns:
        List of normalized field names (FK fields converted to field_id)
    
    Example:
        Input: ['account_number', 'financial_provider']
        Output: ['account_number', 'financial_provider_id']
    """
    normalized = []
    
    for field_name in unique_fields:
        try:
            field_obj = model._meta.get_field(field_name)
            if isinstance(field_obj, models.ForeignKey):
                # Convert FK field to _id field
                normalized.append(f"{field_name}_id")
            else:
                normalized.append(field_name)
        except Exception:
            # Field not found in model, keep as-is
            normalized.append(field_name)
    
    return normalized


def build_unique_key(data, unique_fields):
    """
    Build a unique key tuple from data and unique_fields.

    Args:
        data: Dictionary of field values
        unique_fields: List of field names to use for key

    Returns:
        Tuple of values for unique_fields
    """
    return tuple(data.get(field) for field in unique_fields)


def extract_unique_keys(validated_data, unique_fields):
    """
    Extract unique keys from validated data.

    Args:
        validated_data: List of validated data dicts
        unique_fields: List of field names to use for keys

    Returns:
        List of unique key tuples
    """
    return [build_unique_key(data, unique_fields) for data in validated_data]


def build_lookup_dict(instances, unique_fields):
    """
    Build a lookup dictionary mapping unique keys to instances.

    Args:
        instances: List of model instances
        unique_fields: List of field names to use for keys

    Returns:
        Dict mapping unique_key → instance
    """
    lookup = {}
    for instance in instances:
        key = tuple(getattr(instance, field) for field in unique_fields)
        lookup[key] = instance
    return lookup
