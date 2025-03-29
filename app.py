from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import openai
import os
from dotenv import load_dotenv
from icalendar import Calendar, Event
import json
from pathlib import Path
import re
from event_generator import generate_events, create_activity_event
from icalagentGPT import generate_plan
from brain_dump import create_calendar_from_brain_dump

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
    "hobby": "#E91E63",      # Pink
    "work": "#FF5722",       # Deep Orange
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
            "next_date": "YYYY-MM-DD",
            "source": string
        }},
        "bills": [
            {{
                "name": string,
                "amount": float,
                "due_date": "YYYY-MM-DD",
                "frequency": "monthly" or "biweekly",
                "category": "housing", "transportation", "utilities", "insurance", "other"
            }}
        ],
        "savings_goal": float,
        "emergency_fund": float,
        "additional_income": [
            {{
                "source": string,
                "amount": float,
                "frequency": "monthly" or "biweekly",
                "next_date": "YYYY-MM-DD",
                "category": "child_support", "freelance", "investments", "other"
            }}
        ],
        "expenses": [
            {{
                "name": string,
                "amount": float,
                "frequency": "monthly" or "biweekly",
                "category": "groceries", "entertainment", "shopping", "other"
            }}
        ],
        "financial_goals": [
            {{
                "name": string,
                "target_amount": float,
                "target_date": "YYYY-MM-DD",
                "priority": "high", "medium", "low"
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
                'next_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'primary'
            }
        if 'bills' not in parsed_data:
            parsed_data['bills'] = []
        if 'savings_goal' not in parsed_data:
            parsed_data['savings_goal'] = 0.0
        if 'emergency_fund' not in parsed_data:
            parsed_data['emergency_fund'] = 0.0
        if 'additional_income' not in parsed_data:
            parsed_data['additional_income'] = []
        if 'expenses' not in parsed_data:
            parsed_data['expenses'] = []
        if 'financial_goals' not in parsed_data:
            parsed_data['financial_goals'] = []
            
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
                "preferred_time": "morning", "afternoon", or "evening",
                "category": "health", "education", "family", "personal", "work",
                "priority": "high", "medium", "low",
                "dependencies": ["other_goal_name"],
                "notes": string
            }}
        ],
        "preferences": {{
            "meal_times": ["breakfast", "lunch", "dinner"],
            "workout_times": ["morning", "afternoon", "evening"],
            "other_preferences": string,
            "free_time_activities": [
                {{
                    "name": string,
                    "description": string,
                    "frequency": "daily", "weekly", "occasional",
                    "preferred_time": "morning", "afternoon", "evening",
                    "duration": "1h", "30m", etc.
                }}
            ],
            "constraints": [
                {{
                    "type": "time", "energy", "resources",
                    "description": string
                }}
            ]
        }}
    }}

    User input: {user_input}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an activity goals parser. Return only valid JSON, no additional text. Make sure to include all required fields with appropriate default values if not provided."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        parsed_data = json.loads(response_text)
        
        # Ensure all required fields are present with default values if needed
        if 'goals' not in parsed_data:
            parsed_data['goals'] = []
        if 'preferences' not in parsed_data:
            parsed_data['preferences'] = {
                'meal_times': ['breakfast', 'lunch', 'dinner'],
                'workout_times': ['morning', 'afternoon', 'evening'],
                'other_preferences': '',
                'free_time_activities': [],
                'constraints': []
            }
            
        # Validate and fix each goal
        for goal in parsed_data['goals']:
            if 'type' not in goal:
                goal['type'] = 'other'
            if 'frequency' not in goal:
                goal['frequency'] = 'daily'
            if 'days' not in goal:
                goal['days'] = []
            if 'details' not in goal:
                goal['details'] = ''
            if 'duration' not in goal:
                goal['duration'] = '1h'
            if 'preferred_time' not in goal:
                goal['preferred_time'] = 'morning'
            if 'category' not in goal:
                goal['category'] = 'personal'
            if 'priority' not in goal:
                goal['priority'] = 'medium'
            if 'dependencies' not in goal:
                goal['dependencies'] = []
            if 'notes' not in goal:
                goal['notes'] = ''
                
        return parsed_data
    except Exception as e:
        print(f"Error parsing activity goals: {str(e)}")
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
                "category": "financial", "meal", "workout", "learning", "hobby", "other",
                "priority": "high", "medium", or "low",
                "financial_details": {{
                    "type": "bill_payment", "income", "expense", "savings", "budget_review",
                    "amount": float,
                    "due_date": "YYYY-MM-DD",
                    "account_balance": float,
                    "notes": string
                }}
            }}
        ],
        "financial_summary": {{
            "expected_balance": float,
            "upcoming_bills": [
                {{
                    "name": string,
                    "amount": float,
                    "due_date": "YYYY-MM-DD"
                }}
            ],
            "upcoming_income": [
                {{
                    "source": string,
                    "amount": float,
                    "date": "YYYY-MM-DD"
                }}
            ],
            "savings_progress": {{
                "current": float,
                "goal": float,
                "percentage": float
            }}
        }}
    }}

    Budget Information:
    {json.dumps(budget_info, indent=2)}

    Activity Goals:
    {json.dumps(activity_goals, indent=2)}

    Include events for:
    1. Financial tasks and reminders:
       - Bill payments due
       - Income expected
       - Budget review and planning
       - Savings goal tracking
       - Account balance monitoring
    2. Activities and goals for the day:
       - Workout sessions
       - Learning activities
       - Hobbies and free time activities
       - Family time
    3. Meal planning and preparation
    4. Personal development activities

    Important:
    - Use 24-hour format for time (e.g., "14:30")
    - Keep descriptions clear and concise
    - Ensure all events have valid times between 06:00 and 22:00
    - Space events appropriately throughout the day
    - Include specific details in descriptions
    - Prioritize financial tasks based on due dates
    - Consider energy levels and time constraints
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
                }],
                "financial_summary": {
                    "expected_balance": budget_info.get('starting_balance', 0),
                    "upcoming_bills": [],
                    "upcoming_income": [],
                    "savings_progress": {
                        "current": 0,
                        "goal": budget_info.get('savings_goal', 0),
                        "percentage": 0
                    }
                }
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
                
            # Add financial details if applicable
            if event['category'] == 'financial' and 'financial_details' not in event:
                event['financial_details'] = {
                    'type': 'budget_review',
                    'amount': 0,
                    'due_date': date.strftime('%Y-%m-%d'),
                    'account_balance': budget_info.get('starting_balance', 0),
                    'notes': 'Daily financial review'
                }
        
        # Ensure financial summary exists
        if 'financial_summary' not in parsed_data:
            parsed_data['financial_summary'] = {
                'expected_balance': budget_info.get('starting_balance', 0),
                'upcoming_bills': [],
                'upcoming_income': [],
                'savings_progress': {
                    'current': 0,
                    'goal': budget_info.get('savings_goal', 0),
                    'percentage': 0
                }
            }
        
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
            }],
            "financial_summary": {
                "expected_balance": budget_info.get('starting_balance', 0),
                "upcoming_bills": [],
                "upcoming_income": [],
                "savings_progress": {
                    "current": 0,
                    "goal": budget_info.get('savings_goal', 0),
                    "percentage": 0
                }
            }
        }

def create_event(date, time_str, summary, description, duration_str, category="other", priority="medium", financial_details=None):
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
        
        # Enhanced description with financial details if applicable
        full_description = description or ''
        if financial_details:
            financial_info = []
            if financial_details.get('type') == 'bill_payment':
                financial_info.append(f"Bill Payment: ${financial_details.get('amount', 0):.2f}")
                financial_info.append(f"Due Date: {financial_details.get('due_date', '')}")
            elif financial_details.get('type') == 'income':
                financial_info.append(f"Income: ${financial_details.get('amount', 0):.2f}")
                financial_info.append(f"Date: {financial_details.get('due_date', '')}")
            elif financial_details.get('type') == 'savings':
                financial_info.append(f"Savings Goal: ${financial_details.get('amount', 0):.2f}")
                financial_info.append(f"Current Balance: ${financial_details.get('account_balance', 0):.2f}")
            
            if financial_details.get('notes'):
                financial_info.append(f"Notes: {financial_details['notes']}")
            
            if financial_info:
                full_description += "\n\nFinancial Details:\n" + "\n".join(financial_info)
        
        event.add('description', full_description)
        
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
            
        # Add financial details as custom properties if supported
        if financial_details:
            try:
                event.add('X-FINANCIAL-TYPE', financial_details.get('type', ''))
                event.add('X-FINANCIAL-AMOUNT', str(financial_details.get('amount', 0)))
                event.add('X-FINANCIAL-DUE-DATE', financial_details.get('due_date', ''))
                event.add('X-FINANCIAL-BALANCE', str(financial_details.get('account_balance', 0)))
            except:
                pass  # Skip if custom properties are not supported
            
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

@app.route('/brain-dump')
def brain_dump():
    return render_template('brain_dump.html')

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

@app.route('/api/brain_dump', methods=['POST'])
def process_brain_dump():
    data = request.get_json()
    user_input = data.get('input', '')
    start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
    
    # Generate calendar from brain dump
    cal = create_calendar_from_brain_dump(user_input, start_date, end_date)
    
    if cal:
        # Save calendar file
        with open('static/calendar.ics', 'wb') as f:
            f.write(cal.to_ical())
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Failed to generate calendar"})

def generate_plan(start_date, end_date, budget_info, activity_goals):
    """Generate a complete plan for the specified date range."""
    try:
        print(f"\nStarting plan generation from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        total_days = (end_date - start_date).days + 1
        print(f"Total days to process: {total_days}")
        
        current_date = start_date
        day_count = 0
        
        while current_date <= end_date:
            day_count += 1
            print(f"\nProcessing day {day_count}/{total_days}: {current_date.strftime('%Y-%m-%d')}")
            
            # Generate financial events
            print("Generating financial events...")
            financial_plan = generate_daily_plan(current_date, budget_info, activity_goals)
            if financial_plan and 'events' in financial_plan:
                financial_count = 0
                for event in financial_plan['events']:
                    if event['category'] == 'financial':
                        create_event(
                            current_date,
                            event['time'],
                            event['title'],
                            event['description'],
                            event['duration'],
                            event['category'],
                            event['priority'],
                            event.get('financial_details')
                        )
                        financial_count += 1
                print(f"Created {financial_count} financial events")
            
            # Generate activity events
            print("Generating activity events...")
            activity_plan = generate_events(current_date, activity_goals)
            if activity_plan and 'events' in activity_plan:
                activity_count = 0
                for event in activity_plan['events']:
                    if event['category'] != 'financial':
                        activity_event = create_activity_event(
                            current_date,
                            event['time'],
                            event['title'],
                            event['description'],
                            event['duration'],
                            event['category'],
                            event['priority'],
                            event.get('activity_details')
                        )
                        if activity_event:
                            cal.add_component(activity_event)
                            activity_count += 1
                print(f"Created {activity_count} activity events")
            
            current_date += timedelta(days=1)
        
        # Save the calendar to a file
        print("\nSaving calendar to file...")
        with open('static/calendar.ics', 'wb') as f:
            f.write(cal.to_ical())
        
        print(f"\nCalendar generation completed successfully!")
        print(f"Total days processed: {day_count}")
        return True
    except Exception as e:
        print(f"\nError generating plan: {str(e)}")
        return False

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True) 