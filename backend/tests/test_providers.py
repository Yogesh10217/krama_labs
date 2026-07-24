import pytest
from unittest.mock import MagicMock
from app.extraction.providers.factory import ProviderFactory, FallbackProvider
from app.extraction.providers.base import ExtractionRequest, ExtractionResponse, ExtractedFieldData
from app.extraction.schemas import DocumentSchema
import uuid

@pytest.fixture
def dummy_request():
    return ExtractionRequest(
        organization_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_type="invoice",
        schema=DocumentSchema(schema_name="test", schema_version="1.0", fields=[]),
        ocr_pages=[],
        ocr_regions=[]
    )

def test_fallback_provider_success(dummy_request):
    mock1 = MagicMock()
    mock1.provider_name.return_value = "mock1"
    # mock1 fails
    mock1.extract.side_effect = ValueError("Failed")

    mock2 = MagicMock()
    mock2.provider_name.return_value = "mock2"
    # mock2 succeeds
    success_resp = ExtractionResponse(
        provider="mock2",
        model="test",
        provider_version="1.0",
        schema_version="1.0",
        fields=[ExtractedFieldData(name="total", raw_value="100", normalized_value="100", data_type="STRING", confidence=0.9, evidence=[])],
        confidence=0.9
    )
    mock2.extract.return_value = success_resp

    fallback = FallbackProvider([mock1, mock2])
    
    result = fallback.extract(dummy_request)
    assert result.provider == "mock2"
    assert mock1.extract.called
    assert mock2.extract.called

def test_fallback_provider_all_fail(dummy_request):
    mock1 = MagicMock()
    mock1.provider_name.return_value = "mock1"
    mock1.extract.side_effect = ValueError("Failed")
    
    fallback = FallbackProvider([mock1])
    
    with pytest.raises(RuntimeError, match="All fallback providers failed"):
        fallback.extract(dummy_request)

def test_factory_get_returns_provider():
    provider = ProviderFactory.get()
    assert provider is not None
    # Depending on config, it will be a Provider or FallbackProvider
