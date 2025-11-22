from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Main analysis endpoint (supports both GET and POST)
    path('analyze/', views.RealEstateAnalysisView.as_view(), name='analyze'),
    
    # Additional endpoints for frontend
    path('localities/', views.AvailableLocalitiesView.as_view(), name='localities'),
    path('sample-queries/', views.SampleQueriesView.as_view(), name='sample-queries'),
    path('export/', views.DataExportView.as_view(), name='export-data'),
]
