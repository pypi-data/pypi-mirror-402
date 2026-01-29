prompts = {
    "generate_report": {
        "question": "Generate a JSON-formatted concise report summarizing the main activities from the sprint board. For each activity, include a title, a brief status description and its current status. The JSON should be structured as a list of activities, each with `title`, 'brief_desc_status' and 'status' fields. Status examples include 'Planned', 'InProgress', 'Completed', 'Blocked', and 'Closed'. This structured report should provide a clear overview of the sprint's progress and highlight areas needing attention. Example of expected JSON output: {'activities':[{'title':'Update project documentation','brief_desc_status':'The most of the issues are resolved','status':'InProgress'},{'title':'Fix the critical bug','brief_desc_status':'The bug is fixed, but the tests are failing','status':'Blocked'}]}",
        "additional_info": "The sprint goals were:",
    },
    "chat": {
        "question": "The answer should be a JSON-formatted response to the user query. The example is {'response':'The answer to the user query'}",
    }
}