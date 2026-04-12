#include "gul/jurisdiction.hpp"

namespace gul {

bool JurisdictionId::is_sub_jurisdiction(const JurisdictionId& other) const {
    if (fully_qualified_name() == other.fully_qualified_name()) return true;
    if (!parent) return false;
    return parent->is_sub_jurisdiction(other);
}

int JurisdictionId::depth() const {
    if (!parent) return 0;
    return 1 + parent->depth();
}

std::string JurisdictionId::fully_qualified_name() const {
    if (!parent) return name;
    return parent->fully_qualified_name() + "." + name;
}

} // namespace gul
