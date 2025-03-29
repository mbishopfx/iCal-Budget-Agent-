import SwiftUI

struct OnboardingPage: Identifiable {
    let id = UUID()
    let image: String
    let title: String
    let description: String
    let icon: String
    let color: Color
}

struct OnboardingView: View {
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false
    @State private var currentPage = 0
    @State private var isAnimating = false
    @State private var showContent = false
    @State private var iconScale: CGFloat = 1.0
    @State private var iconRotation: Double = 0
    @State private var backgroundOffset: CGSize = .zero
    
    private let pages = [
        OnboardingPage(
            image: "welcome_animation",
            title: "Welcome to iCal Agent",
            description: "Your personal AI-powered life planner that helps you organize your time, finances, and activities.",
            icon: "calendar.badge.plus",
            color: .blue
        ),
        OnboardingPage(
            image: "planner_tutorial",
            title: "Smart Planning",
            description: "Input your financial goals, work schedule, and activity preferences to create a personalized plan.",
            icon: "list.bullet.clipboard",
            color: .purple
        ),
        OnboardingPage(
            image: "brain_dump_tutorial",
            title: "Brain Dump",
            description: "Let your thoughts flow freely and watch as we transform them into actionable calendar events.",
            icon: "brain",
            color: .orange
        ),
        OnboardingPage(
            image: "calendar_tutorial",
            title: "Calendar Integration",
            description: "Seamlessly sync your plans with your calendar and stay on track with your goals.",
            icon: "calendar",
            color: .green
        )
    ]
    
    var body: some View {
        ZStack {
            // Animated background gradient
            LinearGradient(
                gradient: Gradient(colors: [
                    pages[currentPage].color.opacity(0.3),
                    pages[currentPage].color.opacity(0.1)
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            .offset(backgroundOffset)
            .animation(.easeInOut(duration: 0.5), value: currentPage)
            
            // Floating shapes
            ForEach(0..<3) { index in
                Circle()
                    .fill(pages[currentPage].color.opacity(0.1))
                    .frame(width: 100, height: 100)
                    .offset(x: CGFloat(index * 100 - 100), y: CGFloat(index * 50 - 50))
                    .blur(radius: 20)
                    .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: currentPage)
            }
            
            VStack {
                TabView(selection: $currentPage) {
                    ForEach(Array(pages.enumerated()), id: \.element.id) { index, page in
                        VStack(spacing: 20) {
                            // Image container with 3D effect
                            ZStack {
                                // Shadow
                                RoundedRectangle(cornerRadius: 20)
                                    .fill(page.color.opacity(0.2))
                                    .frame(width: 300, height: 300)
                                    .shadow(color: page.color.opacity(0.3), radius: 20, x: 0, y: 10)
                                
                                // Icon with 3D rotation
                                Image(systemName: page.icon)
                                    .font(.system(size: 60))
                                    .foregroundColor(page.color)
                                    .scaleEffect(iconScale)
                                    .rotation3DEffect(.degrees(iconRotation), axis: (x: 0, y: 1, z: 0))
                                    .animation(
                                        Animation.easeInOut(duration: 1.0)
                                            .repeatForever(autoreverses: true),
                                        value: isAnimating
                                    )
                            }
                            .transition(
                                .asymmetric(
                                    insertion: .scale(scale: 0.8).combined(with: .opacity),
                                    removal: .scale(scale: 1.2).combined(with: .opacity)
                                )
                            )
                            
                            // Text content with staggered animation
                            VStack(spacing: 10) {
                                Text(page.title)
                                    .font(.title)
                                    .bold()
                                    .multilineTextAlignment(.center)
                                    .foregroundColor(page.color)
                                    .transition(.move(edge: .trailing).combined(with: .opacity))
                                
                                Text(page.description)
                                    .font(.body)
                                    .multilineTextAlignment(.center)
                                    .foregroundColor(.secondary)
                                    .padding(.horizontal)
                                    .transition(.move(edge: .trailing).combined(with: .opacity))
                            }
                            .opacity(showContent ? 1 : 0)
                            .offset(y: showContent ? 0 : 20)
                        }
                        .tag(index)
                    }
                }
                .tabViewStyle(.page(indexDisplayMode: .always))
                .indexViewStyle(.page(backgroundDisplayMode: .always))
                
                // Get Started Button with scale animation
                Button(action: {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                        hasCompletedOnboarding = true
                    }
                }) {
                    Text(currentPage == pages.count - 1 ? "Get Started" : "Skip")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(width: 200, height: 50)
                        .background(pages[currentPage].color)
                        .cornerRadius(25)
                        .shadow(color: pages[currentPage].color.opacity(0.3), radius: 10, x: 0, y: 5)
                }
                .padding(.bottom, 30)
                .opacity(showContent ? 1 : 0)
                .offset(y: showContent ? 0 : 20)
                .scaleEffect(showContent ? 1 : 0.8)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.5)) {
                showContent = true
            }
            isAnimating = true
            
            // Start continuous animations
            withAnimation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true)) {
                iconScale = 1.1
                iconRotation = 5
            }
            
            // Animate background
            withAnimation(.easeInOut(duration: 3.0).repeatForever(autoreverses: true)) {
                backgroundOffset = CGSize(width: 50, height: 50)
            }
        }
        .onChange(of: currentPage) { _ in
            // Reset animations
            withAnimation(.easeOut(duration: 0.3)) {
                showContent = false
                iconScale = 1.0
                iconRotation = 0
            }
            
            // Start new animations
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                withAnimation(.easeIn(duration: 0.5)) {
                    showContent = true
                    iconScale = 1.1
                    iconRotation = 5
                }
            }
        }
    }
}

#Preview {
    OnboardingView()
} 