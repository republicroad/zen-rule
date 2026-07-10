import type { ZenEvaluateOptions } from '@gorules/zen-engine';
import {
  ZenEngine,
  ZenDecision,
  ZenDecisionContent,
  ZenEngineHandlerRequest,
  ZenEngineHandlerResponse,
  ZenEngineOptions,
  evaluateExpressionSync,
} from '@gorules/zen-engine';

import { udfManager } from './register.js';
import './contrib.js';

const CUSTOM_HANDLER_META = '__meta__';

interface ExprAstItem {
  id: string;
  key: string;
  value: string | string[];
}

interface EvaluateResponse {
  performance: string;
  result: unknown;
  trace?: unknown;
}

interface GraphNode {
  type?: string;
  name?: string;
  content?: {
    config?: Record<string, unknown>;
  };
  [key: string]: unknown;
}

interface GraphContent {
  id?: string;
  metadata?: Record<string, unknown>;
  nodes: GraphNode[];
  [key: string]: unknown;
}

function evaluateExpressionSafe(expr: string, input?: unknown): unknown {
  try {
    return evaluateExpressionSync(expr, input);
  } catch (e) {
    return null;
  }
}

class ZenRule {
  static CUSTOM_HANDLER_META = CUSTOM_HANDLER_META;
  static udfManager = udfManager;

  engine: ZenEngine;
  options: ZenEngineOptions;
  decisionCache = new Map<string, ZenDecision>();
  contentCache = new Map<string, unknown>();

  constructor(options?: ZenEngineOptions) {
    if (options) {
      const loader = options.loader;
      if (options.customHandler == null) {
        options.customHandler = ZenRule.customHandlerFunc;
      }
      this.options = options;
    } else {
      this.options = { customHandler: ZenRule.customHandlerFunc };
    }
    this.engine = new ZenEngine(this.options);
  }

  createDecision(content: string | object): ZenDecision {
    const contentObj = typeof content === 'string' ? JSON.parse(content) : content;
    const enhanced = this.graphAddons(contentObj);
    const decisionContent = new ZenDecisionContent(enhanced);
    return this.engine.createDecision(decisionContent);
  }

  createDecisionWithCacheKey(key: string, content: string | object): ZenDecision {
    if (this.decisionCache.has(key)) {
      throw new Error(
        `rule key:${key} is existed, if confirm to overwrite this key, please use updateDecisionWithCacheKey`,
      );
    }
    const decision = this.createDecision(content);
    this.decisionCache.set(key, decision);
    this.contentCache.set(key, content);
    return decision;
  }

  updateDecisionWithCacheKey(key: string, content: string | object): ZenDecision {
    if (!this.decisionCache.has(key)) {
      throw new Error(
        `rule key:${key} is not existed, please use createDecisionWithCacheKey`,
      );
    }
    const decision = this.createDecision(content);
    this.decisionCache.set(key, decision);
    this.contentCache.set(key, content);
    return decision;
  }

  deleteDecisionWithCacheKey(key: string): void {
    if (!this.decisionCache.has(key)) {
      throw new Error(`delete failed! rule key:${key} is not existed`);
    }
    this.decisionCache.delete(key);
    this.contentCache.delete(key);
  }

  getDecision(key: string): ZenDecision {
    const cached = this.decisionCache.get(key);
    if (cached) {
      return cached;
    }
    const loader = this.options.loader;
    if (!loader) {
      throw new Error(`decision ${key} not found, please use createDecisionWithCacheKey`);
    }
    const decisionContent = loader(key);
    if (decisionContent instanceof Promise) {
      throw new Error('loader returned a Promise; only sync loaders are supported for now');
    }
    const decision = this.createDecision(decisionContent);
    this.decisionCache.set(key, decision);
    this.contentCache.set(key, decisionContent);
    return decision;
  }

  getDecisionCache(key: string): ZenDecision | undefined {
    return this.decisionCache.get(key);
  }

  getContentCache(key: string): unknown {
    return this.contentCache.get(key);
  }

  evaluate(key: string, ctx: unknown, options?: unknown): Promise<EvaluateResponse> {
    const decision = this.getDecision(key);
    return decision.evaluate(ctx, options as ZenEvaluateOptions | null | undefined) as Promise<EvaluateResponse>;
  }

  async evaluateAsync(key: string, ctx: unknown, options?: unknown): Promise<EvaluateResponse> {
    const decision = this.getDecision(key);
    const result = await decision.evaluate(ctx, options as ZenEvaluateOptions | null | undefined);
    return result as EvaluateResponse;
  }

  graphAddons(content: GraphContent): object {
    const ruleGraph = JSON.parse(JSON.stringify(content)) as GraphContent;

    const inputNodeName =
      ruleGraph.nodes
        .filter((n) => n.type === 'inputNode')
        .map((n) => n.name)
        .filter(Boolean)[0] ?? '';

    const ruleId = ruleGraph.id ?? '';
    const ruleMeta = ruleGraph.metadata ?? {};
    (ruleMeta as Record<string, unknown>)['namespace'] = ruleId;
    (ruleMeta as Record<string, unknown>)['inputNode_name'] = inputNodeName;

    for (const node of ruleGraph.nodes) {
      if (node.type !== 'customNode') continue;
      const config = (node.content?.config ?? {}) as Record<string, unknown>;

      const chMeta = ((config[CUSTOM_HANDLER_META] as Record<string, unknown>) ??
        (config['meta'] as Record<string, unknown>) ??
        {}) as Record<string, unknown>;
      Object.assign(chMeta, ruleMeta);
      config[CUSTOM_HANDLER_META] = chMeta;

      if (config['passThrough'] == null) {
        config['passThrough'] = true;
      }

      const customExpressions = config['expressions'] as ExprAstItem[] | undefined;
      if (customExpressions) {
        const exprAsts: ExprAstItem[] = [];
        for (const funcItem of customExpressions) {
          const item = { ...funcItem };
          item.value =     ZenRule.parseOperatorExpr(funcItem.value);
          exprAsts.push(item);
        }
        config['expr_asts'] = exprAsts;
      }
    }

    return ruleGraph;
  }

  static parseOperatorExpr(expr: string | string[]): string[] {
    if (Array.isArray(expr)) {
      return expr;
    }
    const pattern = /;;(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)/;
    const parts = expr.split(pattern).map((s) => s.trim());
    return parts;
  }

  static async customHandlerFunc(
    request: ZenEngineHandlerRequest,
  ): Promise<ZenEngineHandlerResponse> {
    const node = request.node;
    const exprAsts = (node.config?.['expr_asts'] ?? []) as ExprAstItem[];
    const inputField = (node.config?.['inputField'] as string | null) ?? null;
    const outputPath = (node.config?.['outputPath'] as string | null) ?? null;
    const passThrough = (node.config?.['passThrough'] as boolean | null) ?? null;
    const meta = (node.config?.[CUSTOM_HANDLER_META] as Record<string, unknown>) ?? {};

    const context: Record<string, unknown> = {
      node_id: node.id,
      [CUSTOM_HANDLER_META]: meta,
      passThrough,
      inputField,
      outputPath,
    };

    const coroFuncs = exprAsts.map((item) =>
      ZenRule.executeExpr(item, request.input, context),
    );
    const resultsArr = await Promise.all(coroFuncs);
    const results: Record<string, unknown> = {};
    exprAsts.forEach((item, i) => {
      results[item.key] = resultsArr[i];
    });

    if (passThrough && typeof request.input === 'object' && request.input !== null) {
      const input = request.input as Record<string, unknown>;
      for (const key of Object.keys(input)) {
        if (key !== '$nodes') {
          results[key] = input[key];
        }
      }
    }

    if (outputPath) {
      const tmp = evaluateExpressionSafe(`${outputPath}=_`, { _: results }) as
        | Record<string, unknown>
        | undefined;
      if (tmp && typeof tmp === 'object') {
        Object.assign(results, tmp);
      }
    }

    return { output: results };
  }

  private static async executeExpr(
    execExpr: ExprAstItem,
    nodeInput: unknown,
    context: Record<string, unknown>,
  ): Promise<unknown> {
    try {
      const exprId = execExpr.id;
      const exprKey = execExpr.key;
      const exprAst = execExpr.value;

      const ast = Array.isArray(exprAst) ? exprAst : ZenRule.parseOperatorExpr(exprAst);
      const funcName = ast[0] as string;
      const opArgExpressions = ast.slice(1);

      const inputField = context['inputField'] as string | null;
      const fSchema = udfManager.udfFunctionSchema(funcName);

      if (fSchema) {
        const args = opArgExpressions.map((i: string) => {
          const expr = inputField ? `${inputField}.${i}` : i;
          return evaluateExpressionSafe(expr, nodeInput);
        });

        const operatorKwargs = udfManager.funcBindParams(funcName, args);
        const kwargs: Record<string, unknown> = {
          ...operatorKwargs,
          ...context,
          func_id: exprId,
          expr_id: exprId,
          _node_input_: nodeInput,
        };

        const result = await udfManager.call(funcName, kwargs);
        return result;
      } else {
        if (funcName) {
          return { error: `udf ${funcName} not found` };
        }
        return { error: 'empty udf name not allowed' };
      }
    } catch (e) {
      return null;
    }
  }

  static udfFunctionSchemaTools(): unknown[] {
    return udfManager.udfFunctionSchemaTools();
  }
}

export { ZenRule };
