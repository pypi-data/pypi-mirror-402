"""
Query building and optimization for bulk operations.

Provides utilities for:
- Building efficient OR queries with Q objects
- Single-query fetches for bulk lookups
- Automatic select_related/prefetch_related optimization
"""

from django.db.models import Q


class BulkQueryBuilder:
    """
    Builds optimized queries for bulk operations.
    """

    def __init__(self, model, unique_fields):
        """
        Initialize with model and unique field configuration.

        Args:
            model: Django model class
            unique_fields: Fields used for object matching
        """
        self.model = model
        self.unique_fields = unique_fields if isinstance(unique_fields, (list, tuple)) else [unique_fields]

    def build_lookup_filter(self, lookup_values):
        """
        Build Q objects for complex lookups.

        Args:
            lookup_values: List of dicts with unique field values

        Returns:
            Q object for filtering

        Example:
            unique_fields = ['sku', 'warehouse']
            lookup_values = [
                {'sku': 'A', 'warehouse': 1},
                {'sku': 'B', 'warehouse': 2}
            ]
            Returns: Q(sku='A', warehouse=1) | Q(sku='B', warehouse=2)
        """
        if not lookup_values:
            return Q(pk__in=[])  # Empty queryset

        # Optimize for single field lookups
        if len(self.unique_fields) == 1:
            field = self.unique_fields[0]
            values = [item.get(field) for item in lookup_values if field in item]
            return self.build_in_filter(field, values)

        # Multi-field lookups require OR conditions
        return self.build_or_conditions(lookup_values)

    def build_or_conditions(self, lookup_values):
        """
        Build OR conditions for multiple objects.

        Args:
            lookup_values: List of dicts with unique field values

        Returns:
            Q object with OR conditions
        """
        q_objects = []

        for item in lookup_values:
            # Build AND condition for this item's unique fields
            q_kwargs = {}
            for field in self.unique_fields:
                if field in item:
                    q_kwargs[field] = item[field]

            if q_kwargs:
                q_objects.append(Q(**q_kwargs))

        if not q_objects:
            return Q(pk__in=[])  # Empty queryset

        # Combine with OR
        combined_q = q_objects[0]
        for q in q_objects[1:]:
            combined_q |= q

        return combined_q

    def build_in_filter(self, field, values):
        """
        Build __in filter for single field.

        Args:
            field: Field name
            values: List of values

        Returns:
            Q object with __in filter
        """
        if not values:
            return Q(pk__in=[])  # Empty queryset

        return Q(**{f"{field}__in": values})

    def fetch_by_unique_fields(self, queryset, validated_data):
        """
        Single query to fetch all matching objects.

        Args:
            queryset: Base queryset to filter
            validated_data: List of data dicts with unique field values

        Returns:
            Dict mapping unique_key → instance
        """
        # Build lookup filter
        q_filter = self.build_lookup_filter(validated_data)

        # Execute single query
        instances = queryset.filter(q_filter)

        # Build lookup dict
        lookup = {}
        for instance in instances:
            key = self._get_instance_key(instance)
            lookup[key] = instance

        return lookup

    def _get_instance_key(self, instance):
        """
        Get unique key tuple for an instance.

        Args:
            instance: Model instance

        Returns:
            Tuple of unique field values
        """
        return tuple(getattr(instance, field) for field in self.unique_fields)

    def _get_data_key(self, data):
        """
        Get unique key tuple from data dict.

        Args:
            data: Dictionary of field values

        Returns:
            Tuple of unique field values
        """
        return tuple(data.get(field) for field in self.unique_fields)

    def optimize_queryset(self, queryset, serializer_class):
        """
        Apply select_related/prefetch_related based on serializer.

        Args:
            queryset: Queryset to optimize
            serializer_class: Serializer class to analyze

        Returns:
            Optimized queryset
        """
        optimizer = QueryOptimizer(serializer_class)
        return optimizer.apply_optimizations(queryset)


class QueryOptimizer:
    """
    Analyzes serializers to automatically optimize queries for serialization.
    Auto-detects ForeignKey and ManyToMany relationships from serializer fields.
    
    Uses class-level caching to avoid re-analyzing the same serializer class.
    """
    
    # Class-level cache: serializer_class -> (select_related, prefetch_related, only_fields)
    _analysis_cache = {}

    def __init__(self, serializer_class, context=None):
        """
        Initialize with serializer to analyze.

        Args:
            serializer_class: DRF serializer class to analyze for relationships
            context: The serializer context, which may be needed for some fields.
        """
        self.serializer_class = serializer_class
        self.context = context or {}
        self.model = getattr(getattr(serializer_class, 'Meta', None), 'model', None)
        self._select_related = []
        self._prefetch_related = []
        self._only_fields = []
        self._analyzed = False

    def analyze(self):
        """
        Analyze serializer fields to determine optimizations.
        Uses cached results if available for this serializer class.
        """
        if self._analyzed:
            return

        if not self.serializer_class:
            self._analyzed = True
            return

        # Check cache first
        cache_key = self.serializer_class
        if cache_key in self._analysis_cache:
            cached_select, cached_prefetch, cached_only = self._analysis_cache[cache_key]
            self._select_related = list(cached_select)  # Copy to avoid mutation
            self._prefetch_related = list(cached_prefetch)
            self._only_fields = list(cached_only)
            self._analyzed = True
            return

        # Analyze declared serializer fields
        self._analyze_declared_fields()
        
        # Analyze model fields if available
        self._analyze_model_fields()
        
        # Detect fields to fetch with .only()
        self._detect_only_fields()

        # Cache the results
        self._analysis_cache[cache_key] = (
            list(self._select_related),
            list(self._prefetch_related),
            list(self._only_fields)
        )

        self._analyzed = True

    def _analyze_declared_fields(self):
        """
        Analyze declared serializer fields for optimization opportunities.
        """
        from rest_framework import serializers
        
        # Get declared fields
        if not hasattr(self.serializer_class, '_declared_fields'):
            return
            
        for field_name, field in self.serializer_class._declared_fields.items():
            if self._is_select_related_field(field):
                if field_name not in self._select_related:
                    self._select_related.append(field_name)
            elif self._is_prefetch_related_field(field):
                if field_name not in self._prefetch_related:
                    self._prefetch_related.append(field_name)

    def _analyze_model_fields(self):
        """
        Analyze model fields to detect relationships.
        Only includes fields that are in the serializer's fields list.
        Supports both explicit field lists and fields = '__all__'.
        """
        if not self.model:
            return
            
        # Get serializer's field list
        meta = getattr(self.serializer_class, 'Meta', None)
        if not meta:
            return
            
        serializer_fields = getattr(meta, 'fields', None)
        if not serializer_fields:
            return
        
        # Support fields = '__all__' by analyzing all model fields
        if serializer_fields == '__all__':
            # Get all field names from the model
            serializer_fields = [f.name for f in self.model._meta.get_fields()]
        
        from django.db import models
        
        # Check each model field
        for field in self.model._meta.get_fields():
            # Only include if field is in serializer's fields
            if field.name not in serializer_fields:
                continue
                
            # ForeignKey → select_related
            if isinstance(field, models.ForeignKey):
                if field.name not in self._select_related:
                    self._select_related.append(field.name)
            
            # ManyToMany → prefetch_related
            elif isinstance(field, models.ManyToManyField):
                if field.name not in self._prefetch_related:
                    self._prefetch_related.append(field.name)

    def _detect_only_fields(self):
        """
        Detect which model fields should be fetched with .only() to reduce data transfer.
        Includes all fields explicitly listed in the serializer's Meta.fields.
        Also includes FK _id fields for any select_related fields to prevent extra queries.
        """
        if not self.model:
            return
            
        # Get serializer's field list
        meta = getattr(self.serializer_class, 'Meta', None)
        if not meta:
            return
            
        serializer_fields = getattr(meta, 'fields', None)
        if not serializer_fields:
            return
        
        # If fields = '__all__', don't use .only() (fetch everything)
        if serializer_fields == '__all__':
            return
        
        # Build list of fields to fetch
        model_field_names = {f.name for f in self.model._meta.get_fields() if f.concrete}
        
        for field_name in serializer_fields:
            # Only include actual model fields (not method fields, SerializerMethodFields, etc.)
            if field_name in model_field_names:
                self._only_fields.append(field_name)
        
        # Always include pk even if not explicitly listed
        if 'pk' not in self._only_fields and 'id' not in self._only_fields:
            self._only_fields.append('pk')
        
        # Include FK _id fields for any select_related to prevent Django from making extra queries
        from django.db import models
        for select_field in self._select_related:
            try:
                field = self.model._meta.get_field(select_field)
                if isinstance(field, models.ForeignKey):
                    # Add the database column name (field_name_id)
                    fk_id_field = f"{select_field}_id"
                    if fk_id_field not in self._only_fields:
                        self._only_fields.append(fk_id_field)
            except Exception:
                # Field might not exist, skip
                pass

    def _is_select_related_field(self, field):
        """
        Determine if a serializer field should use select_related.

        Args:
            field: DRF serializer field instance

        Returns:
            bool: True if field should use select_related
        """
        from rest_framework import serializers
        
        # PrimaryKeyRelatedField (single) - ForeignKey
        if isinstance(field, serializers.PrimaryKeyRelatedField):
            return not getattr(field, 'many', False)
        
        # SlugRelatedField (single) - ForeignKey with slug
        if isinstance(field, serializers.SlugRelatedField):
            return not getattr(field, 'many', False)
        
        # StringRelatedField (single) - ForeignKey with __str__
        if isinstance(field, serializers.StringRelatedField):
            return not getattr(field, 'many', False)
        
        # Nested serializer (single) - ForeignKey
        if isinstance(field, serializers.Serializer):
            return not isinstance(field, serializers.ListSerializer)
        
        return False

    def _is_prefetch_related_field(self, field):
        """
        Determine if a serializer field should use prefetch_related.

        Args:
            field: DRF serializer field instance

        Returns:
            bool: True if field should use prefetch_related
        """
        from rest_framework import serializers
        
        # PrimaryKeyRelatedField (many) - ManyToMany or reverse FK
        if isinstance(field, serializers.PrimaryKeyRelatedField):
            return getattr(field, 'many', False)
        
        # SlugRelatedField (many) - ManyToMany with slug
        if isinstance(field, serializers.SlugRelatedField):
            return getattr(field, 'many', False)
        
        # StringRelatedField (many) - ManyToMany with __str__
        if isinstance(field, serializers.StringRelatedField):
            return getattr(field, 'many', False)
        
        # Nested serializer (many) - ManyToMany or reverse FK
        if isinstance(field, serializers.ListSerializer):
            return True
        
        return False

    def get_select_related_fields(self):
        """
        Extract ForeignKey fields that should use select_related.
        Auto-detects from serializer field declarations and model relationships.

        Returns:
            list: Field names for select_related optimization

        Example:
            # For ProductSerializer with fields: ['name', 'category', 'supplier']
            # Returns: ['category', 'supplier'] (if they're ForeignKey fields)
        """
        if not self._analyzed:
            self.analyze()
        return self._select_related

    def get_prefetch_related_fields(self):
        """
        Extract M2M/reverse FK fields for prefetch_related.
        Auto-detects from serializer field declarations and model relationships.

        Returns:
            list: Field names or Prefetch objects for prefetch_related optimization

        Example:
            # For ProductSerializer with fields: ['name', 'tags', 'reviews']
            # Returns: ['tags', 'reviews'] (if they're M2M or reverse FK fields)
        """
        if not self._analyzed:
            self.analyze()
        return self._prefetch_related

    def get_only_fields(self):
        """
        Extract fields for .only() optimization.
        Returns only the fields that should be fetched from the database.

        Returns:
            list: Field names for .only() optimization
        """
        if not self._analyzed:
            self.analyze()
        return self._only_fields

    def apply_optimizations(self, queryset):
        """
        Apply all optimizations to queryset.

        Args:
            queryset: Queryset to optimize

        Returns:
            Optimized queryset
        """
        if not self._analyzed:
            self.analyze()

        # Apply .only() to limit columns fetched from database
        if self._only_fields:
            queryset = queryset.only(*self._only_fields)

        # Apply select_related
        if self._select_related:
            queryset = queryset.select_related(*self._select_related)

        # Apply prefetch_related
        if self._prefetch_related:
            queryset = queryset.prefetch_related(*self._prefetch_related)

        return queryset


def build_filter_for_delete(model, unique_fields, data_list):
    """
    Build filter for bulk delete operation.

    Args:
        model: Django model class
        unique_fields: List of unique field names
        data_list: List of dicts with unique field values

    Returns:
        Q object for filtering records to delete
    """
    builder = BulkQueryBuilder(model, unique_fields)
    return builder.build_lookup_filter(data_list)


def fetch_existing_objects(model, unique_fields, validated_data):
    """
    Fetch existing objects matching validated_data.

    Args:
        model: Django model class
        unique_fields: List of unique field names
        validated_data: List of data dicts

    Returns:
        Dict mapping unique_key → instance
    """
    builder = BulkQueryBuilder(model, unique_fields)
    queryset = model.objects.all()
    return builder.fetch_by_unique_fields(queryset, validated_data)
