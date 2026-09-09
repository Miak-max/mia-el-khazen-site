import AVFoundation
import AppKit
let args = CommandLine.arguments
let asset = AVURLAsset(url: URL(fileURLWithPath: args[1]))
let outPrefix = args[2]
let gen = AVAssetImageGenerator(asset: asset)
gen.appliesPreferredTrackTransform = true
gen.requestedTimeToleranceBefore = .zero
gen.requestedTimeToleranceAfter = .zero
for s in args[3...] {
    let t = Double(s)!
    do {
        let cg = try gen.copyCGImage(at: CMTime(seconds: t, preferredTimescale: 600), actualTime: nil)
        let rep = NSBitmapImageRep(cgImage: cg)
        let data = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.92])!
        try data.write(to: URL(fileURLWithPath: "\(outPrefix)-\(Int(t)).jpg"))
        print("frame \(t)s -> \(cg.width)x\(cg.height)")
    } catch { print("failed at \(t)s: \(error)") }
}
