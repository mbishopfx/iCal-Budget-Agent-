from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import openai
import os
from dotenv import load_dotenv
from icalendar import Calendar, Event
import json
from pathlib import Path
import re
from icalagentGPT import generate_plan

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Initialize calendar
cal = Calendar()
cal.add('prodid', '-//Enhanced Life & Budget Planner//mxm.dk//')
cal.add('version', '2.0')

# Maximum date range (6 months)
MAX_DATE_RANGE = timedelta(days=180)

# Default time slots for different types of activities
TIME_SLOTS = {
    "morning": {"start": "07:00", "end": "12:00"},
    "afternoon": {"start": "12:00", "end": "17:00"},
    "evening": {"start": "17:00", "end": "22:00"}
}

# Event categories and their colors
EVENT_CATEGORIES = {
    "financial": "#4CAF50",  # Green
    "meal": "#FF9800",       # Orange
    "workout": "#2196F3",    # Blue
    "learning": "#9C27B0",   # Purple
    "other": "#607D8B"       # Grey
}

def parse_budget_input(user_input):
    prompt = f"""
    You are a financial information parser. Parse the following user input and extract key financial information.
    Return ONLY a valid JSON object with the following structure, no additional text:
    {{
        "starting_balance": float,
        "income": {{
            "amount": float,
            "frequency": "biweekly" or "monthly",
            "next_date": "YYYY-MM-DD"
        }},
        "bills": [
            {{
                "name": string,
                "amount": float,
                "due_date": "YYYY-MM-DD",
                "frequency": "monthly" or "biweekly"
            }}
        ],
        "savings_goal": float,
        "additional_income": [
            {{
                "source": string,
                "amount": float,
                "frequency": "monthly" or "biweekly",
                "next_date": "YYYY-MM-DD"
            }}
        ]
    }}

    User input: {user_input}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial information parser. Return only valid JSON, no additional text. Make sure to include all required fields with appropriate default values if not provided."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        response_text = response.choices[0].message.content.strip()
        # Remove any markdown code block markers
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        # Parse the JSON response
        parsed_data = json.loads(response_text)
        
        # Ensure all required fields are present with default values if needed
        if 'starting_balance' not in parsed_data:
            parsed_data['starting_balance'] = 0.0
        if 'income' not in parsed_data:
            parsed_data['income'] = {
                'amount': 0.0,
                'frequency': 'monthly',
                'next_date': datetime.now().strftime('%Y-%m-%d')
            }
        if 'bills' not in parsed_data:
            parsed_data['bills'] = []
        if 'savings_goal' not in parsed_data:
            parsed_data['savings_goal'] = 0.0
        if 'additional_income' not in parsed_data:
            parsed_data['additional_income'] = []
            
        return parsed_data
    except Exception as e:
        print(f"Error parsing budget input: {str(e)}")
        return {"error": str(e)}

def parse_activity_goals(user_input):
    prompt = f"""
    You are an activity goals parser. Parse the following user input and extract their goals and preferences.
    Return ONLY a valid JSON object with the following structure, no additional text:
    {{
        "goals": [
            {{
                "type": "meal_planning", "workout", "learning", "hobby", "other",
                "frequency": "daily", "weekly", "specific_days",
                "days": ["monday", "tuesday", etc.],
                "details": string,
                "duration": "1h", "30m", etc.,
                "preferred_time": "morning", "afternoon", or "evening"
            }}
        ],
        "preferences": {{
            "meal_times": ["breakfast", "lunch", "dinner"],
            "workout_times": ["morning", "afternoon", "evening"],
            "other_preferences": string
        }}
    }}

    User input: {user_input}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an activity goals parser. Return only valid JSON, no additional text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        return json.loads(response_text)
    except Exception as e:
        return {"error": str(e)}

def generate_daily_plan(date, budget_info, activity_goals):
    prompt = f"""
    Generate a detailed daily plan for {date.strftime('%Y-%m-%d')} based on the following information.
    Format the response as a JSON object with the following structure:
    {{
        "events": [
            {{
                "title": "Event Title",
                "time": "HH:MM",
                "duration": "1h" or "30m",
                "description": "Detailed description with proper spacing and formatting",
                "category": "financial", "meal", "workout", "learning", "other",
                "priority": "high", "medium", or "low"
            }}
        ]
    }}

    Budget Information:
    {json.dumps(budget_info, indent=2)}

    Activity Goals:
    {json.dumps(activity_goals, indent=2)}

    Include events for:
    1. Financial tasks and reminders (bills due, savings goals)
    2. Activities and goals for the day
    3. Meal planning if applicable
    4. Workout plan if applicable
    5. Learning activities if applicable

    Important:
    - Use 24-hour format for time (e.g., "14:30")
    - Keep descriptions clear and concise
    - Ensure all events have valid times between 06:00 and 22:00
    - Space events appropriately throughout the day
    - Include specific details in descriptions
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a daily planner. Return only valid JSON with properly formatted event descriptions. Ensure all events have valid times and durations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        
        # Parse and validate the response
        parsed_data = json.loads(response_text)
        
        if 'events' not in parsed_data or not parsed_data['events']:
            # Create a default event if none were generated
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
        for event in parsed_data['events']:
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
        
        return parsed_data
    except Exception as e:
        print(f"Error generating daily plan: {str(e)}")
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

def create_event(date, time_str, summary, description, duration_str, category="other", priority="medium"):
    event = Event()
    
    try:
        # Parse duration with better error handling
        duration_hours = 1  # default
        if duration_str:
            if duration_str.endswith('h'):
                duration_hours = float(duration_str[:-1])
            elif duration_str.endswith('m'):
                duration_hours = float(duration_str[:-1]) / 60
        
        # Parse time with better error handling
        try:
            hour, minute = map(int, time_str.split(':'))
        except (ValueError, AttributeError):
            # Default to 9 AM if time parsing fails
            hour, minute = 9, 0
            
        event_start = date.replace(hour=hour, minute=minute)
        
        event.add('summary', summary or 'Untitled Event')
        event.add('dtstart', event_start)
        event.add('dtend', event_start + timedelta(hours=duration_hours))
        event.add('description', description or '')
        
        # Ensure category is valid
        if category not in EVENT_CATEGORIES:
            category = "other"
        event.add('categories', category)
        
        # Add color if supported by the calendar
        try:
            event.add('color', EVENT_CATEGORIES.get(category, "#607D8B"))
        except:
            pass  # Skip if color is not supported
            
        # Add priority if supported
        try:
            if priority in ['high', 'medium', 'low']:
                event.add('priority', {'high': 1, 'medium': 5, 'low': 9}[priority])
        except:
            pass  # Skip if priority is not supported
            
        cal.add_component(event)
        return True
    except Exception as e:
        print(f"Error creating event: {str(e)}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/planner')
def planner():
    return render_template('planner.html')

@app.route('/static/calendar.ics')
def download_calendar():
    try:
        return send_file(
            'static/calendar.ics',
            mimetype='text/calendar',
            as_attachment=True,
            download_name='calendar.ics'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404

@app.route('/api/parse_budget', methods=['POST'])
def parse_budget():
    try:
        data = request.json
        user_input = data.get('input', '')
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'No input provided'
            })
        
        result = parse_budget_input(user_input)
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            })
        
        return jsonify({
            'success': True,
            'budget_info': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/parse_activities', methods=['POST'])
def parse_activities():
    try:
        data = request.json
        user_input = data.get('input', '')
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'No input provided'
            })
        
        result = parse_activity_goals(user_input)
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            })
        
        return jsonify({
            'success': True,
            'activity_goals': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/generate_plan', methods=['POST'])
def create_plan():
    try:
        data = request.json
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        budget_info = data['budget_info']
        activity_goals = data['activity_goals']

        success = generate_plan(start_date, end_date, budget_info, activity_goals)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to generate plan'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True) 