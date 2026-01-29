import pytest
import requests_mock
from gender_api import Client, InvalidArgumentError, ApiError
from gender_api.models import SingleNameResult

def test_get_by_first_name(client):
    endpoint = "https://gender-api.com/v2/gender/by-first-name"
    mock_response = {
        "input": {"first_name": "markus"},
        "details": {
            "credits_used": 1,
            "samples": 123,
            "country": None,
            "first_name_sanitized": "markus",
            "duration": "12ms"
        },
        "result_found": True,
        "first_name": "Markus",
        "probability": 0.99,
        "gender": "male"
    }

    with requests_mock.Mocker() as m:
        m.post(endpoint, json=mock_response)
        result = client.get_by_first_name("markus")
        
        assert isinstance(result, SingleNameResult)
        assert result.gender == "male"
        assert result.accuracy == 99
        assert result.probability == 0.99
        assert result.first_name == "Markus"

def test_get_by_first_name_with_invalid_country(client):
    with pytest.raises(InvalidArgumentError):
        client.get_by_first_name("markus", country="XX")

def test_get_by_multiple_names(client):
    endpoint = "https://gender-api.com/v2/gender/by-first-name-multiple"
    mock_response = [
        {
            "input": {"first_name": "markus", "id": "0"},
            "details": {
                "credits_used": 1,
                "samples": 100,
                "duration": "10ms",
                "country": None,
                "first_name_sanitized": "markus"
            },
            "result_found": True,
            "first_name": "Markus",
            "probability": 0.99,
            "gender": "male"
        },
        {
            "input": {"first_name": "andrea", "id": "1"},
            "details": {
                "credits_used": 1,
                "samples": 200,
                "duration": "10ms",
                 "country": None,
                "first_name_sanitized": "andrea"
            },
            "result_found": True,
            "first_name": "Andrea",
            "probability": 0.98,
            "gender": "female"
        }
    ]

    with requests_mock.Mocker() as m:
        m.post(endpoint, json=mock_response)
        results = client.get_by_multiple_names(["markus", "andrea"])
        
        assert len(results) == 2
        assert results[0].gender == "male"
        assert results[1].gender == "female"

def test_api_error(client):
    endpoint = "https://gender-api.com/v2/gender/by-first-name"
    mock_error = {
        "status": 401,
        "type": "...",
        "title": "unauthorized",
        "detail": "Invalid API Key"
    }

    with requests_mock.Mocker() as m:
        m.post(endpoint, json=mock_error, status_code=401)
        
        with pytest.raises(ApiError) as exc:
            client.get_by_first_name("markus")
        
        assert "Invalid API Key" in str(exc.value)

def test_country_of_origin(client):
    endpoint = "https://gender-api.com/v2/country-of-origin"
    mock_response = {
        "input": {"first_name": "johanna"},
        "details": {"credits_used": 1, "samples": 100, "duration": "10ms", "country": None, "first_name_sanitized": "johanna"},
        "result_found": True,
        "first_name": "Johanna",
        "probability": 0.99,
        "gender": "female",
        "country_of_origin": [
             {"country_name": "Germany", "country": "DE", "probability": 0.5}
        ]
    }
    
    with requests_mock.Mocker() as m:
        m.post(endpoint, json=mock_response)
        result = client.get_country_of_origin("johanna")
        assert result.country_of_origin[0].country == "DE"

def test_stats(client):
    endpoint = "https://gender-api.com/v2/statistic"
    mock_response = {
        "is_limit_reached": False,
        "remaining_credits": 1000,
        "details": {"credits_used": 0, "samples": 0, "duration": "1ms", "country": None, "first_name_sanitized": ""},
        "usage_last_month": {"date": "2023-01", "credits_used": 500}
    }
    
    with requests_mock.Mocker() as m:
         m.get(endpoint, json=mock_response)
         result = client.get_stats()
         assert result.remaining_credits == 1000
 

