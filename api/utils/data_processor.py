import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
from django.apps import apps
from django.conf import settings

class RealEstateDataProcessor:
    """Utility class for processing real estate data from Excel/Sheets."""

    COLUMN_MAP = {
        'final location': 'final_location',
        'year': 'year',
        'city': 'city',
        'loc_lat': 'loc_lat',
        'loc_lng': 'loc_lng',
        'total_sales - igr': 'total_sales',
        'total sold - igr': 'total_sold',
        'flat_sold - igr': 'flat_sold',
        'office_sold - igr': 'office_sold',
        'others_sold - igr': 'others_sold',
        'shop_sold - igr': 'shop_sold',
        'commercial_sold - igr': 'commercial_sold',
        'other_sold - igr': 'other_sold',
        'residential_sold - igr': 'residential_sold',
        'flat - weighted average rate': 'flat_weighted_avg_rate',
        'office - weighted average rate': 'office_weighted_avg_rate',
        'others - weighted average rate': 'others_weighted_avg_rate',
        'shop - weighted average rate': 'shop_weighted_avg_rate',
        'flat - most prevailing rate - range': 'flat_prevailing_rate_range',
        'office - most prevailing rate - range': 'office_prevailing_rate_range',
        'others - most prevailing rate - range': 'others_prevailing_rate_range',
        'shop - most prevailing rate - range': 'shop_prevailing_rate_range',
        'total units': 'total_units',
        'total carpet area supplied (sqft)': 'total_carpet_area',
        'flat total': 'flat_total',
        'shop total': 'shop_total',
        'office total': 'office_total',
        'others total': 'others_total',
    }

    NUMERIC_COLUMNS = [
        'year', 'loc_lat', 'loc_lng', 'total_sales', 'total_sold', 'flat_sold',
        'office_sold', 'others_sold', 'shop_sold', 'commercial_sold', 'other_sold',
        'residential_sold', 'flat_weighted_avg_rate', 'office_weighted_avg_rate',
        'others_weighted_avg_rate', 'shop_weighted_avg_rate', 'total_units',
        'total_carpet_area', 'flat_total', 'shop_total', 'office_total', 'others_total'
    ]

    PROPERTY_COLUMNS = ['flat', 'office', 'shop', 'others', 'commercial', 'residential']
    DB_FIELDS = list(COLUMN_MAP.values())

    def __init__(self, excel_file_path=None, data_url=None, prefer_database=True):
        self.excel_file_path = excel_file_path or settings.EXCEL_FILE_PATH
        self.data_url = data_url or getattr(
            settings,
            'REAL_ESTATE_DATA_URL',
            'https://docs.google.com/spreadsheets/d/1BPFvRBLAFFLyQ1EDJ4ogXt8HYCUXhM80/export?format=csv&gid=240339127'
        )
        self.prefer_database = prefer_database
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load data from the Excel file or Google Sheet into a DataFrame."""
        try:
            df = None
            if self.prefer_database:
                df = self._load_from_database()

            if df is None:
                df = self._load_from_external_source()

            self.df = df

        except Exception as e:
            raise Exception(f"Error loading Excel data: {str(e)}")

    def _load_from_database(self):
        """Load data from the RealEstateData model if rows exist."""
        try:
            RealEstateData = apps.get_model('api', 'RealEstateData')
        except LookupError:
            return None

        queryset = RealEstateData.objects.all()
        if not queryset.exists():
            return None

        df = pd.DataFrame(list(queryset.values(*self.DB_FIELDS)))
        if df.empty:
            return None

        for col in self.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['year'] = df['year'].astype(int)
        df = df.dropna(subset=['final_location', 'city'])
        df = df.sort_values(['final_location', 'year']).reset_index(drop=True)
        return df

    def _load_from_external_source(self):
        """Load data from Excel file or Google Sheet URL."""
        if self.excel_file_path and os.path.exists(self.excel_file_path) and os.path.getsize(self.excel_file_path) > 0:
            if self.excel_file_path.lower().endswith('.csv'):
                df = pd.read_csv(self.excel_file_path)
            else:
                df = pd.read_excel(self.excel_file_path, engine='openpyxl')
        elif self.data_url:
            df = pd.read_csv(self.data_url)
        else:
            raise FileNotFoundError(
                "No real estate dataset found. Provide an Excel file or set REAL_ESTATE_DATA_URL."
            )

        df.columns = [col.strip().lower() for col in df.columns]
        df = df.rename(columns=self.COLUMN_MAP)

        missing_cols = [col for col in self.COLUMN_MAP.values() if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Dataset is missing required columns: {missing_cols}")

        for col in self.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].apply(self._clean_numeric_value), errors='coerce')

        df['year'] = df['year'].astype(int)
        df = df.dropna(subset=['final_location', 'city'])
        df = df.sort_values(['final_location', 'year']).reset_index(drop=True)

        return df

    @staticmethod
    def _clean_numeric_value(value):
        if isinstance(value, str):
            value = value.replace(',', '').replace('₹', '').strip()
            if value == '' or value.lower() == 'na':
                return np.nan
        return value
    
    def filter_data(self, filters=None):
        """
        Filter the dataset based on the provided filters.
        
        Args:
            filters (dict): Dictionary of filters to apply. Can include:
                - locality (str): Filter by locality name
                - year_range (str): Filter by year range (e.g., '2019-2023' or 'last 3 years')
                - property_type (str): Filter by property type
                
        Returns:
            pandas.DataFrame: Filtered DataFrame
        """
        if filters is None:
            filters = {}
            
        df_filtered = self.df.copy()
        
        # Apply locality filter
        locality = filters.get('locality')
        if locality:
            df_filtered = df_filtered[
                df_filtered['final_location'].str.lower() == locality.lower()
            ]
        
        # Apply year range filter
        year_range = filters.get('year_range')
        if year_range:
            current_year = datetime.now().year
            
            # Handle 'last N years' format
            if year_range.lower().startswith('last '):
                try:
                    years = int(year_range.split()[1])
                    min_year = current_year - years
                    df_filtered = df_filtered[df_filtered['year'] >= min_year]
                except (ValueError, IndexError):
                    pass
            # Handle 'YYYY-YYYY' format
            elif '-' in year_range:
                try:
                    start_year, end_year = map(int, year_range.split('-'))
                    df_filtered = df_filtered[
                        (df_filtered['year'] >= start_year) & 
                        (df_filtered['year'] <= end_year)
                    ]
                except (ValueError, IndexError):
                    pass
        
        # Apply property type filter
        property_type = filters.get('property_type')
        if property_type:
            column_name = f"{property_type.lower()}_sold"
            if column_name in df_filtered.columns:
                df_filtered = df_filtered[df_filtered[column_name] > 0]
        
        return df_filtered
    
    def generate_summary(self, df, query=None):
        """
        Generate a natural language summary of the data.
        
        Args:
            df (pandas.DataFrame): Filtered DataFrame to analyze
            query (str, optional): Original user query for context
            
        Returns:
            str: Generated summary text
        """
        if df.empty:
            return "No data available for the specified filters."
        
        # Basic statistics
        localities = df['final_location'].unique()
        years = sorted(df['year'].unique())

        total_sales = df['total_sales'].sum()
        avg_flat_price = df['flat_weighted_avg_rate'].mean()
        avg_office_price = df['office_weighted_avg_rate'].mean()
        avg_shop_price = df['shop_weighted_avg_rate'].mean()

        property_sums = df[[col for col in df.columns if col.endswith('_sold')]].sum()
        if not property_sums.empty:
            top_property = property_sums.idxmax().replace('_sold', '').replace('_', ' ').title()
        else:
            top_property = 'N/A'

        scope_text = (
            f"{localities[0]}" if len(localities) == 1 else f"{len(localities)} localities"
        )

        summary = (
            f"Between {min(years)} and {max(years)}, {scope_text} recorded "
            f"₹{total_sales:,.0f} in total sales with {property_sums.sum():,.0f} units sold. "
            f"Average prices per sq.ft (Flat/Office/Shop) were ₹{avg_flat_price:,.0f} / "
            f"₹{avg_office_price:,.0f} / ₹{avg_shop_price:,.0f}. "
            f"Most active segment: {top_property}."
        )

        return summary
    
    def prepare_chart_data(self, df):
        """
        Prepare data for chart visualization.
        
        Args:
            df (pandas.DataFrame): Filtered DataFrame
            
        Returns:
            dict: Chart data in a format suitable for Chart.js
        """
        if df.empty:
            return {'labels': [], 'datasets': []}

        yearly_data = df.groupby('year').agg({
            'flat_weighted_avg_rate': 'mean',
            'office_weighted_avg_rate': 'mean',
            'shop_weighted_avg_rate': 'mean',
            'total_sales': 'sum',
            'total_sold': 'sum'
        }).reset_index()

        return {
            'labels': yearly_data['year'].astype(int).tolist(),
            'datasets': [
                {
                    'label': 'Avg Flat Price (₹/sq.ft)',
                    'data': yearly_data['flat_weighted_avg_rate'].round(2).tolist(),
                    'borderColor': 'rgb(67, 97, 238)',
                    'tension': 0.2,
                    'yAxisID': 'y'
                },
                {
                    'label': 'Total Units Sold',
                    'data': yearly_data['total_sold'].round(0).tolist(),
                    'type': 'bar',
                    'backgroundColor': 'rgba(230, 57, 70, 0.4)',
                    'borderColor': 'rgba(230, 57, 70, 1)',
                    'yAxisID': 'y1'
                }
            ]
        }
    
    def prepare_table_data(self, df):
        """
        Prepare data for tabular display.
        
        Args:
            df (pandas.DataFrame): Filtered DataFrame
            
        Returns:
            list: List of dictionaries for tabular display
        """
        if df.empty:
            return []
        
        display_columns = [
            'year', 'final_location', 'city', 'total_sales', 'total_sold',
            'flat_weighted_avg_rate', 'office_weighted_avg_rate',
            'shop_weighted_avg_rate', 'others_weighted_avg_rate'
        ]

        table_df = df[display_columns].copy()
        table_df = table_df.rename(columns={
            'final_location': 'Location',
            'total_sales': 'Total Sales (₹)',
            'total_sold': 'Total Units Sold',
            'flat_weighted_avg_rate': 'Flat Avg Rate (₹/sq.ft)',
            'office_weighted_avg_rate': 'Office Avg Rate (₹/sq.ft)',
            'shop_weighted_avg_rate': 'Shop Avg Rate (₹/sq.ft)',
            'others_weighted_avg_rate': 'Others Avg Rate (₹/sq.ft)'
        })

        numeric_cols = [col for col in table_df.columns if table_df[col].dtype != 'object']
        for col in numeric_cols:
            table_df[col] = table_df[col].round(2)

        return table_df.to_dict('records')
    
    def process_query(self, query, filters=None):
        """
        Process a natural language query and return analysis results.
        
        Args:
            query (str): Natural language query
            filters (dict, optional): Additional filters
            
        Returns:
            dict: Analysis results including summary, chart data, and table data
        """
        if filters is None:
            filters = {}
        
        # Extract filters from query if not provided
        if not filters.get('locality') and query:
            localities = self.df['final_location'].unique()
            for loc in localities:
                if loc.lower() in query.lower():
                    filters['locality'] = loc
                    break
        
        # Extract year range from query if not provided
        if not filters.get('year_range') and query:
            # Look for patterns like '2019-2023' or 'last 3 years'
            year_match = re.search(r'(\d{4})\s*-\s*(\d{4})', query)
            if year_match:
                filters['year_range'] = f"{year_match.group(1)}-{year_match.group(2)}"
            else:
                last_years = re.search(r'last\s+(\d+)\s+years?', query.lower())
                if last_years:
                    filters['year_range'] = f"last {last_years.group(1)}"
        
        # Extract property type if not provided
        if not filters.get('property_type') and query:
            for prop in self.PROPERTY_COLUMNS:
                if prop in query.lower():
                    filters['property_type'] = prop
                    break
        
        # Filter data based on extracted filters
        filtered_df = self.filter_data(filters)
        
        # Generate analysis
        summary = self.generate_summary(filtered_df, query)
        chart_data = self.prepare_chart_data(filtered_df)
        table_data = self.prepare_table_data(filtered_df)
        
        return {
            'query': query,
            'summary': summary,
            'chart_data': chart_data,
            'table_data': table_data,
            'filters': filters
        }
