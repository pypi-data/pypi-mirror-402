"""Tests for models."""

from py_mercury_switch_api.models import (
    MODELS,
    SG105E,
    AutodetectedMercuryModel,
    SG108Pro,
)


class TestModels:
    """Test model classes."""

    def test_base_model_defaults(self):
        """Test base model defaults."""
        model = AutodetectedMercuryModel()
        assert model.MODEL_NAME == ""
        assert model.PORTS == 0

    def test_sg108pro_attributes(self):
        """Test SG108Pro attributes."""
        model = SG108Pro()
        assert model.MODEL_NAME == "SG108Pro"
        assert model.PORTS == 8
        assert len(model.CHECKS_AND_RESULTS) > 0

    def test_all_models_registered(self):
        """Test that all models are registered."""
        assert SG108Pro in MODELS
        assert SG105E in MODELS

    def test_model_templates_defined(self):
        """Test that model templates are defined."""
        model = SG108Pro()
        assert len(model.SYSTEM_INFO_TEMPLATES) > 0
        assert len(model.PORT_STATISTICS_TEMPLATES) > 0
        assert len(model.VLAN_8021Q_TEMPLATES) > 0
