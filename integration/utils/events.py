def determine_integration_event(user_integration: dict, event: dict) -> tuple:
    event_name = None
    action = None
    if user_integration["integration__name"] == "Figma":
        event_name = event["event_type"]
        action = None
    elif user_integration["integration__name"] == "Github":
        event_name = event["event"]
        action = event["action"]
    elif user_integration["integration__name"] == "Slack":
        event_name = event["event"]["type"]
        action = None
    elif user_integration["integration__name"] == "Trello":
        event_name = event["type"]
        action = None
    elif user_integration["integration__name"] == "Asana":
        event_name = event["resource"]["resource_type"]
        action = event["action"]
    return event_name, action
