import AVFoundation
import Foundation
// usage: swift transcode.swift <in> <out.mp4> <width> <height> <videoKbps> <audioKbps>
let a = CommandLine.arguments
let asset = AVURLAsset(url: URL(fileURLWithPath: a[1]))
let outURL = URL(fileURLWithPath: a[2]); try? FileManager.default.removeItem(at: outURL)
let w = Int(a[3])!, h = Int(a[4])!, vk = Int(a[5])!, ak = Int(a[6])!
let vTrack = asset.tracks(withMediaType: .video).first!
let aTrack = ak > 0 ? asset.tracks(withMediaType: .audio).first : nil   // ak == 0 drops audio
let reader = try! AVAssetReader(asset: asset)
let writer = try! AVAssetWriter(outputURL: outURL, fileType: .mp4)
let vOut = AVAssetReaderTrackOutput(track: vTrack, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange])
reader.add(vOut)
let vIn = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: vk * 1000, AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel, AVVideoMaxKeyFrameIntervalKey: 60, AVVideoAllowFrameReorderingKey: true]])
vIn.transform = vTrack.preferredTransform
writer.add(vIn)
var aOut: AVAssetReaderTrackOutput? = nil; var aIn: AVAssetWriterInput? = nil
if let t = aTrack {
    aOut = AVAssetReaderTrackOutput(track: t, outputSettings: [AVFormatIDKey: kAudioFormatLinearPCM])
    reader.add(aOut!)
    aIn = AVAssetWriterInput(mediaType: .audio, outputSettings: [AVFormatIDKey: kAudioFormatMPEG4AAC, AVNumberOfChannelsKey: 2, AVSampleRateKey: 44100, AVEncoderBitRateKey: ak * 1000])
    writer.add(aIn!)
}
writer.movieFragmentInterval = .invalid
writer.startWriting(); reader.startReading(); writer.startSession(atSourceTime: .zero)
let group = DispatchGroup()
func pump(_ input: AVAssetWriterInput, _ output: AVAssetReaderTrackOutput, _ q: DispatchQueue) {
    group.enter()
    input.requestMediaDataWhenReady(on: q) {
        while input.isReadyForMoreMediaData {
            if let s = output.copyNextSampleBuffer() { input.append(s) } else { input.markAsFinished(); group.leave(); return }
        }
    }
}
pump(vIn, vOut, DispatchQueue(label: "v"))
if let ai = aIn, let ao = aOut { pump(ai, ao, DispatchQueue(label: "a")) }
group.wait()
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()
print("status \(writer.status.rawValue) error \(String(describing: writer.error))")
let size = (try? FileManager.default.attributesOfItem(atPath: a[2])[.size] as? Int) ?? 0
print("wrote \(a[2]) \(size / 1024) KB")
