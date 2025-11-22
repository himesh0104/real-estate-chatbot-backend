from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
import re


class RealEstateDataSerializer(serializers.Serializer):
    """Serializer for the real estate data model."""

    final_location = serializers.CharField(required=True)
    year = serializers.IntegerField(required=True)
    city = serializers.CharField(required=True)
    loc_lat = serializers.FloatField(required=False, allow_null=True)
    loc_lng = serializers.FloatField(required=False, allow_null=True)
    total_sales = serializers.FloatField(required=False, allow_null=True)
    total_sold = serializers.FloatField(required=False, allow_null=True)
    flat_sold = serializers.FloatField(required=False, allow_null=True)
    office_sold = serializers.FloatField(required=False, allow_null=True)
    others_sold = serializers.FloatField(required=False, allow_null=True)
    shop_sold = serializers.FloatField(required=False, allow_null=True)
    commercial_sold = serializers.FloatField(required=False, allow_null=True)
    other_sold = serializers.FloatField(required=False, allow_null=True)
    residential_sold = serializers.FloatField(required=False, allow_null=True)
    flat_weighted_avg_rate = serializers.FloatField(required=False, allow_null=True)
    office_weighted_avg_rate = serializers.FloatField(required=False, allow_null=True)
    others_weighted_avg_rate = serializers.FloatField(required=False, allow_null=True)
    shop_weighted_avg_rate = serializers.FloatField(required=False, allow_null=True)
    flat_prevailing_rate_range = serializers.CharField(required=False, allow_blank=True)
    office_prevailing_rate_range = serializers.CharField(required=False, allow_blank=True)
    others_prevailing_rate_range = serializers.CharField(required=False, allow_blank=True)
    shop_prevailing_rate_range = serializers.CharField(required=False, allow_blank=True)
    total_units = serializers.FloatField(required=False, allow_null=True)
    total_carpet_area = serializers.FloatField(required=False, allow_null=True)
    flat_total = serializers.FloatField(required=False, allow_null=True)
    shop_total = serializers.FloatField(required=False, allow_null=True)
    office_total = serializers.FloatField(required=False, allow_null=True)
    others_total = serializers.FloatField(required=False, allow_null=True)


class AnalysisQuerySerializer(serializers.Serializer):
    """Serializer for handling analysis query parameters."""

    query = serializers.CharField(required=True)

    locality = serializers.CharField(required=False, allow_blank=True)

    year_from = serializers.IntegerField(
        required=False,
        allow_null=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    year_to = serializers.IntegerField(
        required=False,
        allow_null=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )

    property_type = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=[
            ('flat', 'Flat'),
            ('office', 'Office'),
            ('shop', 'Shop'),
            ('others', 'Others'),
            ('commercial', 'Commercial'),
            ('residential', 'Residential'),
        ]
    )

    def validate(self, data):
        """Extra validation and NLP extraction."""

        # Validate year ordering
        if data.get('year_from') and data.get('year_to'):
            if data['year_from'] > data['year_to']:
                raise serializers.ValidationError("'year_from' cannot be after 'year_to'")

        # Extract years from query
        if not data.get('year_from') or not data.get('year_to'):
            year_matches = re.findall(r'(\d{4})', data['query'])
            if len(year_matches) >= 2:
                years = sorted([int(y) for y in year_matches])
                data['year_from'] = years[0]
                data['year_to'] = years[-1]

        # Extract locality from query
        if not data.get('locality'):
            q = data['query'].lower()
            mapping = {
                "wakad": "Wakad",
                "aundh": "Aundh",
                "baner": "Baner",
                "hinjewadi": "Hinjewadi"
            }
            for key, value in mapping.items():
                if key in q:
                    data['locality'] = value
                    break

        return data


class AnalysisResultSerializer(serializers.Serializer):
    """Serializer for the analysis response."""

    query = serializers.CharField()
    summary = serializers.CharField()
    chart_data = serializers.DictField()
    table_data = serializers.ListField(child=serializers.DictField())
    filters = serializers.DictField()
    metadata = serializers.DictField()


class ExportDataSerializer(serializers.Serializer):
    """Serializer for exporting filtered analysis data."""

    format = serializers.ChoiceField(choices=[('csv', 'CSV'), ('excel', 'Excel')], default='csv')
    include_charts = serializers.BooleanField(default=True)
    include_raw_data = serializers.BooleanField(default=True)
