document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const welcomeScreen = document.getElementById('welcomeScreen');
    const chatContainer = document.getElementById('chatContainer');
    const messages = document.getElementById('messages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const newPlanBtn = document.getElementById('newPlanBtn');
    const startPlanningBtn = document.getElementById('startPlanningBtn');
    const dateModal = document.getElementById('dateModal');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const confirmDateBtn = document.getElementById('confirmDateBtn');
    const cancelDateBtn = document.getElementById('cancelDateBtn');
    const planHistory = document.getElementById('planHistory');

    let currentStep = 'financial'; // 'financial' or 'activities'
    let financialInfo = null;
    let activityGoals = null;

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // Start new plan
    newPlanBtn.addEventListener('click', () => {
        welcomeScreen.style.display = 'flex';
        chatContainer.style.display = 'none';
        messages.innerHTML = '';
        currentStep = 'financial';
        financialInfo = null;
        activityGoals = null;
    });

    // Start planning button
    startPlanningBtn.addEventListener('click', () => {
        welcomeScreen.style.display = 'none';
        chatContainer.style.display = 'flex';
        addAssistantMessage(`Welcome! Let's create your personalized life and budget plan.

Please describe your financial situation, including:
• Current balance
• Income details (amount and frequency)
• Bills and their due dates
• Savings goals
• Any additional income

For example: "I have $3500 in my account. I get paid $2500 biweekly on Fridays. My rent is $1200 due on the 1st, car payment $300 on the 15th. I want to save $500 per paycheck."`);
    });

    // Send message
    const sendMessage = () => {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message
        addUserMessage(message);
        userInput.value = '';
        userInput.style.height = 'auto';

        // Show typing indicator
        const typingIndicator = addTypingIndicator();

        // Process message based on current step
        if (currentStep === 'financial') {
            // Send to backend to process financial information
            fetch('/api/parse_budget', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ input: message })
            })
            .then(response => response.json())
            .then(data => {
                removeTypingIndicator(typingIndicator);
                if (data.success) {
                    financialInfo = data.budget_info;
                    currentStep = 'activities';
                    addAssistantMessage(`Great! I've recorded your financial information.

Now, please describe your goals and activities for the next two weeks, including:
• Meal planning goals
• Workout plans
• Learning goals
• Hobbies or other activities

For example: "I want to cook dinner 6 days a week, workout 4 times in the morning, and study Spanish for 30 minutes every day."`);
                } else {
                    addAssistantMessage("I couldn't process your financial information. Please try again with more details about your income, expenses, and savings goals.");
                }
            })
            .catch(error => {
                removeTypingIndicator(typingIndicator);
                addAssistantMessage("Sorry, there was an error processing your request. Please try again.");
                console.error('Error:', error);
            });
        } else if (currentStep === 'activities') {
            // Send to backend to process activity goals
            fetch('/api/parse_activities', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ input: message })
            })
            .then(response => response.json())
            .then(data => {
                removeTypingIndicator(typingIndicator);
                if (data.success) {
                    activityGoals = data.activity_goals;
                    showDateModal();
                } else {
                    addAssistantMessage("I couldn't process your activity goals. Please try again with more details about your planned activities.");
                }
            })
            .catch(error => {
                removeTypingIndicator(typingIndicator);
                addAssistantMessage("Sorry, there was an error processing your request. Please try again.");
                console.error('Error:', error);
            });
        }
    };

    // Handle send button click and Enter key
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Date modal handlers
    const showDateModal = () => {
        dateModal.classList.add('active');
        // Set min date to today
        const today = new Date().toISOString().split('T')[0];
        startDate.min = today;
        endDate.min = today;
    };

    const hideDateModal = () => {
        dateModal.classList.remove('active');
    };

    confirmDateBtn.addEventListener('click', () => {
        const start = startDate.value;
        const end = endDate.value;

        if (!start || !end) {
            alert('Please select both start and end dates.');
            return;
        }

        if (new Date(end) < new Date(start)) {
            alert('End date must be after start date.');
            return;
        }

        hideDateModal();
        addAssistantMessage("Generating your personalized life and budget plan...");

        // Generate plan
        fetch('/api/generate_plan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_date: start,
                end_date: end,
                budget_info: financialInfo,
                activity_goals: activityGoals
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addAssistantMessage(`Your plan has been generated successfully! 

You can now:
1. Download the calendar file (enhanced_life_plan.ics)
2. Import it into your preferred calendar application
3. Start following your personalized plan

Would you like to create another plan or make any adjustments to this one?`);

                // Add to history
                addToPlanHistory(start, end);
            } else {
                addAssistantMessage("Sorry, there was an error generating your plan. Please try again.");
            }
        })
        .catch(error => {
            addAssistantMessage("Sorry, there was an error generating your plan. Please try again.");
            console.error('Error:', error);
        });
    });

    cancelDateBtn.addEventListener('click', hideDateModal);

    // Close modal when clicking outside
    dateModal.addEventListener('click', (e) => {
        if (e.target === dateModal) {
            hideDateModal();
        }
    });

    // Helper functions
    function addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.textContent = text;
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    function addAssistantMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = text.replace(/\n/g, '<br>');
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    function addTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message assistant typing';
        indicatorDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        messages.appendChild(indicatorDiv);
        messages.scrollTop = messages.scrollHeight;
        return indicatorDiv;
    }

    function removeTypingIndicator(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }

    function addToPlanHistory(start, end) {
        const planDiv = document.createElement('div');
        planDiv.className = 'plan-item';
        planDiv.innerHTML = `
            <svg class="plan-icon" viewBox="0 0 24 24">
                <path d="M21 4H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z" fill="none" stroke="currentColor" stroke-width="2"/>
                <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" stroke-width="2"/>
            </svg>
            <span>${new Date(start).toLocaleDateString()} - ${new Date(end).toLocaleDateString()}</span>
        `;
        planHistory.insertBefore(planDiv, planHistory.firstChild);
    }
}); 