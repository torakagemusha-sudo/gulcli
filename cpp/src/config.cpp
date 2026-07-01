#include "gul/config.hpp"
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <cstring>
#include <iostream>

namespace gul {

bool parse_listen(const std::string& spec, std::string& host, std::uint16_t& port) {
    size_t sep = spec.find('/');
    if (sep == std::string::npos) sep = spec.find(':');
    if (sep == std::string::npos) return false;
    host = spec.substr(0, sep);
    port = static_cast<std::uint16_t>(std::stoul(spec.substr(sep + 1)));
    return true;
}

bool load_config(const std::string& path, CliConfig& out) {
    std::ifstream f(path);
    if (!f) return false;
    std::string line;
    while (std::getline(f, line)) {
        size_t i = 0;
        while (i < line.size() && (line[i] == ' ' || line[i] == '\t')) ++i;
        if (i >= line.size() || line[i] == '#') continue;
        size_t eq = line.find('=', i);
        if (eq == std::string::npos) eq = line.find(':', i);
        if (eq == std::string::npos) continue;
        std::string key;
        while (i < eq && (line[i] == ' ' || line[i] == '\t')) ++i;
        size_t key_end = eq;
        while (key_end > i && (line[key_end - 1] == ' ' || line[key_end - 1] == '\t')) --key_end;
        key = line.substr(i, key_end - i);
        size_t val_start = eq + 1;
        while (val_start < line.size() && (line[val_start] == ' ' || line[val_start] == '\t' || line[val_start] == ':' || line[val_start] == '=')) ++val_start;
        std::string val = line.substr(val_start);
        while (!val.empty() && (val.back() == ' ' || val.back() == '\t' || val.back() == '\r')) val.pop_back();
        if (key == "seed") {
            out.dataset.seed = std::stoull(val);
            out.seed = out.dataset.seed;
        } else if (key == "block_size") {
            out.dataset.block_size = std::stoull(val);
            out.block_size = out.dataset.block_size;
        } else if (key == "max_samples") {
            out.dataset.max_samples = std::stoull(val);
            out.limit_samples = out.dataset.max_samples;
        } else if (key == "random_order") {
            out.dataset.random_order = (val == "true" || val == "1" || val == "yes");
            out.random_order = out.dataset.random_order;
        }
    }
    return true;
}

CliConfig parse_args(int argc, char* argv[]) {
    CliConfig c;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-config" || arg == "--config") {
            if (i + 1 < argc) { c.config_path = argv[++i]; }
            continue;
        }
        if (arg == "-oneshot") { c.oneshot = true; continue; }
        if (arg == "-T") { c.training_stream = true; continue; }
        if (arg == "-deepgul") { c.deepgul = true; continue; }
        if (arg == "-L" || arg == "--listen") {
            if (i + 1 < argc) {
                std::string spec = argv[++i];
                parse_listen(spec, c.listen_addr, c.listen_port);
            }
            continue;
        }
        if (arg == "-n" || arg == "--limit") {
            if (i + 1 < argc) c.limit_samples = std::stoull(argv[++i]);
            continue;
        }
        if (arg == "-random" || arg == "--random") { c.random_order = true; c.dataset.random_order = true; continue; }
        if (arg == "-block" || arg == "--block") {
            if (i + 1 < argc) {
                c.block_size = std::stoull(argv[++i]);
                c.dataset.block_size = c.block_size;
            }
            continue;
        }
        if (arg == "-seed" || arg == "--seed") {
            if (i + 1 < argc) { c.seed = std::stoull(argv[++i]); c.dataset.seed = c.seed; }
            continue;
        }
        if (arg == "validate") {
            c.validate_only = true;
            if (i + 1 < argc && argv[i + 1][0] != '-') c.validate_file = argv[++i];
            while (i + 1 < argc && std::string(argv[i + 1]).rfind("--", 0) == 0) {
                std::string flag = argv[++i];
                if (flag == "--format" && i + 1 < argc) {
                    c.format_json = (std::string(argv[++i]) == "json");
                } else if (flag == "--strict") {
                    // accepted for CLI compatibility; validation already treats issues as errors
                }
            }
            continue;
        }
        if (arg == "infer") {
            c.infer_only = true;
            if (i + 1 < argc && argv[i + 1][0] != '-') c.infer_file = argv[++i];
            while (i + 1 < argc && std::string(argv[i + 1]).rfind("-", 0) == 0) {
                std::string flag = argv[++i];
                if (flag == "--format" && i + 1 < argc) {
                    c.format_json = (std::string(argv[++i]) == "json");
                } else if (flag == "--trace") {
                    c.infer_trace = true;
                }
            }
            continue;
        }
        if (arg == "-h" || arg == "--help") { c.help = true; continue; }
        if (arg == "-v" || arg == "--version") { c.version = true; continue; }
        if (arg[0] != '-') c.positional.push_back(arg);
    }
    if (!c.config_path.empty()) load_config(c.config_path, c);
    if (c.seed) c.dataset.seed = c.seed;
    return c;
}

} // namespace gul
