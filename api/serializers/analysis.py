from rest_framework import serializers

class AnalysisQuerySerializer(serializers.Serializer):
    """
    Serializer for handling analysis queries.
    """
    query = serializers.CharField(
        required=True,
        help_text="Natural language query for real estate analysis"
    )
    
    # Optional filters that can be used to refine the analysis
    locality = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by specific locality (e.g., 'Wakad', 'Aundr')"
    )
    
    year_range = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by year range (e.g., '2019-2023' or 'last 3 years')"
    )
    
    property_type = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by property type (e.g., 'Apartment', 'Villa')"
    )
    
    def validate(self, data):
        """
        Validate the query data.
        """
        # You can add custom validation logic here if needed
        return data


class AnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer for the analysis response.
    """
    query = serializers.CharField(help_text="The original query")
    summary = serializers.CharField(help_text="Generated analysis summary")
    chart_data = serializers.DictField(
        help_text="Data for rendering charts",
        child=serializers.ListField(
            child=serializers.FloatField(),
            allow_empty=True
        )
    )
    table_data = serializers.ListField(
        child=serializers.DictField(),
        help_text="Tabular data for display"
    )
    filters = serializers.DictField(
        help_text="Filters applied to the query"
    )
    
    def to_representation(self, instance):
        """
        Convert the instance to a dictionary.
        """
        return {
            'query': instance.get('query', ''),
            'summary': instance.get('summary', ''),
            'chart_data': instance.get('chart_data', {}),
            'table_data': instance.get('table_data', []),
            'filters': instance.get('filters', {})
        }
