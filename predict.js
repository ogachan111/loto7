/*
 * メール通知用の予想データ生成（Node・依存パッケージなし）
 *
 * GitHub Actions の週次更新で data.json 更新後に `node predict.js` を実行し、
 * prediction.json を出力する。notify_loto7.py がこれを読んでメールに載せる。
 *
 * 予想ロジックは predict_core.js（アプリと共有）なので、
 * メールの予想番号はアプリの「🔒固定予想」と必ず一致する。
 *
 * 出力内容:
 *  - review : 今回の抽選前に固定されていた予想（1回前までのデータ+シード）と当選番号の答え合わせ
 *  - next   : 次回に向けた固定予想（全データ+最新回シード）＝アプリの表示と同一
 */
const fs = require('fs');
const path = require('path');
const core = require('./predict_core.js');

const HERE = __dirname;
const data = JSON.parse(fs.readFileSync(path.join(HERE, 'data.json'), 'utf8'))
  .slice().sort((a, b) => b.round - a.round);

if (!data.length) {
  console.error('❌ data.json が空です');
  process.exit(1);
}

const latest = data[0];

// ① 答え合わせ: 今回(latest)の抽選前に固定されていた予想を再現して照合
const past = data.slice(1);
let review = null;
if (past.length > 30) {
  const st = core.calcStats(past);
  const sets = core.genSets(st, past[0].round);
  review = {
    seedRound: past[0].round,
    sets: sets.map(s => {
      const hits = s.numbers.filter(n => latest.numbers.includes(n));
      const bonusHits = s.numbers.filter(n => latest.bonus.includes(n));
      const g = core.judgeGrade(s.numbers, latest.numbers, latest.bonus);
      return { label: s.label, numbers: s.numbers, bonus: s.bonus, hits, bonusHits, grade: g ? g.label : null };
    }),
  };
}

// ② 次回予想: 全データ+最新回シード（アプリの固定予想と同一になる）
const stats = core.calcStats(data);
const byFreq = core.byFreqOf(stats);
const sets = core.genSets(stats, latest.round);
const commentary = core.genCommentary(stats, byFreq, sets);

const out = {
  generatedAt: new Date().toISOString(),
  latest,
  review,
  next: {
    seedRound: latest.round,
    sets: sets.map(s => ({ label: s.label, numbers: s.numbers, bonus: s.bonus })),
    commentaryIntro: commentary.split('\n')[0],
  },
  statsSummary: {
    n: stats.n,
    hotTop3: byFreq.slice(0, 3).map(x => ({ num: x.num, count: x.count })),
    cold20: Array.from({ length: 37 }, (_, i) => i + 1).filter(n => !stats.recent20.has(n)),
  },
};

fs.writeFileSync(path.join(HERE, 'prediction.json'), JSON.stringify(out, null, 1), 'utf8');
console.log(`✅ prediction.json 生成: 第${latest.round}回の答え合わせ + 次回予想（シード${latest.round}）`);
if (review) console.log(`   答え合わせ: ${review.sets.map(s => s.hits.length + '個').join(' / ')}`);
