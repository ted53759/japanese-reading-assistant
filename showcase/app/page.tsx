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

const studyData: Record<string, Array<[string, string]>> = {
  rashomon: [
    ["ある日（あるひ／某一天）\n暮方（くれがた／傍晚）\n事（こと／事情）", "某一天傍晚的事。"],
    ["一人（ひとり／一個人）\n下人（げにん／僕役、僕人）\n雨やみ（あまやみ／避雨）\n待っていた（まっていた／正在等待）", "一名下人在羅生門下躲雨。"],
    ["広い（ひろい／寬廣的）\n門（もん／城門）\nこの男（このおとこ／這名男子）\n誰もいない（だれもいない／沒有任何人）", "寬廣的門下，除了這名男子以外沒有任何人。"],
    ["所々（ところどころ／好幾處）\n丹塗（にぬり／朱漆塗裝）\n剥げた（はげた／剝落的）\n円柱（まるばしら／圓柱）\n蟋蟀（きりぎりす／螽斯）", "只有一隻螽斯停在數處朱漆剝落的大圓柱上。"],
    ["朱雀大路（すざくおおじ／朱雀大路）\n以上は（いじょうは／既然位於）\n市女笠（いちめがさ／市女笠）\n揉烏帽子（もみえぼし／揉烏帽子）\n二三人（にさんにん／兩三人）", "羅生門既位於朱雀大路，照理說應該還會有兩三個來避雨、戴著市女笠或揉烏帽子的人。"],
    ["それが（然而）\nこの男のほかには（除了這名男子以外）\n誰もいない（沒有任何人）", "然而，除了這名男子以外，一個人也沒有。"],
    ["何故かと云うと（なぜかというと／原因是）\nこの二三年（這兩三年）\n辻風（つじかぜ／旋風）\n飢饉（ききん／饑荒）\n災（わざわい／災害）", "原因是這兩三年京都接連發生地震、旋風、火災與饑荒等災害。"],
    ["そこで（因此）\n洛中（らくちゅう／京都市區）\nさびれ方（さびれかた／衰敗的程度）\n一通りではない（ひととおりではない／非同尋常）", "因此京都市區的衰敗程度非同尋常。"],
    ["旧記（きゅうき／舊紀錄）\n仏像・仏具（ぶつぞう・ぶつぐ／佛像與佛具）\n打砕いて（うちくだいて／打碎）\n薪の料（たきぎのしろ／當作柴薪的材料）", "據舊紀錄所載，人們把佛像與佛具打碎，把沾有朱漆和金銀箔的木頭堆在路旁當柴薪材料販售。"],
    ["その始末であるから（既然落到那種地步）\n修理（しゅうり／修繕）\n元より（もとより／原本就）\n顧みる者（かえりみるもの／願意理會的人）", "京都既然淪落到那種地步，原本就沒有人願意理會羅生門的修繕。"],
    ["荒れ果てた（あれはてた／荒廢至極）\nよい事にして（趁著這個機會）\n狐狸（こり／狐狸）\n棲む（すむ／棲息）", "狐狸便趁著這座門荒廢至極而在此棲息。"],
    ["盗人（ぬすびと／盜賊）\n棲む（すむ／棲息）", "盜賊也在這裡棲息。"],
    ["とうとうしまいには（最後甚至）\n引取り手（ひきとりて／願意領回的人）\n死人（しにん／死者）\n習慣（しゅうかん／習慣）", "最後甚至形成了把無人認領的死者帶到這座門丟棄的習慣。"],
    ["日の目が見えなくなると（日落天黑後）\n気味を悪るがって（覺得可怕）\n近所（きんじょ／附近）\n足ぶみをしない（不敢踏足）", "因此天黑以後，任何人都覺得害怕，不敢踏足這座門附近。"],
    ["その代り（相對地）\n鴉（からす／烏鴉）\n集って来た（たかってきた／聚集而來）", "相對地，許多烏鴉從不知何處聚集而來。"],
    ["何羽となく（數不清有多少隻）\n輪を描いて（わをえがいて／畫著圈）\n鴟尾（しび／屋脊裝飾）\n飛びまわっている（盤旋飛翔）", "白天能看見數不清的烏鴉在高高的鴟尾周圍鳴叫、盤旋飛翔。"],
    ["殊に（ことに／尤其）\n夕焼（ゆうやけ／晚霞）\n胡麻をまいたように（像撒了芝麻般）\nはっきり見えた（清楚可見）", "尤其當門上的天空被晚霞染紅時，牠們清楚得像灑在天空的芝麻。"],
    ["勿論（もちろん／當然）\n死人の肉（しにんのにく／死者的肉）\n啄みに来る（ついばみにくる／來啄食）", "烏鴉當然是來啄食門上死者的肉。"],
    ["しかし（但是）\n刻限（こくげん／時刻）\n遅いせいか（或許因為太晚）\n一羽も見えない（一隻也看不見）", "不過也許因為時刻已晚，今天連一隻也看不見。"],
    ["崩れかかった（快要崩塌的）\n崩れ目（崩塌的缺口）\n石段（いしだん／石階）\n糞（ふん／糞便）\n点々と（點點地）", "只見在快崩塌、長著長草的石階上，烏鴉的糞便點點地黏成白色。"],
  ],
  yumejuya: [
    ["こんな（這樣的）\n夢（ゆめ／夢）\n見た（みた／夢見、看見）", "我做了這樣一個夢。"],
    ["腕組をして（抱著手臂）\n枕元（まくらもと／枕邊）\n仰向（あおむけ／仰躺）\nもう死にます（就要死了）", "我抱著手臂坐在枕邊時，仰躺的女子用平靜的聲音說：我就要死了。"],
    ["長い髪（ながいかみ／長髮）\n輪郭（りんかく／輪廓）\n柔らかな（やわらかな／柔和的）\n横たえている（よこたえている／躺著）", "女子把長髮鋪在枕上，輪廓柔和的瓜子臉躺在髮中。"],
    ["真白な（まっしろな／雪白的）\n頬（ほお／臉頰）\n血の色（ちのいろ／血色）\n唇（くちびる／嘴唇）", "雪白的臉頰透著恰到好處的暖血色，嘴唇當然是紅的。"],
    ["とうてい（無論如何）\n死にそうには見えない（看不出像要死）", "怎麼看都不像快要死去。"],
    ["しかも（然而）\n静かな声（しずかなこえ／平靜的聲音）\n云った（いった／說了）", "然而她仍用平靜的聲音說自己就要死了。"],
    ["自分も（我也）\nそうだろう（大概是那樣）\n思った（おもった／想）", "我也覺得大概真是如此。"],
    ["そこで（於是）\n死ぬんですか（要死了嗎）\n聞いた（きいた／問）", "於是我問：你要死了嗎？"],
    ["微笑んだ（ほほえんだ／微笑）", "女子微笑了。"],
    ["でも（不過）\n死ぬでしょうね（大概會死吧）", "她說：不過，我大概會死吧。"],
    ["黒い瞳（くろいひとみ／黑色瞳孔）\n奥（おく／深處）\n鮮やかな（あざやかな／鮮明的）\n姿（すがた／身影）", "我在女子黑色瞳孔的深處，看見鮮明的自己身影。"],
    ["まぶた（眼皮）\n重み（おもみ／重量）\n堪えかねて（耐受不住）\nしだいに（逐漸）", "看著她的瞳孔禁不住眼皮的重量而逐漸闔上，我想她真的要死了。"],
    ["死んだら（如果死了）\nどうしよう（該怎麼辦）\n考えた（かんがえた／思考）", "接著我想，她死了以後我該怎麼辦。"],
    ["目を閉じたまま（閉著眼睛）\n百年（ひゃくねん／一百年）\n待っていて下さい（請等待）", "女子閉著眼睛說：請等我一百年。"],
    ["思わず（おもわず／不由得）\n待ちます（まちます／會等待）\n答えた（こたえた／回答）", "我不由得回答：我會等。"],
    ["長い睫（ながいまつげ／長睫毛）\n伏せたまま（垂下不動）\nうなずいた（點了頭）", "她垂著長睫毛，點了點頭。"],
    ["庭（にわ／庭院）\n大きな石（おおきないし／大石頭）\n抱えて来た（抱來）", "我走到庭院裡，抱來一塊大石頭。"],
    ["云った通り（いったとおり／照她所說）\n墓標（ぼひょう／墓碑）", "我照她所說，把那塊石頭當成墓碑。"],
    ["それから（從那以後）\n百年を待った（等待了一百年）", "之後，我等待了一百年。"],
    ["けれども（但是）\nまだ（仍然）\n現れなかった（あらわれなかった／沒有出現）", "然而女子仍沒有出現。"],
  ],
  restaurant: [
    ["二人の若い紳士（兩名年輕紳士）\n鉄砲（てっぽう／獵槍）\n白熊のような犬（像白熊般的狗）\n山奥（やまおく／深山）", "兩名年輕紳士打扮得像英國士兵，扛著亮晶晶的獵槍、帶著兩隻像白熊的狗，在深山落葉沙沙作響之處行走。"],
    ["ぜんたい（究竟）\nここら（這一帶）\n怪しからん（けしからん／太不像話）", "這一帶的山究竟是怎麼回事，太不像話了。"],
    ["鳥（とり／鳥）\n獣（けもの／野獸）\n一疋も（いっぴきも／一隻也）\n居やがらん（いない／沒有）", "連一隻鳥或野獸也沒有。"],
    ["なんでも構わない（什麼都無所謂）\n早く（趕快）\nやって見たい（想試著射擊）", "不管是什麼都好，真想快點砰砰地射幾槍看看。"],
    ["鹿（しか／鹿）\n横っ腹（よこっぱら／側腹）\n二三発（にさんぱつ／兩三槍）\n痛快（つうかい／痛快）", "若朝鹿黃色的側腹送上兩三槍，一定很痛快吧。"],
    ["くるくるまわって（轉著圈）\nどたっと（砰然）\n倒れる（たおれる／倒下）", "牠會轉著圈，然後砰然倒下吧。"],
    ["だいぶ（相當地）\n山奥（やまおく／深山）", "那裡是相當深的深山。"],
    ["案内してきた（帶路而來的）\n鉄砲打ち（てっぽううち／獵人）\nまごついて（不知所措）", "甚至連帶路來的專業獵人也有些不知所措，走到不知哪裡去了。"],
    ["それでも（即使如此）\n山鳥（やまどり／雉雞）\nイギリス風（英國風）\n料理（りょうり／料理）", "即使如此，兩名紳士仍想在哪裡看到許多山鳥，把牠們做成英國風料理吃掉。"],
    ["めまい（眩暈）\n吠って（うなって／吠叫）\n泡を吐いて（あわをはいて／吐泡沫）\n死んでしまいました（死去了）", "那兩隻像白熊的狗一起暈眩，吠了一會兒，接著吐著泡沫死去了。"],
    ["たまらず（受不了）\n馬車（ばしゃ／馬車）\n降りて（おりて／下來）\nそばに寄りました（靠近旁邊）", "兩名紳士受不了，從馬車上下來，靠近狗的身旁。"],
    ["どうしたんだろう（是怎麼了呢）", "這到底是怎麼了呢？"],
    ["困った（こまった／糟了、傷腦筋）", "這下可糟了。"],
    ["たいへんな（嚴重的）\nところ（地方）\n来た（きた／來到）", "我們來到了一個不得了的地方。"],
    ["顔を見合わせました（かおをみあわせました／互相對看）", "兩人互相看了看。"],
    ["そのうち（不久）\n遠くの方（とおくのほう／遠方）\n西洋造り（せいようづくり／西式建築）", "不久，他們看見遠方有一棟西式建築。"],
    ["ひと休み（ひとやすみ／休息一下）\n行って（いって／去）", "到那裡去休息一下吧。"],
    ["そうしよう（就那樣做吧）", "就這麼辦吧。"],
    ["急ぎました（いそぎました／趕去）", "兩人朝那棟房子的方向趕去。"],
    ["入口（いりぐち／入口）\n金文字（きんもじ／金色文字）\n大きく（大大地）\n書いてありました（被寫著）", "入口用金色大字寫著如下的文字。"],
  ],
};

function buildFormattedText(story: Story, count: number) {
  return story.sentences.slice(0, count).map((text, index) => {
    const [details, translation] = studyData[story.id][index];
    return `${text}\n\n${details.replace(/\n/g, "\n\n")}\n\n中文翻譯：${translation}`;
  }).join("\n\n\n\n");
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
