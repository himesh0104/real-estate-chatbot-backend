from django.db import models


class RealEstateData(models.Model):
    """Model representing the denormalized dataset provided by the user."""

    final_location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    year = models.IntegerField()
    loc_lat = models.FloatField(null=True, blank=True)
    loc_lng = models.FloatField(null=True, blank=True)

    total_sales = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    total_sold = models.IntegerField(null=True, blank=True)
    flat_sold = models.IntegerField(null=True, blank=True)
    office_sold = models.IntegerField(null=True, blank=True)
    others_sold = models.IntegerField(null=True, blank=True)
    shop_sold = models.IntegerField(null=True, blank=True)
    commercial_sold = models.IntegerField(null=True, blank=True)
    other_sold = models.IntegerField(null=True, blank=True)
    residential_sold = models.IntegerField(null=True, blank=True)

    flat_weighted_avg_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    office_weighted_avg_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    others_weighted_avg_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    shop_weighted_avg_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    flat_prevailing_rate_range = models.CharField(max_length=100, blank=True)
    office_prevailing_rate_range = models.CharField(max_length=100, blank=True)
    others_prevailing_rate_range = models.CharField(max_length=100, blank=True)
    shop_prevailing_rate_range = models.CharField(max_length=100, blank=True)

    total_units = models.IntegerField(null=True, blank=True)
    total_carpet_area = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    flat_total = models.IntegerField(null=True, blank=True)
    shop_total = models.IntegerField(null=True, blank=True)
    office_total = models.IntegerField(null=True, blank=True)
    others_total = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['final_location', 'year']
        unique_together = ('final_location', 'year', 'city')

    def __str__(self):
        return f"{self.final_location} ({self.city}) - {self.year}"


# We'll use this model to store analysis queries and results if needed in the future
class AnalysisQuery(models.Model):
    """
    Model to store analysis queries and their results.
    """
    query_text = models.TextField(help_text="The natural language query from the user")
    locality = models.CharField(max_length=100, blank=True, null=True, help_text="Extracted locality from the query")
    year_range = models.CharField(max_length=50, blank=True, null=True, help_text="Year range from the query")
    property_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of property if specified")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Analysis results
    summary = models.TextField(blank=True, null=True, help_text="Generated analysis summary")
    chart_data = models.JSONField(blank=True, null=True, help_text="Chart data in JSON format")
    
    class Meta:
        verbose_name_plural = "Analysis Queries"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.query_text[:50]}..."


# Note: We're using pandas to read directly from Excel for this project,
# but in a production environment, you might want to import the data into these models
class PropertyListing(models.Model):
    """
    Model representing a property listing.
    This is provided as a reference and can be used to store data from Excel.
    """
    year = models.IntegerField(help_text="Year of the listing")
    month = models.IntegerField(help_text="Month of the listing")
    locality = models.CharField(max_length=100, help_text="Locality of the property")
    property_type = models.CharField(max_length=50, help_text="Type of property")
    price_per_sqft = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per square foot")
    size_sqft = models.IntegerField(help_text="Size in square feet")
    total_price_lakhs = models.DecimalField(max_digits=15, decimal_places=2, help_text="Total price in lakhs")
    demand_score = models.IntegerField(help_text="Demand score (0-100)")
    bedrooms = models.IntegerField(blank=True, null=True, help_text="Number of bedrooms")
    bathrooms = models.IntegerField(blank=True, null=True, help_text="Number of bathrooms")
    furnishing = models.CharField(max_length=20, blank=True, null=True, help_text="Furnishing status")
    transaction_type = models.CharField(max_length=20, blank=True, null=True, help_text="Type of transaction")
    possession_status = models.CharField(max_length=50, blank=True, null=True, help_text="Possession status")
    builder = models.CharField(max_length=100, blank=True, null=True, help_text="Name of the builder")
    
    class Meta:
        ordering = ['-year', '-month', 'locality']
        verbose_name_plural = "Property Listings"
    
    def __str__(self):
        return f"{self.locality} - {self.property_type} - {self.year}"  

# This model would be used if we want to cache analysis results
class CachedAnalysis(models.Model):
    """
    Model to cache analysis results for common queries.
    """
    query_hash = models.CharField(max_length=64, unique=True, help_text="SHA-256 hash of the query parameters")
    query_params = models.JSONField(help_text="Query parameters in JSON format")
    result = models.JSONField(help_text="Cached analysis result")
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.PositiveIntegerField(default=0, help_text="Number of times this cache has been accessed")
    
    class Meta:
        verbose_name_plural = "Cached Analyses"
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"Cache for {self.query_hash} ({self.access_count} accesses)"
