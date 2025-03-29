import SwiftUI

struct FinancialInputView: View {
    @Binding var startingBalance: Double
    @Binding var income: Income
    @Binding var savingsGoal: Double
    @Binding var emergencyFund: Double
    @Binding var expenses: [Expense]
    
    var body: some View {
        VStack(spacing: 20) {
            // Starting Balance
            HStack {
                Text("Starting Balance")
                Spacer()
                TextField("Amount", value: $startingBalance, format: .currency(code: "USD"))
                    .keyboardType(.decimalPad)
                    .multilineTextAlignment(.trailing)
            }
            
            // Income
            VStack(alignment: .leading) {
                Text("Income")
                HStack {
                    TextField("Amount", value: $income.amount, format: .currency(code: "USD"))
                        .keyboardType(.decimalPad)
                    
                    Picker("Frequency", selection: $income.frequency) {
                        Text("Biweekly").tag("biweekly")
                        Text("Monthly").tag("monthly")
                    }
                }
            }
            
            // Savings Goal
            HStack {
                Text("Savings Goal")
                Spacer()
                TextField("Amount", value: $savingsGoal, format: .currency(code: "USD"))
                    .keyboardType(.decimalPad)
                    .multilineTextAlignment(.trailing)
            }
            
            // Emergency Fund
            HStack {
                Text("Emergency Fund")
                Spacer()
                TextField("Amount", value: $emergencyFund, format: .currency(code: "USD"))
                    .keyboardType(.decimalPad)
                    .multilineTextAlignment(.trailing)
            }
            
            // Expenses
            VStack(alignment: .leading) {
                Text("Expenses")
                ForEach($expenses) { $expense in
                    HStack {
                        TextField("Name", text: $expense.name)
                        Spacer()
                        TextField("Amount", value: $expense.amount, format: .currency(code: "USD"))
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                    }
                }
                
                Button(action: {
                    expenses.append(Expense(name: "", amount: 0, frequency: "monthly", category: "other"))
                }) {
                    Label("Add Expense", systemImage: "plus.circle.fill")
                }
            }
        }
        .padding()
    }
}

#Preview {
    FinancialInputView(
        startingBalance: .constant(1000),
        income: .constant(Income(amount: 5000, frequency: "monthly", nextDate: "", source: "work")),
        savingsGoal: .constant(500),
        emergencyFund: .constant(3000),
        expenses: .constant([])
    )
} 