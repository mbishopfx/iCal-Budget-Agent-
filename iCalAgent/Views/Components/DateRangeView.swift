import SwiftUI

struct DateRangeView: View {
    @Binding var dateRange: DateRange
    
    var body: some View {
        VStack(spacing: 20) {
            DatePicker("Start Date", selection: Binding(
                get: { DateFormatter.dateOnly.date(from: dateRange.startDate) ?? Date() },
                set: { dateRange.startDate = DateFormatter.dateOnly.string(from: $0) }
            ), displayedComponents: .date)
            
            DatePicker("End Date", selection: Binding(
                get: { DateFormatter.dateOnly.date(from: dateRange.endDate) ?? Date() },
                set: { dateRange.endDate = DateFormatter.dateOnly.string(from: $0) }
            ), displayedComponents: .date)
        }
        .padding()
    }
}

extension DateFormatter {
    static let dateOnly: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
}

#Preview {
    DateRangeView(dateRange: .constant(DateRange(
        startDate: "2024-03-20",
        endDate: "2024-04-20"
    )))
} 