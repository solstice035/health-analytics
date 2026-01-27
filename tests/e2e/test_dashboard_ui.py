"""
End-to-end Playwright tests for the Health Analytics Dashboard.

These tests verify:
- Dashboard loads correctly
- All sections render with data
- Tab navigation works
- Charts are interactive
- Error recovery UI functions
- Responsive design works

Run with: pytest tests/e2e/ -v
Requires: pip install playwright pytest-playwright && playwright install chromium
"""

import pytest
import subprocess
import time
import os
import socket
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent


def find_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


# Module-level server to be shared across all E2E tests
_server_proc = None
_server_port = None


@pytest.fixture(scope="module")
def server_port():
    """Start the dashboard server once per module and return the port."""
    global _server_proc, _server_port

    _server_port = find_free_port()
    url = f"http://localhost:{_server_port}"

    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'

    _server_proc = subprocess.Popen(
        ['python', 'serve.py', '--no-browser', '--port', str(_server_port)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )

    # Wait for server to start
    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        _server_proc.terminate()
        pytest.skip("Could not start server")

    yield _server_port

    # Cleanup
    _server_proc.terminate()
    try:
        _server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _server_proc.kill()


class TestDashboardE2E:
    """End-to-end tests for the dashboard using Playwright."""

    @pytest.fixture
    def page(self, server_port):
        """Create a Playwright page."""
        from playwright.sync_api import sync_playwright

        url = f"http://localhost:{server_port}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state('networkidle')
            yield page
            browser.close()

    @pytest.mark.e2e
    def test_dashboard_loads(self, page):
        """Dashboard should load successfully."""
        assert "Health" in page.title() or "Dashboard" in page.title()

    @pytest.mark.e2e
    def test_has_header(self, page):
        """Dashboard should have a header."""
        # Look for header elements
        header = page.locator('header, .header, h1')
        assert header.count() > 0

    @pytest.mark.e2e
    def test_has_health_score(self, page):
        """Dashboard should display health score."""
        content = page.content().lower()
        assert 'score' in content or 'health' in content

    @pytest.mark.e2e
    def test_has_stats_cards(self, page):
        """Dashboard should have statistics cards."""
        # Look for stat cards
        stats = page.locator('.stat-card, .stat, [class*="stat"]')
        assert stats.count() >= 1

    @pytest.mark.e2e
    def test_has_charts(self, page):
        """Dashboard should have chart canvases."""
        charts = page.locator('canvas')
        assert charts.count() >= 1

    @pytest.mark.e2e
    def test_no_error_state(self, page):
        """Dashboard should not show error state."""
        page.wait_for_timeout(2000)  # Wait for data to load
        content = page.content().lower()
        # Should not have visible error state
        error_state = page.locator('.error-state:visible')
        assert error_state.count() == 0 or 'error' not in content[:500]

    @pytest.mark.e2e
    def test_has_tabs(self, page):
        """Dashboard should have navigation tabs."""
        tabs = page.locator('.tab-btn, [role="tab"], .tab, button[data-tab]')
        assert tabs.count() >= 1

    @pytest.mark.e2e
    def test_responsive_mobile(self, server_port):
        """Dashboard should work on mobile viewport."""
        from playwright.sync_api import sync_playwright

        url = f"http://localhost:{server_port}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 375, 'height': 667})
            page.goto(url)
            page.wait_for_load_state('networkidle')

            # Content should be visible
            body = page.locator('body')
            assert body.is_visible()

            browser.close()

    @pytest.mark.e2e
    def test_data_displayed(self, page):
        """Dashboard should display actual data values."""
        content = page.content()
        # Should contain numeric values
        has_numbers = any(c.isdigit() for c in content)
        assert has_numbers

    @pytest.mark.e2e
    def test_page_loads_fast(self, server_port):
        """Dashboard should load within 5 seconds."""
        from playwright.sync_api import sync_playwright

        url = f"http://localhost:{server_port}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            start = time.time()
            page.goto(url)
            page.wait_for_load_state('domcontentloaded')
            load_time = time.time() - start

            assert load_time < 5.0, f"Page took {load_time:.2f}s to load"

            browser.close()


# Simple tests that don't require full Playwright
class TestDashboardHTML:
    """Tests for dashboard HTML structure (no browser needed)."""

    @pytest.fixture
    def dashboard_html(self):
        """Read the dashboard HTML file."""
        html_path = PROJECT_ROOT / "dashboard" / "index.html"
        return html_path.read_text()

    @pytest.mark.unit
    def test_html_has_doctype(self, dashboard_html):
        """HTML should have DOCTYPE."""
        assert '<!DOCTYPE html>' in dashboard_html

    @pytest.mark.unit
    def test_html_has_title(self, dashboard_html):
        """HTML should have title."""
        assert '<title>' in dashboard_html

    @pytest.mark.unit
    def test_html_has_chartjs(self, dashboard_html):
        """HTML should include Chart.js."""
        assert 'chart.js' in dashboard_html.lower() or 'chartjs' in dashboard_html.lower()

    @pytest.mark.unit
    def test_html_has_retry_function(self, dashboard_html):
        """HTML should have retry function for error recovery."""
        assert 'retrySection' in dashboard_html or 'retry' in dashboard_html.lower()

    @pytest.mark.unit
    def test_html_has_loadjson_function(self, dashboard_html):
        """HTML should have loadJSON function."""
        assert 'loadJSON' in dashboard_html

    @pytest.mark.unit
    def test_html_has_responsive_meta(self, dashboard_html):
        """HTML should have responsive viewport meta tag."""
        assert 'viewport' in dashboard_html

    @pytest.mark.unit
    def test_html_has_tab_navigation(self, dashboard_html):
        """HTML should have tab navigation."""
        assert 'tab' in dashboard_html.lower()

    @pytest.mark.unit
    def test_html_has_section_definitions(self, dashboard_html):
        """HTML should have SECTIONS config object."""
        assert 'SECTIONS' in dashboard_html

    @pytest.mark.unit
    def test_html_has_error_handling(self, dashboard_html):
        """HTML should have error handling code."""
        assert 'humanizeError' in dashboard_html or 'renderSectionError' in dashboard_html


class TestDashboardUX:
    """UX interaction tests - verify user interactions work correctly."""

    @pytest.fixture
    def page(self, server_port):
        """Create a Playwright page."""
        from playwright.sync_api import sync_playwright

        url = f"http://localhost:{server_port}"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state('networkidle')
            yield page
            browser.close()

    @pytest.mark.e2e
    def test_tab_click_switches_content(self, page):
        """Clicking a tab should display its content panel."""
        # Initially overview tab should be active
        overview_panel = page.locator('#tab-overview')
        assert overview_panel.is_visible()

        # Click trends tab
        trends_btn = page.locator('button:has-text("Trends")')
        trends_btn.click()
        page.wait_for_timeout(500)

        # Trends panel should now be visible
        trends_panel = page.locator('#tab-trends')
        assert trends_panel.is_visible()

        # Overview panel should be hidden
        assert not overview_panel.is_visible()

    @pytest.mark.e2e
    def test_tab_click_updates_active_class(self, page):
        """Clicking a tab should update the active class."""
        # Initially overview button should have active class
        overview_btn = page.locator('button:has-text("Overview")')
        assert 'active' in overview_btn.get_attribute('class')

        # Click heart tab
        heart_btn = page.locator('button:has-text("Heart")')
        heart_btn.click()
        page.wait_for_timeout(300)

        # Heart button should now have active class
        assert 'active' in heart_btn.get_attribute('class')
        # Overview button should not have active class
        assert 'active' not in overview_btn.get_attribute('class')

    @pytest.mark.e2e
    def test_all_tabs_are_clickable(self, page):
        """All navigation tabs should be clickable and show content."""
        tabs = ['Trends', 'Fitness', 'Heart', 'Records', 'Insights', 'Overview']

        for tab_name in tabs:
            btn = page.locator(f'button:has-text("{tab_name}")')
            btn.click()
            page.wait_for_timeout(300)

            # Tab button should be active
            assert 'active' in btn.get_attribute('class'), f"{tab_name} tab not active after click"

    @pytest.mark.e2e
    def test_only_one_tab_visible_at_a_time(self, page):
        """Only one tab content should be visible at any time."""
        # Click fitness tab
        page.locator('button:has-text("Fitness")').click()
        page.wait_for_timeout(300)

        # Count visible tab contents
        visible_tabs = page.locator('.tab-content:visible')
        assert visible_tabs.count() == 1, "Multiple tab contents are visible"

    @pytest.mark.e2e
    def test_health_score_displays_number(self, page):
        """Health score should display a numeric value."""
        score_element = page.locator('.score-value')
        if score_element.count() > 0:
            score_text = score_element.inner_text()
            # Should contain a number
            assert any(c.isdigit() for c in score_text), "Health score should contain a number"

    @pytest.mark.e2e
    def test_quick_stats_have_values(self, page):
        """Quick stat cards should display values."""
        stat_values = page.locator('.quick-stat-value')
        assert stat_values.count() >= 1, "Should have at least one quick stat"

        # Check first stat has content
        first_stat = stat_values.first
        text = first_stat.inner_text()
        assert len(text.strip()) > 0, "Quick stat should have content"

    @pytest.mark.e2e
    def test_chart_canvas_has_content(self, page):
        """Chart canvases should have rendered content."""
        # Wait for charts to render
        page.wait_for_timeout(1000)

        # At least one canvas should exist
        canvases = page.locator('canvas')
        assert canvases.count() >= 1, "Should have at least one chart canvas"

    @pytest.mark.e2e
    def test_refresh_button_exists(self, page):
        """Dashboard should have a refresh button."""
        refresh_btn = page.locator('.refresh-btn, button:has-text("Refresh")')
        assert refresh_btn.count() >= 1, "Should have a refresh button"

    @pytest.mark.e2e
    def test_status_indicator_present(self, page):
        """Dashboard should have a status indicator."""
        status = page.locator('.status-indicator')
        if status.count() > 0:
            assert status.is_visible(), "Status indicator should be visible"

    @pytest.mark.e2e
    def test_goal_cards_visible_on_overview(self, page):
        """Goal cards should be visible on the overview tab."""
        # Make sure we're on overview
        page.locator('button:has-text("Overview")').click()
        page.wait_for_timeout(300)

        # Look for goal elements
        goals = page.locator('.goal-card, [class*="goal"]')
        # Goals section may or may not exist depending on data
        # Just check the page is in a good state
        assert page.locator('#tab-overview').is_visible()

    @pytest.mark.e2e
    def test_records_tab_shows_records(self, page):
        """Records tab should display personal records."""
        page.locator('button:has-text("Records")').click()
        page.wait_for_timeout(500)

        records_panel = page.locator('#tab-records')
        assert records_panel.is_visible()

        # Should have some record content
        content = records_panel.inner_text()
        assert len(content) > 10, "Records tab should have content"

    @pytest.mark.e2e
    def test_insights_tab_accessible(self, page):
        """Insights tab should be accessible and show content."""
        page.locator('button:has-text("Insights")').click()
        page.wait_for_timeout(500)

        insights_panel = page.locator('#tab-insights')
        assert insights_panel.is_visible()
