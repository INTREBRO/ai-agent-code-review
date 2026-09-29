// Jest 配置示例
// https://jestjs.io/docs/configuration

module.exports = {
  // ========== 基础配置 ==========
  rootDir: '.',
  roots: ['<rootDir>/src', '<rootDir>/test'],
  testEnvironment: 'jsdom',  // node | jsdom | jsdom-six
  testURL: 'http://localhost',
  testTimeout: 10000,
  maxWorkers: '50%',  // 并行 worker 数

  // ========== 文件匹配 ==========
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)'
  ],
  testPathIgnorePatterns: [
    '\\\\node_modules\\\\',
    '\\\\dist\\\\',
    '\\\\build\\\\',
    '\\\\coverage\\\\'
  ],

  // ========== 模块处理 ==========
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@types/(.*)$': '<rootDir>/src/types/$1',
    '\\.(css|less|scss|ss)$': 'identity-obj-proxy'
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],

  // ========== 转换 ==========
  transform: {
    '^.+\\.[tj]sx?$': 'babel-jest',
    '^.+\\.css$': '<rootDir>/test/transform/cssTransform.js',
    '^(?!.*\\.css$).*': '<rootDir>/test/transform/fileTransform.js'
  },
  transformIgnorePatterns: [
    '[/\\\\]node_modules[/\\\\].+\\.(js|jsx|ts|tsx)$'
  ],

  // ========== 覆盖率 ==========
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.ts',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!src/**/*.spec.{js,jsx,ts,tsx}',
    '!**/node_modules/**'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'cobertura'],
  coveragePathIgnorePatterns: [
    '\\\\node_modules\\\\',
    '\\\\dist\\\\',
    '\\\\build\\\\'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/ai-review/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    './src/utils/': {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },

  // ========== 设置文件 ==========
  setupFilesAfterEnvironment: ['<rootDir>/test/setupTests.ts'],
  setupFiles: ['<rootDir>/test/setup.js'],

  // ========== 快照 ==========
  snapshotSerializers: ['@emotion/jest/serializer'],
  updateSnapshot: 'new',  // new | always | none

  // ========== 报告 ==========
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: 'test-results',
      outputName: 'junit.xml'
    }],
    ['jest-html-reporters', {
      publicPath: './test-results',
      filename: 'test-report.html'
    }]
  ],

  // ========== 监视模式 ==========
  watchPathIgnorePatterns: ['\\\\coverage\\\\', '\\\\dist\\\\'],
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],

  // ========== 全局变量 ==========
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json'
    }
  },

  // ========== 项目配置（monorepo）==========
  projects: undefined,  // 或指定子项目: ['<rootDir>/packages/*']
};
