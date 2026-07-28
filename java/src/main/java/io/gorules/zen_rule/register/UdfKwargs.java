package io.gorules.zen_rule.register;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 标记某个 Map&lt;String, Object&gt; 参数应接收全部 kwargs。
 * 用于模拟 Python 的 **kwargs 行为。
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.PARAMETER)
public @interface UdfKwargs {
}
