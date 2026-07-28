package io.gorules.zen_rule.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.util.ArrayList;
import java.util.List;

public class NamespaceTools {
    private static final ObjectMapper mapper = new ObjectMapper();

    private String type;
    private String title;
    private String name;
    private String description;
    private List<FunctionSchema> tools;

    public NamespaceTools() {
        this.type = "namespace";
        this.tools = new ArrayList<>();
    }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public List<FunctionSchema> getTools() { return tools; }
    public void setTools(List<FunctionSchema> tools) { this.tools = tools; }

    public ObjectNode toJsonNode() {
        ObjectNode node = mapper.createObjectNode();
        node.put("type", type);
        node.put("title", title);
        node.put("name", name);
        node.put("description", description);
        ArrayNode toolsArray = node.putArray("tools");
        for (FunctionSchema tool : tools) {
            toolsArray.add(tool.toJsonNode());
        }
        return node;
    }
}
