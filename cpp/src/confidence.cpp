#include "gul/confidence.hpp"
#include <string>

namespace gul {

Confidence::Confidence(double v) : value_(v) {
    if (value_ < 0.0 || value_ > 1.0)
        throw std::invalid_argument("Confidence must be in [0,1]");
}

Confidence Confidence::zero() { return Confidence(0.0); }
Confidence Confidence::one() { return Confidence(1.0); }

Confidence Confidence::from_probability(double p) {
    if (p < 0.0) p = 0.0;
    if (p > 1.0) p = 1.0;
    return Confidence(p);
}

Confidence Confidence::complement() const {
    return Confidence(1.0 - value_);
}

bool Confidence::is_certain(double threshold) const {
    return value_ >= threshold;
}

bool Confidence::is_uncertain(double threshold) const {
    return value_ < threshold;
}

Confidence ConfidenceOps::combine_union(Confidence a, Confidence b) {
    return Confidence(std::max(a.value(), b.value()));
}

Confidence ConfidenceOps::combine_intersection(Confidence a, Confidence b) {
    return Confidence(std::min(a.value(), b.value()));
}

Confidence ConfidenceOps::combine_sequential(Confidence a, Confidence b) {
    return Confidence(a.value() * b.value());
}

Confidence ConfidenceOps::combine_parallel(Confidence a, Confidence b) {
    return Confidence(a.value() + b.value() - a.value() * b.value());
}

Confidence ConfidenceOps::weighted_average(const Confidence* begin, const Confidence* end,
                                           const double* weights) {
    if (begin == end) return Confidence::one();
    double sum = 0.0, total_w = 0.0;
    size_t i = 0;
    for (const Confidence* p = begin; p != end; ++p, ++i) {
        double w = weights ? weights[i] : 1.0;
        sum += p->value() * w;
        total_w += w;
    }
    if (total_w == 0.0) return Confidence::one();
    return Confidence(sum / total_w);
}

Confidence ConfidenceOps::aggregate(const Confidence* begin, const Confidence* end,
                                     const char* method) {
    if (begin == end) return Confidence::one();
    if (std::string(method) == "min") {
        double m = begin->value();
        for (const Confidence* p = begin + 1; p != end; ++p)
            if (p->value() < m) m = p->value();
        return Confidence(m);
    }
    if (std::string(method) == "max") {
        double m = begin->value();
        for (const Confidence* p = begin + 1; p != end; ++p)
            if (p->value() > m) m = p->value();
        return Confidence(m);
    }
    if (std::string(method) == "product") {
        Confidence r = Confidence::one();
        for (const Confidence* p = begin; p != end; ++p)
            r = combine_sequential(r, *p);
        return r;
    }
    if (std::string(method) == "parallel") {
        Confidence r = Confidence::zero();
        for (const Confidence* p = begin; p != end; ++p)
            r = combine_parallel(r, *p);
        return r;
    }
    if (std::string(method) == "average")
        return weighted_average(begin, end, nullptr);
    throw std::invalid_argument("Unknown aggregation method");
}

} // namespace gul
