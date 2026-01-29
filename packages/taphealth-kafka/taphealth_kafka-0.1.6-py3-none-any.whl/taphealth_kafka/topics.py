from enum import Enum


class Topics(str, Enum):
    WEEKLY_PLAN_CREATED = "weekly-plan-created"
    UPDATE_WEEEKLY_NUTRTION_PLAN = "update-weekly-nutrition-plan"
    UPDATE_WEEKLY_PLAN = "update-weekly-plan"
    CONVERSATION_SUMMARY = "conversation-summary"
    PROFILE_UPDATED = "profile-updated"
    DAILY_PLAN_CREATED = "daily-plan-created"
    DIET_CREATED = "diet-created"
    EXERCISE_LOGGED = "exercise-logged"
    GLUCOSE_LOGGED = "glucose-logged"
    MEAL_LOGGED = "meal-logged"
    METRIC_LOGGED = "metric-logged"
    VOICE_ANALYTICS = "voice-analytics"

    @classmethod
    def get_all_topics(cls):
        return [topic.value for topic in cls]
