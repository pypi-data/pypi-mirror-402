"""
Serializer layer for bulk operations.

Provides:
- Custom bulk-safe field classes (no DB queries during validation)
- Custom bulk-safe validators (no DB queries during validation)
- BulkSerializerMixin: Preprocessing utilities
- BulkListSerializer: Coordination and delegation
- BulkModelSerializer: Main serializer class
"""

from rest_framework import serializers
from .operations import BulkCreateOperation, BulkUpdateOperation, BulkUpsertOperation
from .results import BulkOperationResult
from .utils import FieldConverter, M2MHandler
from .settings import bulk_settings
from .relations import BulkPrimaryKeyRelatedField, BulkSlugRelatedField


class BulkSerializerMixin:
    """
    Preprocessing utilities for bulk serialization.
    Handles FK → FK_id conversion and M2M extraction.
    """

    def to_internal_value(self, data):
        """
        Override to handle bulk-specific field transformations.

        Args:
            data: Input data dict

        Returns:
            Validated internal data
        """
        # Call parent to_internal_value first
        validated_data = super().to_internal_value(data)

        # Note: FK conversion and M2M extraction are now done in bulk
        # by the ListSerializer, not per-item

        return validated_data

    def _convert_fk_to_id_fields(self, data):
        """
        Transform foreign key references to database-friendly format.

        Note: This is now a no-op as conversion happens in bulk.
        Kept for compatibility.

        Args:
            data: Data dict

        Returns:
            Transformed data
        """
        return data

    def _extract_m2m_fields(self, validated_data):
        """
        Separate M2M fields from main data.
        M2M relations must be set after object creation.

        Args:
            validated_data: Validated data dict

        Returns:
            Tuple of (cleaned_data, m2m_data)
        """
        if not hasattr(self.Meta, "model"):
            return validated_data, {}

        model = self.Meta.model
        m2m_fields = FieldConverter.get_model_m2m_fields(model)

        m2m_data = {}
        for field_name in m2m_fields:
            if field_name in validated_data:
                m2m_data[field_name] = validated_data.pop(field_name)

        return validated_data, m2m_data


class BulkListSerializer(serializers.ListSerializer):
    """
    Coordinator for bulk operations.
    Delegates to operation classes, handles result formatting.
    
    This uses standard DRF validation with NO runtime patching.
    To avoid N+1 queries, use Bulk* field classes (BulkPrimaryKeyRelatedField, etc.)
    and avoid UniqueValidator/UniqueTogetherValidator in your child serializer.
    
    Database validation happens in the operations layer with batched queries.
    """
    
    # No custom is_valid() - uses standard DRF validation
    # No runtime patching - serializer should be configured correctly from the start
    
    def _run_validation(self, data):
        """
        Perform validation without database hits.
        
        This method validates structure and field types without querying the database.
        Database validation (existence checks, FK validation) is deferred to the
        operation layer where it can be done in bulk.
        
        Args:
            data: List of data dicts
            
        Returns:
            List of validated data dicts
            
        Raises:
            ValidationError: If validation fails
        """
        # Ensure data is a list
        if not isinstance(data, list):
            raise serializers.ValidationError({
                'non_field_errors': ['Expected a list of items but got type "{0}".'.format(type(data).__name__)]
            })
        
        if not self.allow_empty and len(data) == 0:
            raise serializers.ValidationError({
                'non_field_errors': ['This list may not be empty.']
            })
        
        # Validate each item
        ret = []
        errors = []
        
        for item in data:
            try:
                # Validate individual item using child serializer
                # This performs field-level validation without DB queries
                validated = self._validate_single_item_without_database_access(item)
                ret.append(validated)
                errors.append({})
            except serializers.ValidationError as exc:
                ret.append({})
                errors.append(exc.detail)
        
        # Check if any errors occurred
        if any(errors):
            raise serializers.ValidationError(errors)
        
        return ret
    
    def _validate_single_item_without_database_access(self, item):
        """
        Validate a single item without database queries.
        
        Uses the child serializer's to_internal_value for field validation,
        but skips unique validators and FK existence checks.
        
        Args:
            item: Data dict for single item
            
        Returns:
            Validated data dict
            
        Raises:
            ValidationError: If field validation fails
        """
        # Use child serializer for field-level validation
        # This validates data types, required fields, etc. without DB queries
        # The validators have been disabled, so this should not hit the database
        return self.child.to_internal_value(item)

    def create(self, validated_data):
        """
        Delegate to BulkCreateOperation.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of created instances
        """
        # Extract M2M data
        validated_data, m2m_data_list = self._extract_m2m_data(validated_data)

        # Convert FK fields in batch
        validated_data = self._convert_fk_fields_batch(validated_data)

        # Extension hook: allow child serializer to handle bulk create
        if hasattr(self.child, "bulk_create"):
            result = self.child.bulk_create(validated_data)
            if isinstance(result, BulkOperationResult):
                self.bulk_result = result
                return result.get_all_instances()
            return result

        # Get operation context
        context = self._prepare_operation_context()

        # Execute operation
        operation = BulkCreateOperation(
            model=context["model"], unique_fields=context.get("unique_fields"), batch_size=context.get("batch_size"), context=context
        )

        result = operation.execute(validated_data, m2m_data_list)

        # Expose operation result for viewset response formatting
        self.bulk_result = result

        return result.get_all_instances()

    def update(self, validated_data):
        """
        Delegate to BulkUpdateOperation.
        Requires all objects exist and unique fields are present.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of updated instances
        """
        # Extract M2M data
        validated_data, m2m_data_list = self._extract_m2m_data(validated_data)

        # Convert FK fields in batch
        validated_data = self._convert_fk_fields_batch(validated_data)

        # Extension hook: allow child serializer to handle bulk update
        if hasattr(self.child, "bulk_update"):
            result = self.child.bulk_update(validated_data)
            if isinstance(result, BulkOperationResult):
                self.bulk_result = result
                return result.get_all_instances()
            return result

        # Get operation context
        context = self._prepare_operation_context()

        # Execute operation
        operation = BulkUpdateOperation(
            model=context["model"], unique_fields=context.get("unique_fields"), batch_size=context.get("batch_size"), context=context
        )

        result = operation.execute(validated_data, m2m_data_list)

        # Expose operation result for viewset response formatting
        self.bulk_result = result

        return result.get_all_instances()

    def upsert(self, validated_data):
        """
        Delegate to BulkUpsertOperation.
        Creates new or updates existing based on unique_fields.

        Args:
            validated_data: List of validated data dicts

        Returns:
            List of instances (created + updated)
        """
        # Extract M2M data
        validated_data, m2m_data_list = self._extract_m2m_data(validated_data)

        # Convert FK fields in batch
        validated_data = self._convert_fk_fields_batch(validated_data)

        # Extension hook: allow child serializer to handle bulk upsert
        if hasattr(self.child, "bulk_upsert"):
            result = self.child.bulk_upsert(validated_data)
            if isinstance(result, BulkOperationResult):
                self.bulk_result = result
                return result.get_all_instances()
            return result

        # Get operation context
        context = self._prepare_operation_context()

        # Execute operation
        operation = BulkUpsertOperation(
            model=context["model"], unique_fields=context.get("unique_fields"), batch_size=context.get("batch_size"), context=context
        )

        result = operation.execute(validated_data, m2m_data_list)

        # Expose operation result for viewset response formatting
        self.bulk_result = result

        return result.get_all_instances()

    def _extract_m2m_data(self, validated_data):
        """
        Extract M2M fields from validated data.

        Args:
            validated_data: List of validated data dicts

        Returns:
            Tuple of (cleaned_data, m2m_data_list)
        """
        if not bulk_settings.enable_m2m_handling:
            return validated_data, []

        model = self._get_model()
        if not model:
            return validated_data, []

        m2m_handler = M2MHandler(model)
        return m2m_handler.extract_m2m_data(validated_data)

    def _convert_fk_fields_batch(self, validated_data):
        """
        Convert FK fields to _id fields for entire batch.
        Single query per FK field.

        Args:
            validated_data: List of validated data dicts

        Returns:
            Updated validated_data
        """
        model = self._get_model()
        if not model:
            return validated_data

        # Pass self.child so FieldConverter can inspect field configurations (e.g., slug_field)
        return FieldConverter.convert_related_fields_batch(validated_data, model, self.child)

    def _get_model(self):
        """
        Get model class from child serializer.

        Returns:
            Model class or None
        """
        if hasattr(self.child, "Meta") and hasattr(self.child.Meta, "model"):
            return self.child.Meta.model
        return None

    def _prepare_operation_context(self):
        """
        Extract context needed by operations.

        Returns:
            Dict with operation context
        """
        context = {
            "model": self._get_model(),
            "unique_fields": self.context.get("unique_fields", ["id"]),
            "batch_size": self.context.get("batch_size", bulk_settings.default_batch_size),
            "user": self.context.get("request").user if self.context.get("request") else None,
            "request": self.context.get("request"),
            "view": self.context.get("view"),
            "serializer_class": self.child.__class__,  # Pass serializer class for query optimization
        }
        return context

    def _get_operation_for_type(self, operation_type_string):
        """
        Factory method to instantiate correct operation class.

        Args:
            operation_type_string: 'create', 'update', or 'upsert'

        Returns:
            Operation instance
        """
        context = self._prepare_operation_context()

        if operation_type_string == "create":
            return BulkCreateOperation(
                model=context["model"], unique_fields=context.get("unique_fields"), batch_size=context.get("batch_size"), context=context
            )
        elif operation_type_string == "update":
            return BulkUpdateOperation(
                model=context["model"], unique_fields=context.get("unique_fields"), batch_size=context.get("batch_size"), context=context
            )
        elif operation_type_string == "upsert":
            return BulkUpsertOperation(
                model=context["model"], unique_fields=context.get("unique_fields"), batch_size=context.get("batch_size"), context=context
            )
        else:
            raise ValueError(f"Unknown operation type: {operation_type_string}")

    def _format_operation_result_for_output(self, operation_result):
        """
        Convert BulkOperationResult to serializer output.

        Args:
            operation_result: BulkOperationResult instance

        Returns:
            List of serialized instances
        """
        instances = operation_result.get_all_instances()
        return self.child.serialize(instances, many=True)


class BulkModelSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    """
    Main serializer users inherit from.
    Auto-uses BulkListSerializer when many=True.
    
    Automatically creates bulk-safe relational fields by overriding DRF's field builders:
    - ForeignKey fields → BulkPrimaryKeyRelatedField
    - This ensures no N+1 queries during validation without post-creation conversion.
    
    Third-party compatibility:
    - Nested serializers (drf-flex-fields, drf-writable-nested) are automatically preserved
    - Only exact DRF field classes are converted (not custom subclasses)
    - Override _should_convert_field() for custom field handling
    - Override _should_strip_field_validators() for custom validator handling
    - Override get_list_serializer_class() for custom list serializer
    """
    
    def build_relational_field(self, field_name, relation_info):
        """
        Override DRF's field builder to create bulk-safe relational fields directly.
        
        This is called by ModelSerializer when it encounters ForeignKey/related fields
        during field construction. By overriding it, we create BulkPrimaryKeyRelatedField
        from the start, avoiding redundant source parameters.
        
        Args:
            field_name: Name of the field on the serializer
            relation_info: RelationInfo namedtuple from DRF
            
        Returns:
            Tuple of (field_class, field_kwargs)
        """
        field_class, field_kwargs = super().build_relational_field(field_name, relation_info)
        
        # If DRF would create a PrimaryKeyRelatedField, use our bulk version instead
        from rest_framework.relations import PrimaryKeyRelatedField as DRFPrimaryKeyRelatedField
        from rest_framework.relations import SlugRelatedField as DRFSlugRelatedField
        
        if field_class == DRFPrimaryKeyRelatedField:
            return BulkPrimaryKeyRelatedField, field_kwargs
        elif field_class == DRFSlugRelatedField:
            return BulkSlugRelatedField, field_kwargs
        
        return field_class, field_kwargs
    
    def get_fields(self):
        """
        Override DRF's get_fields() to convert user-defined relational fields
        and strip database validators.
        
        This is DRF's intended extension point for field modification. It's called
        lazily via @cached_property on `fields`, ensuring all parent mixins
        (like rest_flex_fields) have completed their initialization.
        
        Returns:
            OrderedDict of field_name -> field_instance
        """
        # Let all parent mixins complete their work first
        fields = super().get_fields()
        
        # Convert user-defined relational fields to bulk-safe versions
        self._convert_to_bulk_fields(fields)
        
        # Strip database-hitting validators (uniqueness checked in operations layer)
        self._strip_database_validators(fields)
        
        return fields
    
    def _convert_to_bulk_fields(self, fields):
        """
        Convert user-defined relational fields to bulk-safe equivalents.
        
        This handles fields explicitly defined in the serializer class body.
        Auto-generated fields (from Meta.model) are already bulk-safe via 
        build_relational_field override.
        
        Third-party packages that create nested serializers (drf-flex-fields,
        drf-writable-nested) are automatically handled - their fields are
        not converted.
        
        Args:
            fields: OrderedDict of fields from get_fields()
        """
        from rest_framework.relations import PrimaryKeyRelatedField as DRFPrimaryKeyRelatedField
        from rest_framework.relations import SlugRelatedField as DRFSlugRelatedField
        
        for field_name in list(fields.keys()):
            field = fields[field_name]
            
            # Skip if already bulk-safe
            if isinstance(field, (BulkPrimaryKeyRelatedField, BulkSlugRelatedField)):
                continue
            
            # Skip read-only fields (no DB writes)
            if getattr(field, 'read_only', False):
                continue
            
            # Skip nested serializers (drf-flex-fields, drf-writable-nested, etc.)
            if isinstance(field, serializers.Serializer):
                continue
            
            # Extension point: allow subclasses to control conversion
            if not self._should_convert_field(field_name, field):
                continue
            
            # Only convert exact DRF classes, not custom subclasses from other packages
            # This prevents converting fields that other mixins have customized
            if type(field) is DRFPrimaryKeyRelatedField:
                fields[field_name] = BulkPrimaryKeyRelatedField(
                    queryset=field.queryset,
                    required=field.required,
                    allow_null=field.allow_null,
                    **self._extract_field_kwargs(field)
                )
            
            elif type(field) is DRFSlugRelatedField:
                fields[field_name] = BulkSlugRelatedField(
                    slug_field=field.slug_field,
                    queryset=field.queryset,
                    required=field.required,
                    allow_null=field.allow_null,
                    **self._extract_field_kwargs(field)
                )
    
    def _should_convert_field(self, field_name, field):
        """
        Determine if a field should be converted to its bulk-safe equivalent.
        
        Override in subclasses for custom field handling.
        
        Args:
            field_name: Name of the field
            field: The field instance
            
        Returns:
            bool: True if field should be converted
        """
        return True
    
    def _strip_database_validators(self, fields):
        """
        Remove database-hitting validators from fields.
        
        Uniqueness validation is deferred to the operations layer where
        it can be done efficiently in bulk with batched queries.
        
        NOTE: Serializer-level validators are handled in get_validators() override,
        NOT here. Accessing self.validators during get_fields() causes infinite
        recursion because DRF's validators property depends on fields.
        
        Args:
            fields: OrderedDict of fields from get_fields()
        """
        # Remove from field-level validators only
        for field_name, field in fields.items():
            if not self._should_strip_field_validators(field_name, field):
                continue
            
            if hasattr(field, 'validators'):
                field.validators = [
                    v for v in field.validators
                    if not self._is_database_validator(v)
                ]
    
    def get_validators(self):
        """
        Override to strip database validators at the serializer level.
        
        This is called after fields are cached, so it's safe to filter
        validators here without causing recursion.
        
        Returns:
            List of validators with database-hitting validators removed
        """
        validators = super().get_validators()
        return [v for v in validators if not self._is_database_validator(v)]
    
    def _is_database_validator(self, validator):
        """
        Check if a validator hits the database.
        
        Override to add custom validator types.
        
        Args:
            validator: The validator instance
            
        Returns:
            bool: True if validator queries the database
        """
        from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
        return isinstance(validator, (UniqueTogetherValidator, UniqueValidator))
    
    def _should_strip_field_validators(self, field_name, field):
        """
        Determine if validators should be stripped from a field.
        
        Override in subclasses for custom handling.
        
        Args:
            field_name: Name of the field
            field: The field instance
            
        Returns:
            bool: True if validators should be stripped
        """
        return True
    
    def _extract_field_kwargs(self, field):
        """
        Extract common field kwargs for field conversion.
        
        This method copies attributes from an existing field to create a new bulk-safe
        field with the same configuration. It handles the DRF requirement that source
        should only be specified when it differs from the field name.
        
        Args:
            field: Original bound field instance
            
        Returns:
            Dict of kwargs safe to pass to new field constructor
        """
        kwargs = {}
        
        # Common attributes to copy
        attrs_to_copy = [
            'source', 'label', 'help_text', 'initial',
            'style', 'error_messages', 'validators',
            'allow_empty', 'allow_blank'
        ]
        
        for attr in attrs_to_copy:
            if hasattr(field, attr):
                value = getattr(field, attr)
                # Only include non-default values
                if value is not None and value != '':
                    # DRF validates that source != field_name (considers it redundant)
                    # Only include source if it differs from the field's bound name
                    if attr == 'source' and hasattr(field, 'field_name'):
                        if value == field.field_name:
                            continue
                    kwargs[attr] = value
        
        return kwargs

    @classmethod
    def get_list_serializer_class(cls):
        """
        Return the ListSerializer class to use when many=True.
        
        Override in subclasses to use a custom ListSerializer.
        
        Returns:
            ListSerializer class
        """
        return BulkListSerializer
    
    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        DRF hook called when instantiated with many=True.
        Returns BulkListSerializer instead of default ListSerializer.

        Args:
            *args: Positional arguments (instance for reading)
            **kwargs: Keyword arguments (data for writing)

        Returns:
            BulkListSerializer instance
        """
        # Allow overriding via kwarg or class method
        list_serializer_class = kwargs.pop("list_serializer_class", None)
        if list_serializer_class is None:
            list_serializer_class = cls.get_list_serializer_class()

        # Extract data and instance - these belong to the ListSerializer, not the child
        # The child is just a template for validating individual items
        data = kwargs.pop("data", None)
        instance = args[0] if args else kwargs.pop("instance", None)

        # Create child serializer WITHOUT data/instance
        # The child is a template; it doesn't process the actual data
        child_serializer = cls(**kwargs)

        # Build list serializer kwargs
        list_kwargs = {
            "child": child_serializer,
        }

        # Pass data/instance to the ListSerializer
        if data is not None:
            list_kwargs["data"] = data
        if instance is not None:
            list_kwargs["instance"] = instance

        # Copy context (required for operations)
        if "context" in kwargs:
            list_kwargs["context"] = kwargs["context"]

        # Copy other relevant kwargs
        for key in ["allow_empty", "max_length", "min_length"]:
            if key in kwargs:
                list_kwargs[key] = kwargs[key]

        return list_serializer_class(**list_kwargs)

    def create(self, validated_data):
        """
        Create a single instance.
        Standard DRF behavior.

        Args:
            validated_data: Validated data dict

        Returns:
            Created instance
        """
        # Extract M2M data
        validated_data, m2m_data = self._extract_m2m_fields(validated_data)

        # Create instance
        instance = super().create(validated_data)

        # Set M2M fields
        if m2m_data and bulk_settings.enable_m2m_handling:
            for field_name, value in m2m_data.items():
                setattr(instance, field_name, value)

        return instance

    def update(self, instance, validated_data):
        """
        Update a single instance.
        Standard DRF behavior.

        Args:
            instance: Instance to update
            validated_data: Validated data dict

        Returns:
            Updated instance
        """
        # Extract M2M data
        validated_data, m2m_data = self._extract_m2m_fields(validated_data)

        # Update instance
        instance = super().update(instance, validated_data)

        # Set M2M fields
        if m2m_data and bulk_settings.enable_m2m_handling:
            for field_name, value in m2m_data.items():
                getattr(instance, field_name).set(value)

        return instance
