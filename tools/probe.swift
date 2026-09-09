import AVFoundation
// usage: swift tools/probe.swift <file>…   → codec, natural size, displayed size (after rotation), bitrate, duration
for path in CommandLine.arguments.dropFirst() {
    let asset = AVURLAsset(url: URL(fileURLWithPath: path))
    print("## \(path)  duration \(String(format: "%.1f", CMTimeGetSeconds(asset.duration)))s")
    for t in asset.tracks {
        let d = t.formatDescriptions.first as! CMFormatDescription
        let sub = CMFormatDescriptionGetMediaSubType(d)
        let s = String(format: "%c%c%c%c", (sub>>24)&255,(sub>>16)&255,(sub>>8)&255,sub&255)
        if t.mediaType == .video {
            let disp = t.naturalSize.applying(t.preferredTransform)
            print("  video \(s) natural \(Int(t.naturalSize.width))x\(Int(t.naturalSize.height)) displayed \(Int(abs(disp.width)))x\(Int(abs(disp.height))) \(Int(t.estimatedDataRate/1000)) kbps \(String(format: "%.0f", t.nominalFrameRate)) fps")
        } else {
            print("  \(t.mediaType.rawValue) \(s) \(Int(t.estimatedDataRate/1000)) kbps")
        }
    }
}
