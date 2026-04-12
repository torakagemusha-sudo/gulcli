/** GUL v2.1 — Dataset generation for ML training (streaming, blocks, random). */
#pragma once

#include "gul/confidence.hpp"
#include "gul/decision.hpp"
#include "gul/entity.hpp"
#include "gul/predicate.hpp"
#include "gul/policy_expr.hpp"
#include <cstddef>
#include <cstdint>
#include <functional>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace gul {

struct DatasetConfig {
    std::size_t max_samples = 0;      // 0 = unbounded
    std::size_t block_size = 64;      // samples per block when streaming
    bool random_order = false;
    std::uint64_t seed = 0;           // 0 = random device
    bool json_lines = true;           // one JSON object per line (NDJSON)
};

/** One training sample: inputs (entity, predicate, context) + label (decision, confidence). */
struct DatasetSample {
    Entity entity;
    Predicate predicate;
    double context_confidence = 1.0;
    Decision decision;
    Confidence confidence;
    std::vector<std::string> evidence;

    std::string to_json_line() const;
};

/** Generate GUL-compatible samples for training. */
class DatasetGenerator {
public:
    explicit DatasetGenerator(DatasetConfig config = {});

    void set_seed(std::uint64_t seed);
    /** Generate one sample (deterministic or random per config). */
    DatasetSample next_sample();
    /** Write samples to stream in JSON Lines format. */
    void stream_to(std::ostream& out, std::size_t max_samples = 0);
    /** Write one block of block_size samples to stream. */
    void stream_block_to(std::ostream& out);
    /** Shuffle a vector of samples (for -random). */
    void shuffle(std::vector<DatasetSample>& samples);

private:
    DatasetConfig config_;
    std::mt19937 rng_;
    std::size_t sample_count_ = 0;
    std::vector<Entity> entity_pool_;
    std::vector<Predicate> predicate_pool_;
    void ensure_pools();
};

/** Stream dataset over TCP (for -deepgul -L host/port). */
class DatasetStreamer {
public:
    using WriteFunc = std::function<void(const std::string& line)>;

    /** Stream samples to a custom writer (e.g. socket). */
    static void stream(DatasetGenerator& gen, WriteFunc write,
        std::size_t max_samples = 0, bool random_order = false);
};

} // namespace gul
