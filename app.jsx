
const { useState, useEffect, useRef, useMemo } = React;

// ── ストレージ ──
const store = {
  get: (k) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch(_){return null;} },
  set: (k,v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch(_){} },
  del: (k)   => { try { localStorage.removeItem(k); } catch(_){} },
};

// ── 定数 ──
const DATA_JSON_URL = "https://ogachan111.github.io/loto7/data.json";
const SEED_DATA = [{"round": 683, "date": "2026-06-26", "numbers": [11, 21, 22, 25, 28, 29, 36], "bonus": [8, 32]}, {"round": 682, "date": "2026-06-19", "numbers": [11, 14, 17, 23, 28, 30, 36], "bonus": [12, 20]}, {"round": 681, "date": "2026-06-12", "numbers": [1, 10, 12, 13, 19, 33, 35], "bonus": [14, 37]}, {"round": 680, "date": "2026-06-05", "numbers": [9, 10, 22, 26, 27, 31, 36], "bonus": [20, 29]}, {"round": 679, "date": "2026-05-29", "numbers": [6, 8, 9, 18, 22, 24, 35], "bonus": [4, 20]}, {"round": 678, "date": "2026-05-22", "numbers": [2, 6, 12, 15, 24, 26, 34], "bonus": [18, 20]}, {"round": 677, "date": "2026-05-15", "numbers": [5, 6, 7, 8, 15, 17, 19], "bonus": [1, 33]}, {"round": 676, "date": "2026-05-08", "numbers": [2, 6, 15, 19, 20, 22, 27], "bonus": [31, 33]}, {"round": 675, "date": "2026-05-01", "numbers": [5, 8, 16, 18, 24, 28, 31], "bonus": [6, 23]}, {"round": 674, "date": "2026-04-24", "numbers": [1, 6, 7, 9, 12, 22, 26], "bonus": [8, 14]}, {"round": 673, "date": "2026-04-17", "numbers": [6, 9, 10, 12, 16, 24, 32], "bonus": [17, 19]}, {"round": 672, "date": "2026-04-10", "numbers": [7, 11, 15, 16, 17, 24, 33], "bonus": [6, 9]}, {"round": 671, "date": "2026-04-03", "numbers": [7, 13, 16, 22, 28, 33, 36], "bonus": [2, 25]}, {"round": 670, "date": "2026-03-27", "numbers": [3, 4, 9, 10, 18, 21, 37], "bonus": [15, 23]}, {"round": 669, "date": "2026-03-20", "numbers": [3, 5, 6, 7, 9, 13, 16], "bonus": [11, 23]}, {"round": 668, "date": "2026-03-13", "numbers": [1, 8, 11, 14, 18, 22, 29], "bonus": [19, 35]}, {"round": 667, "date": "2026-03-06", "numbers": [9, 13, 20, 22, 28, 29, 33], "bonus": [21, 23]}, {"round": 666, "date": "2026-02-27", "numbers": [2, 17, 18, 22, 23, 25, 33], "bonus": [16, 34]}, {"round": 665, "date": "2026-02-20", "numbers": [6, 8, 14, 19, 22, 25, 35], "bonus": [12, 17]}, {"round": 664, "date": "2026-02-13", "numbers": [3, 6, 8, 14, 21, 22, 31], "bonus": [17, 37]}, {"round": 663, "date": "2026-02-06", "numbers": [4, 6, 10, 11, 13, 17, 23], "bonus": [25, 32]}, {"round": 662, "date": "2026-01-30", "numbers": [4, 14, 15, 21, 22, 24, 37], "bonus": [5, 20]}, {"round": 661, "date": "2026-01-23", "numbers": [7, 12, 17, 22, 31, 34, 35], "bonus": [20, 32]}, {"round": 660, "date": "2026-01-16", "numbers": [4, 6, 12, 13, 16, 17, 31], "bonus": [14, 20]}, {"round": 659, "date": "2026-01-09", "numbers": [2, 8, 9, 14, 27, 34, 36], "bonus": [5, 18]}, {"round": 658, "date": "2025-12-26", "numbers": [10, 12, 16, 18, 19, 22, 37], "bonus": [11, 20]}, {"round": 657, "date": "2025-12-19", "numbers": [9, 11, 16, 23, 27, 29, 32], "bonus": [6, 24]}, {"round": 656, "date": "2025-12-12", "numbers": [1, 4, 6, 20, 30, 34, 37], "bonus": [14, 25]}, {"round": 655, "date": "2025-12-05", "numbers": [4, 5, 12, 13, 24, 26, 33], "bonus": [3, 14]}, {"round": 654, "date": "2025-11-28", "numbers": [3, 12, 25, 29, 30, 32, 33], "bonus": [28, 31]}, {"round": 653, "date": "2025-11-21", "numbers": [6, 7, 12, 25, 26, 30, 33], "bonus": [13, 15]}, {"round": 652, "date": "2025-11-14", "numbers": [1, 16, 21, 26, 27, 30, 35], "bonus": [6, 37]}, {"round": 651, "date": "2025-11-07", "numbers": [2, 13, 19, 20, 24, 26, 35], "bonus": [29, 36]}, {"round": 650, "date": "2025-10-31", "numbers": [1, 8, 10, 14, 25, 33, 35], "bonus": [12, 21]}, {"round": 649, "date": "2025-10-24", "numbers": [12, 22, 23, 26, 33, 35, 37], "bonus": [2, 21]}, {"round": 648, "date": "2025-10-17", "numbers": [3, 17, 19, 24, 28, 29, 35], "bonus": [7, 13]}, {"round": 647, "date": "2025-10-10", "numbers": [4, 5, 9, 13, 17, 22, 28], "bonus": [18, 31]}, {"round": 646, "date": "2025-10-03", "numbers": [5, 12, 13, 15, 18, 35, 37], "bonus": [11, 29]}, {"round": 645, "date": "2025-09-26", "numbers": [7, 10, 16, 20, 26, 32, 35], "bonus": [24, 33]}, {"round": 644, "date": "2025-09-19", "numbers": [1, 11, 12, 14, 20, 26, 29], "bonus": [2, 5]}, {"round": 643, "date": "2025-09-12", "numbers": [1, 5, 15, 16, 18, 27, 34], "bonus": [19, 22]}, {"round": 642, "date": "2025-09-05", "numbers": [1, 7, 22, 23, 33, 34, 35], "bonus": [2, 24]}, {"round": 641, "date": "2025-08-29", "numbers": [1, 3, 7, 23, 24, 33, 36], "bonus": [17, 30]}, {"round": 640, "date": "2025-08-22", "numbers": [2, 7, 9, 12, 13, 14, 29], "bonus": [15, 30]}, {"round": 639, "date": "2025-08-15", "numbers": [5, 9, 12, 15, 30, 31, 34], "bonus": [13, 29]}, {"round": 638, "date": "2025-08-08", "numbers": [1, 6, 18, 19, 35, 36, 37], "bonus": [11, 24]}, {"round": 637, "date": "2025-08-01", "numbers": [1, 4, 7, 8, 9, 20, 21], "bonus": [11, 30]}, {"round": 636, "date": "2025-07-25", "numbers": [10, 14, 17, 20, 26, 27, 29], "bonus": [3, 11]}, {"round": 635, "date": "2025-07-18", "numbers": [10, 12, 20, 29, 30, 31, 34], "bonus": [4, 15]}, {"round": 634, "date": "2025-07-11", "numbers": [2, 12, 18, 29, 32, 36, 37], "bonus": [5, 21]}];
const AUTO_MS = 10*60*1000;

// ── 予想ロジックは predict_core.js（共有モジュール）にある ──
// judgeGrade / calcStats / byFreqOf / genSets / genCommentary はビルド時に
// このファイルの前に連結されるグローバル関数（メール通知と同一ロジック）。

// ── Ball コンポーネント ──
const BALL_COLORS = {
  main:"linear-gradient(135deg,#6366f1,#3b82f6)",
  bonus:"linear-gradient(135deg,#f43f5e,#ec4899)",
  hot:"linear-gradient(135deg,#f97316,#d97706)",
  cold:"linear-gradient(135deg,#0ea5e9,#1d4ed8)",
  bal:"linear-gradient(135deg,#8b5cf6,#7c3aed)",
  con:"linear-gradient(135deg,#10b981,#0d9488)",
  hit:"linear-gradient(135deg,#eab308,#f59e0b)",
};
const Ball = ({num, type="main", sm=false, hl=false}) => (
  <div style={{
    width:sm?32:44, height:sm?32:44, borderRadius:"50%",
    background: hl ? BALL_COLORS.hit : (BALL_COLORS[type]||BALL_COLORS.main),
    color:"#fff", fontWeight:700, fontSize:sm?11:13,
    display:"flex", alignItems:"center", justifyContent:"center",
    boxShadow: hl?"0 0 0 2px #fde047, 0 2px 8px rgba(0,0,0,.4)":"0 2px 8px rgba(0,0,0,.4)",
    flexShrink:0, transform: hl?"scale(1.1)":"scale(1)",
    transition:"transform .2s",
  }}>
    {String(num).padStart(2,"0")}
  </div>
);

const TAG_BG     = {hot:"rgba(120,53,15,.45)",cold:"rgba(12,74,110,.45)",bal:"rgba(46,16,101,.45)",con:"rgba(6,78,59,.45)"};
const TAG_BORDER = {hot:"rgba(249,115,22,.4)",cold:"rgba(14,165,233,.3)",bal:"rgba(139,92,246,.4)",con:"rgba(16,185,129,.4)"};
const TAG_COLOR  = {hot:"#fb923c",cold:"#38bdf8",bal:"#c4b5fd",con:"#6ee7b7"};

function App() {
  const [tab,setTab]       = useState("predict");
  const [loading,setLoading] = useState(false);
  const [aiMsg,setAiMsg]   = useState("");
  const [history,setHistory] = useState(SEED_DATA);
  const [dataLoaded,setDataLoaded] = useState(false); // data.json読込済みか
  const [fetchSt,setFetchSt] = useState("idle");
  const [sets,setSets]     = useState([]);
  const [saved,setSaved]   = useState(()=>store.get("loto7_saved"));
  const [alerts,setAlerts] = useState([]);
  const [checkedRound,setCheckedRound] = useState(()=>store.get("loto7_checked"));
  const [lastUp,setLastUp] = useState(null);
  const [countdown,setCountdown] = useState(null);
  const fetched = useRef(false);
  const intv    = useRef(null);
  const cntdwn  = useRef(null);

  // 統計計算（682件対応）
  const stats = useMemo(()=>calcStats(history),[history]);
  const byFreq = useMemo(()=>byFreqOf(stats),[stats]);
  const maxF = byFreq[0]?.count || 1;

  // 合計値の分布（60〜219を幅10で16ビン）と平均
  const sumHist = useMemo(()=>{
    const bins = Array.from({length:16},(_,i)=>({lo:60+i*10, count:0}));
    stats.sums.forEach(s=>{
      const idx = Math.min(15, Math.max(0, Math.floor((s-60)/10)));
      bins[idx].count++;
    });
    const avg = stats.sums.length ? stats.sums.reduce((a,b)=>a+b,0)/stats.sums.length : 0;
    return {bins, avg, max: Math.max(1,...bins.map(b=>b.count))};
  },[stats]);

  // 眠り数字（出ていない回数が多い順）
  const sleepers = useMemo(()=>
    Object.entries(stats.lastSeen)
      .map(([n,idx])=>({num:+n, gap: idx<0 ? stats.n : idx}))
      .sort((a,b)=>b.gap-a.gap).slice(0,8),
  [stats]);

  // ── バックテスト（成績タブ）──
  // 予想はシード固定で決定論的なので、「その回の抽選前に出していたはずの予想」を
  // 過去データから再現して実際の当選番号と照合できる。
  const [backtest,setBacktest] = useState(null);
  const computeBacktest = (hist) => {
    const N = Math.min(20, Math.max(0, hist.length - 30)); // 直近20回（統計用に30回分は残す）
    const rows = [];
    const gradeCount = {};
    const tagStats = {hot:{hits:0},bal:{hits:0},cold:{hits:0},con:{hits:0}};
    let totalHits = 0, setCount = 0;
    for(let i=0; i<N; i++){
      const actual = hist[i];
      const past = hist.slice(i+1);
      const st = calcStats(past);
      const predSets = genSets(st, past[0].round);
      const sets = predSets.map(s=>{
        const hits = s.numbers.filter(n=>actual.numbers.includes(n)).length;
        const bHits = s.numbers.filter(n=>actual.bonus.includes(n)).length;
        const g = judgeGrade(s.numbers, actual.numbers, actual.bonus);
        totalHits += hits; setCount++;
        tagStats[s.tag].hits += hits;
        if(g) gradeCount[g.grade] = (gradeCount[g.grade]||0)+1;
        return {tag:s.tag, label:s.label, numbers:s.numbers, hits, bHits, grade:g};
      });
      rows.push({round:actual.round, date:actual.date, win:actual.numbers, bonus:actual.bonus, sets});
    }
    return {rows, N, avg: setCount ? totalHits/setCount : 0, gradeCount, tagStats, latestRound: hist[0]?.round};
  };
  useEffect(()=>{
    if(tab==="results" && history.length>30 && (!backtest || backtest.latestRound!==history[0].round)){
      setBacktest(computeBacktest(history));
    }
  },[tab,history]);
  const [openRound,setOpenRound] = useState(null);

  // 当選照合
  const checkWins = (hist, sv) => {
    if(!sv||!sv.length) return;
    const latest = hist[0]; if(!latest) return;
    if(checkedRound===latest.round) return;
    const al=[];
    sv.forEach((s,si)=>{
      const res=judgeGrade(s.numbers,latest.numbers,latest.bonus);
      if(res) al.push({...res,si,setLabel:s.label,setNums:s.numbers,
        round:latest.round,date:latest.date,winNums:latest.numbers,bonNums:latest.bonus});
    });
    setAlerts(al);
    setCheckedRound(latest.round);
    store.set("loto7_checked",latest.round);
  };

  // ① data.jsonを読み込む（682件）
  const loadDataJson = async () => {
    try {
      const res = await fetch(DATA_JSON_URL + "?t=" + Date.now());
      if(!res.ok) throw new Error("fetch failed");
      const data = await res.json();
      if(Array.isArray(data) && data.length > 0){
        // SEED_DATAとマージして重複除去
        const merged = [...data, ...SEED_DATA]
          .filter((v,i,a)=>a.findIndex(x=>x.round===v.round)===i)
          .sort((a,b)=>b.round-a.round);
        setHistory(merged);
        setDataLoaded(true);
        setLastUp(new Date());
        return merged;
      }
    } catch(e){
      console.warn("data.json読込失敗:", e);
    }
    return null;
  };

  // ② 最新データを再取得（GitHub上のdata.jsonを読み直す。毎週Actionsが自動更新）
  const fetchLatest = async (sv, hist) => {
    setFetchSt("fetching");
    const merged = await loadDataJson();
    if(merged){
      setFetchSt("done");
      setCountdown(AUTO_MS/1000);
      checkWins(merged, sv!==undefined?sv:saved);
    } else {
      setFetchSt("error"); setLastUp(new Date());
    }
  };

  useEffect(()=>{
    if(!fetched.current){
      fetched.current = true;
      fetchLatest(saved);
    }
    intv.current   = setInterval(()=>fetchLatest(null, null), AUTO_MS);
    cntdwn.current = setInterval(()=>setCountdown(p=>p===null?null:p<=1?AUTO_MS/1000:p-1),1000);
    return()=>{ clearInterval(intv.current); clearInterval(cntdwn.current); };
  },[]);

  useEffect(()=>{ if(saved&&history.length) checkWins(history,saved); },[saved]);

  const fmtCnt = s=>s===null?"":`${Math.floor(s/60)}:${String(s%60).padStart(2,"0")}`;

  // 予想生成
  const generate = () => {
    setLoading(true);
    // 最新回の番号をシードに → 同じ回なら毎回同じ4セット（次回抽選まで固定）
    const g = genSets(stats, history[0]?.round || 0);
    setSets(g);
    setAiMsg(genCommentary(stats, byFreq, g));
    setLoading(false);
  };

  const registerSets = () => {
    if(!sets.length) return;
    setSaved(sets); store.set("loto7_saved",sets);
    setAlerts([]); setCheckedRound(null); store.del("loto7_checked");
    alert("✅ 4セットを登録しました！\n次回抽選後に自動で当選チェックします。");
  };

  const latest = history[0];

  const tabs=[
    {id:"predict",icon:"🎯",label:"予想"},
    {id:"mysets", icon:"📌",label:"購入"},
    {id:"results",icon:"🏅",label:"成績"},
    {id:"history",icon:"📋",label:"履歴"},
    {id:"stats",  icon:"📊",label:"統計"},
  ];

  return (
    <div style={{minHeight:"100vh",background:"linear-gradient(160deg,#0f0e1a 0%,#1e1b4b 50%,#0f0e1a 100%)",color:"#f1f5f9",fontFamily:"-apple-system,sans-serif",paddingBottom:80}}>

      {/* ヘッダー */}
      <div className="safe-top" style={{background:"rgba(30,27,75,.85)",backdropFilter:"blur(12px)",WebkitBackdropFilter:"blur(12px)",borderBottom:"1px solid rgba(99,102,241,.25)",padding:"12px 16px 12px"}}>
        <div style={{textAlign:"center"}}>
          <div style={{fontSize:28,lineHeight:1}}>🎯</div>
          <h1 style={{margin:"4px 0 0",fontSize:18,fontWeight:900,letterSpacing:"-0.02em"}}>LOTO7 <span style={{color:"#a5b4fc"}}>予想アプリ</span></h1>
          <p style={{margin:"2px 0 0",fontSize:11,color:"#64748b"}}>📊 {stats.n}回分データ × 統計分析 × 当選自動チェック</p>
        </div>
      </div>

      {/* 当選アラート */}
      {alerts.length>0&&(
        <div style={{padding:"12px 16px 0"}} className="slidein">
          {alerts.map((a,i)=>(
            <div key={i} className="pulse-slow" style={{background:`linear-gradient(135deg,${a.bg}cc,${a.bg}99)`,border:`1.5px solid ${a.color}88`,borderRadius:16,padding:16,marginBottom:10}}>
              <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:8}}>
                <span style={{fontSize:20,fontWeight:900,color:a.color}}>{a.label}</span>
                <span style={{fontSize:11,color:"#cbd5e1"}}>第{a.round}回 ({a.date})</span>
              </div>
              <p style={{fontSize:12,color:"#e2e8f0",marginBottom:8}}>{a.setLabel} が当選！</p>
              <div style={{display:"flex",flexWrap:"wrap",gap:6,marginBottom:4}}>
                {a.setNums.map(n=><Ball key={n} num={n} sm type={a.winNums.includes(n)?"hit":a.bonNums.includes(n)?"bonus":"main"} hl={a.winNums.includes(n)}/>)}
              </div>
              <p style={{fontSize:10,color:"#94a3b8"}}>黄色 = 本数字一致</p>
            </div>
          ))}
          <button onClick={()=>setAlerts([])} style={{width:"100%",padding:"6px",background:"none",border:"none",color:"#64748b",fontSize:12,cursor:"pointer"}}>閉じる ×</button>
        </div>
      )}



      {/* タブコンテンツ */}
      <div style={{padding:"16px 16px 0"}} className="scroll-area">

        {/* 予想タブ */}
        {tab==="predict"&&(
          <div>
            {latest&&(
              <div style={{background:"rgba(30,27,75,.6)",border:"1px solid rgba(99,102,241,.25)",borderRadius:14,padding:14,marginBottom:14}}>
                <p style={{margin:"0 0 8px",fontSize:11,color:"#64748b"}}>第{latest.round}回 当選番号 ({latest.date})</p>
                <div style={{display:"flex",flexWrap:"wrap",gap:8,marginBottom:8}}>
                  {latest.numbers.map(n=><Ball key={n} num={n} type="main"/>)}
                </div>
                <div style={{display:"flex",alignItems:"center",gap:6}}>
                  <span style={{fontSize:11,color:"#f43f5e",fontWeight:700}}>B</span>
                  {latest.bonus.map(n=><Ball key={n} num={n} type="bonus" sm/>)}
                </div>
              </div>
            )}
            <button onClick={generate} disabled={loading}
              style={{width:"100%",padding:"16px",background:"linear-gradient(135deg,#4f46e5,#7c3aed)",color:"#fff",border:"none",borderRadius:14,fontSize:17,fontWeight:900,cursor:"pointer",marginBottom:16,opacity:loading?.6:1,letterSpacing:"-.01em"}}>
              {loading?<span><span className="spin">⚙️</span> 生成中...</span>:`✨ 予想番号を生成する（${stats.n}回分析）`}
            </button>

            {sets.length>0&&(
              <div>
                <p style={{textAlign:"center",fontSize:11,color:"#475569",marginBottom:12}}>── {stats.n}回分データによる4種アルゴリズム予想 ──</p>
                {sets.map((s,i)=>(
                  <div key={i} style={{background:TAG_BG[s.tag],border:`1px solid ${TAG_BORDER[s.tag]}`,borderRadius:14,padding:14,marginBottom:12}}>
                    <div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}>
                      <span style={{fontSize:12,fontWeight:700,color:TAG_COLOR[s.tag]}}>{s.label}</span>
                      <span style={{fontSize:10,color:"#334155"}}>セット{i+1}</span>
                    </div>
                    <p style={{fontSize:11,color:"#475569",margin:"0 0 10px"}}>{s.desc}</p>
                    <div style={{display:"flex",flexWrap:"wrap",gap:8,marginBottom:s.bonus?8:0}}>
                      {s.numbers.map(n=><Ball key={n} num={n} type={s.tag}/>)}
                    </div>
                    {s.bonus&&(
                      <div style={{display:"flex",alignItems:"center",gap:6}}>
                        <span style={{fontSize:11,color:"#f43f5e",fontWeight:700}}>B予想</span>
                        {s.bonus.map(n=><Ball key={n} num={n} type="bonus" sm/>)}
                        <span style={{fontSize:10,color:"#475569"}}>（参考）</span>
                      </div>
                    )}
                  </div>
                ))}
                {aiMsg&&(
                  <div style={{background:"rgba(120,53,15,.2)",border:"1px solid rgba(217,119,6,.3)",borderRadius:14,padding:14,marginBottom:12}}>
                    <p style={{margin:"0 0 6px",fontSize:11,fontWeight:700,color:"#fbbf24"}}>🤖 解説（{stats.n}回分析）</p>
                    <p style={{margin:0,fontSize:12,color:"#e2e8f0",lineHeight:1.7,whiteSpace:"pre-line"}}>{aiMsg}</p>
                  </div>
                )}
                <button onClick={registerSets}
                  style={{width:"100%",padding:"13px",background:"linear-gradient(135deg,#065f46,#0f766e)",color:"#fff",border:"none",borderRadius:14,fontSize:14,fontWeight:700,cursor:"pointer",marginBottom:6}}>
                  📌 この4セットを購入番号として登録する
                </button>
                <p style={{textAlign:"center",fontSize:10,color:"#334155",marginBottom:4}}>登録すると抽選後に自動で当選チェックします</p>
                <p style={{textAlign:"center",fontSize:10,color:"#475569",marginBottom:4}}>🔒 この予想は次回抽選まで固定です（何度押しても同じ番号）</p>
                <p style={{textAlign:"center",fontSize:10,color:"#334155",marginBottom:16}}>※予想は統計分析に基づきます。当選を保証するものではありません。</p>
              </div>
            )}
          </div>
        )}

        {/* 購入セットタブ */}
        {tab==="mysets"&&(
          <div>
            {saved?(
              <>
                <div style={{background:"rgba(6,78,59,.2)",border:"1px solid rgba(16,185,129,.3)",borderRadius:14,padding:12,marginBottom:14}}>
                  <p style={{margin:"0 0 2px",fontSize:11,fontWeight:700,color:"#6ee7b7"}}>📌 登録中の購入セット</p>
                  <p style={{margin:0,fontSize:11,color:"#475569"}}>抽選結果更新時に自動で当選チェックします</p>
                </div>
                {saved.map((s,i)=>(
                  <div key={i} style={{background:TAG_BG[s.tag],border:`1px solid ${TAG_BORDER[s.tag]}`,borderRadius:14,padding:14,marginBottom:12}}>
                    <div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}>
                      <span style={{fontSize:12,fontWeight:700,color:TAG_COLOR[s.tag]}}>{s.label}</span>
                      <span style={{fontSize:10,color:"#334155"}}>セット{i+1}</span>
                    </div>
                    <p style={{fontSize:11,color:"#475569",margin:"0 0 10px"}}>{s.desc}</p>
                    <div style={{display:"flex",flexWrap:"wrap",gap:8,marginBottom:6}}>
                      {s.numbers.map(n=>{
                        const isHit=latest?.numbers.includes(n);
                        return <Ball key={n} num={n} type={s.tag} hl={isHit}/>;
                      })}
                    </div>
                    {latest&&(
                      <p style={{fontSize:10,color:"#475569",margin:0}}>
                        最新回(第{latest.round}回)一致: {s.numbers.filter(n=>latest.numbers.includes(n)).length}個
                        {s.numbers.filter(n=>latest.bonus.includes(n)).length>0?` + ボーナス${s.numbers.filter(n=>latest.bonus.includes(n)).length}個`:""}
                      </p>
                    )}
                  </div>
                ))}
                <button onClick={()=>{if(confirm("登録を解除しますか？")){setSaved(null);setAlerts([]);store.del("loto7_saved");}}}
                  style={{width:"100%",padding:"10px",background:"rgba(51,65,85,.5)",color:"#94a3b8",border:"none",borderRadius:12,fontSize:12,cursor:"pointer",marginBottom:16}}>
                  🗑️ 登録解除
                </button>
              </>
            ):(
              <div style={{textAlign:"center",padding:"60px 0",color:"#475569"}}>
                <div style={{fontSize:40,marginBottom:12}}>📌</div>
                <p style={{fontSize:14,margin:"0 0 4px"}}>購入セットが登録されていません</p>
                <p style={{fontSize:11,color:"#334155",margin:"0 0 20px"}}>「予想」タブで番号を生成して登録してください</p>
                <button onClick={()=>setTab("predict")}
                  style={{padding:"10px 24px",background:"#4f46e5",color:"#fff",border:"none",borderRadius:12,fontSize:13,fontWeight:700,cursor:"pointer"}}>
                  予想を生成する →
                </button>
              </div>
            )}
          </div>
        )}

        {/* 成績タブ（過去予想のバックテスト） */}
        {tab==="results"&&(
          <div>
            {!backtest ? (
              <div style={{textAlign:"center",padding:"60px 0",color:"#475569"}}>
                <div style={{fontSize:32,marginBottom:10}} className="spin">⚙️</div>
                <p style={{fontSize:13}}>過去の予想を再現して照合中...</p>
              </div>
            ):(
              <div>
                <div style={{background:"rgba(67,56,202,.2)",border:"1px solid rgba(99,102,241,.3)",borderRadius:14,padding:14,marginBottom:14}}>
                  <p style={{margin:"0 0 4px",fontSize:12,fontWeight:700,color:"#a5b4fc"}}>🏅 予想の成績（直近{backtest.N}回で検証）</p>
                  <p style={{margin:0,fontSize:10,color:"#64748b",lineHeight:1.6}}>
                    各回の抽選前データだけで「その時の固定予想」を再現し、実際の当選番号と照合した結果です。
                  </p>
                </div>

                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:14}}>
                  <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:12,textAlign:"center"}}>
                    <p style={{margin:"0 0 4px",fontSize:10,color:"#64748b"}}>平均一致数 / 1セット</p>
                    <span style={{fontSize:22,fontWeight:900,color:"#a5b4fc"}}>{backtest.avg.toFixed(2)}個</span>
                    <p style={{margin:"4px 0 0",fontSize:9,color:"#334155"}}>参考: ランダム購入の期待値は約1.32個</p>
                  </div>
                  <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:12,textAlign:"center"}}>
                    <p style={{margin:"0 0 4px",fontSize:10,color:"#64748b"}}>当選（{backtest.N}回×4セット中）</p>
                    {Object.keys(backtest.gradeCount).length ? (
                      <span style={{fontSize:14,fontWeight:700,color:"#86efac"}}>
                        {Object.entries(backtest.gradeCount).sort((a,b)=>a[0]-b[0]).map(([g,c])=>`${g}等×${c}`).join(" ")}
                      </span>
                    ):(
                      <span style={{fontSize:14,fontWeight:700,color:"#64748b"}}>該当なし</span>
                    )}
                    <p style={{margin:"4px 0 0",fontSize:9,color:"#334155"}}>7等=本数字3個一致など</p>
                  </div>
                </div>

                <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:12,marginBottom:14}}>
                  <p style={{margin:"0 0 8px",fontSize:11,color:"#64748b"}}>型別の平均一致数（{backtest.N}回平均）</p>
                  {[["hot","🔥 ホット型"],["bal","⚖️ バランス型"],["cold","❄️ コールド型"],["con","🎯 安定型"]].map(([tag,name])=>{
                    const avg = backtest.N ? backtest.tagStats[tag].hits/backtest.N : 0;
                    return (
                      <div key={tag} style={{display:"flex",alignItems:"center",gap:8,marginBottom:5}}>
                        <span style={{fontSize:11,color:TAG_COLOR[tag],width:92}}>{name}</span>
                        <div style={{flex:1,background:"rgba(255,255,255,.06)",borderRadius:4,height:6}}>
                          <div style={{height:6,background:TAG_COLOR[tag],borderRadius:4,width:`${Math.min(100,avg/3*100)}%`}}/>
                        </div>
                        <span style={{fontSize:10,color:"#475569",width:44,textAlign:"right"}}>{avg.toFixed(2)}個</span>
                      </div>
                    );
                  })}
                </div>

                <p style={{fontSize:11,color:"#475569",marginBottom:8}}>回ごとの結果（タップで詳細）</p>
                {backtest.rows.map(r=>(
                  <div key={r.round} onClick={()=>setOpenRound(openRound===r.round?null:r.round)}
                    style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:12,marginBottom:8,cursor:"pointer"}}>
                    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                      <span style={{fontSize:12,fontWeight:700,color:"#818cf8"}}>第{r.round}回 <span style={{fontSize:10,color:"#475569",fontWeight:400}}>{r.date}</span></span>
                      <div style={{display:"flex",gap:6,alignItems:"center"}}>
                        {r.sets.map((s,i)=>(
                          <span key={i} style={{fontSize:11,fontWeight:700,color:s.hits>=3?"#fde047":s.hits>=2?TAG_COLOR[s.tag]:"#475569"}}>
                            {s.label.slice(0,2)}{s.hits}
                          </span>
                        ))}
                        <span style={{fontSize:10,color:"#334155"}}>{openRound===r.round?"▲":"▼"}</span>
                      </div>
                    </div>
                    {r.sets.some(s=>s.grade)&&(
                      <p style={{margin:"6px 0 0",fontSize:11,fontWeight:700,color:"#86efac"}}>
                        {r.sets.filter(s=>s.grade).map(s=>`${s.label} → ${s.grade.label}`).join(" / ")}
                      </p>
                    )}
                    {openRound===r.round&&(
                      <div style={{marginTop:10}}>
                        <p style={{margin:"0 0 6px",fontSize:10,color:"#64748b"}}>当選番号</p>
                        <div style={{display:"flex",flexWrap:"wrap",gap:5,marginBottom:10}}>
                          {r.win.map(n=><Ball key={n} num={n} type="main" sm/>)}
                          <span style={{fontSize:10,color:"#f43f5e",alignSelf:"center",fontWeight:700}}>B</span>
                          {r.bonus.map(n=><Ball key={n} num={n} type="bonus" sm/>)}
                        </div>
                        {r.sets.map((s,i)=>(
                          <div key={i} style={{marginBottom:8}}>
                            <p style={{margin:"0 0 4px",fontSize:10,color:TAG_COLOR[s.tag]}}>{s.label}（{s.hits}個一致{s.bHits?` +B${s.bHits}`:""}{s.grade?` ${s.grade.label}`:""}）</p>
                            <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                              {s.numbers.map(n=><Ball key={n} num={n} type={s.tag} sm hl={r.win.includes(n)}/>)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                <p style={{textAlign:"center",fontSize:10,color:"#334155",margin:"10px 0 16px"}}>
                  ※現在の予想アルゴリズムを過去データに当てはめた検証値です。将来の当選を約束するものではありません。
                </p>
              </div>
            )}
          </div>
        )}

        {/* 履歴タブ */}
        {tab==="history"&&(
          <div>
            <p style={{fontSize:11,color:"#475569",marginBottom:10}}>過去{history.length}回分の当選番号（第1回〜第{history[0]?.round}回）</p>
            {history.map(d=>(
              <div key={d.round} style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:12,marginBottom:10}}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                  <span style={{fontSize:12,fontWeight:700,color:"#818cf8"}}>第{d.round}回</span>
                  <span style={{fontSize:11,color:"#475569"}}>{d.date}</span>
                </div>
                <div style={{display:"flex",flexWrap:"wrap",gap:6,marginBottom:6}}>
                  {d.numbers.map(n=><Ball key={n} num={n} type="main" sm/>)}
                </div>
                <div style={{display:"flex",alignItems:"center",gap:6}}>
                  <span style={{fontSize:10,fontWeight:700,color:"#f43f5e"}}>B</span>
                  {d.bonus.map(n=><Ball key={n} num={n} type="bonus" sm/>)}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 統計タブ */}
        {tab==="stats"&&(
          <div>
            {/* データ量バッジ */}
            <div style={{background:"rgba(67,56,202,.2)",border:"1px solid rgba(99,102,241,.3)",borderRadius:14,padding:12,marginBottom:14,textAlign:"center"}}>
              <span style={{fontSize:22,fontWeight:900,color:"#a5b4fc"}}>{stats.n}回分</span>
              <span style={{fontSize:12,color:"#64748b",marginLeft:8}}>のデータで分析</span>
              <p style={{margin:"4px 0 0",fontSize:10,color:"#334155"}}>第1回(2013/04/05)〜第{history[0]?.round}回({history[0]?.date})</p>
            </div>

            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:14}}>
              <div style={{background:"rgba(120,53,15,.3)",border:"1px solid rgba(249,115,22,.3)",borderRadius:14,padding:12}}>
                <p style={{margin:"0 0 8px",fontSize:11,color:"#fb923c",fontWeight:700}}>🔥 よく出る TOP5</p>
                <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                  {byFreq.slice(0,5).map(x=>(
                    <div key={x.num} style={{textAlign:"center"}}>
                      <Ball num={x.num} type="hot" sm/>
                      <div style={{fontSize:9,color:"#fb923c",marginTop:2}}>{x.count}回</div>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{background:"rgba(12,74,110,.3)",border:"1px solid rgba(14,165,233,.25)",borderRadius:14,padding:12}}>
                <p style={{margin:"0 0 8px",fontSize:11,color:"#38bdf8",fontWeight:700}}>❄️ 出にくい TOP5</p>
                <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                  {byFreq.slice(-5).reverse().map(x=>(
                    <div key={x.num} style={{textAlign:"center"}}>
                      <Ball num={x.num} type="cold" sm/>
                      <div style={{fontSize:9,color:"#38bdf8",marginTop:2}}>{x.count}回</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 直近20回コールド */}
            <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:14,marginBottom:14}}>
              <p style={{margin:"0 0 8px",fontSize:11,color:"#64748b"}}>❄️ 直近20回未出現（リバウンド候補）</p>
              <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                {Array.from({length:37},(_,i)=>i+1).filter(n=>!stats.recent20.has(n)).map(n=>(
                  <div key={n} style={{textAlign:"center"}}>
                    <Ball num={n} type="cold" sm/>
                  </div>
                ))}
                {Array.from({length:37},(_,i)=>i+1).filter(n=>!stats.recent20.has(n)).length===0&&(
                  <p style={{fontSize:11,color:"#475569"}}>全数字が直近20回以内に出現しています</p>
                )}
              </div>
            </div>

            {/* 合計値の分布 */}
            <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:14,marginBottom:14}}>
              <p style={{margin:"0 0 2px",fontSize:11,color:"#64748b"}}>📈 当選番号の合計値分布（全{stats.n}回）</p>
              <p style={{margin:"0 0 10px",fontSize:10,color:"#334155"}}>平均 {sumHist.avg.toFixed(1)}。<span style={{color:"#a5b4fc"}}>紫のバー</span>が予想の狙う帯（120〜149）</p>
              <div style={{display:"flex",alignItems:"flex-end",gap:2,height:80}}>
                {sumHist.bins.map(b=>{
                  const inBand = b.lo>=120 && b.lo<150;
                  return (
                    <div key={b.lo} style={{flex:1,display:"flex",flexDirection:"column",justifyContent:"flex-end",height:"100%"}}>
                      <div style={{height:`${Math.round(b.count/sumHist.max*100)}%`,minHeight:b.count?2:0,
                        background:inBand?"linear-gradient(180deg,#8b5cf6,#6366f1)":"rgba(100,116,139,.5)",borderRadius:"3px 3px 0 0"}}/>
                    </div>
                  );
                })}
              </div>
              <div style={{display:"flex",gap:2,marginTop:4}}>
                {sumHist.bins.map((b,i)=>(
                  <div key={b.lo} style={{flex:1,textAlign:"center",fontSize:8,color:"#475569"}}>{i%4===0?b.lo:""}</div>
                ))}
              </div>
            </div>

            {/* 眠り数字 */}
            <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:14,marginBottom:14}}>
              <p style={{margin:"0 0 8px",fontSize:11,color:"#64748b"}}>😴 眠り数字ランキング（出ていない回数が多い順）</p>
              <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
                {sleepers.map(s=>(
                  <div key={s.num} style={{textAlign:"center"}}>
                    <Ball num={s.num} type="cold" sm/>
                    <div style={{fontSize:9,color:"#38bdf8",marginTop:2}}>{s.gap}回</div>
                  </div>
                ))}
              </div>
              <p style={{margin:"8px 0 0",fontSize:9,color:"#334155"}}>「N回」= 直近N回の抽選で出ていない（0回=最新回で出た）</p>
            </div>

            <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:14,marginBottom:14}}>
              <p style={{margin:"0 0 10px",fontSize:11,color:"#64748b"}}>📊 出現頻度ランキング（全37数字）</p>
              {byFreq.map((x,i)=>{
                const pct=Math.round((x.count/maxF)*100);
                const type=i<7?"hot":i>=30?"cold":"bal";
                const bc=type==="hot"?"#f97316":type==="cold"?"#64748b":"#8b5cf6";
                return(
                  <div key={x.num} style={{display:"flex",alignItems:"center",gap:8,marginBottom:5}}>
                    <Ball num={x.num} type={type} sm/>
                    <div style={{flex:1,background:"rgba(255,255,255,.06)",borderRadius:4,height:6}}>
                      <div style={{height:6,background:bc,borderRadius:4,width:`${pct}%`}}/>
                    </div>
                    <span style={{fontSize:10,color:"#475569",width:36,textAlign:"right"}}>{x.count}回</span>
                  </div>
                );
              })}
            </div>

            <div style={{background:"rgba(30,27,75,.5)",border:"1px solid rgba(51,65,85,.5)",borderRadius:14,padding:14,marginBottom:14}}>
              <p style={{margin:"0 0 10px",fontSize:11,color:"#64748b"}}>📈 分析サマリー</p>
              {[
                ["分析対象回数",`${stats.n}回（第1〜${history[0]?.round}回）`,"#818cf8"],
                ["最高頻出番号",`${byFreq[0]?.num}番 (${byFreq[0]?.count}回/${stats.n}回)`,"#fb923c"],
                ["最低頻出番号",`${byFreq[36]?.num}番 (${byFreq[36]?.count}回/${stats.n}回)`,"#64748b"],
                ["平均出現回数",`${(stats.n*7/37).toFixed(1)}回`,"#c4b5fd"],
                ["直近20回コールド",`${37-stats.recent20.size}個`,"#38bdf8"],
                ["期間",`2013/04/05〜${history[0]?.date}`,"#6ee7b7"],
              ].map(([k,v,c])=>(
                <div key={k} style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                  <span style={{fontSize:12,color:"#64748b"}}>{k}</span>
                  <span style={{fontSize:12,fontWeight:700,color:c}}>{v}</span>
                </div>
              ))}
            </div>
            <p style={{textAlign:"center",fontSize:10,color:"#334155",marginBottom:16}}>※ロト7は完全ランダム抽選です。統計は参考情報です。</p>
          </div>
        )}
      </div>

      {/* ボトムナビ */}
      <nav className="bottom-nav" style={{background:"rgba(15,14,26,.92)",backdropFilter:"blur(16px)",WebkitBackdropFilter:"blur(16px)",borderTop:"1px solid rgba(99,102,241,.2)"}}>
        <div style={{display:"flex",justifyContent:"space-around",padding:"10px 0 2px"}}>
          {tabs.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)}
              style={{flex:1,background:"none",border:"none",cursor:"pointer",padding:"4px 0 6px",display:"flex",flexDirection:"column",alignItems:"center",gap:2,
                color:tab===t.id?"#818cf8":"#475569",transition:"color .2s"}}>
              <span style={{fontSize:22}}>{t.icon}</span>
              <span style={{fontSize:10,fontWeight:tab===t.id?700:400}}>{t.label}</span>
              {tab===t.id&&<div style={{width:20,height:2,background:"#6366f1",borderRadius:2}}/>}
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
