import pandas as pd
import numpy as np
from datetime import datetime

# Set random seed for reproducibility
np.random.seed(42)

# Sample localities in Pune
localities = ['Wakad', 'Hinjewadi', 'Aundh', 'Baner', 'Kothrud', 'Viman Nagar', 'Kharadi', 'Hinjewadi Phase 1', 
              'Hinjewadi Phase 2', 'Wakad', 'Balewadi', 'Pimple Saudagar', 'Rahatani', 'Wagholi', 'Hinjewadi Phase 3']

# Property types
property_types = ['Apartment', 'Villa', 'Plot', 'Penthouse', 'Studio']

# Generate sample data
data = []
for year in range(2018, 2024):
    for _ in range(100):
        locality = np.random.choice(localities)
        property_type = np.random.choice(property_types)
        
        # Base price based on locality and property type
        base_price = np.random.randint(3000, 10000)  # Price per sq.ft
        
        # Adjust price based on property type
        if property_type == 'Villa':
            base_price *= 1.5
        elif property_type == 'Penthouse':
            base_price *= 1.8
        elif property_type == 'Plot':
            base_price *= 0.7
        
        # Adjust price based on year (appreciation)
        year_factor = 1 + (year - 2018) * 0.1  # 10% appreciation per year
        price = round(base_price * year_factor, 2)
        
        # Generate size
        if property_type in ['Apartment', 'Villa', 'Penthouse']:
            size = np.random.randint(500, 3000)  # sq.ft
        else:  # Plot
            size = np.random.randint(1000, 5000)  # sq.ft
        
        # Calculate total price
        total_price = round(price * size / 100000, 2)  # in lakhs
        
        # Generate demand (0-100)
        demand = np.random.randint(30, 100)
        
        # Add some seasonality
        month = np.random.randint(1, 13)
        if month in [4, 5, 6, 10, 11, 12]:  # Higher demand in these months
            demand = min(100, demand + 10)
        
        data.append({
            'year': year,
            'month': month,
            'locality': locality,
            'property_type': property_type,
            'price_per_sqft': price,
            'size_sqft': size,
            'total_price_lakhs': total_price,
            'demand_score': demand,
            'bedrooms': np.random.randint(1, 5) if property_type != 'Plot' else 0,
            'bathrooms': np.random.randint(1, 4) if property_type != 'Plot' else 0,
            'furnishing': np.random.choice(['Furnished', 'Semi-Furnished', 'Unfurnished']),
            'transaction_type': np.random.choice(['New Booking', 'Resale'], p=[0.7, 0.3]),
            'possession_status': np.random.choice(['Ready to Move', 'Under Construction', 'New Launch']),
            'builder': np.random.choice(['Lodha', 'Godrej', 'Prestige', 'Kolte-Patil', 'VTP', 'Vilas Javdekar', 'Local Builder'])
        })

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
output_file = 'real_estate_data.xlsx'
df.to_excel(output_file, index=False)
print(f"Sample data generated and saved to {output_file}")
print(f"Total records: {len(df)}")
print("\nSample data:")
print(df.head())
