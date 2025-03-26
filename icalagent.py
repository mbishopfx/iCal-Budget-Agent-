# Install required library:
# pip install icalendar

from icalendar import Calendar, Event
from datetime import datetime, timedelta

# Define starting payday and end date
start_payday = datetime(2025, 3, 21)
end_date = datetime(2026, 3, 21)

# Initialize calendar
cal = Calendar()
cal.add('prodid', '-//Budget Plan//mxm.dk//')
cal.add('version', '2.0')

# Constants
paycheck_amount = 1200
child_support_day = 13
child_support_amount = 200

# Function to create event
def create_event(date, summary, description):
    event = Event()
    event.add('summary', summary)
    event.add('dtstart', date)
    event.add('dtend', date + timedelta(hours=1))
    event.add('description', description)
    cal.add_component(event)

# Generate events
current_payday = start_payday
pay_period_counter = 1

while current_payday <= end_date:
    month = current_payday.month

    # Income
    income = paycheck_amount
    description = f'Income: ${income}\n'

    # Child Support Check
    cs_date = current_payday.replace(day=child_support_day)
    if current_payday <= cs_date < current_payday + timedelta(days=14):
        income += child_support_amount
        description += f'Child Support: ${child_support_amount}\n'

    # Bills
    bills = ""
    if 1 <= current_payday.day <= 7 or (month == 5 and pay_period_counter == 3):
        bills += 'Rent: $1175\n'
        spending = income - 1175
    else:
        bills += 'Car Payment: $530\nCWEP (max): $325\n'
        spending = income - 855

    description += f'Bills:\n{bills}'

    # Savings
    savings_target = max(0, spending - 200)  # aiming to save at least $200 each period
    description += f'Savings Target: ${savings_target}\n'

    # Weekly Allowance
    weekly_allowance = (spending - savings_target) // 2
    description += f'Weekly Allowance: ${weekly_allowance} per week\n'

    # Special case for 3-paycheck months
    summary = f'Payday #{pay_period_counter}'
    if month == 5 and pay_period_counter == 3:
        summary += ' (Extra Check - Savings Boost!)'
        description += '\nBonus paycheck: Save majority!'

    create_event(current_payday, summary, description)

    current_payday += timedelta(days=14)

    # Reset monthly counter
    if current_payday.month != month:
        pay_period_counter = 1
    else:
        pay_period_counter += 1

# Save to file
with open('budget_plan.ics', 'wb') as f:
    f.write(cal.to_ical())

print('budget_plan.ics has been created successfully!')
