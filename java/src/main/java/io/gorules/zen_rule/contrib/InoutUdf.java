package io.gorules.zen_rule.contrib;

import io.gorules.zen_rule.register.Udf;
import io.gorules.zen_rule.register.UdfKwargs;
import io.gorules.zen_rule.register.UdfParam;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;

/**
 * 内置 UDF: inout
 * 自定义函数测试, 返回值返回入参, 用于调试.
 */
public class InoutUdf {
    private static final Logger logger = LoggerFactory.getLogger(InoutUdf.class);

    public static Object inout(
            @UdfParam(description = "参数 b") Object b,
            @UdfParam(description = "参数 a") Object a,
            @UdfParam(description = "参数 c") Object c,
            @UdfKwargs Map<String, Object> kwargs) {
        logger.info("function: inout args: b={}, a={}, c={}", b, a, c);
        logger.info("function: inout kwargs: {}", kwargs);
        return kwargs.getOrDefault("_node_input_", Map.of());
    }
}
