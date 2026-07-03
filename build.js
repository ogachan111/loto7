/*
 * ビルドスクリプト: app.jsx (JSXソース) + data.json + index.template.html → index.html
 *
 * 使い方:
 *   npm install @babel/standalone
 *   node build.js
 *
 * - app.jsx の JSX を事前トランスパイルして index.html に埋め込む
 *   （ブラウザ内 babel-standalone が不要になり初回表示が速い）
 * - SEED_DATA は data.json の最新50件から自動注入するので、ソースのSEED_DATAが
 *   古くても出力は常に最新（fetch_loto7.py が data.json を更新する前提）
 *
 * アプリのロジックを変えるときは app.jsx を編集して再ビルドすること。
 */
const fs = require('fs');
const path = require('path');
const Babel = require('@babel/standalone');

const HERE = __dirname;
// 予想エンジン（共有モジュール）を app.jsx の前に連結する。
// ブラウザでは module が無いので export ガードは素通りし、グローバル関数として使える。
const core = fs.readFileSync(path.join(HERE, 'predict_core.js'), 'utf8');
let jsx = fs.readFileSync(path.join(HERE, 'app.jsx'), 'utf8');
const template = fs.readFileSync(path.join(HERE, 'index.template.html'), 'utf8');

// SEED_DATA を data.json の最新50件で差し替え（無ければソースのまま）
try {
  const data = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'));
  const seed = JSON.stringify(data.slice(0, 50));
  jsx = jsx.replace(/const SEED_DATA = \[[\s\S]*?\];/, `const SEED_DATA = ${seed};`);
  console.log(`SEED_DATA: data.json から最新${Math.min(50, data.length)}件を注入`);
} catch (e) {
  console.warn('data.json 読込失敗、app.jsx の SEED_DATA をそのまま使用:', e.message);
}

// JSX → JS（preset react のみ。const/arrow等のES2015+はそのまま=モダンブラウザ前提）
const { code } = Babel.transform(core + '\n' + jsx, {
  // classic ランタイム = React.createElement を出力（CDNのグローバルReactを使う / import無し）
  presets: [['react', { runtime: 'classic' }]],
  filename: 'app.jsx',
  // 日本語/絵文字を \uXXXX にエスケープせずUTF-8のまま出力（読みやすさ・出力の安定）
  generatorOpts: { jsescOption: { minimal: true } },
});

const out = template.replace('/*__APP__*/', code);
fs.writeFileSync(path.join(HERE, 'index.html'), out, 'utf8');
console.log(`✅ index.html を生成（${out.length} bytes）`);
