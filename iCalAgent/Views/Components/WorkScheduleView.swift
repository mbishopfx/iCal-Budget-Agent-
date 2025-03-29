import SwiftUI

struct WorkScheduleView: View {
    @Binding var workSchedule: WorkSchedule
    
    private let weekDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    var body: some View {
        VStack(spacing: 20) {
            // Work Days
            VStack(alignment: .leading) {
                Text("Work Days")
                ForEach(weekDays, id: \.self) { day in
                    Toggle(day, isOn: Binding(
                        get: { workSchedule.days.contains(day.lowercased()) },
                        set: { isOn in
                            if isOn {
                                workSchedule.days.append(day.lowercased())
                            } else {
                                workSchedule.days.removeAll { $0 == day.lowercased() }
                            }
                        }
                    ))
                }
            }
            
            // Work Hours
            VStack(alignment: .leading) {
                Text("Work Hours")
                HStack {
                    DatePicker("Start Time", selection: Binding(
                        get: { DateFormatter.timeOnly.date(from: workSchedule.startTime) ?? Date() },
                        set: { workSchedule.startTime = DateFormatter.timeOnly.string(from: $0) }
                    ), displayedComponents: .hourAndMinute)
                    
                    Text("to")
                    
                    DatePicker("End Time", selection: Binding(
                        get: { DateFormatter.timeOnly.date(from: workSchedule.endTime) ?? Date() },
                        set: { workSchedule.endTime = DateFormatter.timeOnly.string(from: $0) }
                    ), displayedComponents: .hourAndMinute)
                }
            }
        }
        .padding()
    }
}

extension DateFormatter {
    static let timeOnly: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter
    }()
}

#Preview {
    WorkScheduleView(workSchedule: .constant(WorkSchedule(
        days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
        startTime: "09:00",
        endTime: "17:00"
    )))
} 