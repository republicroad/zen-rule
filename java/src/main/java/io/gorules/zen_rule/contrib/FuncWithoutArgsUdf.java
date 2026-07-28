package io.gorules.zen_rule.contrib;

import io.gorules.zen_rule.register.Udf;
import io.gorules.zen_rule.register.UdfKwargs;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;

/**
 * 内置 UDF: func_without_args
 * 无参数函数, 用于自定义函数测试.
 */
public class FuncWithoutArgsUdf {
    private static final Logger logger = LoggerFactory.getLogger(FuncWithoutArgsUdf.class);

    public static Object func_without_args(@UdfKwargs Map<String, Object> kwargs) {
        logger.info("function: func_without_args kwargs: {}", kwargs);
        return kwargs.getOrDefault("_node_input_", Map.of());
    }
}
