import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from core.models import TalentProfile, ProfileReview
from core.services.github_service import GitHubService, GitHubServiceError

# Support singular or plural naming for AI service
try:
    from core.services.ai_services import (
        AIService,
        AIServiceError,
        EvaluationOutput,
        SignalsBreakdown,
    )
except ImportError:
    from core.services.ai_service import (
        AIService,
        AIServiceError,
        EvaluationOutput,
        SignalsBreakdown,
    )


class TalentProfileModelTests(TestCase):
    """Verifies database constraints, custom str representations, and relationships."""

    def setUp(self):
        self.profile = TalentProfile.objects.create(
            username="ezra-builder",
            name="Ezra Builder",
            avatar_url="https://avatars.githubusercontent.com/u/104193473?v=4",
            bio="Building scalable backend systems.",
            location="Lagos, Nigeria",
            public_repos_count=18,
            followers_count=42,
            primary_role="Backend Engineer",
            seniority_level="ENTRY",
            confidence_score=75,
            top_skills=["Python", "Django", "SQL", "REST APIs"],
            metrics_signals={
                "commit_cadence": "High",
                "architecture_depth": "Modular Django architecture with relational models.",
                "collaboration": "Active contributor across public repositories.",
            },
            summary="Demonstrates high velocity and clean repository organization.",
        )

    def test_talent_profile_creation_and_string_representation(self):
        expected_str = f"ezra-builder - Backend Engineer ({self.profile.get_seniority_level_display()})"
        self.assertEqual(str(self.profile), expected_str)
        self.assertEqual(self.profile.confidence_score, 75)
        self.assertEqual(len(self.profile.top_skills), 4)

    def test_profile_review_creation_and_cascade(self):
        review = ProfileReview.objects.create(
            profile=self.profile,
            reviewer_name="Sarah Connor",
            reviewer_title="Staff Engineering Lead",
            rating=5,
            comment="Consistently produces well-structured Django services.",
        )
        self.assertEqual(self.profile.reviews.count(), 1)
        self.assertEqual(review.profile, self.profile)
        self.assertEqual(review.rating, 5)

        self.profile.delete()
        self.assertEqual(ProfileReview.objects.count(), 0)


class GitHubServiceTests(TestCase):
    """Verifies GitHub data extraction, forked repo stripping, and error handling via httpx."""

    def setUp(self):
        self.service = GitHubService()

    @patch("httpx.Client.get")
    def test_fetch_user_data_filters_forks_and_extracts_metrics(self, mock_httpx_get):
        # 1. Profile response
        mock_user = MagicMock()
        mock_user.status_code = 200
        mock_user.json.return_value = {
            "login": "testuser",
            "name": "Test Builder",
            "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
            "bio": "Open-source contributor",
            "location": "Nairobi, Kenya",
            "public_repos": 4,
            "followers": 80,
        }

        # 2. Repositories response (1 original repo, 1 fork to filter)
        mock_repos = MagicMock()
        mock_repos.status_code = 200
        mock_repos.json.return_value = [
            {
                "name": "production-api",
                "fork": False,
                "stargazers_count": 15,
                "forks_count": 2,
                "language": "Python",
                "description": "Enterprise API service",
                "topics": ["django", "api"],
                "pushed_at": "2026-09-20T10:00:00Z",
            },
            {
                "name": "cloned-tutorial",
                "fork": True,
                "stargazers_count": 500,
                "forks_count": 0,
                "language": "JavaScript",
            },
        ]

        # 3. Events response (1 PushEvent with 2 commits)
        mock_events = MagicMock()
        mock_events.status_code = 200
        mock_events.json.return_value = [
            {
                "type": "PushEvent",
                "payload": {"commits": [{"sha": "abc1"}, {"sha": "abc2"}]},
            },
            {"type": "WatchEvent", "payload": {}},
        ]

        def side_effect_router(path, *args, **kwargs):
            if "/repos" in path:
                return mock_repos
            if "/events" in path:
                return mock_events
            return mock_user

        mock_httpx_get.side_effect = side_effect_router

        result = self.service.fetch_user_data("testuser")

        self.assertEqual(result["profile"]["username"], "testuser")
        self.assertEqual(len(result["notable_repositories"]), 1)
        self.assertEqual(result["notable_repositories"][0]["name"], "production-api")
        self.assertEqual(result["stats"]["recent_public_commits"], 2)
        self.assertIn("Python", result["stats"]["primary_languages"])

    @patch("httpx.Client.get")
    def test_fetch_user_data_raises_error_on_404(self, mock_httpx_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_httpx_get.return_value = mock_resp

        with self.assertRaises(GitHubServiceError):
            self.service.fetch_user_data("non_existent_dev_404")


class AIServiceSchemaTests(TestCase):
    """Verifies Pydantic structured output validation."""

    def test_valid_evaluation_schema_parsing(self):
        payload = {
            "primary_role": "Fullstack Engineer",
            "seniority_level": "MID",
            "confidence_score": 86,
            "top_skills": ["Python", "Django", "TypeScript", "React"],
            "metrics_signals": {
                "commit_cadence": "High",
                "architecture_depth": "Containerized multi-service deployment with Docker.",
                "collaboration": "Active PRs and code reviews.",
            },
            "summary": "Proven mid-level engineer exhibiting clean decoupling and high velocity.",
        }

        output = EvaluationOutput.model_validate(payload)
        self.assertEqual(output.seniority_level, "MID")
        self.assertEqual(output.confidence_score, 86)
        self.assertIn("TypeScript", output.top_skills)


class ViewsAndWorkflowTests(TestCase):
    """Verifies single-scroll views, 24-hr caching, badge generator, and reviews."""

    def setUp(self):
        self.client = Client()
        self.profile = TalentProfile.objects.create(
            username="tiangolo",
            name="Sebastián Ramírez",
            avatar_url="https://avatars.githubusercontent.com/u/1326112?v=4",
            primary_role="Senior Systems Architect",
            seniority_level="SENIOR",
            confidence_score=98,
            top_skills=["Python", "FastAPI", "Docker", "Pydantic"],
            metrics_signals={
                "commit_cadence": "Consistent High",
                "architecture_depth": "World-class open source frameworks.",
                "collaboration": "75k+ stars across global enterprise ecosystems.",
            },
            summary="Exceptional senior architectural capability.",
        )

    def test_index_view_loads_correctly(self):
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DevAudit")
        self.assertContains(response, "Hire")
        self.assertContains(response, "How DevAudit Works")

    def test_index_view_with_demo_query_param(self):
        response = self.client.get(f"{reverse('core:index')}?user=tiangolo#audit-result")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sebastián Ramírez")
        self.assertContains(response, "Senior Systems Architect")

    def test_dynamic_svg_badge_for_existing_user(self):
        response = self.client.get(reverse("core:badge", kwargs={"username": "tiangolo"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)
        self.assertIn(b"DevAudit", response.content)
        self.assertIn(b"Senior Systems Architect", response.content)

    def test_dynamic_svg_badge_for_unregistered_user(self):
        response = self.client.get(reverse("core:badge", kwargs={"username": "ghost_dev_999"}))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Candidate Not Audited", response.content)

    @patch("core.views.GitHubService")
    @patch("core.views.AIService")
    def test_audit_reuses_cache_within_24_hours(self, mock_ai_cls, mock_gh_cls):
        # tiangolo profile was updated in setUp (within 24 hours)
        response = self.client.post(reverse("core:audit"), {"username": "tiangolo"})
        self.assertEqual(response.status_code, 200)

        # Confirm external API calls were skipped
        mock_gh_cls.assert_not_called()
        mock_ai_cls.assert_not_called()

    def test_add_review_endpoint_creates_record(self):
        review_url = reverse("core:add_review", kwargs={"username": "tiangolo"})
        response = self.client.post(
            review_url,
            {
                "reviewer_name": "CTO Techstar",
                "reviewer_title": "Head of Engineering",
                "rating": 5,
                "comment": "Incredible contribution velocity and clean architecture design.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.profile.reviews.count(), 1)
        self.assertEqual(self.profile.reviews.first().reviewer_name, "CTO Techstar")