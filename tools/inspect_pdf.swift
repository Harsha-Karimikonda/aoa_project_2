// macOS-only optional PDF inspection; not needed to reproduce experiments.
import Foundation
import AppKit
import PDFKit

guard CommandLine.arguments.count == 3,
      let document = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1])) else {
    fatalError("usage: swift tools/inspect_pdf.swift report/main.pdf /tmp/aoa-pdf-preview")
}
let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
print("Pages: \(document.pageCount)")
var allText = ""
for index in 0..<document.pageCount {
    guard let page = document.page(at: index) else { continue }
    let text = page.string ?? ""
    allText += "\n=== PAGE \(index + 1) ===\n" + text
    print("Page \(index + 1): \(text.prefix(95).replacingOccurrences(of: "\n", with: " | "))")
    let image = page.thumbnail(of: NSSize(width: 1224, height: 1584), for: .mediaBox)
    guard let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let png = bitmap.representation(using: .png, properties: [:]) else { continue }
    try png.write(to: output.appendingPathComponent("page-\(index + 1).png"))
}
try allText.write(to: output.appendingPathComponent("text.txt"), atomically: true, encoding: .utf8)
