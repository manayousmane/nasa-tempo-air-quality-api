#!/usr/bin/env python3
"""
Collect sample real data from APIs to test the system.
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.air_quality_service import air_quality_service


# Test locations
TEST_LOCATIONS = [
    {"name": "New York", "lat": 40.7589, "lon": -73.9851},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
]


async def collect_current_data():
    """Collect current air quality data for test locations."""
    print("📊 Collecting Current Air Quality Data")
    print("=" * 40)
    
    results = []
    
    for location in TEST_LOCATIONS:
        print(f"\n🌍 Collecting data for {location['name']}...")
        
        try:
            # Get current air quality
            air_quality = await air_quality_service.get_current_air_quality(
                latitude=location["lat"],
                longitude=location["lon"]
            )
            
            if air_quality:
                result = {
                    "location": location,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True,
                    "data": {
                        "current_measurement": air_quality.current_measurement.dict() if air_quality.current_measurement else None,
                        "weather": air_quality.weather.dict() if air_quality.weather else None,
                        "predictions_count": len(air_quality.predictions) if air_quality.predictions else 0,
                        "alerts_count": len(air_quality.active_alerts) if air_quality.active_alerts else 0
                    }
                }
                
                print(f"   ✅ Data collected successfully")
                if air_quality.current_measurement:
                    measurement = air_quality.current_measurement
                    print(f"   📈 AQI: {getattr(measurement, 'aqi', 'N/A')}")
                    print(f"   🌡️  PM2.5: {getattr(measurement, 'pm25', 'N/A')} μg/m³")
                    print(f"   💨 NO2: {getattr(measurement, 'no2', 'N/A')} ppb")
                
            else:
                result = {
                    "location": location,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False,
                    "error": "No data returned"
                }
                print(f"   ❌ No data returned")
            
            results.append(result)
            
        except Exception as e:
            result = {
                "location": location,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
            results.append(result)
            print(f"   ❌ Error: {e}")
    
    return results


async def collect_forecast_data():
    """Collect forecast data for test locations."""
    print("\n\n🔮 Collecting Forecast Data")
    print("=" * 40)
    
    results = []
    
    for location in TEST_LOCATIONS:
        print(f"\n🌍 Collecting forecast for {location['name']}...")
        
        try:
            # Get 24-hour forecast
            forecast = await air_quality_service.get_air_quality_forecast(
                latitude=location["lat"],
                longitude=location["lon"],
                hours=24
            )
            
            if forecast:
                result = {
                    "location": location,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True,
                    "data": {
                        "forecast_hours": len(forecast.forecast_data) if forecast.forecast_data else 0,
                        "weather_forecast_hours": len(forecast.weather_forecast) if forecast.weather_forecast else 0,
                        "confidence_metrics": forecast.confidence_metrics if hasattr(forecast, 'confidence_metrics') else {}
                    }
                }
                
                print(f"   ✅ Forecast collected successfully")
                print(f"   📅 Forecast points: {len(forecast.forecast_data) if forecast.forecast_data else 0}")
                
            else:
                result = {
                    "location": location,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False,
                    "error": "No forecast data returned"
                }
                print(f"   ❌ No forecast data returned")
            
            results.append(result)
            
        except Exception as e:
            result = {
                "location": location,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
            results.append(result)
            print(f"   ❌ Error: {e}")
    
    return results


async def collect_historical_data():
    """Collect historical data for test locations."""
    print("\n\n📈 Collecting Historical Data")
    print("=" * 40)
    
    results = []
    
    # Get last 7 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    for location in TEST_LOCATIONS:
        print(f"\n🌍 Collecting historical data for {location['name']}...")
        
        try:
            # Get historical data
            historical = await air_quality_service.get_historical_air_quality(
                latitude=location["lat"],
                longitude=location["lon"],
                start_date=start_date,
                end_date=end_date,
                limit=100
            )
            
            if historical:
                result = {
                    "location": location,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True,
                    "data": {
                        "measurements_count": len(historical.measurements) if historical.measurements else 0,
                        "weather_data_count": len(historical.weather_data) if historical.weather_data else 0,
                        "date_range": {
                            "start": start_date.isoformat(),
                            "end": end_date.isoformat()
                        }
                    }
                }
                
                print(f"   ✅ Historical data collected")
                print(f"   📊 Measurements: {len(historical.measurements) if historical.measurements else 0}")
                
            else:
                result = {
                    "location": location,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False,
                    "error": "No historical data returned"
                }
                print(f"   ❌ No historical data returned")
            
            results.append(result)
            
        except Exception as e:
            result = {
                "location": location,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
            results.append(result)
            print(f"   ❌ Error: {e}")
    
    return results


async def test_data_source_comparison():
    """Test data source comparison functionality."""
    print("\n\n🔄 Testing Data Source Comparison")
    print("=" * 40)
    
    location = TEST_LOCATIONS[0]  # Test with New York
    print(f"\n🌍 Comparing data sources for {location['name']}...")
    
    try:
        comparison = await air_quality_service.compare_data_sources(
            latitude=location["lat"],
            longitude=location["lon"],
            pollutant="pm25",
            hours=24
        )
        
        if comparison:
            print("✅ Data source comparison successful")
            if "statistics" in comparison:
                stats = comparison["statistics"]
                print(f"   📊 Sources available: {stats.get('sources_available', 0)}")
                print(f"   🎯 Agreement score: {stats.get('agreement_score', 0):.2f}")
                print(f"   👍 Recommended source: {stats.get('recommended_source', 'N/A')}")
            
            return {
                "location": location,
                "success": True,
                "comparison": comparison
            }
        else:
            print("❌ No comparison data returned")
            return {
                "location": location,
                "success": False,
                "error": "No comparison data"
            }
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "location": location,
            "success": False,
            "error": str(e)
        }


def save_results(all_results):
    """Save collection results to file."""
    print("\n💾 Saving Results")
    print("=" * 20)
    
    try:
        results_file = "data_collection_results.json"
        
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"✅ Results saved to {results_file}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")


async def main():
    """Run data collection tests."""
    print("🧪 NASA TEMPO Data Collection Test")
    print("=" * 50)
    
    all_results = {
        "test_timestamp": datetime.utcnow().isoformat(),
        "test_locations": TEST_LOCATIONS
    }
    
    # Collect current data
    current_results = await collect_current_data()
    all_results["current_data"] = current_results
    
    # Collect forecast data
    forecast_results = await collect_forecast_data()
    all_results["forecast_data"] = forecast_results
    
    # Collect historical data
    historical_results = await collect_historical_data()
    all_results["historical_data"] = historical_results
    
    # Test comparison
    comparison_result = await test_data_source_comparison()
    all_results["comparison_test"] = comparison_result
    
    # Summary
    print("\n\n📊 COLLECTION SUMMARY")
    print("=" * 50)
    
    current_success = sum(1 for r in current_results if r.get("success"))
    forecast_success = sum(1 for r in forecast_results if r.get("success"))
    historical_success = sum(1 for r in historical_results if r.get("success"))
    comparison_success = 1 if comparison_result.get("success") else 0
    
    print(f"Current Data:     {current_success}/{len(TEST_LOCATIONS)} successful")
    print(f"Forecast Data:    {forecast_success}/{len(TEST_LOCATIONS)} successful") 
    print(f"Historical Data:  {historical_success}/{len(TEST_LOCATIONS)} successful")
    print(f"Comparison Test:  {comparison_success}/1 successful")
    
    total_success = current_success + forecast_success + historical_success + comparison_success
    total_tests = len(TEST_LOCATIONS) * 3 + 1
    
    print(f"\nOverall Success:  {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
    
    # Save results
    save_results(all_results)
    
    if total_success == total_tests:
        print("\n🎉 All data collection tests passed!")
    elif total_success >= total_tests * 0.7:
        print("\n⚠️  Most tests passed. Check failed operations.")
    else:
        print("\n❌ Multiple test failures. Check configuration and connections.")
    
    return total_success == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)