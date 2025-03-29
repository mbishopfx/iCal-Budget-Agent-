from datetime import datetime, timedelta
import json
import openai
import re
from icalendar import Event

# Event categories and their colors
EVENT_CATEGORIES = {
    "financial": "#4CAF50",  # Green
    "meal": "#FF9800",       # Orange
    "workout": "#2196F3",    # Blue
    "learning": "#9C27B0",   # Purple
    "hobby": "#E91E63",      # Pink
    "work": "#FF5722",       # Deep Orange
    "other": "#607D8B"       # Grey
}

def check_event_overlap(event1_start, event1_end, event2_start, event2_end):
    """Check if two events overlap."""
    return (event1_start < event2_end and event2_start < event1_end)

def validate_work_schedule(work_schedule):
    """Validate work schedule to ensure reasonable hours."""
    if not work_schedule:
        return None
        
    start_time = work_schedule.get("start_time", "09:00")
    end_time = work_schedule.get("end_time", "17:00")
    
    try:
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')
        
        # Ensure work hours are between 6 AM and 10 PM
        if start.hour < 6 or end.hour > 22:
            print("Warning: Work hours should be between 6 AM and 10 PM")
            return None
            
        # Ensure work duration is reasonable (between 4 and 12 hours)
        duration = (end - start).total_seconds() / 3600
        if duration < 4 or duration > 12:
            print("Warning: Work duration should be between 4 and 12 hours")
            return None
            
        return work_schedule
    except ValueError:
        print("Error: Invalid time format in work schedule")
        return None

def generate_events(date, activity_goals):
    """Generate events based on activity goals and preferences."""
    print(f"Generating events for {date.strftime('%Y-%m-%d')}")
    
    prompt = f"""
    Generate a detailed list of events for {date.strftime('%Y-%m-%d')} based on the following activity goals and preferences.
    For each activity, create a separate event with its own time slot.
    Format the response as a JSON object with the following structure:
    {{
        "events": [
            {{
                "title": "Event Title",
                "time": "HH:MM",
                "duration": "1h" or "30m",
                "description": "Detailed description with proper spacing and formatting",
                "category": "work", "meal", "workout", "learning", "hobby", "other",
                "priority": "high", "medium", or "low",
                "activity_details": {{
                    "type": "work", "meal_planning", "workout", "learning", "hobby",
                    "preferred_time": "morning", "afternoon", "evening",
                    "notes": string,
                    "sub_activities": [
                        {{
                            "name": string,
                            "duration": "1h" or "30m",
                            "description": string
                        }}
                    ]
                }}
            }}
        ],
        "work_schedule": {{
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "breaks": [
                {{
                    "start": "HH:MM",
                    "end": "HH:MM"
                }}
            ]
        }}
    }}

    Activity Goals:
    {json.dumps(activity_goals, indent=2)}

    Important Instructions:
    1. For each activity in the goals:
       - Create a separate event with its own time slot
       - Space events throughout the day based on preferred times
       - Consider energy levels and time constraints
       - Ensure no overlapping events

    2. For work hours:
       - Create a dedicated work block event
       - Include breaks in the work schedule
       - Ensure other events don't overlap with work hours
       - Consider commute time if applicable

    3. For workout sessions:
       - Create a single event with detailed workout plan in description
       - Include all exercises and sets in the description
       - Schedule around work hours

    4. For learning activities:
       - Create separate events for different topics or tasks
       - Include specific learning objectives in descriptions
       - Schedule around work hours

    5. For meal planning:
       - Create separate events for each meal (breakfast, lunch, dinner)
       - Include meal details and preparation steps
       - Schedule around work hours

    6. For hobbies and free time:
       - Create individual events for each hobby activity
       - Space them throughout the day based on energy levels
       - Include specific details about each activity
       - Schedule around work hours

    7. For family time:
       - Create separate events for different family activities
       - Consider preferred times and durations
       - Schedule around work hours

    Time Guidelines:
    - Use 24-hour format for time (e.g., "14:30")
    - Keep events between 06:00 and 22:00
    - Space events with appropriate breaks
    - Consider energy levels throughout the day
    - Morning (06:00-12:00): High energy activities
    - Afternoon (12:00-17:00): Medium energy activities
    - Evening (17:00-22:00): Low energy activities
    """
    
    try:
        print("Sending request to OpenAI...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an activity planner. Create separate events for each activity, properly spaced throughout the day. Return only valid JSON with properly formatted event descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        print("Received response from OpenAI")
        
        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        
        # Parse and validate the response
        print("Parsing response...")
        parsed_data = json.loads(response_text)
        
        if 'events' not in parsed_data or not parsed_data['events']:
            print("No events generated, creating default event")
            parsed_data = {
                "events": [{
                    "title": "Daily Planning",
                    "time": "09:00",
                    "duration": "1h",
                    "description": "Review your daily goals and schedule",
                    "category": "other",
                    "priority": "medium"
                }]
            }
        
        # Validate and fix each event
        print(f"Processing {len(parsed_data['events'])} events...")
        
        # First, ensure work schedule is properly handled
        work_schedule = validate_work_schedule(parsed_data.get("work_schedule"))
        if work_schedule:
            start_time = work_schedule.get("start_time", "09:00")
            end_time = work_schedule.get("end_time", "17:00")
            
            # Calculate duration in hours
            start = datetime.strptime(start_time, '%H:%M')
            end = datetime.strptime(end_time, '%H:%M')
            duration = (end - start).total_seconds() / 3600
            
            work_event = {
                "title": "Work Hours",
                "time": start_time,
                "duration": f"{duration}h",
                "description": "Work hours",
                "category": "work",
                "priority": "high",
                "activity_details": {
                    "type": "work",
                    "preferred_time": "morning",
                    "notes": "Work hours",
                    "sub_activities": []
                }
            }
            parsed_data["events"].insert(0, work_event)
        
        # Process all events and ensure no overlaps
        processed_events = []
        for event in parsed_data["events"]:
            # Ensure required fields exist
            if 'title' not in event:
                event['title'] = 'Untitled Event'
            if 'time' not in event:
                event['time'] = '09:00'
            if 'duration' not in event:
                event['duration'] = '1h'
            if 'description' not in event:
                event['description'] = ''
            if 'category' not in event or event['category'] not in EVENT_CATEGORIES:
                event['category'] = 'other'
            if 'priority' not in event or event['priority'] not in ['high', 'medium', 'low']:
                event['priority'] = 'medium'
                
            # Validate time format
            try:
                hour, minute = map(int, event['time'].split(':'))
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    event['time'] = '09:00'
            except:
                event['time'] = '09:00'
                
            # Validate duration format
            if not isinstance(event['duration'], str) or not (event['duration'].endswith('h') or event['duration'].endswith('m')):
                event['duration'] = '1h'
            
            # Calculate event start and end times
            start_time = datetime.strptime(event['time'], '%H:%M').time()
            duration_hours = 1
            if event['duration'].endswith('h'):
                duration_hours = float(event['duration'][:-1])
            elif event['duration'].endswith('m'):
                duration_hours = float(event['duration'][:-1]) / 60
            
            # Check for overlaps with existing events
            has_overlap = False
            for processed_event in processed_events:
                processed_start = datetime.strptime(processed_event['time'], '%H:%M').time()
                processed_duration = 1
                if processed_event['duration'].endswith('h'):
                    processed_duration = float(processed_event['duration'][:-1])
                elif processed_event['duration'].endswith('m'):
                    processed_duration = float(processed_event['duration'][:-1]) / 60
                
                if check_event_overlap(start_time, start_time + timedelta(hours=duration_hours),
                                    processed_start, processed_start + timedelta(hours=processed_duration)):
                    has_overlap = True
                    break
            
            if not has_overlap:
                processed_events.append(event)
        
        parsed_data["events"] = processed_events
        
        print(f"Successfully processed {len(processed_events)} events")
        return parsed_data
    except Exception as e:
        print(f"Error generating events: {str(e)}")
        # Return a minimal valid plan
        return {
            "events": [{
                "title": "Daily Planning",
                "time": "09:00",
                "duration": "1h",
                "description": "Review your daily goals and schedule",
                "category": "other",
                "priority": "medium"
            }]
        }

def create_activity_event(date, time_str, summary, description, duration_str, category="other", priority="medium", activity_details=None):
    """Create an event for activities."""
    event = Event()
    
    try:
        # Parse duration with better error handling
        duration_hours = 1  # default
        if duration_str:
            if duration_str.endswith('h'):
                duration_hours = float(duration_str[:-1])
            elif duration_str.endswith('m'):
                duration_hours = float(duration_str[:-1]) / 60
        
        # Set start time
        start_time = datetime.combine(date, datetime.strptime(time_str, '%H:%M').time())
        event.add('dtstart', start_time)
        
        # Set end time
        end_time = start_time + timedelta(hours=duration_hours)
        event.add('dtend', end_time)
        
        # Set summary and description
        event.add('summary', summary)
        event.add('description', description)
        
        # Set category and priority
        event.add('categories', [category])
        event.add('priority', priority)
        
        # Add activity details if provided
        if activity_details:
            event.add('x-activity-details', json.dumps(activity_details))
        
        return event
    except Exception as e:
        print(f"Error creating activity event: {str(e)}")
        return None 