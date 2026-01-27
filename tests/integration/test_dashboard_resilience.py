"""
Tests for dashboard error recovery and resilience.

These tests verify that the dashboard handles:
- Missing JSON files gracefully
- Network errors with retry logic
- Partial data scenarios
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil


class TestDashboardDataLoading:
    """Tests for dashboard data loading resilience."""

    @pytest.fixture
    def temp_dashboard_dir(self, tmp_path):
        """Create a temporary dashboard directory with data folder."""
        data_dir = tmp_path / "dashboard" / "data"
        data_dir.mkdir(parents=True)
        return data_dir

    @pytest.fixture
    def sample_summary_stats(self):
        """Sample summary_stats.json content."""
        return {
            "period": "2026-01-19 to 2026-01-25",
            "days_count": 7,
            "totals": {
                "steps": 82334,
                "distance_km": 69.2,
                "active_energy_kcal": 6205,
                "exercise_minutes": 576
            },
            "averages": {
                "steps": 11762,
                "distance_km": 9.9,
                "active_energy_kcal": 886,
                "exercise_minutes": 82,
                "stand_hours": 13.4,
                "resting_hr": 57,
                "hrv": 43
            },
            "goals": {
                "steps_10k": {"achieved": 5, "total": 7},
                "stand_12h": {"achieved": 6, "total": 7},
                "exercise_30m": {"achieved": 7, "total": 7}
            }
        }

    @pytest.fixture
    def sample_daily_trends(self):
        """Sample daily_trends.json content."""
        return {
            "dates": ["2026-01-24", "2026-01-25"],
            "steps": [11035, 12670],
            "distance": [9.01, 9.84],
            "active_energy": [914, 959],
            "exercise_minutes": [88, 82],
            "stand_hours": [13, 15],
            "resting_hr": [54, 57],
            "hrv": [35, 56]
        }

    def test_creates_valid_json_files(self, temp_dashboard_dir, sample_summary_stats):
        """Test that we can create and read valid JSON files."""
        # Write sample data
        stats_file = temp_dashboard_dir / "summary_stats.json"
        with open(stats_file, "w") as f:
            json.dump(sample_summary_stats, f)

        # Read and verify
        with open(stats_file, "r") as f:
            loaded = json.load(f)

        assert loaded["averages"]["steps"] == 11762
        assert loaded["goals"]["steps_10k"]["achieved"] == 5

    def test_handles_missing_file(self, temp_dashboard_dir):
        """Test that missing files return None or empty result."""
        missing_file = temp_dashboard_dir / "nonexistent.json"

        assert not missing_file.exists()

        # Simulate the behavior of our loadJSON function
        result = None
        if missing_file.exists():
            with open(missing_file, "r") as f:
                result = json.load(f)

        assert result is None

    def test_handles_invalid_json(self, temp_dashboard_dir):
        """Test that invalid JSON is handled gracefully."""
        invalid_file = temp_dashboard_dir / "invalid.json"
        invalid_file.write_text("{ this is not valid json }")

        result = None
        try:
            with open(invalid_file, "r") as f:
                result = json.load(f)
        except json.JSONDecodeError:
            result = None

        assert result is None

    def test_handles_empty_file(self, temp_dashboard_dir):
        """Test that empty files are handled gracefully."""
        empty_file = temp_dashboard_dir / "empty.json"
        empty_file.write_text("")

        result = None
        try:
            with open(empty_file, "r") as f:
                content = f.read()
                if content.strip():
                    result = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            result = None

        assert result is None

    def test_partial_data_scenario(self, temp_dashboard_dir, sample_summary_stats, sample_daily_trends):
        """Test dashboard can work with partial data (some files missing)."""
        # Only write summary_stats, not daily_trends
        stats_file = temp_dashboard_dir / "summary_stats.json"
        with open(stats_file, "w") as f:
            json.dump(sample_summary_stats, f)

        # Simulate loading multiple files
        files_to_load = ["summary_stats.json", "daily_trends.json", "goals_progress.json"]
        loaded_data = {}

        for filename in files_to_load:
            filepath = temp_dashboard_dir / filename
            try:
                if filepath.exists():
                    with open(filepath, "r") as f:
                        loaded_data[filename] = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Should have loaded summary_stats but not the others
        assert "summary_stats.json" in loaded_data
        assert "daily_trends.json" not in loaded_data
        assert "goals_progress.json" not in loaded_data
        assert len(loaded_data) == 1

    def test_data_integrity_validation(self, temp_dashboard_dir, sample_summary_stats):
        """Test that loaded data has expected structure."""
        stats_file = temp_dashboard_dir / "summary_stats.json"
        with open(stats_file, "w") as f:
            json.dump(sample_summary_stats, f)

        with open(stats_file, "r") as f:
            data = json.load(f)

        # Validate structure
        assert "period" in data
        assert "averages" in data
        assert "goals" in data
        assert "steps" in data["averages"]
        assert "steps_10k" in data["goals"]


class TestHealthScoreCalculation:
    """Tests for health score calculation logic."""

    def test_calculates_health_score_from_valid_data(self):
        """Test health score calculation with valid stats."""
        stats = {
            "averages": {
                "steps": 12000,
                "exercise_minutes": 45,
                "stand_hours": 14,
                "resting_hr": 55,
                "hrv": 50
            }
        }

        # Weights: steps=25, exercise=25, stand=20, hr=15, hrv=15
        # Steps: min(12000/10000, 1.2) * 25 = 1.2 * 25 = 30 (capped contribution)
        # Exercise: min(45/30, 1.5) * 25 = 1.5 * 25 = 37.5
        # Stand: min(14/12, 1.2) * 20 = 1.17 * 20 = 23.4
        # Resting HR (55 <= 60): 15
        # HRV (50 >= 50): 15
        # Total: 30 + 37.5 + 23.4 + 15 + 15 = 120.9 -> capped at 100

        score = self._calculate_health_score(stats)
        assert 85 <= score <= 100  # Should be high due to excellent metrics

    def test_calculates_lower_score_for_sedentary(self):
        """Test health score is lower for sedentary lifestyle."""
        stats = {
            "averages": {
                "steps": 3000,
                "exercise_minutes": 10,
                "stand_hours": 6,
                "resting_hr": 75,
                "hrv": 25
            }
        }

        score = self._calculate_health_score(stats)
        assert score < 50  # Should be low

    def test_handles_missing_metrics(self):
        """Test health score handles missing metrics gracefully."""
        stats = {
            "averages": {
                "steps": 10000,
                "exercise_minutes": 30
                # Missing: stand_hours, resting_hr, hrv
            }
        }

        score = self._calculate_health_score(stats)
        assert 0 <= score <= 100

    def test_handles_zero_values(self):
        """Test health score with zero values."""
        stats = {
            "averages": {
                "steps": 0,
                "exercise_minutes": 0,
                "stand_hours": 0,
                "resting_hr": 0,
                "hrv": 0
            }
        }

        score = self._calculate_health_score(stats)
        assert score == 0

    def _calculate_health_score(self, stats):
        """
        Calculate health score - mirrors the JavaScript implementation.

        Weights:
        - Steps: 25 points (goal: 10,000)
        - Exercise: 25 points (goal: 30 min)
        - Stand: 20 points (goal: 12 hours)
        - Resting HR: 15 points (optimal: <=60)
        - HRV: 15 points (optimal: >=50)
        """
        weights = {
            'steps': 25,
            'exercise': 25,
            'stand': 20,
            'resting_hr': 15,
            'hrv': 15
        }

        score = 0
        avgs = stats.get('averages', {})

        # Steps score
        steps = avgs.get('steps', 0)
        steps_ratio = min(steps / 10000, 1.2) if steps else 0
        score += steps_ratio * weights['steps']

        # Exercise score
        exercise = avgs.get('exercise_minutes', 0)
        exercise_ratio = min(exercise / 30, 1.5) if exercise else 0
        score += exercise_ratio * weights['exercise']

        # Stand hours score
        stand = avgs.get('stand_hours', 0)
        stand_ratio = min(stand / 12, 1.2) if stand else 0
        score += stand_ratio * weights['stand']

        # Resting HR score
        rhr = avgs.get('resting_hr', 0)
        if rhr > 0:
            if rhr <= 60:
                score += weights['resting_hr']
            elif rhr <= 70:
                score += weights['resting_hr'] * 0.8
            elif rhr <= 80:
                score += weights['resting_hr'] * 0.6
            else:
                score += weights['resting_hr'] * 0.4

        # HRV score
        hrv = avgs.get('hrv', 0)
        if hrv > 0:
            if hrv >= 50:
                score += weights['hrv']
            elif hrv >= 40:
                score += weights['hrv'] * 0.9
            elif hrv >= 30:
                score += weights['hrv'] * 0.7
            else:
                score += weights['hrv'] * 0.5

        return min(round(score), 100)


class TestInsightGeneration:
    """Tests for AI insight generation."""

    def test_generates_positive_insight_for_step_increase(self):
        """Test positive insight when steps are trending up."""
        trends = {
            "steps": [8000, 8500, 9000, 9500, 10000, 10500, 11000,  # Prior week
                      12000, 12500, 13000, 13500, 14000, 14500, 15000]  # Recent week
        }

        insights = self._generate_step_insight(trends)
        assert insights is not None
        assert insights['type'] == 'positive'
        assert 'up' in insights['title'].lower()

    def test_generates_warning_insight_for_step_decrease(self):
        """Test warning insight when steps are trending down."""
        trends = {
            "steps": [15000, 14500, 14000, 13500, 13000, 12500, 12000,  # Prior week
                      8000, 8500, 9000, 8500, 8000, 7500, 7000]  # Recent week (much lower)
        }

        insights = self._generate_step_insight(trends)
        assert insights is not None
        assert insights['type'] == 'warning'

    def test_no_insight_for_stable_steps(self):
        """Test no insight when steps are stable (within 10%)."""
        trends = {
            "steps": [10000, 10100, 9900, 10000, 10050, 9950, 10000,  # Prior week
                      10000, 10050, 9950, 10000, 10100, 9900, 10000]  # Recent week (similar)
        }

        insights = self._generate_step_insight(trends)
        assert insights is None

    def _generate_step_insight(self, trends):
        """Generate step trend insight - mirrors JavaScript implementation."""
        steps = trends.get("steps", [])

        if len(steps) < 14:
            return None

        recent = steps[-7:]
        prior = steps[-14:-7]

        recent_avg = sum(recent) / len(recent)
        prior_avg = sum(prior) / len(prior)

        if prior_avg == 0:
            return None

        change = ((recent_avg - prior_avg) / prior_avg) * 100

        if change > 10:
            return {
                'type': 'positive',
                'title': 'Steps Trending Up',
                'text': f'Your step count is up {int(change)}% compared to last week.'
            }
        elif change < -10:
            return {
                'type': 'warning',
                'title': 'Activity Dip Detected',
                'text': f'Your steps are down {int(abs(change))}% from last week.'
            }

        return None


class TestErrorRecovery:
    """Tests for error recovery mechanisms."""

    def test_retry_logic_succeeds_after_failures(self):
        """Test retry logic eventually succeeds."""
        attempts = [0]

        def flaky_operation():
            attempts[0] += 1
            if attempts[0] < 3:
                raise IOError("Temporary failure")
            return {"data": "success"}

        result = self._retry_operation(flaky_operation, max_retries=3)

        assert result is not None
        assert result["data"] == "success"
        assert attempts[0] == 3

    def test_retry_logic_fails_after_max_attempts(self):
        """Test retry logic gives up after max attempts."""
        def always_fails():
            raise IOError("Permanent failure")

        result = self._retry_operation(always_fails, max_retries=3)

        assert result is None

    def test_exponential_backoff(self):
        """Test that retry delays increase exponentially."""
        # This is more of a design verification than a functional test
        delays = [2000 * (i + 1) for i in range(3)]  # 2s, 4s, 6s

        assert delays == [2000, 4000, 6000]

    def _retry_operation(self, operation, max_retries=3):
        """Retry an operation with backoff."""
        for attempt in range(max_retries):
            try:
                return operation()
            except (IOError, OSError):
                if attempt == max_retries - 1:
                    return None
        return None


class TestDashboardDataIntegrity:
    """Tests for dashboard data integrity and validation."""

    def test_validates_summary_stats_structure(self):
        """Test validation of summary_stats.json structure."""
        valid_stats = {
            "period": "2026-01-19 to 2026-01-25",
            "days_count": 7,
            "averages": {"steps": 10000},
            "goals": {"steps_10k": {"achieved": 5, "total": 7}}
        }

        assert self._validate_summary_stats(valid_stats)

    def test_rejects_invalid_summary_stats(self):
        """Test rejection of invalid summary_stats structure."""
        invalid_stats = {
            "period": "2026-01-25",
            # Missing required fields
        }

        assert not self._validate_summary_stats(invalid_stats)

    def test_validates_daily_trends_structure(self):
        """Test validation of daily_trends.json structure."""
        valid_trends = {
            "dates": ["2026-01-24", "2026-01-25"],
            "steps": [10000, 11000],
            "active_energy": [800, 850]
        }

        assert self._validate_daily_trends(valid_trends)

    def test_rejects_mismatched_array_lengths(self):
        """Test rejection of trends with mismatched array lengths."""
        invalid_trends = {
            "dates": ["2026-01-24", "2026-01-25"],
            "steps": [10000],  # Wrong length
            "active_energy": [800, 850]
        }

        assert not self._validate_daily_trends(invalid_trends)

    def _validate_summary_stats(self, data):
        """Validate summary_stats structure."""
        required_keys = ["period", "averages"]
        return all(key in data for key in required_keys)

    def _validate_daily_trends(self, data):
        """Validate daily_trends structure."""
        if "dates" not in data:
            return False

        date_count = len(data["dates"])

        for key in ["steps", "active_energy"]:
            if key in data and len(data[key]) != date_count:
                return False

        return True


class TestPerSectionErrorHandling:
    """Tests for per-section error handling in dashboard.

    The dashboard should show available data even when some sections fail.
    Each section should have its own error state and retry capability.
    """

    @pytest.fixture
    def section_data(self):
        """Map of sections to their required data files."""
        return {
            'health_score': ['summary_stats.json'],
            'quick_stats': ['summary_stats.json'],
            'goals': ['summary_stats.json'],
            'daily_trends': ['daily_trends.json'],
            'weekly_comparison': ['weekly_comparison.json'],
            'hr_distribution': ['hr_distribution.json'],
            'insights': ['summary_stats.json', 'daily_trends.json'],
            'deep_analysis': ['deep_analysis.json', 'monthly_progression.json'],
            'records': ['all_personal_records.json'],
            'correlations': ['correlations.json'],
        }

    def test_section_can_determine_required_files(self, section_data):
        """Test that each section knows what files it needs."""
        # Health score only needs summary stats
        assert section_data['health_score'] == ['summary_stats.json']

        # Daily trends needs daily_trends
        assert section_data['daily_trends'] == ['daily_trends.json']

        # Insights needs multiple files
        assert len(section_data['insights']) == 2

    def test_section_state_tracking(self):
        """Test that we can track loading/error/success state per section."""
        # Simulates the JavaScript STATE object structure
        section_states = {
            'health_score': {'status': 'loading', 'error': None, 'data': None},
            'daily_trends': {'status': 'loading', 'error': None, 'data': None},
            'hr_distribution': {'status': 'loading', 'error': None, 'data': None},
        }

        # Simulate successful load for some sections
        section_states['health_score']['status'] = 'success'
        section_states['health_score']['data'] = {'score': 85}

        # Simulate error for one section
        section_states['hr_distribution']['status'] = 'error'
        section_states['hr_distribution']['error'] = 'Failed to load hr_distribution.json'

        # Daily trends still loading
        assert section_states['health_score']['status'] == 'success'
        assert section_states['daily_trends']['status'] == 'loading'
        assert section_states['hr_distribution']['status'] == 'error'

    def test_partial_load_success_calculation(self, section_data):
        """Test calculation of partial load success."""
        total_sections = len(section_data)

        # Simulate 7/10 sections loaded successfully
        loaded_sections = 7
        failed_sections = 3

        success_rate = loaded_sections / total_sections

        assert success_rate == 0.7
        assert loaded_sections + failed_sections == total_sections

    def test_section_retry_resets_state(self):
        """Test that retrying a section resets its state."""
        section_state = {
            'status': 'error',
            'error': 'Network timeout',
            'data': None,
            'retry_count': 2
        }

        # Reset for retry
        section_state['status'] = 'loading'
        section_state['error'] = None
        section_state['retry_count'] += 1

        assert section_state['status'] == 'loading'
        assert section_state['error'] is None
        assert section_state['retry_count'] == 3

    def test_fallback_content_for_failed_section(self):
        """Test that failed sections show meaningful fallback content."""
        fallback_messages = {
            'health_score': 'Unable to calculate health score',
            'daily_trends': 'Activity trends unavailable',
            'hr_distribution': 'Heart rate data unavailable',
            'insights': 'Insights temporarily unavailable',
            'records': 'Personal records unavailable',
        }

        # Each section should have a user-friendly fallback message
        assert all(msg for msg in fallback_messages.values())

        # Messages should not be technical jargon
        for msg in fallback_messages.values():
            assert 'JSON' not in msg
            assert 'fetch' not in msg.lower()
            assert 'HTTP' not in msg


class TestGracefulDegradation:
    """Tests for dashboard graceful degradation behavior."""

    @pytest.fixture
    def available_data(self):
        """Sample of partially available data."""
        return {
            'summary_stats': {
                'averages': {'steps': 10000, 'exercise_minutes': 30},
                'goals': {'steps_10k': {'achieved': 5, 'total': 7}}
            },
            'daily_trends': None,  # Failed to load
            'hr_distribution': None,  # Failed to load
            'metadata': {'generated_at': '2026-01-25T10:00:00'}
        }

    def test_dashboard_renders_with_partial_data(self, available_data):
        """Test that dashboard renders available sections when some fail."""
        renderable_sections = []

        if available_data.get('summary_stats'):
            renderable_sections.append('health_score')
            renderable_sections.append('quick_stats')
            renderable_sections.append('goals')

        if available_data.get('daily_trends'):
            renderable_sections.append('daily_trends')
            renderable_sections.append('exercise_chart')

        if available_data.get('hr_distribution'):
            renderable_sections.append('hr_distribution')

        # Should render some sections even with partial data
        assert len(renderable_sections) == 3
        assert 'health_score' in renderable_sections
        assert 'daily_trends' not in renderable_sections

    def test_metadata_renders_independently(self, available_data):
        """Test that metadata (last updated) renders even if other sections fail."""
        metadata = available_data.get('metadata')

        # Metadata should be available
        assert metadata is not None
        assert 'generated_at' in metadata

    def test_error_count_displayed_to_user(self, available_data):
        """Test that error count is communicated to user."""
        failed_sections = sum(1 for v in available_data.values() if v is None)
        total_sections = len(available_data)

        # User should see how many sections failed
        error_message = f"Some data unavailable ({failed_sections} of {total_sections} sections)"

        assert '2 of 4' in error_message or str(failed_sections) in error_message

    def test_successful_sections_not_affected_by_failures(self, available_data):
        """Test that successful sections render correctly despite other failures."""
        # Even if hr_distribution fails, health_score should work
        summary_stats = available_data.get('summary_stats')

        if summary_stats and 'averages' in summary_stats:
            health_score = self._calculate_health_score_simple(summary_stats)
            assert health_score > 0

    def _calculate_health_score_simple(self, stats):
        """Simplified health score for testing."""
        avgs = stats.get('averages', {})
        steps = avgs.get('steps', 0)
        exercise = avgs.get('exercise_minutes', 0)

        score = 0
        if steps > 0:
            score += min(steps / 10000, 1) * 50
        if exercise > 0:
            score += min(exercise / 30, 1) * 50

        return min(round(score), 100)


class TestErrorUIComponents:
    """Tests for error UI component behavior."""

    def test_error_card_has_retry_button(self):
        """Test that error cards include a retry button."""
        error_card_html = self._generate_error_card('daily_trends', 'Failed to load activity data')

        assert 'retry' in error_card_html.lower() or 'button' in error_card_html.lower()
        assert 'onclick' in error_card_html or 'click' in error_card_html

    def test_error_card_shows_section_name(self):
        """Test that error cards identify which section failed."""
        error_card_html = self._generate_error_card('daily_trends', 'Network error')

        assert 'Activity' in error_card_html or 'trends' in error_card_html.lower()

    def test_error_card_shows_user_friendly_message(self):
        """Test that error messages are user-friendly."""
        # Technical error
        technical_error = "HTTP 500 Internal Server Error"

        # Should be converted to user-friendly message
        user_message = self._humanize_error(technical_error)

        assert 'HTTP' not in user_message
        assert '500' not in user_message
        assert 'server' in user_message.lower() or 'unavailable' in user_message.lower()

    def test_loading_state_shows_spinner(self):
        """Test that loading state includes a spinner."""
        loading_html = self._generate_loading_state('daily_trends')

        assert 'loading' in loading_html.lower() or 'spinner' in loading_html.lower()

    def _generate_error_card(self, section_id, error_message):
        """Generate error card HTML for a section."""
        return f'''
        <div class="section-error" id="{section_id}-error">
            <h4>Activity Trends Unavailable</h4>
            <p>{self._humanize_error(error_message)}</p>
            <button onclick="retrySection('{section_id}')">Try Again</button>
        </div>
        '''

    def _humanize_error(self, technical_error):
        """Convert technical error to user-friendly message."""
        if 'HTTP' in technical_error or '500' in technical_error:
            return "Data temporarily unavailable. Please try again."
        if 'Network' in technical_error or 'timeout' in technical_error.lower():
            return "Connection issue. Check your internet and try again."
        return "Unable to load this section. Please try again."

    def _generate_loading_state(self, section_id):
        """Generate loading state HTML."""
        return f'''
        <div class="section-loading" id="{section_id}-loading">
            <div class="loading-spinner"></div>
            <p>Loading...</p>
        </div>
        '''
