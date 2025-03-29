import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = UserDataViewModel()
    
    var body: some View {
        TabView {
            PlannerView()
                .tabItem {
                    Label("Planner", systemImage: "calendar")
                }
            
            BrainDumpView()
                .tabItem {
                    Label("Brain Dump", systemImage: "brain")
                }
            
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
        }
        .environmentObject(viewModel)
    }
}

struct PlannerView: View {
    @EnvironmentObject var viewModel: UserDataViewModel
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Financial Information")) {
                    // Add financial input fields
                }
                
                Section(header: Text("Activity Goals")) {
                    // Add activity goal input fields
                }
                
                Section(header: Text("Work Schedule")) {
                    // Add work schedule input fields
                }
                
                Section(header: Text("Hobbies & Interests")) {
                    // Add hobbies input field
                }
                
                Section(header: Text("Date Range")) {
                    // Add date range pickers
                }
                
                Section {
                    Button(action: {
                        Task {
                            await viewModel.generatePlan()
                        }
                    }) {
                        if viewModel.isLoading {
                            ProgressView()
                        } else {
                            Text("Generate Plan")
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .disabled(viewModel.isLoading)
                }
            }
            .navigationTitle("Life Planner")
            .alert("Error", isPresented: .constant(viewModel.error != nil)) {
                Button("OK") {
                    viewModel.error = nil
                }
            } message: {
                Text(viewModel.error ?? "")
            }
        }
    }
}

struct BrainDumpView: View {
    @EnvironmentObject var viewModel: UserDataViewModel
    @State private var brainDumpText = ""
    @State private var startDate = Date()
    @State private var endDate = Date().addingTimeInterval(30 * 24 * 60 * 60)
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Your Thoughts")) {
                    TextEditor(text: $brainDumpText)
                        .frame(height: 200)
                }
                
                Section(header: Text("Timeline")) {
                    DatePicker("Start Date", selection: $startDate, displayedComponents: .date)
                    DatePicker("End Date", selection: $endDate, displayedComponents: .date)
                }
                
                Section {
                    Button(action: {
                        // Handle brain dump submission
                    }) {
                        Text("Generate Plan")
                            .frame(maxWidth: .infinity)
                    }
                }
            }
            .navigationTitle("Brain Dump")
        }
    }
}

struct SettingsView: View {
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Account")) {
                    // Add account settings
                }
                
                Section(header: Text("Preferences")) {
                    // Add app preferences
                }
                
                Section(header: Text("About")) {
                    // Add about information
                }
            }
            .navigationTitle("Settings")
        }
    }
}

#Preview {
    ContentView()
} 