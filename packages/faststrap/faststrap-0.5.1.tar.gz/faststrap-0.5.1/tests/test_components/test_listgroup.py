"""Tests for ListGroup and Collapse components."""

from fasthtml.common import Div, to_xml

from faststrap.components.display import Badge
from faststrap.components.navigation.listgroup import Collapse, ListGroup, ListGroupItem


class TestListGroup:
    """Tests for ListGroup component."""

    def test_basic_render(self):
        """Renders ul with list-group class."""
        lg = ListGroup(ListGroupItem("Item 1"))
        html = to_xml(lg)
        assert "<ul" in html
        assert "list-group" in html
        assert "list-group-item" in html
        assert "Item 1" in html

    def test_flush(self):
        """Flush variant."""
        lg = ListGroup(flush=True)
        assert "list-group-flush" in to_xml(lg)

    def test_numbered(self):
        """Numbered variant renders as div (or ol) per implementation."""
        # Implementation uses Div for numbered to allow CSS counters or similar, verify structure
        lg = ListGroup(numbered=True)
        html = to_xml(lg)
        assert "list-group-numbered" in html
        # Implementation decided to return Div for numbered to handle complex content better potentially
        assert "<div" in html

    def test_horizontal(self):
        """Horizontal variants."""
        lg = ListGroup(horizontal=True)
        assert "list-group-horizontal" in to_xml(lg)

        lg_md = ListGroup(horizontal="md")
        assert "list-group-horizontal-md" in to_xml(lg_md)


class TestListGroupItem:
    """Tests for ListGroupItem."""

    def test_variants(self):
        """Color variants."""
        item = ListGroupItem("Test", variant="primary")
        assert "list-group-item-primary" in to_xml(item)

    def test_active_disabled(self):
        """Active and disabled states."""
        active = ListGroupItem("A", active=True)
        html_a = to_xml(active)
        assert "active" in html_a
        assert 'aria-current="true"' in html_a

        disabled = ListGroupItem("D", disabled=True)
        html_d = to_xml(disabled)
        assert "disabled" in html_d
        assert 'aria-disabled="true"' in html_d

    def test_action_link(self):
        """Links and action items."""
        # Explicit action
        btn = ListGroupItem("Button", action=True)
        html_b = to_xml(btn)
        assert "list-group-item-action" in html_b

        # Link implies action
        link = ListGroupItem("Link", href="#")
        html_l = to_xml(link)
        assert "<a" in html_l
        assert "list-group-item-action" in html_l
        assert 'href="#"' in html_l

    def test_badge(self):
        """Badge integration."""
        item = ListGroupItem("Content", badge=Badge("5"))
        html = to_xml(item)
        assert "d-flex" in html
        assert "justify-content-between" in html
        assert "badge" in html
        assert "5" in html


class TestCollapse:
    """Tests for Collapse component."""

    def test_basic_render(self):
        """Core collapse structure."""
        c = Collapse(Div("Content"), collapse_id="my-collapse")
        html = to_xml(c)
        assert 'id="my-collapse"' in html
        assert "collapse" in html
        assert "Content" in html

    def test_show_horizontal(self):
        """Show and horizontal props."""
        c = Collapse("C", collapse_id="id", show=True, horizontal=True)
        html = to_xml(c)
        assert "show" in html
        assert "collapse-horizontal" in html
