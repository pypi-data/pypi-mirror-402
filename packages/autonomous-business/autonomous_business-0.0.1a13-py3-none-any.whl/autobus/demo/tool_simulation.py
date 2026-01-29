def send_to_marketing_campaign(campaign_id: str, subscription_ids:list[int]) -> None:
    """
    Simulate tool call from the generated Prolog program to send target subscriptions to a marketing campaign.
    This typically involves calling some APIs of a consumer marketing platform.
    """
    print(f"{subscription_ids} sent to marketing campaign {campaign_id}.")


def median_household_income(city: str) -> int:
    """
    This is to simulate tool call from the generated Prolog program.
    From here, it could be a call to a web search AI agent, or a call to a service provider API.
    """
    median_household_income = {
        "Austin": 91461,
        "Boston": 94755,
        "Charlotte": 80472,
        "Chicago": 94012,
        "Columbus": 87015,
        "Dallas": 93001,
        "Denver": 107090,
        "Detroit": 78416,
        "Houston": 85000,
        "Jacksonville": 68424,
        "Los Angeles": 75000,
        "New York": 79713,
        "Philadelphia": 60000,
        "Phoenix": 70000,
        "San Antonio": 78000,
        "San Diego": 83000,
        "San Francisco": 109000,
        "San Jose": 130000,
        "Seattle": 97000,
        "Washington": 100000
    }

    income = -1
    if city in median_household_income:
        income = median_household_income[city]

    return income