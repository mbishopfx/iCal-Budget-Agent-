import Foundation

struct UserData: Codable {
    var budgetInfo: BudgetInfo
    var activityGoals: ActivityGoals
    var workSchedule: WorkSchedule
    var hobbiesAndInterests: String
    var dateRange: DateRange
}

struct BudgetInfo: Codable {
    var startingBalance: Double
    var income: Income
    var savingsGoal: Double
    var emergencyFund: Double
    var expenses: [Expense]
}

struct Income: Codable {
    var amount: Double
    var frequency: String
    var nextDate: String
    var source: String
}

struct Expense: Codable, Identifiable {
    var id = UUID()
    var name: String
    var amount: Double
    var frequency: String
    var category: String
}

struct ActivityGoals: Codable {
    var workoutPreferences: WorkoutPreferences
    var goals: [ActivityGoal]
}

struct WorkoutPreferences: Codable {
    var location: String
    var experienceLevel: String
    var availableEquipment: [String]
}

struct ActivityGoal: Codable, Identifiable {
    var id = UUID()
    var title: String
    var frequency: String
    var duration: Int
}

struct WorkSchedule: Codable {
    var days: [String]
    var startTime: String
    var endTime: String
}

struct DateRange: Codable {
    var startDate: String
    var endDate: String
} 