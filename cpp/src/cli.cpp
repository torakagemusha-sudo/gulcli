/** GUL v2.1 — CLI: stream dataset (-oneshot -T, -deepgul -L host/port), -config, validate, infer. */
#include "gul/config.hpp"
#include "gul/dataset.hpp"
#include "gul/runtime_io.hpp"
#include <iostream>
#include <string>
#include <cstring>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#define GUL_SOCKET SOCKET
#define GUL_INVALID_SOCKET INVALID_SOCKET
#define GUL_CLOSE_SOCKET(s) closesocket(s)
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#define GUL_SOCKET int
#define GUL_INVALID_SOCKET (-1)
#define GUL_CLOSE_SOCKET(s) close(s)
#endif

namespace {

void print_help() {
    std::cout << "GUL v2.1 — Governed Uncertainty Logic CLI\n"
                 "Usage: gul [options] [command] [args]\n\n"
                 "Dataset streaming (ML training):\n"
                 "  -oneshot              Single batch mode\n"
                 "  -T                    Stream dataset to stdout (training format, JSON Lines)\n"
                 "  -deepgul              Enable deep GUL streaming\n"
                 "  -L <host/port>         Stream to TCP (e.g. -L 127.0.0.1/1234 or -L 127.0.0.1:1234)\n"
                 "  -n, --limit <N>       Limit to N samples\n"
                 "  -random               Randomize sample order\n"
                 "  -block <N>            Block size for streaming (default 64)\n"
                 "  -seed <N>             RNG seed (0 = random)\n"
                 "  --scenario <mode>     balanced | adversarial\n"
                 "  --spec <path>         GUL spec for provenance and baseline inference\n"
                 "  --stats               Emit scenario/decision distribution to stderr\n\n"
                 "Config:\n"
                 "  -config, --config <path>  Load config file (key=value or key: value)\n\n"
                 "Commands:\n"
                 "  validate [file]        Validate GUL spec file\n"
                 "  infer [file]          Run inference on expression file\n\n"
                 "Other:\n"
                 "  -h, --help             Show this help\n"
                 "  -v, --version         Show version\n\n"
                 "Examples:\n"
                 "  gul -oneshot -T                    # Stream one batch to stdout\n"
                 "  gul -deepgul -L 127.0.0.1/1234    # Stream dataset to TCP listener\n"
                 "  gul -config train.conf -T -n 1000 # Config + stream 1000 samples to stdout\n"
                 "  gul -config train.conf -random -block 32 -T\n";
}

void print_version() {
    std::cout << "GUL 2.2.0\n";
}

int stream_to_stdout(const gul::CliConfig& c) {
    gul::DatasetConfig dconfig = c.dataset;
    dconfig.block_size = c.block_size;
    dconfig.random_order = c.random_order;
    if (c.seed) dconfig.seed = c.seed;
    if (!c.scenario_mode.empty()) dconfig.scenario_mode = c.scenario_mode;
    dconfig.emit_stats = c.emit_stats;
    if (!c.spec_path.empty()) dconfig.spec_path = c.spec_path;
    gul::DatasetGenerator gen(dconfig);
    std::size_t limit = c.limit_samples ? c.limit_samples : c.dataset.max_samples;
    int rc = 0;
    gen.stream_to(std::cout, limit);
    if (c.emit_stats)
        std::cerr << gen.stats().to_json() << "\n";
    return rc;
}

int stream_to_tcp(const gul::CliConfig& c) {
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        std::cerr << "WSAStartup failed\n";
        return 1;
    }
#endif
    GUL_SOCKET fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd == GUL_INVALID_SOCKET) {
        std::cerr << "socket failed\n";
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }
    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(static_cast<unsigned short>(c.listen_port));
#ifdef _WIN32
    addr.sin_addr.s_addr = inet_addr(c.listen_addr.c_str());
#else
    inet_pton(AF_INET, c.listen_addr.c_str(), &addr.sin_addr);
#endif
    if (connect(fd, reinterpret_cast<struct sockaddr*>(&addr), sizeof(addr)) < 0) {
        std::cerr << "connect to " << c.listen_addr << ":" << c.listen_port << " failed\n";
        GUL_CLOSE_SOCKET(fd);
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }
    gul::DatasetConfig dconfig = c.dataset;
    dconfig.block_size = c.block_size;
    dconfig.random_order = c.random_order;
    if (c.seed) dconfig.seed = c.seed;
    if (!c.scenario_mode.empty()) dconfig.scenario_mode = c.scenario_mode;
    dconfig.emit_stats = c.emit_stats;
    if (!c.spec_path.empty()) dconfig.spec_path = c.spec_path;
    gul::DatasetGenerator gen(dconfig);
    std::size_t limit = c.limit_samples ? c.limit_samples : 0;
    gul::DatasetStreamer::stream(gen, [fd](const std::string& line) {
#ifdef _WIN32
        send(fd, line.data(), static_cast<int>(line.size()), 0);
#else
        send(fd, line.data(), line.size(), 0);
#endif
    }, limit, c.random_order);
    if (c.emit_stats)
        std::cerr << gen.stats().to_json() << "\n";
    GUL_CLOSE_SOCKET(fd);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}

int cmd_validate(const gul::CliConfig& c) {
    if (c.validate_file.empty()) {
        std::cerr << "validate: missing file path\n";
        return 1;
    }
    try {
        gul::ValidationResult result = gul::validate_spec_file(c.validate_file);
        if (c.format_json) {
            std::cout << result.to_json() << "\n";
        } else {
            std::cout << (result.ok ? "OK" : "INVALID") << ": " << result.source << "\n";
            for (const auto& msg : result.errors)
                std::cout << "[" << msg.severity << "] " << msg.code << " " << msg.path << ": " << msg.message << "\n";
        }
        return result.ok ? 0 : 1;
    } catch (const std::exception& ex) {
        std::cerr << "validate error: " << ex.what() << "\n";
        return 1;
    }
}

int cmd_infer(const gul::CliConfig& c) {
    if (c.infer_file.empty()) {
        std::cerr << "infer: missing file path\n";
        return 1;
    }
    try {
        gul::InferenceResult result = gul::infer_spec_file(c.infer_file, c.infer_trace, c.facts_file);
        if (c.format_json) {
            std::cout << result.to_json() << "\n";
        } else {
            std::cout << "decision=" << result.decision << "\n";
            std::cout << "confidence=" << result.confidence << "\n";
        }
        return 0;
    } catch (const std::exception& ex) {
        if (c.format_json) {
            std::cout << "{\"schema\":\"gul.inference.result/1\",\"version\":\"2.2.0\",\"error\":\""
                      << ex.what() << "\"}\n";
        } else {
            std::cerr << "infer error: " << ex.what() << "\n";
        }
        return 1;
    }
}

} // namespace

int run_cli(int argc, char* argv[]) {
    gul::CliConfig c = gul::parse_args(argc, argv);

    if (c.help) { print_help(); return 0; }
    if (c.version) { print_version(); return 0; }
    if (c.validate_only) return cmd_validate(c);
    if (c.infer_only) return cmd_infer(c);

    if (c.oneshot || c.training_stream) {
        if (!c.listen_addr.empty() && c.listen_port != 0)
            return stream_to_tcp(c);
        return stream_to_stdout(c);
    }

    if (c.deepgul && !c.listen_addr.empty() && c.listen_port != 0)
        return stream_to_tcp(c);

    print_help();
    return 0;
}
