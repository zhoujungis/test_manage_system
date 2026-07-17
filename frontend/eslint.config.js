// H27 fix: 统一代码风格。Vue 3 + flat config。
import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'

export default [
  js.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.{js,vue}'],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        // Browser
        window: 'readonly',
        document: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        // Vue
        defineProps: 'readonly',
        defineEmits: 'readonly',
        defineExpose: 'readonly',
        withDefaults: 'readonly',
        // Process
        process: 'readonly',
      },
    },
    rules: {
      'vue/multi-word-component-names': 'off',  // LoginView / TestRunListView 都是单词
      'vue/no-v-html': 'error',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': 'off',  // 我们项目里 console.log 是合法调试工具
    },
  },
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        ecmaVersion: 2024,
        sourceType: 'module',
      },
    },
  },
  {
    ignores: ['dist/**', 'node_modules/**', 'coverage/**'],
  },
]