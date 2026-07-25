<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  AlertTriangle,
  BookOpenText,
  Check,
  ChevronDown,
  CircleCheck,
  Download,
  Eye,
  EyeOff,
  FileText,
  KeyRound,
  LoaderCircle,
  Moon,
  Pause,
  Play,
  RotateCcw,
  Sun,
  Upload,
} from '@lucide/vue'

const MAX_FILE_SIZE = 2 * 1024 * 1024
const BATCH_OPTIONS = [5, 10, 20]

const fileInput = ref(null)
const selectedFile = ref(null)
const sourceText = ref('')
const apiKey = ref('')
const showKey = ref(false)
const sentenceLimit = ref(20)
const batchOffset = ref(0)
const preview = ref(null)
const result = ref(null)
const isPreviewing = ref(false)
const isProcessing = ref(false)
const isPaused = ref(false)
const pauseRequested = ref(false)
const batchCompleted = ref(0)
const currentBatchTotal = ref(0)
const completedBeforeBatch = ref(0)
const requestCompleted = ref(0)
const pausedBatchEnd = ref(0)
const activeController = ref(null)
const errorMessage = ref('')
const isDragging = ref(false)
const isDarkMode = ref(false)

onMounted(() => {
  const savedTheme = localStorage.getItem('jra-theme')
  isDarkMode.value =
    savedTheme === 'dark' ||
    (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)
  applyTheme()
})

function applyTheme() {
  document.documentElement.dataset.theme = isDarkMode.value ? 'dark' : 'light'
}

function setTheme(useDarkMode) {
  isDarkMode.value = useDarkMode
  localStorage.setItem('jra-theme', isDarkMode.value ? 'dark' : 'light')
  applyTheme()
}

const canProcess = computed(
  () =>
    preview.value?.sentences?.length > 0 &&
    apiKey.value.trim().length > 0 &&
    !isProcessing.value,
)

const processButtonLabel = computed(() => {
  if (isProcessing.value) return '正在把故事變簡單…'
  if (isPaused.value) return '繼續處理'
  if (result.value && preview.value?.sentences?.length) {
    return `處理下一批（${preview.value.start}–${preview.value.end}）`
  }
  return '開始處理這個章節'
})

const overallTotal = computed(
  () => preview.value?.total ?? result.value?.source?.totalSentences ?? 0,
)

const overallCompleted = computed(() =>
  isProcessing.value
    ? completedBeforeBatch.value + requestCompleted.value
    : result.value?.sentences?.length ?? 0,
)

const overallProgress = computed(() =>
  overallTotal.value
    ? Math.round((overallCompleted.value / overallTotal.value) * 100)
    : 0,
)

const batchProgress = computed(() =>
  currentBatchTotal.value
    ? Math.round((batchCompleted.value / currentBatchTotal.value) * 100)
    : 0,
)

const qualitySummary = computed(() => {
  if (!result.value) {
    return { passed: 0, warnings: 0, failed: 0 }
  }

  const warningCount = result.value.quality.warnings.length
  const criticalCount = result.value.quality.criticalWarnings.length

  return {
    passed:
      result.value.quality.passedCount ??
      (criticalCount === 0 ? result.value.sentences.length : 0),
    warnings: warningCount - criticalCount,
    failed: criticalCount,
  }
})

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const body = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(body.error || '本機服務發生錯誤，請稍後再試。')
  }

  return body
}

async function requestStream(path, payload, onEvent, signal) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.error || '本機服務發生錯誤，請稍後再試。')
  }

  if (!response.body) {
    throw new Error('瀏覽器無法讀取串流結果。')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.trim()) continue
      await onEvent(JSON.parse(line))
    }

    if (done) {
      if (buffer.trim()) await onEvent(JSON.parse(buffer))
      break
    }
  }
}

async function acceptFile(file) {
  errorMessage.value = ''
  result.value = null
  preview.value = null
  batchOffset.value = 0
  isPaused.value = false
  batchCompleted.value = 0
  currentBatchTotal.value = 0
  requestCompleted.value = 0
  pausedBatchEnd.value = 0

  if (!file) return
  if (!file.name.toLowerCase().endsWith('.txt')) {
    errorMessage.value = '第一版目前只接受 TXT 檔案。'
    return
  }
  if (file.size > MAX_FILE_SIZE) {
    errorMessage.value = '檔案請小於 2 MB；第一版會先以短篇文字測試。'
    return
  }

  selectedFile.value = file
  sourceText.value = await file.text()
  await loadPreview()
}

async function loadPreview() {
  if (!sourceText.value.trim()) {
    errorMessage.value = '這個檔案沒有可讀取的文字。'
    return
  }

  isPreviewing.value = true
  errorMessage.value = ''

  try {
    const previewLimit =
      pausedBatchEnd.value > batchOffset.value
        ? pausedBatchEnd.value - batchOffset.value
        : Number(sentenceLimit.value)

    preview.value = await requestJson('/api/preview', {
      method: 'POST',
      body: JSON.stringify({
        text: sourceText.value,
        limit: previewLimit,
        offset: batchOffset.value,
      }),
    })
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isPreviewing.value = false
  }
}

function handleFileInput(event) {
  acceptFile(event.target.files?.[0])
}

function handleDrop(event) {
  isDragging.value = false
  acceptFile(event.dataTransfer.files?.[0])
}

function mergeBatchResult(batchResult) {
  const batchPassedCount = batchResult.quality.passed
    ? batchResult.sentences.length
    : 0

  if (!result.value) {
    result.value = {
      ...batchResult,
      quality: {
        ...batchResult.quality,
        passedCount: batchPassedCount,
      },
    }
    return
  }

  const previous = result.value
  const sentences = [...previous.sentences, ...batchResult.sentences]

  result.value = {
    ...batchResult,
    source: {
      ...batchResult.source,
      processedSentences: sentences.length,
      batchStart: 1,
    },
    elapsedSeconds: Number(
      (previous.elapsedSeconds + batchResult.elapsedSeconds).toFixed(1),
    ),
    sentences,
    formattedText: [previous.formattedText, batchResult.formattedText]
      .filter(Boolean)
      .join('\n\n\n'),
    quality: {
      warnings: [
        ...previous.quality.warnings,
        ...batchResult.quality.warnings,
      ],
      criticalWarnings: [
        ...previous.quality.criticalWarnings,
        ...batchResult.quality.criticalWarnings,
      ],
      passed:
        previous.quality.passed &&
        batchResult.quality.passed,
      passedCount:
        (previous.quality.passedCount ?? 0) +
        batchPassedCount,
    },
  }
}

function requestPause() {
  if (!isProcessing.value || pauseRequested.value) return
  pauseRequested.value = true
}

async function processText() {
  if (!canProcess.value) return

  const startingOffset = batchOffset.value
  const resumingPausedBatch =
    isPaused.value && pausedBatchEnd.value > startingOffset
  const batchCompletedBase = resumingPausedBatch
    ? batchCompleted.value
    : 0
  const requestedLimit =
    preview.value?.sentences?.length ?? Number(sentenceLimit.value)
  const partialSentences = []
  const partialFormattedText = []
  const partialWarnings = []
  const partialCriticalWarnings = []
  const startedAt = performance.now()
  let streamInfo = null
  let finalBatchResult = null

  isProcessing.value = true
  isPaused.value = false
  pauseRequested.value = false
  requestCompleted.value = 0
  batchCompleted.value = batchCompletedBase
  if (!resumingPausedBatch) {
    currentBatchTotal.value = requestedLimit
  }
  completedBeforeBatch.value = result.value?.sentences?.length ?? 0
  errorMessage.value = ''
  activeController.value = new AbortController()

  try {
    await requestStream(
      '/api/process-stream',
      {
        text: sourceText.value,
        apiKey: apiKey.value.trim(),
        limit: requestedLimit,
        offset: batchOffset.value,
      },
      async (event) => {
        if (event.type === 'error') {
          throw new Error(event.error || '處理失敗，請稍後再試。')
        }

        if (event.type === 'start') {
          streamInfo = event
          if (!resumingPausedBatch) {
            currentBatchTotal.value = event.batchTotal
          }
          return
        }

        if (event.type === 'sentence') {
          requestCompleted.value = event.completed
          batchCompleted.value = batchCompletedBase + event.completed
          if (event.sentence) partialSentences.push(event.sentence)
          if (event.formattedText) partialFormattedText.push(event.formattedText)
          partialWarnings.push(...(event.quality?.warnings || []))
          partialCriticalWarnings.push(
            ...(event.quality?.criticalWarnings || []),
          )

          if (pauseRequested.value) {
            activeController.value?.abort()
          }
          return
        }

        if (event.type === 'result') {
          finalBatchResult = event
        }
      },
      activeController.value.signal,
    )

    if (!finalBatchResult) {
      throw new Error('處理完成，但沒有收到完整結果。')
    }

    mergeBatchResult(finalBatchResult)
    requestCompleted.value = finalBatchResult.sentences.length
    batchCompleted.value =
      batchCompletedBase + finalBatchResult.sentences.length

    if (
      pausedBatchEnd.value &&
      finalBatchResult.source.nextOffset >= pausedBatchEnd.value
    ) {
      pausedBatchEnd.value = 0
    }

    if (finalBatchResult.source.hasMore) {
      batchOffset.value = finalBatchResult.source.nextOffset
      await loadPreview()
    } else {
      apiKey.value = ''
    }
  } catch (error) {
    if (error.name === 'AbortError' && pauseRequested.value) {
      const completedCount = partialSentences.length

      if (completedCount > 0 && streamInfo) {
        const nextOffset = startingOffset + completedCount
        pausedBatchEnd.value = streamInfo.source.batchEnd
        mergeBatchResult({
          source: {
            ...streamInfo.source,
            processedSentences: completedCount,
            batchStart: startingOffset + 1,
            batchEnd: nextOffset,
            nextOffset,
            hasMore: nextOffset < streamInfo.source.totalSentences,
          },
          model: streamInfo.model,
          elapsedSeconds: Number(
            ((performance.now() - startedAt) / 1000).toFixed(1),
          ),
          sentences: partialSentences,
          formattedText: partialFormattedText.join('\n\n\n'),
          quality: {
            warnings: partialWarnings,
            criticalWarnings: partialCriticalWarnings,
            passed: partialCriticalWarnings.length === 0,
          },
        })
        batchOffset.value = nextOffset
        if (nextOffset < streamInfo.source.totalSentences) {
          await loadPreview()
        } else {
          apiKey.value = ''
        }
      }

      isPaused.value = true
    } else {
      errorMessage.value = error.message
      isPaused.value = pausedBatchEnd.value > batchOffset.value
    }
  } finally {
    isProcessing.value = false
    pauseRequested.value = false
    activeController.value = null
  }
}

function resetTask() {
  activeController.value?.abort()
  selectedFile.value = null
  sourceText.value = ''
  apiKey.value = ''
  preview.value = null
  result.value = null
  batchOffset.value = 0
  isPaused.value = false
  pauseRequested.value = false
  batchCompleted.value = 0
  currentBatchTotal.value = 0
  requestCompleted.value = 0
  pausedBatchEnd.value = 0
  errorMessage.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function downloadBlob(content, mimeType, extension) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  const baseName = selectedFile.value?.name.replace(/\.txt$/i, '') || 'reading-result'

  anchor.href = url
  anchor.download = `${baseName}-analysis.${extension}`
  anchor.click()
  URL.revokeObjectURL(url)
}

function downloadJson() {
  downloadBlob(JSON.stringify(result.value, null, 2), 'application/json;charset=utf-8', 'json')
}

function downloadText() {
  downloadBlob(
    `\uFEFF${result.value.formattedText}\n`,
    'text/plain;charset=utf-8',
    'txt',
  )
}
</script>

<template>
  <div class="app-shell">
    <main :class="{ 'has-result': result }">
      <section class="hero">
        <div class="hero-topline">
          <div class="eyebrow">
            <BookOpenText :size="16" />
            Japanese Reading Assistant
            <span>· Story-first Japanese learning</span>
          </div>

          <div class="theme-switch" role="group" aria-label="外觀模式">
            <span
              class="theme-switch-slider"
              :class="{ 'is-dark': isDarkMode }"
              aria-hidden="true"
            ></span>
            <button
              class="theme-switch-option"
              :class="{ 'is-active': !isDarkMode }"
              type="button"
              :aria-pressed="!isDarkMode"
              @click="setTheme(false)"
            >
              <Sun :size="16" />
              <span>淺色</span>
            </button>
            <button
              class="theme-switch-option"
              :class="{ 'is-active': isDarkMode }"
              type="button"
              :aria-pressed="isDarkMode"
              @click="setTheme(true)"
            >
              <Moon :size="16" />
              <span>深色</span>
            </button>
          </div>
        </div>
        <h1>從喜歡的故事開始，初學者也能讀日文小說。</h1>
        <p>
          把追劇、讀小說般的娛樂感帶進學習：匯入故事，就能得到逐字拆解、假名與繁中翻譯。
        </p>
        <div class="privacy-note">
          <KeyRound :size="17" />
          <span>本機處理 · API Key 不儲存 · 初學者友善</span>
        </div>
      </section>

      <div class="dashboard-grid" :class="{ 'has-result': result }">
        <section class="workspace-grid">
        <section class="panel story-panel" aria-label="選擇小說與切句預覽">
          <div class="story-panel-grid">
            <div class="story-pane story-input-pane">
              <div class="panel-heading">
                <span class="step-number">01</span>
                <div>
                  <h2>選擇小說 TXT</h2>
                  <p>每批最多 20 句，逐批讀完整個章節。</p>
                </div>
              </div>

              <button
                class="dropzone"
                :class="{ dragging: isDragging, selected: selectedFile }"
                type="button"
                @click="fileInput?.click()"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleDrop"
              >
                <input
                  ref="fileInput"
                  class="sr-only"
                  type="file"
                  accept=".txt,text/plain"
                  @change="handleFileInput"
                />
                <span class="upload-icon">
                  <FileText v-if="selectedFile" :size="25" />
                  <Upload v-else :size="25" />
                </span>
                <span v-if="selectedFile" class="file-details">
                  <strong>{{ selectedFile.name }}</strong>
                  <small>{{ (selectedFile.size / 1024).toFixed(1) }} KB · 點擊可重新選擇</small>
                </span>
                <span v-else class="file-details">
                  <strong>放入想讀的故事</strong>
                  <small>拖曳或點擊選擇 UTF-8 TXT</small>
                </span>
              </button>

              <div class="field-row">
                <label for="sentence-limit">每批處理句數</label>
                <div class="select-wrap">
                  <select
                    id="sentence-limit"
                    v-model="sentenceLimit"
                    :disabled="isProcessing || Boolean(result)"
                    @change="batchOffset = 0; sourceText && loadPreview()"
                  >
                    <option v-for="count in BATCH_OPTIONS" :key="count" :value="count">
                      {{ count }} 句
                    </option>
                  </select>
                  <ChevronDown :size="16" />
                </div>
              </div>
            </div>

            <div class="story-pane story-preview-pane">
              <div class="panel-heading compact">
                <span class="step-number">02</span>
                <div>
                  <h2>確認切句預覽</h2>
                  <p v-if="preview">
                    共辨識 {{ preview.total }} 句，本批第 {{ preview.start }}～{{ preview.end }} 句
                  </p>
                  <p v-else>選擇 TXT 後會先在這裡確認內容。</p>
                </div>
              </div>

              <div v-if="isPreviewing" class="empty-state">
                <LoaderCircle class="spin" :size="28" />
                <p>正在整理句子…</p>
              </div>

              <ol v-else-if="preview?.sentences?.length" class="sentence-preview">
                <li v-for="sentence in preview.sentences" :key="sentence.number">
                  <span>{{ String(sentence.number).padStart(2, '0') }}</span>
                  <p lang="ja">{{ sentence.text }}</p>
                </li>
              </ol>

              <div v-else class="empty-state">
                <FileText :size="30" />
                <p>尚未選擇文字檔</p>
                <small>我們不會在預覽階段呼叫 OpenAI API。</small>
              </div>
            </div>
          </div>
        </section>

        <article class="panel key-panel">
          <div class="panel-heading">
            <span class="step-number">03</span>
            <div>
              <h2>輸入 API Key 並開始</h2>
              <p>逐批處理並累積結果，整章完成後自動清空。</p>
            </div>
          </div>

          <label class="key-field">
            <KeyRound :size="18" />
            <input
              v-model="apiKey"
              :type="showKey ? 'text' : 'password'"
              placeholder="sk-..."
              autocomplete="off"
              spellcheck="false"
            />
            <button
              type="button"
              :aria-label="showKey ? '隱藏 API Key' : '顯示 API Key'"
              @click="showKey = !showKey"
            >
              <EyeOff v-if="showKey" :size="18" />
              <Eye v-else :size="18" />
            </button>
          </label>

          <button class="primary-button" :disabled="!canProcess" @click="processText">
            <LoaderCircle v-if="isProcessing" class="spin" :size="19" />
            <Play v-else :size="19" fill="currentColor" />
            {{ processButtonLabel }}
          </button>

          <div class="fun-note">
            <BookOpenText :size="18" />
            <span>不必先背完整本單字書，從想知道的劇情開始學。</span>
          </div>
        </article>

        <div v-if="errorMessage" class="error-banner workspace-error" role="alert">
          <AlertTriangle :size="19" />
          <span>{{ errorMessage }}</span>
        </div>
        </section>

        <section
          class="results-section"
          :class="{ 'is-empty': !result }"
          :aria-busy="isProcessing"
          aria-live="polite"
        >
        <div v-if="isProcessing || isPaused" class="processing-progress">
          <div class="progress-heading">
            <div>
              <strong>{{ isPaused ? '已暫停' : 'AI 正在逐句整理' }}</strong>
              <span>
                {{ isPaused ? '已保留完成的句子，可以隨時繼續。' : '每完成一句就會更新真實進度。' }}
              </span>
            </div>
            <button
              v-if="isProcessing"
              class="pause-button"
              type="button"
              :disabled="pauseRequested"
              @click="requestPause"
            >
              <Pause :size="16" fill="currentColor" />
              {{ pauseRequested ? '完成這句後暫停' : '暫停' }}
            </button>
          </div>

          <div class="progress-row">
            <div class="progress-label">
              <span>整份文件</span>
              <strong>{{ overallCompleted }}／{{ overallTotal }} 句 · {{ overallProgress }}%</strong>
            </div>
            <div
              class="progress-track"
              role="progressbar"
              aria-label="整份文件進度"
              :aria-valuenow="overallProgress"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              <span :style="{ width: `${overallProgress}%` }"></span>
            </div>
          </div>

          <div class="progress-row is-batch">
            <div class="progress-label">
              <span>目前這一批</span>
              <strong>{{ batchCompleted }}／{{ currentBatchTotal }} 句 · {{ batchProgress }}%</strong>
            </div>
            <div
              class="progress-track"
              role="progressbar"
              aria-label="目前批次進度"
              :aria-valuenow="batchProgress"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              <span :style="{ width: `${batchProgress}%` }"></span>
            </div>
          </div>
        </div>

        <template v-if="result">
          <div class="results-header">
            <div>
              <div class="eyebrow">
                <LoaderCircle v-if="isProcessing" class="spin" :size="16" />
                <CircleCheck v-else :size="16" />
                {{ isProcessing ? 'Processing story' : isPaused ? 'Processing paused' : 'Processing complete' }}
              </div>
              <h2>處理結果</h2>
              <p>
                {{ result.model }} · 已完成 {{ result.sentences.length }}／{{ result.source.totalSentences }} 句
                · 累計 {{ result.elapsedSeconds }} 秒
              </p>
            </div>
            <div class="result-actions">
              <button class="secondary-button" @click="downloadJson">
                <Download :size="17" /> JSON
              </button>
              <button class="secondary-button" @click="downloadText">
                <Download :size="17" /> TXT
              </button>
              <button class="icon-button" title="重新開始" @click="resetTask">
                <RotateCcw :size="18" />
              </button>
            </div>
          </div>

          <div class="quality-grid">
            <article class="quality-card success">
              <CircleCheck :size="20" />
              <span>通過</span>
              <strong>{{ qualitySummary.passed }}</strong>
            </article>
            <article class="quality-card warning">
              <AlertTriangle :size="20" />
              <span>一般警告</span>
              <strong>{{ qualitySummary.warnings }}</strong>
            </article>
            <article class="quality-card failed">
              <AlertTriangle :size="20" />
              <span>嚴重問題</span>
              <strong>{{ qualitySummary.failed }}</strong>
            </article>
          </div>

          <div
            v-if="result.quality.warnings.length === 0"
            class="quality-passed"
          >
            <Check :size="18" />
            編號、原句、逐字拆解、翻譯與格式檢核皆通過。
          </div>

          <div v-else class="quality-issues">
            <h3>需要留意的項目</h3>
            <ul>
              <li v-for="warning in result.quality.warnings" :key="warning">{{ warning }}</li>
            </ul>
          </div>

          <article class="formatted-output">
            <div>
              <span>輸出結果</span>
              <small>畫面顯示與 TXT 下載皆使用相同排版</small>
            </div>
            <pre>{{ result.formattedText }}</pre>
          </article>
        </template>

        <template v-else>
          <div class="results-placeholder-header">
            <div class="eyebrow">
              <LoaderCircle v-if="isProcessing" class="spin" :size="16" />
              <FileText v-else :size="16" />
              {{ isProcessing ? 'Processing story' : 'Your reading result' }}
            </div>
            <h2>處理結果</h2>
          </div>

          <div class="results-placeholder" :class="{ 'is-processing': isProcessing }">
            <span class="results-placeholder-icon">
              <LoaderCircle v-if="isProcessing" class="spin" :size="28" />
              <BookOpenText v-else :size="28" />
            </span>
            <div>
              <strong>
                {{ isProcessing ? 'AI 正在整理這段故事…' : '你的閱讀輔助結果會顯示在這裡' }}
              </strong>
              <p v-if="isProcessing">
                正在產生逐字拆解、假名、繁中翻譯與品質檢核，完成後會更新在同一區域。
              </p>
              <p v-else>
                選擇小說、確認切句並開始處理後，就能在這裡閱讀及下載結果。
              </p>
            </div>
          </div>
        </template>
        </section>
      </div>
    </main>

    <footer>
      <span>Japanese Reading Assistant</span>
      <span>Local-first · Your key, your text, your control.</span>
    </footer>
  </div>
</template>
