from datetime import datetime, timedelta
import openai
import json
from icalendar import Calendar, Event
import re

def parse_brain_dump(user_input):
    """Parse unstructured user input into structured calendar events."""
    prompt = f"""
    You are a calendar planning assistant. Analyze the following user input and create a detailed calendar plan.
    Return ONLY a valid JSON object with the following structure, no additional text:
    {{
        "events": [
            {{
                "title": "Event Title",
                "time": "HH:MM",
                "duration": "1h" or "30m",
                "description": "Detailed description",
                "category": "work", "meal", "workout", "learning", "hobby", "other",
                "priority": "high", "medium", "low",
                "activity_details": {{
                    "type": string,
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

    User input: {user_input}

    Important Instructions:
    1. Identify all activities mentioned in the input
    2. Create appropriate time slots for each activity
    3. Ensure work hours are properly blocked out
    4. Space events throughout the day
    5. Consider energy levels and time constraints
    6. Ensure no overlapping events
    7. Include detailed descriptions for each event
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a calendar planning assistant. Create a detailed schedule from unstructured input. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        parsed_data = json.loads(response_text)
        
        return parsed_data
    except Exception as e:
        print(f"Error parsing brain dump: {str(e)}")
        return {"error": str(e)}

def create_calendar_from_brain_dump(user_input, start_date, end_date):
    """Create a calendar from brain dump input."""
    # Validate date range
    if end_date < start_date:
        print("Error: End date must be after start date")
        return None
        
    if (end_date - start_date).days > 180:  # Maximum 6 months
        print("Error: Date range cannot exceed 6 months")
        return None
    
    cal = Calendar()
    cal.add('prodid', '-//Brain Dump Calendar Generator//mxm.dk//')
    cal.add('version', '2.0')
    
    # Parse the brain dump input
    parsed_data = parse_brain_dump(user_input)
    
    if "error" in parsed_data:
        print(f"Error parsing brain dump: {parsed_data['error']}")
        return None
    
    if not parsed_data.get("events"):
        print("Error: No events generated from input")
        return None
    
    # Generate events for each day in the date range
    current_date = start_date
    while current_date <= end_date:
        # Create events for the current day
        processed_events = []
        for event in parsed_data.get("events", []):
            try:
                # Create the event
                event_obj = Event()
                event_obj.add('summary', event.get('title', 'Untitled Event'))
                event_obj.add('description', event.get('description', ''))
                
                # Set start time
                time_str = event.get('time', '09:00')
                start_time = datetime.combine(current_date, datetime.strptime(time_str, '%H:%M').time())
                
                # Set duration
                duration_str = event.get('duration', '1h')
                duration_hours = 1
                if duration_str.endswith('h'):
                    duration_hours = float(duration_str[:-1])
                elif duration_str.endswith('m'):
                    duration_hours = float(duration_str[:-1]) / 60
                
                end_time = start_time + timedelta(hours=duration_hours)
                
                # Check for overlaps with existing events
                has_overlap = False
                for processed_event in processed_events:
                    if check_event_overlap(start_time, end_time,
                                        processed_event['start'], processed_event['end']):
                        has_overlap = True
                        break
                
                if not has_overlap:
                    event_obj.add('dtstart', start_time)
                    event_obj.add('dtend', end_time)
                    
                    # Add category and priority
                    event_obj.add('categories', [event.get('category', 'other')])
                    event_obj.add('priority', event.get('priority', 'medium'))
                    
                    # Add to calendar
                    cal.add_component(event_obj)
                    
                    # Add to processed events for overlap checking
                    processed_events.append({
                        'start': start_time,
                        'end': end_time
                    })
            except Exception as e:
                print(f"Error creating event: {str(e)}")
                continue
        
        current_date += timedelta(days=1)
    
    return cal 