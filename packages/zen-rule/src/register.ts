export interface UdfSchemaParameter {
  type?: string;
  description?: string;
  default?: unknown;
}

export interface UdfSchema {
  parameters?: Record<string, UdfSchemaParameter>;
  returns?: { type?: string; description?: string };
  namespace?: string;
}

interface UdfEntry {
  fn: Function;
  schema: UdfSchema;
}

const pyTDefaultsMaps: Record<string, unknown> = {
  null: null,
  boolean: false,
  string: '',
  object: {},
  array: [],
  integer: 0,
  number: 0.0,
};

function jsonT2pyT(jsonType: string): (v: unknown) => unknown {
  const m: Record<string, (v: unknown) => unknown> = {
    null: () => null,
    boolean: (v) => Boolean(v),
    string: (v) => String(v),
    object: (v) => (typeof v === 'object' && v !== null ? v : {}),
    array: (v) => (Array.isArray(v) ? v : []),
    integer: (v) => {
      const n = Number(v);
      return Number.isInteger(n) ? n : 0;
    },
    number: (v) => Number(v),
  };
  return m[jsonType] ?? ((v) => v);
}

class UDFManager {
  private functions = new Map<string, UdfEntry>();

  registerFunction(
    fn: Function,
    namespace?: string,
    schema?: UdfSchema,
    nameOverride?: string,
  ): void {
    const name = nameOverride ?? fn.name;
    if (!name) {
      throw new Error('Function must have a name to register');
    }
    this.functions.set(name, {
      fn,
      schema: {
        parameters: schema?.parameters ?? {},
        returns: schema?.returns ?? { type: 'null' },
        namespace: namespace ?? 'default',
      },
    });
  }

  udfFunctionSchema(name: string): UdfSchema | undefined {
    return this.functions.get(name)?.schema;
  }

  funcBindParams(name: string, args: unknown[]): Record<string, unknown> {
    const schema = this.udfFunctionSchema(name);
    if (!schema?.parameters) {
      return {};
    }
    const paramEntries = Object.entries(schema.parameters);
    const bound: Record<string, unknown> = {};
    paramEntries.forEach(([paramName, paramSchema], i) => {
      const val = i < args.length ? args[i] : paramSchema.default ?? null;
      const converter = jsonT2pyT(paramSchema.type ?? 'null');
      bound[paramName] = converter(val);
    });
    return bound;
  }

  async call(udfName: string, ...args: unknown[]): Promise<unknown> {
    const entry = this.functions.get(udfName);
    if (!entry) {
      throw new Error(`Function '${udfName}' is not registered in UDFManager`);
    }
    const fn = entry.fn;
    const result = fn(...args);
    return result instanceof Promise ? await result : result;
  }

  udfFunctionSchemaTools(): unknown[] {
    const funcTools: unknown[] = [];
    for (const entry of this.functions.values()) {
      funcTools.push(entry.schema);
    }
    return funcTools;
  }
}

const udfManager = new UDFManager();

function registerUdf(
  name: string,
  namespace?: string,
  schema?: UdfSchema,
): (fn: Function) => Function {
  return (fn: Function) => {
    udfManager.registerFunction(fn, namespace, schema, name);
    return fn;
  };
}

export { UDFManager, udfManager, registerUdf };
