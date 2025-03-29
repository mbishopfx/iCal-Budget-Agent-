import Foundation
import UIKit

class AssetCatalogManager {
    static let shared = AssetCatalogManager()
    
    private let imageNames = [
        "welcome_animation",
        "planner_tutorial",
        "brain_dump_tutorial",
        "calendar_tutorial"
    ]
    
    func savePlaceholderImages() {
        let images = ImageGenerator.generatePlaceholderImages()
        
        for (index, image) in images.enumerated() {
            saveImage(image, withName: imageNames[index])
        }
    }
    
    private func saveImage(_ image: UIImage, withName name: String) {
        guard let data = image.pngData() else { return }
        
        // Get the documents directory
        guard let documentsDirectory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else { return }
        
        // Create the file URL
        let fileURL = documentsDirectory.appendingPathComponent("\(name).png")
        
        // Write the image data
        try? data.write(to: fileURL)
        
        print("Saved image: \(fileURL.path)")
    }
} 