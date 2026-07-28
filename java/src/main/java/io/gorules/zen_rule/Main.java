package io.gorules.zen_rule;

import io.gorules.zen_engine.*;
import io.gorules.zen_rule.register.Udf;
import io.gorules.zen_rule.register.UdfParam;
import io.gorules.zen_rule.register.UdfManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.io.InputStream;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

public class Main {
    private static final Logger logger = LoggerFactory.getLogger(Main.class);

    @Udf(namespace = "demo")
    public static class FooUdf {
        public static String foo(@UdfParam(description = "参数 a") String a,
                                  @UdfParam(description = "参数 b") String b,
                                  @UdfParam(description = "参数 c") String c) {
            logger.info("function: foo args: a={}, b={}, c={}", a, b, c);
            return "foo value";
        }
    }

    public static void main(String[] args) throws Exception {
        testZenRuleFoo();
        testZenRule();
    }

    public static void testZenRule() throws Exception {
        logger.info("=== test_zenrule ===");
        UdfManager udfManager = new UdfManager();
        udfManager.register(FooUdf.class);
        ZenRule.registerDefaultUdfs(udfManager);

        String graphPath = "graph/custom.json";
        String content = readResource(graphPath);

        try (ZenRule zr = new ZenRule(Map.of(), udfManager)) {
            String key = graphPath;
            zr.createDecisionWithCacheKey(key, content);

            Map<String, Object> input = Map.of("input", 7, "myvar", 15);
            ZenEngineResponse result = zr.evaluateSync(key, input);
            logger.info("zen rule custom result: {}", result.result());
            logger.info("performance: {}", result.performance());
        }
    }

    public static void testZenRuleFoo() throws Exception {
        logger.info("=== test_zenrule_foo ===");
        UdfManager udfManager = new UdfManager();
        udfManager.register(FooUdf.class);
        ZenRule.registerDefaultUdfs(udfManager);

        String graphPath = "graph/custom_fullnode.json";
        String content = readResource(graphPath);

        try (ZenRule zr = new ZenRule(Map.of(), udfManager)) {
            String key = graphPath;
            zr.createDecisionWithCacheKey(key, content);

            Map<String, Object> input = Map.of("input", 7, "myvar", 15);
            ZenEngineResponse result = zr.evaluateSync(key, input);
            logger.info("zen rule custom result: {}", result.result());

            // Parse result and assert
            String resultStr = result.result().value() != null
                ? new String(result.result().value())
                : "";
            if (resultStr.contains("foo value")) {
                logger.info("TEST PASSED: custom rule execution succeeded");
            } else {
                logger.error("TEST FAILED: expected 'foo value' in result, got: {}", resultStr);
                throw new AssertionError("custom rule execution failed");
            }
        }
    }

    private static String readResource(String name) throws Exception {
        try (InputStream is = Main.class.getClassLoader().getResourceAsStream(name)) {
            if (is == null) throw new RuntimeException("Resource not found: " + name);
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
}
