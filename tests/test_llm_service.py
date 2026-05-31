import pytest
import json
from app.llm_service import get_diagnosis_from_image, get_diagnosis_from_description

@pytest.mark.asyncio
async def test_get_diagnosis_from_image(mocker):
    # We will mock the internal _call_llm to avoid setting up OpenAI API mocks
    mock_call_llm = mocker.patch("app.llm_service._call_llm", new_callable=mocker.AsyncMock)
    mock_call_llm.return_value = {
        "disease_name_en": "Alternaria Alternata",
        "description_en": "A fungal disease."
    }
    
    result = await get_diagnosis_from_image("Alternaria Alternata", 0.95)
    
    assert result["disease_name_en"] == "Alternaria Alternata"
    assert mock_call_llm.called
    
    # Test low confidence scenario
    await get_diagnosis_from_image("Alternaria Alternata", 0.45)
    call_args = mock_call_llm.call_args[0][0]
    assert "below 60%" in call_args

@pytest.mark.asyncio
async def test_get_diagnosis_from_description(mocker):
    mock_call_llm = mocker.patch("app.llm_service._call_llm", new_callable=mocker.AsyncMock)
    mock_call_llm.return_value = {
        "disease_name_en": "Cercospora Nicotianae",
    }
    
    result = await get_diagnosis_from_description("Spots on leaves like frog eyes", "en")
    
    assert result["disease_name_en"] == "Cercospora Nicotianae"
    assert mock_call_llm.called
    call_args = mock_call_llm.call_args[0][0]
    assert "Respond only in English" in call_args
