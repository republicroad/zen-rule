package io.gorules.zen_rule.register;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.gorules.zen_rule.model.FunctionSchema;
import io.gorules.zen_rule.model.NamespaceTools;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class UdfManager {
    private static final Logger logger = LoggerFactory.getLogger(UdfManager.class);

    private final Map<String, UdfFunction> functions = new ConcurrentHashMap<>();
    private static final ObjectMapper mapper = new ObjectMapper();

    public void register(Class<?> udfClass) {
        Udf udfAnnotation = udfClass.getAnnotation(Udf.class);
        String namespace = "";
        if (udfAnnotation != null && !udfAnnotation.namespace().isEmpty()) {
            namespace = udfAnnotation.namespace();
        } else {
            String className = udfClass.getSimpleName();
            namespace = className.toLowerCase();
        }

        for (Method method : udfClass.getDeclaredMethods()) {
            Udf methodUdf = method.getAnnotation(Udf.class);
            String funcNamespace = namespace;
            if (methodUdf != null && !methodUdf.namespace().isEmpty()) {
                funcNamespace = methodUdf.namespace();
            }

            FunctionSchema schema = FunctionSchemaBuilder.buildSchema(method, funcNamespace);
            UdfFunction udfFunc = new UdfFunction(method, null, schema);
            functions.put(method.getName(), udfFunc);
            logger.debug("Registered UDF: {} in namespace: {}", method.getName(), funcNamespace);
        }
    }

    public void register(String name, Object instance, Method method, String namespace) {
        FunctionSchema schema = FunctionSchemaBuilder.buildSchema(method, namespace);
        UdfFunction udfFunc = new UdfFunction(method, instance, schema);
        functions.put(name, udfFunc);
        logger.debug("Registered UDF: {} in namespace: {}", name, namespace);
    }

    public FunctionSchema getSchema(String name) {
        UdfFunction func = functions.get(name);
        return func != null ? func.schema : null;
    }

    public Map<String, UdfFunction> getFunctions() {
        return functions;
    }

    public Object execute(String name, Map<String, Object> kwargs) throws Exception {
        UdfFunction func = functions.get(name);
        if (func == null) {
            throw new IllegalArgumentException("Function '" + name + "' is not registered in UDFManager");
        }

        Method method = func.method;
        Parameter[] params = method.getParameters();
        Object[] args = new Object[params.length];

        for (int i = 0; i < params.length; i++) {
            if (params[i].isAnnotationPresent(UdfKwargs.class)) {
                args[i] = new HashMap<>(kwargs);
            } else {
                String paramName = params[i].getName();
                if (kwargs.containsKey(paramName)) {
                    args[i] = coerceType(kwargs.get(paramName), params[i].getType());
                } else {
                    args[i] = getDefaultValue(params[i].getType());
                }
            }
        }

        long t1 = System.currentTimeMillis();
        Object result;
        if (func.instance != null) {
            result = method.invoke(func.instance, args);
        } else {
            result = method.invoke(null, args);
        }
        logger.debug("{} cost: {}ms", name, System.currentTimeMillis() - t1);
        return result;
    }

    private Object getDefaultValue(Class<?> type) {
        if (type == int.class) return 0;
        if (type == long.class) return 0L;
        if (type == float.class) return 0.0f;
        if (type == double.class) return 0.0d;
        if (type == boolean.class) return false;
        if (type == String.class) return "";
        if (type == List.class) return List.of();
        if (type == Map.class) return Map.of();
        return null;
    }

    private Object coerceType(Object value, Class<?> targetType) {
        if (value == null) {
            return getDefaultValue(targetType);
        }
        if (targetType.isInstance(value)) {
            return value;
        }

        String strValue = value.toString();

        if (targetType == String.class) {
            return strValue;
        } else if (targetType == int.class || targetType == Integer.class) {
            return (int) Double.parseDouble(strValue);
        } else if (targetType == long.class || targetType == Long.class) {
            return (long) Double.parseDouble(strValue);
        } else if (targetType == float.class || targetType == Float.class) {
            return (float) Double.parseDouble(strValue);
        } else if (targetType == double.class || targetType == Double.class) {
            return Double.parseDouble(strValue);
        } else if (targetType == boolean.class || targetType == Boolean.class) {
            return Boolean.parseBoolean(strValue);
        }

        return value;
    }

    public List<NamespaceTools> getAllSchemasGroupedByNamespace() {
        Map<String, List<FunctionSchema>> grouped = new LinkedHashMap<>();
        for (UdfFunction func : functions.values()) {
            String ns = func.schema.getNamespace();
            grouped.computeIfAbsent(ns, k -> new ArrayList<>()).add(func.schema);
        }

        List<NamespaceTools> result = new ArrayList<>();
        for (Map.Entry<String, List<FunctionSchema>> entry : grouped.entrySet()) {
            NamespaceTools nsTools = new NamespaceTools();
            nsTools.setName(entry.getKey());
            nsTools.setTitle(entry.getKey());
            nsTools.setDescription("");
            nsTools.setTools(entry.getValue());
            result.add(nsTools);
        }
        return result;
    }

    public static class UdfFunction {
        public final Method method;
        public final Object instance;
        public final FunctionSchema schema;

        public UdfFunction(Method method, Object instance, FunctionSchema schema) {
            this.method = method;
            this.instance = instance;
            this.schema = schema;
        }
    }
}
