#include "gul/dataset.hpp"
#include <algorithm>
#include <cstdio>
#include <random>
#include <sstream>

namespace gul {

static std::string escape_json(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 8);
    for (unsigned char c : s) {
        if (c == '"') out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else if (c < 32) { char buf[8]; snprintf(buf, sizeof(buf), "\\u%04x", c); out += buf; }
        else out += c;
    }
    return out;
}

std::string DatasetSample::to_json_line() const {
    std::ostringstream o;
    o << "{";
    o << "\"entity\":{\"kind\":\"" << escape_json(entity.kind) << "\",\"id\":\"" << escape_json(entity.id) << "\"}";
    o << ",\"predicate\":{\"tag\":\"" << escape_json(predicate.tag) << "\"";
    if (!predicate.args.empty()) {
        o << ",\"args\":[";
        for (size_t i = 0; i < predicate.args.size(); ++i) {
            if (i) o << ",";
            o << "\"" << escape_json(predicate.args[i]) << "\"";
        }
        o << "]";
    }
    o << "}";
    o << ",\"context_confidence\":" << context_confidence;
    o << ",\"decision\":\"" << to_string(decision) << "\"";
    o << ",\"confidence\":" << confidence.value();
    if (!evidence.empty()) {
        o << ",\"evidence\":[";
        for (size_t i = 0; i < evidence.size(); ++i) {
            if (i) o << ",";
            o << "\"" << escape_json(evidence[i]) << "\"";
        }
        o << "]";
    }
    o << "}";
    return o.str();
}

DatasetGenerator::DatasetGenerator(DatasetConfig config)
    : config_(std::move(config)) {
    if (config_.seed != 0)
        rng_.seed(static_cast<std::mt19937::result_type>(config_.seed));
    else
        rng_.seed(std::random_device{}());
    ensure_pools();
}

void DatasetGenerator::set_seed(std::uint64_t seed) {
    rng_.seed(static_cast<std::mt19937::result_type>(seed));
}

void DatasetGenerator::ensure_pools() {
    if (!entity_pool_.empty()) return;
    entity_pool_ = {
        Entity("agent", "alice"),
        Entity("agent", "bob"),
        Entity("resource", "doc1"),
        Entity("resource", "doc2"),
        Entity("context", "ctx1"),
        Entity("context", "ctx2"),
        Entity("policy", "p1"),
    };
    predicate_pool_ = {
        belongs_to(Entity("agent", "alice"), Entity("resource", "doc1")),
        has_role(Entity("agent", "alice"), "admin"),
        has_role(Entity("agent", "bob"), "viewer"),
        has_attribute(Entity("resource", "doc1"), "level", "secret"),
        in_context(Entity("agent", "alice"), Entity("context", "ctx1")),
        custom("custom_rule_1"),
        custom("custom_rule_2"),
    };
}

DatasetSample DatasetGenerator::next_sample() {
    ensure_pools();
    std::uniform_int_distribution<size_t> ed(0, entity_pool_.size() - 1);
    std::uniform_int_distribution<size_t> pd(0, predicate_pool_.size() - 1);
    std::uniform_real_distribution<double> conf(0.3, 1.0);
    std::uniform_int_distribution<int> dec(0, 3);

    Entity e = entity_pool_[ed(rng_)];
    Predicate p = predicate_pool_[pd(rng_)];
    double c = conf(rng_);
    Decision d = static_cast<Decision>(dec(rng_));
    Confidence conf_val(c);
    std::vector<std::string> evidence = { "gen_" + std::to_string(sample_count_) };
    sample_count_++;

    return DatasetSample{ e, p, c, d, conf_val, evidence };
}

void DatasetGenerator::stream_to(std::ostream& out, std::size_t max_samples) {
    std::size_t limit = max_samples ? max_samples : config_.max_samples;
    std::vector<DatasetSample> block;
    for (std::size_t n = 0; !limit || n < limit; ++n) {
        block.push_back(next_sample());
        if (block.size() >= config_.block_size) {
            if (config_.random_order) shuffle(block);
            for (const auto& s : block) out << s.to_json_line() << "\n";
            block.clear();
        }
    }
    if (config_.random_order) shuffle(block);
    for (const auto& s : block) out << s.to_json_line() << "\n";
}

void DatasetGenerator::stream_block_to(std::ostream& out) {
    std::vector<DatasetSample> block;
    for (std::size_t i = 0; i < config_.block_size; ++i)
        block.push_back(next_sample());
    if (config_.random_order) shuffle(block);
    for (const auto& s : block) out << s.to_json_line() << "\n";
}

void DatasetGenerator::shuffle(std::vector<DatasetSample>& samples) {
    std::shuffle(samples.begin(), samples.end(), rng_);
}

void DatasetStreamer::stream(DatasetGenerator& gen, WriteFunc write,
    std::size_t max_samples, bool random_order) {
    std::size_t n = 0;
    while (!max_samples || n < max_samples) {
        auto s = gen.next_sample();
        write(s.to_json_line() + "\n");
        ++n;
    }
}

} // namespace gul
