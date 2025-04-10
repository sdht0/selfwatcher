import Carbon
import Cocoa
import CoreGraphics
import Foundation

let homeDirURL = FileManager.default.homeDirectoryForCurrentUser
let logBaseDirURL =
    homeDirURL
    .appendingPathComponent(".local")
    .appendingPathComponent("selfwatcher")

assert(
    FileManager.default.fileExists(atPath: logBaseDirURL.path),
    "Log dir missing: \(logBaseDirURL.path)")

let FILE_SEP = ";"
let IDLE_TIMEOUT_SEC: TimeInterval = 5 * 60
let POLL_INTERVAL_SEC: TimeInterval = 2
let PRINT_INTERVAL_SEC: TimeInterval = 1 * 60

let KEYS_ARR: [(String, String)] = [
    ("TIME", "time"),
    ("ALPHABETS", "k-az"),
    ("NUMBERS", "k-09"),
    ("SPECHARS", "k-spl"),
    ("ALT", "k-alt"),
    ("SHIFT", "k-sft"),
    ("CTRL", "k-ctl"),
    ("DELETE", "k-del"),
    ("CMD", "k-cmd"),
    ("ARROWS", "k-arr"),
    ("ENTER", "k-etr"),
    ("SPACE", "k-spc"),
    ("TAB", "k-tab"),
    ("ESC", "k-esc"),
    ("NAV", "k-nav"),
    ("FUNC", "k-fun"),
    ("OTHERS", "k-oth"),
    ("LCLICK", "m-lc"),
    ("RCLICK", "m-rc"),
    ("MCLICK", "m-mc"),
    ("SCROLL", "m-srl"),
]
let KEYS_INDICES = Dictionary(uniqueKeysWithValues: KEYS_ARR.enumerated().map { ($0.element.0, $0.offset) })

let INIT_COUNTS = Array(repeating: 0, count: KEYS_ARR.count)
var G_key_counts_now = INIT_COUNTS
var G_key_counts_next = INIT_COUNTS

var G_data_now = [(String, String, [Int])]()
var G_data_next = [(String, String, [Int])]()

var G_last_input_time = Date()
var G_last_report_time = Date()
var G_last_mouse_position = NSEvent.mouseLocation

let lock = NSLock()
let lock2 = NSLock()

// MARK: - Utility Functions

func getActiveWindowTitle() -> String {
    guard let frontmostApp = NSWorkspace.shared.frontmostApplication else {
        return "_unknown" + FILE_SEP + "_unknown"
    }

    let appName = frontmostApp.localizedName ?? "_unknown"
    var windowTitle = "_unknown"

    let pid = frontmostApp.processIdentifier
    let focusedApp = AXUIElementCreateApplication(pid)
    var focusedWindow: AnyObject?
    AXUIElementCopyAttributeValue(focusedApp, kAXFocusedWindowAttribute as CFString, &focusedWindow)

    if focusedWindow != nil {
        let window = focusedWindow as! AXUIElement
        var title: AnyObject?
        AXUIElementCopyAttributeValue(window, kAXTitleAttribute as CFString, &title)
        windowTitle = title as? String ?? "_unknown"
    }

    let cleanApp = appName.replacingOccurrences(of: FILE_SEP, with: "_")
    let cleanTitle = windowTitle.replacingOccurrences(of: FILE_SEP, with: "_")
    return cleanApp + FILE_SEP + cleanTitle
}

func classifyKey(event: CGEvent) -> [Int] {
    let keyCode = CGKeyCode(event.getIntegerValueField(.keyboardEventKeycode))
    let flags = event.flags

    var out: [Int] = []

    // Modifier keys (like CMD, ALT, SHIFT)
    if flags.contains(.maskAlternate) {
        out.append(KEYS_INDICES["ALT"]!)
    }
    if flags.contains(.maskShift) {
        out.append(KEYS_INDICES["SHIFT"]!)
    }
    if flags.contains(.maskControl) {
        out.append(KEYS_INDICES["CTRL"]!)
    }
    if flags.contains(.maskCommand) {
        out.append(KEYS_INDICES["CMD"]!)
    }

    // print(keyCode)

    switch keyCode {
    case 0, 11, 8, 2, 14, 3, 5, 4, 34, 38, 40, 37, 46, 45, 31, 35, 12, 15, 1, 17, 32, 9, 13, 7, 16, 6:  // a-z
        out.append(KEYS_INDICES["ALPHABETS"]!)
    case 29, 18, 19, 20, 21, 23, 22, 26, 28, 25:  // 0-9
        out.append(KEYS_INDICES["NUMBERS"]!)
    case 50, 27, 24, 33, 30, 41, 39, 43, 47, 44, 42, 75, 67, 78, 69, 65:  // specialchars
        out.append(KEYS_INDICES["SPECHARS"]!)
    case 51, 117:  // delete, forward delete
        out.append(KEYS_INDICES["DELETE"]!)
    case 123, 124, 125, 126:  // arrows: left, right, down, up
        out.append(KEYS_INDICES["ARROWS"]!)
    case 36:  // return
        out.append(KEYS_INDICES["ENTER"]!)
    case 49:  // space
        out.append(KEYS_INDICES["SPACE"]!)
    case 48:  // tab
        out.append(KEYS_INDICES["TAB"]!)
    case 53:  // esc
        out.append(KEYS_INDICES["ESC"]!)
    case 115, 119, 121, 116, 114, 57:  // home, end, page down, page up, insert, caps lock
        out.append(KEYS_INDICES["NAV"]!)
    case 122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111:  // F1–F12
        out.append(KEYS_INDICES["FUNC"]!)
    default:
        out.append(KEYS_INDICES["OTHERS"]!)
    }

    return out
}

func updateLastInput() {
    lock.lock()
    G_last_input_time = Date()
    lock.unlock()
}

func startReporter() {
    DispatchQueue.global(qos: .background).async {
        while true {
            Thread.sleep(forTimeInterval: POLL_INTERVAL_SEC)

            let currentMousePosition = NSEvent.mouseLocation
            if currentMousePosition != G_last_mouse_position {
                updateLastInput()
                G_last_mouse_position = currentMousePosition
            }

            lock.lock()
            let idle = Date().timeIntervalSince(G_last_input_time) > IDLE_TIMEOUT_SEC
            lock.unlock()

            var isIdle = "";
            if idle {
                isIdle = "_idle"
            }

            let title = getActiveWindowTitle()
            let windowTitle = "\(isIdle)\(FILE_SEP)\(title)"

            lock.lock()
            swap(&G_key_counts_now, &G_key_counts_next)
            lock.unlock()

            G_key_counts_next[KEYS_INDICES["TIME"]!] = Int(Date().timeIntervalSince(G_last_report_time))

            lock2.lock()
            if G_data_now.count == 0 || G_data_now.last?.1 != windowTitle {
                let dateFormatter = DateFormatter()
                dateFormatter.dateFormat = "HH:mm:ss"
                let timeStr = dateFormatter.string(from: Date())
                G_data_now.append((timeStr, windowTitle, INIT_COUNTS))
            }

            let last = G_data_now.count - 1
            for (_, index) in KEYS_INDICES {
                G_data_now[last].2[index] += G_key_counts_next[index]
                G_key_counts_next[index] = 0;
            }
            lock2.unlock()

            G_last_report_time = Date()
        }
    }
}

func startPrinter() {
    DispatchQueue.global(qos: .background).async {
        while true {
            Thread.sleep(forTimeInterval: PRINT_INTERVAL_SEC)

            lock2.lock()
            swap(&G_data_now, &G_data_next)
            lock2.unlock()

            let now = Date()
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "yyyy-MM-dd"
            dateFormatter.dateFormat = "yyyy"
            let year = dateFormatter.string(from: now)
            dateFormatter.dateFormat = "MM"
            let month = dateFormatter.string(from: now)
            dateFormatter.dateFormat = "dd"
            let day = dateFormatter.string(from: now)
            let dateStr = "\(year)-\(month)-\(day)"

            var lines: [String] = []
            for (timeStr, window, counts) in G_data_next {
                let stats = KEYS_ARR.map { "\($0.1):\(counts[KEYS_INDICES[$0.0]!])" }.joined(separator: FILE_SEP)
                lines.append("\(timeStr)\(FILE_SEP)\(window)\(FILE_SEP)\(stats)")
            }
            G_data_next.removeAll()

            let logDir = logBaseDirURL.appendingPathComponent(year).appendingPathComponent(month)

            do {
                try FileManager.default.createDirectory(
                    at: logDir, withIntermediateDirectories: true, attributes: nil)
            } catch {
                print("Error creating log directory: \(error)")
                exit(1)
            }

            let logFile = logDir.appendingPathComponent("window-\(dateStr).txt")

            do {
                if !FileManager.default.fileExists(atPath: logFile.path) {
                    FileManager.default.createFile(
                        atPath: logFile.path, contents: nil, attributes: nil)
                }

                let fileHandle = try FileHandle(forUpdating: logFile)
                defer {
                    fileHandle.closeFile()
                }

                for line in lines {
                    if let data = (line + "\n").data(using: .utf8) {
                        fileHandle.seekToEndOfFile()
                        fileHandle.write(data)
                    }
                }
            } catch {
                print("Error writing to log file: \(error)")
                exit(1)
            }
        }
    }
}

// MARK: - Start Hooks

func setupCGEventTap() {
    let eventMask: CGEventMask =
        ((1 << CGEventType.keyDown.rawValue) | (1 << CGEventType.leftMouseDown.rawValue)
            | (1 << CGEventType.rightMouseDown.rawValue)
            | (1 << CGEventType.otherMouseDown.rawValue) | (1 << CGEventType.scrollWheel.rawValue))

    let eventTap = CGEvent.tapCreate(
        tap: .cgSessionEventTap,
        place: .headInsertEventTap,
        options: .defaultTap,
        eventsOfInterest: eventMask,
        callback: { _, type, event, _ -> Unmanaged<CGEvent>? in
            switch type {
            case .keyDown:
                updateLastInput()
                let indices = classifyKey(event: event)
                // print(keys)
                lock.lock()
                for index in indices {
                    G_key_counts_now[index] += 1
                }
                lock.unlock()
            case .leftMouseDown:
                updateLastInput()
                // print("click: left")
                lock.lock()
                G_key_counts_now[KEYS_INDICES["LCLICK"]!] += 1
                lock.unlock()
            case .rightMouseDown:
                updateLastInput()
                // print("click: right")
                lock.lock()
                G_key_counts_now[KEYS_INDICES["RCLICK"]!] += 1
                lock.unlock()
            case .otherMouseDown:
                updateLastInput()
                // print("click: middle")
                lock.lock()
                G_key_counts_now[KEYS_INDICES["MCLICK"]!] += 1
                lock.unlock()
            case .scrollWheel:
                updateLastInput()
                // print("scroll")
                lock.lock()
                G_key_counts_now[KEYS_INDICES["SCROLL"]!] += 1
                lock.unlock()
            default:
                break
            }

            return Unmanaged.passRetained(event)
        },
        userInfo: nil
    )

    guard let tap = eventTap else {
        print("Failed to create event tap. Run with accessibility permissions enabled.")
        exit(1)
    }

    let runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
    CGEvent.tapEnable(tap: tap, enable: true)
}

// MARK: - Main

startReporter()
startPrinter()
setupCGEventTap()
CFRunLoopRun()
