#include "common/graph_attributes.h"

#include <functional>
#include <utility>
#include <ranges>
#include <format>
using namespace std;
using namespace graph_layout;

const string AttributeRankDir::TOP_TO_BOTTOM = "tb";
const string AttributeRankDir::BOTTOM_TO_TOP = "bt";
const string AttributeRankDir::LEFT_TO_RIGHT = "lr";
const string AttributeRankDir::RIGHT_TO_LEFT = "rl";

const string AttributeShape::NONE = "none";
const string AttributeShape::CIRCLE = "circle";
const string AttributeShape::DOUBLE_CIRCLE = "doublecircle";
const string AttributeShape::ELLIPSE = "ellipse";
const string AttributeShape::RECT = "rect";
const string AttributeShape::RECORD = "record";

const string AttributeSplines::LINE = "line";
const string AttributeSplines::SPLINE = "spline";

const string AttributeArrowShape::NONE = "none";
const string AttributeArrowShape::NORMAL = "normal";
const string AttributeArrowShape::EMPTY = "empty";

const string Attributes::MONOSPACE_FONT_FAMILY = R"(ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace)";

unordered_map<string_view, string> Attributes::DEFAULT_GRAPH_ATTRIBUTE_VALUES = {
    {ATTR_KEY_RANK_DIR, AttributeRankDir::TOP_TO_BOTTOM},
    {ATTR_KEY_BG_COLOR, "none"},
    {ATTR_KEY_FONT_NAME, "Times,serif"},
    {ATTR_KEY_FONT_SIZE, "14"},
    {ATTR_KEY_COLOR, "black"},
    {ATTR_KEY_FILL_COLOR, "none"},
    {ATTR_KEY_FONT_COLOR, "black"},
};

unordered_map<string_view, string> Attributes::DEFAULT_VERTEX_ATTRIBUTE_VALUES = {
    {ATTR_KEY_LABEL, ""},
    {ATTR_KEY_SHAPE, AttributeShape::CIRCLE},
};

unordered_map<string_view, string> Attributes::DEFAULT_EDGE_ATTRIBUTE_VALUES = {
    {ATTR_KEY_LABEL, ""},
    {ATTR_KEY_TAIL_LABEL, ""},
    {ATTR_KEY_HEAD_LABEL, ""},
    {ATTR_KEY_LABEL_DISTANCE, "2.0"},
    {ATTR_KEY_SPLINES, "line"},
    {ATTR_KEY_ARROW_HEAD, AttributeArrowShape::NORMAL},
    {ATTR_KEY_ARROW_TAIL, AttributeArrowShape::NONE},
};

Attribute::Attribute() = default;

Attribute::Attribute(const string& value) : _raw(value) {
}

void Attribute::set(const string &value) {
    _raw = value;
}

const string& Attribute::value() const {
    return _raw;
}

string Attributes::graphAttributes(const string_view& key) const {
    if (const auto it = _graphAttributes.find(key); it != _graphAttributes.end()) {
        return it->second;
    }
    return DEFAULT_GRAPH_ATTRIBUTE_VALUES[key];
}

void Attributes::setGraphAttributes(const string_view& key, const string &value) {
    _graphAttributes[key] = value;
}

void Attributes::setGraphAttributes(const unordered_map<string_view, string>& attributes) {
    _graphAttributes = attributes;
}

string Attributes::vertexAttributes(const int u, const string_view& key) const {
    if (const auto vIt = _vertexAttributes.find(u); vIt != _vertexAttributes.end()) {
        if (const auto it = vIt->second.find(key); it != vIt->second.end()) {
            return it->second;
        }
    }
    if (const auto it = _vertexDefaultAttributes.find(key); it != _vertexDefaultAttributes.end()) {
        return it->second;
    }
    if (const auto it = DEFAULT_VERTEX_ATTRIBUTE_VALUES.find(key); it != DEFAULT_VERTEX_ATTRIBUTE_VALUES.end()) {
        return it->second;
    }
    return graphAttributes(key);
}

void Attributes::setVertexAttributes(const int u, const string_view& key, const string &value) {
    _vertexAttributes[u][key] = value;
}

void Attributes::setVertexAttributes(const int u, const unordered_map<string_view, string>& attributes) {
    _vertexAttributes[u] = attributes;
}

string Attributes::edgeAttributes(const int u, const string_view& key) const {
    if (const auto eIt = _edgeAttributes.find(u); eIt != _edgeAttributes.end()) {
        if (const auto it = eIt->second.find(key); it != eIt->second.end()) {
            return it->second;
        }
    }
    if (const auto it = _edgeDefaultAttributes.find(key); it != _edgeDefaultAttributes.end()) {
        return it->second;
    }
    if (const auto it = DEFAULT_EDGE_ATTRIBUTE_VALUES.find(key); it != DEFAULT_EDGE_ATTRIBUTE_VALUES.end()) {
        return it->second;
    }
    return graphAttributes(key);
}

void Attributes::setEdgeAttributes(const int u, const string_view& key, const string &value) {
    _edgeAttributes[u][key] = value;
}

void Attributes::setEdgeAttributes(const int u, const string_view& key, const double value) {
    _edgeAttributes[u][key] = format("{}", value);
}

void Attributes::setEdgeAttributes(const int u, const unordered_map<string_view, string>& mapping) {
    _edgeAttributes[u] = mapping;
}

void Attributes::transferEdgeAttributes(const int u, const int v) {
    if (_edgeAttributes.contains(u)) {
        _edgeAttributes[v] = _edgeAttributes[u];
    }
}

string Attributes::rankDir() const {
    return graphAttributes(ATTR_KEY_RANK_DIR);
}

void Attributes::setRankDir(const string &value) {
    setGraphAttributes(ATTR_KEY_RANK_DIR, value);
}

void Attributes::setVertexDefaultShape(const string& value) {
    _vertexDefaultAttributes[ATTR_KEY_SHAPE] = value;
}

void Attributes::setEdgeDefaultSplines(const string& value) {
    _edgeDefaultAttributes[ATTR_KEY_SPLINES] = value;
}

void Attributes::setVertexDefaultMonospace() {
    _vertexDefaultAttributes[ATTR_KEY_FONT_NAME] = MONOSPACE_FONT_FAMILY;
}

void Attributes::setEdgeDefaultMonospace() {
    _edgeDefaultAttributes[ATTR_KEY_FONT_NAME] = MONOSPACE_FONT_FAMILY;
}

void Attributes::setVertexShape(const int u, const string &value) {
    setVertexAttributes(u, ATTR_KEY_SHAPE, value);
}

void Attributes::setEdgeSplines(const int edgeId, const string& value) {
    setEdgeAttributes(edgeId, ATTR_KEY_SPLINES, value);
}

void Attributes::setEdgeTailLabel(const int edgeId, const string& label) {
    setEdgeAttributes(edgeId, ATTR_KEY_TAIL_LABEL, label);
}

void Attributes::setEdgeHeadLabel(const int edgeId, const string& label) {
    setEdgeAttributes(edgeId, ATTR_KEY_HEAD_LABEL, label);
}

void Attributes::setEdgeLabelDistance(const int edgeId, const double scale) {
    setEdgeAttributes(edgeId, ATTR_KEY_LABEL_DISTANCE, scale);
}

void Attributes::setEdgeDefaultArrowHead(const string& value) {
    _edgeDefaultAttributes[ATTR_KEY_ARROW_HEAD] = value;
}

void Attributes::setEdgeDefaultArrowTail(const string& value) {
    _edgeDefaultAttributes[ATTR_KEY_ARROW_TAIL] = value;
}

void Attributes::setEdgeArrowHead(const int edgeId, const string& value) {
    setEdgeAttributes(edgeId, ATTR_KEY_ARROW_HEAD, value);
}

void Attributes::setEdgeArrowTail(const int edgeId, const string& value) {
    setEdgeAttributes(edgeId, ATTR_KEY_ARROW_TAIL, value);
}

void Attributes::setVertexDefaultColor(const string& value) {
    _vertexDefaultAttributes[ATTR_KEY_COLOR] = value;
}

void Attributes::setVertexDefaultFillColor(const string& value) {
    _vertexDefaultAttributes[ATTR_KEY_FILL_COLOR] = value;
}

void Attributes::setVertexDefaultFontColor(const string& value) {
    _vertexDefaultAttributes[ATTR_KEY_FONT_COLOR] = value;
}

void Attributes::setEdgeDefaultColor(const string& value) {
    _edgeDefaultAttributes[ATTR_KEY_COLOR] = value;
}

void Attributes::setEdgeDefaultFontColor(const string& value) {
    _edgeDefaultAttributes[ATTR_KEY_FONT_COLOR] = value;
}

void Attributes::setVertexColor(const int u, const string& value) {
    setVertexAttributes(u, ATTR_KEY_COLOR, value);
}

void Attributes::setVertexFillColor(const int u, const string& value) {
    setVertexAttributes(u, ATTR_KEY_FILL_COLOR, value);
}

void Attributes::setVertexFontColor(const int u, const string& value) {
    setVertexAttributes(u, ATTR_KEY_FONT_COLOR, value);
}

void Attributes::setEdgeColor(const int edgeId, const string& value) {
    setEdgeAttributes(edgeId, ATTR_KEY_COLOR, value);
}

void Attributes::setEdgeFontColor(const int edgeId, const string& value) {
    setEdgeAttributes(edgeId, ATTR_KEY_FONT_COLOR, value);
}
