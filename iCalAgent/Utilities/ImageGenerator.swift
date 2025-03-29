import SwiftUI

struct PlaceholderImage: View {
    let title: String
    let icon: String
    let color: Color
    
    var body: some View {
        ZStack {
            // Background
            RoundedRectangle(cornerRadius: 20)
                .fill(color.opacity(0.2))
                .frame(width: 300, height: 300)
            
            VStack(spacing: 20) {
                // Icon
                Image(systemName: icon)
                    .font(.system(size: 60))
                    .foregroundColor(color)
                
                // Title
                Text(title)
                    .font(.headline)
                    .foregroundColor(color)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
        }
    }
}

struct ImageGenerator {
    static func generatePlaceholderImages() -> [UIImage] {
        let images = [
            (title: "Welcome", icon: "calendar.badge.plus", color: Color.blue),
            (title: "Smart Planning", icon: "list.bullet.clipboard", color: Color.purple),
            (title: "Brain Dump", icon: "brain", color: Color.orange),
            (title: "Calendar", icon: "calendar", color: Color.green)
        ]
        
        return images.map { image in
            let renderer = ImageRenderer(content: PlaceholderImage(
                title: image.title,
                icon: image.icon,
                color: image.color
            ))
            renderer.scale = 3.0 // 3x for Retina
            return renderer.uiImage ?? UIImage()
        }
    }
} 