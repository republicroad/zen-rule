package io.gorules.zen_rule.model;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.util.LinkedHashMap;
import java.util.Map;

public class FunctionSchema {
    private static final ObjectMapper mapper = new ObjectMapper();

    private String name;
    private String title;
    private String type;
    private String description;
    private String namespace;
    private String kind;
    private ObjectNode parameters;
    private ObjectNode returns;

    public FunctionSchema() {
        this.type = "function";
        this.parameters = mapper.createObjectNode();
        this.returns = mapper.createObjectNode();
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getNamespace() { return namespace; }
    public void setNamespace(String namespace) { this.namespace = namespace; }

    public String getKind() { return kind; }
    public void setKind(String kind) { this.kind = kind; }

    public ObjectNode getParameters() { return parameters; }
    public void setParameters(ObjectNode parameters) { this.parameters = parameters; }

    public ObjectNode getReturns() { return returns; }
    public void setReturns(ObjectNode returns) { this.returns = returns; }

    public ObjectNode toJsonNode() {
        ObjectNode node = mapper.createObjectNode();
        node.put("name", name);
        node.put("title", title);
        node.put("type", type);
        node.put("description", description);
        node.put("namespace", namespace);
        node.put("kind", kind);
        node.set("parameters", parameters);
        node.set("returns", returns);
        return node;
    }

    public static FunctionSchema fromJsonNode(ObjectNode node) {
        FunctionSchema schema = new FunctionSchema();
        schema.name = node.path("name").asText();
        schema.title = node.path("title").asText();
        schema.type = node.path("type").asText("function");
        schema.description = node.path("description").asText("");
        schema.namespace = node.path("namespace").asText("");
        schema.kind = node.path("kind").asText("");
        schema.parameters = (ObjectNode) node.path("parameters");
        schema.returns = (ObjectNode) node.path("returns");
        return schema;
    }
}
