#ifndef GRAPHLAYOUT_GRAPH_ATTRIBUTES_H
#define GRAPHLAYOUT_GRAPH_ATTRIBUTES_H

#include <string>
#include <unordered_map>

namespace graph_layout {

    constexpr std::string_view ATTR_KEY_BG_COLOR = "bgcolor";
    constexpr std::string_view ATTR_KEY_RANK_DIR = "rankdir";
    constexpr std::string_view ATTR_KEY_LABEL = "label";
    constexpr std::string_view ATTR_KEY_SHAPE = "shape";
    constexpr std::string_view ATTR_KEY_FONT_NAME = "fontname";
    constexpr std::string_view ATTR_KEY_FONT_SIZE = "fontsize";
    constexpr std::string_view ATTR_KEY_WIDTH = "width";
    constexpr std::string_view ATTR_KEY_HEIGHT = "height";
    constexpr std::string_view ATTR_KEY_TAIL_LABEL = "taillabel";
    constexpr std::string_view ATTR_KEY_HEAD_LABEL = "headlabel";
    constexpr std::string_view ATTR_KEY_LABEL_DISTANCE = "labeldistance";
    constexpr std::string_view ATTR_KEY_SPLINES = "splines";
    constexpr std::string_view ATTR_KEY_ARROW_HEAD = "arrowhead";
    constexpr std::string_view ATTR_KEY_ARROW_TAIL = "arrowtail";
    constexpr std::string_view ATTR_KEY_COLOR = "color";
    constexpr std::string_view ATTR_KEY_FILL_COLOR = "fillcolor";
    constexpr std::string_view ATTR_KEY_FONT_COLOR = "fontcolor";

    class Attribute {
    public:
        Attribute();
        explicit Attribute(const std::string& value);
        ~Attribute() = default;

        void set(const std::string& value);
        [[nodiscard]] const std::string& value() const;

    protected:
        std::string _raw;
    };

    class AttributeColor : public Attribute {
    public:
        using Attribute::Attribute;

        [[nodiscard]] static std::tuple<double, double, double> toRGB(const std::string& raw);
    };

    class AttributeRankDir : public Attribute {
    public:
        using Attribute::Attribute;

        static const std::string TOP_TO_BOTTOM;
        static const std::string BOTTOM_TO_TOP;
        static const std::string LEFT_TO_RIGHT;
        static const std::string RIGHT_TO_LEFT;
    };

    class AttributeShape : public Attribute {
    public:
        using Attribute::Attribute;

        static const std::string NONE;
        static const std::string CIRCLE;
        static const std::string DOUBLE_CIRCLE;
        static const std::string ELLIPSE;
        static const std::string RECT;
        static const std::string RECORD;
    };

    class AttributeSplines : public Attribute {
    public:
        using Attribute::Attribute;

        static const std::string LINE;
        static const std::string SPLINE;
    };

    class AttributeArrowShape : public Attribute {
    public:
        using Attribute::Attribute;

        static const std::string NONE;
        static const std::string NORMAL;
        static const std::string EMPTY;
    };

    class Attributes {
    public:
        Attributes() = default;
        ~Attributes() = default;

        [[nodiscard]] std::string graphAttributes(const std::string_view& key) const;
        void setGraphAttributes(const std::string_view& key, const std::string& value);
        void setGraphAttributes(const std::unordered_map<std::string_view, std::string> &attributes);

        [[nodiscard]] std::string vertexAttributes(int u, const std::string_view& key) const;
        void setVertexAttributes(int u, const std::string_view& key, const std::string& value);
        void setVertexAttributes(int u, const std::unordered_map<std::string_view, std::string> &attributes);

        [[nodiscard]] std::string edgeAttributes(int u, const std::string_view& key) const;
        void setEdgeAttributes(int u, const std::string_view& key, const std::string& value);
        void setEdgeAttributes(int u, const std::string_view& key, double value);

        void setEdgeAttributes(int u, const std::unordered_map<std::string_view, std::string>& mapping);
        void transferEdgeAttributes(int u, int v);

        [[nodiscard]] std::string rankDir() const;
        void setRankDir(const std::string& value);

        void setVertexDefaultShape(const std::string& value);
        void setEdgeDefaultSplines(const std::string& value);
        void setVertexDefaultMonospace();
        void setEdgeDefaultMonospace();

        void setVertexShape(int u, const std::string& value);
        void setEdgeSplines(int edgeId, const std::string& value);
        void setEdgeTailLabel(int edgeId, const std::string& label);
        void setEdgeHeadLabel(int edgeId, const std::string& label);
        void setEdgeLabelDistance(int edgeId, double scale);

        void setEdgeDefaultArrowHead(const std::string& value);
        void setEdgeDefaultArrowTail(const std::string& value);
        void setEdgeArrowHead(int edgeId, const std::string& value);
        void setEdgeArrowTail(int edgeId, const std::string& value);

        void setVertexDefaultColor(const std::string& value);
        void setVertexDefaultFillColor(const std::string& value);
        void setVertexDefaultFontColor(const std::string& value);
        void setEdgeDefaultColor(const std::string& value);
        void setEdgeDefaultFontColor(const std::string& value);
        void setVertexColor(int u, const std::string& value);
        void setVertexFillColor(int u, const std::string& value);
        void setVertexFontColor(int u, const std::string& value);
        void setEdgeColor(int edgeId, const std::string& value);
        void setEdgeFontColor(int edgeId, const std::string& value);

    private:
        static const std::string MONOSPACE_FONT_FAMILY;

        static std::unordered_map<std::string_view, std::string> DEFAULT_GRAPH_ATTRIBUTE_VALUES;
        static std::unordered_map<std::string_view, std::string> DEFAULT_VERTEX_ATTRIBUTE_VALUES;
        static std::unordered_map<std::string_view, std::string> DEFAULT_EDGE_ATTRIBUTE_VALUES;

        std::unordered_map<std::string_view, std::string> _graphAttributes;
        std::unordered_map<std::string_view, std::string> _vertexDefaultAttributes;
        std::unordered_map<int, std::unordered_map<std::string_view, std::string>> _vertexAttributes;
        std::unordered_map<std::string_view, std::string> _edgeDefaultAttributes;
        std::unordered_map<int, std::unordered_map<std::string_view, std::string>> _edgeAttributes;
    };

}

#endif //GRAPHLAYOUT_GRAPH_ATTRIBUTES_H