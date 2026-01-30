# 🚀 Advanced Speedtest CLI

[![PyPI version](https://badge.fury.io/py/adv-speedtest-cli.svg)](https://pypi.org/project/adv-speedtest-cli/)
[![Python Version](https://img.shields.io/badge/python-3.7+-3776ab?style=flat-square&logo=python)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen?style=flat-square)](https://github.com/shakilofficial0/adv-speedtest-cli)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-cross--platform-orange?style=flat-square)](README.md)

> A **sophisticated**, **cross-platform** command-line utility for measuring internet speed with precision. Engineered for accuracy, optimized for performance, and designed for modern networks.

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🔧 System Requirements](#-system-requirements)
- [📦 Installation](#-installation)
- [⚡ Quick Start](#-quick-start)
- [🎯 Usage Guide](#-usage-guide)
- [🔬 Advanced Configuration](#-advanced-configuration)
- [📊 Performance Metrics](#-performance-metrics)
- [🏗️ Architecture](#️-architecture)
- [🤝 Contributing](#-contributing)
- [📞 Support](#-support)

---

## ✨ Features

### Core Capabilities
- 🎯 **Precision Latency Testing** - Real-time WebSocket-based ping measurement with millisecond accuracy
- 📥 **Adaptive Download Testing** - Multi-threaded parallel connections with intelligent stabilization detection
- 📤 **Dynamic Upload Testing** - Configurable concurrent uploads with real-time progress tracking
- 🌐 **Server Diversity** - Automatic server selection or manual picking from global speedtest infrastructure
- 👤 **Dual-Mode Authentication** - Seamless support for registered users and anonymous testing

### User Experience
- 🎨 **Color-Coded Results** - Intuitive visual feedback with performance-based color indicators:
  - 🟢 **Green** (1-10ms / Excellent) - Premium connectivity
  - 🔵 **Cyan** (10-60ms / Good) - Solid performance
  - 🟡 **Yellow** (60-120ms / Acceptable) - Adequate connectivity
  - 🔴 **Red** (120+ms / Poor) - Degraded performance
- 📈 **Real-Time Progress Visualization** - tqdm-powered progress bars for all test phases
- ⚙️ **Configurable Concurrency** - Adjust parallel connection count (1-64) for optimal performance
- 🔒 **Secure Authentication** - Cookie-based session management with credential caching

### Developer-Friendly
- ⚡ **Quick Mode** - Launch full speedtest with `--q` flag for automation and scripting
- 🔌 **Modular Architecture** - Clean separation of concerns with specialized test classes
- 📍 **Comprehensive Logging** - Detailed error handling and user feedback
- 🚀 **Asynchronous Operations** - Non-blocking ping monitoring concurrent with speed tests

---

## 🔧 System Requirements

### Minimum Requirements
| Component | Specification |
|-----------|--------------|
| **Python** | 3.7 or higher |
| **Memory** | 256 MB RAM |
| **Network** | Stable internet connection |
| **OS** | Windows, macOS, Linux |

### Recommended Setup
| Component | Recommendation |
|-----------|----------------|
| **Python** | 3.9+ for optimal performance |
| **Memory** | 1 GB RAM or higher |
| **Bandwidth** | Minimum 1 Mbps for testing |
| **OS** | Latest stable version |

---

## 📦 Installation

### Option 1: Install from PyPI (Recommended)

The easiest way - install directly from PyPI:
```bash
pip install adv-speedtest-cli
```

Then run:
```bash
adv-speedtest-cli
```

### Option 2: Install from Source

**Prerequisites:**
Ensure Python 3.7+ is installed:
```bash
python --version
```

**Step 1: Clone Repository**
```bash
git clone https://github.com/shakilofficial0/adv-speedtest-cli.git
cd adv-speedtest-cli
```

**Step 2: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 3: Verify Installation**
```bash
python speedtest.py --help
```

---

## ⚡ Quick Start

### Using PyPI Installation

**Quick Mode** - Execute immediate speedtest with default settings:
```bash
adv-speedtest-cli --q
```

**Interactive Mode** - Launch the full-featured menu:
```bash
adv-speedtest-cli
```

### Alternative Commands

You can also use these equivalent commands:
```bash
advanced-speedtest
speedtest-cli
```

### Using Source Installation

**Quick Mode:**
```bash
python speedtest.py --q
```

**Interactive Mode:**
```bash
python speedtest.py
```

### Expected Output
```
✓ Ping Test Complete!
  Min: 8.62 ms (Very Good)
  Max: 9.42 ms (Very Good)
  Avg: 9.00 ms (Very Good)
  Median: 9.08 ms (Very Good)
  Samples: 10

✓ Download Complete!
  Speed: 276.20 Mbps
  Duration: 10.45s
  Downloaded: 250.00 MB

✓ Upload Complete!
  Speed: 255.96 Mbps
  Measurement Window: 3-12s (9s)
  Uploaded: 40.00 MB

SPEED TEST RESULTS
==================================================
✓ Test Complete!
  Ping: 9.00 ms (Very Good)
  Download: 276.20 Mbps
  Upload: 255.96 Mbps
==================================================
```

---

## 🎯 Usage Guide

### Main Menu Navigation
1. **Login** - Authenticate with speedtest.net account (or skip for anonymous)
2. **Select Server** - Choose testing server or use auto-pick
3. **Run SpeedTest** - Execute comprehensive network analysis
4. **Run SpeedTest and Share** - Test and generate shareable result link
5. **Settings** - Configure test parameters
6. **Logout** - Clear authentication and session data

### Settings Configuration

#### Speedtest Mode
- **Single Connection** - Conservative testing with 1 parallel connection
- **Multiple Connections** - Aggressive testing with configurable worker threads

#### Parallel Connections
- **Range**: 1 to 64 connections
- **Default**: 8 connections
- **Impact**: Higher connections = more aggressive network utilization

### Server Selection
```
0. Auto Pick (Nearest Server)
1-N. Manual Server Selection
Search Server Option (ISP/Location/Name)
```

---

## 🔬 Advanced Configuration

### Ping Test Protocol
```
Duration: 10 sequential packets
Timeout: 5 seconds per packet
Protocol: WebSocket (WSS)
Sampling: Real-time measurement
```

### Download Test Strategy
```
Duration: 10-30 seconds (adaptive)
File Size: 250 MB
Skip Window: First 3 seconds (ramp-up)
Measurement: Overall bytes / total duration
Connections: Configurable (1-64)
```

### Upload Test Strategy
```
Total Duration: 15 seconds fixed
Measurement Window: 3-12 seconds
Data Size: 40 MB per test
Skip Window: First 3 seconds
Measurement: Bytes in window / 9 seconds
Connections: Configurable (1-64)
```

---

## 📊 Performance Metrics

### Speed Calculation Formula
```
Speed (Mbps) = (Total Bytes × 8) / (Duration × 1,000,000)
```

### Accuracy Factors
- **Stabilization**: 3-second warm-up period to reach peak throughput
- **Duration**: Longer tests provide more stable results
- **Concurrency**: Multiple connections reduce per-connection overhead
- **Network Conditions**: Real-time network state directly impacts measurements

### Quality Indicators
| Metric | Threshold | Status |
|--------|-----------|--------|
| **Ping** | ≤10ms | Exceptional |
| | 10-60ms | Excellent |
| | 60-120ms | Good |
| | >120ms | Needs Improvement |
| **Download** | >100 Mbps | Fiber/5G |
| | 25-100 Mbps | Broadband |
| | <25 Mbps | Standard |
| **Upload** | >20 Mbps | Professional |
| | 5-20 Mbps | Standard |
| | <5 Mbps | Limited |

---

## 🏗️ Architecture

### Class Structure

#### `Config`
Static configuration and API endpoints management

#### `CookieManager`
Persistent session and authentication token storage

#### `LoginManager`
User authentication workflow and credential validation

#### `ServerManager`
Server discovery, filtering, and auto-selection logic

#### `State`
Application state and user session tracking

#### `Display`
Terminal UI rendering and menu presentation

#### `PingTest`
WebSocket-based latency measurement with color coding

#### `DownloadTest`
Adaptive speed measurement with concurrent connection pooling

#### `SpeedTest`
Orchestration layer coordinating all test phases

#### `Application`
Main event loop and menu interaction handler

### Data Flow
```
User Input
    ↓
Authentication (Optional)
    ↓
Server Selection
    ↓
Test Execution (Ping → Download → Upload)
    ↓
Results Aggregation
    ↓
Display & Share (Optional)
```

---

## 📝 Key Technologies

| Technology | Purpose | Version |
|-----------|---------|---------|
| **Python** | Core language | 3.7+ |
| **asyncio** | Asynchronous operations | Built-in |
| **websockets** | Real-time ping protocol | Latest |
| **requests** | HTTP/HTTPS communication | Latest |
| **tqdm** | Progress visualization | Latest |
| **colorama** | Cross-platform colored output | Latest |

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/enhancement`
3. **Implement** changes with clear commits
4. **Test** thoroughly before submission
5. **Submit** Pull Request with detailed description

---

## 📞 Support

### Getting Help
- 📧 **Email**: shakilofficial0@gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/shakilofficial0/adv-speedtest-cli/issues)
- 💡 **Discussions**: [GitHub Discussions](https://github.com/shakilofficial0/adv-speedtest-cli/discussions)

### Troubleshooting

#### Connection Failed
```bash
# Verify internet connectivity
ping google.com

# Check firewall/proxy settings
# Disable VPN if active
```

#### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify Python version
python --version
```

#### Timeout Issues
```bash
# Check network stability
# Reduce parallel connections in Settings
# Try with --q (quick mode)
```

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- **Speedtest.net** - Infrastructure and testing methodology
- **Python Community** - Excellent standard library and ecosystem
- **Open Source Contributors** - All dependencies and inspirations

---

## 📊 Project Statistics

```
Language:       Python 3.7+
Lines of Code:  2,600+
Test Coverage:  Comprehensive
Platform:       Cross-Platform (Windows, macOS, Linux)
Active:         ✅ Under Active Development
```

---

## 🔐 Security & Privacy

- ✅ **HTTPS Only** - All connections encrypted
- ✅ **Anonymous Support** - Test without account
- ✅ **Local Caching** - Credentials stored locally only
- ✅ **No Tracking** - Privacy-focused design
- ✅ **Open Source** - Code transparency for security auditing

---

## 🎯 Roadmap

### Upcoming Features
- [ ] **JSON Export** - Save results in structured format
- [ ] **Historical Analysis** - Track speed trends over time
- [ ] **Save and Share Result** - Auto Save and Share result in the speedtest

---

## ⭐ Show Your Support

If this project helped you, please consider:
- ⭐ **Star** this repository
- 🍴 **Fork** and contribute
- 🐛 **Report** issues and suggestions
- 📢 **Share** with your network

---

**Created with ❤️ by [Shakil Ahmed](https://github.com/shakilofficial0)**

#NetworkTesting #SpeedTest #Python #CLI #CrossPlatform #OpenSource #Networking #DevTools

---

*Last Updated: January 2026*
*Version: 1.0.0*
