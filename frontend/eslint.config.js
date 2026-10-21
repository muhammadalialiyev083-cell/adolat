import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import hooks from 'eslint-plugin-react-hooks';
export default tseslint.config(
  { ignores: ['dist/**','node_modules/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  { files:['src/**/*.{ts,tsx}'], plugins:{'react-hooks':hooks}, rules:{
    '@typescript-eslint/no-explicit-any':'off',
    '@typescript-eslint/no-unused-vars':['error',{argsIgnorePattern:'^_',varsIgnorePattern:'^_',caughtErrors:'none'}],
    'react-hooks/rules-of-hooks':'error',
    'react-hooks/exhaustive-deps':'error',
    'no-undef':'off'
  }},
  { files:['tests/**/*.mjs','eslint.config.js'], rules:{'no-undef':'off'} }
);
