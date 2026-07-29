"use client";

import { useMemo, useState } from "react";
import generatedData from "../data/generated-results.json";

type Breakdown = { word: string; kana: string; meaning: string };
type AnalyzedSentence = {
  number: number;
  original: string;
  breakdown: Breakdown[];
  translation: string;
};
type Quality = { passed: number; warnings: string[]; critical: string[] };
type Story = {
  id: string;
  title: string;
  author: string;
  source: string;
  sourceLabel: string;
  totalSentences: number;
  preview: string[];
  sentences: AnalyzedSentence[];
  qualityByCount: Record<string, Quality>;
  elapsedSeconds: number;
};

const stories = generatedData.stories as Story[];

function formatForDisplay(sentences: AnalyzedSentence[]) {
  return sentences
    .map((sentence) => {
      const lines = [`【${sentence.number}】`, "", sentence.original];
      sentence.breakdown.forEach((item) => {
        lines.push("", `${item.word} （${item.kana} / ${item.meaning}）`);
      });
      lines.push("", `中文翻譯： ${sentence.translation}`);
      return lines.join("\n");
    })
    .join("\n\n──────────\n\n");
}

function downloadFile(name: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function Home() {
  const [storyId, setStoryId] = useState(stories[0].id);
  const [count, setCount] = useState(5);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const story = stories.find((item) => item.id === storyId) ?? stories[0];
  const selected = story.sentences.slice(0, count);
  const formattedText = useMemo(() => formatForDisplay(selected), [selected]);
  const quality = story.qualityByCount[String(count)];
  const result = {
    story: story.title,
    author: story.author,
    sentenceCount: count,
    quality,
    sentences: selected,
    formattedText,
  };

  return (
    <main className={theme === "dark" ? "app dark" : "app dark slate"}>
      <header className="hero">
        <div className="brand">▣ &nbsp; JAPANESE READING ASSISTANT</div>
        <h1>從喜歡的故事開始，初學者也能讀日文小說。</h1>
        <p>選擇公開文本，就能看到逐字拆解、假名與繁中翻譯的處理成果。</p>
        <div className="demo-note">◉ 展示模式 · 原始 pipeline 預先處理 · 不需 API Key</div>
        <div className="theme-switch" role="group" aria-label="外觀模式">
          <button onClick={() => setTheme("light")} className={theme === "light" ? "active" : ""}>☾ 藍灰</button>
          <button onClick={() => setTheme("dark")} className={theme === "dark" ? "active" : ""}>◐ 深色</button>
        </div>
      </header>

      <section className="dashboard">
        <section className="panel story-panel" aria-label="選擇公開文本與切句預覽">
          <div className="story-input">
            <div className="panel-heading"><b>01</b><div><h2>選擇展示文本</h2><p>使用已確認來源的日文原文節錄。</p></div></div>
            <label className="select-label" htmlFor="story">公開作品</label>
            <select id="story" value={storyId} onChange={(event) => setStoryId(event.target.value)}>
              {stories.map((item) => <option key={item.id} value={item.id}>{item.title}｜{item.author}</option>)}
            </select>
            <div className="source-box"><strong>{story.title}</strong><small>{story.author} · {story.totalSentences} 句展示節錄</small><a href={story.source} target="_blank" rel="noreferrer">查看原文來源 ↗</a></div>
            <div className="field-row"><label htmlFor="count">本次選擇句數</label><select id="count" value={count} onChange={(event) => setCount(Number(event.target.value))}>{[3, 5, 10, 20].map((value) => <option key={value} value={value}>{value} 句</option>)}</select></div>
          </div>
          <div className="story-preview">
            <div className="panel-heading"><b>02</b><div><h2>確認切句預覽</h2><p>共準備 {story.totalSentences} 句，目前展示前 {count} 句。</p></div></div>
            <ol className="sentence-preview">{selected.map((sentence) => <li key={`${story.id}-${sentence.number}`}><span>{String(sentence.number).padStart(2, "0")}</span><p lang="ja">{sentence.original}</p></li>)}</ol>
          </div>
        </section>

        <section className="panel result-panel">
          <div className="result-top"><div><div className="complete">✓ PROCESSING COMPLETE</div><h2>處理結果</h2><p>{story.title} · {count} 句 · {story.elapsedSeconds} 秒</p></div><div className="actions"><button onClick={() => downloadFile(`${story.id}-${count}-analysis.json`, JSON.stringify(result, null, 2), "application/json;charset=utf-8")}>⇩ JSON</button><button onClick={() => downloadFile(`${story.id}-${count}-analysis.txt`, `\uFEFF${formattedText}\n`, "text/plain;charset=utf-8")}>⇩ TXT</button></div></div>
          <div className="quality"><div><span>✓</span><strong>通過</strong><b>{quality.passed}</b></div><div><span>△</span><strong>一般警告</strong><b>{quality.warnings.length}</b></div><div><span>!</span><strong>嚴重問題</strong><b>{quality.critical.length}</b></div><p>✓ 編號、原句、逐字拆解、翻譯與格式檢核皆通過。</p></div>
          <div className="output"><div><strong>輸出結果</strong><small>畫面展示與 TXT 下載皆使用相同排版</small></div><pre lang="ja">{formattedText}</pre></div>
          <aside className="source-footer">資料來源：<a href={story.source} target="_blank" rel="noreferrer">{story.sourceLabel}</a>。此頁僅使用公開展示所需的原文節錄。</aside>
        </section>
      </section>
      <footer>
        <span>Japanese Reading Assistant</span>
        <span>Local-first · 你的 Key、你的文字、你的控制權</span>
      </footer>
    </main>
  );
}
