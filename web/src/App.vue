<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import dataset from './data/tasks.json'

const statusMeta = {
  success: { label: '成功', shortLabel: '通過', symbol: '✓' },
  warning: { label: '警告', shortLabel: '注意', symbol: '!' },
  failed: { label: '失敗', shortLabel: '失敗', symbol: '×' },
  review: { label: '待複查', shortLabel: '複查', symbol: '?' },
}

const categoryMeta = {
  completeness: '完整性',
  numbering: '編號',
  format: '格式',
  language: '語言',
  tokenization: '單字拆解',
  translation: '翻譯',
}

const outcomeMeta = {
  pass: '通過',
  warning: '注意',
  error: '錯誤',
  review: '待複查',
}

const getTaskStatus = (task) => {
  if (task.status && statusMeta[task.status]) return task.status

  const outcomes = task.checks.map((check) => check.outcome)
  if (outcomes.includes('error')) return 'failed'
  if (outcomes.includes('review')) return 'review'
  if (outcomes.includes('warning')) return 'warning'
  return 'success'
}

const tasks = dataset.tasks.map((task) => ({
  ...task,
  status: getTaskStatus(task),
}))

const learningMode = ref('beginner')
const activeStatus = ref('all')
const activeCategory = ref('all')
const searchQuery = ref('')
const selectedTaskId = ref(tasks[0]?.id ?? null)
const selectedSentenceId = ref(null)
const showMobileDetail = ref(false)
const detailHeading = ref(null)
const lastSelectedTaskId = ref(null)

const summary = computed(() =>
  Object.keys(statusMeta).map((status) => ({
    status,
    ...statusMeta[status],
    count: tasks.filter((task) => task.status === status).length,
  })),
)

const categories = computed(() => {
  const values = new Set()
  tasks.forEach((task) => {
    task.checks
      .filter((check) => check.outcome !== 'pass')
      .forEach((check) => values.add(check.category))
  })
  return [...values]
})

const filteredTasks = computed(() => {
  const needle = searchQuery.value.trim().toLocaleLowerCase()

  return tasks.filter((task) => {
    const matchesStatus = activeStatus.value === 'all' || task.status === activeStatus.value
    const matchesCategory =
      activeCategory.value === 'all' ||
      task.checks.some(
        (check) =>
          check.category === activeCategory.value &&
          check.outcome !== 'pass',
      )
    const searchableText = [
      task.id,
      task.outputFile,
      `file ${String(task.fileNumber).padStart(3, '0')}`,
      ...task.sentences.map((sentence) => `${sentence.number} ${sentence.original}`),
    ]
      .join(' ')
      .toLocaleLowerCase()
    const matchesSearch = !needle || searchableText.includes(needle)

    return matchesStatus && matchesCategory && matchesSearch
  })
})

const selectedTask = computed(
  () => tasks.find((task) => task.id === selectedTaskId.value) ?? null,
)

const selectedSentence = computed(() => {
  if (!selectedTask.value) return null
  return (
    selectedTask.value.sentences.find(
      (sentence) => sentence.id === selectedSentenceId.value,
    ) ?? selectedTask.value.sentences[0]
  )
})

const selectedTaskIssues = computed(
  () => selectedTask.value?.checks.filter((check) => check.outcome !== 'pass') ?? [],
)

const selectedSentenceChecks = computed(() => {
  if (!selectedTask.value || !selectedSentence.value) return []
  return selectedTask.value.checks.filter(
    (check) =>
      (check.sentenceId && check.sentenceId === selectedSentence.value.id) ||
      (!check.sentenceId &&
        check.sentenceNumber === selectedSentence.value.number),
  )
})

const totalExpectedSentences = computed(() =>
  tasks.reduce(
    (sum, task) =>
      sum + (task.sentenceRange.end - task.sentenceRange.start + 1),
    0,
  ),
)

const datasetDate = computed(() =>
  new Intl.DateTimeFormat('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(dataset.meta.generatedAt)),
)

const scoreFor = (task) => {
  if (typeof task.qualityScore === 'number') return task.qualityScore
  if (!task.checks.length) return 100
  const weights = { pass: 1, warning: 0.72, review: 0.55, error: 0 }
  const total = task.checks.reduce(
    (sum, check) => sum + (weights[check.outcome] ?? 0),
    0,
  )
  return Math.round((total / task.checks.length) * 100)
}

const issueCountFor = (task) =>
  task.checks.filter((check) => check.outcome !== 'pass').length

const formatDuration = (milliseconds) =>
  milliseconds < 1000
    ? `${milliseconds} ms`
    : `${(milliseconds / 1000).toFixed(1)} 秒`

const formatProcessedAt = (value) =>
  new Intl.DateTimeFormat('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(value))

const setStatusFilter = (status) => {
  activeStatus.value = activeStatus.value === status ? 'all' : status
}

const clearFilters = () => {
  activeStatus.value = 'all'
  activeCategory.value = 'all'
  searchQuery.value = ''
}

const selectTask = async (taskId) => {
  selectedTaskId.value = taskId
  lastSelectedTaskId.value = taskId

  if (window.matchMedia('(max-width: 860px)').matches) {
    showMobileDetail.value = true
    await nextTick()
    detailHeading.value?.focus()
  }
}

const returnToTaskList = async () => {
  showMobileDetail.value = false
  await nextTick()
  if (lastSelectedTaskId.value) {
    document
      .querySelector(`[data-task-id="${lastSelectedTaskId.value}"]`)
      ?.focus()
  }
}

const checkCanSelectSentence = (check) => {
  if (!selectedTask.value) return false
  if (check.sentenceId) {
    return selectedTask.value.sentences.some(
      (sentence) => sentence.id === check.sentenceId,
    )
  }
  if (!check.sentenceNumber) return false
  return (
    selectedTask.value.sentences.filter(
      (sentence) => sentence.number === check.sentenceNumber,
    ).length === 1
  )
}

const selectCheck = (check) => {
  if (checkCanSelectSentence(check)) {
    selectedSentenceId.value =
      check.sentenceId ??
      selectedTask.value.sentences.find(
        (sentence) => sentence.number === check.sentenceNumber,
      )?.id ??
      null
  }
}

const sentenceHasIssue = (sentence) =>
  selectedTask.value?.checks.some(
    (check) =>
      check.outcome !== 'pass' &&
      ((check.sentenceId && check.sentenceId === sentence.id) ||
        (!check.sentenceId && check.sentenceNumber === sentence.number)),
  )

const sentenceNavLabel = (task, sentence) => {
  const duplicates = task.sentences.filter(
    (item) => item.number === sentence.number,
  )
  if (duplicates.length === 1) return `句 ${sentence.number}`
  const occurrence = duplicates.findIndex((item) => item.id === sentence.id) + 1
  return `句 ${sentence.number}，重複項目 ${occurrence}`
}

watch(
  filteredTasks,
  (visibleTasks) => {
    if (!visibleTasks.some((task) => task.id === selectedTaskId.value)) {
      selectedTaskId.value = visibleTasks[0]?.id ?? null
      if (!selectedTaskId.value) showMobileDetail.value = false
    }
  },
  { immediate: true },
)

watch(
  selectedTaskId,
  () => {
    const task = selectedTask.value
    if (!task) {
      selectedSentenceId.value = null
      return
    }

    const firstExactIssue = task.checks.find(
      (check) =>
        check.outcome !== 'pass' &&
        check.sentenceId &&
        task.sentences.some((sentence) => sentence.id === check.sentenceId),
    )
    const firstUniqueNumberIssue = task.checks.find(
      (check) =>
        check.outcome !== 'pass' &&
        !check.sentenceId &&
        task.sentences.filter(
          (sentence) => sentence.number === check.sentenceNumber,
        ).length === 1,
    )
    const firstIssue = firstExactIssue ?? firstUniqueNumberIssue
    selectedSentenceId.value =
      firstIssue?.sentenceId ??
      task.sentences.find(
        (sentence) => sentence.number === firstIssue?.sentenceNumber,
      )?.id ??
      task.sentences[0]?.id ??
      null
  },
  { immediate: true },
)

watch(learningMode, (mode) => {
  localStorage.setItem('jra-learning-mode', mode)
})

onMounted(() => {
  const savedMode = localStorage.getItem('jra-learning-mode')
  if (savedMode === 'beginner' || savedMode === 'advanced') {
    learningMode.value = savedMode
  }
})
</script>

<template>
  <div class="app-shell" :data-mode="learningMode">
    <a class="skip-link" href="#dashboard-content">跳到主要內容</a>

    <header class="site-header">
      <div class="header-bar">
        <a class="brand" href="#dashboard-content" aria-label="Japanese Reading Assistant 首頁">
          <span class="brand-mark" aria-hidden="true">読</span>
          <span class="brand-copy">
            <strong>Japanese Reading Assistant</strong>
            <small>AI 文本品質檢核台</small>
          </span>
        </a>

        <div class="mode-switcher" aria-label="閱讀模式">
          <span class="mode-label">閱讀模式</span>
          <div class="segmented-control">
            <button
              type="button"
              :aria-pressed="learningMode === 'beginner'"
              :class="{ active: learningMode === 'beginner' }"
              @click="learningMode = 'beginner'"
            >
              初學者
            </button>
            <button
              type="button"
              :aria-pressed="learningMode === 'advanced'"
              :class="{ active: learningMode === 'advanced' }"
              @click="learningMode = 'advanced'"
            >
              進階者
            </button>
          </div>
        </div>
      </div>

      <div class="hero">
        <div class="hero-copy">
          <p class="eyebrow">
            <span class="live-dot" aria-hidden="true"></span>
            PORTFOLIO DEMO · MOCK DATA
          </p>
          <h1>從 AI 輸出到可交付教材，<br />品質一眼可見。</h1>
          <p class="hero-description">
            集中檢視長文本處理任務、逐句拆解與格式異常，讓人工複查只聚焦在真正需要判斷的地方。
          </p>
        </div>

        <dl class="batch-note">
          <div>
            <dt>資料集</dt>
            <dd>{{ dataset.meta.datasetName }}</dd>
          </div>
          <div>
            <dt>本批句數</dt>
            <dd>{{ totalExpectedSentences }} 句</dd>
          </div>
          <div>
            <dt>更新時間</dt>
            <dd>{{ datasetDate }}</dd>
          </div>
        </dl>
      </div>
    </header>

    <main id="dashboard-content">
      <section class="overview-section" aria-labelledby="overview-heading">
        <div class="section-heading">
          <div>
            <p class="section-kicker">BATCH OVERVIEW</p>
            <h2 id="overview-heading">任務總覽</h2>
          </div>
          <p>點選卡片即可篩選任務，再次點選可取消。</p>
        </div>

        <div class="summary-grid">
          <button
            v-for="item in summary"
            :key="item.status"
            type="button"
            class="summary-card"
            :class="[`status-${item.status}`, { active: activeStatus === item.status }]"
            :aria-pressed="activeStatus === item.status"
            @click="setStatusFilter(item.status)"
          >
            <span class="summary-icon" aria-hidden="true">{{ item.symbol }}</span>
            <span class="summary-content">
              <span>{{ item.label }}</span>
              <strong>{{ String(item.count).padStart(2, '0') }}</strong>
            </span>
            <span class="summary-caption">個任務</span>
          </button>
        </div>
      </section>

      <section class="task-section" aria-labelledby="tasks-heading">
        <div class="section-heading task-heading">
          <div>
            <p class="section-kicker">QUALITY WORKSPACE</p>
            <h2 id="tasks-heading">任務與逐句檢視</h2>
          </div>
          <div class="mock-disclaimer">
            <span aria-hidden="true">i</span>
            所有內容皆為作品集模擬資料，未連接 API
          </div>
        </div>

        <div class="filter-bar">
          <label class="search-field">
            <span>搜尋任務或日文原句</span>
            <span class="input-shell">
              <span class="search-symbol" aria-hidden="true"></span>
              <input
                v-model="searchQuery"
                type="search"
                placeholder="例如：FILE 003、校庭、句號 20"
              />
            </span>
          </label>

          <div class="status-filter" aria-label="任務狀態篩選">
            <span class="control-label">任務狀態</span>
            <div class="filter-pills">
              <button
                type="button"
                :class="{ active: activeStatus === 'all' }"
                :aria-pressed="activeStatus === 'all'"
                @click="activeStatus = 'all'"
              >
                全部
              </button>
              <button
                v-for="(meta, status) in statusMeta"
                :key="status"
                type="button"
                :class="[`status-${status}`, { active: activeStatus === status }]"
                :aria-pressed="activeStatus === status"
                @click="activeStatus = status"
              >
                <span class="status-dot" aria-hidden="true"></span>
                {{ meta.shortLabel }}
              </button>
            </div>
          </div>

          <label class="category-field">
            <span>問題類型</span>
            <select v-model="activeCategory">
              <option value="all">所有類型</option>
              <option v-for="category in categories" :key="category" :value="category">
                {{ categoryMeta[category] ?? category }}
              </option>
            </select>
          </label>

          <button
            type="button"
            class="clear-button"
            :disabled="
              activeStatus === 'all' &&
              activeCategory === 'all' &&
              !searchQuery
            "
            @click="clearFilters"
          >
            清除
          </button>
        </div>

        <p class="result-count" aria-live="polite">
          顯示 {{ filteredTasks.length }} / {{ tasks.length }} 個任務
        </p>

        <div
          class="workspace"
          :class="{ 'show-mobile-detail': showMobileDetail }"
        >
          <aside class="task-list-panel" aria-label="任務列表">
            <div v-if="filteredTasks.length" class="task-list">
              <button
                v-for="task in filteredTasks"
                :key="task.id"
                type="button"
                class="task-card"
                :class="{ selected: selectedTaskId === task.id }"
                :aria-current="selectedTaskId === task.id ? 'true' : undefined"
                :data-task-id="task.id"
                @click="selectTask(task.id)"
              >
                <span class="task-card-topline">
                  <span class="file-id">
                    FILE {{ String(task.fileNumber).padStart(3, '0') }}
                  </span>
                  <span class="status-badge" :class="`status-${task.status}`">
                    <span class="status-dot" aria-hidden="true"></span>
                    {{ statusMeta[task.status].label }}
                  </span>
                </span>

                <span class="task-range">
                  句 {{ task.sentenceRange.start }}–{{ task.sentenceRange.end }}
                  <small>{{ task.outputFile }}</small>
                </span>

                <span class="task-preview" lang="ja">
                  {{ task.sentences[0]?.original }}
                </span>

                <span class="task-quality">
                  <span class="quality-row">
                    <span>品質分數 {{ scoreFor(task) }}</span>
                    <span>
                      {{
                        issueCountFor(task)
                          ? `${issueCountFor(task)} 個問題`
                          : '全部通過'
                      }}
                    </span>
                  </span>
                  <span class="mini-meter" aria-hidden="true">
                    <span :style="{ width: `${scoreFor(task)}%` }"></span>
                  </span>
                </span>

                <span class="task-meta">
                  <span>{{ formatProcessedAt(task.processedAt) }}</span>
                  <span>{{ formatDuration(task.processingTimeMs) }}</span>
                  <span>嘗試 {{ task.attempts }} 次</span>
                </span>
              </button>
            </div>

            <div v-else class="empty-state">
              <span aria-hidden="true">空</span>
              <h3>沒有符合條件的任務</h3>
              <p>試著調整關鍵字或清除篩選條件。</p>
              <button type="button" @click="clearFilters">清除所有篩選</button>
            </div>
          </aside>

          <article v-if="selectedTask" class="detail-panel">
            <button type="button" class="mobile-back" @click="returnToTaskList">
              <span aria-hidden="true">←</span>
              返回任務列表
            </button>

            <header class="detail-header">
              <div>
                <div class="detail-labels">
                  <span class="status-badge" :class="`status-${selectedTask.status}`">
                    <span class="status-dot" aria-hidden="true"></span>
                    {{ statusMeta[selectedTask.status].label }}
                  </span>
                  <span>句 {{ selectedTask.sentenceRange.start }}–{{ selectedTask.sentenceRange.end }}</span>
                </div>
                <h2 ref="detailHeading" tabindex="-1">
                  FILE {{ String(selectedTask.fileNumber).padStart(3, '0') }}
                </h2>
                <p>{{ selectedTask.outputFile }}</p>
              </div>

              <div class="score-block">
                <strong>{{ scoreFor(selectedTask) }}</strong>
                <span>品質分數</span>
                <span class="score-meter" aria-hidden="true">
                  <span :style="{ width: `${scoreFor(selectedTask)}%` }"></span>
                </span>
              </div>
            </header>

            <div class="detail-metadata">
              <div>
                <span>處理時間</span>
                <strong>{{ formatDuration(selectedTask.processingTimeMs) }}</strong>
              </div>
              <div>
                <span>處理嘗試</span>
                <strong>{{ selectedTask.attempts }} 次</strong>
              </div>
              <div>
                <span>問題數</span>
                <strong>{{ selectedTaskIssues.length }}</strong>
              </div>
            </div>

            <section class="sentence-section" aria-labelledby="sentence-heading">
              <div class="subsection-heading">
                <div>
                  <span class="step-index">01</span>
                  <div>
                    <p>OUTPUT REVIEW</p>
                    <h3 id="sentence-heading">逐句閱讀</h3>
                  </div>
                </div>
                <span class="mode-indicator">
                  {{ learningMode === 'beginner' ? '初學者視圖' : '進階者視圖' }}
                </span>
              </div>

              <nav class="sentence-nav" aria-label="選擇句子">
                <button
                  v-for="sentence in selectedTask.sentences"
                  :key="sentence.id"
                  type="button"
                  :class="{
                    active: selectedSentence?.id === sentence.id,
                    issue: sentenceHasIssue(sentence),
                  }"
                  :aria-current="
                    selectedSentence?.id === sentence.id ? 'true' : undefined
                  "
                  :aria-label="sentenceNavLabel(selectedTask, sentence)"
                  @click="selectedSentenceId = sentence.id"
                >
                  {{ sentence.number }}
                  <span
                    v-if="sentenceHasIssue(sentence)"
                    class="issue-mark"
                    aria-label="此句有檢核問題"
                  ></span>
                </button>
              </nav>

              <div v-if="selectedSentence" class="sentence-content">
                <div class="original-card">
                  <div class="content-label">
                    <span>日文原句</span>
                    <span>句 {{ selectedSentence.number }}</span>
                  </div>
                  <p lang="ja">{{ selectedSentence.original }}</p>
                  <div
                    v-if="selectedSentenceChecks.length"
                    class="sentence-alert"
                    :class="`outcome-${selectedSentenceChecks[0].outcome}`"
                  >
                    <span aria-hidden="true">!</span>
                    {{ selectedSentenceChecks[0].title }}
                  </div>
                </div>

                <div class="breakdown-block">
                  <div class="content-label">
                    <span>單字拆解</span>
                    <span>{{ selectedSentence.tokens.length }} 個詞素</span>
                  </div>

                  <ul
                    v-if="learningMode === 'beginner'"
                    class="beginner-tokens"
                    aria-label="初學者單字拆解"
                  >
                    <li
                      v-for="(token, index) in selectedSentence.tokens"
                      :key="`${token.surface}-${index}`"
                    >
                      <div class="token-word" lang="ja">
                        <ruby>
                          {{ token.surface }}
                          <rt>{{ token.reading }}</rt>
                        </ruby>
                      </div>
                      <strong>{{ token.meaning }}</strong>
                      <p>{{ token.beginnerNote }}</p>
                    </li>
                  </ul>

                  <div v-else class="advanced-table-wrap">
                    <table class="advanced-table">
                      <thead>
                        <tr>
                          <th scope="col">單字</th>
                          <th scope="col">假名</th>
                          <th scope="col">詞性／文法</th>
                          <th scope="col">中文</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="(token, index) in selectedSentence.tokens"
                          :key="`${token.surface}-${index}`"
                        >
                          <th scope="row" lang="ja">{{ token.surface }}</th>
                          <td lang="ja">{{ token.reading }}</td>
                          <td>
                            <span class="pos-tag">{{ token.partOfSpeech }}</span>
                            <span
                              v-for="tag in token.grammarTags"
                              :key="tag"
                              class="grammar-tag"
                            >
                              {{ tag }}
                            </span>
                          </td>
                          <td>{{ token.meaning }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <div
                  class="translation-card"
                  :class="{ missing: !selectedSentence.translation }"
                >
                  <div class="content-label">
                    <span>中文翻譯</span>
                    <span>zh-Hant</span>
                  </div>
                  <p lang="zh-Hant">
                    {{ selectedSentence.translation || '此句缺少中文翻譯。' }}
                  </p>
                </div>
              </div>
            </section>

            <section class="check-section" aria-labelledby="checks-heading">
              <div class="subsection-heading">
                <div>
                  <span class="step-index">02</span>
                  <div>
                    <p>QUALITY ASSURANCE</p>
                    <h3 id="checks-heading">品質檢核</h3>
                  </div>
                </div>
                <span>{{ selectedTask.checks.length }} 項規則</span>
              </div>

              <div class="check-list">
                <button
                  v-for="check in selectedTask.checks"
                  :key="check.id"
                  type="button"
                  class="check-item"
                  :class="`outcome-${check.outcome}`"
                  :disabled="!checkCanSelectSentence(check)"
                  @click="selectCheck(check)"
                >
                  <span class="check-symbol" aria-hidden="true">
                    {{ check.outcome === 'pass' ? '✓' : check.outcome === 'error' ? '×' : '!' }}
                  </span>
                  <span class="check-copy">
                    <span class="check-title-row">
                      <strong>{{ check.title }}</strong>
                      <span>{{ outcomeMeta[check.outcome] }}</span>
                    </span>
                    <span>{{ check.message }}</span>
                    <code v-if="check.evidence">{{ check.evidence }}</code>
                  </span>
                  <span v-if="check.sentenceNumber" class="check-sentence">
                    句 {{ check.sentenceNumber }}
                  </span>
                </button>
              </div>
            </section>
          </article>

          <div v-else class="detail-panel no-selection">
            <span aria-hidden="true">選</span>
            <h3>請先選擇一個任務</h3>
            <p>任務詳情、逐字拆解與品質檢核會顯示在這裡。</p>
          </div>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <p>
        Japanese Reading Assistant
        <span>·</span>
        Portfolio quality dashboard
      </p>
      <p>Vue 3 + Vite · Static mock data</p>
    </footer>
  </div>
</template>
