from django.http import HttpRequest


def get_user_agent(request: HttpRequest) -> str | None:
    return request.META.get("HTTP_USER_AGENT")
