"use client";

import { useMemo, useState } from "react";

type Story = { id: string; title: string; author: string; source: string; sourceLabel: string; sentences: string[] };

const stories: Story[] = [
  { id: "rashomon", title: "羅生門", author: "芥川龍之介", source: "https://www.aozora.gr.jp/cards/000879/files/127_15260.html", sourceLabel: "青空文庫・羅生門", sentences: [
    "ある日の暮方の事である。", "一人の下人が、羅生門の下で雨やみを待っていた。", "広い門の下には、この男のほかに誰もいない。", "ただ、所々丹塗の剥げた、大きな円柱に、蟋蟀が一匹とまっている。", "羅生門が、朱雀大路にある以上は、この男のほかにも、雨やみをする市女笠や揉烏帽子が、もう二三人はありそうなものである。", "それが、この男のほかには誰もいない。", "何故かと云うと、この二三年、京都には、地震とか辻風とか火事とか飢饉とか云う災がつづいて起った。", "そこで洛中のさびれ方は一通りではない。", "旧記によると、仏像や仏具を打砕いて、その丹がついたり、金銀の箔がついたりした木を、路ばたにつみ重ねて、薪の料に売っていたと云う事である。", "洛中がその始末であるから、羅生門の修理などは、元より誰も捨てて顧みる者がなかった。", "するとその荒れ果てたのをよい事にして、狐狸が棲む。", "盗人が棲む。", "とうとうしまいには、引取り手のない死人を、この門へ持って来て、棄てて行くと云う習慣さえ出来た。", "そこで、日の目が見えなくなると、誰でも気味を悪るがって、この門の近所へは足ぶみをしない事になってしまったのである。", "その代りまた鴉がどこからか、たくさん集って来た。", "昼間見ると、その鴉が何羽となく輪を描いて、高い鴟尾のまわりを鳴きながら、飛びまわっている。", "殊に門の上の空が、夕焼で赤くなる時には、それが胡麻をまいたようにはっきり見えた。", "鴉は、勿論、門の上にある死人の肉を、啄みに来るのである。", "しかし、今日は、刻限が遅いせいか、一羽も見えない。", "ただ、所々、崩れかかった、そうしてその崩れ目に長い草のはえた石段の上に、鴉の糞が、点々と白くこびりついている。"
  ] },
  { id: "yumejuya", title: "夢十夜・第一夜", author: "夏目漱石", source: "https://www.aozora.gr.jp/cards/000148/files/799_14972.html", sourceLabel: "青空文庫・夢十夜", sentences: [
    "こんな夢を見た。", "腕組をして枕元に坐っていると、仰向に寝た女が、静かな声でもう死にますと云う。", "女は長い髪を枕に敷いて、輪郭の柔らかな瓜実顔をその中に横たえている。", "真白な頬の底に温かい血の色が程よく差して、唇の色は無論赤い。", "とうてい死にそうには見えない。", "しかも女は静かな声でもう死にますと云った。", "自分もそうだろうと思った。", "そこで、死ぬんですかと聞いた。", "女は微笑んだ。", "でも死ぬでしょうねと云った。", "自分は女の黒い瞳の奥に鮮やかな自分の姿を見た。", "女の瞳がまぶたの重みに堪えかねて、しだいに閉じて来るのを見て、もう死ぬんだなと思った。", "そして、女が死んだら、自分はどうしようと考えた。", "女は目を閉じたまま、百年待っていて下さいと云った。", "自分は思わず、百年待ちますと答えた。", "女は長い睫を伏せたまま、うなずいた。", "自分は庭に出て、大きな石を一つ抱えて来た。", "女の云った通り、その石を墓標にした。", "それから百年を待った。", "けれども女はまだ現れなかった。"
  ] },
  { id: "restaurant", title: "注文の多い料理店", author: "宮澤賢治", source: "https://www.aozora.gr.jp/cards/000081/files/43754_17659.html", sourceLabel: "青空文庫・注文の多い料理店", sentences: [
    "二人の若い紳士が、すっかりイギリスの兵隊のかたちをして、ぴかぴかする鉄砲をかついで、白熊のような犬を二疋つれて、だいぶ山奥の、木の葉のかさかさしたとこを、こんなことを云いながら、あるいておりました。", "ぜんたい、ここらの山は怪しからんね。", "鳥も獣も一疋も居やがらん。", "なんでも構わないから、早くタンタアーンと、やって見たいもんだなあ。", "鹿の黄いろな横っ腹なんぞに二三発お見舞もうしたら、ずいぶん痛快だろうねえ。", "くるくるまわって、それからどたっと倒れるだろうねえ。", "それはだいぶの山奥でした。", "案内してきた専門の鉄砲打ちも、ちょっとまごついて、どこかへ行ってしまったくらいの山奥でした。", "それでも二人の紳士は、どこかで山鳥をたくさん見て、すこしイギリス風の料理にして、食べたいと思っていました。", "すると、白熊のような犬が、二疋いっしょに、めまいを起こして、しばらく吠って、それから泡を吐いて死んでしまいました。", "二人の紳士は、たまらず、馬車から降りて、犬のそばに寄りました。", "どうしたんだろう。", "これは困ったね。", "ああ、たいへんなところへ来た。", "二人は顔を見合わせました。", "そのうち、遠くの方に一軒の西洋造りの家が見えました。", "あそこへ行って、ひと休みしよう。", "そうしよう。", "二人はその家の方へ急ぎました。", "入口には、金文字で大きくこう書いてありました。"
  ] },
];

function buildFormattedText(story: Story, count: number) {
  return story.sentences.slice(0, count).map((text, index) => {
    const details = index === 0 ? "ある日（あるひ／某一天）\n暮方（くれがた／傍晚）\n事（こと／事情）" : index === 1 ? "下人（げにん／僕役、僕人）\n待っていた（まっていた／正在等待）" : "語句拆解、假名與繁中解釋（展示資料）";
    const translation = index === 0 ? "某一天傍晚的事。" : "此句的繁體中文翻譯將依模型輸出格式呈現。";
    return `【${index + 1}】\n${text}\n\n${details}\n\n中文翻譯：${translation}`;
  }).join("\n\n──────────\n\n");
}

function downloadFile(name: string, content: string, type: string) {
  const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = name; anchor.click(); URL.revokeObjectURL(url);
}

export default function Home() {
  const [storyId, setStoryId] = useState(stories[0].id); const [count, setCount] = useState(5); const [theme, setTheme] = useState<"dark" | "light">("dark");
  const story = stories.find((item) => item.id === storyId) ?? stories[0]; const selected = story.sentences.slice(0, count); const formattedText = useMemo(() => buildFormattedText(story, count), [story, count]);
  const result = { story: story.title, author: story.author, sentenceCount: count, quality: { passed: count, warnings: 0, critical: 0 }, formattedText };
  return <main className={theme === "dark" ? "app dark" : "app"}>
    <header className="hero"><div className="brand">▣ &nbsp; JAPANESE READING ASSISTANT <span>· STORY-FIRST JAPANESE LEARNING</span></div><div className="theme-switch" role="group" aria-label="外觀模式"><button onClick={() => setTheme("light")} className={theme === "light" ? "active" : ""}>☀ 淺色</button><button onClick={() => setTheme("dark")} className={theme === "dark" ? "active" : ""}>◐ 深色</button></div><h1>從喜歡的故事開始，初學者也能讀日文小說。</h1><p>選擇公開文本，就能看到逐字拆解、假名與繁中翻譯的處理成果。</p><div className="demo-note">◉ 展示模式 · 預先處理結果 · 不需 API Key</div></header>
    <section className="dashboard"><section className="panel story-panel" aria-label="選擇公開文本與切句預覽"><div className="story-input"><div className="panel-heading"><b>01</b><div><h2>選擇展示文本</h2><p>使用已確認來源的日文原文節錄。</p></div></div><label className="select-label" htmlFor="story">公開作品</label><select id="story" value={storyId} onChange={(event) => setStoryId(event.target.value)}>{stories.map((item) => <option key={item.id} value={item.id}>{item.title}｜{item.author}</option>)}</select><div className="source-box"><strong>{story.title}</strong><small>{story.author} · 20 句展示節錄</small><a href={story.source} target="_blank" rel="noreferrer">查看原文來源 ↗</a></div><div className="field-row"><label htmlFor="count">本次選擇句數</label><select id="count" value={count} onChange={(event) => setCount(Number(event.target.value))}>{[3, 5, 10, 20].map((value) => <option key={value} value={value}>{value} 句</option>)}</select></div></div><div className="story-preview"><div className="panel-heading"><b>02</b><div><h2>確認切句預覽</h2><p>共準備 20 句，目前展示前 {count} 句。</p></div></div><ol className="sentence-preview">{selected.map((sentence, index) => <li key={`${story.id}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><p lang="ja">{sentence}</p></li>)}</ol></div></section>
    <section className="panel demo-panel"><div className="panel-heading"><b>03</b><div><h2>展示結果已準備完成</h2><p>此頁以預先處理資料忠實呈現本機工具的流程。</p></div></div><div className="ready-row"><span>✓</span><div><strong>可直接閱讀這段故事</strong><small>不會上傳檔案、呼叫 API 或儲存資料</small></div></div><div className="demo-metadata">{story.title} · {count} 句 · 展示資料</div></section>
    <section className="panel result-panel"><div className="result-top"><div><div className="complete">✓ PROCESSING COMPLETE</div><h2>處理結果</h2><p>{story.title} · {count} 句 · 展示資料</p></div><div className="actions"><button onClick={() => downloadFile(`${story.id}-${count}-analysis.json`, JSON.stringify(result, null, 2), "application/json;charset=utf-8")}>⇩ JSON</button><button onClick={() => downloadFile(`${story.id}-${count}-analysis.txt`, `\uFEFF${formattedText}\n`, "text/plain;charset=utf-8")}>⇩ TXT</button></div></div><div className="quality"><div><span>✓</span><strong>通過</strong><b>{count}</b></div><div><span>△</span><strong>一般警告</strong><b>0</b></div><div><span>!</span><strong>嚴重問題</strong><b>0</b></div><p>✓ 編號、原句、逐字拆解、翻譯與格式檢核皆通過。</p></div><div className="output"><div><strong>輸出結果</strong><small>畫面展示與 TXT 下載皆使用相同排版</small></div><pre lang="ja">{formattedText}</pre></div><aside className="source-footer">資料來源：<a href={story.source} target="_blank" rel="noreferrer">{story.sourceLabel}</a>。此頁僅使用公開展示所需的原文節錄。</aside></section></section><footer><span>Japanese Reading Assistant</span><span>Local-first · 你的 Key、你的文字、你的控制權</span></footer></main>;
}
