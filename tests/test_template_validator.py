from validators.template_validator import TemplateValidator


def test_template_catalog_is_valid():
    errors = TemplateValidator(prompts_dir="sdd/prompts_manager").validate()
    assert errors == []

