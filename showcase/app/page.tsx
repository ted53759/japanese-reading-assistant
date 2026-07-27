"use client";

import { useState } from "react";

const sentences = [
  {
    number: "01",
    original: "雨が止んだあと、駅前の小さな本屋に入った。",
    translation: "雨停之後，我走進車站前的一間小書店。",
    words: [
      ["雨", "あめ", "雨"],
      ["が", "が", "主語標記"],
      ["止んだあと", "やんだあと", "停止之後"],
      ["駅前", "えきまえ", "車站前"],
      ["小さな", "ちいさな", "小小的"],
      ["本屋", "ほんや", "書店"],
      ["に", "に", "到；在"],
      ["入った", "はいった", "進入了"],
    ],
  },
  {
    number: "02",
    original: "棚のすみに、青い表紙の古い本が一冊だけ残っていた。",
    translation: "書架角落裡，只剩下一本藍色封面的舊書。",
    words: [
      ["棚", "たな", "書架"],
      ["すみ", "すみ", "角落"],
      ["青い", "あおい", "藍色的"],
      ["表紙", "ひょうし", "封面"],
      ["古い", "ふるい", "舊的"],
      ["一冊", "いっさつ", "一本（書籍量詞）"],
      ["だけ", "だけ", "只有"],
      ["残っていた", "のこっていた", "還留著"],
    ],
  },
  {
    number: "03",
    original: "最初のページに、「ゆっくり読めば大丈夫」と書いてあった。",
    translation: "第一頁寫著：「慢慢讀也沒關係。」",
    words: [
      ["最初", "さいしょ", "最初"],
      ["ページ", "ぺーじ", "頁面"],
      ["ゆっくり", "ゆっくり", "慢慢地"],
      ["読めば", "よめば", "如果讀"],
      ["大丈夫", "だいじょうぶ", "沒關係；沒問題"],
      ["書いてあった", "かいてあった", "寫著"],
    ],
  },
];

const steps = ["切分句子", "建立閱讀卡", "檢查輸出品質"];

export default function Home() {
  const [mode, setMode] = useState<"beginner" | "advanced">("beginner");
  const [progress, setProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [showResult, setShowResult] = useState(false);

  async function playDemo() {
    if (isRunning) return;
    setIsRunning(true);
    setShowResult(false);
    setProgress(0);
    for (const value of [28, 61, 100]) {
      await new Promise((resolve) => window.setTimeout(resolve, 520));
      setProgress(value);
    }
    await new Promise((resolve) => window.setTimeout(resolve, 260));
    setShowResult(true);
    setIsRunning(false);
  }

  return (
    <main>
      <section className="hero">
        <div className="hero-art" aria-hidden="true" />
        <div className="hero-content">
          <p className="eyebrow">Japanese Reading Assistant · public showcase</p>
          <h1>用故事，開始讀懂日文。</h1>
          <p className="hero-copy">
            這是一個將日文長文本轉成可閱讀學習卡的工具展示。從原句、假名到繁中翻譯，讓初學者也能循著故事累積語感。
          </p>
          <div className="hero-tags" aria-label="展示特色">
            <span>自製範例資料</span><span>不需 API Key</span><span>公開安全展示</span>
          </div>
          <a className="source-link" href="https://github.com/ted53759/japanese-reading-assistant" target="_blank" rel="noreferrer">
            查看 GitHub 原始專案 <span aria-hidden="true">↗</span>
          </a>
        </div>
      </section>

      <section className="workspace" aria-labelledby="demo-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Interactive walkthrough</p>
            <h2 id="demo-title">用一段範例，看見完整閱讀流程。</h2>
          </div>
          <div className="mode-switch" role="group" aria-label="閱讀模式">
            <button className={mode === "beginner" ? "active" : ""} onClick={() => setMode("beginner")}>初學者模式</button>
            <button className={mode === "advanced" ? "active" : ""} onClick={() => setMode("advanced")}>進階閱讀</button>
          </div>
        </div>

        <div className="demo-grid">
          <article className="flow-card">
            <div className="card-label">01 · 選擇素材</div>
            <div className="file-card">
              <span className="file-icon">文</span>
              <div><strong>雨後的書店（展示範例）.txt</strong><small>3 句 · 自製日文短文</small></div>
              <span className="ready">已載入</span>
            </div>
            <ol className="preview-list">
              {sentences.map((sentence) => <li key={sentence.number}><span>{sentence.number}</span><p lang="ja">{sentence.original}</p></li>)}
            </ol>
          </article>

          <article className="flow-card process-card">
            <div className="card-label">02 · 模擬處理流程</div>
            <div className="processing-orbit"><span>{isRunning ? `${progress}%` : showResult ? "完成" : "準備"}</span></div>
            <ul className="step-list">
              {steps.map((step, index) => {
                const done = progress >= [28, 61, 100][index];
                return <li key={step} className={done ? "done" : ""}><i>{done ? "✓" : index + 1}</i>{step}</li>;
              })}
            </ul>
            <button className="play-button" onClick={playDemo} disabled={isRunning}>
              {isRunning ? "正在建立閱讀結果…" : showResult ? "重新播放展示" : "播放展示流程"}
            </button>
            <p className="fine-print">展示模式使用預先準備的範例結果，不會上傳內容或呼叫 API。</p>
          </article>

          <article className="flow-card qa-card">
            <div className="card-label">03 · 品質檢核</div>
            <div className="qa-stats"><div><strong>3</strong><span>通過</span></div><div><strong>1</strong><span>提醒</span></div><div><strong>0</strong><span>嚴重問題</span></div></div>
            <div className="qa-pass">✓ 編號、原句、假名與翻譯格式皆已檢查。</div>
            <div className="qa-note"><b>提醒</b><p>第 3 句含引號語氣，建議閱讀者依情境確認中文語感。</p></div>
          </article>
        </div>

        <section className="result-panel" aria-live="polite">
          <div className="result-heading">
            <div><p className="eyebrow">Reading result</p><h2>{showResult ? "閱讀結果已準備完成" : "點擊播放，展開閱讀結果"}</h2></div>
            <span className={showResult ? "status success" : "status"}>{showResult ? "品質檢核完成" : "等待展示"}</span>
          </div>

          {showResult ? (
            <div className="reading-stack">
              {sentences.map((sentence) => <article className="sentence-card" key={sentence.number}>
                <div className="sentence-meta"><span>第 {sentence.number} 句</span><span>日文原句</span></div>
                <p className="original" lang="ja">{sentence.original}</p>
                {mode === "beginner" ? <div className="word-grid">{sentence.words.map(([word, kana, meaning]) => <div className="word-card" key={`${sentence.number}-${word}`}><strong lang="ja">{word}</strong><small lang="ja">{kana}</small><span>{meaning}</span></div>)}</div> : <p className="advanced-hint">先讀原句，再用下方翻譯確認理解。這個模式保留較完整的閱讀節奏。</p>}
                <div className="translation"><span>繁中翻譯</span><p>{sentence.translation}</p></div>
              </article>)}
            </div>
          ) : (
            <div className="empty-result"><span>✦</span><p>從一段安全的範例，看看工具如何把閱讀阻力拆小。</p></div>
          )}
        </section>
      </section>

      <section className="principles">
        <div><span>01</span><h3>長期持續</h3><p>從想讀的故事開始，讓學習成為能維持的日常。</p></div>
        <div><span>02</span><h3>追求效率</h3><p>選擇文字資訊集中、可反覆查閱的小說作為素材。</p></div>
        <div><span>03</span><h3>入門友善</h3><p>逐字拆解、假名與翻譯都在同一個閱讀流程裡。</p></div>
      </section>

      <footer><span>Japanese Reading Assistant</span><span>Portfolio showcase · Built with Python, OpenAI API, Vue and quality checks</span></footer>
    </main>
  );
}
