# Install required libraries:
# pip install icalendar openai python-dotenv

import openai
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import os
import re
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

def get_valid_date(prompt):
    while True:
        try:
            date_str = input(prompt)
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")

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
                {"role": "system", "content": "You are a financial information parser. Return only valid JSON, no additional text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        response_text = response.choices[0].message.content.strip()
        response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        return json.loads(response_text)
    except Exception as e:
        print(f"Error parsing budget input: {str(e)}")
        return None

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
        print(f"Error parsing activity goals: {str(e)}")
        return None

def parse_budget_info(budget_info):
    """Parse budget information into a structured format."""
    try:
        # Calculate weekly income
        weekly_income = budget_info['income']['amount']
        if budget_info['income']['frequency'] == 'monthly':
            weekly_income = budget_info['income']['amount'] / 4
        elif budget_info['income']['frequency'] == 'biweekly':
            weekly_income = budget_info['income']['amount'] / 2

        # Calculate weekly expenses
        weekly_expenses = {}
        for expense in budget_info['expenses']:
            amount = expense['amount']
            if budget_info['income']['frequency'] == 'monthly':
                amount = amount / 4
            elif budget_info['income']['frequency'] == 'biweekly':
                amount = amount / 2
            weekly_expenses[expense['name']] = amount

        # Calculate savings goals
        weekly_savings = budget_info['savings_goal']
        if budget_info['income']['frequency'] == 'monthly':
            weekly_savings = budget_info['savings_goal'] / 4
        elif budget_info['income']['frequency'] == 'biweekly':
            weekly_savings = budget_info['savings_goal'] / 2

        # Calculate discretionary spending
        total_weekly_expenses = sum(weekly_expenses.values())
        discretionary_spending = weekly_income - total_weekly_expenses - weekly_savings

        # Calculate progress towards financial goals
        emergency_fund_progress = budget_info['starting_balance'] / budget_info['emergency_fund']
        if budget_info.get('debt_payoff'):
            debt_payoff_progress = budget_info['starting_balance'] / budget_info['debt_payoff']
        else:
            debt_payoff_progress = None

        return {
            'weekly_income': weekly_income,
            'weekly_expenses': weekly_expenses,
            'weekly_savings': weekly_savings,
            'discretionary_spending': discretionary_spending,
            'emergency_fund_progress': emergency_fund_progress,
            'debt_payoff_progress': debt_payoff_progress,
            'investment_goal': budget_info.get('investment_goal'),
            'retirement_contribution': budget_info.get('retirement_contribution')
        }
    except Exception as e:
        print(f"Error parsing budget info: {e}")
        return None

def generate_workout_suggestions(workout_preferences):
    """Generate personalized workout suggestions based on user preferences."""
    try:
        location = workout_preferences['location']
        experience = workout_preferences['experience_level']
        equipment = workout_preferences['available_equipment']

        # Base workout structure
        workout = {
            'warmup': [],
            'main_workout': [],
            'cooldown': []
        }

        # Generate warmup exercises
        workout['warmup'] = [
            {'name': 'Light Cardio', 'duration': '5-10 minutes', 'description': 'Walking, jogging, or cycling'},
            {'name': 'Dynamic Stretches', 'duration': '5 minutes', 'description': 'Arm circles, leg swings, hip circles'}
        ]

        # Generate main workout based on location and experience
        if location == 'gym':
            if experience == 'beginner':
                workout['main_workout'] = [
                    {'name': 'Machine-based exercises', 'sets': '3', 'reps': '12-15', 'description': 'Start with lighter weights and focus on form'},
                    {'name': 'Bodyweight exercises', 'sets': '3', 'reps': '10-12', 'description': 'Push-ups, squats, planks'}
                ]
            elif experience == 'intermediate':
                workout['main_workout'] = [
                    {'name': 'Compound exercises', 'sets': '4', 'reps': '8-12', 'description': 'Squats, deadlifts, bench press'},
                    {'name': 'Isolation exercises', 'sets': '3', 'reps': '10-12', 'description': 'Bicep curls, tricep extensions, lateral raises'}
                ]
            else:  # advanced
                workout['main_workout'] = [
                    {'name': 'Advanced compound movements', 'sets': '5', 'reps': '6-8', 'description': 'Heavy squats, deadlifts, overhead press'},
                    {'name': 'Supersets', 'sets': '4', 'reps': '8-12', 'description': 'Combined exercises for intensity'}
                ]
        else:  # home workouts
            if experience == 'beginner':
                workout['main_workout'] = [
                    {'name': 'Basic bodyweight exercises', 'sets': '3', 'reps': '10-12', 'description': 'Push-ups, squats, planks'},
                    {'name': 'Mobility work', 'sets': '2', 'duration': '30 seconds each', 'description': 'Hip mobility, shoulder mobility'}
                ]
            elif experience == 'intermediate':
                workout['main_workout'] = [
                    {'name': 'Advanced bodyweight exercises', 'sets': '4', 'reps': '8-12', 'description': 'Diamond push-ups, Bulgarian split squats'},
                    {'name': 'Circuit training', 'sets': '3', 'duration': '45 seconds each', 'description': 'High-intensity bodyweight movements'}
                ]
            else:  # advanced
                workout['main_workout'] = [
                    {'name': 'Complex movements', 'sets': '5', 'reps': '6-8', 'description': 'Pistol squats, handstand push-ups'},
                    {'name': 'HIIT intervals', 'sets': '4', 'duration': '30 seconds work, 15 seconds rest', 'description': 'High-intensity interval training'}
                ]

        # Add equipment-specific exercises if available
        if equipment:
            equipment_exercises = []
            if 'dumbbells' in equipment:
                equipment_exercises.extend([
                    {'name': 'Dumbbell exercises', 'sets': '3-4', 'reps': '10-12', 'description': 'Rows, presses, curls'}
                ])
            if 'resistance_bands' in equipment:
                equipment_exercises.extend([
                    {'name': 'Resistance band exercises', 'sets': '3-4', 'reps': '12-15', 'description': 'Band pull-aparts, band squats'}
                ])
            if 'pull_up_bar' in equipment:
                equipment_exercises.extend([
                    {'name': 'Pull-up variations', 'sets': '3-4', 'reps': '6-10', 'description': 'Pull-ups, chin-ups, hanging leg raises'}
                ])
            if 'yoga_mat' in equipment:
                equipment_exercises.extend([
                    {'name': 'Core work', 'sets': '3', 'duration': '45 seconds each', 'description': 'Planks, crunches, mountain climbers'}
                ])
            workout['main_workout'].extend(equipment_exercises)

        # Generate cooldown exercises
        workout['cooldown'] = [
            {'name': 'Static stretching', 'duration': '5-10 minutes', 'description': 'Focus on major muscle groups used in the workout'},
            {'name': 'Deep breathing', 'duration': '2-3 minutes', 'description': 'Relaxation and recovery'}
        ]

        return workout
    except Exception as e:
        print(f"Error generating workout suggestions: {e}")
        return None

def is_work_time(date, work_schedule):
    """Check if a given date and time falls within work hours."""
    if not work_schedule:
        return False
        
    day_name = date.strftime('%A').lower()
    if day_name not in work_schedule['days']:
        return False
        
    work_start = datetime.strptime(work_schedule['start_time'], '%H:%M').time()
    work_end = datetime.strptime(work_schedule['end_time'], '%H:%M').time()
    event_time = date.time()
    
    return work_start <= event_time <= work_end

def find_available_time(date, duration_hours, work_schedule):
    """Find an available time slot that doesn't conflict with work hours."""
    # Try morning slot (7 AM)
    morning_time = date.replace(hour=7, minute=0)
    if not is_work_time(morning_time, work_schedule) and not is_work_time(morning_time + timedelta(hours=duration_hours), work_schedule):
        return morning_time
        
    # Try lunch slot (12 PM)
    lunch_time = date.replace(hour=12, minute=0)
    if not is_work_time(lunch_time, work_schedule) and not is_work_time(lunch_time + timedelta(hours=duration_hours), work_schedule):
        return lunch_time
        
    # Try evening slot (18 PM)
    evening_time = date.replace(hour=18, minute=0)
    if not is_work_time(evening_time, work_schedule) and not is_work_time(evening_time + timedelta(hours=duration_hours), work_schedule):
        return evening_time
        
    # If no slots available, return None
    return None

def generate_daily_plan(budget_info, activity_goals, date):
    """Generate a detailed daily plan with financial analysis and workout suggestions."""
    try:
        # Parse budget information
        budget_analysis = parse_budget_info(budget_info)
        if not budget_analysis:
            print("Failed to parse budget information")
            return None

        # Generate workout suggestions
        workout_plan = generate_workout_suggestions(activity_goals.get('workout_preferences', {}))
        if not workout_plan:
            print("Failed to generate workout suggestions")
            return None

        # Create daily plan
        daily_plan = {
            'date': date,
            'work_schedule': budget_info.get('work_schedule'),
            'financial_analysis': {
                'daily_budget': budget_analysis['weekly_income'] / 7,
                'daily_expenses': sum(budget_analysis['weekly_expenses'].values()) / 7,
                'daily_savings': budget_analysis['weekly_savings'] / 7,
                'discretionary_spending': budget_analysis['discretionary_spending'] / 7,
                'progress_towards_goals': {
                    'emergency_fund': budget_analysis['emergency_fund_progress'],
                    'debt_payoff': budget_analysis['debt_payoff_progress']
                }
            },
            'workout_plan': workout_plan,
            'activity_schedule': []
        }

        # Add activities based on goals
        goals = activity_goals.get('goals', [])
        for goal in goals:
            try:
                # Skip if goal is missing required fields
                if not all(key in goal for key in ['title', 'duration']):
                    print(f"Skipping goal due to missing required fields: {goal}")
                    continue

                # Determine if this goal should be added today
                should_add = False
                if goal.get('frequency') == 'daily':
                    should_add = True
                elif goal.get('frequency') == 'weekly' and date.weekday() == 0:  # Monday
                    should_add = True
                elif goal.get('frequency') == 'biweekly' and date.weekday() == 0 and date.day <= 7:  # First Monday of the month
                    should_add = True

                if should_add:
                    daily_plan['activity_schedule'].append({
                        'title': goal['title'],
                        'duration': goal['duration']
                    })
            except Exception as e:
                print(f"Error processing goal: {str(e)}")
                continue

        return daily_plan
    except Exception as e:
        print(f"Error generating daily plan: {str(e)}")
        return None

def create_event(date, time_str, summary, description, duration_str):
    event = Event()
    
    # Parse duration
    duration_hours = 1  # default
    if duration_str.endswith('h'):
        duration_hours = float(duration_str[:-1])
    elif duration_str.endswith('m'):
        duration_hours = float(duration_str[:-1]) / 60
    
    # Parse time
    hour, minute = map(int, time_str.split(':'))
    event_start = date.replace(hour=hour, minute=minute)
    
    event.add('summary', summary)
    event.add('dtstart', event_start)
    event.add('dtend', event_start + timedelta(hours=duration_hours))
    event.add('description', description)
    cal.add_component(event)

def save_progress(current_payday, current_balance, pay_period_counter, data):
    progress = {
        'current_payday': current_payday.strftime('%Y-%m-%d'),
        'current_balance': current_balance,
        'pay_period_counter': pay_period_counter,
        'data': data
    }
    with open('budget_progress.json', 'w') as f:
        json.dump(progress, f)

def load_progress():
    if Path('budget_progress.json').exists():
        with open('budget_progress.json', 'r') as f:
            return json.load(f)
    return None

# GPT Helper to format descriptions
def gpt_format_details(financial_info):
    prompt = f"""
    Generate a clear and insightful financial summary for a user's payday event based on the following details:
    {financial_info}
    Provide a friendly assessment of their financial balance and offer advice on staying on track with savings.
    Keep the response concise and focused on key points.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Using 3.5 for faster response
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,  # Reduced token count
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Warning: Error generating financial advice: {str(e)}")
        return "Unable to generate financial advice at this time."

def create_calendar_events(plans):
    """Create calendar events with detailed descriptions."""
    try:
        calendar = Calendar()
        calendar.add('prodid', '-//AI Life & Budget Planner//EN')
        calendar.add('version', '2.0')
        
        for plan in plans:
            date = plan["date"]
            work_schedule = plan.get("work_schedule", None)
            
            # Add work event if it's a work day
            if work_schedule and date.strftime('%A').lower() in work_schedule['days']:
                work_start = datetime.strptime(work_schedule['start_time'], '%H:%M').time()
                work_end = datetime.strptime(work_schedule['end_time'], '%H:%M').time()
                
                event = Event()
                event.add('summary', 'Work')
                event.add('dtstart', date.replace(hour=work_start.hour, minute=work_start.minute))
                event.add('dtend', date.replace(hour=work_end.hour, minute=work_end.minute))
                event.add('description', 'Work hours')
                calendar.add_component(event)
            
            # Add financial summary event
            financial_time = find_available_time(date, 0.5, work_schedule)  # 30 minutes
            if financial_time:
                financial_summary = f"""
Financial Summary for {date.strftime("%B %d, %Y")}:
• Daily Budget: ${plan["financial_analysis"]["daily_budget"]:.2f}
• Daily Expenses: ${plan["financial_analysis"]["daily_expenses"]:.2f}
• Daily Savings: ${plan["financial_analysis"]["daily_savings"]:.2f}
• Discretionary Spending: ${plan["financial_analysis"]["discretionary_spending"]:.2f}

Progress Towards Goals:
• Emergency Fund: {plan["financial_analysis"]["progress_towards_goals"]["emergency_fund"]*100:.1f}%
"""
                if plan["financial_analysis"]["progress_towards_goals"]["debt_payoff"]:
                    financial_summary += f"• Debt Payoff: {plan['financial_analysis']['progress_towards_goals']['debt_payoff']*100:.1f}%\n"

                event = Event()
                event.add('summary', f"Financial Summary - {date.strftime('%B %d')}")
                event.add('dtstart', financial_time)
                event.add('dtend', financial_time + timedelta(minutes=30))
                event.add('description', financial_summary)
                calendar.add_component(event)

            # Add workout event
            workout_time = find_available_time(date, 1, work_schedule)  # 1 hour
            if workout_time:
                workout = plan["workout_plan"]
                workout_description = f"""
Workout Plan for {date.strftime("%B %d, %Y")}:

Warmup:
{chr(10).join(f"• {ex['name']}: {ex['duration']} - {ex['description']}" for ex in workout["warmup"])}

Main Workout:
{chr(10).join(f"• {ex['name']}: {ex.get('sets', '')} {ex.get('reps', '')} {ex.get('duration', '')} - {ex['description']}" for ex in workout["main_workout"])}

Cooldown:
{chr(10).join(f"• {ex['name']}: {ex['duration']} - {ex['description']}" for ex in workout["cooldown"])}
"""
                event = Event()
                event.add('summary', f"Workout - {date.strftime('%B %d')}")
                event.add('dtstart', workout_time)
                event.add('dtend', workout_time + timedelta(hours=1))
                event.add('description', workout_description)
                calendar.add_component(event)

            # Add other activities
            for activity in plan["activity_schedule"]:
                activity_time = find_available_time(date, 1, work_schedule)  # Default 1 hour
                if activity_time:
                    event = Event()
                    event.add('summary', activity["title"])
                    event.add('dtstart', activity_time)
                    event.add('dtend', activity_time + timedelta(hours=1))
                    event.add('description', f"Duration: {activity['duration']} minutes")
                    calendar.add_component(event)

        return calendar
    except Exception as e:
        print(f"Error creating calendar events: {e}")
        return None

def generate_plan(start_date, end_date, budget_info, activity_goals):
    """Generate a complete plan for the specified date range."""
    try:
        plans = []
        current_date = start_date

        while current_date <= end_date:
            daily_plan = generate_daily_plan(budget_info, activity_goals, current_date)
            if daily_plan:
                plans.append(daily_plan)
            current_date += timedelta(days=1)

        if not plans:
            print("No plans were generated")
            return None

        calendar = create_calendar_events(plans)
        if not calendar:
            print("Failed to create calendar events")
            return None

        # Save the calendar to a file
        with open('static/calendar.ics', 'wb') as f:
            f.write(calendar.to_ical())
        
        print("Calendar file generated successfully")
        return True

    except Exception as e:
        print(f"Error generating plan: {str(e)}")
        return None

def main():
    try:
        # Example usage
        budget_info = {
            "starting_balance": 5000,
            "income": {
                "amount": 4000,
                "frequency": "monthly"
            },
            "savings_goal": 1000,
            "emergency_fund": 10000,
            "expenses": [
                {"name": "Rent", "amount": 1500},
                {"name": "Utilities", "amount": 200},
                {"name": "Groceries", "amount": 400}
            ]
        }

        activity_goals = {
            "goals": [
                {
                    "type": "workout",
                    "frequency": "daily",
                    "duration": 60,
                    "title": "Morning Workout"
                }
            ],
            "workout_preferences": {
                "location": "gym",
                "experience_level": "intermediate",
                "available_equipment": ["dumbbells", "resistance_bands"]
            }
        }

        start_date = datetime.now()
        end_date = start_date + timedelta(days=14)

        success = generate_plan(start_date, end_date, budget_info, activity_goals)
        if success:
            print("Plan generated successfully!")
            print("Calendar file saved to static/calendar.ics")
        else:
            print("Failed to generate plan.")
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()
