package io.gorules.zen_rule.register;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.gorules.zen_rule.model.FunctionSchema;

import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.*;
import java.util.stream.Collectors;

public class FunctionSchemaBuilder {
    private static final ObjectMapper mapper = new ObjectMapper();

    private static final Map<Class<?>, String> JAVA_TO_JSON_TYPE = new LinkedHashMap<>();

    static {
        JAVA_TO_JSON_TYPE.put(void.class, "null");
        JAVA_TO_JSON_TYPE.put(Void.class, "null");
        JAVA_TO_JSON_TYPE.put(boolean.class, "boolean");
        JAVA_TO_JSON_TYPE.put(Boolean.class, "boolean");
        JAVA_TO_JSON_TYPE.put(String.class, "string");
        JAVA_TO_JSON_TYPE.put(int.class, "integer");
        JAVA_TO_JSON_TYPE.put(Integer.class, "integer");
        JAVA_TO_JSON_TYPE.put(long.class, "integer");
        JAVA_TO_JSON_TYPE.put(Long.class, "integer");
        JAVA_TO_JSON_TYPE.put(float.class, "number");
        JAVA_TO_JSON_TYPE.put(Float.class, "number");
        JAVA_TO_JSON_TYPE.put(double.class, "number");
        JAVA_TO_JSON_TYPE.put(Double.class, "number");
        JAVA_TO_JSON_TYPE.put(List.class, "array");
        JAVA_TO_JSON_TYPE.put(Map.class, "object");
    }

    public static FunctionSchema buildSchema(Method method, String namespace) {
        FunctionSchema schema = new FunctionSchema();
        schema.setName(method.getName());
        schema.setTitle(method.getName());
        schema.setNamespace(namespace);
        schema.setKind(namespace);
        schema.setDescription(extractMethodJavadoc(method));
        schema.setParameters(buildParametersSchema(method));
        schema.setReturns(buildReturnSchema(method));
        return schema;
    }

    private static ObjectNode buildParametersSchema(Method method) {
        ObjectNode paramsSchema = mapper.createObjectNode();
        paramsSchema.put("type", "object");

        ObjectNode properties = mapper.createObjectNode();
        ArrayNode required = mapper.createArrayNode();

        Parameter[] parameters = method.getParameters();
        for (Parameter param : parameters) {
            String paramName = param.getName();
            ObjectNode propSchema = mapper.createObjectNode();
            String jsonType = mapJavaTypeToJsonType(param.getType());
            propSchema.put("type", jsonType);
            propSchema.put("title", paramName.substring(0, 1).toUpperCase() + paramName.substring(1));

            String description = extractParameterJavadoc(method, paramName);
            if (description != null && !description.isEmpty()) {
                propSchema.put("description", description);
            }

            UdfParam udfParam = param.getAnnotation(UdfParam.class);
            if (udfParam != null && !udfParam.description().isEmpty()) {
                propSchema.put("description", udfParam.description());
            }

            properties.set(paramName, propSchema);
        }

        paramsSchema.set("properties", properties);
        return paramsSchema;
    }

    private static ObjectNode buildReturnSchema(Method method) {
        ObjectNode returnSchema = mapper.createObjectNode();
        Class<?> returnType = method.getReturnType();

        if (returnType == void.class || returnType == Void.class) {
            returnSchema.put("type", "null");
        } else {
            String jsonType = mapJavaTypeToJsonType(returnType);
            returnSchema.put("type", jsonType);
        }

        return returnSchema;
    }

    private static String mapJavaTypeToJsonType(Class<?> javaType) {
        return JAVA_TO_JSON_TYPE.getOrDefault(javaType, "string");
    }

    private static String extractMethodJavadoc(Method method) {
        Class<?> declaringClass = method.getDeclaringClass();
        String methodName = method.getName();

        Package pkg = declaringClass.getPackage();
        String packageName = pkg != null ? pkg.getName() : "";
        return "UDF function: " + methodName + " in namespace " + packageName;
    }

    private static String extractParameterJavadoc(Method method, String paramName) {
        return "";
    }
}
