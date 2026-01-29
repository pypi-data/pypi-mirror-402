"""Tests for Checkbox, Radio, Switch, and Range components."""

from fasthtml.common import to_xml

from faststrap.components.forms.checks import Checkbox, Radio, Range, Switch


class TestCheckbox:
    """Tests for Checkbox."""

    def test_basic(self):
        """Basic rendering."""
        cb = Checkbox("foo", label="Bar")
        html = to_xml(cb)
        assert 'type="checkbox"' in html
        assert 'name="foo"' in html
        assert "Bar" in html
        assert "form-check" in html
        assert "form-check-input" in html
        assert "form-check-label" in html

    def test_states(self):
        """Checked, disabled, required."""
        cb = Checkbox("c", checked=True, disabled=True, required=True)
        html = to_xml(cb)
        assert "checked" in html
        assert "disabled" in html
        assert "required" in html

    def test_inline_reverse(self):
        """Inline and reverse variants."""
        cb = Checkbox("c", inline=True, reverse=True)
        html = to_xml(cb)
        assert "form-check-inline" in html
        assert "form-check-reverse" in html

    def test_help_text(self):
        """Help text rendering."""
        cb = Checkbox("c", help_text="Helper")
        assert "form-text" in to_xml(cb)
        assert "Helper" in to_xml(cb)

    def test_switch(self):
        """Switch variant."""
        sw = Switch("s", label="Toggle")
        html = to_xml(sw)
        assert "form-switch" in html
        assert 'role="switch"' in html
        assert 'type="checkbox"' in html


class TestRadio:
    """Tests for Radio."""

    def test_basic(self):
        """Basic rendering."""
        r = Radio("grp", label="Opt 1", value="1")
        html = to_xml(r)
        assert 'type="radio"' in html
        assert 'name="grp"' in html
        assert 'value="1"' in html
        assert "Opt 1" in html

    def test_checked(self):
        """Checked state."""
        r = Radio("grp", checked=True)
        assert "checked" in to_xml(r)


class TestRange:
    """Tests for Range."""

    def test_basic(self):
        """Basic rendering."""
        rng = Range("vol", label="Volume")
        html = to_xml(rng)
        assert 'type="range"' in html
        assert "form-range" in html
        assert "form-label" in html
        assert "Volume" in html

    def test_min_max_step(self):
        """Min, max, step attributes."""
        rng = Range("r", min_val=5, max_val=50, step=5, value=25)
        html = to_xml(rng)
        assert 'min="5"' in html
        assert 'max="50"' in html
        assert 'step="5"' in html
        assert 'value="25"' in html
