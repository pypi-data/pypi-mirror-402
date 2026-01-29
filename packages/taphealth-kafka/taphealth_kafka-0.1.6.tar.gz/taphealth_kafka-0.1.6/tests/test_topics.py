"""
Tests for Topics enum.

Test Coverage:
=============

Enum Structure
--------------
- test_topics_is_enum: Topics is an Enum class
- test_topics_inherits_from_str: Topics inherits from str (can be used as string)
- test_topics_member_count: Correct number of topic members

Topic Values
------------
- test_all_topics_are_strings: All topic values are strings
- test_topic_values_are_kebab_case: All values use kebab-case format
- test_topic_values_are_lowercase: All values are lowercase
- test_topic_values_have_no_spaces: No topic values contain spaces
- test_topic_values_have_no_underscores: No topic values contain underscores

Known Topics
------------
- test_known_topics_exist: All expected topics are present
- test_weekly_plan_created_value: WEEKLY_PLAN_CREATED has correct value
- test_update_weekly_nutrition_plan_value: UPDATE_WEEEKLY_NUTRTION_PLAN has correct value
- test_update_weekly_plan_value: UPDATE_WEEKLY_PLAN has correct value
- test_conversation_summary_value: CONVERSATION_SUMMARY has correct value
- test_profile_updated_value: PROFILE_UPDATED has correct value
- test_daily_plan_created_value: DAILY_PLAN_CREATED has correct value
- test_diet_created_value: DIET_CREATED has correct value
- test_exercise_logged_value: EXERCISE_LOGGED has correct value
- test_glucose_logged_value: GLUCOSE_LOGGED has correct value
- test_meal_logged_value: MEAL_LOGGED has correct value
- test_metric_logged_value: METRIC_LOGGED has correct value
- test_voice_analytics_value: VOICE_ANALYTICS has correct value

get_all_topics Method
---------------------
- test_get_all_topics_returns_list: get_all_topics returns a list
- test_get_all_topics_length_matches_enum: List length matches enum member count
- test_get_all_topics_contains_all_values: All enum values are in the list
- test_get_all_topics_returns_values_not_names: Returns .value not .name

String Behavior
---------------
- test_topic_can_be_used_as_string: Topic enum can be used directly as string
- test_topic_value_equality: Topic value equals expected string
- test_topic_string_concatenation: Topic can be concatenated with strings
"""

from enum import Enum

from taphealth_kafka import Topics


class TestTopicsEnumStructure:
    """Tests for Topics enum structure."""

    def test_topics_is_enum(self):
        """Topics is an Enum class."""
        assert issubclass(Topics, Enum)

    def test_topics_inherits_from_str(self):
        """Topics inherits from str, allowing direct string usage."""
        assert issubclass(Topics, str)

    def test_topics_member_count(self):
        """Topics has expected number of members."""
        # Update this when topics are added/removed
        assert len(Topics) == 12


class TestTopicsValues:
    """Tests for Topics value format."""

    def test_all_topics_are_strings(self):
        """All topic values are strings."""
        for topic in Topics:
            assert isinstance(topic.value, str)

    def test_topic_values_are_kebab_case(self):
        """All topic values use kebab-case format (words separated by hyphens)."""
        for topic in Topics:
            # Kebab-case: lowercase letters and hyphens only
            assert all(c.islower() or c == "-" for c in topic.value), (
                f"Topic {topic.name} value '{topic.value}' is not kebab-case"
            )

    def test_topic_values_are_lowercase(self):
        """All topic values are lowercase."""
        for topic in Topics:
            assert topic.value == topic.value.lower(), (
                f"Topic {topic.name} value '{topic.value}' is not lowercase"
            )

    def test_topic_values_have_no_spaces(self):
        """No topic values contain spaces."""
        for topic in Topics:
            assert " " not in topic.value, (
                f"Topic {topic.name} value '{topic.value}' contains spaces"
            )

    def test_topic_values_have_no_underscores(self):
        """No topic values contain underscores (use hyphens instead)."""
        for topic in Topics:
            assert "_" not in topic.value, (
                f"Topic {topic.name} value '{topic.value}' contains underscores"
            )


class TestKnownTopics:
    """Tests for specific known topics."""

    def test_known_topics_exist(self):
        """All expected topics are present in the enum."""
        expected_topics = [
            "weekly-plan-created",
            "update-weekly-nutrition-plan",
            "update-weekly-plan",
            "conversation-summary",
            "profile-updated",
            "daily-plan-created",
            "diet-created",
            "exercise-logged",
            "glucose-logged",
            "meal-logged",
            "metric-logged",
            "voice-analytics",
        ]

        all_topics = Topics.get_all_topics()

        for topic in expected_topics:
            assert topic in all_topics, f"Missing topic: {topic}"

    def test_weekly_plan_created_value(self):
        """WEEKLY_PLAN_CREATED has correct value."""
        assert Topics.WEEKLY_PLAN_CREATED.value == "weekly-plan-created"

    def test_update_weekly_nutrition_plan_value(self):
        """UPDATE_WEEEKLY_NUTRTION_PLAN has correct value."""
        assert (
            Topics.UPDATE_WEEEKLY_NUTRTION_PLAN.value == "update-weekly-nutrition-plan"
        )

    def test_update_weekly_plan_value(self):
        """UPDATE_WEEKLY_PLAN has correct value."""
        assert Topics.UPDATE_WEEKLY_PLAN.value == "update-weekly-plan"

    def test_conversation_summary_value(self):
        """CONVERSATION_SUMMARY has correct value."""
        assert Topics.CONVERSATION_SUMMARY.value == "conversation-summary"

    def test_profile_updated_value(self):
        """PROFILE_UPDATED has correct value."""
        assert Topics.PROFILE_UPDATED.value == "profile-updated"

    def test_daily_plan_created_value(self):
        """DAILY_PLAN_CREATED has correct value."""
        assert Topics.DAILY_PLAN_CREATED.value == "daily-plan-created"

    def test_diet_created_value(self):
        """DIET_CREATED has correct value."""
        assert Topics.DIET_CREATED.value == "diet-created"

    def test_exercise_logged_value(self):
        """EXERCISE_LOGGED has correct value."""
        assert Topics.EXERCISE_LOGGED.value == "exercise-logged"

    def test_glucose_logged_value(self):
        """GLUCOSE_LOGGED has correct value."""
        assert Topics.GLUCOSE_LOGGED.value == "glucose-logged"

    def test_meal_logged_value(self):
        """MEAL_LOGGED has correct value."""
        assert Topics.MEAL_LOGGED.value == "meal-logged"

    def test_metric_logged_value(self):
        """METRIC_LOGGED has correct value."""
        assert Topics.METRIC_LOGGED.value == "metric-logged"

    def test_voice_analytics_value(self):
        """VOICE_ANALYTICS has correct value."""
        assert Topics.VOICE_ANALYTICS.value == "voice-analytics"


class TestGetAllTopics:
    """Tests for Topics.get_all_topics() method."""

    def test_get_all_topics_returns_list(self):
        """get_all_topics returns a list."""
        all_topics = Topics.get_all_topics()

        assert isinstance(all_topics, list)

    def test_get_all_topics_length_matches_enum(self):
        """get_all_topics list length matches enum member count."""
        all_topics = Topics.get_all_topics()

        assert len(all_topics) == len(Topics)

    def test_get_all_topics_contains_all_values(self):
        """get_all_topics contains all enum values."""
        all_topics = Topics.get_all_topics()

        for topic in Topics:
            assert topic.value in all_topics

    def test_get_all_topics_returns_values_not_names(self):
        """get_all_topics returns .value strings, not .name strings."""
        all_topics = Topics.get_all_topics()

        # Values are kebab-case, names are UPPER_SNAKE_CASE
        assert "weekly-plan-created" in all_topics
        assert "WEEKLY_PLAN_CREATED" not in all_topics

    def test_get_all_topics_no_duplicates(self):
        """get_all_topics contains no duplicate values."""
        all_topics = Topics.get_all_topics()

        assert len(all_topics) == len(set(all_topics))


class TestTopicsStringBehavior:
    """Tests for Topics string behavior (inherits from str)."""

    def test_topic_can_be_used_as_string(self):
        """Topic enum can be used directly as a string due to str inheritance."""
        topic = Topics.WEEKLY_PLAN_CREATED

        # Can be compared directly to string
        assert topic == "weekly-plan-created"

    def test_topic_value_equality(self):
        """Topic value equals expected string."""
        assert Topics.WEEKLY_PLAN_CREATED.value == "weekly-plan-created"
        assert Topics.DIET_CREATED.value == "diet-created"

    def test_topic_string_concatenation(self):
        """Topic can be concatenated with strings."""
        topic = Topics.WEEKLY_PLAN_CREATED
        prefix = "kafka-topic-"

        result = prefix + topic

        assert result == "kafka-topic-weekly-plan-created"

    def test_topic_in_string_formatting(self):
        """Topic value can be used in string formatting."""
        topic = Topics.WEEKLY_PLAN_CREATED

        result = f"Subscribing to {topic.value}"

        assert result == "Subscribing to weekly-plan-created"

    def test_topic_in_list_with_strings(self):
        """Topic can be used in list operations with strings."""
        topics = ["other-topic", Topics.WEEKLY_PLAN_CREATED, "another-topic"]

        assert "weekly-plan-created" in topics
        assert Topics.WEEKLY_PLAN_CREATED in topics


class TestTopicsEnumAccess:
    """Tests for accessing Topics enum members."""

    def test_access_by_name(self):
        """Topics can be accessed by name."""
        topic = Topics["WEEKLY_PLAN_CREATED"]

        assert topic == Topics.WEEKLY_PLAN_CREATED

    def test_access_by_value(self):
        """Topics can be accessed by value."""
        topic = Topics("weekly-plan-created")

        assert topic == Topics.WEEKLY_PLAN_CREATED

    def test_iteration_yields_all_members(self):
        """Iterating over Topics yields all members."""
        topics_list = list(Topics)

        assert len(topics_list) == 12
        assert Topics.WEEKLY_PLAN_CREATED in topics_list
        assert Topics.VOICE_ANALYTICS in topics_list
