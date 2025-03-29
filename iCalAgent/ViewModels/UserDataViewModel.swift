import Foundation
import SwiftUI

class UserDataViewModel: ObservableObject {
    @Published var userData: UserData?
    @Published var isLoading = false
    @Published var error: String?
    
    private let apiBaseURL = "https://your-api-domain.com/api"
    
    func generatePlan() async {
        guard let userData = userData else { return }
        
        isLoading = true
        error = nil
        
        do {
            let url = URL(string: "\(apiBaseURL)/generate_plan")!
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(userData)
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                throw URLError(.badServerResponse)
            }
            
            // Handle successful response
            // You might want to save the calendar file or handle it differently
            
        } catch {
            self.error = error.localizedDescription
        }
        
        isLoading = false
    }
    
    func saveUserData() {
        // Implement local storage using UserDefaults or CoreData
    }
    
    func loadUserData() {
        // Load saved user data
    }
} 