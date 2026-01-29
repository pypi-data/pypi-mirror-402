"""
Bulk-safe relational field classes.

These fields defer database validation to the operations layer,
enabling efficient bulk operations without N+1 queries.
"""

from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField


class BulkPrimaryKeyRelatedField(PrimaryKeyRelatedField):
    """
    A PrimaryKeyRelatedField that defers database validation to the operations layer.
    
    This field accepts raw primary key values (integers) without performing database
    lookups during validation. FK existence is validated in bulk using batched queries
    in the operations layer.
    
    This is the recommended field type for foreign key relationships in bulk operations.
    
    Usage:
        class ArticleSerializer(BulkModelSerializer):
            category = BulkPrimaryKeyRelatedField(queryset=Category.objects.all())
            # queryset is kept for introspection but not used during validation
    
    Note: The queryset parameter is still required for DRF compatibility and is used
    to determine the related model, but it won't be queried during validation.
    """
    
    def to_internal_value(self, data):
        """
        Accept and validate the raw PK value without database lookup.
        
        Performs only basic type validation (null checks, type coercion).
        Database existence checking is handled by the operations layer.
        
        Args:
            data: The primary key value (typically an integer)
            
        Returns:
            The raw PK value (not the model instance)
            
        Raises:
            ValidationError: If data is null and field doesn't allow null
        """
        if data is None:
            if not self.allow_null:
                self.fail('required')
            return None
        
        # Basic type validation - ensure it's the right type for a PK
        try:
            # Most PKs are integers, but support UUID and other types
            pk_type = self.queryset.model._meta.pk.get_internal_type() if self.queryset else 'AutoField'
            
            # For common integer PK types, validate it's numeric
            if pk_type in ('AutoField', 'BigAutoField', 'SmallAutoField', 'IntegerField', 'BigIntegerField'):
                return int(data)
            else:
                # For UUIDs, strings, etc., just return as-is
                return data
        except (ValueError, TypeError):
            self.fail('incorrect_type', data_type=type(data).__name__)
        
        return data


class BulkSlugRelatedField(SlugRelatedField):
    """
    A SlugRelatedField that defers database validation to the operations layer.
    
    This field accepts raw slug values without performing database lookups during
    validation. Slug existence is validated in bulk using batched queries in the
    operations layer.
    
    Usage:
        class ArticleSerializer(BulkModelSerializer):
            category = BulkSlugRelatedField(
                slug_field='slug',
                queryset=Category.objects.all()
            )
    
    Note: The queryset parameter is still required for DRF compatibility and is used
    to determine the related model and slug field, but it won't be queried during validation.
    """
    
    def to_internal_value(self, data):
        """
        Accept and validate the raw slug value without database lookup.
        
        Performs only basic type validation (null/blank checks, string coercion).
        Database existence checking is handled by the operations layer.
        
        Args:
            data: The slug value (typically a string)
            
        Returns:
            The raw slug value (not the model instance)
            
        Raises:
            ValidationError: If data is null/blank and field doesn't allow it
        """
        if data is None:
            if not self.allow_null:
                self.fail('required')
            return None
        
        # Coerce to string
        data = str(data)
        
        if data == '':
            if not self.allow_blank:
                self.fail('blank')
            return ''
        
        # Return the raw slug value - operations layer will resolve it
        return data


# Note: BulkHyperlinkedRelatedField is not provided because hyperlinked fields
# are rarely used in bulk operations. Use BulkPrimaryKeyRelatedField instead.

