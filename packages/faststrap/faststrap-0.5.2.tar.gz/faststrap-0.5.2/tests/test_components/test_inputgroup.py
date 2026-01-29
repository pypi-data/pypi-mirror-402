"""Tests for InputGroup and FloatingLabel."""

from fasthtml.common import to_xml

from faststrap.components.forms.input import Input
from faststrap.components.forms.inputgroup import FloatingLabel, InputGroup, InputGroupText


class TestInputGroup:
    """Tests for InputGroup."""

    def test_basic(self):
        """Renders container and children."""
        ig = InputGroup(InputGroupText("@"), Input("user"))
        html = to_xml(ig)
        assert "input-group" in html
        assert "input-group-text" in html
        assert "@" in html
        assert "<input" in html

    def test_size_nowrap(self):
        """Size and nowrap options."""
        ig = InputGroup(size="lg", nowrap=True)
        html = to_xml(ig)
        assert "input-group-lg" in html
        assert "flex-nowrap" in html


class TestFloatingLabel:
    """Tests for FloatingLabel."""

    def test_basic(self):
        """Renders input and label in wrapper."""
        fl = FloatingLabel("email", label="Email Address")
        html = to_xml(fl)

        # Check structure: wrapper > input + label
        assert "form-floating" in html
        assert "<input" in html
        assert "<label" in html

        # Check attributes
        assert 'placeholder="Email Address"' in html  # Required for float effect
        assert "Email Address" in html  # Label text

    def test_types_and_defaults(self):
        """Attributes passed correctly."""
        fl = FloatingLabel(
            "pwd", label="Pass", input_type="password", value="secret", required=True
        )
        html = to_xml(fl)

        assert 'type="password"' in html
        assert 'value="secret"' in html
        assert "required" in html

    def test_readonly_disabled(self):
        """States."""
        fl = FloatingLabel("x", label="x", readonly=True, disabled=True)
        html = to_xml(fl)
        assert "readonly" in html
        assert "disabled" in html
