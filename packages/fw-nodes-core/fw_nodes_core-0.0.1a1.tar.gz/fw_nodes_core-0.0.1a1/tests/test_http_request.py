"""Tests for HTTP Request node."""

from fw_nodes_core.nodes.http_request import HTTPRequestNode


def test_http_method_field_has_default_value():
    """Test that the HTTP method field has a default value of GET in the schema.

    This ensures that:
    1. The schema exposes a default value for the method field
    2. The default value is GET
    3. The frontend will pre-select GET in the dropdown (no "Select..." placeholder)
    """
    # Get the input schema
    input_schema = HTTPRequestNode.get_input_schema()
    schema_dict = input_schema.model_json_schema()

    # Check that 'method' field exists in properties
    assert 'method' in schema_dict['properties'], "method field should be in schema properties"

    # Get the method field schema
    method_field = schema_dict['properties']['method']

    # Check that default value exists and is GET
    assert 'default' in method_field, "method field should have a default value in schema"
    assert method_field['default'] == 'GET', \
        f"method field default should be GET, got {method_field.get('default')}"

    # Resolve the enum values (may be in $ref or allOf)
    enum_values = []
    ref_path = None

    if '$ref' in method_field:
        # Direct $ref at field level
        ref_path = method_field['$ref']
    elif 'allOf' in method_field and '$ref' in method_field['allOf'][0]:
        # $ref wrapped in allOf
        ref_path = method_field['allOf'][0]['$ref']
    elif 'enum' in method_field:
        enum_values = method_field['enum']

    if ref_path:
        ref_name = ref_path.split('/')[-1]  # e.g., 'HTTPMethod' from '#/$defs/HTTPMethod'
        if '$defs' in schema_dict and ref_name in schema_dict['$defs']:
            enum_values = schema_dict['$defs'][ref_name].get('enum', [])

    # Verify that GET is a valid enum value
    assert 'GET' in enum_values, f"GET should be in enum values, got {enum_values}"


def test_http_method_field_not_in_required():
    """Test that method field is not in required fields (since it has a default)."""
    input_schema = HTTPRequestNode.get_input_schema()
    schema_dict = input_schema.model_json_schema()

    # A field with a default value should not be in the required list
    required_fields = schema_dict.get('required', [])
    assert 'method' not in required_fields, \
        "method field should not be required since it has a default value"
