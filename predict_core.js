/*
 * 予想エンジン（共有モジュール）
 *
 * アプリ（app.jsx）とメール通知（predict.js → prediction.json → notify_loto7.py）の
 * 両方からまったく同じロジックを使うため、予想関連の関数をここに集約している。
 * - ブラウザ: build.js がこのファイルを app.jsx の前に連結して index.html に埋め込む（グローバル関数として使う）
 * - Node:     predict.js が require('./predict_core.js') で読み込む
 *
 * ここを変更するとアプリの予想とメールの予想が同時に変わる（ズレない）。
 */

// ── 等級判定 ──
const judgeGrade = (my, win, bon) => {
  const s = new Set(my);
  const m = win.filter(n=>s.has(n)).length;
  const b = bon.filter(n=>s.has(n)).length;
  if(m===7)               return {grade:1,label:"🏆 1等！",color:"#fde047",bg:"#78350f"};
  if(m===6&&b>=1)         return {grade:2,label:"🥇 2等！",color:"#fb923c",bg:"#7c2d12"};
  if(m===6)               return {grade:3,label:"🥈 3等！",color:"#fb923c",bg:"#7c2d12"};
  if(m===5&&b>=1)         return {grade:4,label:"🥉 4等！",color:"#a5b4fc",bg:"#312e81"};
  if(m===5)               return {grade:5,label:"✨ 5等！",color:"#a5b4fc",bg:"#312e81"};
  if(m===4)               return {grade:6,label:"🎉 6等！",color:"#5eead4",bg:"#134e4a"};
  if(m===3||(m===2&&b>=1))return{grade:7,label:"🎊 7等！",color:"#86efac",bg:"#14532d"};
  return null;
};

// ── 統計計算 ──
const calcStats = (history) => {
  const n = history.length;
  // 全期間頻度
  const freq = {}; for(let i=1;i<=37;i++) freq[i]=0;
  history.forEach(d=>d.numbers.forEach(n=>freq[n]++));

  // 重み付きスコア（直近ほど重視）
  const score = {}; for(let i=1;i<=37;i++) score[i]=0;
  history.forEach((d,i)=>{
    const w = Math.exp(-i/(n*0.4));
    d.numbers.forEach(n=>{ score[n]+=w; });
  });

  // 直近20回・直近5回の出現数字
  const recent20 = new Set(history.slice(0,20).flatMap(d=>d.numbers));
  const recent5  = new Set(history.slice(0,5).flatMap(d=>d.numbers));

  // ボーナス数字頻度
  const bonusFreq = {}; for(let i=1;i<=37;i++) bonusFreq[i]=0;
  history.forEach(d=>d.bonus.forEach(n=>bonusFreq[n]++));

  // 連続ペア出現頻度
  const pairFreq = {};
  history.forEach(d=>{
    const nums = [...d.numbers].sort((a,b)=>a-b);
    for(let i=0;i<nums.length-1;i++){
      if(nums[i+1]-nums[i]===1){
        const key=`${nums[i]}-${nums[i+1]}`;
        pairFreq[key]=(pairFreq[key]||0)+1;
      }
    }
  });

  // 同時出現ペア頻度（相性）: 同じ回に一緒に出た2数字の組み合わせを全回分カウント
  const coFreq = {};
  history.forEach(d=>{
    const nums = d.numbers;
    for(let i=0;i<nums.length;i++){
      for(let j=i+1;j<nums.length;j++){
        const a = Math.min(nums[i],nums[j]), b = Math.max(nums[i],nums[j]);
        const key = a+"-"+b;
        coFreq[key]=(coFreq[key]||0)+1;
      }
    }
  });

  // 前回（最新回）の数字＝引っ張り候補
  const lastSet = new Set(history[0] ? history[0].numbers : []);

  // 各数字が何回前に出たか（0=最新回で出た、-1=データ内で未出現）
  const lastSeen = {};
  for(let i=1;i<=37;i++){
    lastSeen[i] = history.findIndex(d=>d.numbers.includes(i));
  }

  // 当選番号の合計値一覧（分布グラフ用）
  const sums = history.map(d=>d.numbers.reduce((a,b)=>a+b,0));

  // 直近20回のボーナス数字
  const recentBonus20 = new Set(history.slice(0,20).flatMap(d=>d.bonus));

  return { freq, score, recent20, recent5, bonusFreq, pairFreq, coFreq, lastSet, lastSeen, sums, recentBonus20, n };
};

// 頻度ランキング（statsから導出）
const byFreqOf = (stats) =>
  Object.entries(stats.freq).map(([n,c])=>({num:+n,count:c})).sort((a,b)=>b.count-a.count);

// ── シード付き乱数（同じ回なら毎回同じ結果＝次回抽選まで固定） ──
let RNG = Math.random;
const mulberry32 = (seed) => {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};
// RNG を使った安定シャッフル（Fisher–Yates）
const rnd = (arr, n) => {
  const a = [...arr];
  for(let i=a.length-1; i>0; i--){
    const j = Math.floor(RNG() * (i+1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a.slice(0, n);
};

// ── セット品質スコア ──
// 合計値の条件を満たした候補の中から「過去の当選パターンに近い形」を選ぶための採点。
// 高いほど典型的な当選回に近い構成。
const setQuality = (pick, stats) => {
  let q = 0;

  // 奇偶バランス: 当選回で最も多いのは奇数3〜4個
  const odd = pick.filter(n=>n%2===1).length;
  q += (odd===3||odd===4) ? 2 : (odd===2||odd===5) ? 1 : 0;

  // ゾーン分散（1-9 / 10-19 / 20-29 / 30-37）: 3ゾーン以上に散っている方が典型的
  const zones = new Set(pick.map(n=> n<10?0 : n<20?1 : n<30?2 : 3)).size;
  q += zones===4 ? 2 : zones===3 ? 1 : -1;

  // ペア相性: セット内21ペアの過去同時出現回数の合計（多いほど「よく一緒に出る組み合わせ」）
  let pairSum = 0;
  for(let i=0;i<pick.length;i++){
    for(let j=i+1;j<pick.length;j++){
      const a = Math.min(pick[i],pick[j]), b = Math.max(pick[i],pick[j]);
      pairSum += stats.coFreq[a+"-"+b]||0;
    }
  }
  // 期待値はおよそ n×0.66（21ペア×出現率21/666）なので、平均が約2点になるよう正規化
  q += stats.n > 0 ? pairSum / (stats.n * 0.33) : 0;

  // 引っ張り（前回の数字の継続）: 実際の抽選では平均1.3個程度が前回と重複する
  const carry = pick.filter(n=>stats.lastSet.has(n)).length;
  q += (carry===1||carry===2) ? 1.5 : carry===0 ? 0 : -0.5;

  return q;
};

// セット間の重複ペナルティ: 既出セットと同じ数字ばかりだと4セット買う意味が薄れるため、
// 使用済み数字1個につき減点して数字の散らばり（カバレッジ）を保つ
const overlapPenalty = (pick, used) => {
  let c = 0;
  pick.forEach(n=>{ if(used.has(n)) c++; });
  return c * 0.5;
};

// ── 予想アルゴリズム ──
// 合計値が目標範囲に入る候補を複数つくり、品質スコア最高の1つを採用する
const predictWithSum = (stats, targetMin, targetMax, useCold=false, used=new Set()) => {
  const sorted = Object.entries(stats.score).map(([n,v])=>({num:+n,score:v})).sort((a,b)=>b.score-a.score);
  const top20 = sorted.slice(0,20).map(x=>x.num);
  const cold = Array.from({length:37},(_,i)=>i+1).filter(n=>!stats.recent20.has(n));
  let best = null, bestQ = -Infinity, found = 0;
  for(let attempt=0; attempt<3000; attempt++){
    let pick;
    if(useCold && cold.length >= 2){
      const coldPick = rnd(cold, 2);
      const hotPool = top20.filter(n=>!coldPick.includes(n));
      pick = [...coldPick, ...rnd(hotPool, 5)];
    } else {
      pick = rnd(top20, 7);
    }
    const s = pick.reduce((a,b)=>a+b, 0);
    if(s < targetMin || s > targetMax) continue;
    const q = setQuality(pick, stats) - overlapPenalty(pick, used);
    if(q > bestQ){ bestQ = q; best = pick; }
    if(++found >= 40) break;  // 合計値OKの候補40個から最良を選ぶ
  }
  if(best) return best.sort((a,b)=>a-b);
  return rnd(sorted.slice(0,15), 7).map(x=>x.num).sort((a,b)=>a-b);
};

// ボーナス数字予想（頻出1個＋コールド1個）
const predictBonus = (stats, excludeNums) => {
  const bonusSorted = Object.entries(stats.bonusFreq).map(([n,v])=>({num:+n,score:v})).sort((a,b)=>b.score-a.score);
  const bonusHot = bonusSorted.slice(0,10).map(x=>x.num).filter(n=>!excludeNums.has(n));
  const bonusCold = Array.from({length:37},(_,i)=>i+1).filter(n=>!stats.recentBonus20.has(n) && !excludeNums.has(n));
  const b1 = bonusHot.length>0 ? bonusHot[Math.floor(RNG()*Math.min(5,bonusHot.length))] : bonusSorted.find(x=>!excludeNums.has(x.num))?.num||14;
  const pool2 = bonusCold.filter(n=>n!==b1);
  const b2 = pool2.length>0 ? pool2[Math.floor(RNG()*pool2.length)] : bonusSorted.filter(x=>!excludeNums.has(x.num)&&x.num!==b1)[0]?.num||20;
  return [b1,b2].sort((a,b)=>a-b);
};

const genSets = (stats, seed) => {
  // 同じ回(seed)なら毎回同じ4セットになるよう乱数を固定
  RNG = mulberry32((seed || 0) + 1);
  const used = new Set();
  const take = (s)=>{ s.forEach(n=>used.add(n)); return s; };
  const s1 = take(predictWithSum(stats, 126, 136, false, used));
  const s2 = take(predictWithSum(stats, 138, 148, false, used));
  const s3 = take(predictWithSum(stats, 126, 143, true,  used));
  const s4 = take(predictWithSum(stats, 129, 137, false, used));
  const sum1=s1.reduce((a,b)=>a+b,0), sum2=s2.reduce((a,b)=>a+b,0);
  const sum3=s3.reduce((a,b)=>a+b,0), sum4=s4.reduce((a,b)=>a+b,0);
  return [
    {label:"🔥 ホット×合計130狙い",    tag:"hot",  desc:`頻出数字で合計${sum1}（出やすい帯126〜136）`,      numbers:s1, bonus:predictBonus(stats,new Set(s1))},
    {label:"⚖️ バランス×合計143狙い",  tag:"bal",  desc:`バランス重視で合計${sum2}（出やすい帯138〜148）`,  numbers:s2, bonus:predictBonus(stats,new Set(s2))},
    {label:"❄️ コールド×合計範囲内",   tag:"cold", desc:`直近未出現を混え合計${sum3}（リバウンド狙い）`,     numbers:s3, bonus:predictBonus(stats,new Set(s3))},
    {label:"🎯 平均合計133狙い",        tag:"con",  desc:`過去平均133.4に近い合計${sum4}を狙う`,             numbers:s4, bonus:predictBonus(stats,new Set(s4))},
  ];
};

// ── 解説生成（統計ベース・ローカル / AI APIは使わない） ──
const jnum = (arr) => arr.map(n=>n+"番").join("・");
const genCommentary = (stats, byFreq, sets) => {
  const hotTop = new Set(byFreq.slice(0,10).map(x=>x.num));
  const lines = sets.map((s,i)=>{
    const sum = s.numbers.reduce((a,b)=>a+b,0);
    const odd = s.numbers.filter(n=>n%2===1).length;
    const recent5In = s.numbers.filter(n=>stats.recent5.has(n));
    const coldIn    = s.numbers.filter(n=>!stats.recent20.has(n));
    const hotIn     = s.numbers.filter(n=>hotTop.has(n));
    const carryIn   = s.numbers.filter(n=>stats.lastSet.has(n));
    const sumDesc = sum<126 ? "やや低め" : sum>148 ? "やや高め" : "過去平均帯(約133)";
    const head =
      s.tag==="hot"  ? "頻出数字中心のホット型" :
      s.tag==="bal"  ? "高めの合計を狙うバランス型" :
      s.tag==="cold" ? "直近未出現を混ぜたリバウンド型" :
                       "平均合計帯を狙う安定型";
    const recent5Only = recent5In.filter(n=>!carryIn.includes(n));
    let detail = "";
    if(carryIn.length)      detail += `前回から続く${jnum(carryIn)}を引っ張り採用。`;
    if(recent5Only.length)  detail += `直近5回でも出た${jnum(recent5Only.slice(0,3))}を含む。`;
    else if(!carryIn.length && hotIn.length) detail += `頻出の${jnum(hotIn.slice(0,3))}を採用。`;
    if(coldIn.length)     detail += `${jnum(coldIn)}は直近20回未出現のリバウンド候補。`;
    return `セット${i+1}: ${head}。合計${sum}（${sumDesc}）・奇偶${odd}:${7-odd}。${detail}`.trim();
  });
  const top3 = byFreq.slice(0,3).map(x=>`${x.num}番(${x.count}回)`).join("・");
  const coldCount = 37 - stats.recent20.size;
  const intro = `${stats.n}回分を分析。全期間の頻出は${top3}。直近20回の未出現は${coldCount}個。各セットは合計値の出やすい帯に加え、奇偶バランス・ゾーン分散・ペア相性・前回からの引っ張りを採点して選んでいます。`;
  return intro + "\n\n" + lines.join("\n");
};

// Node（predict.js）から使えるようにエクスポート。ブラウザではこのifは通らずグローバル関数のまま。
if (typeof module !== "undefined" && module.exports) {
  module.exports = { judgeGrade, calcStats, byFreqOf, mulberry32, genSets, genCommentary };
}
