import SwiftUI

struct ActivityInputView: View {
    @Binding var workoutPreferences: WorkoutPreferences
    @Binding var goals: [ActivityGoal]
    
    var body: some View {
        VStack(spacing: 20) {
            // Workout Location
            VStack(alignment: .leading) {
                Text("Workout Location")
                Picker("Location", selection: $workoutPreferences.location) {
                    Text("Gym").tag("gym")
                    Text("Home").tag("home")
                    Text("Both").tag("both")
                }
                .pickerStyle(.segmented)
            }
            
            // Experience Level
            VStack(alignment: .leading) {
                Text("Experience Level")
                Picker("Level", selection: $workoutPreferences.experienceLevel) {
                    Text("Beginner").tag("beginner")
                    Text("Intermediate").tag("intermediate")
                    Text("Advanced").tag("advanced")
                }
                .pickerStyle(.segmented)
            }
            
            // Available Equipment
            VStack(alignment: .leading) {
                Text("Available Equipment")
                ForEach(["Dumbbells", "Resistance Bands", "Pull-up Bar", "Yoga Mat"], id: \.self) { equipment in
                    Toggle(equipment, isOn: Binding(
                        get: { workoutPreferences.availableEquipment.contains(equipment.lowercased()) },
                        set: { isOn in
                            if isOn {
                                workoutPreferences.availableEquipment.append(equipment.lowercased())
                            } else {
                                workoutPreferences.availableEquipment.removeAll { $0 == equipment.lowercased() }
                            }
                        }
                    ))
                }
            }
            
            // Activity Goals
            VStack(alignment: .leading) {
                Text("Activity Goals")
                ForEach($goals) { $goal in
                    VStack {
                        TextField("Activity Name", text: $goal.title)
                        
                        HStack {
                            Picker("Frequency", selection: $goal.frequency) {
                                Text("Daily").tag("daily")
                                Text("Weekly").tag("weekly")
                                Text("Biweekly").tag("biweekly")
                            }
                            
                            TextField("Duration (min)", value: $goal.duration, format: .number)
                                .keyboardType(.numberPad)
                        }
                    }
                    .padding(.vertical, 8)
                }
                
                Button(action: {
                    goals.append(ActivityGoal(title: "", frequency: "weekly", duration: 30))
                }) {
                    Label("Add Activity", systemImage: "plus.circle.fill")
                }
            }
        }
        .padding()
    }
}

#Preview {
    ActivityInputView(
        workoutPreferences: .constant(WorkoutPreferences(
            location: "home",
            experienceLevel: "beginner",
            availableEquipment: []
        )),
        goals: .constant([])
    )
} 