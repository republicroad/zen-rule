import { registerUdf } from './register.js';

export const inout = registerUdf(
  'inout',
  undefined,
  {
    parameters: {
      b: { type: 'integer', description: '参数 b' },
      a: { type: 'string', description: '参数 a' },
      c: { type: 'string', description: '参数 c' },
    },
    returns: { type: 'object', description: 'inout 函数返回' },
  },
)(function (kwargs: Record<string, unknown>) {
  return kwargs?.['_node_input_'] ?? {};
});

export const funcWithoutArgs = registerUdf(
  'func_without_args',
  undefined,
  {
    returns: { type: 'object', description: 'func_without_args 函数返回' },
  },
)(function (kwargs: Record<string, unknown>) {
  return kwargs?.['_node_input_'] ?? {};
});
