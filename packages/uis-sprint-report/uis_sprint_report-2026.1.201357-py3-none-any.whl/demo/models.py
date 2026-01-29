"""
This module defines data models using Pydantic for structured data representation and validation
within the UIS Sprint Report application. These models are essential for ensuring that data
conforms to expected formats throughout the application's logic, especially when generating,
processing, and responding to sprint-related data.

Classes:
- Activity: Represents an individual sprint activity, detailing its current status and description.
- SprintReport: Aggregates multiple activities into a single report format.
- ResponseModel: Formats responses to user queries for consistent interaction.
"""
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List


class Activity(BaseModel):
    """
    Represents a single activity within a sprint, providing a structured format for maintaining
    the title, brief description, and current status of the activity.

    Attributes:
        title (str): Summarizes the main goal or purpose of the activity.
        brief_desc_status (str): Provides a concise description of the activity's current status.
        status (str): Indicates the current progress status of the activity (e.g., 'Planned', 'InProgress', 'Completed').
    """
    title: str = Field(..., description="The title of the activity, summarizing the main goal or purpose of the activity.")
    brief_desc_status: str = Field(..., description="A short and concise description of the status activity, summarizing its main status.")
    status: str = Field(..., description="The current status of the activity, indicating its progress such as 'Planned', 'InProgress', or 'Completed'.")


class SprintReport(BaseModel):
    """
    Aggregates multiple activities into a structured sprint report, suitable for generating
    detailed overviews of sprint progress.

    Attributes:
        activities (List[Activity]): A list of activities, each represented by an `Activity` instance.
    """
    activities: List[Activity] = Field(..., description="A list of main activities, each described with a title, brief description status, and current status, summarizing the sprint's progress.")


class ResponseModel(BaseModel):
    """
    Provides a structured format for responses to user queries, ensuring consistency across
    different parts of the application when communicating results or statuses to users.

    Attributes:
        response (str): The actual text response provided to the user, encapsulating the answer or information requested.
    """
    response: str = Field(..., description="The response to the user query, providing the requested information.")