package io.gorules.zen_rule;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.gorules.zen_engine.*;
import io.gorules.zen_rule.register.UdfManager;
import io.gorules.zen_rule.contrib.InoutUdf;
import io.gorules.zen_rule.contrib.FuncWithoutArgsUdf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Method;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class ZenRule implements AutoCloseable {
    private static final Logger logger = LoggerFactory.getLogger(ZenRule.class);
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final String CUSTOM_HANDLER_META = "__meta__";

    private static final Pattern SEMICOLON_PATTERN = Pattern.compile(
        ";;(?=(?:[^\"'`]*[\"'`][^\"'`]*[\"'`])*[^\"'`]*$)"
    );

    private final ZenEngine engine;
    private final UdfManager udfManager;
    private final ConcurrentHashMap<String, ZenDecision> decisionCache = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, String> contentCache = new ConcurrentHashMap<>();
    private final Map<String, Object> customContext = new ConcurrentHashMap<>();

    public ZenRule(Map<String, Object> options) {
        this.udfManager = new UdfManager();
        this.engine = createEngine(options);
    }

    public ZenRule(Map<String, Object> options, UdfManager udfManager) {
        this.udfManager = udfManager;
        this.engine = createEngine(options);
    }

    /**
     * 注册内置 UDF (inout, func_without_args) 到 UdfManager。
     * 等价于 Python 版本中 contrib 模块随 engine 导入自动注册的行为。
     */
    public static void registerDefaultUdfs(UdfManager udfManager) {
        udfManager.register(InoutUdf.class);
        udfManager.register(FuncWithoutArgsUdf.class);
    }

    private ZenEngine createEngine(Map<String, Object> options) {
        if (options == null) {
            options = new HashMap<>();
        }

        Object loaderObj = options.get("loader");
        ZenDecisionLoaderCallback loader = null;
        if (loaderObj instanceof ZenDecisionLoaderCallback) {
            loader = (ZenDecisionLoaderCallback) loaderObj;
        } else if (loaderObj instanceof java.util.function.Function) {
            @SuppressWarnings("unchecked")
            java.util.function.Function<String, CompletableFuture<JsonBuffer>> loaderFn =
                (java.util.function.Function<String, CompletableFuture<JsonBuffer>>) loaderObj;
            loader = loaderFn::apply;
        }

        ZenCustomNodeCallback customCallback = this::handleCustomNode;
        return new ZenEngine(loader, customCallback);
    }

    private CompletableFuture<ZenEngineHandlerResponse> handleCustomNode(ZenEngineHandlerRequest request) {
        try {
            return CompletableFuture.completedFuture(customHandlerFunc(request));
        } catch (Exception e) {
            logger.error("Custom handler error", e);
            CompletableFuture<ZenEngineHandlerResponse> future = new CompletableFuture<>();
            future.completeExceptionally(e);
            return future;
        }
    }

    public ZenDecision createDecision(String content) {
        String contentProcessed = graphAddons(content);
        JsonBuffer buffer = new JsonBuffer(contentProcessed.getBytes());
        try {
            return engine.createDecision(buffer);
        } catch (ZenException e) {
            throw new RuntimeException("Failed to create decision", e);
        }
    }

    public ZenDecision createDecisionWithCacheKey(String key, String content) {
        if (decisionCache.containsKey(key)) {
            throw new RuntimeException("rule key:" + key + " is existed, if confirm to overwrite this key, please use updateDecisionWithCacheKey");
        }
        ZenDecision decision = createDecision(content);
        decisionCache.put(key, decision);
        contentCache.put(key, content);
        return decision;
    }

    public ZenDecision updateDecisionWithCacheKey(String key, String content) {
        if (!decisionCache.containsKey(key)) {
            throw new RuntimeException("rule key:" + key + " is not existed, please use createDecisionWithCacheKey");
        }
        ZenDecision decision = createDecision(content);
        decisionCache.put(key, decision);
        contentCache.put(key, content);
        return decision;
    }

    public void deleteDecisionWithCacheKey(String key) {
        if (!decisionCache.containsKey(key)) {
            throw new RuntimeException("delete failed! rule key:" + key + " is not existed");
        }
        decisionCache.remove(key);
        contentCache.remove(key);
    }

    public ZenDecision getDecision(String key) {
        ZenDecision decision = decisionCache.get(key);
        if (decision != null) {
            return decision;
        }
        throw new RuntimeException("decision " + key + " not found, please createDecisionWithCacheKey");
    }

    public ZenDecision getDecisionFromLoader(String key) {
        ZenDecision decision = decisionCache.get(key);
        if (decision != null) {
            return decision;
        }
        throw new RuntimeException("decision " + key + " not found in cache, and loader is not configured for dynamic loading");
    }

    public CompletableFuture<ZenEngineResponse> evaluate(String key, Map<String, Object> ctx) {
        ZenDecision decision = getDecision(key);
        JsonBuffer input = new JsonBuffer(toJsonBytes(ctx));
        return decision.evaluate(input, null);
    }

    public ZenEngineResponse evaluateSync(String key, Map<String, Object> ctx) throws Exception {
        ZenDecision decision = getDecision(key);
        JsonBuffer input = new JsonBuffer(toJsonBytes(ctx));
        return decision.evaluate(input, null).join();
    }

    public String graphAddons(String graphContent) {
        try {
            JsonNode graphNode = mapper.readTree(graphContent);
            if (!graphNode.isObject()) {
                throw new IllegalArgumentException("Expected JSON object, got " + graphNode.getNodeType());
            }
            ObjectNode ruleGraph = (ObjectNode) graphNode;

            // Find inputNode name
            String inputNodeName = "";
            JsonNode nodes = ruleGraph.path("nodes");
            if (nodes.isArray()) {
                for (JsonNode node : nodes) {
                    if ("inputNode".equals(node.path("type").asText())) {
                        String name = node.path("name").asText("");
                        if (!name.isEmpty()) {
                            inputNodeName = name;
                            break;
                        }
                    }
                }
            }

            String ruleId = ruleGraph.path("id").asText("");
            ObjectNode ruleMeta = mapper.createObjectNode();
            ruleMeta.put("namespace", ruleId);
            ruleMeta.put("inputNode_name", inputNodeName);

            // Copy existing metadata if present
            JsonNode existingMeta = ruleGraph.path("metadata");
            if (existingMeta.isObject()) {
                existingMeta.fields().forEachRemaining(entry -> {
                    ruleMeta.put(entry.getKey(), entry.getValue().asText());
                });
            }

            // Process custom nodes
            if (nodes.isArray()) {
                for (JsonNode node : nodes) {
                    if ("customNode".equals(node.path("type").asText())) {
                        processCustomNode((ObjectNode) node, ruleMeta);
                    }
                }
            }

            return mapper.writeValueAsString(ruleGraph);
        } catch (Exception e) {
            throw new RuntimeException("graphAddons failed", e);
        }
    }

    private void processCustomNode(ObjectNode node, ObjectNode ruleMeta) {
        ObjectNode content = (ObjectNode) node.path("content");
        ObjectNode config = (ObjectNode) content.path("config");

        // Inject __meta__
        ObjectNode existingMeta = (ObjectNode) config.path(CUSTOM_HANDLER_META);
        ObjectNode meta = existingMeta.isObject() ? existingMeta : mapper.createObjectNode();
        ruleMeta.fields().forEachRemaining(entry -> {
            meta.put(entry.getKey(), entry.getValue().asText());
        });
        config.set(CUSTOM_HANDLER_META, meta);

        // Default passThrough = true
        JsonNode passThrough = config.path("passThrough");
        if (passThrough.isNull() || !config.has("passThrough")) {
            config.put("passThrough", true);
        }

        // Parse expressions
        JsonNode expressions = config.path("expressions");
        if (expressions.isArray() && expressions.size() > 0) {
            ArrayNode exprAsts = mapper.createArrayNode();
            for (JsonNode expr : expressions) {
                ObjectNode astItem = ((ObjectNode) expr).deepCopy();
                String value = expr.path("value").asText("");
                List<String> parsed = parseOperatorExpr(value);
                astItem.set("value", mapper.valueToTree(parsed));
                exprAsts.add(astItem);
            }
            config.set("expr_asts", exprAsts);
        }

        logger.debug("rule_graph after processing: {}", ruleGraph_pretty(node));
    }

    private ZenEngineHandlerResponse customHandlerFunc(ZenEngineHandlerRequest request) throws Exception {
        JsonBuffer inputBuffer = request.input();
        JsonBuffer nodeConfigBuffer = request.node().config();

        Map<String, Object> input = mapper.readValue(inputBuffer.value(), new TypeReference<Map<String, Object>>() {});
        Map<String, Object> nodeConfig = mapper.readValue(nodeConfigBuffer.value(), new TypeReference<Map<String, Object>>() {});

        List<Map<String, Object>> exprAsts = (List<Map<String, Object>>) nodeConfig.getOrDefault("expr_asts", List.of());
        String inputField = (String) nodeConfig.getOrDefault("inputField", null);
        String outputPath = (String) nodeConfig.getOrDefault("outputPath", null);
        Boolean passThrough = (Boolean) nodeConfig.getOrDefault("passThrough", true);
        Map<String, Object> meta = (Map<String, Object>) nodeConfig.getOrDefault(CUSTOM_HANDLER_META, Map.of());

        logger.debug("custom node use custom_handler");

        Map<String, Object> context = new HashMap<>();
        context.put("node_id", request.node().id());
        context.put(CUSTOM_HANDLER_META, meta);
        context.put("passThrough", passThrough);
        context.put("inputField", inputField);
        context.put("outputPath", outputPath);

        // Execute all expressions in parallel
        List<CompletableFuture<Map.Entry<String, Object>>> futures = new ArrayList<>();
        for (Map<String, Object> item : exprAsts) {
            futures.add(
                executeExpression(item, input, context)
                    .thenApply(result -> new AbstractMap.SimpleEntry<>((String) item.get("key"), result))
            );
        }

        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();

        Map<String, Object> results = new HashMap<>();
        for (CompletableFuture<Map.Entry<String, Object>> future : futures) {
            Map.Entry<String, Object> entry = future.join();
            results.put(entry.getKey(), entry.getValue());
        }

        if (Boolean.TRUE.equals(passThrough)) {
            Map<String, Object> resultsRef = results;
            input.forEach((k, v) -> {
                if (!"$nodes".equals(k)) {
                    resultsRef.put(k, v);
                }
            });
        }

        if (outputPath != null && !outputPath.isEmpty()) {
            try {
                Map<String, Object> wrapper = Map.of("_", results);
                String expr = outputPath + "=_";
                JsonBuffer ctx = new JsonBuffer(toJsonBytes(wrapper));
                JsonBuffer outputResult = ZenUniffi.evaluateExpression(expr, ctx);
                results = mapper.readValue(outputResult.value(), new TypeReference<Map<String, Object>>() {});
            } catch (Exception e) {
                logger.error("outputPath evaluation failed", e);
            }
        }

        logger.debug("custom result: {}", results);
        JsonBuffer outputBuffer = new JsonBuffer(toJsonBytes(results));
        return new ZenEngineHandlerResponse(outputBuffer, null);
    }

    private CompletableFuture<Object> executeExpression(Map<String, Object> exprItem, Map<String, Object> nodeInput, Map<String, Object> context) {
        try {
            String exprId = (String) exprItem.get("id");
            List<String> exprAst = (List<String>) exprItem.get("value");
            String exprKey = (String) exprItem.get("key");

            if (exprAst == null || exprAst.isEmpty()) {
                return CompletableFuture.completedFuture(Map.of("error", "empty expression"));
            }

            String funcName = exprAst.get(0);
            List<String> argExpressions = exprAst.subList(1, exprAst.size());

            logger.debug("node_input: {}  context: {}", nodeInput, context);
            logger.debug("func: {}  literal args: {}", funcName, argExpressions);

            String inputField = (String) context.getOrDefault("inputField", null);

            UdfManager.UdfFunction udfFunc = udfManager.getFunctions().get(funcName);
            if (udfFunc != null) {
                // Evaluate arguments
                List<Object> args = new ArrayList<>();
                for (String argExpr : argExpressions) {
                    String evalExpr = inputField != null && !inputField.isEmpty()
                        ? inputField + "." + argExpr.trim()
                        : argExpr.trim();
                    try {
                        JsonBuffer inputBuf = new JsonBuffer(toJsonBytes(nodeInput));
                        Object argValue = ZenUniffi.evaluateExpression(evalExpr, inputBuf);
                        args.add(argValue);
                    } catch (Exception e) {
                        logger.warn("Failed to evaluate expression: {}", evalExpr, e);
                        args.add(null);
                    }
                }

                // Bind parameters
                Map<String, Object> boundParams = funcBindParams(funcName, args);

                // Build kwargs
                Map<String, Object> kwargs = new HashMap<>(boundParams);
                kwargs.putAll(context);
                kwargs.put("func_id", exprId);
                kwargs.put("expr_id", exprId);
                kwargs.put("_node_input_", nodeInput);

                try {
                    Object result = udfManager.execute(funcName, kwargs);
                    return CompletableFuture.completedFuture(result);
                } catch (Exception e) {
                    logger.error("UDF execution failed: {}", funcName, e);
                    return CompletableFuture.completedFuture(null);
                }
            } else {
                if (funcName != null && !funcName.isEmpty()) {
                    return CompletableFuture.completedFuture(Map.of("error", "udf " + funcName + " not found"));
                } else {
                    return CompletableFuture.completedFuture(Map.of("error", "empty udf name not allowed"));
                }
            }
        } catch (Exception e) {
            logger.error("Expression execution error", e);
            return CompletableFuture.completedFuture(null);
        }
    }

    private Map<String, Object> funcBindParams(String funcName, List<Object> args) {
        UdfManager.UdfFunction func = udfManager.getFunctions().get(funcName);
        if (func == null) {
            return Map.of();
        }

        Map<String, Object> result = new LinkedHashMap<>();
        var params = func.method.getParameters();
        for (int i = 0; i < Math.min(params.length, args.size()); i++) {
            String paramName = params[i].getName();
            Object value = args.get(i);
            result.put(paramName, value);
        }
        return result;
    }

    public List<String> parseOperatorExpr(String expr) {
        if (expr == null || expr.isEmpty()) {
            return List.of();
        }
        String[] parts = SEMICOLON_PATTERN.split(expr);
        return Arrays.stream(parts)
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .collect(Collectors.toList());
    }

    private byte[] toJsonBytes(Object obj) {
        try {
            return mapper.writeValueAsBytes(obj);
        } catch (Exception e) {
            throw new RuntimeException("JSON serialization failed", e);
        }
    }

    private String ruleGraph_pretty(JsonNode node) {
        try {
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(node);
        } catch (Exception e) {
            return node.toString();
        }
    }

    @Override
    public void close() {
        engine.close();
    }
}
