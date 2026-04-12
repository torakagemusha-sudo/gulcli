/** GUL v2.1 — Confidence lattice. Bounded [0,1] with algebraic operations. */
#pragma once

#include <stdexcept>
#include <cmath>

namespace gul {

class Confidence {
public:
    explicit Confidence(double v);
    static Confidence zero();
    static Confidence one();
    static Confidence from_probability(double p);

    double value() const { return value_; }
    Confidence complement() const;
    bool is_certain(double threshold = 1.0) const;
    bool is_uncertain(double threshold = 0.5) const;

private:
    double value_;
};

class ConfidenceOps {
public:
    static Confidence combine_union(Confidence a, Confidence b);
    static Confidence combine_intersection(Confidence a, Confidence b);
    static Confidence combine_sequential(Confidence a, Confidence b);
    static Confidence combine_parallel(Confidence a, Confidence b);
    static Confidence weighted_average(const Confidence* begin, const Confidence* end,
                                       const double* weights = nullptr);
    static Confidence aggregate(const Confidence* begin, const Confidence* end,
                                const char* method = "min");
};

} // namespace gul
