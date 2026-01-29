#include "common/test_utils.h"
#include "xml_element.h"
using namespace std;
using namespace svg_diagram;
using namespace graph_layout;

bool compareSVGContent(const string& a, const string& b) {
    XMLElement rootA, rootB;
    rootA.addChildren(XMLElement::parse(a));
    rootB.addChildren(XMLElement::parse(b));
    return rootA == rootB;
}
