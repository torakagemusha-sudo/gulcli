/** GUL v2.1 — Config loading for CLI. */
#pragma once

#include "gul/dataset.hpp"
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace gul {

struct CliConfig {
    std::string config_path;
    DatasetConfig dataset;
    bool oneshot = false;
    bool training_stream = false;   // -T: stream dataset to stdout
    bool deepgul = false;           // -deepgul
    std::string listen_addr;        // -L 127.0.0.1/1234 => host=127.0.0.1, port=1234
    std::uint16_t listen_port = 0;
    std::size_t limit_samples = 0;   // -n N
    bool random_order = false;      // -random
    std::size_t block_size = 64;    // -block N
    std::uint64_t seed = 0;         // from config or -seed
    bool validate_only = false;
    std::string validate_file;
    bool infer_only = false;
    std::string infer_file;
    bool help = false;
    bool version = false;
    std::vector<std::string> positional;
};

/** Parse -L 127.0.0.1/1234 or 127.0.0.1:1234 into host and port. */
bool parse_listen(const std::string& spec, std::string& host, std::uint16_t& port);

/** Load config from JSON file (optional keys: seed, block_size, max_samples, random_order). */
bool load_config(const std::string& path, CliConfig& out);

/** Parse argv into CliConfig. */
CliConfig parse_args(int argc, char* argv[]);

} // namespace gul
