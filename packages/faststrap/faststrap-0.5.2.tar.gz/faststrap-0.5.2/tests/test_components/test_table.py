"""Tests for Table component."""

from fasthtml.common import to_xml

from faststrap.components.display import Table, TBody, TCell, THead, TRow


class TestTableBasic:
    """Basic Table functionality tests."""

    def test_table_renders_correctly(self):
        """Table renders with correct HTML structure."""
        table = Table(
            THead(TRow(TCell("Name", header=True), TCell("Age", header=True))),
            TBody(TRow(TCell("Alice"), TCell("25"))),
        )
        html = to_xml(table)

        assert "<table" in html
        assert "table" in html
        assert "Name" in html
        assert "Alice" in html

    def test_table_default_class(self):
        """Table has .table class by default."""
        table = Table()
        html = to_xml(table)
        assert 'class="table"' in html


class TestTableVariants:
    """Test Table style variants."""

    def test_striped(self):
        """Striped variant adds correct class."""
        table = Table(striped=True)
        html = to_xml(table)
        assert "table-striped" in html

    def test_striped_columns(self):
        """Striped columns variant adds correct class."""
        table = Table(striped_columns=True)
        html = to_xml(table)
        assert "table-striped-columns" in html

    def test_bordered(self):
        """Bordered variant adds correct class."""
        table = Table(bordered=True)
        html = to_xml(table)
        assert "table-bordered" in html

    def test_borderless(self):
        """Borderless variant adds correct class."""
        table = Table(borderless=True)
        html = to_xml(table)
        assert "table-borderless" in html

    def test_hover(self):
        """Hover variant adds correct class."""
        table = Table(hover=True)
        html = to_xml(table)
        assert "table-hover" in html

    def test_small(self):
        """Small size adds correct class."""
        table = Table(small=True)
        html = to_xml(table)
        assert "table-sm" in html

    def test_color_variant(self):
        """Color variant adds correct class."""
        table = Table(variant="dark")
        html = to_xml(table)
        assert "table-dark" in html

    def test_multiple_variants(self):
        """Multiple variants can be combined."""
        table = Table(striped=True, hover=True, bordered=True, variant="primary")
        html = to_xml(table)
        assert "table-striped" in html
        assert "table-hover" in html
        assert "table-bordered" in html
        assert "table-primary" in html


class TestTableResponsive:
    """Test responsive table wrapper."""

    def test_responsive_true(self):
        """responsive=True wraps in .table-responsive."""
        table = Table(responsive=True)
        html = to_xml(table)
        assert "table-responsive" in html
        assert "<div" in html

    def test_responsive_breakpoint(self):
        """Responsive breakpoint adds correct class."""
        table = Table(responsive="lg")
        html = to_xml(table)
        assert "table-responsive-lg" in html

    def test_non_responsive_no_wrapper(self):
        """Non-responsive table has no wrapper div."""
        table = Table()
        html = to_xml(table)
        # Should start with table, not div
        assert html.strip().startswith("<table")


class TestTHead:
    """Test THead component."""

    def test_thead_renders(self):
        """THead renders correctly."""
        thead = THead(TRow(TCell("Header", header=True)))
        html = to_xml(thead)
        assert "<thead" in html
        assert "Header" in html

    def test_thead_variant(self):
        """THead variant adds correct class."""
        thead = THead(variant="dark")
        html = to_xml(thead)
        assert "table-dark" in html


class TestTBody:
    """Test TBody component."""

    def test_tbody_renders(self):
        """TBody renders correctly."""
        tbody = TBody(TRow(TCell("Data")))
        html = to_xml(tbody)
        assert "<tbody" in html
        assert "Data" in html

    def test_tbody_divider(self):
        """TBody divider adds correct class."""
        tbody = TBody(divider=True)
        html = to_xml(tbody)
        assert "table-group-divider" in html

    def test_tbody_variant(self):
        """TBody variant adds correct class."""
        tbody = TBody(variant="light")
        html = to_xml(tbody)
        assert "table-light" in html


class TestTRow:
    """Test TRow component."""

    def test_trow_renders(self):
        """TRow renders correctly."""
        row = TRow(TCell("Cell 1"), TCell("Cell 2"))
        html = to_xml(row)
        assert "<tr" in html
        assert "Cell 1" in html
        assert "Cell 2" in html

    def test_trow_variant(self):
        """TRow variant adds correct class."""
        row = TRow(variant="success")
        html = to_xml(row)
        assert "table-success" in html

    def test_trow_active(self):
        """TRow active adds correct class."""
        row = TRow(active=True)
        html = to_xml(row)
        assert "table-active" in html


class TestTCell:
    """Test TCell component."""

    def test_tcell_td_default(self):
        """TCell renders as td by default."""
        cell = TCell("Data")
        html = to_xml(cell)
        assert "<td" in html
        assert "Data" in html

    def test_tcell_th_header(self):
        """TCell renders as th when header=True."""
        cell = TCell("Header", header=True)
        html = to_xml(cell)
        assert "<th" in html
        assert "Header" in html

    def test_tcell_variant(self):
        """TCell variant adds correct class."""
        cell = TCell("Data", variant="warning")
        html = to_xml(cell)
        assert "table-warning" in html

    def test_tcell_active(self):
        """TCell active adds correct class."""
        cell = TCell("Data", active=True)
        html = to_xml(cell)
        assert "table-active" in html

    def test_tcell_colspan(self):
        """TCell colspan attribute."""
        cell = TCell("Wide", colspan=2)
        html = to_xml(cell)
        assert 'colspan="2"' in html

    def test_tcell_rowspan(self):
        """TCell rowspan attribute."""
        cell = TCell("Tall", rowspan=3)
        html = to_xml(cell)
        assert 'rowspan="3"' in html

    def test_tcell_scope(self):
        """TCell scope attribute for headers."""
        cell = TCell("Header", header=True, scope="col")
        html = to_xml(cell)
        assert 'scope="col"' in html


class TestTableHTMX:
    """Test HTMX integration."""

    def test_table_htmx_attrs(self):
        """Table supports HTMX attributes."""
        table = Table(hx_get="/api/data", hx_target="#content")
        html = to_xml(table)
        assert 'hx-get="/api/data"' in html
        assert 'hx-target="#content"' in html

    def test_trow_htmx_attrs(self):
        """TRow supports HTMX attributes."""
        row = TRow(hx_get="/api/row/1", hx_swap="outerHTML")
        html = to_xml(row)
        assert 'hx-get="/api/row/1"' in html


class TestTableCustomization:
    """Test customization options."""

    def test_table_custom_classes(self):
        """Table merges custom classes."""
        table = Table(cls="my-custom-table shadow")
        html = to_xml(table)
        assert "table" in html
        assert "my-custom-table" in html
        assert "shadow" in html

    def test_table_custom_id(self):
        """Table accepts custom id."""
        table = Table(id="users-table")
        html = to_xml(table)
        assert 'id="users-table"' in html

    def test_table_data_attributes(self):
        """Table supports data attributes."""
        table = Table(data_page="1", data_total="100")
        html = to_xml(table)
        assert 'data-page="1"' in html
        assert 'data-total="100"' in html
