import csv
import io
import logging

from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None

from .serializers.real_estate import (
    AnalysisQuerySerializer,
    AnalysisResultSerializer,
    ExportDataSerializer,
)
from .utils.data_processor import RealEstateDataProcessor

logger = logging.getLogger(__name__)

class RealEstateAnalysisView(APIView):
    """
    API endpoint for real estate analysis.
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.processor = RealEstateDataProcessor()
            self.ai_client = self._init_openai_client()
        except Exception as e:
            logger.error(f"Error initializing RealEstateDataProcessor: {str(e)}")
            raise
    
    def get(self, request, format=None):
        ""
        # Handle GET requests with query parameters.
        # Example: /api/analyze?query=analyze%20Wakad&locality=Wakad
        ""
        serializer = AnalysisQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid query parameters", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return self.process_analysis(serializer.validated_data)
    
    def post(self, request, format=None):
        ""
        #Handle POST requests with JSON data.
        ""
        serializer = AnalysisQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return self.process_analysis(serializer.validated_data)
    
    def process_analysis(self, data):
        ""
        #Process the analysis request and return the response.
        ""
        try:
            query = data.get('query', '')
            filters = {
                'locality': data.get('locality') or '',
                'year_range': data.get('year_range', ''),
                'property_type': data.get('property_type', ''),
                'year_from': data.get('year_from'),
                'year_to': data.get('year_to'),
            }

            result = self.processor.process_query(query, filters)
            result['filters'] = filters
            result['metadata'] = {
                'rows': len(result.get('table_data', [])),
                'generated_at': settings.TIME_ZONE,
            }

            ai_summary = self._maybe_generate_ai_summary(query, result)
            if ai_summary:
                result['summary'] = ai_summary
                result['metadata']['ai_summary'] = True
            else:
                result['metadata']['ai_summary'] = False

            response_serializer = AnalysisResultSerializer(data=result)
            if not response_serializer.is_valid():
                logger.warning(f"Response validation failed: {response_serializer.errors}")
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing analysis: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _init_openai_client(self):
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key or OpenAI is None:
            return None
        try:
            return OpenAI(api_key=api_key)
        except Exception as exc:  # pragma: no cover - network
            logger.warning("Unable to initialize OpenAI client: %s", exc)
            return None

    def _maybe_generate_ai_summary(self, query, result):
        if not self.ai_client or not query:
            return None

        prompt = (
            "You are an expert real-estate analyst. Summarize the following dataset insightfully:\n"
            f"User query: {query}\n"
            f"Baseline summary: {result.get('summary')}\n"
            f"Key stats: {result.get('metadata', {})}\n"
            f"Table sample: {result.get('table_data', [])[:3]}"
        )

        try:
            completion = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Provide concise, action-oriented market insights."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=250,
            )
            return completion.choices[0].message.content.strip()
        except Exception as exc:  # pragma: no cover - network
            logger.warning("OpenAI summary failed: %s", exc)
            return None


class AvailableLocalitiesView(APIView):
    """
    API endpoint to get the list of available localities.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, format=None):
        ""
        #Return a list of unique localities in the dataset.
        ""
        try:
            processor = RealEstateDataProcessor()
            localities = sorted(processor.df['final_location'].unique().tolist())
            return Response({"localities": localities}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting localities: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to retrieve localities"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SampleQueriesView(APIView):
    """
    API endpoint to get sample queries.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, format=None):
        ""
        #Return a list of sample queries.
        ""
        sample_queries = [
            {
                "query": "Analyze real estate trends in Wakad",
                "description": "Get an overview of the real estate market in Wakad"
            },
            {
                "query": "Show price trends for the last 3 years",
                "description": "View price trends over the past 3 years"
            },
            {
                "query": "Compare demand between Wakad and Hinjewadi",
                "description": "Compare demand metrics between two localities"
            },
            {
                "query": "Show apartment prices in Baner",
                "description": "Filter by property type (Apartment) and locality (Baner)"
            },
            {
                "query": "Analyze price growth from 2020 to 2023",
                "description": "View price changes over a specific time period"
            }
        ]
        
        return Response({"sample_queries": sample_queries}, status=status.HTTP_200_OK)


class DataExportView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = ExportDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        processor = RealEstateDataProcessor()
        filters = {
            'locality': request.data.get('locality', ''),
            'year_range': request.data.get('year_range', ''),
            'property_type': request.data.get('property_type', ''),
            'year_from': request.data.get('year_from'),
            'year_to': request.data.get('year_to'),
        }
        filtered_df = processor.filter_data(filters)

        if filtered_df.empty:
            return Response(
                {'detail': 'No data available for the specified filters.'},
                status=status.HTTP_404_NOT_FOUND
            )

        export_format = serializer.validated_data['format']
        if export_format == 'excel':
            buffer = io.BytesIO()
            filtered_df.to_excel(buffer, index=False)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'real_estate_export.xlsx'
        else:
            buffer = io.StringIO()
            filtered_df.to_csv(buffer, index=False)
            content_type = 'text/csv'
            filename = 'real_estate_export.csv'

        response = HttpResponse(buffer.getvalue(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
